"""Base provider implementation."""
from __future__ import annotations

import functools
import json
import logging
from collections.abc import AsyncIterator, Callable, Iterable
from contextlib import suppress

import httpx
import pybreaker

from app.llm import circuit as llm_circuit
from app.llm import retry as llm_retry
from app.llm import usage as llm_usage
from app.llm.schema import BaseProvider, LlmChunk, LlmMessage, LlmProviderError, LlmUsage

logger = logging.getLogger(__name__)


class BaseProviderImpl(BaseProvider):
    """Shared provider helpers."""

    #: provider 名（熔断 breaker 粒度 / usage 落表 / 重试日志）；未声明用类名
    PROVIDER_NAME: str | None = None

    #: 边界包装（重试+熔断+usage 落表）开关。Bailian 关闭：fallback 链内逐候选
    #: 自走 _resilient_stream（先同模型退避重试、再换模型，链语义不变）。
    _boundary_resilience: bool = True

    def __init_subclass__(cls, **kwargs) -> None:
        """给每个子类的 complete_stream 统一套韧性边界（llm-layer-hardening）。

        施加面钉死在 BaseProviderImpl 边界：所有继承本类并实现
        complete_stream 的 provider（含测试 fake）自动获得
        熔断 guard + 退避重试 + usage 落表观测；_boundary_resilience=False
        的子类（Bailian）在 fallback 链内逐候选自走 _resilient_stream。
        """
        super().__init_subclass__(**kwargs)
        fn = cls.__dict__.get("complete_stream")
        if fn is None or not getattr(cls, "_boundary_resilience", True):
            return

        @functools.wraps(fn)
        async def complete_stream(self, messages, model=None):  # noqa: ANN001,ANN202
            async for chunk in self._resilient_stream(
                lambda: fn(self, messages, model=model),
                model=model or "",
            ):
                yield chunk

        cls.complete_stream = complete_stream

    def _provider_name(self) -> str:
        return self.PROVIDER_NAME or type(self).__name__

    async def _resilient_stream(
        self,
        stream_factory: Callable[[], AsyncIterator[LlmChunk]],
        *,
        model: str,
    ) -> AsyncIterator[LlmChunk]:
        """统一韧性边界：熔断 guard（外）+ 退避重试（内）+ usage 落表观测。

        - 熔断：provider 级 breaker 逐次 __anext__ 过 guard；open 时零出网
          立即 circuit_open（retryable=False）；重试在 guard 内发生并逐次
          计入失败；业务错误（retryable=False）不计数。
        - 重试：仅 LlmProviderError(retryable=True) 且尚未吐首 content
          chunk；耗尽抛原始错误（不包装丢根因）。流中已吐正文后出错 →
          零重试零换模型，原样上抛走既有 error 事件路径。
        - usage：见到 usage 末帧落 ops_llm_usage（无帧不落，不写 0 假账；
          落表故障 log+计数，不挡主答）。
        """
        provider = self._provider_name()
        cfg = llm_retry.retry_config()
        cb = llm_circuit.breaker_for(provider) if llm_circuit.enabled() else None
        attempts = 0
        while True:
            attempts += 1
            emitted_content = False
            agen = stream_factory()
            try:
                while True:
                    done = False
                    try:
                        if cb is not None:
                            # yield 在 guard 外：消费者取消（GeneratorExit）
                            # 永远不会穿过 calling() 被误计为失败
                            with cb.calling():
                                try:
                                    chunk = await agen.__anext__()
                                except StopAsyncIteration:
                                    done = True
                        else:
                            try:
                                chunk = await agen.__anext__()
                            except StopAsyncIteration:
                                done = True
                    except pybreaker.CircuitBreakerError:
                        raise llm_circuit.circuit_open_error(provider, cb) from None  # type: ignore[arg-type]
                    if done:
                        return
                    if chunk.content:
                        emitted_content = True
                    usage_meta = (chunk.meta or {}).get("usage")
                    if usage_meta:
                        await self._record_usage_safe(
                            usage_meta,
                            provider=provider,
                            model=model,
                            attempts=attempts,
                        )
                    yield chunk
            except LlmProviderError as exc:
                if (
                    emitted_content
                    or not cfg.enabled
                    or not exc.retryable
                    or attempts >= cfg.max_attempts
                ):
                    raise
                delay = llm_retry.backoff_delay(attempts - 1, cfg)
                logger.info(
                    "llm_retry attempt=%d delay=%.2fs provider=%s model=%s",
                    attempts,
                    delay,
                    provider,
                    model,
                )
                await llm_retry.sleep(delay)
            finally:
                with suppress(Exception):
                    await agen.aclose()

    @staticmethod
    async def _record_usage_safe(
        usage_meta: object,
        *,
        provider: str,
        model: str,
        attempts: int,
    ) -> None:
        """usage 末帧落 ops_llm_usage；解析失败/落表故障不挡主答（不写 0 假账）。"""
        parsed = LlmUsage.from_provider_usage(usage_meta)
        if parsed is None:
            return
        try:
            await llm_usage.record_llm_usage(
                parsed, provider=provider, model=model, attempts=attempts
            )
        except Exception:  # pragma: no cover - record_llm_usage 已内 catch，此为兜底
            logger.warning("ops_llm_usage record hook failed", exc_info=True)

    @staticmethod
    def _messages_to_openai(messages: Iterable[LlmMessage]) -> list[dict]:
        """Convert internal messages to OpenAI-compatible format."""
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    def _require_api_key(self, key: str | None, name: str) -> str:
        """Validate API key presence."""
        if not key:
            raise ValueError(f"{name} API key is not configured")
        return key

    async def _complete_from_stream(
        self,
        messages: Iterable[LlmMessage],
        model: str | None = None,
    ) -> str:
        """聚合 complete_stream：拼正文，usage / I/O 末帧副作用上报。"""
        parts: list[str] = []
        usage_meta: object | None = None
        async for chunk in self.complete_stream(messages, model=model):
            meta = chunk.meta or {}
            if meta.get("usage"):
                usage_meta = meta["usage"]
                continue
            if meta.get("event_type") == "model.fallback":
                continue
            parts.append(chunk.content)
        text = "".join(parts)
        if usage_meta is not None:
            self._report_complete_usage(usage_meta)
        self._report_complete_io(messages, text)
        return text

    @staticmethod
    def _report_complete_usage(usage_meta: object) -> None:
        """把 usage 报到当前 generation；tracing 关或失败则静默。"""
        parsed = LlmUsage.from_provider_usage(usage_meta)
        if parsed is None:
            return
        try:
            # 函数内 lazy import：llm 不硬依赖 ops，图谱出边保持「—」
            from app.ops.tracing import tracing_enabled, update_current_generation_usage

            if not tracing_enabled():
                return
            update_current_generation_usage(parsed)
        except Exception:
            return

    @staticmethod
    def _report_complete_io(messages: Iterable[LlmMessage], output: str) -> None:
        """complete 边界写截断 Input/Output；失败不挡主答。"""
        try:
            from app.ops.tracing import tracing_enabled, update_current_generation_io

            if not tracing_enabled():
                return
            # 紧凑文本：role: content 行，避免巨型 JSON
            lines = [f"{m.role}: {m.content}" for m in messages]
            update_current_generation_io(input="\n".join(lines), output=output or "")
        except Exception:
            return

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
                # headers 已到即可读 status；禁止 aread() 整包缓冲（会破坏 token 真流式）
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
