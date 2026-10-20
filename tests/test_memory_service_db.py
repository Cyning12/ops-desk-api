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
    revoke_by_key,
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
        await session.execute(text("DELETE FROM ops_memory_facts WHERE tenant_id LIKE 'mf-test-%'"))


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
            text("SELECT status, key, value FROM ops_memory_facts WHERE id = :i"),
            {"i": fact_id},
        )
        return rows.first()


# ---------------- 1. 闸拒不落库 ----------------


async def test_gate_rejection_writes_nothing():
    # memory-preference-profile：preference 已放开，改用双向绑定违例触发闸拒
    # （preference + 非 pref. key → key_kind_mismatch）；「闸拒不落库」语义不变
    with pytest.raises(GateRejectedError) as exc:
        await write_fact(_candidate(kind="preference"))
    assert exc.value.reason_code == "key_kind_mismatch"
    assert await _count() == 0  # 查表为零，不是"存了不召回"

    with pytest.raises(GateRejectedError) as exc0:
        await write_fact(_candidate(kind="profile"))  # kind 集合外
    assert exc0.value.reason_code == "kind_not_allowed"
    assert await _count() == 0

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
                text("UPDATE ops_memory_facts SET updated_at = :ts WHERE id = :i"),
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
    """三态变异检验（④b 休眠形态）：写入 → 服务层召回可见污染（通路非空真）→
    装配面恒零注入块（④b 收窄不变量）→ revoke → 服务层召回归零。

    写入侧零改动；装配消费面已收窄，污染/痊愈语义由服务层 recall_active 承担。
    ④a 复活时按 docs/tasks/deferred/task_memory_facts_build_4a.md 清单恢复注入块三态断言。
    """
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    user = "u-mutation"
    src = "run-wrong-" + uuid.uuid4().hex[:8]
    await write_fact(
        _candidate(user_id=user, key="project.deploy_target", value="wrong-prod-host"),
        source_run_id=src,
    )

    # 第一态：服务层通路是通的——错误事实确实可召回（撤销语义非空真）
    recalled = await recall_active(_TENANT, user)
    assert any(f.key == "project.deploy_target" and f.value == "wrong-prod-host" for f in recalled)
    # ④b 收窄不变量：装配面恒零注入块（即使开关开、库内有污染）
    polluted = await assemble_graph_messages_with_memory(
        "部署到哪里？", [], tenant_id=_TENANT, user_id=user
    )
    assert not any(MEMORY_FACTS_HEADER in str(m.content) for m in polluted)

    await revoke_by_source(src)

    assert await recall_active(_TENANT, user) == []  # 服务层痊愈
    healed = await assemble_graph_messages_with_memory(
        "部署到哪里？", [], tenant_id=_TENANT, user_id=user
    )
    assert not any("wrong-prod-host" in str(m.content) for m in healed)
    assert not any(MEMORY_FACTS_HEADER in str(m.content) for m in healed)


# ---------------- 跨 tenant 隔离 ----------------


async def test_cross_tenant_recall_is_empty():
    user = "u-iso"
    await write_fact(_candidate(user_id=user))
    assert await recall_active(_OTHER_TENANT, user) == []
    assert len(await recall_active(_TENANT, user)) == 1


# ---------------- memory-preference-profile · kind=preference（显式-only） ----------------


def _pref_candidate(**over) -> FactCandidate:
    base = {
        "tenant_id": _TENANT,
        "user_id": "u-" + uuid.uuid4().hex[:8],
        "key": "pref.answer_lang",
        "value": "中文",
        "kind": "preference",
    }
    base.update(over)
    return FactCandidate(**base)


async def test_preference_write_recall_roundtrip():
    """显式 preference 写入 → 召回命中（kind=preference 落库）；渲染进偏好节。"""
    from app.ops.lg_rag.continuity import (
        MEMORY_PREFERENCES_HEADER,
        render_memory_facts_block,
    )

    user = "u-pref"
    fact = await write_fact(_pref_candidate(user_id=user))
    assert fact.kind == "preference"
    recalled = await recall_active(_TENANT, user)
    assert [(f.key, f.kind) for f in recalled] == [("pref.answer_lang", "preference")]

    block = render_memory_facts_block(recalled)
    assert MEMORY_PREFERENCES_HEADER in block
    assert "pref.answer_lang=中文" in block
    assert MEMORY_FACTS_HEADER not in block  # 无 fact → 事实节物理不存在


async def test_preference_same_key_supersedes_old_value():
    """同 kind 同 key 新写 → 旧行 superseded + 召回只见新值（沿用 P0 范式）。"""
    user = "u-pref-sup"
    old = await write_fact(_pref_candidate(user_id=user, value="中文"))
    new = await write_fact(_pref_candidate(user_id=user, value="English"))

    recalled = await recall_active(_TENANT, user)
    assert [f.value for f in recalled] == ["English"]
    assert str(new.supersedes) == str(old.id)
    old_row = await _row_by_id(str(old.id))
    assert old_row is not None and old_row[0] == "superseded"


