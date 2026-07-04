# StudyGen AI – Agentic Smart Study Assistant

> **Powered by IBM watsonx.ai Granite models**  
> A production-ready, multi-agent AI application that helps students learn smarter from uploaded study materials.

---

## 📋 Project Overview

StudyGen AI is an intelligent study assistant built with **Python Flask** and **IBM watsonx.ai**. Students upload PDF study materials (textbooks, notes, lecture slides) and six specialised AI agents collaborate to:

- 📄 Extract and index document content
- 💡 Generate concise summaries and key points
- ❓ Create practice quizzes (MCQ, short, long answer)
- 🗓️ Build personalised study schedules
- 💬 Answer doubts in student-friendly language
- 🃏 Generate revision flashcards

All AI outputs are **grounded in uploaded documents** via a FAISS-based Retrieval-Augmented Generation (RAG) pipeline.

---

## 🤖 Agentic AI Architecture

StudyGen AI implements **6 specialised agents** that collaborate through a shared knowledge base:

```
PDF Upload
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Agent 1: Document Processing Agent                         │
│  • Extracts text from PDFs (pdfplumber / PyPDF2)            │
│  • Cleans and normalises content                            │
│  • Splits into retrieval-friendly chunks                     │
└───────────────────────┬─────────────────────────────────────┘
                        │ chunks
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Agent 2: Knowledge Retrieval Agent (RAG)                   │
│  • Embeds chunks using SentenceTransformers                 │
│  • Builds FAISS vector index                                │
│  • Retrieves top-k relevant chunks per query                │
└────┬──────────┬──────────┬──────────┬──────────┬───────────┘
     │ context  │ context  │ context  │ context  │ context
     ▼          ▼          ▼          ▼          ▼
  Agent 3    Agent 4    Agent 5    Agent 6
  Summary    Quiz       Planner    Doubt Solver
  Agent      Agent      Agent      Agent
     │          │          │          │
     └──────────┴──────────┴──────────┘
                        │
                        ▼
              IBM Granite (watsonx.ai)
              ibm/granite-4-h-small
```

### Agent Responsibilities

| Agent | Name | Responsibility |
|-------|------|----------------|
| 1 | **DocumentProcessingAgent** | PDF upload, text extraction, chunking |
| 2 | **KnowledgeRetrievalAgent** | FAISS index management, semantic search |
| 3 | **SummarizationAgent** | Summaries, key points, revision notes, flashcards |
| 4 | **QuizGenerationAgent** | MCQ, short-answer, long-answer, answer evaluation |
| 5 | **StudyPlannerAgent** | Study plans, weekly schedules, exam tips, checklists |
| 6 | **DoubtSolvingAgent** | RAG-grounded Q&A, concept explanations, recommendations |

---

## 🧠 IBM Granite Usage

| Feature | Model Used |
|---------|-----------|
| Text Generation (all agents) | `ibm/granite-4-h-small` |
| Embeddings (RAG pipeline) | SentenceTransformers `all-MiniLM-L6-v2` (local) |

All generation goes through `config/ibm_config.py` which provides:
- Centralised credential management
- Two generation parameter profiles (standard + RAG-conservative)
- Cached `ModelInference` instances via `@lru_cache`
- `AGENT_INSTRUCTIONS` dict for customising teaching style, difficulty, and exam focus

---

## 📁 Project Structure

```
StudyGen AI/
├── app.py                          # Flask application & routes
├── requirements.txt
├── .env.example                    # Environment template
├── README.md
│
├── config/
│   ├── __init__.py
│   └── ibm_config.py               # IBM watsonx.ai config + AGENT_INSTRUCTIONS
│
├── agents/
│   ├── __init__.py
│   ├── document_agent.py           # Agent 1 – PDF processing
│   ├── retrieval_agent.py          # Agent 2 – Knowledge retrieval
│   ├── summarization_agent.py      # Agent 3 – Summaries
│   ├── quiz_agent.py               # Agent 4 – Quiz generation
│   ├── planner_agent.py            # Agent 5 – Study planning
│   └── doubt_solver_agent.py       # Agent 6 – Doubt solving
│
├── rag/
│   ├── __init__.py
│   └── rag_engine.py               # FAISS vector index + search
│
├── templates/
│   ├── base.html                   # Layout with navbar, dark mode
│   ├── index.html                  # Landing page
│   ├── dashboard.html              # Student dashboard
│   ├── upload.html                 # PDF upload page
│   ├── chat.html                   # AI tutor chat
│   ├── summary.html                # Summarization page
│   ├── quiz.html                   # Quiz generator page
│   ├── planner.html                # Study planner page
│   └── flashcards.html             # Flashcard generator
│
├── static/
│   ├── css/
│   │   └── studygen.css            # Custom stylesheet + dark mode
│   └── js/
│       ├── studygen.js             # Global utilities, dark mode
│       ├── upload.js               # Upload page logic
│       ├── chat.js                 # Chat interface
│       ├── summary.js              # Summary page logic
│       ├── quiz.js                 # Quiz page logic
│       ├── planner.js              # Planner page logic
│       └── flashcards.js           # Flashcard page logic
│
├── uploads/                        # Uploaded PDFs (auto-created)
└── data/
    └── faiss_index/                # Persisted FAISS index (auto-created)
```

