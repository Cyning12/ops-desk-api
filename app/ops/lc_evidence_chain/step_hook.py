"""lc_evidence_chain · 可选步骤 hook（供 SSE 里程碑，无反向依赖 lg_rag）。

挂载方（如 ``rag_subtask``）经 ContextVar 注入 async hook；
chain 各步入口/出口调用 ``emit_chain_step``。无 hook 时为空操作。
"""

from __future__ import annotations

import contextvars
import logging
from collections.abc import Awaitable, Callable
from typing import Any

logger = logging.getLogger(__name__)

# hook(step, detail|None)：step 如 retrieve/grade/answer
ChainStepHook = Callable[[str, dict[str, Any] | None], Awaitable[None]]

_chain_step_hook: contextvars.ContextVar[ChainStepHook | None] = contextvars.ContextVar(
    "lc_evidence_chain_step_hook", default=None
)


def set_chain_step_hook(
    hook: ChainStepHook,
) -> contextvars.Token[ChainStepHook | None]:
    """挂步骤 hook（rag_subtask 在 astream 前调用）。"""
    return _chain_step_hook.set(hook)


def reset_chain_step_hook(
    handle: contextvars.Token[ChainStepHook | None],
) -> None:
    """摘除 hook（finally 复位）。"""
    _chain_step_hook.reset(handle)


async def emit_chain_step(
    step: str,
    detail: dict[str, Any] | None = None,
) -> None:
    """有 hook 则推送；异常只打日志，不中断 chain。"""
    hook = _chain_step_hook.get()
    if hook is None:
        return
    try:
        await hook(step, detail)
    except Exception as exc:
        logger.warning(
            "lc_evidence_chain step hook 失败 step=%s err=%r",
            step,
            exc,
        )
