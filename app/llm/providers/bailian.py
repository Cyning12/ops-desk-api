"""Bailian (DashScope) provider."""
from collections.abc import AsyncIterator, Iterable

from app.llm.providers.base import BaseProviderImpl
from app.llm.schema import LlmChunk, LlmMessage


class BailianProvider(BaseProviderImpl):
    """Alibaba Bailian / DashScope provider."""

    async def complete(self, messages: Iterable[LlmMessage], model: str | None = None) -> str:
        """Non-streaming completion."""
        # TODO: implement with httpx / openai client
        return ""

    async def complete_stream(
        self, messages: Iterable[LlmMessage], model: str | None = None
    ) -> AsyncIterator[LlmChunk]:
        """Streaming completion with fallback chain."""
        # TODO: implement streaming + fallback
        yield LlmChunk(content="")
