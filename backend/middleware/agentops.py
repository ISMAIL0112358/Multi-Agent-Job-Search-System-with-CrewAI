import logging
from backend.config import settings

logger = logging.getLogger(__name__)


def init_agentops():
    """Initialize AgentOps for monitoring CrewAI agent runs.
    
    AgentOps has built-in CrewAI integration — once initialized,
    it automatically tracks all crew runs, agent actions, and tool usage.
    """
    if not settings.AGENTOPS_API_KEY:
        logger.warning("AGENTOPS_API_KEY not set — AgentOps monitoring disabled")
        return

    try:
        import agentops
        agentops.init(
            api_key=settings.AGENTOPS_API_KEY,
            default_tags=["job-search-system"],
        )
        logger.info("AgentOps initialized successfully")
    except ImportError:
        logger.warning("agentops package not installed — monitoring disabled")
    except Exception as e:
        logger.error(f"Failed to initialize AgentOps: {e}")


def get_agentops_callback_handler(tags=None):
    """Get the LangChain callback handler for AgentOps if configured."""
    if not settings.AGENTOPS_API_KEY:
        return None
    try:
        from agentops.integration.callbacks.langchain import LangchainCallbackHandler
        return LangchainCallbackHandler(
            api_key=settings.AGENTOPS_API_KEY,
            tags=tags or ["job-search-system"],
        )
    except Exception as e:
        logger.warning(f"Failed to load AgentOps LangchainCallbackHandler: {e}")
        return None
