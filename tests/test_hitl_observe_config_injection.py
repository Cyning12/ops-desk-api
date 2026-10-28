"""observe_node config 注入形态钉 + 行为钉（fix/hitl-observe-node-config-injection）。

根因（nodes.py:27-32 早已钉案）：该模块带 ``from __future__ import annotations``，
注解字符串化后 langgraph 1.x 只认 ``RunnableConfig`` / ``Optional[RunnableConfig]``
两种字面写法；PR #274 的 ruff --fix 把 observe_node 签名改写成
``RunnableConfig | None`` ⇒ config **不注入** ⇒ ``_thread_id_of`` 兜底落空返回 ""
⇒ 落库审批单 thread_id 空 ⇒ 批准后 POST /resume 409 定位不到 checkpoint。

两层钉（先红后绿）：
1. 形态钉 —— observe_node 签名源码必须是 ``Optional[RunnableConfig]`` 且同行
   带 ``noqa: UP045``（防 ruff --fix 再咬回去）；
2. 行为钉 —— state **故意不写** thread_id（线上 thread_id 只在 config 里，
   写了会被 state 直取短路、测不到注入路径），仅在
   ``config.configurable.thread_id`` 给值，跑最小 observe 图到 interrupt，
   断言落库审批单 thread_id 非空且等于该 run 的 thread_id。
"""

from __future__ import annotations

import inspect

import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

import app.ops.lg_rag.multi.nodes as nodes_mod
from app.ops.hitl import reset_hitl_store, set_hitl_store
from app.ops.hitl.store import InMemoryHitlStore
from app.ops.lg_rag.multi.nodes import observe_node, route_after_react
from app.ops.lg_rag.state import LgRagState

_RUN = "runcfginj"
_T1 = f"{_RUN}:1"
_T2 = f"{_RUN}:2"
_TOOL = "mock_get_issue_status"
_THREAD = "t-cfg-injection"


def _observe_signature() -> str:
    """observe_node 的 def 行（含同行行尾 noqa 注释）。"""
    src = inspect.getsource(nodes_mod)
    start = src.index("async def observe_node")
    end = src.index("-> dict:", start)
    return src[start : src.index("\n", end)]


def test_observe_node_config_annotation_form():
    """形态钉：签名必须是 Optional[RunnableConfig] 形态且带 noqa 防咬。"""
    sig = _observe_signature()
    assert "RunnableConfig | None" not in sig, (
        "observe_node 签名被改写成 'RunnableConfig | None' —— future-annotations"
        " 字符串化下 langgraph 1.x 不识别 ⇒ config 不注入 ⇒ 审批单 thread_id 空"
        " ⇒ resume 409。必须是 'Optional[RunnableConfig]'（nodes.py:27-32 钉案）。"
    )
    assert "Optional[RunnableConfig]" in sig, f"签名不是钉案形态：{sig}"
    assert "noqa: UP045" in sig, (
        "缺 # noqa: UP045 ⇒ ruff check 必红、ruff --fix 会把签名再咬回"
        " 'RunnableConfig | None'（#274 就是这么回归的）。"
    )


def _hitl_state_without_thread() -> dict:
    """触发 HITL 拦截的状态；**故意不带 thread_id**（只能走 config 兜底）。"""
    return {
        "messages": [HumanMessage(content="复合问题")],
        "run_id": _RUN,
        "allowed_capability_ids": [_TOOL],
        "supervisor_step_count": 1,
        "host_subtask_seq": 2,
        "react_round": 0,
        "inflight_subtask_ids": [],
        "subtasks": [
            {
                "id": _T1,
                "subtask_id": _T1,
                "alias": "t1",
                "type": "tool",
                "tool": _TOOL,
                "input": "x",
                "depends_on": [],
            },
            {
                "id": _T2,
                "subtask_id": _T2,
                "alias": "t2",
                "type": "tool",
                "tool": _TOOL,
                "input": "x",
                "depends_on": [],
            },
        ],
        "subtask_results": [
            {"subtask_id": _T1, "type": "tool", "output": {"assignee": "张三"}},
            {
                "subtask_id": _T2,
                "type": "tool",
                "error": "需要重跑已执行步骤",
                "blocked_by": "prefix_touch_required",
                "hitl_required": True,
            },
        ],
        "plan_prefix_ids": [_T1],
    }


def _observe_only_graph():
    """只含真 observe_node 的最小图（承 test_react_observe harness ·
    interrupt 需真实 runnable 上下文）。"""
    builder = StateGraph(LgRagState)
    builder.add_node("observe", observe_node)
    builder.add_edge(START, "observe")
    builder.add_conditional_edges("observe", route_after_react, {"replan": END, "settle": END})
    return builder.compile(checkpointer=InMemorySaver())


@pytest.mark.asyncio
async def test_hitl_request_persists_config_thread_id():
    """行为钉：config 注入的 thread_id 必须落进审批单（非空且等于 run 的 thread_id）。"""
    store = InMemoryHitlStore()
    set_hitl_store(store)
    try:
        graph = _observe_only_graph()
        cfg = {"configurable": {"thread_id": _THREAD}}
        payload = None
        async for chunk in graph.astream(
            _hitl_state_without_thread(), cfg, stream_mode="updates"
        ):
            for intr in chunk.get("__interrupt__") or []:
                payload = intr.value

        assert payload is not None, "有 HITL 挂起却没有 interrupt —— 图没有真的停下"
        assert payload["thread_id"] == _THREAD, (
            "interrupt 载荷 thread_id 落空 ⇒ _thread_id_of 的 config 兜底没生效"
        )
        rows = await store.alist(status="pending")
        assert len(rows) == 1, f"审批单数不对：{rows}"
        assert rows[0]["thread_id"] == _THREAD, (
            "落库审批单 thread_id 为空/不等于 run 的 thread_id ⇒ 批准后 resume "
            "409 定位不到 checkpoint（本 task 根因实证）"
        )
    finally:
        reset_hitl_store()
