"""Chat Pydantic schemas."""
from datetime import datetime

from pydantic import BaseModel, Field


class ChatStreamRequest(BaseModel):
    """Request body for chat stream."""

    message: str = Field(..., min_length=1)
    session_id: str | None = None
    model: str | None = None


class ChatModelsResponse(BaseModel):
    """Available models response."""

    provider: str
    default_model: str
    models: list[dict]


class ChatSessionOut(BaseModel):
    """Chat session response for iOS and clients."""

    id: str
    user_id: str
    title: str | None
    created_at: datetime
    updated_at: datetime
