"""Jarvis AI Agent - FastAPI application entry point."""

import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.config import get_settings
from app.db.database import init_db
from app.api.routes import router
from app.api.websocket import ws_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("jarvis")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Starting Jarvis AI Agent...")
    await init_db()
    logger.info("Database initialized.")
    yield
    logger.info("Shutting down Jarvis AI Agent.")


app = FastAPI(
    title="Jarvis AI Agent",
    description="A modular personal productivity AI assistant",
    version="1.1.0",
    lifespan=lifespan,
)

# CORS middleware — allow frontend dev server to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

# Include routers
app.include_router(router, prefix="/api")
app.include_router(ws_router)


@app.get("/")
async def root():
    """Serve the frontend dashboard."""
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Jarvis AI Agent API", "docs": "/docs"}


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )
