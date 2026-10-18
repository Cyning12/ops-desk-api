"""memory-embedding-backfill · D1/D2/D4 回填批处理集成测试（真 PostgreSQL · opsdesk_test）。

覆盖（逐块映射 task 验收标准）：
- D1：扫描谓词只命中 active-NULL（superseded/revoked/expired/已嵌行零嵌入）·
  embed() 文本 == _fact_embed_text(key, value) 逐条一致 · asyncio.to_thread 线程卸载断言 ·
  回写再核竞态（supersede 行记 skipped 保持 NULL）· 前置校验维度/name 不符 exit 2 零写入 ·
  keyset 分页 id 严格递增无重复
- D2：幂等重跑零嵌入调用 · 断点续跑（连续 3 页全败终止 → 重跑补齐不重复）·
  部分失败计数 + failed_ids + 重跑清零 · 报告形态 + 计数守恒 ·
  env 非法值回退 + warning · --dry-run 零嵌入零写库
- D4：干跑/实跑对账（scanned 相等 · 重扫剩余 == failed）· 对账不等 → status failed（不伪装成功）·
  金样轨**态② FakeEmbedder 集成夹具**：paraphrase 查询回填前 top1 不命中存量行 / 回填后命中

⚠️ 全文件 async def（asyncio_mode=auto）；回填是全表扫描，fixture 清**全表**保确定性
（opsdesk_test 由 conftest _assert_test_database 强制隔离，删全表安全）。
"""

from __future__ import annotations

import logging
import threading
import uuid
from datetime import datetime, timedelta

import httpx
import pytest
import yaml
from sqlalchemy import text

from app.config import settings
from app.db.models import now_utc
from app.db.session import AsyncSessionLocal
from app.ops.memory.gate import FactCandidate
from app.ops.memory.service import (
    _fact_embed_text,
    recall_with_vector,
    write_fact,
)
from scripts.memory_embedding_backfill import (
    PREFLIGHT_PROBE_TEXT,
    BackfillPreflightError,
    _read_checkpoint,
    backfill_batch_size,
    backfill_checkpoint_path,
    backfill_sleep_ms,
    main,
    run_backfill,
)
from tests.conftest import DB_AVAILABLE

pytestmark = pytest.mark.skipif(
    not DB_AVAILABLE, reason="需要 PostgreSQL（conftest 会准备 opsdesk_test）"
)

_TENANT = "mfb-test-tenant"
_EMBED_DIM = 1024


class RecordingFakeEmbedder:
    """确定性向量（关键词 → 正交单位基向量）+ 调用记录/故障注入/竞态回调。

    - calls：全部 embed() 调用（含前置试嵌探针）；fact_calls 过滤探针。
    - fail_on_fact_calls：fact 调用序号（0-based）命中 → 抛 httpx.HTTPError。
    - on_text：embed 内同步回调（竞态/并发写模拟，跑在 to_thread 工作线程）。
    - thread_idents：线程卸载断言（须 != 事件循环主线程）。
    """

    def __init__(self, *, dim: int = _EMBED_DIM, name: str = "fake-embedder") -> None:
        self.name = name
        self._dim = dim
        self.calls: list[list[str]] = []
        self.thread_idents: set[int] = set()
        self.fail_on_fact_calls: set[int] = set()
        self.on_text = None

    @property
    def fact_calls(self) -> list[list[str]]:
        return [c for c in self.calls if c != [PREFLIGHT_PROBE_TEXT]]

    def _vec(self, text_value: str) -> list[float]:
        t = text_value.lower()
        v = [0.0] * self._dim
        if any(k in t for k in ("repo", "仓库")):
            v[0] = 1.0
        elif any(k in t for k in ("deploy", "部署")):
            v[1] = 1.0
        else:
            v[2] = 1.0
        return v

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.thread_idents.add(threading.get_ident())
        self.calls.append(list(texts))
        if self.on_text is not None:
            for t in texts:
                self.on_text(t)
        if (
            list(texts) != [PREFLIGHT_PROBE_TEXT]
            and (len(self.fact_calls) - 1) in self.fail_on_fact_calls
        ):
            raise httpx.HTTPError("embed down (injected)")
        return [self._vec(t) for t in texts]


