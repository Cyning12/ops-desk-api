"""Ops Chat · 可选 LLM tracing（Langfuse · env 开关 · 未开启时 no-op）。

移植自 Ink `api/ops/tracing.py`（2026-08-10），裁剪为 langfuse-only
（langsmith 支路未启用，需要时照 Ink 原文件补回）。

主控开关：环境变量 `OPS_CHAT_TRACER=langfuse` + `LANGFUSE_PUBLIC_KEY` /
`LANGFUSE_SECRET_KEY`（+ 可选 `LANGFUSE_BASE_URL`，默认官方云；
Ink 账号在 jp 区：https://jp.cloud.langfuse.com）。
环境：仓内 `LANGFUSE_ENV`（默认 `prod`；本机 `.env` 写 `dev`），同步到 SDK
`LANGFUSE_TRACING_ENVIRONMENT`。UI 须选同一 environment，否则像「没有 tracing」。
未开启时零成本、不报错、不引入新依赖（langfuse SDK 为可选 import）。

热路径用法：
- `@traceable(name=..., run_type="tool"|"llm"|"retriever"|"chain")`：包函数生成 observation
- `trace_span(name, run_type=..., **metadata)`：with 块生成 span
- `update_current_span_metadata({...})`：给当前 observation 附加结构化 metadata
- `update_current_generation_usage(usage)`：同步 LLM usage 到当前 generation
- `update_current_generation_io(input=..., output=...)`：截断正文 I/O（complete 边界）
- `score_current_trace(name, value, ...)`：抽样写 score；关 tracing / 采样 miss / 异常 → no-op
- `flush_traces()`：短脚本/评测结束前 flush（服务进程由 SDK 后台批量上报，无需调）

线上抽样：``OPS_EVAL_SCORE_SAMPLE_RATE``（0.0–1.0，默认 ``0`` = 不打分）。
I/O 截断：``OPS_LANGFUSE_IO_TRUNCATE``（字符，默认 ``4000``）。
"""
from __future__ import annotations

import logging
import os
import random
import re
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger(__name__)

_RUN_TYPE_TO_AS_TYPE: dict[str, str] = {
    "llm": "generation",
    "chain": "chain",
    "tool": "tool",
    "retriever": "retriever",
}

# Langfuse 官方约束：小写、数字、连字符、下划线；不能以 langfuse 开头
_ENV_RE = re.compile(r"^(?!langfuse)[a-z0-9-_]{1,40}$")
DEFAULT_LANGFUSE_ENV = "prod"


def _truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes")


def _env(name: str) -> str:
    """读进程环境；剥掉 .env 里误加的引号。"""
    return (os.getenv(name) or "").strip().strip('"').strip("'")


def _langfuse_configured() -> bool:
    return bool(_env("LANGFUSE_PUBLIC_KEY") and _env("LANGFUSE_SECRET_KEY"))


def langfuse_environment() -> str:
    """上报环境：``LANGFUSE_ENV`` 优先，否则 ``LANGFUSE_TRACING_ENVIRONMENT``，默认 ``prod``。

    仓内用短名 ``LANGFUSE_ENV``（dev/prod）；SDK 只认官方键
    ``LANGFUSE_TRACING_ENVIRONMENT``。须在构造 CallbackHandler / get_client 前同步。
    """
    raw = (
        _env("LANGFUSE_ENV") or _env("LANGFUSE_TRACING_ENVIRONMENT") or DEFAULT_LANGFUSE_ENV
    ).lower()
    if not raw:
        return DEFAULT_LANGFUSE_ENV
    if not _ENV_RE.match(raw):
        logger.warning(
            "invalid LANGFUSE_ENV=%r; fallback to %s",
            raw,
            DEFAULT_LANGFUSE_ENV,
        )
        return DEFAULT_LANGFUSE_ENV
    return raw


def ensure_langfuse_environment() -> str:
    """把仓内 ``LANGFUSE_ENV`` 写入 SDK 官方键，避免 UI 环境过滤对不上。"""
    env = langfuse_environment()
    os.environ["LANGFUSE_TRACING_ENVIRONMENT"] = env
    return env


_TRACING_LOGGED = False


def tracing_status_line() -> str:
    """给人看的一行状态：不含密钥。"""
    tracer = _env("OPS_CHAT_TRACER") or "(unset)"
    keys = "yes" if _langfuse_configured() else "no"
    base = _env("LANGFUSE_BASE_URL") or _env("LANGFUSE_HOST") or "(sdk default)"
    env = langfuse_environment()
    on = tracing_enabled()
    return (
        f"langfuse tracing={'on' if on else 'off'} "
        f"OPS_CHAT_TRACER={tracer} keys={keys} LANGFUSE_ENV={env} base={base}"
    )


def log_tracing_startup() -> None:
    """启动时打到 uvicorn 日志（应用 logger 默认不出现在 make dev 终端）。"""
    logging.getLogger("uvicorn.error").info(tracing_status_line())


