from crewai import Crew, Process
from agents.jd_analyst import get_jd_analyst_agent, create_jd_analysis_task
from agents.resume_cl_agent import get_resume_cl_agent, create_resume_cl_task
from agents.messaging_agent import get_messaging_agent, create_messaging_task
from usajobs_api import fetch_usajobs
def run_pipeline(job_data, resume_text, user_bio):
    job_summary = job_data['UserArea']['Details']['JobSummary']
    agency_name = job_data.get('OrganizationName', 'Unknown Agency')
    job_title = job_data.get('PositionTitle', 'Unknown Position')

    # Initialize agents
    jd_agent = get_jd_analyst_agent()
    resume_agent = get_resume_cl_agent()
    message_agent = get_messaging_agent()

    # Create tasks
    jd_task = create_jd_analysis_task(jd_agent, job_summary)
    resume_task = create_resume_cl_task(resume_agent, job_summary, resume_text)
    message_task = create_messaging_task(message_agent, job_summary, agency_name, user_bio)

    # Run the crew
    crew = Crew(
        agents=[jd_agent, resume_agent, message_agent],
        tasks=[jd_task, resume_task, message_task],
        process=Process.sequential
    )
    result = crew.kickoff()

    print("\n=== FINAL OUTPUT ===\n")
    print(result)

    return result