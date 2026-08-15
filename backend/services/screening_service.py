"""
Screening Service — AI-powered candidate screening and vetting using LangChain.

Uses RAG (Retrieval-Augmented Generation) to match candidates against Job Descriptions,
generate match scores with justifications, and create vetting Q&As.
"""
import json
import logging
import os
import re
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from pydantic import BaseModel, Field

from backend.config import settings
from backend.services.vector_service import VectorService

logger = logging.getLogger(__name__)


# ── Pydantic models for structured LLM output ──────────────────────

class CandidateMatchResult(BaseModel):
    """Structured output from candidate-JD matching."""
    match_score: float = Field(description="Match score from 0 to 100")
    justification: str = Field(description="Structured justification explaining the score with skills match, experience relevance, and identified gaps")


class VettingQuestion(BaseModel):
    """A single vetting question for a candidate."""
    question: str = Field(description="The verification question to ask the candidate")
    expected_answer: str = Field(description="Expected answer or key points to look for")
    skill_area: str = Field(description="The skill or experience area being verified")
    difficulty: str = Field(description="Difficulty level: basic, intermediate, or advanced")


class VettingQuestionSet(BaseModel):
    """Set of vetting questions for a candidate."""
    questions: list[VettingQuestion] = Field(description="List of 5 targeted verification questions")


class ExtractedCandidateInfo(BaseModel):
    """Contact info extracted from a resume."""
    name: str = Field(description="Full name of the candidate")
    email: str = Field(default="", description="Email address if found, empty string otherwise")
    phone: str = Field(default="", description="Phone number if found, empty string otherwise")


# ── Service Class ───────────────────────────────────────────────────

