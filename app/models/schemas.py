"""Pydantic schemas for API request/response models."""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """A single chat message."""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    message: str
    provider: str | None = None


class ChatResponse(BaseModel):
    """Response body for chat endpoint."""
    response: str
    provider: str
    action_taken: str | None = None


class TaskCreate(BaseModel):
    """Schema for creating a task."""
    title: str
    description: str = ""
    priority: str = "medium"  # low, medium, high
    due_date: datetime | None = None


class TaskResponse(BaseModel):
    """Schema for task response."""
    id: int
    title: str
    description: str
    priority: str
    completed: bool
    due_date: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReminderCreate(BaseModel):
    """Schema for creating a reminder."""
    message: str
    remind_at: datetime


class ReminderResponse(BaseModel):
    """Schema for reminder response."""
    id: int
    message: str
    remind_at: datetime
    triggered: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NoteCreate(BaseModel):
    """Schema for creating a note."""
    title: str
    content: str
    tags: str = ""  # comma-separated tags


class NoteResponse(BaseModel):
    """Schema for note response."""
    id: int
    title: str
    content: str
    tags: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    available_providers: list[str] = []


class WebSocketMessage(BaseModel):
    """Message format for WebSocket communication."""
    type: str  # "chat", "action", "confirm", "status"
    content: str
    provider: str | None = None
    action: str | None = None
    params: dict | None = None
    requires_confirmation: bool = False
