"""host-v1-episodic-memory-feedback · D3 召回注入 + D1/D2 DB 断言（真 PostgreSQL · opsdesk_test）。

纯装配段（无 DB · 恒跑）：off 逐字节零 diff · [相似经验] 独立分节（变异检验③
锚点）· 三闸预算渲染 · 召回失败降级不注入 · env 非法回退。
DB 段（skipif 无 PG）：零互写双向表计数对拍（变异检验①锚点）· 闸拒不落库
（变异检验②锚点）· revoke_by_run · 跨租户零召回 · off 态 drop 安全 ·
迁移 upgrade/downgrade 可逆。

⚠️ 全文件 async def（asyncio_mode=auto）；DB 段 fixture 清 ep-test-% 行。
"""
from __future__ import annotations

import importlib.util
import logging
import uuid
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import BaseMessage, SystemMessage
from sqlalchemy import text

from app.ops.lg_rag.continuity import (
    EPISODE_BLOCK_MAX_CHARS,
    EPISODE_ITEM_MAX_CHARS,
    MEMORY_EPISODES_HEADER,
    MEMORY_FACTS_HEADER,
    assemble_graph_messages,
    assemble_graph_messages_with_memory,
    memory_episodes_enabled,
    memory_episodes_max_items,
    render_memory_episodes_block,
)
from app.ops.memory.episode_gate import compute_context_fingerprint

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _fixture_turns() -> list[dict]:
    return [{"role": "user", "content": f"q{i}"} for i in range(10)]


def _shape(messages: list[BaseMessage]) -> list[tuple[str, str]]:
    return [(type(m).__name__, str(m.content)) for m in messages]


def _episode_dict(summary: str, tools: list[str] | None = None, **over) -> dict:
    base = {
        "tenant_id": "ops-desk-pilot",
        "run_id": "run-" + uuid.uuid4().hex[:8],
        "task_domain": "ops_kb",
        "context_fingerprint": "f" * 64,
        "plan_summary": summary,
        "tool_sequence": tools or ["logs.read"],
        "outcome": "success",
        "status": "active",
    }
    base.update(over)
    return base


def _patch_episode_recall(monkeypatch: pytest.MonkeyPatch, *, episodes=None, error=None):
    mock = (
        AsyncMock(side_effect=error)
        if error is not None
        else AsyncMock(return_value=episodes or [])
    )
    monkeypatch.setattr(
        "app.ops.memory.episode_service.recall_success_episodes", mock
    )
    return mock


# ================= 纯装配段（无 DB） =================

# ---------------- off = 逐字节零 diff（默认关 · 双开关独立） ----------------