class ScreeningService:
    """AI-powered candidate screening using LangChain + RAG."""

    def __init__(self, vector_service: Optional[VectorService] = None):
        # Set up LangSmith tracing if configured
        if settings.LANGSMITH_API_KEY:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
            os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
            logger.info("LangSmith tracing enabled for project: %s", settings.LANGSMITH_PROJECT)

        # Get AgentOps callback handler for LangChain if configured
        from backend.middleware.agentops import get_agentops_callback_handler
        handler = get_agentops_callback_handler(tags=["hr-screening"])
        callbacks = [handler] if handler else None

        if settings.ENV == "local":
            self._llm = ChatOllama(
                model=settings.LOCAL_LLM_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0.2,
                callbacks=callbacks,
            )
        else:
            # Strip "gemini/" prefix if present for langchain-google-genai compatibility
            model_name = settings.GEMINI_MODEL_NAME
            if model_name.startswith("gemini/"):
                model_name = model_name[len("gemini/"):]

            primary = ChatGoogleGenerativeAI(
                model="gemini-3.1-flash-lite",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.2,
                callbacks=callbacks,
            )
            fallbacks = [
                ChatGoogleGenerativeAI(model=m, google_api_key=settings.GEMINI_API_KEY, temperature=0.2, callbacks=callbacks)
                for m in ["gemini-3-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-2.5-flash"]
            ]
            self._llm = primary.with_fallbacks(fallbacks)

        self._vector_service = vector_service or VectorService.get_instance()

    @staticmethod
    def _get_response_text(response) -> str:
        """Safely extract text content from an LLM response.

        ChatGoogleGenerativeAI can return response.content as either a plain
        string or a list of content parts (e.g. [{'type': 'text', 'text': '...'}]).
        This normalises it to always return a string.
        """
        content = response.content
        if isinstance(content, list):
            # Join all text parts
            parts = []
            for part in content:
                if isinstance(part, dict):
                    parts.append(part.get("text", str(part)))
                elif isinstance(part, str):
                    parts.append(part)
                else:
                    parts.append(str(part))
            return "\n".join(parts)
        return str(content)

    def screen_candidates(self, jd_text: str, top_n: int = 10, candidate_resumes: dict | None = None) -> list[dict]:
        """Screen candidates against a job description using RAG.

        Args:
            jd_text: The full job description text.
            top_n: Number of top candidates to return.
            candidate_resumes: Optional dict of {candidate_id: resume_text} for direct scoring.

        Returns:
            List of dicts with {candidate_id, match_score, match_justification}.
        """
        # Step 1: Vector search to find relevant candidates
        search_results = self._vector_service.search_candidates(jd_text, top_n=top_n * 2)

        if not search_results:
            logger.info("No candidates found in vector search")
            return []

        # Step 2: For each unique candidate, run detailed matching via LLM in parallel
        from concurrent.futures import ThreadPoolExecutor

        def score_single(candidate_match):
            candidate_id = candidate_match["candidate_id"]
            resume_text = (
                candidate_resumes.get(candidate_id, candidate_match["chunk_text"])
                if candidate_resumes
                else candidate_match["chunk_text"]
            )
            try:
                match_result, tokens = self._score_candidate(jd_text, resume_text)
                return {
                    "candidate_id": candidate_id,
                    "match_score": match_result.match_score,
                    "match_justification": match_result.justification,
                    "tokens": tokens,
                }
            except Exception as e:
                logger.error("Failed to score candidate %s: %s", candidate_id, e)
                return {
                    "candidate_id": candidate_id,
                    "match_score": candidate_match["score"] * 100,  # Fallback to vector similarity
                    "match_justification": f"Scoring based on semantic similarity (LLM scoring failed: {e})",
                    "tokens": 0,
                }

        results = []
        with ThreadPoolExecutor(max_workers=min(top_n, 10)) as executor:
            # Concurrently process candidate evaluations
            results = list(executor.map(score_single, search_results[:top_n]))

        # Sort by match_score descending
        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results[:top_n]

    def _score_candidate(self, jd_text: str, resume_text: str) -> tuple[CandidateMatchResult, int]:
        """Score a single candidate against a JD using LLM and return (CandidateMatchResult, tokens)."""
        system_prompt = """You are a senior HR analytics specialist with expertise in resume screening.
Evaluate how well the candidate's resume matches the job description.

You MUST respond with valid JSON in exactly this format:
{
  "match_score": <number between 0 and 100>,
  "justification": "<structured analysis covering: 1) Skills Match, 2) Experience Relevance, 3) Education/Qualification Fit, 4) Key Strengths, 5) Identified Gaps>"
}

Be precise and data-driven. Do not inflate scores — a 70+ score means the candidate is genuinely a strong match."""

        human_prompt = f"""--- JOB DESCRIPTION ---
{jd_text}

--- CANDIDATE RESUME ---
{resume_text}

Analyze the match and respond with JSON only."""

        response = self._llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ])

        from backend.services.token_service import extract_gemini_generation_tokens
        tokens = extract_gemini_generation_tokens(response)

        raw_text = self._get_response_text(response)

        # Parse the JSON response
        try:
            content = raw_text.strip()
            # Handle potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)
            return CandidateMatchResult(**data), tokens
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("Failed to parse LLM JSON response: %s — raw: %s", e, raw_text[:200])
            # Fallback: try to extract score from text
            score = 50.0
            score_match = re.search(r"(\d{1,3})", raw_text)
            if score_match:
                score = min(float(score_match.group(1)), 100.0)
            return CandidateMatchResult(
                match_score=score,
                justification=raw_text[:500],
            ), tokens

    def generate_vetting_questions(self, resume_text: str, jd_text: str) -> tuple[list[dict], int]:
        """Generate targeted verification Q&As for a candidate and return (questions, tokens)."""
        system_prompt = """You are an expert HR interviewer specialized in candidate verification.
Generate 5 targeted verification questions based on the candidate's resume claims.

These questions should:
1. Test if the candidate truly possesses the skills they claim
2. Verify specific experiences mentioned in the resume
3. Help detect potential resume padding or misrepresentation
4. Range from basic to advanced difficulty
5. Be relevant to the job description requirements

You MUST respond with valid JSON in exactly this format:
{
  "questions": [
    {
      "question": "<the verification question>",
      "expected_answer": "<what a truthful candidate should answer, including key terms/concepts>",
      "skill_area": "<the skill or experience being verified>",
      "difficulty": "<basic|intermediate|advanced>"
    }
  ]
}"""

        human_prompt = f"""--- JOB DESCRIPTION ---
{jd_text}

--- CANDIDATE RESUME ---
{resume_text}

Generate 5 targeted verification questions. Respond with JSON only."""

        response = self._llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ])

        from backend.services.token_service import extract_gemini_generation_tokens
        tokens = extract_gemini_generation_tokens(response)

        raw_text = self._get_response_text(response)

        try:
            content = raw_text.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)
            question_set = VettingQuestionSet(**data)
            return [q.model_dump() for q in question_set.questions], tokens
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("Failed to parse vetting questions JSON: %s — raw: %s", e, raw_text[:200])
            return [{
                "question": "Could not generate questions. Please try again.",
                "expected_answer": "",
                "skill_area": "general",
                "difficulty": "basic",
            }], tokens

    def extract_candidate_info(self, resume_text: str) -> dict:
        """Extract basic contact information from a resume and return dict including exact tokens."""
        system_prompt = """Extract the candidate's basic contact information from the resume.

You MUST respond with valid JSON in exactly this format:
{
  "name": "<full name>",
  "email": "<email address or empty string if not found>",
  "phone": "<phone number or empty string if not found>"
}

Respond with JSON only. Do not add any extra text."""

        response = self._llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Extract contact info from this resume:\n\n{resume_text[:2000]}"),
        ])

        from backend.services.token_service import extract_gemini_generation_tokens
        tokens = extract_gemini_generation_tokens(response)

        raw_text = self._get_response_text(response)

        try:
            content = raw_text.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)
            info = ExtractedCandidateInfo(**data)
            res = info.model_dump()
            res["tokens"] = tokens
            return res
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("Failed to extract candidate info: %s", e)
            # Fallback: try simple regex extraction
            name = "Unknown Candidate"
            email = ""
            phone = ""

            email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", resume_text)
            if email_match:
                email = email_match.group(0)

            phone_match = re.search(r"[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{7,15}", resume_text)
            if phone_match:
                phone = phone_match.group(0).strip()

            # Try to get name from first non-empty line
            for line in resume_text.split("\n"):
                line = line.strip()
                if line and len(line) < 60 and not re.search(r"[@|:]", line):
                    name = line
                    break

            return {"name": name, "email": email, "phone": phone, "tokens": tokens}
