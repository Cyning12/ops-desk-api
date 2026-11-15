"""P1-T4 · goal 入口接线（/lg-rag/stream 闸内懒创建 · issue #396 · 07 §5 T4）。

- 闸 off：POST /stream → ops_goals 零行且 store 调用计数=0（零触达红线）。
- 闸 on：懒创建一行（objective 单行化）；同 thread 二轮复用不重开。
- 并发：10 路 resolve_goal_for_thread → 仅一行（uq_ops_goals_active_thread 实证）。
- turns 表无 [当前目标] 横幅残留（注入只在装配层消息，不落 turns）。
"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any
from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage

from tests.conftest import DB_AVAILABLE

_DB_REQUIRED = pytest.mark.skipif(not DB_AVAILABLE, reason="需要本地 PG（opsdesk_test）真跑 ops_goals")

_PATH = "/api/ops/lg-rag/stream"


async def _fake_supervisor_stream(
    query: str, *, thread_id: str = "t", checkpointer: Any = None, **_kwargs
) -> Any:
    yield {"strategy_builder": {"allowed_capability_ids": []}}
    yield {"supervisor": {"subtasks": [{"id": "t1", "type": "rag", "input": query}]}}
    yield {"rag_subtask": {"subtask_results": [{"id": "t1", "type": "rag", "output": "hit"}]}}
    yield {"aggregator": {"messages": [AIMessage(content="最终答案")]}}
    yield {"critic_node": {"critic_verdict": "pass"}}


@pytest.fixture
async def seed_auth_user():
    """override_auth_maintainer 的固定 id 用户补行进 ops_users（FK 真源）。

    承 test_chat_history_api.py:117 先例：conftest override 用户并不真在表里，
    stream 持久化 turns/threads 有 FK → 须先补用户行。
    """
    from app.db.models import OpsUser
    from app.db.session import AsyncSessionLocal

    uid = "00000000-0000-0000-0000-000000000001"
    async with AsyncSessionLocal() as db:
        if await db.get(OpsUser, uid) is None:
            db.add(OpsUser(id=uid, username=f"t4-{uuid.uuid4().hex[:12]}", role="maintainer"))
            await db.commit()
    yield uid
    async with AsyncSessionLocal() as db:
        row = await db.get(OpsUser, uid)
        if row is not None and str(row.username).startswith("t4-"):
            await db.delete(row)
            await db.commit()


def _parse_sse(body: str) -> list[dict]:
    events: list[dict] = []
    for block in body.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        for line in block.split("\n"):
            if line.startswith("data: "):
                events.append(json.loads(line[len("data: ") :]))
                break
    return events


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_gate_off_creates_no_goal_and_store_untouched(
    client, override_auth_maintainer, monkeypatch
) -> None:
    """闸 off：goal 零行 + resolve_goal_for_thread 调用计数=0（off 零触达红线）。"""
    monkeypatch.setenv("GOAL_INJECT_ENABLED", "")
    from app.ops.goals import store as goal_store
    from app.ops.goals.store import list_goals
    from app.ops.tenant_context import TENANT_A

    calls = {"n": 0}
    real = goal_store.resolve_goal_for_thread

    async def spy(**kwargs):
        calls["n"] += 1
        return await real(**kwargs)

    monkeypatch.setattr(goal_store, "resolve_goal_for_thread", spy)
    thread = f"th-t4off-{uuid.uuid4().hex[:8]}"
    with patch(
        "app.ops.lg_rag.multi.graph.astream_supervisor_agent", new=_fake_supervisor_stream
    ):
        resp = await client.post(_PATH, json={"query": "查一下同步状态", "thread_id": thread})
    assert resp.status_code == 200
    assert calls["n"] == 0
    assert await list_goals(tenant_id=TENANT_A, thread_id=thread) == []


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_gate_on_lazy_create_and_reuse(
    client, override_auth_maintainer, seed_auth_user, monkeypatch
) -> None:
    """闸 on：首轮懒创建（objective 单行化）；二轮复用同一行（3 轮冒烟等效）。"""
    monkeypatch.setenv("GOAL_INJECT_ENABLED", "1")
    from app.ops.goals.store import list_goals
    from app.ops.tenant_context import TENANT_A

    thread = f"th-t4on-{uuid.uuid4().hex[:8]}"
    with patch(
        "app.ops.lg_rag.multi.graph.astream_supervisor_agent", new=_fake_supervisor_stream
    ):
        for q in ("把 issue 同步\n修好", "进展如何", "还没好么"):
            resp = await client.post(_PATH, json={"query": q, "thread_id": thread})
            assert resp.status_code == 200
            assert _parse_sse(resp.text)[-1]["event_type"] == "done"

    goals = await list_goals(tenant_id=TENANT_A, thread_id=thread)
    assert len(goals) == 1
    assert goals[0]["objective"] == "把 issue 同步 修好"  # 首轮 query 单行化
    assert goals[0]["status"] == "active"
    assert goals[0]["tenant_id"] == TENANT_A


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_concurrent_resolve_single_row() -> None:
    """并发 10 路懒创建 → uq_ops_goals_active_thread 兜底，仅一非终态行。"""
    from app.db.session import engine  # 池化连接跨 event loop 复用会炸 → 先清池
    from app.ops.goals.store import list_goals, resolve_goal_for_thread

    await engine.dispose()
    tenant = f"ten-{uuid.uuid4().hex[:8]}"
    thread = f"th-{uuid.uuid4().hex[:8]}"
    results = await asyncio.gather(
        *[
            resolve_goal_for_thread(tenant_id=tenant, thread_id=thread, query=f"并发目标{i}")
            for i in range(10)
        ]
    )
    assert all(r is not None for r in results)
    goal_ids = {r["goal_id"] for r in results}
    assert len(goal_ids) == 1
    goals = await list_goals(tenant_id=tenant, thread_id=thread)
    assert len(goals) == 1


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_turns_no_goal_banner(
    client, override_auth_maintainer, seed_auth_user, monkeypatch
) -> None:
    """闸 on 全流后：turns 表仅存原文 query，无 [当前目标] 横幅残留。"""
    monkeypatch.setenv("GOAL_INJECT_ENABLED", "1")
    from app.ops.lg_rag.thread_store import load_thread_turns

    thread = f"th-t4turns-{uuid.uuid4().hex[:8]}"
    query = "原始问题不带横幅"
    with patch(
        "app.ops.lg_rag.multi.graph.astream_supervisor_agent", new=_fake_supervisor_stream
    ):
        resp = await client.post(_PATH, json={"query": query, "thread_id": thread})
    assert resp.status_code == 200
    turns = await load_thread_turns(thread)
    assert turns, "stream 应持久化 turns"
    user_texts = [t.get("query") or t.get("content") or "" for t in turns]
    assert any(query in t for t in user_texts)
    assert all("[当前目标]" not in json.dumps(t, ensure_ascii=False) for t in turns)
