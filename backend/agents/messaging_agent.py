from crewai import Agent, Task, LLM
from backend.config import settings


def _get_llm():
    return LLM(
        model=settings.GEMINI_MODEL_NAME,
        temperature=0.5,
        api_key=settings.GEMINI_API_KEY,
    )


def get_messaging_agent() -> Agent:
    """Create the Outreach Message Writer agent."""
    return Agent(
        role="Outreach Message Writer",
        goal="Draft personalized messages for job outreach",
        backstory="You're a professional career coach skilled in writing effective cold emails "
                  "and outreach messages for job seekers in tech and government.",
        llm=_get_llm(),
        verbose=True,
    )


def create_messaging_task(
    agent: Agent,
    job_summary: str,
    agency_name: str,
    user_bio: str = "I'm a professional looking for new opportunities.",
) -> Task:
    """Create a task for writing an outreach message."""
    return Task(
        description=f"""
        Write a concise and compelling outreach message that the candidate could send 
        to someone at {agency_name}, expressing interest in the job described below.
        
        --- Job Summary ---
        {job_summary}
        
        --- Candidate Bio ---
        {user_bio}
        
        The message should be friendly, professional, and under 150 words. 
        Tailor it for a platform like LinkedIn or email.
        """,
        expected_output="A short outreach message under 150 words, tailored for LinkedIn or email, "
                        "that is professional and expresses interest in the job at the given agency.",
        agent=agent,
    )
