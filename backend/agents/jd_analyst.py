from crewai import Agent, Task
from backend.agents.llm_provider import get_agent_llm


def _get_llm():
    return get_agent_llm(temperature=0.2)


def get_jd_analyst_agent() -> Agent:
    """Create the JD Analyst agent for parsing job descriptions."""
    return Agent(
        role="JD Analyst",
        goal="Understand and summarize job postings, extracting key requirements",
        backstory="You're an expert in job market analysis with a focus on job listings. "
                  "You can quickly identify key skills, qualifications, and responsibilities "
                  "from any job description.",
        llm=_get_llm(),
        verbose=True,
    )


def create_jd_analysis_task(agent: Agent, job_description: str) -> Task:
    """Create a task for analyzing a job description."""
    return Task(
        description=f"""
        Analyze the following job posting and extract:
        - A summary of the role
        - Key skills required
        - Any specific qualifications or eligibility
        - Key responsibilities

        Job Description:
        {job_description}
        """,
        expected_output="A structured markdown summary containing sections for Role Summary, "
                        "Required Skills, Qualifications, and Key Responsibilities.",
        agent=agent,
    )
