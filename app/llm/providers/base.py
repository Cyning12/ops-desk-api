"""Base provider implementation."""
from collections.abc import Iterable

from app.llm.schema import BaseProvider, LlmMessage


class BaseProviderImpl(BaseProvider):
    """Shared provider helpers."""

    @staticmethod
    def _messages_to_openai(messages: Iterable[LlmMessage]) -> list[dict]:
        """Convert internal messages to OpenAI-compatible format."""
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    def _require_api_key(self, key: str | None, name: str) -> str:
        """Validate API key presence."""
        if not key:
            raise ValueError(f"{name} API key is not configured")
        return key
