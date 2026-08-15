from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from backend.config import settings
from backend.database import get_db
from backend.deps import get_current_user
from backend.models.user import User
from backend.models.conversation import Conversation, Message
from backend.schemas.job import JobAnalysisRequest
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.schemas.hr import TaskResponse
from backend.tasks import run_crewai_analysis_task
from backend.middleware.agentops import get_agentops_callback_handler

router = APIRouter(prefix="/conversations", tags=["Agents"])


@router.post("/{conversation_id}/analyze-job", response_model=TaskResponse)
async def analyze_job(
    conversation_id: str,
    body: JobAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run full CrewAI analysis on a job: JD summary, resume tweaks, cover letter."""
    # Validate conversation
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
    )
    convo = result.scalar_one_or_none()
    if not convo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    if not convo.resume_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a resume first.",
        )

    task = run_crewai_analysis_task.delay(
        current_user.id,
        conversation_id,
        body.job_data,
        body.user_bio
    )

    return TaskResponse(task_id=task.id, status="Processing job analysis")


@router.post("/{conversation_id}/chat", response_model=ChatResponse)
async def chat_followup(
    conversation_id: str,
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Answer a follow-up question based on the job context asynchronously."""
    # Validate conversation
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
    )
    convo = result.scalar_one_or_none()
    if not convo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    # Enforce follow-up messages limit check
    count_result = await db.execute(
        select(func.count(Message.id))
        .where(Message.conversation_id == conversation_id, Message.role == "user")
    )
    user_messages_count = count_result.scalar_one()

    if user_messages_count >= current_user.max_messages_per_conversation:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Follow-up limit exceeded. You can ask up to {current_user.max_messages_per_conversation} follow-up questions per conversation (Current: {user_messages_count})."
        )

    # Use LangChain to query the model asynchronously
    try:
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
        
        response = await llm.ainvoke(messages)
        
        # Safely extract text content from LLM response
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
        # Track tokens directly from Gemini API response
        from backend.services.token_service import extract_gemini_generation_tokens, add_tokens_async
        token_count = extract_gemini_generation_tokens(response)
        if token_count > 0:
            await add_tokens_async(current_user.id, generative_tokens=token_count)

        convo.updated_at = datetime.now(timezone.utc)
        await db.commit()
        
        return ChatResponse(reply=reply_text)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}",
        )
