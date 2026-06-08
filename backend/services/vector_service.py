"""
Vector Service — manages ChromaDB vector store for candidate resumes.

Handles chunking, embedding, storage, and semantic search of resume documents
using Google's embedding model via LangChain.
"""
import logging
import os
from typing import Optional

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

from backend.config import settings

logger = logging.getLogger(__name__)


class VectorService:
    """Manages the ChromaDB vector store for candidate resumes."""

    _collection_name = "candidate_resumes"
    _instance: Optional["VectorService"] = None

    def __init__(self):
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)

        self._embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=settings.GEMINI_API_KEY,
        )

        self._vectorstore = Chroma(
            collection_name=self._collection_name,
            embedding_function=self._embeddings,
            persist_directory=settings.CHROMA_PERSIST_DIR,
        )

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        logger.info(
            "VectorService initialized — collection=%s, persist=%s",
            self._collection_name,
            settings.CHROMA_PERSIST_DIR,
        )

    @classmethod
    def get_instance(cls) -> "VectorService":
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_resume(self, candidate_id: str, resume_text: str) -> str:
        """Chunk, embed, and store a resume in ChromaDB.

        Args:
            candidate_id: Unique candidate identifier (used as metadata).
            resume_text: Full extracted text from the PDF.

        Returns:
            A document ID prefix used to identify all chunks for this candidate.
        """
        chunks = self._splitter.split_text(resume_text)
        if not chunks:
            logger.warning("No chunks generated for candidate %s", candidate_id)
            return candidate_id

        doc_ids = [f"{candidate_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"candidate_id": candidate_id, "chunk_index": i} for i in range(len(chunks))]

        self._vectorstore.add_texts(
            texts=chunks,
            ids=doc_ids,
            metadatas=metadatas,
        )

        logger.info("Added %d chunks for candidate %s", len(chunks), candidate_id)
        return candidate_id

    def search_candidates(self, query: str, top_n: int = 10) -> list[dict]:
        """Semantic search across all candidate resumes.

        Args:
            query: The job description or search query text.
            top_n: Number of top results to return (by unique candidate).

        Returns:
            List of {candidate_id, score, chunk_text} dicts, deduplicated by candidate.
        """
        # Fetch more results than needed to account for deduplication
        raw_results = self._vectorstore.similarity_search_with_relevance_scores(
            query, k=top_n * 3
        )

        # Deduplicate by candidate_id, keeping the best score per candidate
        seen = {}
        for doc, score in raw_results:
            cid = doc.metadata.get("candidate_id", "unknown")
            if cid not in seen or score > seen[cid]["score"]:
                seen[cid] = {
                    "candidate_id": cid,
                    "score": float(score),
                    "chunk_text": doc.page_content,
                }

        # Sort by score descending and take top_n
        results = sorted(seen.values(), key=lambda x: x["score"], reverse=True)[:top_n]
        logger.info("Search returned %d unique candidates (from %d chunks)", len(results), len(raw_results))
        return results

    def delete_resume(self, candidate_id: str):
        """Remove all chunks for a candidate from ChromaDB.

        Args:
            candidate_id: The candidate whose resume data should be deleted.
        """
        try:
            # Get all doc IDs for this candidate
            results = self._vectorstore.get(where={"candidate_id": candidate_id})
            if results and results["ids"]:
                self._vectorstore.delete(ids=results["ids"])
                logger.info("Deleted %d chunks for candidate %s", len(results["ids"]), candidate_id)
            else:
                logger.info("No chunks found for candidate %s", candidate_id)
        except Exception as e:
            logger.error("Failed to delete chunks for candidate %s: %s", candidate_id, e)
            raise
