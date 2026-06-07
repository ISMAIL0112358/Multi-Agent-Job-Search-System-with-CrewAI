from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    job_context: dict

class ChatResponse(BaseModel):
    reply: str
