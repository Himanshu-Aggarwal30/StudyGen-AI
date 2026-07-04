"""
rag/rag_engine.py
Retrieval-Augmented Generation (RAG) Engine

Builds a FAISS vector index from document chunks and performs
semantic similarity search to retrieve relevant context before
passing it to Granite for grounded answer generation.
"""

import os
import logging
import pickle
from pathlib import Path
from typing import List, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ── Optional heavy dependencies ───────────────────────────────
try:
    import faiss  # type: ignore
    _FAISS_AVAILABLE = True
except ImportError:
    _FAISS_AVAILABLE = False
    logger.warning("FAISS not available – falling back to keyword search.")

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    _SBERT_AVAILABLE = True
except ImportError:
    _SBERT_AVAILABLE = False
    logger.warning("sentence-transformers not available – falling back to keyword search.")


class RAGEngine:
    """
    Manages the FAISS index lifecycle:
      build()     – embed all chunks and create the index
      search()    – retrieve top-k most relevant chunks
      save/load() – persist the index to disk
    """

    _EMBED_MODEL = "all-MiniLM-L6-v2"   # lightweight, fast, good quality

    def __init__(
        self,
        index_path: str | None = None,
        top_k: int | None = None,
    ):
        self.index_path = Path(
            index_path or os.getenv("FAISS_INDEX_PATH", "data/faiss_index")
        )
        self.top_k = int(top_k or os.getenv("TOP_K_RESULTS", 5))
        self._chunks: List[str] = []
        self._index = None
        self._embedder = None
        self._ready = False

    # ── Public API ───────────────────────────────────────────

    def build_index(self, chunks: List[str]) -> bool:
        """
        Embed all chunks and build a FAISS flat-L2 index.

        Returns True on success, False on failure (falls back silently).
        """
        if not chunks:
            logger.warning("RAGEngine: no chunks provided – index not built.")
            return False

        self._chunks = chunks

        if not (_FAISS_AVAILABLE and _SBERT_AVAILABLE):
            logger.warning("RAGEngine: running in keyword-fallback mode.")
            self._ready = True   # keyword search still works
            return True

        try:
            embedder = self._get_embedder()
            logger.info("RAGEngine: embedding %d chunks…", len(chunks))
            vectors = embedder.encode(chunks, show_progress_bar=False, batch_size=64)
            vectors = np.array(vectors, dtype="float32")
            faiss.normalize_L2(vectors)

            dim = vectors.shape[1]
            index = faiss.IndexFlatIP(dim)   # inner-product (cosine after L2-norm)
            index.add(vectors)               # type: ignore[attr-defined]

            self._index = index
            self._ready = True
            logger.info("RAGEngine: FAISS index built with %d vectors (dim=%d).", len(chunks), dim)
            return True
        except Exception as exc:
            logger.exception("RAGEngine: failed to build FAISS index: %s", exc)
            self._ready = True   # allow keyword fallback
            return False

    def search(self, query: str, top_k: int | None = None) -> List[str]:
        """
        Retrieve the top-k most relevant chunks for query.

        Falls back to keyword matching when FAISS is unavailable.
        """
        k = top_k or self.top_k
        if not self._ready or not self._chunks:
            return []

        if self._index is not None and _FAISS_AVAILABLE and _SBERT_AVAILABLE:
            return self._faiss_search(query, k)
        return self._keyword_search(query, k)

    def get_context(self, query: str, top_k: int | None = None) -> str:
        """
        Convenience method – return retrieved chunks joined as a string
        suitable for injection into a prompt.
        """
        chunks = self.search(query, top_k)
        if not chunks:
            return ""
        return "\n\n---\n\n".join(chunks)

    def save_index(self) -> bool:
        """Persist the FAISS index and chunk list to disk."""
        if not self._ready:
            return False
        try:
            self.index_path.mkdir(parents=True, exist_ok=True)
            # Save chunk list
            with open(self.index_path / "chunks.pkl", "wb") as fh:
                pickle.dump(self._chunks, fh)
            # Save FAISS index if available
            if self._index is not None and _FAISS_AVAILABLE:
                faiss.write_index(self._index, str(self.index_path / "index.faiss"))
            logger.info("RAGEngine: index saved to '%s'.", self.index_path)
            return True
        except Exception as exc:
            logger.exception("RAGEngine: failed to save index: %s", exc)
            return False

    def load_index(self) -> bool:
        """Load a previously saved FAISS index from disk."""
        try:
            chunks_file = self.index_path / "chunks.pkl"
            index_file = self.index_path / "index.faiss"
            if not chunks_file.exists():
                return False
            with open(chunks_file, "rb") as fh:
                self._chunks = pickle.load(fh)
            if index_file.exists() and _FAISS_AVAILABLE:
                self._index = faiss.read_index(str(index_file))
            self._ready = True
            logger.info(
                "RAGEngine: loaded index with %d chunks from '%s'.",
                len(self._chunks),
                self.index_path,
            )
            return True
        except Exception as exc:
            logger.exception("RAGEngine: failed to load index: %s", exc)
            return False

    @property
    def is_ready(self) -> bool:
        return self._ready

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    # ── Private helpers ──────────────────────────────────────

    def _get_embedder(self):
        if self._embedder is None:
            logger.info("RAGEngine: loading SentenceTransformer '%s'…", self._EMBED_MODEL)
            self._embedder = SentenceTransformer(self._EMBED_MODEL)
        return self._embedder

    def _faiss_search(self, query: str, k: int) -> List[str]:
        embedder = self._get_embedder()
        q_vec = embedder.encode([query], show_progress_bar=False)
        q_vec = np.array(q_vec, dtype="float32")
        faiss.normalize_L2(q_vec)
        distances, indices = self._index.search(q_vec, min(k, len(self._chunks)))  # type: ignore[attr-defined]
        results = []
        for idx in indices[0]:
            if 0 <= idx < len(self._chunks):
                results.append(self._chunks[idx])
        return results

    def _keyword_search(self, query: str, k: int) -> List[str]:
        """Simple TF-style keyword overlap fallback."""
        query_words = set(query.lower().split())
        scored: List[Tuple[float, str]] = []
        for chunk in self._chunks:
            chunk_words = set(chunk.lower().split())
            score = len(query_words & chunk_words) / (len(query_words) + 1e-9)
            scored.append((score, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:k] if _ > 0]
