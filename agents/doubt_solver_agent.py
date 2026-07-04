"""
agents/doubt_solver_agent.py
Doubt Solving Agent

Responsibilities:
  - Answer student questions using uploaded study material (RAG-grounded)
  - Provide student-friendly, clear explanations
  - Break down complex topics into simple language
  - Suggest follow-up learning resources
"""

import logging
from config.ibm_config import generate_text, AGENT_INSTRUCTIONS

logger = logging.getLogger(__name__)

_STYLE = AGENT_INSTRUCTIONS["teaching_style"]
_DEPTH = AGENT_INSTRUCTIONS["explanation_depth"]
_LEVEL = AGENT_INSTRUCTIONS["academic_level"]
_SAFETY = AGENT_INSTRUCTIONS["safety_rules"]
_FORMAT = AGENT_INSTRUCTIONS["response_format"]


class DoubtSolvingAgent:
    """
    Agent 6 – Doubt Solving Agent

    The conversational face of StudyGen AI.  Receives questions from
    students, enriched with retrieved context from the RAG pipeline,
    and produces clear, grounded explanations using IBM Granite.
    """

    # ── Public API ───────────────────────────────────────────

    def answer_question(
        self,
        question: str,
        context: str = "",
        chat_history: list | None = None,
    ) -> str:
        """
        Answer a student's question, optionally grounded in retrieved context.

        Args:
            question:     The student's question.
            context:      Retrieved RAG context (may be empty).
            chat_history: Previous turns [(role, message), …] for multi-turn.
        """
        history_block = ""
        if chat_history:
            history_lines = []
            for role, msg in chat_history[-6:]:   # keep last 6 turns
                prefix = "Student" if role == "user" else "AI Tutor"
                history_lines.append(f"{prefix}: {msg}")
            history_block = "\n".join(history_lines) + "\n\n"

        context_block = (
            f"RELEVANT STUDY MATERIAL:\n{context}\n\n" if context else ""
        )

        prompt = f"""You are a Doubt Solving Agent – a friendly, expert AI tutor.
Teaching style: {_STYLE}
Explanation depth: {_DEPTH}
Academic level: {_LEVEL}
Safety rules: {_SAFETY}
Response format: {_FORMAT}

{context_block}{history_block}Student Question: {question}

Provide a helpful, accurate, and encouraging answer.
If the question relates to the provided study material, ground your answer in it.
If unsure, say so honestly rather than guessing.

AI Tutor Answer:"""
        logger.info("DoubtSolvingAgent: answering question.")
        return generate_text(prompt, rag_mode=bool(context))

    def explain_concept(self, concept: str, context: str = "") -> str:
        """
        Explain a concept in simple, student-friendly language.

        Args:
            concept: The concept to explain.
            context: Optional surrounding context from the material.
        """
        context_block = (
            f"Context from study material:\n{context}\n\n" if context else ""
        )
        prompt = f"""You are a Doubt Solving Agent.
Teaching style: {_STYLE}
Explanation depth: {_DEPTH}
Academic level: {_LEVEL}

{context_block}Explain the following concept clearly and simply:

CONCEPT: {concept}

Your explanation must:
1. Start with a simple 1-sentence definition
2. Explain WHY it is important
3. Give a real-world analogy or example
4. Break it down step by step if it is a process
5. End with a "Common Misconceptions" note if applicable

EXPLANATION:"""
        logger.info("DoubtSolvingAgent: explaining concept '%s'.", concept)
        return generate_text(prompt)

    def simplify_text(self, text: str, target_level: str = "beginner") -> str:
        """
        Rewrite a complex passage in simpler language.

        Args:
            text:         Complex text to simplify.
            target_level: "beginner" | "intermediate".
        """
        prompt = f"""You are a Doubt Solving Agent who excels at simplifying complex text.
Target level: {target_level}
Teaching style: {_STYLE}

Rewrite the following text so a {target_level} student can easily understand it.
- Use simple vocabulary
- Break long sentences
- Add analogies where helpful
- Keep all key information

ORIGINAL TEXT:
{text[:2000]}

SIMPLIFIED VERSION:"""
        logger.info("DoubtSolvingAgent: simplifying text to '%s' level.", target_level)
        return generate_text(prompt)

    def get_learning_recommendations(self, topic: str, context: str = "") -> str:
        """
        Suggest further reading and learning strategies for a topic.

        Args:
            topic:   The topic the student is studying.
            context: Optional document context.
        """
        context_block = (
            f"Context:\n{context[:1000]}\n\n" if context else ""
        )
        prompt = f"""You are a Doubt Solving Agent and learning coach.
Academic level: {_LEVEL}
Teaching style: {_STYLE}

{context_block}The student is studying: {topic}

Provide personalised learning recommendations:
1. **Next Steps** – what to study after mastering this topic
2. **Study Techniques** – best methods for this type of content
3. **Practice Resources** – types of exercises to do (no external URLs)
4. **Common Pitfalls** – what students struggle with and how to overcome it
5. **Self-Assessment** – 3 questions to test their own understanding

LEARNING RECOMMENDATIONS:"""
        logger.info(
            "DoubtSolvingAgent: generating learning recommendations for '%s'.", topic
        )
        return generate_text(prompt)
