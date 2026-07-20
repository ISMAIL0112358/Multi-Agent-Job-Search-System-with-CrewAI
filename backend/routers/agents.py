import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import get_current_user
from backend.models.user import User
from backend.models.conversation import Conversation, Message
from backend.schemas.job import JobAnalysisRequest, JobAnalysisResponse
from backend.services.agent_service import run_full_analysis
from backend.services.storage_service import save_cover_letter, save_generated_resume

router = APIRouter(prefix="/conversations", tags=["Agents"])


@router.post("/{conversation_id}/analyze-job", response_model=JobAnalysisResponse)
def analyze_job(
    conversation_id: str,
    body: JobAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run full CrewAI analysis on a job: JD summary, resume tweaks, cover letter."""
    # Validate conversation
    convo = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not convo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    if not convo.resume_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a resume first.",
        )

    # Run the full analysis pipeline
    try:
        result = run_full_analysis(body.job_data, convo.resume_text, body.user_bio, current_user.skills)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent pipeline failed: {str(e)}",
        )

    # Save generated documents to user's folders
    job_title = body.job_data.get("PositionTitle", body.job_data.get("position_title", "Unknown"))

    if result["cover_letter"]:
        save_cover_letter(current_user.id, job_title, result["cover_letter"])

    if result["resume_tweaks"]:
        save_generated_resume(current_user.id, job_title, result["resume_tweaks"])

    # Save as conversation messages
    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=json.dumps({
            "jd_summary": result["jd_summary"],
            "resume_tweaks": result["resume_tweaks"],
            "cover_letter": result["cover_letter"],
            "company_profile": result["company_profile"],
            "interview_prep": result["interview_prep"],
            "hiring_score": result["hiring_score"],
            "hiring_score_reasoning": result["hiring_score_reasoning"],
        }),
        metadata_={
            "type": "job_analysis",
            "job_title": job_title,
        },
    )
    db.add(assistant_msg)

    convo.updated_at = datetime.now(timezone.utc)
    db.commit()

    return JobAnalysisResponse(**result)


from backend.schemas.chat import ChatRequest, ChatResponse
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from backend.config import settings

@router.post("/{conversation_id}/chat", response_model=ChatResponse)
def chat_followup(
    conversation_id: str,
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Answer a follow-up question based on the job context."""
    # Validate conversation
    convo = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    # Enforce follow-up messages limit check
    user_messages_count = db.query(Message).filter(
        Message.conversation_id == conversation_id,
        Message.role == "user"
    ).count()
    if user_messages_count >= current_user.max_messages_per_conversation:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Follow-up limit exceeded. You can ask up to {current_user.max_messages_per_conversation} follow-up questions per conversation (Current: {user_messages_count})."
        )

    # Use LangChain to query the model directly
    try:
        from backend.middleware.agentops import get_agentops_callback_handler
        handler = get_agentops_callback_handler(tags=["chat-followup"])
        callbacks = [handler] if handler else None

        if settings.ENV == "local":
            llm = ChatOllama(
                model=settings.LOCAL_LLM_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0.3,
                callbacks=callbacks,
            )
        else:
            primary = ChatGoogleGenerativeAI(
                model="gemini-3.1-flash-lite",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.3,
                callbacks=callbacks,
            )
            fallbacks = [
                ChatGoogleGenerativeAI(model=m, google_api_key=settings.GEMINI_API_KEY, temperature=0.3, callbacks=callbacks)
                for m in ["gemini-3-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-2.5-flash"]
            ]
            llm = primary.with_fallbacks(fallbacks)
        
        from langchain_core.messages import HumanMessage, SystemMessage
        
        system_prompt = f"""
        You are a helpful career advisor assisting a user with a job application.
        The user has analyzed a job posting. Here is the context of the job analysis:
        
        Job Title: {body.job_context.get('position_title', 'Unknown')}
        Organization: {body.job_context.get('organization_name', 'Unknown')}
        Job Summary: {body.job_context.get('job_summary', 'Unknown')}
        
        Please answer the user's follow-up question based on this context. Be concise and professional.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=body.message)
        ]
        
        response = llm.invoke(messages)
        
        # Safely extract text content from LLM response (ChatGoogleGenerativeAI can return list of dicts)
        content = response.content
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict):
                    parts.append(part.get("text", str(part)))
                elif isinstance(part, str):
                    parts.append(part)
                else:
                    parts.append(str(part))
            reply_text = "\n".join(parts)
        else:
            reply_text = str(content)
        
        # Save as conversation messages
        user_msg = Message(
            conversation_id=conversation_id,
            role="user",
            content=body.message,
            metadata_={"type": "followup_question"}
        )
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=reply_text,
            metadata_={"type": "followup_answer"}
        )
        db.add(user_msg)
        db.add(assistant_msg)
        
        convo.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        return ChatResponse(reply=reply_text)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}",
        )

