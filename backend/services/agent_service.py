from crewai import Crew, Process
from backend.agents.jd_analyst import get_jd_analyst_agent, create_jd_analysis_task
from backend.agents.resume_cl_agent import get_resume_cl_agent, create_resume_cl_task
from backend.agents.messaging_agent import get_messaging_agent, create_messaging_task
from backend.agents.hiring_scorer import get_hiring_scorer_agent, create_hiring_score_task
from backend.agents.company_profiler import get_company_profiler_agent, create_company_profile_task
from backend.agents.interview_prep import get_interview_prep_agent, create_interview_prep_task


def run_hiring_score(job_summary: str, resume_text: str, user_skills: str = None, company_preference: str = None) -> dict:
    """Run the hiring scorer agent to get a match percentage.
    
    Returns dict with 'score' (int 0-100) and 'reasoning' (str).
    """
    agent = get_hiring_scorer_agent()
    
    # Append skills and preferences to resume text for the agent's context
    enhanced_resume = resume_text
    if user_skills:
        enhanced_resume += f"\n\n--- User Declared Skills ---\n{user_skills}"
    if company_preference:
        enhanced_resume += f"\n\n--- User Company Preferences ---\n{company_preference}"
        
    task = create_hiring_score_task(agent, job_summary, enhanced_resume)

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )
    result = crew.kickoff()
    result_text = str(result)

    # Parse the score from the output
    score = 50  # Default
    reasoning = result_text

    # Try to extract a numeric score
    import re
    score_match = re.search(r"(\d{1,3})%", result_text)
    if score_match:
        score = min(int(score_match.group(1)), 100)

    # Try to split score and reasoning
    lines = result_text.strip().split("\n")
    if len(lines) > 1:
        reasoning = "\n".join(lines[1:]).strip()

    return {"score": score, "reasoning": reasoning}


def run_full_analysis(job_data: dict, resume_text: str, user_bio: str, user_skills: str = None) -> dict:
    """Run the full CrewAI pipeline: JD analysis → resume tweak → cover letter → company profile → interview prep.
    
    Returns dict with jd_summary, resume_tweaks, cover_letter, hiring_score, hiring_score_reasoning, company_profile, interview_prep.
    """
    enhanced_resume = resume_text
    if user_skills:
        enhanced_resume += f"\n\n--- User Declared Skills ---\n{user_skills}"
        
    job_summary = ""
    # Try to extract job summary from different data structures
    if isinstance(job_data, dict):
        user_area = job_data.get("UserArea", {})
        if isinstance(user_area, dict):
            details = user_area.get("Details", {})
            job_summary = details.get("JobSummary", "")
        if not job_summary:
            job_summary = job_data.get("job_summary", "")
        if not job_summary:
            job_summary = str(job_data)

    agency_name = job_data.get("OrganizationName", job_data.get("organization_name", "Unknown Agency"))
    job_title = job_data.get("PositionTitle", job_data.get("position_title", "Unknown Position"))

    # Initialize agents
    jd_agent = get_jd_analyst_agent()
    resume_agent = get_resume_cl_agent()
    message_agent = get_messaging_agent()
    company_agent = get_company_profiler_agent()
    interview_agent = get_interview_prep_agent()

    # Create tasks
    jd_task = create_jd_analysis_task(jd_agent, job_summary)
    resume_task = create_resume_cl_task(resume_agent, job_summary, enhanced_resume)
    
    enhanced_bio = user_bio
    if user_skills:
        enhanced_bio += f"\nSkills: {user_skills}"
        
    message_task = create_messaging_task(message_agent, job_summary, agency_name, enhanced_bio)
    company_task = create_company_profile_task(company_agent, agency_name, job_title)
    interview_task = create_interview_prep_task(interview_agent, job_summary, job_title)

    # Run tasks in parallel using ThreadPoolExecutor
    from concurrent.futures import ThreadPoolExecutor

    def _run_single_agent_task(agent, task) -> str:
        """Run a single task using its assigned agent inside a temporary Crew."""
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False,
        )
        crew.kickoff()
        return str(task.output) if task.output else ""

    tasks_to_run = [
        ("jd", jd_agent, jd_task),
        ("resume", resume_agent, resume_task),
        ("message", message_agent, message_task),
        ("company", company_agent, company_task),
        ("interview", interview_agent, interview_task),
    ]

    outputs = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        # Submit all agent task crews to the executor
        futures = {
            executor.submit(_run_single_agent_task, agent, task): name
            for name, agent, task in tasks_to_run
        }
        
        # Concurrently calculate the hiring score
        hiring_score_future = executor.submit(
            run_hiring_score, job_summary, resume_text, user_skills
        )
        
        # Gather outputs for each task
        for future in futures:
            name = futures[future]
            try:
                outputs[name] = future.result()
            except Exception as e:
                logger.error("Error running agent task %s: %s", name, e)
                outputs[name] = f"Error during analysis: {str(e)}"
                
        # Gather hiring score result
        try:
            score_result = hiring_score_future.result()
        except Exception as e:
            logger.error("Error calculating hiring score: %s", e)
            score_result = {"score": 50, "reasoning": f"Error running hiring score: {str(e)}"}

    return {
        "jd_summary": outputs.get("jd", ""),
        "resume_tweaks": outputs.get("resume", ""),
        "cover_letter": outputs.get("message", ""),
        "company_profile": outputs.get("company", ""),
        "interview_prep": outputs.get("interview", ""),
        "hiring_score": score_result["score"],
        "hiring_score_reasoning": score_result["reasoning"],
    }