@pytest.fixture(autouse=True)
def _force_defaults(monkeypatch: pytest.MonkeyPatch):
    """写入侧嵌入默认关（写入即 NULL 存量行）；各用例按需自行 setenv。"""
    monkeypatch.delenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", raising=False)
    monkeypatch.delenv("MEMORY_BACKFILL_BATCH_SIZE", raising=False)
    monkeypatch.delenv("MEMORY_BACKFILL_SLEEP_MS", raising=False)
    monkeypatch.delenv("MEMORY_BACKFILL_CHECKPOINT", raising=False)


async def _clear_all_rows() -> None:
    # 回填是全表扫描（无 tenant 谓词），计数断言需全表确定性；
    # 安全前提 = conftest _assert_test_database 强制 *_test 库。
    async with AsyncSessionLocal() as session, session.begin():
        await session.execute(text("DELETE FROM ops_memory_facts"))


@pytest.fixture(autouse=True)
async def _clean():
    await _clear_all_rows()
    yield
    await _clear_all_rows()


def _candidate(**over) -> FactCandidate:
    base = {
        "tenant_id": _TENANT,
        "user_id": "u-" + uuid.uuid4().hex[:8],
        "key": "project.primary_repo",
        "value": "cyning/ops-desk",
    }
    base.update(over)
    return FactCandidate(**base)


async def _write_null(user: str, key: str, value: str):
    """开关关写入 → embedding 留 NULL（模拟 P0 存量行）。"""
    return await write_fact(_candidate(user_id=user, key=key, value=value))


async def _set_status(fact_id, status: str) -> None:
    async with AsyncSessionLocal() as session, session.begin():
        await session.execute(
            text("UPDATE ops_memory_facts SET status = :s WHERE id = :i"),
            {"s": status, "i": str(fact_id)},
        )


async def _embedding_of(fact_id):
    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            text("SELECT embedding FROM ops_memory_facts WHERE id = :i"),
            {"i": str(fact_id)},
        )
        return rows.scalar()


async def _remaining_null_active() -> int:
    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            text(
                "SELECT count(*) FROM ops_memory_facts "
                "WHERE embedding IS NULL AND status = 'active'"
            )
        )
        return int(rows.scalar() or 0)


async def _pin_updated_at(fact_id, ts) -> None:
    async with AsyncSessionLocal() as session, session.begin():
        await session.execute(
            text("UPDATE ops_memory_facts SET updated_at = :ts WHERE id = :i"),
            {"ts": ts, "i": str(fact_id)},
        )


def _sync_execute(sql: str, params: tuple) -> None:
    """to_thread 工作线程内的同步 DB 操作（竞态/并发写模拟；psycopg 直连）。"""
    import psycopg

    url = settings.database_url.replace("+asyncpg", "")  # psycopg 直连 URI
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(sql, params)


def _run(fake: RecordingFakeEmbedder, tmp_path, **kw):
    return run_backfill(
        embedder=fake,
        batch_size=kw.pop("batch_size", 8),
        sleep_ms=0,
        checkpoint_path=None,
        report_dir=tmp_path,
        **kw,
    )


# ---------------- D1 · 回填主体 ----------------


