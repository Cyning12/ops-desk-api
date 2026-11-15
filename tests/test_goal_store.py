"""P1-T1 · goal_store（ops_goals 读写收口 · issue #385 · 设计真源 07 §1/§5）。

- 纯函数：sanitize_objective 单行化截断。
- 状态机全矩阵：合法流转 / 非法拒绝 / 终态不可逆（真 PG）。
- tenant 隔离：跨租户 get/patch 不可见。
- 懒创建：幂等 · 空 objective 降级 · 并发重读（IntegrityError 消化）。
- 分层纪律：读路径故障返回 None/[]；patch 显式抛错。
"""

from __future__ import annotations

import uuid

import pytest

from tests.conftest import DB_AVAILABLE

_DB_REQUIRED = pytest.mark.skipif(not DB_AVAILABLE, reason="需要本地 PG（opsdesk_test）真跑 ops_goals")


def test_sanitize_objective() -> None:
    """单行化：换行/控制符→空格、折叠、截 200；非字符串/空串降级。"""
    from app.ops.goals.store import OBJECTIVE_MAX_CHARS, sanitize_objective

    assert sanitize_objective("把 A 服务\n重启一下\t谢谢") == "把 A 服务 重启一下 谢谢"
    assert sanitize_objective("a\x00b\x1fc") == "a b c"
    assert sanitize_objective("  多   段 \r\n 空白  ") == "多 段 空白"
    long_text = "x" * 500
    out = sanitize_objective(long_text)
    assert len(out) == OBJECTIVE_MAX_CHARS == 200
    assert sanitize_objective("") == ""
    assert sanitize_objective("   ") == ""
    assert sanitize_objective(None) == ""


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_resolve_lazy_create_and_idempotent() -> None:
    """∅→active 懒创建；同 thread 再 resolve 返回同一行（幂等不重复建行）。"""
    from app.ops.goals.store import list_goals, resolve_goal_for_thread

    tenant = f"ten-{uuid.uuid4().hex[:8]}"
    thread = f"th-{uuid.uuid4().hex[:8]}"
    g1 = await resolve_goal_for_thread(tenant_id=tenant, thread_id=thread, query="把 issue 同步修好")
    assert g1 is not None
    assert g1["status"] == "active"
    assert g1["objective"] == "把 issue 同步修好"
    assert g1["tenant_id"] == tenant and g1["thread_id"] == thread

    g2 = await resolve_goal_for_thread(tenant_id=tenant, thread_id=thread, query="另一个问题")
    assert g2 is not None and g2["goal_id"] == g1["goal_id"]  # 不重开
    goals = await list_goals(tenant_id=tenant, thread_id=thread)
    assert len(goals) == 1

    # 空 objective 降级不建行
    empty_thread = f"th-{uuid.uuid4().hex[:8]}"
    assert (
        await resolve_goal_for_thread(tenant_id=tenant, thread_id=empty_thread, query="  ") is None
    )
    assert await list_goals(tenant_id=tenant, thread_id=empty_thread) == []
    # 参数缺失静默 None
    assert await resolve_goal_for_thread(tenant_id="", thread_id=thread, query="x") is None


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_status_machine_full_matrix() -> None:
    """07 §1 矩阵：active↔paused 人工双向；{active,paused}→done/abandoned；终态不可逆。"""
    import pytest as _pytest

    from app.ops.goals.store import (
        GoalStateTransitionError,
        patch_goal_status,
        resolve_goal_for_thread,
    )

    tenant = f"ten-{uuid.uuid4().hex[:8]}"

    async def new_goal() -> dict:
        g = await resolve_goal_for_thread(
            tenant_id=tenant, thread_id=f"th-{uuid.uuid4().hex[:8]}", query="q"
        )
        assert g is not None
        return g

    # active → paused → active（O-1：人工复活唯一路径）
    g = await new_goal()
    g = await patch_goal_status(goal_id=g["goal_id"], tenant_id=tenant, new_status="paused")
    assert g["status"] == "paused"
    g = await patch_goal_status(goal_id=g["goal_id"], tenant_id=tenant, new_status="active")
    assert g["status"] == "active"

    # {active,paused} → done / abandoned
    g = await new_goal()
    g = await patch_goal_status(goal_id=g["goal_id"], tenant_id=tenant, new_status="done")
    assert g["status"] == "done"
    g = await new_goal()
    g = await patch_goal_status(goal_id=g["goal_id"], tenant_id=tenant, new_status="paused")
    g = await patch_goal_status(goal_id=g["goal_id"], tenant_id=tenant, new_status="abandoned")
    assert g["status"] == "abandoned"

    # 终态不可逆：done/abandoned → 任何状态皆拒
    for terminal in ("done", "abandoned"):
        g = await new_goal()
        g = await patch_goal_status(goal_id=g["goal_id"], tenant_id=tenant, new_status=terminal)
        for target in ("active", "paused", "done", "abandoned"):
            with _pytest.raises(GoalStateTransitionError):
                await patch_goal_status(goal_id=g["goal_id"], tenant_id=tenant, new_status=target)

    # active → active / paused → paused（自流转非法）
    g = await new_goal()
    with _pytest.raises(GoalStateTransitionError):
        await patch_goal_status(goal_id=g["goal_id"], tenant_id=tenant, new_status="active")
    # 词表外值
    with _pytest.raises(GoalStateTransitionError):
        await patch_goal_status(goal_id=g["goal_id"], tenant_id=tenant, new_status="running")


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_tenant_isolation() -> None:
    """跨租户：get/patch 不可见（404 语义）；list 不串租户。"""
    import pytest as _pytest

    from app.ops.goals.store import (
        GoalNotFoundError,
        get_goal,
        list_goals,
        patch_goal_status,
        resolve_goal_for_thread,
    )

    t1, t2 = f"ten-{uuid.uuid4().hex[:6]}", f"ten-{uuid.uuid4().hex[:6]}"
    thread = f"th-{uuid.uuid4().hex[:8]}"
    g = await resolve_goal_for_thread(tenant_id=t1, thread_id=thread, query="t1 的目标")
    assert g is not None

    assert await get_goal(goal_id=g["goal_id"], tenant_id=t2) is None
    assert (await get_goal(goal_id=g["goal_id"], tenant_id=t1))["goal_id"] == g["goal_id"]
    with _pytest.raises(GoalNotFoundError):
        await patch_goal_status(goal_id=g["goal_id"], tenant_id=t2, new_status="done")
    # 同 thread 不同 tenant：各自 1:1 空间独立
    assert await list_goals(tenant_id=t2, thread_id=thread) == []
    g2 = await resolve_goal_for_thread(tenant_id=t2, thread_id=thread, query="t2 的目标")
    assert g2 is not None and g2["goal_id"] != g["goal_id"]


@_DB_REQUIRED
@pytest.mark.asyncio
async def test_patch_explicit_errors_not_swallowed() -> None:
    """分层纪律：patch 用户显式动作——不存在抛 GoalNotFoundError（绝不吞错装成功）。"""
    import pytest as _pytest

    from app.ops.goals.store import GoalNotFoundError, patch_goal_status

    with _pytest.raises(GoalNotFoundError):
        await patch_goal_status(
            goal_id=str(uuid.uuid4()), tenant_id=f"ten-{uuid.uuid4().hex[:6]}", new_status="done"
        )


@pytest.mark.asyncio
async def test_read_paths_swallow_db_failure(monkeypatch) -> None:
    """分层纪律：读路径（resolve/get/list）DB 故障 → None/[] 不炸（日志带 thread_id）。"""
    from app.ops.goals import store

    class _Boom:
        def __init__(self, *a, **kw):
            raise RuntimeError("db down")

    monkeypatch.setattr(store, "AsyncSessionLocal", _Boom)
    assert await store.resolve_goal_for_thread(tenant_id="t", thread_id="th", query="q") is None
    assert await store.get_goal(goal_id="x", tenant_id="t") is None
    assert await store.list_goals(thread_id="th", tenant_id="t") == []
