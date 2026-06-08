import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import Base, engine
from backend.middleware.agentops import init_agentops
from backend.routers import auth, conversations, resume, jobs, agents, hr

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created.")

    # Ensure ChromaDB persist directory exists
    import os
    from backend.config import settings
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    logger.info("ChromaDB persist directory ready: %s", settings.CHROMA_PERSIST_DIR)

    logger.info("Initializing AgentOps...")
    init_agentops()

    yield

    # Shutdown
    logger.info("Application shutting down.")


app = FastAPI(
    title="AI Job Hunt Assistant",
    description="Multi-agent job search system with CrewAI",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers under /api prefix
app.include_router(auth.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(resume.router, prefix="/api")
app.include_router(resume.user_resumes_router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(hr.router, prefix="/api")


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}
