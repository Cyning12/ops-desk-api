"""Base provider implementation."""
from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterable

import httpx

from app.llm.schema import BaseProvider, LlmChunk, LlmMessage, LlmProviderError


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

    @staticmethod
    async def _stream_openai_compatible(
        base_url: str,
        api_key: str,
        model: str,
        messages: Iterable[LlmMessage],
    ) -> AsyncIterator[LlmChunk]:
        """Stream completions from an OpenAI-compatible chat endpoint."""
        request_body = {
            "model": model,
            "messages": BaseProviderImpl._messages_to_openai(messages),
            "stream": True,
            # 末帧回传 token usage（OpenAI 兼容），供观测上报
            "stream_options": {"include_usage": True},
        }

        timeout = httpx.Timeout(connect=10.0, read=180.0, write=30.0, pool=5.0)
        try:
            async with (
                httpx.AsyncClient(base_url=base_url, timeout=timeout) as client,
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
                    await BaseProviderImpl._raise_for_status(response)

                async for line in response.aiter_lines():
                    chunk = BaseProviderImpl._parse_sse_line(line)
                    if chunk is not None:
                        yield chunk
        except httpx.HTTPStatusError as exc:
            await BaseProviderImpl._raise_for_status(exc.response)
        except httpx.RequestError as exc:
            raise LlmProviderError(
                f"LLM request failed: {exc}",
                retryable=True,
            ) from exc

    @staticmethod
    def _parse_sse_line(line: str) -> LlmChunk | None:
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
                f"Failed to parse SSE payload: {exc}",
                retryable=True,
            ) from exc

        choices = payload.get("choices") or []
        if not choices:
            # include_usage 末帧：choices 为空、携带 usage
            usage = payload.get("usage")
            if usage:
                return LlmChunk(content="", meta={"usage": usage})
            return None
        delta = choices[0].get("delta") or {}
        content = delta.get("content") or ""
        if not content:
            return None
        return LlmChunk(content=content)

    @staticmethod
    async def _raise_for_status(response: httpx.Response) -> None:
        """Raise LlmProviderError from an HTTP error response."""
        status_code = response.status_code
        try:
            body = await response.aread()
            detail = body.decode("utf-8", errors="replace")[:500]
        except Exception:  # pragma: no cover - defensive
            detail = "unknown"

        retryable = status_code in (408, 429) or status_code >= 500
        raise LlmProviderError(
            f"LLM API error {status_code}: {detail}",
            retryable=retryable,
            status_code=status_code,
        )
