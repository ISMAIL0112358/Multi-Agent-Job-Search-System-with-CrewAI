from crewai import Agent, Task, LLM
from backend.config import settings


def _get_llm():
    return LLM(
        model=settings.GEMINI_MODEL_NAME,
        temperature=0.3,
        api_key=settings.GEMINI_API_KEY,
    )


def get_resume_cl_agent() -> Agent:
    """Create the Resume & Cover Letter agent."""
    return Agent(
        role="Resume & Cover Letter Writer",
        goal="Customize application materials to match job descriptions for maximum hiring potential",
        backstory="You're an expert in professional writing and tailoring resumes for job applications. "
                  "You understand ATS systems, keyword optimization, and what hiring managers look for. "
                  "You can identify gaps in a resume and suggest specific improvements.",
        llm=_get_llm(),
        verbose=True,
    )


def create_resume_cl_task(agent: Agent, job_summary: str, resume_text: str) -> Task:
    """Create a task for generating tailored resume and cover letter."""
    return Task(
        description=f"""
        Based on the job summary below, analyze the candidate's resume and provide:
        
        1. **Resume Tweaks**: Specific suggestions to improve the resume for this job.
           - Keywords to add
           - Sections to emphasize
           - Experience to highlight
           - A rewritten professional summary
        
        2. **Cover Letter**: A personalized, compelling cover letter tailored for this position.
        
        --- Job Summary ---
        {job_summary}
        
        --- Candidate Resume ---
        {resume_text}
        
        Format your output clearly with headers:
        ## Resume Tweaks
        [Your suggestions here]
        
        ## Cover Letter
        [Your cover letter here]
        """,
        expected_output="A structured response with two sections: Resume Tweaks (specific improvement suggestions) "
                        "and a tailored Cover Letter.",
        agent=agent,
    )