def tracing_enabled() -> bool:
    """是否向 Langfuse 发送 trace。主开关 OPS_CHAT_TRACER，兼容旧 LANGFUSE_TRACING。"""
    global _TRACING_LOGGED
    if _env("OPS_CHAT_TRACER").lower() == "langfuse":
        on = _langfuse_configured()
    else:
        # 向后兼容旧配置；未知 OPS_CHAT_TRACER 值视为关闭，避免拼写错误静默启用
        on = _truthy("LANGFUSE_TRACING") and _langfuse_configured()
    if on:
        ensure_langfuse_environment()
        if not _TRACING_LOGGED:
            logger.info("langfuse tracing on environment=%s", langfuse_environment())
            _TRACING_LOGGED = True
    return on


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
def trace_span(
    name: str,
    *,
    run_type: str | None = None,
    tags: Sequence[str] | None = None,
    **metadata: Any,
) -> Iterator[None]:
    """上下文管理器：with 块生成 span；未开启时零成本。

    已有父 span 时成为子节点（调用链）；无父时自己成为根 trace。
    ``tags`` 写到 **trace** 上，便于 UI 过滤。
    """
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
    with cm as observation:
        if tags:
            try:
                updater = getattr(observation, "update_trace", None)
                if callable(updater):
                    updater(name=name, tags=list(tags))
                else:
                    client.update_current_trace(name=name, tags=list(tags))
            except Exception:
                logger.debug("langfuse update_trace tags failed", exc_info=True)
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
    """将 LLM usage 同步到当前 generation；未开启或失败时静默跳过。

    Langfuse ``usage_details`` 键：
    - ``input``：非缓存 input（exclusive；= prompt − cached）
    - ``output``：completion
    - ``cached-input-tokens``：缓存命中（对齐 SiliconFlow 账单后缀）
    """
    if not tracing_enabled():
        return
    try:
        from langfuse import get_client

        prompt = int(getattr(usage, "prompt_tokens", 0) or 0)
        output = int(getattr(usage, "completion_tokens", 0) or 0)
        cached = int(getattr(usage, "cached_input_tokens", 0) or 0)
        if cached < 0:
            cached = 0
        # exclusive-bucket：input 不含已计入 cache 的部分
        input_tokens = max(0, prompt - cached)
        get_client().update_current_generation(
            usage_details={
                "input": input_tokens,
                "output": output,
                "cached-input-tokens": cached,
            }
        )
    except Exception:
        return


# Generation 正文 I/O 默认截断（字符）；可用 env 覆盖
_DEFAULT_IO_TRUNCATE = 4000


def generation_io_truncate_chars() -> int:
    """``OPS_LANGFUSE_IO_TRUNCATE``；非法或 ≤0 → 默认 4000。"""
    raw = _env("OPS_LANGFUSE_IO_TRUNCATE")
    if not raw:
        return _DEFAULT_IO_TRUNCATE
    try:
        n = int(raw)
    except ValueError:
        return _DEFAULT_IO_TRUNCATE
    return n if n > 0 else _DEFAULT_IO_TRUNCATE


def _truncate_io_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + "…"


def update_current_generation_io(
    *,
    input: Any = None,
    output: Any = None,
    truncate: int | None = None,
) -> None:
    """将截断后的 prompt/completion 写入当前 generation；失败 no-op。

    钉死在 complete 边界（非 SSE payload）。无当前 generation 时静默。
    """
    if not tracing_enabled():
        return
    max_chars = truncate if truncate is not None else generation_io_truncate_chars()
    kwargs: dict[str, Any] = {}
    try:
        if input is not None:
            raw = input if isinstance(input, str) else str(input)
            kwargs["input"] = _truncate_io_text(raw, max_chars)
        if output is not None:
            raw = output if isinstance(output, str) else str(output)
            kwargs["output"] = _truncate_io_text(raw, max_chars)
        if not kwargs:
            return
        from langfuse import get_client

        get_client().update_current_generation(**kwargs)
    except Exception:
        logger.debug("langfuse update_current_generation_io failed", exc_info=True)
        return


def eval_score_sample_rate() -> float:
    """线上 score 采样率：``OPS_EVAL_SCORE_SAMPLE_RATE``，默认 0；非法 → 0 + warning。"""
    raw = _env("OPS_EVAL_SCORE_SAMPLE_RATE")
    if not raw:
        return 0.0
    try:
        rate = float(raw)
    except ValueError:
        logger.warning(
            "invalid OPS_EVAL_SCORE_SAMPLE_RATE=%r; treat as 0",
            raw,
        )
        return 0.0
    if rate < 0.0 or rate > 1.0:
        logger.warning(
            "OPS_EVAL_SCORE_SAMPLE_RATE=%r out of [0,1]; treat as 0",
            raw,
        )
        return 0.0
    return rate


def _should_sample_eval_score() -> bool:
    """按采样率决定是否写分；rate≤0 永不写，≥1 总写。"""
    rate = eval_score_sample_rate()
    if rate <= 0.0:
        return False
    if rate >= 1.0:
        return True
    return random.random() < rate


def score_current_trace(name: str, value: Any, **kwargs: Any) -> None:
    """写当前 trace 的 score；tracing 关 / 采样 miss / SDK 失败 → 静默 no-op。

    Score 名须符合 ROADMAP §3.2（如 ``stab.fallback``）。热路径禁止 LLM-as-judge。
    """
    if not tracing_enabled():
        return
    if not _should_sample_eval_score():
        return
    try:
        from langfuse import get_client

        get_client().score_current_trace(name=name, value=value, **kwargs)
    except Exception:
        logger.debug("langfuse score_current_trace failed", exc_info=True)


def flush_traces() -> None:
    """短脚本/评测结束前 flush；未开启或无 client 时静默跳过。"""
    if not tracing_enabled():
        return
    try:
        from langfuse import get_client

        get_client().flush()
    except Exception:
        return
