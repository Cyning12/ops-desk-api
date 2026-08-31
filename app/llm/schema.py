"""LLM provider shared schemas."""
from __future__ import annotations

from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass


@dataclass
class LlmMessage:
    """Unified LLM message."""

    role: str
    content: str


@dataclass
class LlmUsage:
    """Token usage。

    ``cached_input_tokens``：缓存命中 input（SiliconFlow:
    ``prompt_cache_hit_tokens`` / ``prompt_tokens_details.cached_tokens``）。
    ``prompt_tokens`` 与官方一致，通常 **含** 缓存部分。
    """

    prompt_tokens: int
    completion_tokens: int
    cached_input_tokens: int = 0

    @classmethod
    def from_provider_usage(cls, usage_meta: object) -> LlmUsage | None:
        """从 OpenAI 兼容 usage 对象构造；非法则 None。"""
        if not isinstance(usage_meta, dict):
            return None
        try:
            prompt = int(usage_meta.get("prompt_tokens") or 0)
            completion = int(usage_meta.get("completion_tokens") or 0)
        except (TypeError, ValueError):
            return None
        if prompt < 0 or completion < 0:
            return None

        cached = 0
        hit = usage_meta.get("prompt_cache_hit_tokens")
        if hit is not None:
            try:
                cached = int(hit)
            except (TypeError, ValueError):
                cached = 0
        else:
            details = usage_meta.get("prompt_tokens_details")
            if isinstance(details, dict) and details.get("cached_tokens") is not None:
                try:
                    cached = int(details.get("cached_tokens") or 0)
                except (TypeError, ValueError):
                    cached = 0
        if cached < 0:
            cached = 0

        return cls(
            prompt_tokens=prompt,
            completion_tokens=completion,
            cached_input_tokens=cached,
        )


@dataclass
class LlmChunk:
    """Streaming chunk."""

    content: str
    meta: dict | None = None  # out-of-band metadata, e.g. model.fallback events


class LlmProviderError(Exception):
    """Provider-level error with retryability hint."""

    def __init__(
        self,
        message: str,
        *,
        retryable: bool = False,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.status_code = status_code


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
