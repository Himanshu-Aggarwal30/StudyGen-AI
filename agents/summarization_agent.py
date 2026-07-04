"""
agents/summarization_agent.py
Study Summarization Agent

Responsibilities:
  - Generate concise chapter / document summaries
  - Extract key points and exam notes
  - Identify important concepts
  - Produce revision-friendly content
"""

import logging
from config.ibm_config import generate_text, AGENT_INSTRUCTIONS

logger = logging.getLogger(__name__)

_STYLE = AGENT_INSTRUCTIONS["teaching_style"]
_DEPTH = AGENT_INSTRUCTIONS["explanation_depth"]
_FOCUS = AGENT_INSTRUCTIONS["exam_focus"]
_LEVEL = AGENT_INSTRUCTIONS["academic_level"]
_FORMAT = AGENT_INSTRUCTIONS["response_format"]


class SummarizationAgent:
    """
    Agent 3 – Study Summarization Agent

    Uses IBM Granite to produce structured summaries, key-point lists,
    and important-concept breakdowns from extracted document text.
    """

    # ── Public API ───────────────────────────────────────────

    def summarize(self, text: str, topic: str = "") -> str:
        """
        Generate a comprehensive study summary.

        Args:
            text:  Extracted document / chapter text.
            topic: Optional topic label for context.
        """
        topic_line = f"Topic: {topic}\n" if topic else ""
        prompt = f"""You are a Study Summarization Agent – an expert academic tutor.
Teaching style: {_STYLE}
Explanation depth: {_DEPTH}
Focus: {_FOCUS}
Academic level: {_LEVEL}
Response format: {_FORMAT}

{topic_line}Create a comprehensive study summary of the following text.
Include:
1. **Overview** – 2-3 sentence summary
2. **Key Concepts** – bullet list of the most important ideas
3. **Detailed Summary** – organised by theme or section
4. **Important Terms** – glossary of key vocabulary
5. **Exam Tips** – 3-5 points students should remember for exams

TEXT:
{text[:3000]}

SUMMARY:"""
        logger.info("SummarizationAgent: generating summary.")
        return generate_text(prompt)

    def extract_key_points(self, text: str) -> str:
        """Extract concise bullet-point key takeaways."""
        prompt = f"""You are a Study Summarization Agent.
Teaching style: {_STYLE}
Focus: {_FOCUS}

Extract the 10 most important key points from the following text.
Format each point as a numbered list item.
Be concise – max 2 sentences per point.
Highlight any terms that are likely to appear in exams.

TEXT:
{text[:2500]}

KEY POINTS:"""
        logger.info("SummarizationAgent: extracting key points.")
        return generate_text(prompt)

    def generate_revision_notes(self, text: str) -> str:
        """Create exam-focused revision notes."""
        prompt = f"""You are a Study Summarization Agent creating exam revision notes.
Teaching style: {_STYLE}
Focus: {_FOCUS}
Academic level: {_LEVEL}

Create concise revision notes from the text below.
Format:
## Quick Revision Notes

**Must-Know Concepts:** (bullet list)
**Key Definitions:** (term: definition pairs)
**Common Exam Questions:** (3 likely exam questions)
**Memory Tricks:** (mnemonics or associations if helpful)

TEXT:
{text[:2500]}

REVISION NOTES:"""
        logger.info("SummarizationAgent: generating revision notes.")
        return generate_text(prompt)

    def identify_important_topics(self, text: str) -> str:
        """Identify and rank the most important topics in the material."""
        prompt = f"""You are a Study Summarization Agent.
Focus: {_FOCUS}
Academic level: {_LEVEL}

Analyse the following text and identify the top 8 most important topics.
For each topic provide:
- Topic name
- Why it is important (1 sentence)
- Subtopics or related concepts

TEXT:
{text[:2500]}

IMPORTANT TOPICS:"""
        logger.info("SummarizationAgent: identifying important topics.")
        return generate_text(prompt)

    def generate_flashcards(self, text: str, count: int = 10) -> str:
        """
        Generate study flashcards from the text.

        Args:
            text:  Source text.
            count: Number of flashcards to generate.
        """
        flashcard_style = AGENT_INSTRUCTIONS["flashcard_style"]
        prompt = f"""You are a Study Summarization Agent creating flashcards.
Flashcard style: {flashcard_style}
Count: {count}

Generate exactly {count} study flashcards from the text below.
Format each card as:

**Card [N]**
FRONT: [question or term]
BACK: [answer or definition + 1 real-world example]

---

TEXT:
{text[:2500]}

FLASHCARDS:"""
        logger.info("SummarizationAgent: generating %d flashcards.", count)
        return generate_text(prompt)
