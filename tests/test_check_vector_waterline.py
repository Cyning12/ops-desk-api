"""tests for scripts/check_vector_waterline.py（task prod-vector-waterline-check E5）。

桩 Qdrant 客户端 + fake PG 会话，不连真库（CI 确定性）：
- 双侧面聚合断言（行数/count/DLQ/水位聚合进报告）
- 差集方向断言（PG 有 Qdrant 无 / Qdrant 有 PG 无 · 计数+抽样）
- 降级三态断言（Qdrant 不可达→PG 单侧+标注 · PG 不可达→Qdrant 单侧+标注 ·
  双不可达→非零退出+stderr 显式错误 · 含子进程命令输出断言）
- 只读断言（桩客户端写方法零调用 + fake PG 全部 SQL 均为 SELECT）
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import yaml

from scripts.check_vector_waterline import (
    EXIT_BOTH_UNREACHABLE,
    EXIT_OK,
    SQL_PG_COUNT,
    SQL_PG_DLQ,
    SQL_PG_IDS,
    SQL_PG_WATERLINE,
    FaceResult,
    collect_pg_face,
    collect_qdrant_face,
    main,
    reconcile,
)

NOW = datetime(2026, 10, 17, 12, 0, 0, tzinfo=UTC)
DLQ_OLDEST = datetime(2026, 10, 17, 10, 30, 0, tzinfo=UTC)  # 距 NOW 5400 秒


class _FakeResult:
    """SQLAlchemy Result 最小语义：scalar_one / all / one。"""

    def __init__(self, rows):
        self._rows = rows

    def scalar_one(self):
        return self._rows[0][0]

    def all(self):
        return self._rows

    def one(self):
        return self._rows[0]


class FakePgConn:
    """按 SQL 常量分发罐头数据；记录全部 SQL 供只读断言。"""

    def __init__(self, *, row_count: int, waterline, ids: set[int], dlq: tuple[int, object]):
        self.row_count = row_count
        self.waterline = waterline
        self.ids = sorted(ids)
        self.dlq = dlq
        self.sql_log: list[str] = []

    def execute(self, stmt, params=None):
        sql = str(stmt).strip()
        self.sql_log.append(sql)
        if sql == SQL_PG_COUNT:
            return _FakeResult([(self.row_count,)])
        if sql == SQL_PG_WATERLINE:
            return _FakeResult([(self.waterline,)])
        if sql == SQL_PG_IDS:
            return _FakeResult([(i,) for i in self.ids])
        if sql == SQL_PG_DLQ:
            depth, oldest = self.dlq
            return _FakeResult([SimpleNamespace(depth=depth, oldest=oldest)])
        raise AssertionError(f"unexpected SQL: {sql}")


class StubQdrantClient:
    """count/scroll 桩；写方法全部入账（E5 断言零写调用）。"""

    WRITE_METHODS = (
        "upsert",
        "delete",
        "create_collection",
        "delete_collection",
        "update_collection",
    )

    def __init__(self, ids: set[int], *, page_size: int = 2):
        self._ids = sorted(ids)
        self._page_size = page_size
        self.write_calls: list[tuple] = []
        for name in self.WRITE_METHODS:
            setattr(self, name, self._record_write(name))

    def _record_write(self, name: str):
        def _w(*args, **kwargs):
            self.write_calls.append((name, args, kwargs))

        return _w

    def count(self, *, collection_name: str, exact: bool = True):
        assert exact is True
        return SimpleNamespace(count=len(self._ids))

    def scroll(self, *, collection_name: str, limit: int, offset, with_payload, with_vectors):
        assert with_payload is False and with_vectors is False  # 只取 id，零数据搬运
        start = 0 if offset is None else int(offset)
        page = self._ids[start : start + self._page_size]
        points = [SimpleNamespace(id=i) for i in page]
        next_offset = start + self._page_size if start + self._page_size < len(self._ids) else None
        return points, next_offset


def _fake_connect(conn: FakePgConn):
    """返回 pg_connect 工厂：main 以 with connect(url) as conn 使用。"""

    def _connect(url: str):
        @contextmanager
        def _cm():
            yield conn

        return _cm()

    return _connect


def _run_main(tmp_path: Path, monkeypatch, *, pg_conn=None, qdrant_ids=None, qdrant_exc=None):
    """统一驱动：注入 fake/桩跑 main，返回 (exit_code, 报告 dict 或 None)。"""
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://ro:***@db:5432/opsdesk")
    kwargs = {"now": NOW}
    if pg_conn is not None:
        kwargs["pg_connect"] = _fake_connect(pg_conn)
    if qdrant_exc is not None:

        def _boom(**kw):
            raise qdrant_exc

        kwargs["qdrant_factory"] = _boom
    elif qdrant_ids is not None:
        stub = StubQdrantClient(qdrant_ids)
        kwargs["qdrant_factory"] = lambda **kw: stub
        kwargs["_stub"] = stub  # 调用方取桩断言写调用
    stub = kwargs.pop("_stub", None)
    code = main(["--env", "test", "--report-dir", str(tmp_path)], **kwargs)
    reports = list(tmp_path.glob("vector_waterline_test_*.yaml"))
    report = yaml.safe_load(reports[0].read_text(encoding="utf-8")) if reports else None
    return code, report, stub


# ================= 聚合与对账（双侧 ok） =================


def test_collect_pg_face_aggregates_counts_dlq_waterline():
    conn = FakePgConn(row_count=42, waterline=NOW, ids={1, 2, 3}, dlq=(2, DLQ_OLDEST))
    res = collect_pg_face(conn, now=NOW)
    assert res.status == "ok"
    assert res.face["row_count"] == 42
    assert res.face["ingest_waterline"]["column"] == "ops_knowledge_chunks.embedded_at"
    assert res.face["ingest_waterline"]["max"] == NOW.isoformat()
    dlq = res.face["dlq"]
    assert dlq["depth"] == 2
    assert dlq["oldest_created_at"] == DLQ_OLDEST.isoformat()
    assert dlq["oldest_age_seconds"] == 5400.0
    assert dlq["verdict"] == "backlogged"
    assert res.ids == {1, 2, 3}


def test_collect_pg_face_empty_dlq_and_null_waterline():
    conn = FakePgConn(row_count=0, waterline=None, ids=set(), dlq=(0, None))
    res = collect_pg_face(conn, now=NOW)
    assert res.face["ingest_waterline"]["max"] is None
    assert res.face["dlq"]["depth"] == 0
    assert res.face["dlq"]["oldest_age_seconds"] is None
    assert res.face["dlq"]["verdict"] == "empty"


def test_collect_qdrant_face_scrolls_all_pages():
    stub = StubQdrantClient({1, 2, 3, 4, 5}, page_size=2)
    res = collect_qdrant_face(stub, collection="ops_knowledge")
    assert res.status == "ok"
    assert res.face["points_count"] == 5
    assert res.face["scrolled_ids"] == 5
    assert res.ids == {1, 2, 3, 4, 5}


def test_reconcile_match():
    pg = FaceResult(status="ok", face={"row_count": 3}, ids={1, 2, 3})
    qd = FaceResult(status="ok", face={"points_count": 3}, ids={1, 2, 3})
    rec = reconcile(pg, qd)
    assert rec["verdict"] == "match"
    assert rec["count_diff"] == 0
    assert rec["pg_only_in_qdrant_missing"]["count"] == 0
    assert rec["qdrant_only_in_pg_missing"]["count"] == 0


def test_reconcile_diff_directions_and_samples():
    pg = FaceResult(status="ok", face={"row_count": 3}, ids={1, 2, 3})
    qd = FaceResult(status="ok", face={"points_count": 4}, ids={2, 3, 4, 5})
    rec = reconcile(pg, qd, sample_limit=20)
    assert rec["verdict"] == "mismatch"
    assert rec["count_diff"] == 3 - 4
    assert rec["pg_only_in_qdrant_missing"] == {"count": 1, "sample": [1]}
    assert rec["qdrant_only_in_pg_missing"] == {"count": 2, "sample": [4, 5]}


def test_reconcile_skipped_when_one_face_no_evidence():
    pg = FaceResult(status="no_evidence", reason="PG 面无实证：x")
    qd = FaceResult(status="ok", face={"points_count": 1}, ids={1})
    assert reconcile(pg, qd)["status"] == "skipped"
    pg2 = FaceResult(status="ok", face={"row_count": 1}, ids={1})
    qd2 = FaceResult(status="no_evidence", reason="Qdrant 面无实证：x")
    assert reconcile(pg2, qd2)["status"] == "skipped"


def test_main_both_faces_ok_report_aggregated(tmp_path, monkeypatch):
    conn = FakePgConn(row_count=3, waterline=NOW, ids={1, 2, 3}, dlq=(0, None))
    code, report, stub = _run_main(tmp_path, monkeypatch, pg_conn=conn, qdrant_ids={1, 2, 3})
    assert code == EXIT_OK
    assert report["status"] == "ok"
    assert report["degradation"]["degraded"] is False
    assert report["pg_face"]["row_count"] == 3
    assert report["qdrant_face"]["points_count"] == 3
    assert report["reconcile"]["verdict"] == "match"
    assert report["environment"] == "test"


# ================= 降级三态 =================


def test_degraded_qdrant_unreachable_pg_single_face(tmp_path, monkeypatch):
    conn = FakePgConn(row_count=7, waterline=NOW, ids={1}, dlq=(1, DLQ_OLDEST))
    code, report, _ = _run_main(
        tmp_path, monkeypatch, pg_conn=conn, qdrant_exc=ConnectionError("refused")
    )
    assert code == EXIT_OK  # 单侧降级不失败退出
    assert report["status"] == "degraded"
    assert report["pg_face"]["status"] == "ok"
    assert report["pg_face"]["row_count"] == 7
    assert report["qdrant_face"]["status"] == "no_evidence"
    assert "refused" in report["qdrant_face"]["reason"]
    assert report["reconcile"]["status"] == "skipped"
    assert any("Qdrant 面无实证" in n for n in report["degradation"]["notes"])


def test_degraded_pg_unreachable_qdrant_single_face(tmp_path, monkeypatch):
    """PG 连接抛错 → Qdrant 单侧 + 「PG 面无实证」标注，exit 0。"""
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://ro:***@db:5432/opsdesk")

    def _boom(url: str):
        raise OSError("connection refused")

    stub = StubQdrantClient({9, 10})
    code = main(
        ["--env", "test", "--report-dir", str(tmp_path)],
        pg_connect=_boom,
        qdrant_factory=lambda **kw: stub,
        now=NOW,
    )
    assert code == EXIT_OK
    report = yaml.safe_load(next(tmp_path.glob("*.yaml")).read_text(encoding="utf-8"))
    assert report["status"] == "degraded"
    assert report["qdrant_face"]["status"] == "ok"
    assert report["qdrant_face"]["points_count"] == 2
    assert report["pg_face"]["status"] == "no_evidence"
    assert "connection refused" in report["pg_face"]["reason"]
    assert report["reconcile"]["status"] == "skipped"
    assert any("PG 面无实证" in n for n in report["degradation"]["notes"])


def test_degraded_pg_no_database_url(tmp_path, monkeypatch):
    """PG 凭证缺失（env 未配置）→ Qdrant 单侧 + 「PG 面无实证」标注。"""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("WATERLINE_DATABASE_URL", raising=False)
    stub = StubQdrantClient({9, 10})
    code = main(
        ["--env", "test", "--report-dir", str(tmp_path)],
        qdrant_factory=lambda **kw: stub,
        now=NOW,
    )
    assert code == EXIT_OK
    report = yaml.safe_load(next(tmp_path.glob("*.yaml")).read_text(encoding="utf-8"))
    assert report["status"] == "degraded"
    assert report["pg_face"]["status"] == "no_evidence"
    assert "未配置" in report["pg_face"]["reason"]
    assert report["qdrant_face"]["status"] == "ok"
    assert any("PG 面无实证" in n for n in report["degradation"]["notes"])


def test_both_unreachable_nonzero_exit_no_report(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("WATERLINE_DATABASE_URL", raising=False)
    code = main(
        ["--env", "test", "--report-dir", str(tmp_path)],
        qdrant_factory=_raise(ConnectionError("refused")),
        now=NOW,
    )
    assert code == EXIT_BOTH_UNREACHABLE
    assert list(tmp_path.glob("*.yaml")) == []  # 不出半份冒充报告
    err = capsys.readouterr().err
    assert "双侧均无实证" in err
    assert "PG 面无实证" in err and "Qdrant 面无实证" in err


def _raise(exc):
    def _f(**kw):
        raise exc

    return _f


# ================= 只读断言 =================


def test_readonly_stub_zero_write_calls_and_select_only_sql(tmp_path, monkeypatch):
    conn = FakePgConn(row_count=2, waterline=NOW, ids={1, 2}, dlq=(0, None))
    code, report, stub = _run_main(tmp_path, monkeypatch, pg_conn=conn, qdrant_ids={1, 2})
    assert code == EXIT_OK
    assert stub.write_calls == []  # Qdrant 写 API 零调用
    assert conn.sql_log  # 确实发过 SQL
    for sql in conn.sql_log:
        head = sql.lstrip().split(None, 1)[0].upper()
        assert head == "SELECT", f"非只读 SQL: {sql}"
        for bad in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"):
            # 词边界匹配：避免 created_at 等列名误判为 CREATE
            assert not re.search(rf"\b{bad}\b", sql.upper()), f"非只读 SQL: {sql}"


# ================= 命令行端到端（双不可达 → 非零 + stderr） =================


def test_cli_both_unreachable_exit_2(tmp_path):
    """真跑脚本命令：PG 指 127.0.0.1:1（拒绝），Qdrant 指 127.0.0.1:1（拒绝）。"""
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("DATABASE_URL", "WATERLINE_DATABASE_URL", "QDRANT_API_KEY")
    }
    env["DATABASE_URL"] = "postgresql+psycopg://ro:x@127.0.0.1:1/opsdesk"
    env["QDRANT_URL"] = "http://127.0.0.1:1"
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/check_vector_waterline.py",
            "--env",
            "test",
            "--report-dir",
            str(tmp_path),
            "--timeout",
            "2",
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    assert proc.returncode == EXIT_BOTH_UNREACHABLE
    assert "双侧均无实证" in proc.stderr
    assert list(tmp_path.glob("*.yaml")) == []
