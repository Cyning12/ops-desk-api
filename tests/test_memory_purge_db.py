"""memory-compliance-delete · purge_by_user 物理删除守护（真 PostgreSQL · opsdesk_test）。

验收否决面（task D1/D3 · SPEC §6）：
- 谓词锚点：DELETE 谓词含且仅含 tenant_id+user_id（变异检验①兜底对象）
- dry_run 默认 true **零写**（前后计数逐行对拍）· 计数守恒（scanned/deleted/by_status）
- 全 status 四态行 + 非 NULL embedding 行**整删**（行零残留 = 两通路零残留）
- 幂等：重复实删第二次 deleted==0（审计仍留痕 affected=0）
- 越域零影响：他 tenant 同 user / 同 tenant 他 user 夹具行逐行不动 · 跨 tenant 0 行
- 审计 logger 记动作不记内容（caplog 字段含 tenant/user/dry_run/affected · 不含 key/value）
- 删除后 recall_active 零命中 · recall_with_vector 零命中（mock embedder）

⚠️ 全文件 async def（asyncio_mode=auto）；不要自建 event loop。
"""

from __future__ import annotations

import logging
import uuid

import pytest
from sqlalchemy import delete as sa_delete
from sqlalchemy import text

from app.db.models import OpsMemoryFact
from app.db.session import AsyncSessionLocal
from app.ops.memory.gate import FactCandidate
from app.ops.memory.service import (
    _purge_predicate,
    _set_embedding,
    purge_by_user,
    recall_active,
    recall_with_vector,
    write_fact,
)
from tests.conftest import DB_AVAILABLE

pytestmark = pytest.mark.skipif(
    not DB_AVAILABLE, reason="需要 PostgreSQL（conftest 会准备 opsdesk_test）"
)

_TENANT = "mfp-test-tenant"
_OTHER_TENANT = "mfp-test-tenant-b"
_EMBED_DIM = 1024


class FakeEmbedder:
    """确定性向量（test_memory_vector_p1 先例同形）：无随机、不连外网。"""

    name = "fake-embedder"

    def _vec(self, text_value: str) -> list[float]:
        t = text_value.lower()
        v = [0.0] * _EMBED_DIM
        if any(k in t for k in ("repo", "仓库")):
            v[0] = 1.0
        else:
            v[2] = 1.0
        return v

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]


async def _clear_test_rows() -> None:
    async with AsyncSessionLocal() as session, session.begin():
        await session.execute(
            text("DELETE FROM ops_memory_facts WHERE tenant_id LIKE 'mfp-test-%'")
        )


@pytest.fixture(autouse=True)
async def _clean():
    await _clear_test_rows()
    yield
    await _clear_test_rows()


def _candidate(user_id: str, **over) -> FactCandidate:
    base = {
        "tenant_id": _TENANT,
        "user_id": user_id,
        "key": "project.primary_repo",
        "value": "cyning/ops-desk",
    }
    base.update(over)
    return FactCandidate(**base)


async def _rows(tenant_id: str, user_id: str) -> list[tuple]:
    """全 status 行快照（越域「逐行不动」对拍用）。"""
    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            text(
                "SELECT id, status, key, value, embedding IS NOT NULL "
                "FROM ops_memory_facts "
                "WHERE tenant_id = :t AND user_id = :u ORDER BY id"
            ),
            {"t": tenant_id, "u": user_id},
        )
        return [tuple(r) for r in rows.all()]


async def _count(tenant_id: str, user_id: str) -> int:
    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            text(
                "SELECT count(*) FROM ops_memory_facts "
                "WHERE tenant_id = :t AND user_id = :u"
            ),
            {"t": tenant_id, "u": user_id},
        )
        return int(rows.scalar() or 0)


async def _set_status(fact_id: str, status: str) -> None:
    async with AsyncSessionLocal() as session, session.begin():
        await session.execute(
            text("UPDATE ops_memory_facts SET status = :s WHERE id = :i"),
            {"s": status, "i": fact_id},
        )


async def _seed_four_statuses(user: str, tenant: str = _TENANT) -> dict[str, str]:
    """造 active/superseded/revoked/expired 四态行各一，active 行带非 NULL embedding。"""
    ids: dict[str, str] = {}
    keys = {
        "active": "project.primary_repo",
        "superseded": "project.deploy_target",
        "revoked": "user.display_tz",
        "expired": "project.favorite_color",
    }
    for status, key in keys.items():
        fact = await write_fact(_candidate(user, tenant_id=tenant, key=key))
        ids[status] = str(fact.id)
    for status in ("superseded", "revoked", "expired"):
        await _set_status(ids[status], status)
    await _set_embedding(ids["active"], [0.1] * _EMBED_DIM, session=None)
    return ids


# ---------------- 谓词锚点：含且仅含 tenant_id+user_id ----------------


async def test_purge_predicate_anchor_only_tenant_user():
    stmt = sa_delete(OpsMemoryFact).where(*_purge_predicate("t", "u"))
    compiled = str(stmt)
    assert "tenant_id" in compiled
    assert "user_id" in compiled
    assert "status" not in compiled  # 全 status 无差别：不得带 status 谓词
    assert "key" not in compiled
    assert "source_run_id" not in compiled


# ---------------- dry_run 默认 true：零写对拍 + 计数守恒 + 审计 ----------------


