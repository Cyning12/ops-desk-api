"""Shared Pydantic models for Ops Desk endpoints."""
from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    """Generic API response wrapper."""

    data: Any | None = None
    error: str | None = None
