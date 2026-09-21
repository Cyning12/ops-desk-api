"""memory-facts-p0 · M2/M4 状态机与否定性断言（真 PostgreSQL · opsdesk_test）。

每条机制配一条**否定性断言**（SPEC §6 / task M4）：
1. 闸拒不落库（查表为零）2. supersede 后召回只见新值、旧值表内可查
3. revoke_by_source 后召回零命中 4. 过期事实查询路径查不到（不调 sweep）
5. 变异检验：写错误事实 → 断言污染注入块 → revoke → 断言消失
另：预算截断确定性 / 跨 tenant 隔离 / sweep 显式盘点。

⚠️ 全文件 `async def`（asyncio_mode=auto）；不要自建 event loop
（对齐 tests/test_capability_persistence_db.py 头注）。
"""
from __future__ import annotations

import uuid
from datetime import timedelta

import pytest
from langchain_core.messages import SystemMessage
from sqlalchemy import text

from app.db.models import now_utc
from app.db.session import AsyncSessionLocal
from app.ops.lg_rag.continuity import (
    MEMORY_FACTS_HEADER,
    assemble_graph_messages_with_memory,
)
from app.ops.memory.gate import FactCandidate
from app.ops.memory.service import (
    GateRejectedError,
    recall_active,
    revoke_by_source,
    sweep_expired,
    write_fact,
)
from tests.conftest import DB_AVAILABLE

pytestmark = pytest.mark.skipif(
    not DB_AVAILABLE, reason="需要 PostgreSQL（conftest 会准备 opsdesk_test）"
)

_TENANT = "mf-test-tenant"
_OTHER_TENANT = "mf-test-tenant-b"


async def _clear_test_rows() -> None:
    async with AsyncSessionLocal() as session, session.begin():
        await session.execute(
            text("DELETE FROM ops_memory_facts WHERE tenant_id LIKE 'mf-test-%'")
        )


@pytest.fixture(autouse=True)
async def _clean():
    await _clear_test_rows()
    yield
    await _clear_test_rows()


def _candidate(**over) -> FactCandidate:
    base = {
        "tenant_id": _TENANT,
        "user_id": "u-" + uuid.uuid4().hex[:8],
        "key": "project.primary_repo",
        "value": "cyning/ops-desk",
    }
    base.update(over)
    return FactCandidate(**base)


async def _count(tenant_id: str = _TENANT) -> int:
    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            text("SELECT count(*) FROM ops_memory_facts WHERE tenant_id = :t"),
            {"t": tenant_id},
        )
        return int(rows.scalar() or 0)


async def _row_by_id(fact_id: str):
    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            text(
                "SELECT status, key, value FROM ops_memory_facts WHERE id = :i"
            ),
            {"i": fact_id},
        )
        return rows.first()


# ---------------- 1. 闸拒不落库 ----------------


async def test_gate_rejection_writes_nothing():
    with pytest.raises(GateRejectedError) as exc:
        await write_fact(_candidate(kind="preference"))
    assert exc.value.reason_code == "kind_not_allowed"
    assert await _count() == 0  # 查表为零，不是"存了不召回"

    with pytest.raises(GateRejectedError) as exc2:
        await write_fact(_candidate(value={"nested": "snapshot"}))
    assert exc2.value.reason_code == "value_not_scalar"
    assert await _count() == 0


# ---------------- 2. supersede：召回只见新值，旧值表内可查 ----------------


async def test_same_key_supersedes_old_value():
    user = "u-sup"
    old = await write_fact(_candidate(user_id=user, value="repo-old"))
    new = await write_fact(_candidate(user_id=user, value="repo-new"))

    recalled = await recall_active(_TENANT, user)
    assert [f.value for f in recalled] == ["repo-new"]  # 召回只见新值
    assert str(new.supersedes) == str(old.id)

    old_row = await _row_by_id(str(old.id))
    assert old_row is not None and old_row[0] == "superseded"  # 旧值表内可查（审计）
    assert old_row[2] == "repo-old"


# ---------------- 3. revoke_by_source：召回零命中 + 幂等 + 审计 ----------------


