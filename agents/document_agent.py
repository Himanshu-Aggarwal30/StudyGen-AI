"""
agents/document_agent.py
Document Processing Agent

Responsibilities:
  - Accept uploaded PDF files
  - Extract and clean raw text
  - Split text into retrieval-friendly chunks
  - Persist chunks for the RAG pipeline
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# ── Optional rich PDF extraction (falls back to PyPDF2) ──────
try:
    import pdfplumber  # type: ignore
    _PDFPLUMBER_AVAILABLE = True
except ImportError:
    _PDFPLUMBER_AVAILABLE = False

try:
    import PyPDF2  # type: ignore
    _PYPDF2_AVAILABLE = True
except ImportError:
    _PYPDF2_AVAILABLE = False


class DocumentProcessingAgent:
    """
    Agent 1 – Document Processing Agent

    Handles PDF ingestion, text extraction, cleaning, and chunking.
    The resulting chunks are consumed by the RAG pipeline.
    """

    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
        upload_folder: str = "uploads",
    ):
        self.chunk_size = int(os.getenv("CHUNK_SIZE", chunk_size))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", chunk_overlap))
        self.upload_folder = Path(os.getenv("UPLOAD_FOLDER", upload_folder))
        self.upload_folder.mkdir(parents=True, exist_ok=True)
        self._documents: Dict[str, dict] = {}   # filename → metadata + chunks
        logger.info(
            "DocumentProcessingAgent ready (chunk_size=%d, overlap=%d).",
            self.chunk_size,
            self.chunk_overlap,
        )

    # ── Public API ───────────────────────────────────────────

    def process_pdf(self, file_path: str, filename: str) -> dict:
        """
        Full pipeline: extract → clean → chunk → store.

        Returns a result dict with status, chunk count, and preview.
        """
        logger.info("Processing document: %s", filename)
        try:
            raw_text = self._extract_text(file_path)
            if not raw_text.strip():
                return {
                    "success": False,
                    "error": "No text could be extracted from the PDF.",
                    "filename": filename,
                }
            cleaned = self._clean_text(raw_text)
            chunks = self._split_into_chunks(cleaned)
            self._documents[filename] = {
                "filename": filename,
                "file_path": file_path,
                "full_text": cleaned,
                "chunks": chunks,
                "total_chunks": len(chunks),
                "char_count": len(cleaned),
                "word_count": len(cleaned.split()),
            }
            logger.info(
                "Document '%s' processed: %d chunks, %d words.",
                filename,
                len(chunks),
                len(cleaned.split()),
            )
            return {
                "success": True,
                "filename": filename,
                "total_chunks": len(chunks),
                "word_count": len(cleaned.split()),
                "char_count": len(cleaned),
                "preview": cleaned[:400] + "…" if len(cleaned) > 400 else cleaned,
            }
        except Exception as exc:
            logger.exception("Error processing '%s': %s", filename, exc)
            return {"success": False, "error": str(exc), "filename": filename}

    def get_all_chunks(self) -> List[str]:
        """Return flat list of all text chunks across all documents."""
        return [
            chunk
            for doc in self._documents.values()
            for chunk in doc["chunks"]
        ]

    def get_document_info(self) -> List[dict]:
        """Return lightweight metadata for each loaded document."""
        return [
            {
                "filename": d["filename"],
                "total_chunks": d["total_chunks"],
                "word_count": d["word_count"],
            }
            for d in self._documents.values()
        ]

    def get_full_text(self, filename: Optional[str] = None) -> str:
        """
        Return full text for a named document, or concatenate all
        documents when filename is None.
        """
        if filename and filename in self._documents:
            return self._documents[filename]["full_text"]
        return "\n\n---\n\n".join(
            d["full_text"] for d in self._documents.values()
        )

    def clear(self) -> None:
        """Remove all in-memory documents."""
        self._documents.clear()
        logger.info("DocumentProcessingAgent memory cleared.")

    # ── Private helpers ──────────────────────────────────────

    def _extract_text(self, file_path: str) -> str:
        """Try pdfplumber first, fall back to PyPDF2."""
        if _PDFPLUMBER_AVAILABLE:
            return self._extract_with_pdfplumber(file_path)
        if _PYPDF2_AVAILABLE:
            return self._extract_with_pypdf2(file_path)
        raise ImportError("Neither pdfplumber nor PyPDF2 is installed.")

    @staticmethod
    def _extract_with_pdfplumber(file_path: str) -> str:
        import pdfplumber  # noqa: F811
        pages = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
        return "\n\n".join(pages)

    @staticmethod
    def _extract_with_pypdf2(file_path: str) -> str:
        import PyPDF2  # noqa: F811
        pages = []
        with open(file_path, "rb") as fh:
            reader = PyPDF2.PdfReader(fh)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
        return "\n\n".join(pages)

    @staticmethod
    def _clean_text(text: str) -> str:
        """Remove noise while preserving meaningful whitespace."""
        # Collapse 3+ newlines → double newline
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Remove null bytes / control characters (keep tab + newline)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", text)
        # Normalise spaces on each line
        lines = [" ".join(line.split()) for line in text.split("\n")]
        text = "\n".join(lines)
        # Collapse runs of multiple spaces
        text = re.sub(r" {2,}", " ", text)
        return text.strip()

    def _split_into_chunks(self, text: str) -> List[str]:
        """
        Sliding-window character-level chunker.
        Splits on sentence boundaries where possible.
        """
        chunks: List[str] = []
        start = 0
        length = len(text)
        while start < length:
            end = min(start + self.chunk_size, length)
            # Try to end at a sentence boundary
            if end < length:
                for sep in (". ", ".\n", "? ", "! ", "\n\n"):
                    boundary = text.rfind(sep, start, end)
                    if boundary != -1:
                        end = boundary + len(sep)
                        break
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            next_start = end - self.chunk_overlap
            # Guard: always advance forward to prevent infinite loop
            if next_start <= start:
                next_start = end
            start = next_start
        return chunks
