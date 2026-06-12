from crewai import Agent, Task
from backend.agents.llm_provider import get_agent_llm


def _get_llm():
    return get_agent_llm(temperature=0.1)


def get_hiring_scorer_agent() -> Agent:
    """Create the Hiring Score agent that evaluates resume-job match."""
    return Agent(
        role="Hiring Match Scorer",
        goal="Evaluate how well a candidate's resume matches a job description and provide a percentage score",
        backstory="You're a senior HR analytics specialist who has reviewed thousands of applications. "
                  "You can accurately assess how well a candidate's skills, experience, and qualifications "
                  "match a given job description. You provide honest, data-driven assessments.",
        llm=_get_llm(),
        verbose=True,
    )


def create_hiring_score_task(agent: Agent, job_summary: str, resume_text: str) -> Task:
    """Create a task for scoring resume-job match."""
    return Task(
        description=f"""
        Evaluate how well the candidate's resume matches the job description below.
        
        Provide:
        1. A match score as a percentage (0-100%), e.g., "75%"
        2. Brief reasoning explaining the score (3-5 bullet points)
        
        Consider:
        - Skills match (technical and soft skills)
        - Experience relevance
        - Education/qualification fit
        - Industry alignment
        
        --- Job Description ---
        {job_summary}
        
        --- Candidate Resume ---
        {resume_text}
        
        Start your response with the score percentage on the first line, 
        followed by your reasoning.
        """,
        expected_output="A percentage score (e.g., '75%') on the first line, followed by "
                        "3-5 bullet points explaining the match assessment.",
        agent=agent,
    )
