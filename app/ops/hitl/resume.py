"""HITL 恢复驱动器：把"批准"变成"图真的继续跑"。

**为什么这个文件必须存在**：
``interrupt()`` 把图挂起只是前半件事。挂起之后需要一个**能定位到那次挂起、
并把人的决定喂回去**的入口，否则"批准"就只是把库里一行 status 改成
approved —— 图还躺在 checkpoint 里，前端还停在"等待授权"那一帧，
人批了但什么都没发生（比不批更糟：它看起来像批了）。

恢复段还要**接着同一条 run 落事件**：SSE 在 ``interrupt()`` 那一帧就收尾了，
前端听到的最后一句是"等待授权"。批准之后跑完的那段如果只留在 HTTP 响应里，
前端就得自己再造一条通道 —— 而 replay 通道本来就存在，只需要把这段
**按同一个 run_id 接着编号**写进去（见 ``ResumeEventSink``）。

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
import time
from collections.abc import Awaitable, Callable
from typing import Any

from langgraph.types import Command

logger = logging.getLogger(__name__)

# 与 LangGraph 一致：thread_id 有长度上限，超了会被截断成"另一个 thread"
_THREAD_ID_MAX = 255


class ResumeError(RuntimeError):
    """恢复失败。``code`` 决定 HTTP 状态码——**不给 200 + 半句提示**。"""

    #: not_interrupted / no_thread_id  → 409（请求本身说得通，但此刻不成立）
    #: stranded_checkpoint             → 409（旧版本格式残留，**永远**恢复不了）
    #: checkpointer_not_configured     → 503（配置问题，重试无用）
    #: resume_failed                   → 502（下游真的跑挂了）
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


class ResumeEventSink:
    """把恢复段的节点 update 落进**同一条 run** 的事件表。

    为什么必须有它：SSE 在 ``interrupt()`` 那一帧就收尾了（发了
    ``hitl.waiting`` + ``done(status=waiting_approval)``）。批准之后跑完的那段
    如果只留在 HTTP 响应里，前端要拿到结论就得再造一条通道；而 replay
    通道本来就存在（T4 的 cursor 机制），只要**接同一个 run_id 编号**即可 ——
    前端拿最后一帧的 cursor 再调 replay，就能收到"批准之后发生了什么"。

    两件不能省的事：
    - ``open()`` 先发一帧 ``hitl.resumed``：replay 出来的这段要能自解释，
      否则客户端看到凭空多出来的一串节点帧，不知道那是恢复段；
    - 恢复段**又挂起**时要再发一帧 ``hitl.waiting``：批准一次不代表后面
      不会再拦一次，静默收尾会让人以为跑完了。
    """

    def __init__(
        self,
        *,
        run_id: str,
        user_id: str,
        thread_id: str,
        start_seq: int = 0,
    ) -> None:
        self.run_id = str(run_id or "")
        self.user_id = str(user_id or "")
        self.thread_id = str(thread_id or "")
        self.seq = int(start_seq or 0)
        self.persisted = 0
        self.failed = 0
        self.re_interrupted = False
        self._started = time.perf_counter()

    async def _emit(self, event_type: str, role: str, payload: dict[str, Any]) -> None:
        from app.ops.lg_rag.event_store import persist_run_event

        self.seq += 1
        try:
            await persist_run_event(
                run_id=self.run_id,
                seq=self.seq,
                user_id=self.user_id,
                thread_id=self.thread_id,
                ts_ms=int((time.perf_counter() - self._started) * 1000),
                agent_role=role,
                event_type=event_type,
                payload=payload,
            )
            self.persisted += 1
        except Exception:
            self.failed += 1
            logger.exception(
                "HITL 恢复段事件落盘失败 run=%s seq=%s type=%s",
                self.run_id,
                self.seq,
                event_type,
            )

    async def open(self, *, approved: list[str], decided_by: str = "") -> None:
        await self._emit(
            "hitl.resumed",
            "system",
            {
                "run_id": self.run_id,
                "thread_id": self.thread_id,
                "approved": list(approved),
                "decided_by": decided_by,
            },
        )

    async def close(self) -> None:
        await self._emit(
            "done",
            "system",
            {
                "run_id": self.run_id,
                "thread_id": self.thread_id,
                "status": "waiting_approval" if self.re_interrupted else "resumed",
                "events_persisted": self.persisted,
                # F-OBS-1：终帧观测字段，与 lg-rag/chat SSE done 同口径
                # （int((time.perf_counter() - started) * 1000)，起点见 __init__）。
                "latency_ms": int((time.perf_counter() - self._started) * 1000),
            },
        )

    async def __call__(self, update: dict[str, Any]) -> None:
        from app.ops.lg_rag.sse_stream import extract_interrupt, map_node_update

        # 恢复段又挂起 ⇒ 说清楚，别让 replay 出来的流静默结束
        waiting = extract_interrupt(update)
        if waiting is not None:
            self.re_interrupted = True
            await self._emit(
                "hitl.waiting",
                "system",
                {**waiting, "run_id": waiting.get("run_id") or self.run_id},
            )
            return
        for node_name, node_output in update.items():
            if str(node_name).startswith("__"):
                continue
            event_type, role, payload = map_node_update(str(node_name), node_output)
            await self._emit(event_type, role, payload)

    @property
    def cursor(self) -> str:
        from app.ops.lg_rag.sse_replay import make_cursor

        return make_cursor(self.run_id, self.seq) if self.run_id else ""


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


def _answer_of(state: dict[str, Any]) -> str:
    """最终答案（末条 AI 消息）。复用 SSE 的抽取口径，避免两处漂移。"""
    from app.ops.lg_rag.sse_stream import extract_ai_text

    try:
        return str(extract_ai_text(state.get("messages")) or "")
    except Exception:
        return ""


def _query_of(state: dict[str, Any]) -> str:
    """原始提问（首条 Human 消息）——补落 thread turns 要用。

    SSE 在"等待授权"那帧就收尾了，**用户这一轮根本没落进历史**；
    恢复完成后由这里补上，否则下一轮对话看不到自己问过什么。
    """
    for msg in state.get("messages") or []:
        if getattr(msg, "type", None) == "human":
            content = getattr(msg, "content", "")
            return content if isinstance(content, str) else str(content)
    return ""


async def _resume_with(
    checkpointer: Any,
    *,
    thread_id: str,
    approved: list[str],
    rejected: list[str],
    decided_by: str,
    graph_factory: Any | None,
    update_sink: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
    preflight_only: bool = False,
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
    if not [t for t in tasks if getattr(t, "interrupts", None)]:
        # ★ 这条分支**专门**覆盖"跨大版本升级后残留的挂起"：
        #   实测（langgraph 0.2 → 1.2）：旧格式 checkpoint 能读回 values 和
        #   pending task，但 interrupt 元数据新栈认不出（task.interrupts 为空）；
        #   硬喂 Command(resume=...) 会在 pregel 内部炸
        #   ``TypeError: 'Interrupt' object is not subscriptable``。
        #   所以必须在这里拦成 409，而不是让客户端拿到 500。
        #   运维含义：**升级前要排空在飞的审批**，升级后这类 run 只能作废重开。
        raise ResumeError(
            "stranded_checkpoint",
            f"thread {thread_id[:32]} 有未完成任务但没有 interrupt 元数据 —— "
            "多半是升级前旧版本格式的 checkpoint，无法恢复（只能作废重开）",
        )

    if preflight_only:
        # 请求内守卫探针（异步 resume）：两道快照检查都过了就返回，**不 astream**
        # —— 真正驱动图的是后台执行体；这里只负责把同步可判定的错提前响出来。
        return {
            "thread_id": thread_id[:_THREAD_ID_MAX],
            "approved": list(approved),
            "rejected": list(rejected),
            "decided_by": decided_by,
            "preflight": True,
            "state": {},
            "answer": "",
            "query": "",
        }

    # ⚠️ 用 astream 而不是 ainvoke：ainvoke 只给最终 state，
    #   恢复段的**过程帧**就没了 ⇒ 前端 replay 不出来"批准之后发生了什么"。
    #   astream(Command(resume=...)) 与 ainvoke 语义一致（实测确认），
    #   只是把中间每个节点 update 也吐出来。
    async for chunk in graph.astream(
        Command(
            resume={
                "approved": list(approved),
                "rejected": list(rejected),
                "decided_by": decided_by,
            }
        ),
        config,
        stream_mode="updates",
    ):
        if update_sink is not None and isinstance(chunk, dict):
            try:
                await update_sink(chunk)
            except Exception:  # 落盘失败不许把恢复本身弄挂
                logger.exception("HITL 恢复段事件落盘失败 thread_id=%s", thread_id)

    # astream 不给最终 state；跑完后再取一次快照（已验证与 ainvoke 结果一致）
    snapshot = await graph.aget_state(config)
    result = dict(getattr(snapshot, "values", None) or {})
    return {
        "thread_id": thread_id[:_THREAD_ID_MAX],
        "approved": list(approved),
        "rejected": list(rejected),
        "decided_by": decided_by,
        "state": _summarize(result),
        "answer": _answer_of(result),
        "query": _query_of(result),
    }


async def resume_hitl_run(
    *,
    thread_id: str,
    approved: list[str],
    decided_by: str = "",
    rejected: list[str] | None = None,
    checkpointer: Any | None = None,
    graph_factory: Any | None = None,
    update_sink: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
    preflight_only: bool = False,
) -> dict[str, Any]:
    """恢复一条被 HITL 挂起的 run。

    ``checkpointer`` 显式传入时用它（联调 / 单测注入内存 saver）；
    否则按 ``LG_RAG_HTTP_CHECKPOINTER=postgres`` 决定 —— 没开就**显式失败**。

    ``update_sink`` 收到恢复段的每个节点 update（``{node: output}``），
    用来把这段过程**接着同一条 run 落盘**，让前端 replay 得到批准后的结论。

    preflight_only=True 时只做守卫检查（决定非空 → checkpointer →
    挂起快照两道校验）并返回 preflight 标记，**不驱动图** ——
    异步 resume 端点在请求内用它 fail-fast，真正执行归后台任务。
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
            update_sink=update_sink,
            preflight_only=preflight_only,
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
        # preflight 只读快照，不做 setup（不建表/不改 schema，请求内更快）
        async with apostgres_saver(setup=not preflight_only) as saver:
            return await _resume_with(
                saver,
                thread_id=tid,
                approved=approved,
                rejected=list(rejected or []),
                decided_by=decided_by,
                graph_factory=graph_factory,
                update_sink=update_sink,
                preflight_only=preflight_only,
            )
    except ResumeError:
        raise
    except Exception as exc:
        logger.exception("HITL 恢复失败 thread_id=%s", tid)
        raise ResumeError("resume_failed", f"恢复执行失败：{exc!r}") from exc


def _env_name() -> str:
    from app.ops.lg_rag.checkpointer import CHECKPOINTER_ENV

    return CHECKPOINTER_ENV