---

## 🚀 Installation Steps

### Prerequisites

- Python 3.10 or 3.11
- An [IBM Cloud account](https://cloud.ibm.com/) with Watson Machine Learning service
- An IBM watsonx.ai project

### 1. Clone / Download the project

```bash
cd "StudyGen AI"
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** Install `faiss-cpu` (not `faiss-gpu` unless you have CUDA). The AVX2 warning on startup (`Could not load library with AVX2 support`) is harmless — FAISS falls back to the standard build automatically.

---

## ⚙️ Environment Setup

### 1. Copy the environment template

```bash
cp .env.example .env
```

### 2. Fill in your IBM credentials in `.env`

```env
IBM_WATSONX_API_KEY=your_api_key_here
IBM_WATSONX_PROJECT_ID=your_project_id_here
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com

GRANITE_CHAT_MODEL=ibm/granite-4-h-small
GRANITE_EMBEDDING_MODEL=ibm/slate-125m-english-rtrvr-v2
FLASK_SECRET_KEY=some-random-secret-string
```

#### How to get IBM watsonx.ai credentials

1. Go to [IBM Cloud](https://cloud.ibm.com/) → Create a **Watson Machine Learning** service
2. Under **Manage** → **Access (IAM)** → **API keys**, create a new API key
3. Open [watsonx.ai](https://dataplatform.cloud.ibm.com/wx/home) → Create or open a **Project**
4. Copy the **Project ID** from the project settings

---

## ▶️ Running the Application

```bash
python app.py
```

The application will start at **http://localhost:5000**

### Production (Gunicorn)

```bash
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

---

## 🎯 Usage Guide

1. **Upload a PDF** → Go to `/upload`, drop your study material
2. **Summarize** → `/summary` → Choose Full Summary, Key Points, Revision Notes, or Important Topics
3. **Generate Quiz** → `/quiz` → Select question type (MCQ/Short/Long/Mixed) and topic
4. **Chat with AI Tutor** → `/chat` → Ask questions grounded in your document
5. **Flashcards** → `/flashcards` → Generate and flip through study cards
6. **Study Planner** → `/planner` → Enter exam date, hours, and subjects for a personalised plan

---

## 🔧 Agent Customisation

Edit `AGENT_INSTRUCTIONS` in [`config/ibm_config.py`](config/ibm_config.py) to customise:

| Setting | Default | Options |
|---------|---------|---------|
| `teaching_style` | clear, encouraging | formal, Socratic, visual |
| `explanation_depth` | medium | shallow, deep |
| `difficulty_level` | intermediate | beginner, advanced |
| `exam_focus` | exam-oriented | conceptual, applied |
| `academic_level` | undergraduate | high school, postgraduate |
| `quiz_difficulty` | moderate | easy, hard |
| `study_planning_strategy` | spaced repetition | intensive, marathon |
| `flashcard_style` | concise front, detailed back | Q&A, definition |

---

## 🔌 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /api/upload` | multipart/form-data | Upload and process PDF |
| `GET  /api/documents` | – | List loaded documents |
| `POST /api/chat` | JSON | Send message to AI tutor |
| `POST /api/summarize` | JSON | Generate summary/key points |
| `POST /api/flashcards` | JSON | Generate flashcard set |
| `POST /api/quiz` | JSON | Generate quiz questions |
| `POST /api/evaluate` | JSON | Evaluate a student answer |
| `POST /api/planner` | JSON | Generate study plan |
| `POST /api/explain` | JSON | Explain a concept |
| `POST /api/recommendations` | JSON | Learning recommendations |
| `GET  /api/status` | – | System health & config status |

---

## 🔭 Future Scope

- **Multi-document RAG** – Cross-document question answering
- **Voice Interface** – Speech-to-text input for the AI tutor
- **Student Progress Tracking** – Quiz history, scores, and analytics dashboard
- **Collaborative Study** – Multi-user shared document spaces
- **Exam Simulation Mode** – Timed mock exams with automatic grading
- **Multi-language Support** – Study materials in multiple languages
- **Mobile App** – React Native / Flutter companion app
- **LangGraph Integration** – Formal agent orchestration with state graphs
- **IBM watsonx.governance** – Responsible AI guardrails and bias monitoring
- **Cloud Deployment** – One-click IBM Code Engine / Red Hat OpenShift deploy

---

## 🛡️ Security Notes

- API keys are loaded from `.env` only – never committed to version control
- File uploads are validated (PDF-only, 50 MB max) and stored with UUID-prefixed names
- `werkzeug.utils.secure_filename` sanitises all filenames

---

## 📄 License

MIT License – See [LICENSE](LICENSE) for details.

---

*Built with ❤️ using IBM watsonx.ai Granite · Flask · FAISS · SentenceTransformers · Bootstrap 5*
