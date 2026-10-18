"""LLM usage 落表（ops_llm_usage）与 run 上下文（llm-layer-hardening D4）。

纪律（task 钉死契约）：
- run 上下文（run_id / surface / task_type）经 **ContextVar** 由入口点注入
  （chat streaming / lg_rag router / memory 抽取 / chat 节点声明 task_type）；
  provider 层在见到 usage 末帧的同一钩点消费——**不改 complete/complete_stream 签名**。
- **tracing 关也落表**（不依赖 Langfuse）；无 usage 末帧 → 无行，**不写 0 假账**
  （provider 包装层只在真见到 usage chunk 时才调本模块）。
- 落表异常 → log + 计数（`snapshot()` 可见），**不挡主答**；
  不得静默声称已记账。
- run 上下文缺失（无 ContextVar 的调用点）→ `run_id=NULL · surface=background`，
  不阻断记账。
- 行内只存 token 计数与模型名，**不存** prompt/answer 正文。
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass

from app.llm.schema import LlmUsage

logger = logging.getLogger(__name__)

# surface 取值：chat / lg_rag / background（无上下文或后台任务）
SURFACE_CHAT = "chat"
SURFACE_LG_RAG = "lg_rag"
SURFACE_BACKGROUND = "background"


@dataclass(frozen=True)
class LlmRunContext:
    """一次 LLM 调用的归属：哪个 run、哪个入口面、哪类任务。"""

    run_id: str | None = None
    surface: str = SURFACE_BACKGROUND
    task_type: str | None = None  # answer | grader | extract | structured


_DEFAULT_CONTEXT = LlmRunContext()
_current: ContextVar[LlmRunContext] = ContextVar("llm_run_context", default=_DEFAULT_CONTEXT)

#: 落表失败累计计数（进程内观测；失败 = log + 计数，不挡主答）
_persist_failures = 0


def current_run_context() -> LlmRunContext:
    """当前 run 上下文；无注入点时返回默认（run_id=None · surface=background）。"""
    return _current.get()


def set_run_context(
    *,
    run_id: str | None = None,
    surface: str | None = None,
    task_type: str | None = None,
) -> Token[LlmRunContext]:
    """注入 run 上下文（None 字段继承当前值）；返回 token 供 `reset_run_context`。"""
    cur = _current.get()
    return _current.set(
        LlmRunContext(
            run_id=run_id if run_id is not None else cur.run_id,
            surface=surface if surface is not None else cur.surface,
            task_type=task_type if task_type is not None else cur.task_type,
        )
    )


def reset_run_context(token: Token[LlmRunContext]) -> None:
    """复位到 `set_run_context` 之前的上下文。"""
    _current.reset(token)


@contextmanager
def use_run_context(
    *,
    run_id: str | None = None,
    surface: str | None = None,
    task_type: str | None = None,
) -> Iterator[None]:
    """with 块内注入 run 上下文（None 字段继承当前值），退出自动复位。"""
    token = set_run_context(run_id=run_id, surface=surface, task_type=task_type)
    try:
        yield
    finally:
        reset_run_context(token)


@contextmanager
def ensure_task_type(task_type: str) -> Iterator[None]:
    """仅当当前上下文**尚未声明** task_type 时才设置（内层不覆盖外层声明）。

    例：memory 抽取（extract）走 structured_output 管道——extract 已声明
    `task_type="extract"`，管道内层的 `structured` 默认不再覆盖。
    """
    if _current.get().task_type is not None:
        yield
        return
    with use_run_context(task_type=task_type):
        yield


async def record_llm_usage(
    usage: LlmUsage,
    *,
    provider: str,
    model: str,
    attempts: int,
) -> bool:
    """落一行 `ops_llm_usage`；成功 True。

    任何异常（DB 故障 / migration 未跑）→ log + 计数 + False，**不挡主答**。
    """
    global _persist_failures
    ctx = current_run_context()
    try:
        # 函数内 lazy import：llm 不硬依赖 db 会话装配，import 期零 DB 触网
        from app.db.models import OpsLlmUsage
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            session.add(
                OpsLlmUsage(
                    run_id=ctx.run_id,
                    surface=ctx.surface,
                    task_type=ctx.task_type,
                    provider=provider,
                    model=model,
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    cached_input_tokens=usage.cached_input_tokens,
                    attempts=attempts,
                )
            )
            await session.commit()
        return True
    except Exception:
        _persist_failures += 1
        logger.warning(
            "ops_llm_usage persist failed (answer unaffected) run_id=%s surface=%s "
            "provider=%s model=%s",
            ctx.run_id,
            ctx.surface,
            provider,
            model,
            exc_info=True,
        )
        return False


def persist_failure_count() -> int:
    """落表失败累计次数（观测用；>0 即「有账没记上」，不得静默）。"""
    return _persist_failures


def reset_persist_failure_count() -> None:
    """测试用：清零落表失败计数。"""
    global _persist_failures
    _persist_failures = 0


def snapshot() -> dict:
    """观测快照（供 /runtime 类观测面）。"""
    return {"persist_failures": _persist_failures}
