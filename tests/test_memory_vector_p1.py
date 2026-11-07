"""memory-facts-p1 · 向量语义召回红线（真 PostgreSQL · opsdesk_test · fake embedder 确定性）。

红线（SPEC §5 D3 / task V3）：
① 复述召回：写入 project.primary_repo 后用改写 query 经**向量通路**召回
   （构造确定性 top-N 不含该事实，只有向量 top-M 能捞到它）
⑤ 向量降级：embedder 抛错 → 回退确定性结果 + memory_vector_degraded 标记
⑦ 变异检验：错误事实经向量通路真被复述 query 召回 → revoke_by_source → 消失
另：写入时嵌入失败不阻断写入；null embedding 存量行只走确定性通路；
跨 tenant 向量召回为空；融合截断确定性。

fake embedder：关键词命中间 → 正交单位基向量（1024 维），无随机、不连外网。

⚠️ 全文件 async def（asyncio_mode=auto）；不要自建 event loop。
"""

from __future__ import annotations

import logging
import uuid
from datetime import timedelta

import pytest
from sqlalchemy import text

from app.db.models import now_utc
from app.db.session import AsyncSessionLocal
from app.ops.memory.gate import FactCandidate
from app.ops.memory.service import (
    recall_active,
    recall_with_vector,
    revoke_by_source,
    write_fact,
)
from tests.conftest import DB_AVAILABLE

pytestmark = pytest.mark.skipif(
    not DB_AVAILABLE, reason="需要 PostgreSQL（conftest 会准备 opsdesk_test）"
)

_TENANT = "mfv1-test-tenant"
_OTHER_TENANT = "mfv1-test-tenant-b"
_EMBED_DIM = 1024


class FakeEmbedder:
    """确定性向量：命中间 → 正交单位基向量；无命中 → 兜底基向量。"""

    name = "fake-embedder"

    def _vec(self, text_value: str) -> list[float]:
        t = text_value.lower()
        v = [0.0] * _EMBED_DIM
        if any(k in t for k in ("repo", "仓库")):
            v[0] = 1.0
        elif any(k in t for k in ("deploy", "部署")):
            v[1] = 1.0
        else:
            v[2] = 1.0
        return v

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]


class BoomEmbedder:
    """embed 必抛：验证降级通路。"""

    name = "boom-embedder"

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("embed down")


async def _prepare() -> None:
    """清测试行（embedding 列由 conftest _create_test_schema 保证）。"""
    async with AsyncSessionLocal() as session, session.begin():
        await session.execute(
            text("DELETE FROM ops_memory_facts WHERE tenant_id LIKE 'mfv1-test-%'")
        )


@pytest.fixture(autouse=True)
async def _clean():
    await _prepare()
    yield
    await _prepare()


def _candidate(**over) -> FactCandidate:
    base = {
        "tenant_id": _TENANT,
        "user_id": "u-" + uuid.uuid4().hex[:8],
        "key": "project.primary_repo",
        "value": "cyning/ops-desk",
    }
    base.update(over)
    return FactCandidate(**base)


async def _pin_updated_at(fact_id: str, ts) -> None:
    async with AsyncSessionLocal() as session, session.begin():
        await session.execute(
            text("UPDATE ops_memory_facts SET updated_at = :ts WHERE id = :i"),
            {"ts": ts, "i": fact_id},
        )


async def _embedding_of(fact_id: str):
    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            text("SELECT embedding FROM ops_memory_facts WHERE id = :i"),
            {"i": fact_id},
        )
        return rows.scalar()


# ---------------- ① 复述召回：向量通路捞回确定性 top-N 漏掉的事实 ----------------


