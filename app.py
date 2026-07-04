"""
app.py
StudyGen AI – Agentic Smart Study Assistant
Flask application entry point and route definitions.

Multi-agent architecture:
  Agent 1 – DocumentProcessingAgent   : PDF ingestion & chunking
  Agent 2 – KnowledgeRetrievalAgent   : FAISS-based RAG retrieval
  Agent 3 – SummarizationAgent        : Summaries, key points, flashcards
  Agent 4 – QuizGenerationAgent       : MCQ / short / long-answer quizzes
  Agent 5 – StudyPlannerAgent         : Personalised study schedules
  Agent 6 – DoubtSolvingAgent         : Conversational Q&A chatbot
"""

import os
import logging
import uuid
from pathlib import Path
from functools import lru_cache

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    flash,
    session,
)
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# ── Load environment ─────────────────────────────────────────
load_dotenv()

# ── Logging setup ────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Agent imports ─────────────────────────────────────────────
from agents.document_agent import DocumentProcessingAgent
from agents.retrieval_agent import KnowledgeRetrievalAgent
from agents.summarization_agent import SummarizationAgent
from agents.quiz_agent import QuizGenerationAgent
from agents.planner_agent import StudyPlannerAgent
from agents.doubt_solver_agent import DoubtSolvingAgent
from config.ibm_config import IBMConfig, AGENT_INSTRUCTIONS

