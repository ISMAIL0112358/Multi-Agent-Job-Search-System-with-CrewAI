import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend.database import Base, async_engine
from backend.middleware.agentops import init_agentops
from backend.routers import auth, conversations, resume, jobs, agents, hr, tasks

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup
    logger.info("Creating database tables asynchronously...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created.")

        # Ensure user limit columns exist (Alters existing table for schema updates)
        for col, default_val in [
            ("max_resumes", 50),
            ("resumes_count", 0),
            ("max_jds", 10),
            ("jds_count", 0),
            ("max_screenings", 50),
            ("screenings_count", 0),
            ("max_conversations", 10),
            ("conversations_count", 0),
            ("max_messages_per_conversation", 50)
        ]:
            try:
                await conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} INTEGER DEFAULT {default_val} NOT NULL;"))
                logger.info(f"Added column {col} to users table.")
            except Exception:
                # Column already exists or table does not support it, ignore
                pass

    # Ensure ChromaDB persist directory exists
    import os
    from backend.config import settings
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    logger.info("ChromaDB persist directory ready: %s", settings.CHROMA_PERSIST_DIR)

    logger.info("Initializing AgentOps...")
    init_agentops()

    yield

    # Shutdown
    logger.info("Closing async database connection pool...")
    await async_engine.dispose()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title="AI Job Hunt & Recruitment Assistant",
    description="An AI-driven job hunt and talent recruitment platform using cooperative CrewAI agents to assist both candidates and HR personnel",
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
app.include_router(tasks.router, prefix="/api")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}
