from crewai import Agent, Task, LLM
from backend.config import settings


def _get_llm():
    return LLM(
        model=settings.GEMINI_MODEL_NAME,
        temperature=0.3,
        api_key=settings.GEMINI_API_KEY,
    )


def get_company_profiler_agent() -> Agent:
    """Create the Company Profiler agent."""
    return Agent(
        role="Company Profiler & Culture Analyst",
        goal="Provide insights into a company's background, culture, and pay ranges",
        backstory="You're a corporate researcher and career advisor. You have extensive knowledge "
                  "about tech companies, government agencies, and corporate environments. "
                  "You help candidates understand who they are applying to, what the culture is like, "
                  "and what compensation they might expect.",
        llm=_get_llm(),
        verbose=True,
    )


def create_company_profile_task(agent: Agent, agency_name: str, job_title: str) -> Task:
    """Create a task for profiling a company."""
    return Task(
        description=f"""
        Research and provide a profile for the organization '{agency_name}' and the role '{job_title}'.
        
        Please provide the following details if you have them in your knowledge base. 
        If specific details are NOT available, explicitly state "Details are not available".
        
        Include:
        - **Founder Name**: (if applicable)
        - **Company Size**: (e.g., 50-200 employees, 10,000+ employees)
        - **Founded In**: (Year)
        
        Also include sections for:
        - **Work Culture Review**: A brief summary of what it's like to work there.
        - **Pay Range**: The estimated pay range for the role of '{job_title}' at this organization (or generally for this role if company-specific data is unavailable).
        
        Format the output clearly using Markdown. Use bullet points for the founder, size, and founded year.
        """,
        expected_output="A structured markdown profile of the company, including founder, size, year founded, work culture, and estimated pay range.",
        agent=agent,
    )
