"""
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import health, chat, sessions
from app.core.database import init_db


# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A context-aware chatbot API powered by Ollama, Qdrant, and PostgreSQL"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event - initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")


# Include routers
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(sessions.router)


@app.get("/", tags=["root"])
def root():
    """Root endpoint"""
    return {
        "message": "Welcome to the Chatbot API",
        "version": settings.app_version,
        "docs": "/docs"
    }