async def test_cross_kind_same_key_no_supersede():
    """supersede 谓词含 kind（双保险第二道）：跨 kind 同 key 两行各自 active。

    第一道防线（闸双向绑定）下该形态无法经闸构造——直插 ORM 绕过闸，
    模拟「未来 key 域约定松动」场景，钉死谓词级防御。
    """
    user = "u-cross-kind"
    async with AsyncSessionLocal() as session, session.begin():
        # 直插绕过闸（模拟 key 域约定松动）；测试库 create_all 无服务端
        # 默认值，status/时间戳显式给
        await session.execute(
            text(
                "INSERT INTO ops_memory_facts "
                "(id, tenant_id, user_id, key, value, kind, status, created_at, updated_at) "
                "VALUES (gen_random_uuid(), :t, :u, 'pref.theme', '\"dark\"', "
                "'fact', 'active', now(), now())"
            ),
            {"t": _TENANT, "u": user},
        )
    await write_fact(_pref_candidate(user_id=user, key="pref.theme", value="light"))

    recalled = await recall_active(_TENANT, user)
    pairs = {(f.key, f.kind, f.value) for f in recalled}
    assert pairs == {
        ("pref.theme", "fact", "dark"),  # 跨 kind 不被 supersede
        ("pref.theme", "preference", "light"),
    }


async def test_revoke_by_key_semantics(caplog):
    """revoke_by_key：active→revoked · 幂等 0 行 · 跨 tenant 0 行 · 审计记 affected。"""
    import logging

    user = "u-revkey"
    await write_fact(_pref_candidate(user_id=user))
    assert len(await recall_active(_TENANT, user)) == 1

    with caplog.at_level(logging.INFO, logger="app.ops.memory.service"):
        n1 = await revoke_by_key(_TENANT, user, "pref.answer_lang")
    assert n1 == 1
    assert await recall_active(_TENANT, user) == []  # 清除后零召回
    assert "revoke_by_key" in caplog.text and "affected=1" in caplog.text  # 审计

    n2 = await revoke_by_key(_TENANT, user, "pref.answer_lang")  # 幂等
    assert n2 == 0
    with caplog.at_level(logging.INFO, logger="app.ops.memory.service"):
        caplog.clear()
        n3 = await revoke_by_key(_OTHER_TENANT, user, "pref.answer_lang")  # 跨 tenant
    assert n3 == 0
    assert "affected=0" in caplog.text  # 幂等/跨 tenant 也留审计痕


async def test_explicit_preference_weight_is_explicit_1():
    """显式 preference（source_run_id 空）来源权重 == SOURCE_WEIGHT_EXPLICIT（1.0）。

    0.8 抽取路径对 preference 物理不存在（显式-only 通路约束的下游不变量）。
    """
    from app.ops.memory.service import SOURCE_WEIGHT_EXPLICIT, _source_weight

    fact = await write_fact(_pref_candidate())
    assert fact.source_run_id is None  # 显式写入无来源 run
    assert SOURCE_WEIGHT_EXPLICIT == 1.0
    assert _source_weight(fact) == SOURCE_WEIGHT_EXPLICIT


async def test_mutation_wrong_preference_pollutes_then_revoke_by_key_erases(
    monkeypatch: pytest.MonkeyPatch,
):
    """三态全链路变异检验（preference 版）：写入错误偏好 → 断言污染出现在
    **偏好节** → revoke_by_key → 断言消失且偏好节物理不存在。

    缺第一态（污染真出现），"撤销成功"就是假通过。
    """
    from app.ops.lg_rag.continuity import MEMORY_PREFERENCES_HEADER

    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    user = "u-pref-mutation"
    await write_fact(_pref_candidate(user_id=user, value="wrong-klingon"))

    # 第一态：服务层通路是通的——错误偏好确实可召回（撤销语义非空真）
    recalled = await recall_active(_TENANT, user)
    assert any(f.key == "pref.answer_lang" and f.value == "wrong-klingon" for f in recalled)
    # ④b 收窄不变量：装配面恒零偏好节/事实节块（即使开关开、库内有污染）
    polluted = await assemble_graph_messages_with_memory(
        "我以后用什么语言回答？", [], tenant_id=_TENANT, user_id=user
    )
    assert not any(MEMORY_PREFERENCES_HEADER in str(m.content) for m in polluted)
    assert not any(MEMORY_FACTS_HEADER in str(m.content) for m in polluted)

    n = await revoke_by_key(_TENANT, user, "pref.answer_lang")
    assert n == 1

    assert await recall_active(_TENANT, user) == []  # 服务层痊愈
    healed = await assemble_graph_messages_with_memory(
        "我以后用什么语言回答？", [], tenant_id=_TENANT, user_id=user
    )
    # 第三态：污染消失 + 装配面恒零偏好节（④b 下恒成立）
    assert not any("wrong-klingon" in str(m.content) for m in healed)
    assert not any(MEMORY_PREFERENCES_HEADER in str(m.content) for m in healed)
