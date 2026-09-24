"""Jarvis AI Agent - FastAPI application entry point."""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.config import get_settings
from app.db.database import init_db
from app.api.routes import router
from app.api.websocket import ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    await init_db()
    yield
    # Shutdown


app = FastAPI(
    title="Jarvis AI Agent",
    description="A modular personal productivity AI assistant",
    version="1.0.0",
    lifespan=lifespan,
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
        host=getattr(settings, "app_host", "127.0.0.1"),
        port=getattr(settings, "app_port", 8000),
        reload=getattr(settings, "debug", True),
    )
