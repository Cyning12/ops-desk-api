"""LLM provider shared schemas."""
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass


@dataclass
class LlmMessage:
    """Unified LLM message."""

    role: str
    content: str


@dataclass
class LlmUsage:
    """Token usage."""

    prompt_tokens: int
    completion_tokens: int


@dataclass
class LlmChunk:
    """Streaming chunk."""

    content: str


class BaseProvider:
    """Base class for LLM providers."""

    async def complete(self, messages: Iterable[LlmMessage], model: str | None = None) -> str:
        """Non-streaming completion."""
        raise NotImplementedError

    async def complete_stream(
        self, messages: Iterable[LlmMessage], model: str | None = None
    ) -> AsyncIterator[LlmChunk]:
        """Streaming completion."""
        raise NotImplementedError