# ─────────────────────────────────────────────────────────────
#  Flask app factory
# ─────────────────────────────────────────────────────────────
def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "studygen-secret-key-change-me")

    CORS(app)

    # Upload configuration
    upload_folder = Path(os.getenv("UPLOAD_FOLDER", "uploads"))
    upload_folder.mkdir(parents=True, exist_ok=True)
    data_folder = Path("data")
    data_folder.mkdir(parents=True, exist_ok=True)

    app.config["UPLOAD_FOLDER"] = str(upload_folder)
    app.config["MAX_CONTENT_LENGTH"] = (
        int(os.getenv("MAX_CONTENT_LENGTH_MB", 50)) * 1024 * 1024
    )
    app.config["ALLOWED_EXTENSIONS"] = {"pdf"}

    # ── Initialise agents (singleton per process) ────────────
    doc_agent = DocumentProcessingAgent()
    retrieval_agent = KnowledgeRetrievalAgent()
    summary_agent = SummarizationAgent()
    quiz_agent = QuizGenerationAgent()
    planner_agent = StudyPlannerAgent()
    doubt_agent = DoubtSolvingAgent()

    # Try to reload a persisted index on startup
    retrieval_agent.load_existing_index()

    # ── Helpers ───────────────────────────────────────────────
    def _allowed_file(filename: str) -> bool:
        return (
            "." in filename
            and filename.rsplit(".", 1)[1].lower()
            in app.config["ALLOWED_EXTENSIONS"]
        )

    def _get_context(query: str) -> str:
        """Retrieve RAG context; fall back to full document text."""
        if retrieval_agent.is_ready:
            ctx = retrieval_agent.get_context_string(query)
            if ctx:
                return ctx
        return doc_agent.get_full_text()[:3000]

    # ─────────────────────────────────────────────────────────
    #  ROUTES – Pages
    # ─────────────────────────────────────────────────────────

    @app.route("/")
    def index():
        """Landing page."""
        return render_template("index.html")

    @app.route("/dashboard")
    def dashboard():
        """Main student dashboard."""
        docs = doc_agent.get_document_info()
        return render_template(
            "dashboard.html",
            documents=docs,
            ibm_configured=IBMConfig.is_configured(),
            chunk_count=retrieval_agent.chunk_count,
        )

    @app.route("/upload")
    def upload_page():
        return render_template("upload.html")

    @app.route("/chat")
    def chat_page():
        docs = doc_agent.get_document_info()
        return render_template("chat.html", documents=docs)

    @app.route("/summary")
    def summary_page():
        docs = doc_agent.get_document_info()
        return render_template("summary.html", documents=docs)

    @app.route("/quiz")
    def quiz_page():
        docs = doc_agent.get_document_info()
        return render_template("quiz.html", documents=docs)

    @app.route("/planner")
    def planner_page():
        return render_template("planner.html")

    @app.route("/flashcards")
    def flashcards_page():
        docs = doc_agent.get_document_info()
        return render_template("flashcards.html", documents=docs)

    # ─────────────────────────────────────────────────────────
    #  API ROUTES
    # ─────────────────────────────────────────────────────────

    # ── Agent 1: Document Upload ─────────────────────────────
    @app.route("/api/upload", methods=["POST"])
    def api_upload():
        """Upload and process a PDF document."""
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file part in request."}), 400

        file = request.files["file"]
        if not file or file.filename == "":
            return jsonify({"success": False, "error": "No file selected."}), 400

        if not _allowed_file(file.filename):
            return jsonify({"success": False, "error": "Only PDF files are allowed."}), 400

        filename = secure_filename(file.filename)
        # Prepend a short UUID to avoid name collisions
        unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
        file.save(file_path)

        # Agent 1 – process
        result = doc_agent.process_pdf(file_path, unique_name)
        if not result["success"]:
            return jsonify(result), 422

        # Agent 2 – build / update RAG index
        all_chunks = doc_agent.get_all_chunks()
        kb_result = retrieval_agent.build_knowledge_base(all_chunks)
        result["knowledge_base"] = kb_result

        logger.info("Document uploaded and indexed: %s", unique_name)
        return jsonify(result)

    @app.route("/api/documents", methods=["GET"])
    def api_documents():
        return jsonify({"documents": doc_agent.get_document_info()})

    # ── Agent 3: Summarization ───────────────────────────────
    @app.route("/api/summarize", methods=["POST"])
    def api_summarize():
        data = request.get_json(force=True)
        mode = data.get("mode", "summary")   # summary | key_points | revision | topics
        topic = data.get("topic", "")

        text = _get_context(topic or "main concepts")
        if not text:
            return jsonify({"success": False, "error": "No study material uploaded yet."}), 400

        if mode == "key_points":
            result = summary_agent.extract_key_points(text)
        elif mode == "revision":
            result = summary_agent.generate_revision_notes(text)
        elif mode == "topics":
            result = summary_agent.identify_important_topics(text)
        else:
            result = summary_agent.summarize(text, topic)

        return jsonify({"success": True, "result": result, "mode": mode})

    # ── Agent 3: Flashcards ──────────────────────────────────
    @app.route("/api/flashcards", methods=["POST"])
    def api_flashcards():
        data = request.get_json(force=True)
        count = int(data.get("count", 10))
        topic = data.get("topic", "")

        text = _get_context(topic or "key concepts definitions")
        if not text:
            return jsonify({"success": False, "error": "No study material uploaded yet."}), 400

        result = summary_agent.generate_flashcards(text, count)
        return jsonify({"success": True, "result": result, "count": count})

    # ── Agent 4: Quiz Generation ─────────────────────────────
    @app.route("/api/quiz", methods=["POST"])
    def api_quiz():
        data = request.get_json(force=True)
        quiz_type = data.get("type", "mcq")   # mcq | short | long | mixed
        count = int(data.get("count", 5))
        topic = data.get("topic", "")

        text = _get_context(topic or "exam questions")
        if not text:
            return jsonify({"success": False, "error": "No study material uploaded yet."}), 400

        if quiz_type == "short":
            result = quiz_agent.generate_short_answer(text, topic, count)
            return jsonify({"success": True, "result": result, "type": quiz_type})
        elif quiz_type == "long":
            result = quiz_agent.generate_long_answer(text, topic, count)
            return jsonify({"success": True, "result": result, "type": quiz_type})
        elif quiz_type == "mixed":
            result = quiz_agent.generate_mixed_quiz(text, topic)
            return jsonify({"success": True, "result": result, "type": quiz_type})
        else:
            result = quiz_agent.generate_mcq(text, topic, count)
            return jsonify({"success": True, "result": result, "type": quiz_type})

    @app.route("/api/evaluate", methods=["POST"])
    def api_evaluate():
        data = request.get_json(force=True)
        question = data.get("question", "")
        student_answer = data.get("student_answer", "")
        model_answer = data.get("model_answer", "")

        if not (question and student_answer):
            return jsonify({"success": False, "error": "Question and answer required."}), 400

        result = quiz_agent.evaluate_answer(question, student_answer, model_answer)
        return jsonify({"success": True, "result": result})

    # ── Agent 5: Study Planner ───────────────────────────────
    @app.route("/api/planner", methods=["POST"])
    def api_planner():
        data = request.get_json(force=True)
        action = data.get("action", "plan")   # plan | weekly | tips | checklist

        if action == "weekly":
            subjects = data.get("subjects", [])
            daily_hours = float(data.get("daily_hours", 3))
            week = int(data.get("week", 1))
            result = planner_agent.generate_weekly_schedule(subjects, daily_hours, week)

        elif action == "tips":
            subject = data.get("subject", "")
            exam_type = data.get("exam_type", "written")
            result = planner_agent.get_exam_preparation_tips(subject, exam_type)

        elif action == "checklist":
            topics = data.get("topics", [])
            subject = data.get("subject", "")
            result = planner_agent.generate_revision_checklist(topics, subject)

        else:   # default: full study plan
            subject = data.get("subject", "")
            exam_date = data.get("exam_date", "")
            daily_hours = float(data.get("daily_hours", 3))
            topics = data.get("topics", "")
            level = data.get("current_level", "intermediate")

            if not (subject and exam_date):
                return jsonify(
                    {"success": False, "error": "Subject and exam_date are required."}
                ), 400

            result = planner_agent.create_study_plan(
                subject, exam_date, daily_hours, topics, level
            )

        return jsonify({"success": True, "result": result, "action": action})

    # ── Agent 6: Doubt Solving / Chat ────────────────────────
    @app.route("/api/chat", methods=["POST"])
    def api_chat():
        data = request.get_json(force=True)
        message = data.get("message", "").strip()
        history = data.get("history", [])   # [[role, text], …]

        if not message:
            return jsonify({"success": False, "error": "Message is required."}), 400

        # Agent 2 retrieves context; Agent 6 answers with it
        context = retrieval_agent.get_context_string(message) if retrieval_agent.is_ready else ""
        answer = doubt_agent.answer_question(message, context, history)
        return jsonify({"success": True, "answer": answer})

    @app.route("/api/explain", methods=["POST"])
    def api_explain():
        data = request.get_json(force=True)
        concept = data.get("concept", "").strip()
        if not concept:
            return jsonify({"success": False, "error": "Concept is required."}), 400

        context = retrieval_agent.get_context_string(concept) if retrieval_agent.is_ready else ""
        result = doubt_agent.explain_concept(concept, context)
        return jsonify({"success": True, "result": result})

    @app.route("/api/recommendations", methods=["POST"])
    def api_recommendations():
        data = request.get_json(force=True)
        topic = data.get("topic", "").strip()
        if not topic:
            return jsonify({"success": False, "error": "Topic is required."}), 400

        context = retrieval_agent.get_context_string(topic) if retrieval_agent.is_ready else ""
        result = doubt_agent.get_learning_recommendations(topic, context)
        return jsonify({"success": True, "result": result})

    # ── Status / Health ──────────────────────────────────────
    @app.route("/api/status", methods=["GET"])
    def api_status():
        return jsonify(
            {
                "success": True,
                "ibm_configured": IBMConfig.is_configured(),
                "documents_loaded": len(doc_agent.get_document_info()),
                "knowledge_base_ready": retrieval_agent.is_ready,
                "chunk_count": retrieval_agent.chunk_count,
                "model": IBMConfig.CHAT_MODEL,
                "agent_instructions": AGENT_INSTRUCTIONS,
            }
        )

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"success": False, "error": "File too large. Maximum 50 MB."}), 413

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception("Internal server error: %s", e)
        return jsonify({"success": False, "error": "Internal server error."}), 500

    return app


# ─────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────
app = create_app()

if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    logger.info("Starting StudyGen AI on http://%s:%d  debug=%s", host, port, debug)
    app.run(host=host, port=port, debug=debug)