async def test_revoke_by_source_zero_hits_and_idempotent(caplog):
    user = "u-rev"
    src = "run-" + uuid.uuid4().hex[:8]
    await write_fact(_candidate(user_id=user), source_run_id=src)
    assert len(await recall_active(_TENANT, user)) == 1

    import logging

    with caplog.at_level(logging.INFO, logger="app.ops.memory.service"):
        n1 = await revoke_by_source(src)
    assert n1 == 1
    assert await recall_active(_TENANT, user) == []  # 零命中
    assert f"source_run_id={src} affected=1" in caplog.text  # 审计日志

    n2 = await revoke_by_source(src)  # 幂等
    assert n2 == 0
    n3 = await revoke_by_source("run-never-existed")  # 不存在 source：0 行
    assert n3 == 0


# ---------------- 4. 过期双保险：查询路径查不到（不调 sweep） ----------------


async def test_expired_invisible_on_query_path_without_sweep():
    user = "u-ttl"
    await write_fact(
        _candidate(user_id=user, key="project.expired_fact", value="gone"),
        expires_at=now_utc() - timedelta(seconds=1),
    )
    await write_fact(
        _candidate(user_id=user, key="project.live_fact", value="here"),
        expires_at=now_utc() + timedelta(hours=1),
    )
    await write_fact(_candidate(user_id=user, key="project.no_ttl", value="forever"))

    keys = {f.key for f in await recall_active(_TENANT, user)}
    assert "project.expired_fact" not in keys  # 不依赖 sweep 已跑
    assert keys == {"project.live_fact", "project.no_ttl"}

    # sweep 只做显式盘点：把过期行置 expired
    n = await sweep_expired(now_utc())
    assert n == 1
    rows = await recall_active(_TENANT, user)
    assert {f.key for f in rows} == {"project.live_fact", "project.no_ttl"}


# ---------------- 预算截断确定性：超限截断低优先级（最旧 updated_at） ----------------


async def test_recall_limit_truncates_oldest_first():
    user = "u-budget"
    facts = [
        await write_fact(_candidate(user_id=user, key=f"project.fact_{i:02d}", value=i))
        for i in range(10)
    ]
    # 显式钉死 updated_at 顺序：fact_00 最旧 … fact_09 最新
    async with AsyncSessionLocal() as session, session.begin():
        for i, f in enumerate(facts):
            await session.execute(
                text(
                    "UPDATE ops_memory_facts SET updated_at = :ts WHERE id = :i"
                ),
                {"ts": now_utc() + timedelta(seconds=i), "i": str(f.id)},
            )

    recalled = await recall_active(_TENANT, user, limit=8)
    keys = [f.key for f in recalled]
    assert len(keys) == 8
    # 确定性：被截掉的是 updated_at 最旧的两条（尾部低优先级）
    assert "project.fact_00" not in keys
    assert "project.fact_01" not in keys
    assert keys[0] == "project.fact_09"  # updated_at desc


# ---------------- 5. 变异检验：写入 → 污染注入块 → 撤销 → 消失 ----------------


async def test_mutation_wrong_fact_pollutes_then_revoke_erases(
    monkeypatch: pytest.MonkeyPatch,
):
    """缺第一步（断言污染真的进入注入块），"撤销成功"就是假通过。"""
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    user = "u-mutation"
    src = "run-wrong-" + uuid.uuid4().hex[:8]
    await write_fact(
        _candidate(user_id=user, key="project.deploy_target", value="wrong-prod-host"),
        source_run_id=src,
    )

    polluted = await assemble_graph_messages_with_memory(
        "部署到哪里？", [], tenant_id=_TENANT, user_id=user
    )
    blocks = [
        str(m.content) for m in polluted if isinstance(m, SystemMessage)
    ]
    # 第一步：通路是通的——错误事实确实出现在注入块
    assert any(MEMORY_FACTS_HEADER in b for b in blocks)
    assert any("project.deploy_target=wrong-prod-host" in b for b in blocks)

    await revoke_by_source(src)

    healed = await assemble_graph_messages_with_memory(
        "部署到哪里？", [], tenant_id=_TENANT, user_id=user
    )
    healed_blocks = [
        str(m.content) for m in healed if isinstance(m, SystemMessage)
    ]
    assert not any("wrong-prod-host" in b for b in healed_blocks)
    assert not any(MEMORY_FACTS_HEADER in b for b in healed_blocks)


# ---------------- 跨 tenant 隔离 ----------------


async def test_cross_tenant_recall_is_empty():
    user = "u-iso"
    await write_fact(_candidate(user_id=user))
    assert await recall_active(_OTHER_TENANT, user) == []
    assert len(await recall_active(_TENANT, user)) == 1
