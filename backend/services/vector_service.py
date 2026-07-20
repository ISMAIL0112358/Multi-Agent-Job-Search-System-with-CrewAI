"""
Vector Service — manages ChromaDB vector store for candidate resumes.

Handles chunking, embedding, storage, and semantic search of resume documents
using Google's embedding model via LangChain.
"""
import logging
import os
import re
from typing import Optional

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

from backend.config import settings

logger = logging.getLogger(__name__)


class FixedGoogleGenerativeAIEmbeddings(GoogleGenerativeAIEmbeddings):
    """GoogleGenerativeAIEmbeddings with forced output dimensionality of 768 to match the database schema."""
    
    def embed_documents(self, texts, **kwargs):
        kwargs['output_dimensionality'] = 768
        try:
            self.model = "models/gemini-embedding-2"
            return super().embed_documents(texts, **kwargs)
        except Exception as e:
            logger.warning("Primary embedding model models/gemini-embedding-2 failed: %s. Falling back to models/gemini-embedding-001...", e)
            try:
                self.model = "models/gemini-embedding-001"
                return super().embed_documents(texts, **kwargs)
            except Exception as ex:
                logger.error("Fallback embedding model models/gemini-embedding-001 also failed: %s", ex)
                raise ex

    def embed_query(self, text, **kwargs):
        kwargs['output_dimensionality'] = 768
        try:
            self.model = "models/gemini-embedding-2"
            return super().embed_query(text, **kwargs)
        except Exception as e:
            logger.warning("Primary embedding model models/gemini-embedding-2 failed: %s. Falling back to models/gemini-embedding-001...", e)
            try:
                self.model = "models/gemini-embedding-001"
                return super().embed_query(text, **kwargs)
            except Exception as ex:
                logger.error("Fallback embedding model models/gemini-embedding-001 also failed: %s", ex)
                raise ex


class VectorService:
    """Manages the ChromaDB vector store for candidate resumes."""

    _collection_name = "candidate_resumes"
    _instance: Optional["VectorService"] = None

    def __init__(self):
        if settings.ENV == "local":
            self._embeddings = OllamaEmbeddings(
                model=settings.LOCAL_EMBEDDING_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
            )
        else:
            self._embeddings = FixedGoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-2",
                google_api_key=settings.GEMINI_API_KEY,
            )

        if settings.VECTOR_STORE_PROVIDER == "pgvector":
            from langchain_community.vectorstores.pgvector import PGVector
            self._vectorstore = PGVector(
                connection_string=settings.DATABASE_URL,
                embedding_function=self._embeddings,
                collection_name=self._collection_name,
            )
        else:
            os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
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

    def _clean_and_normalize_line(self, line: str) -> str:
        """Remove leading/trailing bullet points, markdown symbols, and whitespace."""
        line = re.sub(r'^[\s#\-*•○▪►●✔·]+', '', line)
        line = re.sub(r'[\s:;]+$', '', line)
        return line.strip()

    def _is_section_header(self, line: str) -> bool:
        """Identify if a line is likely a section header in a resume."""
        cleaned = self._clean_and_normalize_line(line)
        if not cleaned or len(cleaned) > 50:
            return False
            
        words = cleaned.lower().split()
        if not words:
            return False
            
        # Standard keywords representing resume sections
        keywords = {
            "summary", "objective", "experience", "employment", "history", 
            "education", "skills", "projects", "certifications", "achievements", 
            "awards", "publications", "languages", "hobbies", "interests", 
            "contact", "qualifications", "profile", "about"
        }
        
        # Header must be concise (usually 1 to 4 words) and contain at least one keyword
        if len(words) <= 4 and any(w in keywords for w in words):
            return True
            
        return False

    def split_resume_by_sections(self, resume_text: str) -> list[str]:
        """Split resume text into chunks based on logical sections, prepending headers to sub-chunks."""
        lines = resume_text.split("\n")
        sections = []
        current_sec_name = "Header"
        current_sec_lines = []
        
        for line in lines:
            if self._is_section_header(line):
                # Save the previous section
                if current_sec_lines:
                    sections.append((current_sec_name, "\n".join(current_sec_lines).strip()))
                current_sec_name = self._clean_and_normalize_line(line)
                current_sec_lines = []
            else:
                current_sec_lines.append(line)
                
        if current_sec_lines:
            sections.append((current_sec_name, "\n".join(current_sec_lines).strip()))
            
        # Chunk the extracted sections
        chunks = []
        for sec_name, sec_text in sections:
            if not sec_text:
                continue
                
            # If the entire section is small, keep it as a single chunk
            if len(sec_text) <= 1200:
                if sec_name.lower() != "header":
                    chunk_content = f"Section: {sec_name}\n\n{sec_text}"
                else:
                    chunk_content = sec_text
                chunks.append(chunk_content)
            else:
                # For larger sections, split and prepend the section context
                sub_chunks = self._splitter.split_text(sec_text)
                for sub_chunk in sub_chunks:
                    if sec_name.lower() != "header":
                        chunk_content = f"Section: {sec_name} (continued)\n\n{sub_chunk}"
                    else:
                        chunk_content = sub_chunk
                    chunks.append(chunk_content)
                    
        return chunks

    def add_resume(self, candidate_id: str, resume_text: str) -> str:
        """Chunk, embed, and store a resume in ChromaDB.

        Args:
            candidate_id: Unique candidate identifier (used as metadata).
            resume_text: Full extracted text from the PDF.

        Returns:
            A document ID prefix used to identify all chunks for this candidate.
        """
        chunks = self.split_resume_by_sections(resume_text)
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
        """Remove all chunks for a candidate from the vector store."""
        if settings.VECTOR_STORE_PROVIDER == "pgvector":
            try:
                from sqlalchemy import text
                from backend.database import engine
                with engine.begin() as conn:
                    # PGVector stores metadata in cmetadata column as JSON
                    conn.execute(
                        text("DELETE FROM langchain_pg_embedding WHERE cmetadata->>'candidate_id' = :cid"),
                        {"cid": candidate_id}
                    )
                logger.info("Deleted pgvector chunks for candidate %s", candidate_id)
            except Exception as e:
                logger.error("Failed to delete pgvector chunks for candidate %s: %s", candidate_id, e)
                raise
        else:
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
