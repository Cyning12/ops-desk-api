"""Ops Chat · 可选 LLM tracing（Langfuse · env 开关 · 未开启时 no-op）。

移植自 Ink `api/ops/tracing.py`（2026-08-10），裁剪为 langfuse-only
（langsmith 支路未启用，需要时照 Ink 原文件补回）。

主控开关：环境变量 `OPS_CHAT_TRACER=langfuse` + `LANGFUSE_PUBLIC_KEY` /
`LANGFUSE_SECRET_KEY`（+ 可选 `LANGFUSE_BASE_URL`，默认官方云；
Ink 账号在 jp 区：https://jp.cloud.langfuse.com）。
未开启时零成本、不报错、不引入新依赖（langfuse SDK 为可选 import）。

热路径用法：
- `@traceable(name=..., run_type="tool"|"llm"|"retriever"|"chain")`：包函数生成 observation
- `trace_span(name, run_type=..., **metadata)`：with 块生成 span
- `update_current_span_metadata({...})`：给当前 observation 附加结构化 metadata
- `update_current_generation_usage(usage)`：同步 LLM usage 到当前 generation
- `flush_traces()`：短脚本/评测结束前 flush（服务进程由 SDK 后台批量上报，无需调）
"""
from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

_RUN_TYPE_TO_AS_TYPE: dict[str, str] = {
    "llm": "generation",
    "chain": "chain",
    "tool": "tool",
    "retriever": "retriever",
}


def _truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes")


def _langfuse_configured() -> bool:
    return bool(
        (os.getenv("LANGFUSE_PUBLIC_KEY") or "").strip()
        and (os.getenv("LANGFUSE_SECRET_KEY") or "").strip()
    )


def tracing_enabled() -> bool:
    """是否向 Langfuse 发送 trace。主开关 OPS_CHAT_TRACER，兼容旧 LANGFUSE_TRACING。"""
    if os.getenv("OPS_CHAT_TRACER", "").strip().lower() == "langfuse":
        return _langfuse_configured()
    # 向后兼容旧配置；未知 OPS_CHAT_TRACER 值视为关闭，避免拼写错误静默启用
    return _truthy("LANGFUSE_TRACING") and _langfuse_configured()


def traceable(*decorator_args: Any, **decorator_kwargs: Any) -> Callable[[F], F] | F:
    """与 langfuse.observe 签名近似；未开启或未装 SDK 时透传原函数。"""

    def _wrap(fn: F) -> F:
        if not tracing_enabled():
            return fn
        try:
            from langfuse import observe
        except ImportError:
            return fn

        observe_kwargs: dict[str, Any] = {}
        name = decorator_kwargs.get("name")
        run_type = decorator_kwargs.get("run_type")
        if name is not None:
            observe_kwargs["name"] = name
        as_type = decorator_kwargs.get("as_type") or _RUN_TYPE_TO_AS_TYPE.get(
            run_type if isinstance(run_type, str) else ""
        )
        if as_type:
            observe_kwargs["as_type"] = as_type
        for key in ("capture_input", "capture_output"):
            if key in decorator_kwargs:
                observe_kwargs[key] = decorator_kwargs[key]
        return observe(**observe_kwargs)(fn) if observe_kwargs else observe(fn)

    if len(decorator_args) == 1 and callable(decorator_args[0]) and not decorator_kwargs:
        return _wrap(decorator_args[0])
    return _wrap


@contextmanager
def trace_span(name: str, *, run_type: str | None = None, **metadata: Any) -> Iterator[None]:
    """上下文管理器：with 块生成 span；未开启时零成本。"""
    if not tracing_enabled():
        yield None
        return
    try:
        from langfuse import get_client
    except Exception:
        yield None
        return

    as_type = _RUN_TYPE_TO_AS_TYPE.get(run_type or "span", "span")
    model = metadata.pop("model", None)
    try:
        client = get_client()
        # SDK v3 正统上下文管理器：with 期间该 observation 即为 current，
        # with 体内的 update_current_generation / metadata 更新才会正确落点
        if as_type == "generation":
            cm = client.start_as_current_generation(
                name=name, model=model, metadata=metadata or None
            )
        else:
            cm = client.start_as_current_span(name=name, metadata=metadata or None)
    except Exception:
        yield None
        return
    # 注意：with 体内的异常必须正常传播（cm.__exit__ 记录错误后抛出），
    # 不能再 yield（否则 generator didn't stop after throw()）
    with cm:
        yield None


def update_current_span_metadata(metadata: dict[str, Any]) -> None:
    """为当前 observation 附加 metadata；未开启或失败时静默跳过。"""
    if not tracing_enabled():
        return
    try:
        from langfuse import get_client

        get_client().update_current_span(metadata=metadata)
    except Exception:
        return


def update_current_generation_usage(usage: Any) -> None:
    """将 LLM usage 同步到当前 generation；未开启或失败时静默跳过。"""
    if not tracing_enabled():
        return
    try:
        from langfuse import get_client

        get_client().update_current_generation(
            usage_details={
                "input": int(usage.prompt_tokens or 0),
                "output": int(usage.completion_tokens or 0),
            }
        )
    except Exception:
        return


def flush_traces() -> None:
    """短脚本/评测结束前 flush；未开启或无 client 时静默跳过。"""
    if not tracing_enabled():
        return
    try:
        from langfuse import get_client

        get_client().flush()
    except Exception:
        return
