"""HITL 恢复驱动器：把"批准"变成"图真的继续跑"。

**为什么这个文件必须存在**：
``interrupt()`` 把图挂起只是前半件事。挂起之后需要一个**能定位到那次挂起、
并把人的决定喂回去**的入口，否则"批准"就只是把库里一行 status 改成
approved —— 图还躺在 checkpoint 里，前端还停在"等待授权"那一帧，
人批了但什么都没发生（比不批更糟：它看起来像批了）。

恢复的三件硬事：

1. **定位**：靠 ``thread_id``（checkpoint 的 namespace）找到挂起的那个 checkpoint。
   申请行里存的就是它 —— 这也是为什么 ``_persist_hitl`` 非要把 thread_id 写进去。
2. **同源**：恢复用的 checkpointer 必须和挂起时**同一个**。
   挂起走 PG、恢复走内存 ⇒ 找不到挂起点 ⇒ 静默变成"什么都没发生"。
   所以这里**不猜**：没开 PG 开关就显式报错（fail-closed）。
3. **喂值**：``Command(resume=...)`` 的值由 ``_apply_hitl_decision`` 解释，
   ``approved`` 里放的是**要解锁并重跑的 subtask_id**（= 申请行的
   ``unlock_subtask_id``），不是"被阻塞的那一步"。放错了就是批准了却没重跑。
"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.types import Command

logger = logging.getLogger(__name__)

# 与 LangGraph 一致：thread_id 有长度上限，超了会被截断成"另一个 thread"
_THREAD_ID_MAX = 255


class ResumeError(RuntimeError):
    """恢复失败。``code`` 决定 HTTP 状态码——**不给 200 + 半句提示**。"""

    #: not_interrupted / no_thread_id → 409（请求本身说得通，但此刻不成立）
    #: checkpointer_not_configured     → 503（配置问题，重试无用）
    #: resume_failed                   → 502（下游真的跑挂了）
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


def _default_graph_factory(*, checkpointer: Any | None) -> Any:
    """默认恢复的是**supervisor 图**——只有它有 observe / interrupt。"""
    from app.ops.lg_rag.multi.graph import build_supervisor_agent

    return build_supervisor_agent(checkpointer=checkpointer)


def _summarize(state: Any) -> dict[str, Any]:
    """恢复后的结果摘要：不要把整份 state 塞进 HTTP 响应。"""
    if not isinstance(state, dict):
        return {}
    out: dict[str, Any] = {}
    for key in (
        "react_round",
        "react_observation",
        "hitl_unlocked_ids",
        "hitl_interrupt",
        "route",
        "subtasks",
    ):
        if key in state:
            out[key] = state[key]
    out["subtask_result_count"] = len(state.get("subtask_results") or [])
    return out


async def _resume_with(
    checkpointer: Any,
    *,
    thread_id: str,
    approved: list[str],
    rejected: list[str],
    decided_by: str,
    graph_factory: Any | None,
) -> dict[str, Any]:
    factory = graph_factory or _default_graph_factory
    graph = factory(checkpointer=checkpointer)
    config: dict[str, Any] = {"configurable": {"thread_id": thread_id[:_THREAD_ID_MAX]}}

    # 先确认"这里真的有个挂起"，再喂值。
    # 不检查的话，thread 不存在时 Command(resume=...) 会被当成一次普通输入，
    # 表现为"从头又跑了一遍" —— 人以为恢复了，实际是重开了一局。
    snapshot = await graph.aget_state(config)
    tasks = list(getattr(snapshot, "tasks", None) or ())
    if snapshot is None or not tasks:
        raise ResumeError(
            "not_interrupted",
            f"thread {thread_id[:32]} 没有挂起的 interrupt —— "
            "要么这轮已经跑完，要么 checkpointer 与挂起时不是同一个",
        )
    interleaved = [t for t in tasks if getattr(t, "interrupts", None)]
    if not interleaved:
        raise ResumeError(
            "not_interrupted",
            f"thread {thread_id[:32]} 有未完成的任务但不是 interrupt 挂起，拒绝恢复",
        )

    result = await graph.ainvoke(
        Command(
            resume={
                "approved": list(approved),
                "rejected": list(rejected),
                "decided_by": decided_by,
            }
        ),
        config,
    )
    return {
        "thread_id": thread_id[:_THREAD_ID_MAX],
        "approved": list(approved),
        "rejected": list(rejected),
        "decided_by": decided_by,
        "state": _summarize(result),
    }


async def resume_hitl_run(
    *,
    thread_id: str,
    approved: list[str],
    decided_by: str = "",
    rejected: list[str] | None = None,
    checkpointer: Any | None = None,
    graph_factory: Any | None = None,
) -> dict[str, Any]:
    """恢复一条被 HITL 挂起的 run。

    ``checkpointer`` 显式传入时用它（联调 / 单测注入内存 saver）；
    否则按 ``LG_RAG_HTTP_CHECKPOINTER=postgres`` 决定 —— 没开就**显式失败**。
    """
    tid = str(thread_id or "").strip()
    if not tid:
        raise ResumeError(
            "no_thread_id",
            "申请里没有 thread_id —— 定位不到挂起的 checkpoint，无法恢复",
        )
    approved = [str(x) for x in approved if str(x).strip()]
    if not approved and not rejected:
        raise ResumeError(
            "no_decision",
            "既没有 approved 也没有 rejected —— 空决定不驱动恢复",
        )

    if checkpointer is not None:
        return await _resume_with(
            checkpointer,
            thread_id=tid,
            approved=approved,
            rejected=list(rejected or []),
            decided_by=decided_by,
            graph_factory=graph_factory,
        )

    from app.ops.lg_rag.checkpointer import apostgres_saver, use_postgres_checkpointer

    if not use_postgres_checkpointer():
        # ★ fail-closed：内存 saver 是**每请求新建**的，跨请求恢复必然找不到
        #   挂起点。这里返回 200 的话，人看到"恢复成功"却什么都没发生。
        raise ResumeError(
            "checkpointer_not_configured",
            f"未启用 PG checkpointer（设 {_env_name()}=postgres）—— "
            "跨请求恢复在内存 saver 下不可能成立，拒绝假装成功",
        )
    try:
        async with apostgres_saver(setup=True) as saver:
            return await _resume_with(
                saver,
                thread_id=tid,
                approved=approved,
                rejected=list(rejected or []),
                decided_by=decided_by,
                graph_factory=graph_factory,
            )
    except ResumeError:
        raise
    except Exception as exc:
        logger.exception("HITL 恢复失败 thread_id=%s", tid)
        raise ResumeError("resume_failed", f"恢复执行失败：{exc!r}") from exc


def _env_name() -> str:
    from app.ops.lg_rag.checkpointer import CHECKPOINTER_ENV

    return CHECKPOINTER_ENV
