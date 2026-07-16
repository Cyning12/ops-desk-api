"""SiliconFlow provider."""
from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterable

import httpx

from app.config import settings
from app.llm.model_catalog import get_default_model
from app.llm.providers.base import BaseProviderImpl
from app.llm.schema import LlmChunk, LlmMessage, LlmProviderError


class SiliconFlowProvider(BaseProviderImpl):
    """SiliconFlow API provider (OpenAI-compatible)."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self.base_url = base_url or settings.siliconflow_base_url
        self.api_key = api_key or settings.siliconflow_api_key

    async def complete(self, messages: Iterable[LlmMessage], model: str | None = None) -> str:
        """Non-streaming completion by aggregating the stream."""
        parts: list[str] = []
        async for chunk in self.complete_stream(messages, model=model):
            parts.append(chunk.content)
        return "".join(parts)

    async def complete_stream(
        self,
        messages: Iterable[LlmMessage],
        model: str | None = None,
    ) -> AsyncIterator[LlmChunk]:
        """Streaming completion."""
        api_key = self._require_api_key(self.api_key, "SiliconFlow")
        resolved_model = model or get_default_model("siliconflow")

        request_body = {
            "model": resolved_model,
            "messages": self._messages_to_openai(messages),
            "stream": True,
        }

        timeout = httpx.Timeout(connect=10.0, read=180.0, write=30.0, pool=5.0)
        try:
            async with (
                httpx.AsyncClient(base_url=self.base_url, timeout=timeout) as client,
                client.stream(
                    "POST",
                    "/chat/completions",
                    json=request_body,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream",
                    },
                ) as response,
            ):
                await response.aread()  # start request to get status code
                if response.status_code >= 400:
                    await self._raise_for_status(response)

                async for line in response.aiter_lines():
                    chunk = self._parse_sse_line(line)
                    if chunk is not None:
                        yield chunk
        except httpx.HTTPStatusError as exc:
            await self._raise_for_status(exc.response)
        except httpx.RequestError as exc:
            raise LlmProviderError(
                f"SiliconFlow request failed: {exc}",
                retryable=True,
            ) from exc

    def _parse_sse_line(self, line: str) -> LlmChunk | None:
        """Parse a single SSE line into an LlmChunk if it carries content."""
        line = line.strip()
        if not line.startswith("data: "):
            return None
        data = line[len("data: "):].strip()
        if data == "[DONE]":
            return None

        try:
            payload = json.loads(data)
        except json.JSONDecodeError as exc:
            raise LlmProviderError(
                f"Failed to parse SiliconFlow SSE payload: {exc}",
                retryable=True,
            ) from exc

        choices = payload.get("choices") or []
        if not choices:
            return None
        delta = choices[0].get("delta") or {}
        content = delta.get("content") or ""
        if not content:
            return None
        return LlmChunk(content=content)

    async def _raise_for_status(self, response: httpx.Response) -> None:
        """Raise LlmProviderError from an HTTP error response."""
        status_code = response.status_code
        try:
            body = await response.aread()
            detail = body.decode("utf-8", errors="replace")[:500]
        except Exception:  # pragma: no cover - defensive
            detail = "unknown"

        retryable = status_code in (408, 429) or status_code >= 500
        raise LlmProviderError(
            f"SiliconFlow API error {status_code}: {detail}",
            retryable=retryable,
            status_code=status_code,
        )