async def test_backfill_embeds_only_active_null_rows(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setenv("RAG_EMBED_MODEL", "fake-embedder")
    fake = RecordingFakeEmbedder()
    user = "u-bf1"
    rows = [await _write_null(user, f"project.fact_{i}", f"v{i}") for i in range(3)]
    sup = await _write_null(user, "project.gone_sup", "x")
    await _set_status(sup.id, "superseded")
    rev = await _write_null(user, "project.gone_rev", "x")
    await _set_status(rev.id, "revoked")
    exp = await _write_null(user, "project.gone_exp", "x")
    await _set_status(exp.id, "expired")
    # active 已嵌行（写入时嵌入，用独立 embedder 防污染回填调用记录）
    monkeypatch.setenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", "true")
    done = await write_fact(
        _candidate(user_id=user, key="project.done", value="y"),
        embedder=RecordingFakeEmbedder(),
    )
    monkeypatch.delenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", raising=False)
    before_done = await _embedding_of(done.id)
    assert before_done is not None

    report = await _run(fake, tmp_path)

    assert report.status == "pass"
    assert (report.scanned, report.embedded, report.skipped, report.failed) == (3, 3, 0, 0)
    # embed() 收到文本 == _fact_embed_text(key, value) 逐条一致
    embedded_texts = sorted(t for call in fake.fact_calls for t in call)
    assert embedded_texts == sorted(
        _fact_embed_text(f"project.fact_{i}", f"v{i}") for i in range(3)
    )
    for fact in rows:
        assert await _embedding_of(fact.id) is not None
    # inactive 行零嵌入
    for fact in (sup, rev, exp):
        assert await _embedding_of(fact.id) is None
    # 已嵌行不被触碰
    assert await _embedding_of(done.id) == before_done
    assert "project.done=y" not in embedded_texts
    # 同步 Embedder 经 asyncio.to_thread 卸载（不在事件循环线程执行）
    assert fake.thread_idents
    assert threading.get_ident() not in fake.thread_idents


async def test_write_recheck_race_marks_skipped(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """回填进行中目标行被 supersede（竞态）→ 该行计 skipped，embedding 保持 NULL。"""
    monkeypatch.setenv("RAG_EMBED_MODEL", "fake-embedder")
    user = "u-race"
    target = await _write_null(user, "project.race_target", "x")
    other = await _write_null(user, "project.race_other", "y")
    fake = RecordingFakeEmbedder()

    def flip(text_value: str) -> None:
        # embed 后、回写前把目标行置 superseded（模拟并发状态机流转）
        if "race_target" in text_value:
            _sync_execute(
                "UPDATE ops_memory_facts SET status = 'superseded' WHERE id = %s",
                (str(target.id),),
            )

    fake.on_text = flip
    report = await _run(fake, tmp_path)

    assert report.status == "pass"
    assert (report.scanned, report.embedded, report.skipped, report.failed) == (2, 1, 1, 0)
    assert await _embedding_of(target.id) is None  # 竞态失效行不误嵌
    assert await _embedding_of(other.id) is not None


async def test_preflight_bad_dimension_exit_2(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setenv("RAG_EMBED_MODEL", "fake-embedder")
    row = await _write_null("u-pre-d", "project.dim_bad", "x")
    bad = RecordingFakeEmbedder(dim=512)

    with pytest.raises(BackfillPreflightError):
        await _run(bad, tmp_path)
    assert await _embedding_of(row.id) is None  # 零写入
    assert await _remaining_null_active() == 1


async def test_preflight_name_mismatch_exit_2(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.delenv("RAG_EMBED_MODEL", raising=False)  # 期望默认 BAAI/bge-m3
    row = await _write_null("u-pre-n", "project.name_bad", "x")
    fake = RecordingFakeEmbedder()  # name="fake-embedder" 不符

    with pytest.raises(BackfillPreflightError):
        await _run(fake, tmp_path)
    assert await _embedding_of(row.id) is None


async def test_cli_preflight_failures_exit_2(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """CLI 层（main · 自建引擎 · asyncio.run）：前置校验失败翻译 exit 2，零写入。

    main 经 asyncio.to_thread 调用（工作线程无运行中 loop，可自建 asyncio.run）；
    CLI 引擎独立于 app 全局连接池，不污染 pytest 事件循环。
    """
    import asyncio

    from app.ops.rag.embedder import reset_query_embedder_cache

    # name 不符 → exit 2
    monkeypatch.delenv("RAG_EMBED_MODEL", raising=False)
    rc = await asyncio.to_thread(
        main, ["--report-dir", str(tmp_path)], embedder=RecordingFakeEmbedder()
    )
    assert rc == 2

    # 维度不符（有候选行才试嵌）→ exit 2 且该行保持 NULL
    monkeypatch.setenv("RAG_EMBED_MODEL", "fake-embedder")
    row_id = str(uuid.uuid4())
    _sync_execute(
        "INSERT INTO ops_memory_facts "
        "(id, tenant_id, user_id, key, value, kind, status, created_at, updated_at) "
        "VALUES (%s, %s, %s, %s, %s::jsonb, 'fact', 'active', now(), now())",
        (row_id, _TENANT, "u-cli-dim", "project.cli_dim_bad", '"x"'),
    )
    rc = await asyncio.to_thread(
        main,
        ["--report-dir", str(tmp_path)],
        embedder=RecordingFakeEmbedder(dim=512),
    )
    assert rc == 2
    assert await _embedding_of(row_id) is None  # 零写入

    # SILICONFLOW_API_KEY 缺失 → ApiEmbedder 构造即抛 → exit 2（不静默退 local ST）
    monkeypatch.delenv("SILICONFLOW_API_KEY", raising=False)
    monkeypatch.setenv("RAG_EMBED_BACKEND", "siliconflow")
    reset_query_embedder_cache()
    rc = await asyncio.to_thread(main, ["--dry-run", "--report-dir", str(tmp_path)])
    assert rc == 2
    reset_query_embedder_cache()


async def test_keyset_pagination_strictly_increasing(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setenv("RAG_EMBED_MODEL", "fake-embedder")
    user = "u-keyset"
    rows = [await _write_null(user, f"project.page_{i}", f"v{i}") for i in range(5)]
    id_by_key = {f"project.page_{i}": str(r.id) for i, r in enumerate(rows)}
    fake = RecordingFakeEmbedder()

    report = await _run(fake, tmp_path, batch_size=2)

    assert report.embedded == 5
    pages = fake.fact_calls
    assert [len(p) for p in pages] == [2, 2, 1]  # 3 页
    paged_ids = [id_by_key[t.split("=", 1)[0]] for call in pages for t in call]
    assert len(set(paged_ids)) == 5  # 无重复
    assert paged_ids == sorted(paged_ids)  # id ASC 严格递增（跨页同序）


# ---------------- D2 · 幂等/续跑/报告 ----------------


async def test_idempotent_second_run_zero_embed_calls(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setenv("RAG_EMBED_MODEL", "fake-embedder")
    user = "u-idem"
    for i in range(3):
        await _write_null(user, f"project.idem_{i}", f"v{i}")
    fake1 = RecordingFakeEmbedder()
    r1 = await _run(fake1, tmp_path)
    assert (r1.scanned, r1.embedded) == (3, 3)

    fake2 = RecordingFakeEmbedder()
    r2 = await _run(fake2, tmp_path)
    assert (r2.scanned, r2.embedded, r2.skipped, r2.failed) == (0, 0, 0, 0)
    assert fake2.calls == []  # 零嵌入调用（含前置试嵌：零候选跳过）
    # 每条 fact 文本全程只嵌一次
    texts = [t for call in fake1.fact_calls for t in call]
    assert len(texts) == len(set(texts)) == 3


async def test_resume_after_consecutive_page_failures(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """第 1 页成功后连续 3 页全败 → 终止（status=failed）；重跑补齐且不重复嵌入。"""
    monkeypatch.setenv("RAG_EMBED_MODEL", "fake-embedder")
    user = "u-resume"
    rows = [await _write_null(user, f"project.resume_{i}", f"v{i}") for i in range(8)]
    fake1 = RecordingFakeEmbedder()
    fake1.fail_on_fact_calls = {1, 2, 3}  # 页 2/3/4 全败
    r1 = await _run(fake1, tmp_path, batch_size=2)
    assert r1.status == "failed"
    assert (r1.scanned, r1.embedded, r1.failed) == (8, 2, 6)
    page1_texts = set(fake1.fact_calls[0])
    assert len(r1.failed_ids) == 6

    fake2 = RecordingFakeEmbedder()
    r2 = await _run(fake2, tmp_path, batch_size=2)
    assert r2.status == "pass"
    assert (r2.scanned, r2.embedded, r2.failed) == (6, 6, 0)
    rerun_texts = {t for call in fake2.fact_calls for t in call}
    assert rerun_texts.isdisjoint(page1_texts)  # 第 1 页行不重复嵌入
    for fact in rows:
        assert await _embedding_of(fact.id) is not None


async def test_partial_page_failure_counts_and_rerun_heals(
    monkeypatch: pytest.MonkeyPatch, tmp_path
):
    monkeypatch.setenv("RAG_EMBED_MODEL", "fake-embedder")
    user = "u-partial"
    rows = [await _write_null(user, f"project.part_{i}", f"v{i}") for i in range(4)]
    sorted_ids = sorted(str(r.id) for r in rows)
    fake1 = RecordingFakeEmbedder()
    fake1.fail_on_fact_calls = {1}  # 仅第 2 页抛 httpx.HTTPError
    r1 = await _run(fake1, tmp_path, batch_size=2)
    assert r1.status == "partial"
    assert (r1.embedded, r1.failed) == (2, 2)
    assert set(r1.failed_ids) == set(sorted_ids[2:4])  # failed_ids 含第 2 页 id
    assert r1.remaining_null_active == 2  # 对账：剩余 == failed

    fake2 = RecordingFakeEmbedder()
    r2 = await _run(fake2, tmp_path, batch_size=2)
    assert r2.status == "pass"
    assert (r2.embedded, r2.failed) == (2, 0)  # 重跑后 failed 清零
    assert await _remaining_null_active() == 0


async def test_report_yaml_shape_and_conservation(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setenv("RAG_EMBED_MODEL", "fake-embedder")
    user = "u-report"
    await _write_null(user, "project.rep_0", "v0")
    await _write_null(user, "project.rep_1", "v1")
    gone = await _write_null(user, "project.rep_gone", "x")
    await _set_status(gone.id, "revoked")
    fake = RecordingFakeEmbedder()

    report = await _run(fake, tmp_path)
    assert report.embedded + report.skipped + report.failed == report.scanned

    files = list(tmp_path.glob("backfill_*.yaml"))
    assert len(files) == 1
    data = yaml.safe_load(files[0].read_text(encoding="utf-8"))
    required = {
        "status",
        "dry_run",
        "scanned",
        "embedded",
        "skipped",
        "failed",
        "failed_ids",
        "embedder_name",
        "batch_size",
        "sleep_ms",
        "remaining_null_active",
        "elapsed_s",
        "recorded_at",
    }
    assert required <= set(data)
    assert data["status"] == "pass"
    assert data["dry_run"] is False
    assert data["embedder_name"] == "fake-embedder"
    assert data["embedded"] + data["skipped"] + data["failed"] == data["scanned"]
    assert data["remaining_null_active"] == 0
    assert data["elapsed_s"] >= 0
    datetime.fromisoformat(data["recorded_at"])  # ISO 时间戳可解析


def test_env_invalid_fallback_with_warning(monkeypatch: pytest.MonkeyPatch, caplog, tmp_path):
    logger_name = "scripts.memory_embedding_backfill"
    monkeypatch.delenv("MEMORY_BACKFILL_BATCH_SIZE", raising=False)
    assert backfill_batch_size() == 32
    with caplog.at_level(logging.WARNING, logger=logger_name):
        monkeypatch.setenv("MEMORY_BACKFILL_BATCH_SIZE", "abc")
        assert backfill_batch_size() == 32
        monkeypatch.setenv("MEMORY_BACKFILL_BATCH_SIZE", "0")
        assert backfill_batch_size() == 32
    assert "MEMORY_BACKFILL_BATCH_SIZE" in caplog.text
    monkeypatch.setenv("MEMORY_BACKFILL_BATCH_SIZE", "4")
    assert backfill_batch_size() == 4

    monkeypatch.delenv("MEMORY_BACKFILL_SLEEP_MS", raising=False)
    assert backfill_sleep_ms() == 200
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger=logger_name):
        monkeypatch.setenv("MEMORY_BACKFILL_SLEEP_MS", "abc")
        assert backfill_sleep_ms() == 200
        monkeypatch.setenv("MEMORY_BACKFILL_SLEEP_MS", "-1")
        assert backfill_sleep_ms() == 200
    assert "MEMORY_BACKFILL_SLEEP_MS" in caplog.text
    monkeypatch.setenv("MEMORY_BACKFILL_SLEEP_MS", "0")
    assert backfill_sleep_ms() == 0

    # checkpoint env 指向目录 = 非法 → 回退禁用 + warning
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger=logger_name):
        monkeypatch.setenv("MEMORY_BACKFILL_CHECKPOINT", str(tmp_path))
        assert backfill_checkpoint_path() is None
    assert "MEMORY_BACKFILL_CHECKPOINT" in caplog.text
    # checkpoint 文件损坏 → 从头重扫（None）+ warning
    bad = tmp_path / "checkpoint.json"
    bad.write_text("not-json{", encoding="utf-8")
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger=logger_name):
        assert _read_checkpoint(bad) is None
    assert "corrupt checkpoint" in caplog.text


async def test_dry_run_zero_embed_zero_write(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setenv("RAG_EMBED_MODEL", "fake-embedder")
    user = "u-dry"
    rows = [await _write_null(user, f"project.dry_{i}", f"v{i}") for i in range(3)]
    fake = RecordingFakeEmbedder()

    report = await _run(fake, tmp_path, dry_run=True)

    assert report.dry_run is True
    assert report.status == "pass"
    assert (report.scanned, report.embedded, report.skipped, report.failed) == (3, 0, 0, 0)
    assert fake.calls == []  # 零嵌入调用（含前置试嵌）
    for fact in rows:
        assert await _embedding_of(fact.id) is None  # 零写库
    data = yaml.safe_load(next(tmp_path.glob("backfill_*.yaml")).read_text(encoding="utf-8"))
    assert data["dry_run"] is True


# ---------------- D4 · 对账与金样对照（态② FakeEmbedder 集成夹具轨） ----------------


async def test_dry_run_matches_real_run_scanned(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """同库序 dry-run scanned == 实跑 scanned；实跑后重扫剩余 == failed。"""
    monkeypatch.setenv("RAG_EMBED_MODEL", "fake-embedder")
    user = "u-recon"
    for i in range(4):
        await _write_null(user, f"project.recon_{i}", f"v{i}")

    dry = await _run(RecordingFakeEmbedder(), tmp_path, dry_run=True)
    real = await _run(RecordingFakeEmbedder(), tmp_path)

    assert dry.scanned == real.scanned == 4
    assert real.status == "pass"
    assert real.remaining_null_active == real.failed == 0
    assert await _remaining_null_active() == real.failed


async def test_reconcile_mismatch_marks_failed(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """实跑期间并发写入新 NULL 行 → 重扫剩余 != failed → status failed（不伪装成功）。"""
    monkeypatch.setenv("RAG_EMBED_MODEL", "fake-embedder")
    user = "u-mismatch"
    await _write_null(user, "project.mm_0", "v0")
    await _write_null(user, "project.mm_1", "v1")
    fake = RecordingFakeEmbedder()
    inserted = {"done": False}

    def concurrent_write(text_value: str) -> None:
        if text_value == PREFLIGHT_PROBE_TEXT or inserted["done"]:
            return
        inserted["done"] = True
        # test-baseline-reds D3：注入行用确定性小 id，恒落在 keyset 水位前，
        # 消除「uuid4 随机落点 × id > last_id 翻页」竞态（约 40% 翻车）。
        # PG uuid 按字节序比较：v4 uuid 第 6 字节高位必为 0x4_，而
        # UUID(int=1) 前 15 字节全 0 → 恒小于任何 v4 uuid（两个种子行 id 均 v4），
        # 下一页 id > last_id 永远扫不到它 → remaining=1 / embedded=2 恒成立。
        _sync_execute(
            "INSERT INTO ops_memory_facts "
            "(id, tenant_id, user_id, key, value, kind, status, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s::jsonb, 'fact', 'active', now(), now())",
            (
                str(uuid.UUID(int=1)),
                _TENANT,
                user,
                "project.concurrent_fact",
                '"surprise"',
            ),
        )

    fake.on_text = concurrent_write
    report = await _run(fake, tmp_path)

    assert inserted["done"] is True
    assert report.embedded == 2 and report.failed == 0
    assert report.status == "failed"  # 对账不等：剩余 1 != failed 0
    assert report.remaining_null_active == 1


async def test_paraphrase_recall_before_after_backfill(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """金样轨态②：存量 NULL 行回填前向量通路不可达（top1 不命中）/ 回填后 top1 命中。"""
    monkeypatch.setenv("RAG_EMBED_MODEL", "fake-embedder")
    fake = RecordingFakeEmbedder()
    user = "u-golden"
    target = await _write_null(user, "project.primary_repo", "cyning/ops-desk")
    d1 = await _write_null(user, "project.favorite_color", "blue")
    d2 = await _write_null(user, "project.favorite_editor", "vim")
    # 钉死 updated_at：target 最旧 → 确定性 top-2 只有 d1/d2
    base = now_utc()
    await _pin_updated_at(target.id, base)
    await _pin_updated_at(d1.id, base + timedelta(seconds=1))
    await _pin_updated_at(d2.id, base + timedelta(seconds=2))

    monkeypatch.setenv("MEMORY_FACTS_VECTOR_RECALL_ENABLED", "true")
    # 回填前基线：复述 query 经混合召回，存量 NULL 行进不了向量 top-M，top1 不命中
    pre = await recall_with_vector(_TENANT, user, "我主要负责哪个仓库", limit=2, embedder=fake)
    assert pre[0].key == "project.favorite_editor"
    assert all(str(f.id) != str(target.id) for f in pre[:1])

    report = await _run(fake, tmp_path)
    assert report.status == "pass" and report.embedded == 3

    # 回填后：向量通路捞回存量行，top1 命中
    post = await recall_with_vector(_TENANT, user, "我主要负责哪个仓库", limit=2, embedder=fake)
    assert post[0].key == "project.primary_repo"
    assert str(post[0].id) == str(target.id)