async def test_episodes_disabled_default_is_byte_identical(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("MEMORY_EPISODES_ENABLED", raising=False)
    history = _fixture_turns()
    baseline = assemble_graph_messages("本轮问", history)
    out = await assemble_graph_messages_with_memory(
        "本轮问",
        history,
        tenant_id="ops-desk-pilot",
        user_id="u-1",
        task_domain="ops_kb",
        intent_features={"needs_tool": True},
        tool_sequence=["logs.read"],
    )
    assert _shape(out) == _shape(baseline)


@pytest.mark.parametrize("value", ["false", "0", "no", "off", "garbage"])
async def test_episodes_disabled_or_invalid_is_byte_identical(
    monkeypatch: pytest.MonkeyPatch, value: str
):
    monkeypatch.setenv("MEMORY_EPISODES_ENABLED", value)
    history = _fixture_turns()
    baseline = assemble_graph_messages("q-now", history)
    out = await assemble_graph_messages_with_memory(
        "q-now", history, tenant_id="ops-desk-pilot", user_id="u-1", task_domain="ops_kb"
    )
    assert _shape(out) == _shape(baseline)


def test_episodes_enabled_invalid_value_warns_and_falls_back(
    monkeypatch: pytest.MonkeyPatch, caplog
):
    monkeypatch.setenv("MEMORY_EPISODES_ENABLED", "enable plz")
    with caplog.at_level(logging.WARNING, logger="app.ops.lg_rag.continuity"):
        assert memory_episodes_enabled() is False
    assert "MEMORY_EPISODES_ENABLED" in caplog.text


def test_episodes_max_items_default_and_fallback(monkeypatch: pytest.MonkeyPatch, caplog):
    monkeypatch.delenv("MEMORY_EPISODES_MAX_ITEMS", raising=False)
    assert memory_episodes_max_items() == 3
    monkeypatch.setenv("MEMORY_EPISODES_MAX_ITEMS", "abc")
    with caplog.at_level(logging.WARNING, logger="app.ops.lg_rag.continuity"):
        assert memory_episodes_max_items() == 3
    assert "MEMORY_EPISODES_MAX_ITEMS" in caplog.text
    monkeypatch.setenv("MEMORY_EPISODES_MAX_ITEMS", "0")
    assert memory_episodes_max_items() == 3
    monkeypatch.setenv("MEMORY_EPISODES_MAX_ITEMS", "5")
    assert memory_episodes_max_items() == 5


async def test_episodes_enabled_but_missing_tenant_skips(
    monkeypatch: pytest.MonkeyPatch, caplog
):
    monkeypatch.setenv("MEMORY_EPISODES_ENABLED", "true")
    history = _fixture_turns()
    baseline = assemble_graph_messages("q", history)
    with caplog.at_level(logging.WARNING, logger="app.ops.lg_rag.continuity"):
        out = await assemble_graph_messages_with_memory("q", history, task_domain="ops_kb")
    assert _shape(out) == _shape(baseline)
    assert "skip episode injection" in caplog.text


# ---------------- [相似经验] 独立分节（变异检验③锚点） ----------------


async def test_episode_section_is_physically_separate(monkeypatch: pytest.MonkeyPatch):
    """[相似经验] 是独立 SystemMessage 分节，不与 [已知事实]/[用户偏好] 合并。

    变异检验③：把经验注入并入事实块（摘 [相似经验] 头）→ 本断言必挂。
    """
    monkeypatch.setenv("MEMORY_EPISODES_ENABLED", "true")
    _patch_episode_recall(
        monkeypatch,
        episodes=[_episode_dict("先查日志再重启", ["logs.read", "svc.restart"])],
    )
    out = await assemble_graph_messages_with_memory(
        "服务挂了怎么办",
        _fixture_turns(),
        tenant_id="ops-desk-pilot",
        user_id="u-1",
        task_domain="ops_kb",
    )
    episode_msgs = [
        m
        for m in out
        if isinstance(m, SystemMessage) and str(m.content).startswith(MEMORY_EPISODES_HEADER)
    ]
    assert len(episode_msgs) == 1  # 独立 SystemMessage
    content = str(episode_msgs[0].content)
    assert MEMORY_FACTS_HEADER not in content  # 不掺事实节
    assert "先查日志再重启" in content
    # 零泄漏：事实块不掺经验内容
    assert not any(
        isinstance(m, SystemMessage)
        and str(m.content).startswith(MEMORY_FACTS_HEADER)
        and "先查日志再重启" in str(m.content)
        for m in out
    )


async def test_episode_recall_called_with_tenant_and_fingerprint(
    monkeypatch: pytest.MonkeyPatch,
):
    """召回谓词 = 同 tenant + 当前意图 fingerprint（写入同规则计算）。"""
    monkeypatch.setenv("MEMORY_EPISODES_ENABLED", "true")
    mock = _patch_episode_recall(monkeypatch, episodes=[])
    await assemble_graph_messages_with_memory(
        "q",
        _fixture_turns(),
        tenant_id="ops-desk-pilot",
        user_id="u-1",
        task_domain="ops_kb",
        intent_features={"needs_tool": True},
        tool_sequence=["logs.read"],
    )
    expected_fp = compute_context_fingerprint(
        "ops_kb", {"needs_tool": True}, ["logs.read"]
    )
    mock.assert_awaited_once()
    args, kwargs = mock.await_args
    assert args[0] == "ops-desk-pilot"
    assert args[1] == expected_fp
    assert kwargs["limit"] == 3  # 条数闸默认 3


# ---------------- 三闸预算渲染 ----------------


def test_render_episodes_block_empty():
    assert render_memory_episodes_block([]) == ""


def test_render_episodes_block_format():
    block = render_memory_episodes_block(
        [_episode_dict("先 A 后 B", ["a.read", "b.write"])]
    )
    lines = block.split("\n")
    assert lines[0] == MEMORY_EPISODES_HEADER
    assert lines[1] == "- 先 A 后 B｜工具: a.read,b.write"


def test_render_episode_item_over_200_truncated():
    """单条闸：行 >200 字符 → 截到 200 加省略号。"""
    block = render_memory_episodes_block([_episode_dict("长" * 300)])
    line = block.split("\n")[1]
    assert len(line) == EPISODE_ITEM_MAX_CHARS
    assert line.endswith("…")


def test_render_episode_block_over_800_drops_tail():
    """整块闸：>800 字符从尾部丢低优先级行（召回序尾部 = 最旧）。"""
    episodes = [_episode_dict(f"经验{i:02d}" + "述" * 150) for i in range(6)]
    block = render_memory_episodes_block(episodes)
    assert len(block) <= EPISODE_BLOCK_MAX_CHARS
    lines = block.split("\n")
    assert lines[0] == MEMORY_EPISODES_HEADER
    assert len(lines) < 7  # 尾部行被丢
    # 保住的是前面的（高优先级），丢的是尾部
    assert "经验00" in block
    assert "经验05" not in block


def test_render_episode_first_item_hard_truncated_into_budget():
    """首条都装不下整块预算时硬截进预算（宁少给，不超预算）。"""
    episodes = [_episode_dict("巨" * 1000)]
    block = render_memory_episodes_block(episodes)
    assert len(block) <= EPISODE_BLOCK_MAX_CHARS
    assert block.startswith(MEMORY_EPISODES_HEADER)


def test_render_episode_multiline_summary_escaped():
    block = render_memory_episodes_block([_episode_dict("a\nb")])
    assert "a\\nb" in block  # 换行转义，保住一行一条


# ---------------- span 与降级 ----------------


def _capture_span(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    from app.ops.lg_rag import continuity

    captured: list[dict] = []
    monkeypatch.setattr(
        continuity, "update_current_span_metadata", lambda m: captured.append(m)
    )
    return captured


async def test_span_memory_episodes_injected_count(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MEMORY_EPISODES_ENABLED", "true")
    captured = _capture_span(monkeypatch)
    _patch_episode_recall(
        monkeypatch,
        episodes=[_episode_dict("e1"), _episode_dict("e2")],
    )
    await assemble_graph_messages_with_memory(
        "q", _fixture_turns(), tenant_id="ops-desk-pilot", user_id="u-1", task_domain="ops_kb"
    )
    ep_spans = [m for m in captured if any(k.startswith("memory_episodes") for k in m)]
    assert ep_spans == [{"memory_episodes_injected": 2}]


async def test_span_memory_episodes_injected_zero(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MEMORY_EPISODES_ENABLED", "true")
    captured = _capture_span(monkeypatch)
    _patch_episode_recall(monkeypatch, episodes=[])
    out = await assemble_graph_messages_with_memory(
        "q", _fixture_turns(), tenant_id="ops-desk-pilot", user_id="u-1", task_domain="ops_kb"
    )
    ep_spans = [m for m in captured if any(k.startswith("memory_episodes") for k in m)]
    assert ep_spans == [{"memory_episodes_injected": 0}]
    assert not any(
        isinstance(m, SystemMessage) and str(m.content).startswith(MEMORY_EPISODES_HEADER)
        for m in out
    )


async def test_episode_recall_failure_degrades_to_no_injection(
    monkeypatch: pytest.MonkeyPatch, caplog
):
    """召回失败降级不注入（承事实召回 :369 先例）：输出与 off 逐字节一致。"""
    monkeypatch.setenv("MEMORY_EPISODES_ENABLED", "true")
    captured = _capture_span(monkeypatch)
    history = _fixture_turns()
    baseline = assemble_graph_messages("q", history)
    _patch_episode_recall(monkeypatch, error=RuntimeError("db down"))
    with caplog.at_level(logging.ERROR, logger="app.ops.lg_rag.continuity"):
        out = await assemble_graph_messages_with_memory(
            "q", history, tenant_id="ops-desk-pilot", user_id="u-1", task_domain="ops_kb"
        )
    assert _shape(out) == _shape(baseline)
    ep_spans = [m for m in captured if any(k.startswith("memory_episodes") for k in m)]
    assert ep_spans == [{"memory_episodes_degraded": True}]
    assert "degrade to no injection" in caplog.text


# ================= DB 段（真 PostgreSQL · opsdesk_test） =================

from app.db.models import now_utc  # noqa: E402
from app.db.session import AsyncSessionLocal, engine  # noqa: E402
from app.ops.memory.episode_gate import EpisodeCandidate  # noqa: E402
from app.ops.memory.episode_service import (  # noqa: E402
    EpisodeGateRejectedError,
    recall_success_episodes,
    revoke_by_run,
    write_episode,
)
from app.ops.memory.gate import FactCandidate  # noqa: E402
from app.ops.memory.service import write_fact  # noqa: E402
from tests.conftest import DB_AVAILABLE  # noqa: E402

_needs_pg = pytest.mark.skipif(
    not DB_AVAILABLE, reason="需要 PostgreSQL（conftest 会准备 opsdesk_test）"
)

_TENANT = "ep-test-tenant"
_OTHER_TENANT = "ep-test-tenant-b"


async def _clear_test_rows() -> None:
    if not DB_AVAILABLE:
        return
    async with AsyncSessionLocal() as session, session.begin():
        await session.execute(
            text("DELETE FROM ops_memory_episodes WHERE tenant_id LIKE 'ep-test-%'")
        )
        await session.execute(
            text("DELETE FROM ops_memory_facts WHERE tenant_id LIKE 'ep-test-%'")
        )


@pytest.fixture(autouse=True)
async def _clean():
    await _clear_test_rows()
    yield
    await _clear_test_rows()


def _ep_candidate(**over) -> EpisodeCandidate:
    base = {
        "tenant_id": _TENANT,
        "run_id": "run-" + uuid.uuid4().hex[:8],
        "task_domain": "ops_kb",
        "context_fingerprint": compute_context_fingerprint(
            "ops_kb", {"needs_tool": True}, ["logs.read"]
        ),
        "plan_summary": "先查日志再重启服务",
        "tool_sequence": ["logs.read", "svc.restart"],
        "outcome": "success",
    }
    base.update(over)
    return EpisodeCandidate(**base)


async def _count_episodes(tenant_id: str = _TENANT) -> int:
    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            text("SELECT count(*) FROM ops_memory_episodes WHERE tenant_id = :t"),
            {"t": tenant_id},
        )
        return int(rows.scalar() or 0)


async def _count_facts(tenant_id: str = _TENANT) -> int:
    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            text("SELECT count(*) FROM ops_memory_facts WHERE tenant_id = :t"),
            {"t": tenant_id},
        )
        return int(rows.scalar() or 0)


# ---------------- D2 · 零互写双向表计数对拍（变异检验①锚点） ----------------


@_needs_pg
async def test_zero_interwrite_episode_write_does_not_touch_facts(
    monkeypatch: pytest.MonkeyPatch,
):
    """write_episode 后 ops_memory_facts 计数零变化（变异检验①：episode_service
    临时写一行 ops_memory_facts → 本断言必挂）。"""
    monkeypatch.setenv("MEMORY_EPISODES_WRITE_ENABLED", "true")
    facts_before = await _count_facts()
    ep = await write_episode(_ep_candidate())
    assert ep is not None
    assert await _count_episodes() == 1
    assert await _count_facts() == facts_before  # 事实表零变化


@_needs_pg
async def test_zero_interwrite_fact_write_does_not_touch_episodes():
    """write_fact 后 episodes 计数零变化（双向对拍）。"""
    episodes_before = await _count_episodes()
    await write_fact(
        FactCandidate(
            tenant_id=_TENANT,
            user_id="u-interwrite",
            key="project.interwrite_probe",
            value="probe",
        )
    )
    assert await _count_facts() == 1
    assert await _count_episodes() == episodes_before  # episode 表零变化


# ---------------- D2 · 闸拒不落库（变异检验②锚点） + 写开关默认关 ----------------


@_needs_pg
async def test_gate_rejection_writes_nothing(monkeypatch: pytest.MonkeyPatch):
    """闸拒 = 不落库（查表为零，不是存了不召回）。

    变异检验②：闸恒放行 → 本断言必挂。
    """
    monkeypatch.setenv("MEMORY_EPISODES_WRITE_ENABLED", "true")
    with pytest.raises(EpisodeGateRejectedError) as exc:
        await write_episode(_ep_candidate(outcome="failure"))  # failure 缺 class
    assert exc.value.reason_code == "failure_class_missing"
    assert await _count_episodes() == 0

    with pytest.raises(EpisodeGateRejectedError) as exc2:
        await write_episode(_ep_candidate(plan_summary="长" * 201))
    assert exc2.value.reason_code == "plan_summary_too_long"
    assert await _count_episodes() == 0

    with pytest.raises(EpisodeGateRejectedError) as exc3:
        await write_episode(_ep_candidate(outcome="failure", failure_class="llm_error"))
    assert exc3.value.reason_code == "failure_class_invalid"
    assert await _count_episodes() == 0


@_needs_pg
async def test_write_switch_default_off_writes_nothing(monkeypatch: pytest.MonkeyPatch):
    """MEMORY_EPISODES_WRITE_ENABLED 默认关：不读不写返回 None（off 态零写入）。"""
    monkeypatch.delenv("MEMORY_EPISODES_WRITE_ENABLED", raising=False)
    result = await write_episode(_ep_candidate())
    assert result is None
    assert await _count_episodes() == 0


# ---------------- D3 · 召回：success+active+fingerprint · 跨租户零召回 ----------------


@_needs_pg
async def test_recall_only_success_active_fingerprint(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MEMORY_EPISODES_WRITE_ENABLED", "true")
    fp_a = compute_context_fingerprint("ops_kb", {"needs_tool": True}, ["logs.read"])
    fp_b = compute_context_fingerprint("ops_kb", {"needs_tool": False}, ["logs.read"])
    await write_episode(_ep_candidate())  # fp_a success active → 命中
    await write_episode(_ep_candidate(outcome="failure", failure_class="other"))  # failure 不召回
    await write_episode(_ep_candidate(outcome="partial"))  # partial 不召回
    await write_episode(_ep_candidate(context_fingerprint=fp_b))  # 异指纹不命中

    recalled = await recall_success_episodes(_TENANT, fp_a, limit=3)
    assert len(recalled) == 1
    assert recalled[0].outcome == "success"
    assert recalled[0].status == "active"

    # 异指纹零命中（宁可不召回方向）
    assert await recall_success_episodes(_TENANT, "0" * 64, limit=3) == []


@_needs_pg
async def test_cross_tenant_recall_is_empty(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MEMORY_EPISODES_WRITE_ENABLED", "true")
    fp = compute_context_fingerprint("ops_kb", {"needs_tool": True}, ["logs.read"])
    await write_episode(_ep_candidate())
    assert await recall_success_episodes(_OTHER_TENANT, fp, limit=3) == []
    assert len(await recall_success_episodes(_TENANT, fp, limit=3)) == 1


@_needs_pg
async def test_recall_top_n_deterministic_order(monkeypatch: pytest.MonkeyPatch):
    """top-N = created_at desc；超限截最旧（确定性，不随机）。"""
    monkeypatch.setenv("MEMORY_EPISODES_WRITE_ENABLED", "true")
    fp = compute_context_fingerprint("ops_kb", {"needs_tool": True}, ["logs.read"])
    eps = [await write_episode(_ep_candidate()) for _ in range(5)]
    # 钉死 created_at 顺序：eps[0] 最旧 … eps[4] 最新
    from datetime import timedelta

    async with AsyncSessionLocal() as session, session.begin():
        for i, ep in enumerate(eps):
            await session.execute(
                text("UPDATE ops_memory_episodes SET created_at = :ts WHERE id = :i"),
                {"ts": now_utc() + timedelta(seconds=i), "i": str(ep.id)},
            )
    recalled = await recall_success_episodes(_TENANT, fp, limit=3)
    assert len(recalled) == 3
    ids = [str(r.id) for r in recalled]
    assert ids == [str(eps[4].id), str(eps[3].id), str(eps[2].id)]


# ---------------- D2 · revoke_by_run：召回零命中 · 表内可查 · 审计 · 幂等 ----------------


@_needs_pg
async def test_revoke_by_run_zero_hits_row_kept_audit_idempotent(
    monkeypatch: pytest.MonkeyPatch, caplog
):
    monkeypatch.setenv("MEMORY_EPISODES_WRITE_ENABLED", "true")
    fp = compute_context_fingerprint("ops_kb", {"needs_tool": True}, ["logs.read"])
    run_id = "run-revoke-" + uuid.uuid4().hex[:8]
    ep = await write_episode(_ep_candidate(run_id=run_id))
    assert len(await recall_success_episodes(_TENANT, fp, limit=3)) == 1

    with caplog.at_level(logging.INFO, logger="app.ops.memory.episode_service"):
        n1 = await revoke_by_run(run_id)
    assert n1 == 1
    assert await recall_success_episodes(_TENANT, fp, limit=3) == []  # 召回零命中
    assert f"run_id={run_id} affected=1" in caplog.text  # 审计记动作

    # 行留表可查（status=revoked）
    async with AsyncSessionLocal() as session:
        row = (
            await session.execute(
                text("SELECT status FROM ops_memory_episodes WHERE id = :i"),
                {"i": str(ep.id)},
            )
        ).first()
    assert row is not None and row[0] == "revoked"

    assert await revoke_by_run(run_id) == 0  # 幂等
    assert await revoke_by_run("run-never-existed") == 0


# ---------------- D1 · off 态 drop 安全（表不存在读写不炸） + 迁移可逆 ----------------

_MIGRATION_PATH = _REPO_ROOT / "alembic/versions/20260923_memory_episodes.py"


def _load_migration_module():
    spec = importlib.util.spec_from_file_location(
        "migration_20260923_memory_episodes", _MIGRATION_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _migration_sql(direction: str) -> list[str]:
    """捕获 migration upgrade()/downgrade() 的 op.execute SQL（不落库）。"""
    module = _load_migration_module()
    captured: list[str] = []
    import alembic.op as alembic_op

    original = alembic_op.execute
    alembic_op.execute = lambda sql, *a, **k: captured.append(str(sql))  # type: ignore[assignment]
    try:
        getattr(module, direction)()
    finally:
        alembic_op.execute = original  # type: ignore[assignment]
    return captured


async def _exec_sqls(sqls: list[str]) -> None:
    async with engine.begin() as conn:
        for sql in sqls:
            await conn.execute(text(sql))


async def _table_exists() -> bool:
    async with AsyncSessionLocal() as session:
        rows = await session.execute(text("SELECT to_regclass('ops_memory_episodes')"))
        return rows.scalar() is not None


def test_migration_chain_and_reversible_sql_shape():
    """迁移链：head 接 20260922_session_summaries 后；upgrade 含全列/索引，
    downgrade 含对应 DROP（可逆形状断言 · 无 DB 恒跑）。"""
    module = _load_migration_module()
    assert module.revision == "20260923_memory_episodes"
    assert module.down_revision == "20260922_session_summaries"

    up = "\n".join(_migration_sql("upgrade"))
    for column in (
        "tenant_id",
        "run_id",
        "task_domain",
        "context_fingerprint",
        "plan_summary",
        "tool_sequence",
        "outcome",
        "failure_class",
        "status",
        "created_at",
    ):
        assert column in up
    for index in (
        "idx_ops_memory_episodes_recall",
        "idx_ops_memory_episodes_fingerprint",
        "idx_ops_memory_episodes_run",
    ):
        assert index in up
    down = "\n".join(_migration_sql("downgrade"))
    assert "DROP TABLE IF EXISTS ops_memory_episodes" in down
    for index in (
        "idx_ops_memory_episodes_recall",
        "idx_ops_memory_episodes_fingerprint",
        "idx_ops_memory_episodes_run",
    ):
        assert f"DROP INDEX IF EXISTS {index}" in down


@_needs_pg
async def test_migration_upgrade_downgrade_roundtrip_on_db():
    """迁移可逆实证：upgrade SQL 建表 → downgrade SQL 掉表 → upgrade 复原。"""
    up_sqls = _migration_sql("upgrade")
    down_sqls = _migration_sql("downgrade")
    assert await _table_exists() is True  # conftest create_all 已建
    try:
        await _exec_sqls(down_sqls)
        assert await _table_exists() is False
        await _exec_sqls(up_sqls)
        assert await _table_exists() is True
        # 索引真实存在
        async with AsyncSessionLocal() as session:
            rows = await session.execute(
                text(
                    "SELECT indexname FROM pg_indexes "
                    "WHERE tablename = 'ops_memory_episodes' ORDER BY indexname"
                )
            )
            names = {r[0] for r in rows.all()}
        assert {
            "idx_ops_memory_episodes_recall",
            "idx_ops_memory_episodes_fingerprint",
            "idx_ops_memory_episodes_run",
        } <= names
    finally:
        await _exec_sqls(up_sqls)  # 幂等复原（IF NOT EXISTS）


@_needs_pg
async def test_dropped_table_read_write_revoke_degrade_safely(
    monkeypatch: pytest.MonkeyPatch,
):
    """off 态 drop 安全：表不存在时 write/recall/revoke 全降级不炸（承
    session_summaries 先例 · SPEC FP-4）。"""
    monkeypatch.setenv("MEMORY_EPISODES_WRITE_ENABLED", "true")
    up_sqls = _migration_sql("upgrade")
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS ops_memory_episodes"))
    try:
        assert await _table_exists() is False
        # 写：降级返回 None（不炸 run 终态异步面）
        assert await write_episode(_ep_candidate()) is None
        # 读：降级空列表
        assert await recall_success_episodes(_TENANT, "f" * 64, limit=3) == []
        # 撤：降级 0 行
        assert await revoke_by_run("run-any") == 0
        # 装配面：on 态也不炸（降级不注入）
        monkeypatch.setenv("MEMORY_EPISODES_ENABLED", "true")
        history = _fixture_turns()
        baseline = assemble_graph_messages("q", history)
        out = await assemble_graph_messages_with_memory(
            "q", history, tenant_id=_TENANT, user_id="u-1", task_domain="ops_kb"
        )
        assert _shape(out) == _shape(baseline)
    finally:
        await _exec_sqls(up_sqls)  # 复原供后续用例
        assert await _table_exists() is True
