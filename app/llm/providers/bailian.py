"""Bailian (DashScope) provider."""
from __future__ import annotations

from collections.abc import AsyncIterator, Iterable

from app.config import settings
from app.llm.model_catalog import ModelInfo, get_default_model, get_fallback_chain
from app.llm.providers.base import BaseProviderImpl
from app.llm.schema import LlmChunk, LlmMessage, LlmProviderError


class BailianProvider(BaseProviderImpl):
    """Alibaba Bailian / DashScope provider (OpenAI-compatible)."""

    PROVIDER_NAME = "bailian"

    #: 边界包装关闭：fallback 链内**逐候选**走 _resilient_stream（先同模型
    #: 退避重试、再换模型）；链语义 / 顺序 / test_only 过滤不变。
    _boundary_resilience = False

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self.base_url = base_url or settings.bailian_base_url
        self.api_key = api_key or settings.bailian_api_key

    async def complete(self, messages: Iterable[LlmMessage], model: str | None = None) -> str:
        """Non-streaming completion by aggregating the stream."""
        return await self._complete_from_stream(messages, model=model)

    async def complete_stream(
        self,
        messages: Iterable[LlmMessage],
        model: str | None = None,
    ) -> AsyncIterator[LlmChunk]:
        """Streaming completion with internal model fallback chain."""
        api_key = self._require_api_key(self.api_key, "Bailian")
        chain = self._fallback_chain(model)
        last_error: LlmProviderError | None = None

        for idx, candidate in enumerate(chain):
            if idx > 0:
                reason = str(last_error) if last_error else "fallback"
                yield LlmChunk(
                    content="",
                    meta={
                        "event_type": "model.fallback",
                        "from_model": chain[idx - 1].id,
                        "to_model": candidate.id,
                        "reason": reason,
                        "step": "answer",
                    },
                )
            try:
                # 链内每个候选走同一韧性层：先同模型退避重试（首 content
                # chunk 前限定），耗尽再换下一候选（上面已发 model.fallback）
                async for chunk in self._resilient_stream(
                    lambda c=candidate: self._stream_openai_compatible(
                        base_url=self.base_url,
                        api_key=api_key,
                        model=c.id,
                        messages=messages,
                    ),
                    model=candidate.id,
                ):
                    yield chunk
                return
            except LlmProviderError as exc:
                if not exc.retryable:
                    raise
                last_error = exc

        raise LlmProviderError(
            "Bailian fallback chain exhausted",
            retryable=False,
        )

    def _fallback_chain(self, model: str | None) -> list[ModelInfo]:
        """Return fallback chain, filtering test-only models by default."""
        if model:
            return [ModelInfo(id=model, name=model)]

        chain = [info for info in get_fallback_chain("bailian") if not info.test_only]
        if chain:
            return chain

        default = get_default_model("bailian")
        return [ModelInfo(id=default, name=default)]
