"""
agents/retrieval_agent.py
Knowledge Retrieval Agent

Responsibilities:
  - Maintain and query the FAISS vector index
  - Retrieve relevant context for all other agents
  - Provide grounded information from uploaded study materials
  - Act as the RAG intermediary in the multi-agent pipeline
"""

import logging
from typing import List, Optional

from rag.rag_engine import RAGEngine

logger = logging.getLogger(__name__)


class KnowledgeRetrievalAgent:
    """
    Agent 2 – Knowledge Retrieval Agent

    Wraps the RAGEngine and exposes a clean interface that other
    agents call to get grounded context before invoking Granite.
    """

    def __init__(self, top_k: int = 5):
        self._engine = RAGEngine(top_k=top_k)
        logger.info("KnowledgeRetrievalAgent initialised (top_k=%d).", top_k)

    # ── Public API ───────────────────────────────────────────

    def build_knowledge_base(self, chunks: List[str]) -> dict:
        """
        Build the vector index from document chunks.

        Args:
            chunks: Text chunks produced by the DocumentProcessingAgent.

        Returns:
            Status dict with success flag and chunk count.
        """
        if not chunks:
            return {"success": False, "error": "No chunks provided.", "chunk_count": 0}

        success = self._engine.build_index(chunks)
        self._engine.save_index()

        return {
            "success": success,
            "chunk_count": self._engine.chunk_count,
            "message": (
                f"Knowledge base built with {self._engine.chunk_count} chunks."
                if success
                else "Index build failed – keyword fallback active."
            ),
        }

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[str]:
        """
        Retrieve the most relevant chunks for a query.

        Args:
            query: Student question or generation topic.
            top_k: Override the default top-k.

        Returns:
            List of relevant text chunks.
        """
        if not self._engine.is_ready:
            logger.warning(
                "KnowledgeRetrievalAgent: index not ready – returning empty context."
            )
            return []
        return self._engine.search(query, top_k)

    def get_context_string(self, query: str, top_k: Optional[int] = None) -> str:
        """
        Return retrieved chunks as a single context string for prompt injection.

        Args:
            query: The search query.
            top_k: Override the default top-k.
        """
        return self._engine.get_context(query, top_k)

    def load_existing_index(self) -> bool:
        """
        Attempt to load a previously persisted FAISS index.

        Returns True if successfully loaded.
        """
        loaded = self._engine.load_index()
        if loaded:
            logger.info(
                "KnowledgeRetrievalAgent: loaded existing index (%d chunks).",
                self._engine.chunk_count,
            )
        return loaded

    @property
    def is_ready(self) -> bool:
        """True once the knowledge base has been built or loaded."""
        return self._engine.is_ready

    @property
    def chunk_count(self) -> int:
        return self._engine.chunk_count
