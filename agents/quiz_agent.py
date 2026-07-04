"""
agents/quiz_agent.py
Quiz Generation Agent

Responsibilities:
  - Generate Multiple Choice Questions (MCQ)
  - Generate short-answer questions
  - Generate long-answer / essay questions
  - Provide correct answers and explanations
"""

import logging
from config.ibm_config import generate_text, AGENT_INSTRUCTIONS

logger = logging.getLogger(__name__)

_STYLE = AGENT_INSTRUCTIONS["teaching_style"]
_QUIZ_DIFF = AGENT_INSTRUCTIONS["quiz_difficulty"]
_LEVEL = AGENT_INSTRUCTIONS["academic_level"]
_FOCUS = AGENT_INSTRUCTIONS["exam_focus"]


class QuizGenerationAgent:
    """
    Agent 4 – Quiz Generation Agent

    Uses IBM Granite to create varied question types grounded in the
    uploaded study material retrieved by the RAG pipeline.
    """

    # ── Public API ───────────────────────────────────────────

    def generate_mcq(self, context: str, topic: str = "", count: int = 5) -> str:
        """
        Generate Multiple Choice Questions.

        Args:
            context: Retrieved or full document text.
            topic:   Optional topic label.
            count:   Number of questions.
        """
        topic_line = f"Topic: {topic}\n" if topic else ""
        prompt = f"""You are a Quiz Generation Agent specialising in MCQ creation.
Difficulty: {_QUIZ_DIFF}
Academic level: {_LEVEL}
Focus: {_FOCUS}

{topic_line}Generate exactly {count} multiple-choice questions based on the text below.

Format each question strictly as:

**Q[N]. [Question text]**
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
✅ Correct Answer: [Letter] – [Brief explanation]

---

TEXT:
{context[:2500]}

MCQ QUESTIONS:"""
        logger.info("QuizAgent: generating %d MCQs.", count)
        return generate_text(prompt)

    def generate_short_answer(self, context: str, topic: str = "", count: int = 5) -> str:
        """Generate short-answer questions with model answers."""
        topic_line = f"Topic: {topic}\n" if topic else ""
        prompt = f"""You are a Quiz Generation Agent.
Difficulty: {_QUIZ_DIFF}
Academic level: {_LEVEL}
Focus: {_FOCUS}

{topic_line}Generate exactly {count} short-answer questions based on the text.
Each question should require a 2-4 sentence answer.

Format:

**Q[N]. [Question]**
📝 Model Answer: [Concise answer in 2-4 sentences]

---

TEXT:
{context[:2500]}

SHORT-ANSWER QUESTIONS:"""
        logger.info("QuizAgent: generating %d short-answer questions.", count)
        return generate_text(prompt)

    def generate_long_answer(self, context: str, topic: str = "", count: int = 3) -> str:
        """Generate essay / long-answer questions with outline answers."""
        topic_line = f"Topic: {topic}\n" if topic else ""
        prompt = f"""You are a Quiz Generation Agent.
Difficulty: {_QUIZ_DIFF}
Academic level: {_LEVEL}
Focus: {_FOCUS}

{topic_line}Generate exactly {count} long-answer / essay questions based on the text.
These should test deep understanding and critical thinking.

Format:

**Q[N]. [Question]** (Marks: 10)
📋 Outline Answer:
- Introduction: [1-2 key points]
- Main Body: [4-5 key arguments/points]
- Conclusion: [1-2 wrapping points]

---

TEXT:
{context[:2500]}

LONG-ANSWER QUESTIONS:"""
        logger.info("QuizAgent: generating %d long-answer questions.", count)
        return generate_text(prompt)

    def generate_mixed_quiz(
        self, context: str, topic: str = "", mcq: int = 5, short: int = 3, long: int = 2
    ) -> dict:
        """
        Generate a complete mixed quiz with all question types.

        Returns a dict with keys: mcq, short_answer, long_answer.
        """
        logger.info("QuizAgent: generating full mixed quiz.")
        return {
            "mcq": self.generate_mcq(context, topic, mcq),
            "short_answer": self.generate_short_answer(context, topic, short),
            "long_answer": self.generate_long_answer(context, topic, long),
        }

    def evaluate_answer(self, question: str, student_answer: str, model_answer: str) -> str:
        """
        Evaluate a student's answer against the model answer.

        Args:
            question:       The original question.
            student_answer: What the student wrote.
            model_answer:   Reference / correct answer.
        """
        prompt = f"""You are a Quiz Generation Agent acting as a fair examiner.
Teaching style: {_STYLE}
Academic level: {_LEVEL}

Evaluate the student's answer below.

QUESTION: {question}
MODEL ANSWER: {model_answer}
STUDENT ANSWER: {student_answer}

Provide:
1. **Score** – X / 10
2. **Feedback** – what was correct and what was missed
3. **Improvement Tips** – how the student can improve their answer
4. **Key Points Missed** – any critical concepts not addressed

EVALUATION:"""
        logger.info("QuizAgent: evaluating student answer.")
        return generate_text(prompt)
