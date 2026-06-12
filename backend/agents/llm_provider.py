from crewai import LLM
from backend.config import settings

def get_agent_llm(temperature: float = 0.3) -> LLM:
    """Returns a CrewAI LLM instance based on settings.ENV."""
    if settings.ENV == "local":
        model_name = settings.LOCAL_LLM_MODEL
        # Prefix model name with ollama/ if not already present
        if not model_name.startswith("ollama/"):
            model_name = f"ollama/{model_name}"
            
        return LLM(
            model=model_name,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=temperature,
        )
    else:
        return LLM(
            model=settings.GEMINI_MODEL_NAME,
            temperature=temperature,
            api_key=settings.GEMINI_API_KEY,
        )
