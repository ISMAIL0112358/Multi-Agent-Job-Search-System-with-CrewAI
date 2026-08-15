import json
import logging
from typing import Dict, Any

from celery import shared_task
from sqlalchemy.orm import Session

from backend.celery_app import celery_app
from backend.database import SessionLocal
from backend.models.user import User
from backend.models.candidate import Candidate
from backend.models.job_description import JobDescription
from backend.models.screening_result import ScreeningResult
from backend.models.conversation import Conversation, Message
from backend.services.pdf_service import extract_text_from_pdf
from backend.services.storage_service import save_candidate_resume, save_cover_letter, save_generated_resume
from backend.services.vector_service import VectorService
from backend.services.screening_service import ScreeningService
from backend.services.agent_service import run_full_analysis

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.process_bulk_resumes")
def process_bulk_resumes_task(user_id: str, files_data: list[Dict[str, Any]]):
    """
    Process multiple candidate resumes.
    files_data is a list of dicts: {"filename": str, "filepath": str, "candidate_id": str}
    """
    logger.info(f"Processing {len(files_data)} resumes for user {user_id}")
    
    db: Session = SessionLocal()
    try:
        current_user = db.query(User).filter(User.id == user_id).first()
        if not current_user:
            logger.error(f"User {user_id} not found")
            return {"error": "User not found"}

        vector_service = VectorService.get_instance()

        # here screening service is used to just extract user details during resume upload
        screening_service = ScreeningService(vector_service)

        processed_count = 0
        from backend.routers.hr import _process_single_resume
        
        for file_data in files_data:
            filename = file_data["filename"]
            filepath = file_data["filepath"]
            candidate_id = file_data["candidate_id"]
            
            try:
                with open(filepath, "rb") as f:
                    file_bytes = f.read()
                resume_text = extract_text_from_pdf(file_bytes)
                
                _process_single_resume(
                    resume_text=resume_text,
                    source_label=filename,
                    category=None,
                    screening_service=screening_service,
                    vector_service=vector_service,
                    current_user=current_user,
                    db=db,
                    candidate_id=candidate_id,
                )
                processed_count += 1
            except Exception as e:
                logger.error(f"Failed to process {filename}: {str(e)}")

        return {"processed_count": processed_count, "total": len(files_data)}
    finally:
        db.close()


import time
from backend.services.token_service import add_tokens_sync


@celery_app.task(name="tasks.run_ai_screening")
def run_ai_screening_task(user_id: str, job_description_id: str, top_n: int = 50):
    """Run AI screening asynchronously and track execution duration and tokens."""
    start_time = time.time()
    db: Session = SessionLocal()
    try:
        jd = db.query(JobDescription).filter(
            JobDescription.id == job_description_id, 
            JobDescription.created_by == user_id
        ).first()
        
        if not jd:
            return {"error": "Job Description not found"}

        vector_service = VectorService.get_instance()
        screening_service = ScreeningService(vector_service)

        all_candidates = db.query(Candidate).filter(Candidate.uploaded_by == user_id).all()
        candidate_resumes = {c.id: c.resume_text for c in all_candidates}

        raw_results = screening_service.screen_candidates(
            jd_text=jd.description,
            top_n=top_n,
            candidate_resumes=candidate_resumes,
        )

        db.query(ScreeningResult).filter(ScreeningResult.job_description_id == jd.id).delete()

        count = 0
        for raw in raw_results:
            candidate = db.query(Candidate).filter(Candidate.id == raw["candidate_id"], Candidate.uploaded_by == user_id).first()
            if not candidate:
                continue

            screening_result = ScreeningResult(
                job_description_id=jd.id,
                candidate_id=candidate.id,
                match_score=raw["match_score"],
                match_justification=raw["match_justification"],
            )
            db.add(screening_result)
            count += 1
            
        db.commit()

        # Track exact tokens directly from Gemini API
        from backend.services.token_service import get_gemini_embedding_tokens
        gen_tokens = sum(r.get("tokens", 0) for r in raw_results)
        emb_tokens = get_gemini_embedding_tokens(jd.description)
        if gen_tokens > 0 or emb_tokens > 0:
            add_tokens_sync(user_id, generative_tokens=gen_tokens, embedding_tokens=emb_tokens)

        duration_seconds = round(time.time() - start_time, 2)
        return {"screened_count": count, "duration_seconds": duration_seconds}
    except Exception as e:
        logger.error(f"Screening pipeline failed: {e}")
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(name="tasks.run_crewai_analysis")
def run_crewai_analysis_task(user_id: str, conversation_id: str, job_data: dict, user_bio: str):
    """Run full CrewAI analysis on a job."""
    db: Session = SessionLocal()
    try:
        current_user = db.query(User).filter(User.id == user_id).first()
        convo = db.query(Conversation).filter(
            Conversation.id == conversation_id, 
            Conversation.user_id == user_id
        ).first()

        if not convo or not current_user or not convo.resume_text:
            return {"error": "Invalid conversation or missing resume"}

        # Run the full analysis pipeline
        result = run_full_analysis(job_data, convo.resume_text, user_bio, current_user.skills)

        # Save generated documents
        job_title = (
            job_data.get("PositionTitle")
            or job_data.get("position_title")
            or job_data.get("title")
            or "Unknown"
        )

        if result.get("cover_letter"):
            save_cover_letter(current_user.id, job_title, result["cover_letter"])

        if result.get("resume_tweaks"):
            save_generated_resume(current_user.id, job_title, result["resume_tweaks"])

        analysis_payload = {
            "jd_summary": result.get("jd_summary", ""),
            "resume_tweaks": result.get("resume_tweaks", ""),
            "cover_letter": result.get("cover_letter", ""),
            "company_profile": result.get("company_profile", ""),
            "interview_prep": result.get("interview_prep", ""),
            "hiring_score": result.get("hiring_score", 50),
            "hiring_score_reasoning": result.get("hiring_score_reasoning", ""),
        }

        # Save as conversation messages
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=json.dumps(analysis_payload),
            metadata_={
                "type": "job_analysis",
                "job_title": job_title,
            },
        )
        db.add(assistant_msg)
        
        # Track exact tokens generated across all agents directly from Gemini API
        total_tokens = result.get("total_tokens", 0)
        if total_tokens > 0:
            add_tokens_sync(user_id, generative_tokens=total_tokens)

        import datetime
        convo.updated_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()
        
        return {
            "status": "success",
            "job_title": job_title,
            "analysis": analysis_payload,
        }
    except Exception as e:
        logger.error(f"CrewAI analysis failed: {e}")
        return {"error": str(e)}
    finally:
        db.close()
