"""
config/ibm_config.py
IBM watsonx.ai configuration and client initialisation module.

All IBM-specific settings live here so agents import a single
clean interface rather than scattering credential logic.
"""

import os
import logging
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
#  AGENT INSTRUCTIONS
#  Customise teaching style, difficulty, and safety rules here
#  without touching any agent logic.
# ─────────────────────────────────────────────────────────────
AGENT_INSTRUCTIONS = {
    # How the AI explains concepts to students
    "teaching_style": "clear, encouraging, and student-friendly",

    # How deep should explanations be?  shallow | medium | deep
    "explanation_depth": "medium",

    # Target difficulty: beginner | intermediate | advanced
    "difficulty_level": "intermediate",

    # Focus area for all content generation
    "exam_focus": "exam-oriented with key concepts highlighted",

    # Academic level context
    "academic_level": "undergraduate university level",

    # Safety rules – model must always follow these
    "safety_rules": (
        "Never generate harmful content. "
        "Always be respectful and inclusive. "
        "Do not fabricate facts – base answers on provided material."
    ),

    # Preferred response format
    "response_format": "structured with headings, bullet points, and examples",

    # Quiz generation defaults
    "quiz_difficulty": "moderate – mix of recall and application questions",

    # Study planning strategy
    "study_planning_strategy": (
        "spaced repetition with interleaved practice and regular revision breaks"
    ),

    # Flashcard style
    "flashcard_style": "concise front, detailed back with a real-world example",
}


# ─────────────────────────────────────────────────────────────
#  IBM watsonx.ai configuration
# ─────────────────────────────────────────────────────────────
class IBMConfig:
    """Centralised IBM watsonx.ai configuration."""

    API_KEY: str = os.getenv("IBM_WATSONX_API_KEY", "")
    PROJECT_ID: str = os.getenv("IBM_WATSONX_PROJECT_ID", "")
    URL: str = os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com")

    # Model IDs
    CHAT_MODEL: str = os.getenv("GRANITE_CHAT_MODEL", "ibm/granite-4-h-small")
    EMBEDDING_MODEL: str = os.getenv(
        "GRANITE_EMBEDDING_MODEL", "ibm/slate-125m-english-rtrvr"
    )

    # Generation parameters – tuned for study content
    GENERATION_PARAMS: dict = {
        "max_new_tokens": 1500,
        "min_new_tokens": 50,
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 50,
        "repetition_penalty": 1.1,
    }

    # Conservative params for factual Q&A (RAG)
    RAG_PARAMS: dict = {
        "max_new_tokens": 1200,
        "min_new_tokens": 30,
        "temperature": 0.3,
        "top_p": 0.85,
        "top_k": 40,
        "repetition_penalty": 1.05,
    }

    @classmethod
    def is_configured(cls) -> bool:
        """Return True when mandatory credentials are present."""
        return bool(cls.API_KEY and cls.PROJECT_ID)

    @classmethod
    def validate(cls) -> None:
        """Raise if credentials are missing."""
        if not cls.API_KEY:
            raise EnvironmentError(
                "IBM_WATSONX_API_KEY is not set. "
                "Copy .env.example → .env and fill in your credentials."
            )
        if not cls.PROJECT_ID:
            raise EnvironmentError(
                "IBM_WATSONX_PROJECT_ID is not set. "
                "Copy .env.example → .env and fill in your credentials."
            )


@lru_cache(maxsize=1)
def get_watsonx_client():
    """
    Return a cached ibm_watsonx_ai Credentials object.
    Uses lru_cache so the heavy import + auth only happens once.
    """
    try:
        from ibm_watsonx_ai import Credentials  # type: ignore

        IBMConfig.validate()
        creds = Credentials(url=IBMConfig.URL, api_key=IBMConfig.API_KEY)
        logger.info("IBM watsonx.ai client initialised successfully.")
        return creds
    except ImportError as exc:
        logger.error("ibm-watsonx-ai package not installed: %s", exc)
        raise
    except EnvironmentError as exc:
        logger.error("IBM credential error: %s", exc)
        raise


@lru_cache(maxsize=1)
def get_model_inference():
    """
    Return a cached ModelInference instance for text generation.
    """
    try:
        from ibm_watsonx_ai.foundation_models import ModelInference  # type: ignore
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams  # type: ignore

        creds = get_watsonx_client()
        params = {
            GenParams.MAX_NEW_TOKENS: IBMConfig.GENERATION_PARAMS["max_new_tokens"],
            GenParams.MIN_NEW_TOKENS: IBMConfig.GENERATION_PARAMS["min_new_tokens"],
            GenParams.TEMPERATURE: IBMConfig.GENERATION_PARAMS["temperature"],
            GenParams.TOP_P: IBMConfig.GENERATION_PARAMS["top_p"],
            GenParams.TOP_K: IBMConfig.GENERATION_PARAMS["top_k"],
            GenParams.REPETITION_PENALTY: IBMConfig.GENERATION_PARAMS["repetition_penalty"],
        }
        model = ModelInference(
            model_id=IBMConfig.CHAT_MODEL,
            credentials=creds,
            project_id=IBMConfig.PROJECT_ID,
            params=params,
        )
        logger.info("Granite model '%s' loaded.", IBMConfig.CHAT_MODEL)
        return model
    except Exception as exc:
        logger.error("Failed to load Granite model: %s", exc)
        raise


def generate_text(prompt: str, rag_mode: bool = False) -> str:
    """
    Convenience wrapper – generate text using the Granite model.

    Args:
        prompt:   Full prompt string.
        rag_mode: Use conservative RAG params when True.

    Returns:
        Generated text string.
    """
    try:
        from ibm_watsonx_ai.foundation_models import ModelInference  # type: ignore
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams  # type: ignore

        creds = get_watsonx_client()
        params_src = IBMConfig.RAG_PARAMS if rag_mode else IBMConfig.GENERATION_PARAMS
        params = {
            GenParams.MAX_NEW_TOKENS: params_src["max_new_tokens"],
            GenParams.MIN_NEW_TOKENS: params_src["min_new_tokens"],
            GenParams.TEMPERATURE: params_src["temperature"],
            GenParams.TOP_P: params_src["top_p"],
            GenParams.TOP_K: params_src["top_k"],
            GenParams.REPETITION_PENALTY: params_src["repetition_penalty"],
        }
        model = ModelInference(
            model_id=IBMConfig.CHAT_MODEL,
            credentials=creds,
            project_id=IBMConfig.PROJECT_ID,
            params=params,
        )
        response = model.generate_text(prompt=prompt)
        return response.strip() if response else ""
    except Exception as exc:
        logger.error("Text generation error: %s", exc)
        return f"[Generation Error] {str(exc)}"
