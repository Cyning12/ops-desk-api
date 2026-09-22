"""SiliconFlow provider."""
from __future__ import annotations

from collections.abc import AsyncIterator, Iterable

from app.config import settings
from app.llm.model_catalog import get_default_model
from app.llm.providers.base import BaseProviderImpl
from app.llm.schema import LlmChunk, LlmMessage


class SiliconFlowProvider(BaseProviderImpl):
    """SiliconFlow API provider (OpenAI-compatible)."""

    PROVIDER_NAME = "siliconflow"

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self.base_url = base_url or settings.siliconflow_base_url
        self.api_key = api_key or settings.siliconflow_api_key

    async def complete(self, messages: Iterable[LlmMessage], model: str | None = None) -> str:
        """Non-streaming completion by aggregating the stream."""
        return await self._complete_from_stream(messages, model=model)

    async def complete_stream(
        self,
        messages: Iterable[LlmMessage],
        model: str | None = None,
    ) -> AsyncIterator[LlmChunk]:
        """Streaming completion."""
        api_key = self._require_api_key(self.api_key, "SiliconFlow")
        resolved_model = model or get_default_model("siliconflow")
        async for chunk in self._stream_openai_compatible(
            base_url=self.base_url,
            api_key=api_key,
            model=resolved_model,
            messages=messages,
        ):
            yield chunk
