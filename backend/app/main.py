"""
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import health, chat


# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A simple chatbot API powered by Ollama and Llama 3"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(chat.router)


@app.get("/", tags=["root"])
def root():
    """Root endpoint"""
    return {
        "message": "Welcome to the Chatbot API",
        "version": settings.app_version,
        "docs": "/docs"
    }