async def test_paraphrase_query_recalls_fact_via_vector_path(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", "true")
    fake = FakeEmbedder()
    user = "u-para"
    target = await write_fact(_candidate(user_id=user), embedder=fake)
    d1 = await write_fact(
        _candidate(user_id=user, key="project.favorite_color", value="blue"),
        embedder=fake,
    )
    d2 = await write_fact(
        _candidate(user_id=user, key="project.favorite_editor", value="vim"),
        embedder=fake,
    )
    # 钉死 updated_at：target 最旧 → 确定性 top-2 只有 d1/d2
    base = now_utc()
    await _pin_updated_at(str(target.id), base)
    await _pin_updated_at(str(d1.id), base + timedelta(seconds=1))
    await _pin_updated_at(str(d2.id), base + timedelta(seconds=2))

    deterministic = await recall_active(_TENANT, user, limit=2)
    assert "project.primary_repo" not in {f.key for f in deterministic}  # 前提：确定性漏掉

    # 改写 query（"我主要负责哪个仓库" ≈ primary_repo；fake embedder 同基向量）
    fused = await recall_with_vector(_TENANT, user, "我主要负责哪个仓库", limit=2, embedder=fake)
    assert fused[0].key == "project.primary_repo"  # 向量通路真召回且排首
    assert str(fused[0].id) == str(target.id)


# ---------------- 存量行 null embedding：只走确定性通路即正确 ----------------


async def test_null_embedding_rows_stay_on_deterministic_path(
    monkeypatch: pytest.MonkeyPatch,
):
    # 开关关时写入 = P0 行为：embedding 留 NULL（既有行不回填等价态）
    # 显式钉 off：宿主 .env 可能设 MEMORY_FACTS_VECTOR_RECALL_ENABLED=true
    # （test-baseline-reds 全量回归 unmask：网络可用时写入路径会真嵌向量）
    monkeypatch.delenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", raising=False)
    user = "u-null"
    fact = await write_fact(_candidate(user_id=user))
    assert await _embedding_of(str(fact.id)) is None

    monkeypatch.setenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", "true")
    fused = await recall_with_vector(
        _TENANT, user, "我主要负责哪个仓库", limit=8, embedder=FakeEmbedder()
    )
    # null embedding 行不进向量 top-M，但确定性 ∪ 仍把它带回来
    assert str(fact.id) in {str(f.id) for f in fused}


# ---------------- ⑤ 向量降级：embedder 抛错 → 回退确定性 + memory_vector_degraded ----------------


async def test_embedder_failure_degrades_with_marker(monkeypatch: pytest.MonkeyPatch, caplog):
    monkeypatch.setenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", "true")
    # 播种走 FakeEmbedder（同 ⑦ 变异检验的装配口径）：本用例测的是「召回时 embedder 抛错」，
    # 不依赖 SILICONFLOW_API_KEY 真实环境——缺 key 的干净环境此前在此裸奔 RuntimeError。
    monkeypatch.setattr("app.ops.rag.embedder.get_query_embedder", lambda: FakeEmbedder())
    user = "u-degrade"
    await write_fact(_candidate(user_id=user))
    expected = await recall_active(_TENANT, user, limit=8)

    with caplog.at_level(logging.WARNING, logger="app.ops.memory.service"):
        fused = await recall_with_vector(
            _TENANT, user, "任意问题", limit=8, embedder=BoomEmbedder()
        )
    assert [str(f.id) for f in fused] == [str(f.id) for f in expected]  # 回退=P0 结果
    assert "memory_vector_degraded" in caplog.text  # 降级标记


async def test_write_embed_failure_does_not_block(monkeypatch: pytest.MonkeyPatch, caplog):
    monkeypatch.setenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", "true")
    user = "u-writeboom"
    with caplog.at_level(logging.WARNING, logger="app.ops.memory.service"):
        fact = await write_fact(_candidate(user_id=user), embedder=BoomEmbedder())
    assert fact.id  # 写入不被嵌入失败阻断
    assert await _embedding_of(str(fact.id)) is None  # 该行走确定性通路
    assert "stays deterministic" in caplog.text


# ---------------- ⑦ 变异检验：错误事实经向量通路真召回 → revoke → 消失 ----------------


async def test_mutation_wrong_fact_vector_recalled_then_revoke(
    monkeypatch: pytest.MonkeyPatch,
):
    """缺"先断言真召回"，"撤销后消失"就是假通过（对齐 P0 变异检验纪律）。"""
    monkeypatch.setenv("MEMORY_FACTS_ENABLED", "true")
    monkeypatch.setenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", "true")
    monkeypatch.setenv("MEMORY_FACTS_MAX_ITEMS", "1")
    fake = FakeEmbedder()
    # 装配路径走 get_query_embedder 工厂：patch 成 fake（不连外网）
    monkeypatch.setattr("app.ops.rag.embedder.get_query_embedder", lambda: fake)

    user = "u-mutation"
    src = "run-wrong-" + uuid.uuid4().hex[:8]
    wrong = await write_fact(
        _candidate(user_id=user, key="project.deploy_target", value="wrong-prod-host"),
        source_run_id=src,
        embedder=fake,
    )
    distractor = await write_fact(
        _candidate(user_id=user, key="project.favorite_color", value="blue"),
        embedder=fake,
    )
    # 错误事实略旧：确定性 top-1 只有 distractor，向量通路才捞得到错误事实
    base = now_utc()
    await _pin_updated_at(str(wrong.id), base)
    await _pin_updated_at(str(distractor.id), base + timedelta(seconds=1))

    deterministic = await recall_active(_TENANT, user, limit=1)
    assert [f.key for f in deterministic] == ["project.favorite_color"]  # 前提：确定性漏掉

    # 第一步：复述 query 经向量通路**真召回**错误事实（相似 1.0 × 抽取权重 0.8
    # > SIM_FLOOR 0.3 × 显式权重 1.0，排第一）
    # 注记：SIM_FLOOR 0.5→0.3 为 task memory-fusion-weight-tuning 调参定稿（2026-09-21）；
    # 断言语义不变（0.8 > 0.3 不等式方向同旧值），仅注释同步新默认值。
    fused = await recall_with_vector(_TENANT, user, "部署到哪里？", limit=1, embedder=fake)
    assert [f.key for f in fused] == ["project.deploy_target"]
    assert fused[0].value == "wrong-prod-host"

    n = await revoke_by_source(src)
    assert n == 1
    fused_after = await recall_with_vector(_TENANT, user, "部署到哪里？", limit=1, embedder=fake)
    assert all(f.key != "project.deploy_target" for f in fused_after)  # 消失

    # 装配面（④b 休眠断言）：注入开 + 向量开关开下装配面恒零注入块、输出逐字节等于
    # 基线；污染/痊愈三态由服务层 recall_with_vector 断言承担（写入侧零改动对拍）。
    # ④a 复活时按 docs/tasks/deferred/task_memory_facts_build_4a.md 清单恢复注入块断言。
    from app.ops.lg_rag.continuity import (
        MEMORY_FACTS_HEADER,
        assemble_graph_messages,
        assemble_graph_messages_with_memory,
    )

    src2 = "run-wrong2-" + uuid.uuid4().hex[:8]
    await write_fact(
        _candidate(user_id=user, key="project.deploy_target", value="wrong-again"),
        source_run_id=src2,
        embedder=fake,
    )
    # 服务层通路是通的：新污染同样经向量通路真召回（装配休眠断言非空真）
    fused2 = await recall_with_vector(_TENANT, user, "部署到哪里？", limit=8, embedder=fake)
    assert any(f.key == "project.deploy_target" and f.value == "wrong-again" for f in fused2)
    baseline = assemble_graph_messages("部署到哪里？", [])
    polluted = await assemble_graph_messages_with_memory(
        "部署到哪里？", [], tenant_id=_TENANT, user_id=user
    )
    assert [(type(m).__name__, str(m.content)) for m in polluted] == [
        (type(m).__name__, str(m.content)) for m in baseline
    ]
    assert not any(MEMORY_FACTS_HEADER in str(m.content) for m in polluted)
    await revoke_by_source(src2)
    fused2_after = await recall_with_vector(_TENANT, user, "部署到哪里？", limit=8, embedder=fake)
    assert all(f.value != "wrong-again" for f in fused2_after)  # 服务层痊愈
    healed = await assemble_graph_messages_with_memory(
        "部署到哪里？", [], tenant_id=_TENANT, user_id=user
    )
    assert not any("wrong-again" in str(m.content) for m in healed)
    assert not any(MEMORY_FACTS_HEADER in str(m.content) for m in healed)


# ---------------- 跨 tenant：向量查询必带 tenant 谓词 ----------------


async def test_cross_tenant_vector_recall_empty(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", "true")
    fake = FakeEmbedder()
    user = "u-iso"
    await write_fact(_candidate(user_id=user), embedder=fake)
    fused = await recall_with_vector(
        _OTHER_TENANT, user, "我主要负责哪个仓库", limit=8, embedder=fake
    )
    assert fused == []  # 跨 tenant = 空（含向量通路）


# ---------------- 融合截断确定性：同输入两次同输出 ----------------


async def test_fused_recall_deterministic_tiebreak(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", "true")
    fake = FakeEmbedder()
    user = "u-det"
    for i in range(4):
        await write_fact(
            _candidate(user_id=user, key=f"project.item_{i:02d}", value=f"v{i}"),
            embedder=fake,
        )
    first = await recall_with_vector(_TENANT, user, "任意问题", limit=2, embedder=fake)
    second = await recall_with_vector(_TENANT, user, "任意问题", limit=2, embedder=fake)
    assert [str(f.id) for f in first] == [str(f.id) for f in second]  # 截低分不随机
    assert len(first) == 2


# ---------------- env 非法值回退 + warning ----------------


def test_vector_recall_env_invalid_fallback(monkeypatch: pytest.MonkeyPatch, caplog):
    from app.ops.memory.service import memory_facts_vector_recall_enabled

    monkeypatch.delenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", raising=False)
    assert memory_facts_vector_recall_enabled() is False
    monkeypatch.setenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", "enable plz")
    with caplog.at_level(logging.WARNING, logger="app.ops.memory.service"):
        assert memory_facts_vector_recall_enabled() is False
    assert "MEMORY_FACTS_VECTOR_RECALL_ENABLED" in caplog.text
    monkeypatch.setenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", "1")
    assert memory_facts_vector_recall_enabled() is True


# ---------------- memory-preference-profile · 向量通路召回的 preference 进偏好节 ----------------


async def test_vector_recalled_preference_lands_in_preference_section(
    monkeypatch: pytest.MonkeyPatch,
):
    """向量通路捞回的 preference 同样进 `[用户偏好]` 节（SQL 不加 kind 谓词，
    渲染层分 kind）；确定性 top-1 漏掉它 → 证明真走向量通路。"""
    monkeypatch.setenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", "true")
    fake = FakeEmbedder()
    user = "u-pref-vec"
    pref = await write_fact(
        _candidate(user_id=user, key="pref.deploy_tone", value="极简", kind="preference"),
        embedder=fake,
    )
    distractor = await write_fact(
        _candidate(user_id=user, key="project.favorite_color", value="blue"),
        embedder=fake,
    )
    base = now_utc()
    await _pin_updated_at(str(pref.id), base)
    await _pin_updated_at(str(distractor.id), base + timedelta(seconds=1))

    deterministic = await recall_active(_TENANT, user, limit=1)
    assert [f.key for f in deterministic] == ["project.favorite_color"]  # 前提：确定性漏掉

    fused = await recall_with_vector(_TENANT, user, "部署风格如何", limit=1, embedder=fake)
    assert [f.key for f in fused] == ["pref.deploy_tone"]
    assert fused[0].kind == "preference"

    from app.ops.lg_rag.continuity import (
        MEMORY_FACTS_HEADER,
        MEMORY_PREFERENCES_HEADER,
        render_memory_facts_block,
    )

    block = render_memory_facts_block(fused)
    assert MEMORY_PREFERENCES_HEADER in block
    assert "pref.deploy_tone=极简" in block
    assert MEMORY_FACTS_HEADER not in block  # 向量捞回的 preference 不污染事实节
