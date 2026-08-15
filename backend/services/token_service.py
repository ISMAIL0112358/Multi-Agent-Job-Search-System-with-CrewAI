"""Token Tracking Service — extracts exact token usage directly from Gemini API responses and records them."""
import logging
from sqlalchemy import text
from backend.database import SessionLocal, AsyncSessionLocal

logger = logging.getLogger(__name__)


def extract_gemini_generation_tokens(response_or_crew) -> int:
    """Extract total token count directly from Gemini API response metadata or CrewAI usage metrics.
    If unavailable, prints 'failed to get token used' and returns 0 without any fallback calculations.
    """
    if response_or_crew is None:
        print("failed to get token used")
        return 0

    # 1. CrewAI Crew instance with usage_metrics
    if hasattr(response_or_crew, "usage_metrics") and response_or_crew.usage_metrics:
        total = getattr(response_or_crew.usage_metrics, "total_tokens", None)
        if total is not None and isinstance(total, (int, float)) and total > 0:
            return int(total)

    # 2. LangChain AIMessage / response with usage_metadata (dict or object)
    if hasattr(response_or_crew, "usage_metadata") and response_or_crew.usage_metadata:
        um = response_or_crew.usage_metadata
        if isinstance(um, dict) and "total_tokens" in um and um["total_tokens"] is not None:
            return int(um["total_tokens"])
        elif hasattr(um, "total_token_count") and um.total_token_count is not None:
            return int(um.total_token_count)
        elif hasattr(um, "total_tokens") and um.total_tokens is not None:
            return int(um.total_tokens)

    # 3. LangChain AIMessage with response_metadata
    if hasattr(response_or_crew, "response_metadata") and response_or_crew.response_metadata:
        rm = response_or_crew.response_metadata
        if isinstance(rm, dict):
            um = rm.get("usage_metadata") or rm.get("token_usage")
            if isinstance(um, dict) and "total_tokens" in um and um["total_tokens"] is not None:
                return int(um["total_tokens"])
            elif isinstance(um, dict) and "total_token_count" in um and um["total_token_count"] is not None:
                return int(um["total_token_count"])

    # 4. Direct Google GenAI GenerateContentResponse
    if hasattr(response_or_crew, "usage_metadata") and response_or_crew.usage_metadata:
        um = response_or_crew.usage_metadata
        if hasattr(um, "total_token_count") and um.total_token_count is not None:
            return int(um.total_token_count)

    print("failed to get token used")
    return 0


def get_gemini_embedding_tokens(contents: str | list[str]) -> int:
    """Get exact embedding token count directly from Gemini API count_tokens endpoint.
    If unavailable, prints 'failed to get token used' and returns 0 without any fallback calculations.
    """
    if not contents:
        return 0
    try:
        from google import genai
        from backend.config import settings
        if not settings.GEMINI_API_KEY:
            print("failed to get token used")
            return 0
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        res = client.models.count_tokens(model="models/gemini-embedding-2", contents=contents)
        if hasattr(res, "total_tokens") and res.total_tokens is not None:
            return int(res.total_tokens)
        print("failed to get token used")
        return 0
    except Exception as e:
        print(f"failed to get token used: {e}")
        return 0


def add_tokens_sync(user_id: str, generative_tokens: int = 0, embedding_tokens: int = 0):
    """Synchronously increment cumulative token usage for a user."""
    if not user_id or (generative_tokens <= 0 and embedding_tokens <= 0):
        return
    try:
        with SessionLocal() as db:
            db.execute(
                text("""
                    UPDATE users
                    SET generative_tokens_count = generative_tokens_count + :gen,
                        embedding_tokens_count = embedding_tokens_count + :emb
                    WHERE id = :uid
                """),
                {"gen": max(0, int(generative_tokens)), "emb": max(0, int(embedding_tokens)), "uid": user_id}
            )
            db.commit()
    except Exception as e:
        logger.error(f"Failed to record sync tokens for user {user_id}: {e}")


async def add_tokens_async(user_id: str, generative_tokens: int = 0, embedding_tokens: int = 0):
    """Asynchronously increment cumulative token usage for a user."""
    if not user_id or (generative_tokens <= 0 and embedding_tokens <= 0):
        return
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(
                text("""
                    UPDATE users
                    SET generative_tokens_count = generative_tokens_count + :gen,
                        embedding_tokens_count = embedding_tokens_count + :emb
                    WHERE id = :uid
                """),
                {"gen": max(0, int(generative_tokens)), "emb": max(0, int(embedding_tokens)), "uid": user_id}
            )
            await db.commit()
    except Exception as e:
        logger.error(f"Failed to record async tokens for user {user_id}: {e}")