async def test_dry_run_default_zero_write_and_count_conservation(caplog):
    user = "u-dry-" + uuid.uuid4().hex[:8]
    await _seed_four_statuses(user)
    before = await _rows(_TENANT, user)
    assert len(before) == 4
    assert any(row[4] for row in before)  # 有非 NULL embedding 行

    with caplog.at_level(logging.INFO, logger="app.ops.memory.service"):
        report = await purge_by_user(_TENANT, user)  # 默认 dry_run=True

    assert report.dry_run is True
    assert report.scanned == 4
    assert report.deleted == 0  # 干跑计数守恒
    assert report.by_status == {
        "active": 1,
        "superseded": 1,
        "revoked": 1,
        "expired": 1,
    }
    assert sum(report.by_status.values()) == report.scanned
    assert report.elapsed_s >= 0
    assert await _rows(_TENANT, user) == before  # 零写：前后逐行对拍一致

    # 审计：字段含 tenant/user/dry_run/affected，不含 key/value 内容
    assert "memory purge_by_user" in caplog.text
    assert f"tenant={_TENANT}" in caplog.text
    assert f"user={user}" in caplog.text
    assert "dry_run=True" in caplog.text
    assert "affected=0" in caplog.text
    assert "project.primary_repo" not in caplog.text
    assert "cyning/ops-desk" not in caplog.text


# ---------------- 实删：全 status 整行消失 + 召回零命中 + 审计 ----------------


async def test_real_purge_all_status_rows_gone(caplog):
    user = "u-real-" + uuid.uuid4().hex[:8]
    await _seed_four_statuses(user)
    assert len(await recall_active(_TENANT, user)) == 1  # 事前有 active 行

    with caplog.at_level(logging.INFO, logger="app.ops.memory.service"):
        report = await purge_by_user(_TENANT, user, dry_run=False)

    assert report.dry_run is False
    assert report.deleted == report.scanned == 4  # 实删计数守恒
    assert await _count(_TENANT, user) == 0  # 表行全 status 零残留
    assert await recall_active(_TENANT, user) == []  # 召回通路零命中
    assert "dry_run=False" in caplog.text
    assert "affected=4" in caplog.text
    assert "project.primary_repo" not in caplog.text  # 记动作不记内容


# ---------------- 幂等：重复实删第二次 deleted==0，审计仍留痕 ----------------


async def test_purge_idempotent_second_delete_zero(caplog):
    user = "u-idem-" + uuid.uuid4().hex[:8]
    await _seed_four_statuses(user)
    first = await purge_by_user(_TENANT, user, dry_run=False)
    assert first.deleted == 4

    with caplog.at_level(logging.INFO, logger="app.ops.memory.service"):
        second = await purge_by_user(_TENANT, user, dry_run=False)
    assert second.deleted == 0
    assert second.scanned == 0
    assert second.by_status == {}
    assert "affected=0" in caplog.text  # 幂等 0 行也留审计痕


# ---------------- 越域零影响：他 tenant/他 user 逐行不动 · 跨 tenant 0 行 ----------------


async def test_cross_tenant_and_other_user_zero_impact():
    user = "u-iso-" + uuid.uuid4().hex[:8]
    other_user = "u-iso2-" + uuid.uuid4().hex[:8]
    await _seed_four_statuses(user, tenant=_TENANT)
    await _seed_four_statuses(user, tenant=_OTHER_TENANT)  # 他 tenant 同 user
    await _seed_four_statuses(other_user, tenant=_TENANT)  # 同 tenant 他 user
    other_tenant_before = await _rows(_OTHER_TENANT, user)
    other_user_before = await _rows(_TENANT, other_user)

    report = await purge_by_user(_TENANT, user, dry_run=False)
    assert report.deleted == 4

    # 越域夹具行逐行不动
    assert await _rows(_OTHER_TENANT, user) == other_tenant_before
    assert await _rows(_TENANT, other_user) == other_user_before

    # 跨 tenant 谓词调用影响 0 行（目标 tenant 无该 user 行）
    cross = await purge_by_user(
        _OTHER_TENANT, "no-such-user-" + uuid.uuid4().hex[:8], dry_run=False
    )
    assert cross.deleted == 0
    assert await _rows(_OTHER_TENANT, user) == other_tenant_before


# ---------------- 向量通路：实删后 recall_with_vector 零命中（mock embedder） ----------------


async def test_vector_path_zero_hit_after_purge(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", "true")
    fake = FakeEmbedder()
    user = "u-vec-" + uuid.uuid4().hex[:8]
    await write_fact(_candidate(user), embedder=fake)  # 写入时嵌入（embedding 非 NULL）

    fused_before = await recall_with_vector(
        _TENANT, user, "我主要负责哪个仓库", limit=8, embedder=fake
    )
    assert [f.key for f in fused_before] == ["project.primary_repo"]  # 通路是通的

    report = await purge_by_user(_TENANT, user, dry_run=False)
    assert report.deleted == 1

    fused_after = await recall_with_vector(
        _TENANT, user, "我主要负责哪个仓库", limit=8, embedder=fake
    )
    assert fused_after == []  # 向量通路零命中（embedding 随行删除）
    assert await recall_active(_TENANT, user) == []
    assert await _count(_TENANT, user) == 0


# ---------------- 干跑/实删同谓词同计数口径（口径漂移 = 409 误拒防线） ----------------


async def test_dry_run_and_real_same_predicate_count_parity():
    user = "u-parity-" + uuid.uuid4().hex[:8]
    await _seed_four_statuses(user)
    dry = await purge_by_user(_TENANT, user, dry_run=True)
    real = await purge_by_user(_TENANT, user, dry_run=False)
    assert dry.scanned == real.scanned == real.deleted == 4
    assert dry.by_status == real.by_status
