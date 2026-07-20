import logging
from crewai import LLM
from backend.config import settings

logger = logging.getLogger(__name__)


class FallbackLLM(LLM):
    """CrewAI LLM wrapper that automatically falls back to alternative models upon execution failure."""

    def call(self, *args, **kwargs):
        fallback_models = [
            "gemini/gemini-3-flash",
            "gemini/gemini-2.0-flash",
            "gemini/gemini-2.0-flash-lite",
            "gemini/gemini-2.5-flash"
        ]
        try:
            # Force primary model first
            self.model = "gemini/gemini-3.1-flash-lite"
            return super().call(*args, **kwargs)
        except Exception as e:
            logger.warning("Primary CrewAI LLM call (gemini-3.1-flash-lite) failed with error: %s. Initiating fallbacks...", e)
            for model_name in fallback_models:
                try:
                    logger.info("CrewAI falling back to model: %s", model_name)
                    fallback_llm = LLM(
                        model=model_name,
                        temperature=self.temperature,
                        api_key=self.api_key,
                        base_url=self.base_url,
                        stop=self.stop,
                        additional_params=self.additional_params,
                    )
                    return fallback_llm.call(*args, **kwargs)
                except Exception as ex:
                    logger.warning("Fallback model %s failed: %s", model_name, ex)
            raise e

    async def acall(self, *args, **kwargs):
        fallback_models = [
            "gemini/gemini-3-flash",
            "gemini/gemini-2.0-flash",
            "gemini/gemini-2.0-flash-lite",
            "gemini/gemini-2.5-flash"
        ]
        try:
            # Force primary model first
            self.model = "gemini/gemini-3.1-flash-lite"
            return await super().acall(*args, **kwargs)
        except Exception as e:
            logger.warning("Primary CrewAI LLM acall (gemini-3.1-flash-lite) failed with error: %s. Initiating fallbacks...", e)
            for model_name in fallback_models:
                try:
                    logger.info("CrewAI falling back to model: %s", model_name)
                    fallback_llm = LLM(
                        model=model_name,
                        temperature=self.temperature,
                        api_key=self.api_key,
                        base_url=self.base_url,
                        stop=self.stop,
                        additional_params=self.additional_params,
                    )
                    return await fallback_llm.acall(*args, **kwargs)
                except Exception as ex:
                    logger.warning("Fallback model %s failed: %s", model_name, ex)
            raise e


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
        return FallbackLLM(
            model="gemini/gemini-3.1-flash-lite",
            temperature=temperature,
            api_key=settings.GEMINI_API_KEY,
        )
