"""多副本验证 · 双进程**子进程**入口（P1 subprocess 双 uvicorn 真隔离基建）。

为什么有这个文件
----------------
本仓既有测试全是 TestClient 同进程形态（task B1 #9 实证：tests/ grep uvicorn 零命中）。
而 capability registry / budget / circuit / metrics 全是**模块级单例**——同进程起两个
FastAPI app 共享这些单例，是「假跨实例」，失真断言全部空真（SPEC §4 P2 弃选钉死）。
所以双进程用例必须起**两个独立 uvicorn 子进程**，本模块就是子进程跑的那个入口。

LLM 替身（诚实声明）
--------------------
被验证对象是**状态外置链路**（PG checkpointer / 事件表 / DbHitlStore / 配额计数），
不是 LLM 编排。真 supervisor 图的 supervisor/aggregator 节点要调真 LLM（SiliconFlow），
进了 CI 就是外部依赖 + 非确定性。所以子进程在 app.main 导入后用一张**确定性替身图**
（真 LangGraph StateGraph · 真 interrupt() · 真 compile(checkpointer=PG saver)）替换两个入口：

- app.ops.lg_rag.multi.graph.astream_supervisor_agent —— SSE 流入口替身；
- app.ops.hitl.resume._default_graph_factory —— HITL 恢复用的图工厂替身。

替身图**不换**的东西（=被验证对象，全真）：checkpoint 落 PG / 事件帧落
ops_lg_rag_run_events / HITL 申请落 DbHitlStore / resume 驱动的
aget_state + Command(resume=...) / ResumeEventSink 续写同 run_id。
替身图换掉的东西：LLM 调用 → 确定性字符串。

用法（由 tests/test_multi_replica_dualproc.py 的 fixture 拉起，也可手跑）::

    DATABASE_URL=postgresql+asyncpg://ops:ops_password@127.0.0.1:5432/opsdesk_test \
    LG_RAG_HTTP_CHECKPOINTER=postgres OPS_HITL_PERSISTENCE=db \
    python -m tests.dualproc_server --port 18101 --name replica-a

测试面端点（仅子进程内挂，app/ 零改动）：

- GET  /__dualproc__/whoami —— 实例归属指纹（pid/name/port）+ 配置生效自证；
- POST /__dualproc__/capability-call —— 经**真** capability 网关打一次 mock 能力
  （D3 budget 配额放大实证的触发面；网关/计数全真，只是触发入口是测试路由）。
"""

from __future__ import annotations

import argparse
import os
import time
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import interrupt

# HITL 触发标记：query 里带它，替身图就在 observe 节点 interrupt() 挂起
HITL_MARKER = "[hitl]"


# ---------------------------------------------------------------- 替身图


class _DpState(TypedDict, total=False):
    """替身图 state（刻意不复用 LgRagState：只留 resume 断言要看的字段）。"""

    messages: Annotated[list, add_messages]
    run_id: str
    thread_id: str
    want_hitl: bool
    decision: dict[str, Any]


def _planner_node(state: _DpState) -> dict[str, Any]:
    query = state["messages"][-1].content if state.get("messages") else ""
    return {"messages": [AIMessage(content=f"[dualproc] plan: {query[:80]}")]}


async def _observe_node(state: _DpState) -> dict[str, Any]:
    """want_hitl 时真 interrupt() 挂起；申请落库走**真** get_hitl_store()。

    幂等去重口径对齐 multi/nodes._persist_hitl：interrupt 挂起时节点 return
    不进 checkpoint，恢复后节点整体重跑 ⇒ 去重必须查 store（按 run_id），
    不能只看 state。这里按**全状态**拉取再过滤（approved 的也算已有），
    避免「恢复一次又造一条 pending 申请」。
    """
    if not state.get("want_hitl"):
        return {}
    from app.ops.hitl import get_hitl_store, new_request_id

    run_id = str(state.get("run_id") or "")
    thread_id = str(state.get("thread_id") or "")
    store = get_hitl_store()
    existing: dict[str, Any] | None = None
    for row in await store.alist(limit=200):
        if str(row.get("run_id") or "") == run_id:
            existing = row
            break
    if existing is None:
        existing = await store.acreate(
            {
                "id": new_request_id(),
                "run_id": run_id,
                "thread_id": thread_id,
                "tenant_id": "dualproc",
                "subtask_id": f"{run_id}:2",
                "blocked_by": "prefix_touch_required",
                "unlock_subtask_id": f"{run_id}:1",
                "reason": "dualproc 替身图确定性挂起",
                "detail": "multi-replica-verify 双进程验证",
                "payload": {},
                "status": "pending",
                "created_at": time.time(),
            }
        )
    decision = interrupt(
        {
            "reason": "hitl_waiting",
            "run_id": run_id,
            "thread_id": thread_id,
            "requests": [existing],
        }
    )
    # 恢复后 interrupt() 返回 Command(resume=...) 的值
    return {"decision": decision}


