from crewai import Agent, Task
from backend.agents.llm_provider import get_agent_llm


def _get_llm():
    return get_agent_llm(temperature=0.4)


def get_interview_prep_agent() -> Agent:
    """Create the Interview Preparation agent."""
    return Agent(
        role="Interview Coach",
        goal="Prepare candidates for interviews by providing past questions and prep tips",
        backstory="You're an expert interview coach and former technical recruiter. "
                  "You know the exact types of questions companies ask for specific roles. "
                  "You provide actionable, strategic advice to help candidates ace their interviews.",
        llm=_get_llm(),
        verbose=True,
    )


def create_interview_prep_task(agent: Agent, job_summary: str, job_title: str) -> Task:
    """Create a task for suggesting interview questions and tips."""
    return Task(
        description=f"""
        Based on the role '{job_title}' and the job description below, prepare the candidate for an interview.
        
        Provide:
        1. **Past/Expected Interview Questions**: Suggest 5-7 questions that are highly likely to be asked for this specific role. Include a mix of technical (if applicable) and behavioral questions.
        2. **Interview Prep Tips**: Actionable advice on how to prepare, what to emphasize from their background, and what the interviewers will be looking for.
        
        --- Job Description ---
        {job_summary}
        
        Format the output using clear Markdown headers and bullet points.
        """,
        expected_output="A structured markdown document containing expected interview questions and actionable preparation tips.",
        agent=agent,
    )