def _aggregator_node(state: _DpState) -> dict[str, Any]:
    """节点名刻意叫 aggregator：ResumeEventSink/SSE 把它映射成 answer 终帧。"""
    query = state["messages"][0].content if state.get("messages") else ""
    decision = state.get("decision") or {}
    if decision:
        answer = "[dualproc] resumed answer: approved=" + str(
            decision.get("approved"),
        ) + " decided_by=" + str(decision.get("decided_by"))
    else:
        answer = f"[dualproc] answer: {query[:80]}"
    return {"messages": [AIMessage(content=answer)]}


def _build_graph(*, checkpointer: Any | None = None) -> Any:
    """编译替身图；checkpointer 全真（PG saver 由调用方传入）。"""
    builder = StateGraph(_DpState)
    builder.add_node("planner", _planner_node)
    builder.add_node("observe", _observe_node)
    builder.add_node("aggregator", _aggregator_node)
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "observe")
    builder.add_edge("observe", "aggregator")
    builder.add_edge("aggregator", END)
    return builder.compile(checkpointer=checkpointer)


async def _fake_astream_supervisor_agent(
    query: str,
    *,
    thread_id: str = "dualproc",
    checkpointer: Any | None = None,
    history_turns: list[dict] | None = None,
    run_id: str | None = None,
    user_id: str | None = None,
):
    """astream_supervisor_agent 的确定性替身（签名对齐真身）。"""
    graph = _build_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": thread_id}}
    initial: _DpState = {
        "messages": [HumanMessage(content=query)],
        "run_id": run_id or "",
        "thread_id": thread_id,
        "want_hitl": HITL_MARKER in query,
    }
    async for update in graph.astream(initial, config, stream_mode="updates"):
        yield update


def _fake_graph_factory(*, checkpointer: Any | None = None) -> Any:
    """resume._default_graph_factory 替身：同一张替身图编译进恢复 saver。"""
    return _build_graph(checkpointer=checkpointer)


# ---------------------------------------------------------------- 子进程 app


def build_app():
    """导入 app.main 后装替身与测试面端点，返回 FastAPI app。"""
    import app.ops.hitl.resume as resume_mod
    import app.ops.lg_rag.multi.graph as multi_graph
    from app.main import app

    # 替身注入（sse_stream 在调用时才 from ... import，属性替换即生效；
    # resume_hitl_run 内部按模块全局名查 _default_graph_factory，同理）。
    multi_graph.astream_supervisor_agent = _fake_astream_supervisor_agent
    resume_mod._default_graph_factory = _fake_graph_factory

    from fastapi import Body

    @app.get("/__dualproc__/whoami")
    async def _whoami() -> dict[str, Any]:
        """实例归属指纹 + 配置生效自证（前置断言数据源）。"""
        from app.ops.capability.persistence import describe_persistence
        from app.ops.hitl.persistence import describe_hitl_persistence
        from app.ops.lg_rag.checkpointer import use_postgres_checkpointer

        return {
            "pid": os.getpid(),
            "name": os.environ.get("DUALPROC_NAME", ""),
            "port": int(os.environ.get("DUALPROC_PORT", "0")),
            "checkpointer_postgres": use_postgres_checkpointer(),
            "hitl_persistence": describe_hitl_persistence(),
            "capability_persistence": describe_persistence(),
        }

    @app.post("/__dualproc__/capability-call")
    async def _capability_call(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
        """经**真** capability 网关打一次 mock 能力（D3 配额放大实证触发面）。

        budget 计数维度 = ctx.session_id（对齐 budget.session_key 口径）。
        """
        from app.ops.capability import ainvoke as capability_ainvoke

        session_id = str(body.get("session_id") or "")
        result = await capability_ainvoke(
            "mock_get_issue_status",
            "dualproc",
            ctx={"session_id": session_id},
        )
        return {
            "ok": bool(result.ok),
            "error": result.error,
            "session_id": session_id,
        }

    return app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--name", default="replica")
    # 容器里必须 0.0.0.0（端口映射到的是容器 eth0 不是 loopback）；
    # pytest 轨默认 127.0.0.1（本机最小暴露面）
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    os.environ["DUALPROC_NAME"] = args.name
    os.environ["DUALPROC_PORT"] = str(args.port)

    import uvicorn

    app = build_app()
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()

