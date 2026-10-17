#!/usr/bin/env python3
"""生产向量水位/对账核查（只读 · task prod-vector-waterline-check E1/E2）。

只读硬约束（FP-5 / TC-WL-6）：本脚本对 PG 只发 SELECT；对 Qdrant 只用
count / scroll 读 API（禁 upsert/delete/create_collection 等一切写 API）。
无任何 INSERT/UPDATE/DELETE/DDL。

三断面（路线 §P1-RAG「生产向量水位与对账 待人工」缺口）：
1. 对账：Qdrant ops_knowledge points count vs PG ops_knowledge_chunks 行数，
   含差集方向（PG 有 Qdrant 无 / Qdrant 有 PG 无）计数 + 抽样。
2. DLQ：ops_qdrant_dlq 深度与最老条目年龄。
3. ingest 水位：max(ops_knowledge_chunks.embedded_at)
   （表无 created_at/updated_at，口径按表结构实定为 embedded_at，
   alembic/versions/20260808_rag_chunks.py:46）。

降级三态（E2 · 显式失败不冒充）：
- Qdrant 不可达/凭证缺失 → PG 单侧水位 + 报告标注「Qdrant 面无实证」（含原因），exit 0。
- PG 不可达 → Qdrant 单侧 + 标注「PG 面无实证」，exit 0。
- 双侧均不可达 → 非零退出（exit 2）+ stderr 显式错误，不出半份冒充报告。

用法：
    DATABASE_URL=postgresql+psycopg://<ro_user>:<pass>@<host>:5432/opsdesk \
    QDRANT_URL=http://<host>:6333 QDRANT_API_KEY=<key> \
    python scripts/check_vector_waterline.py --env prod

报告落 reports/vector_waterline_<env>_<UTCts>.yaml（模板：
reports/vector_waterline_TEMPLATE.yaml）。生产执行属维护者动作
（HG-PROD-READONLY-ACCESS）；本脚本只出证据，差集处置另 task（FP-6）。
"""
from __future__ import annotations

import argparse
import getpass
import os
import subprocess
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import yaml
from sqlalchemy import create_engine, text

try:  # 本地开发便利：.env 可选加载；生产用显式 env 注入
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv 缺失不阻塞
    pass

# ---- 只读 SQL（全部 SELECT；FP-5 桩测断言本清单无写语句） ----
SQL_PG_COUNT = "SELECT count(*) FROM ops_knowledge_chunks"
SQL_PG_WATERLINE = "SELECT max(embedded_at) FROM ops_knowledge_chunks"
SQL_PG_IDS = "SELECT id FROM ops_knowledge_chunks ORDER BY id"
SQL_PG_DLQ = "SELECT count(*) AS depth, min(created_at) AS oldest FROM ops_qdrant_dlq"

DEFAULT_QDRANT_URL = "http://127.0.0.1:6333"
DEFAULT_COLLECTION = "ops_knowledge"
DEFAULT_SAMPLE_LIMIT = 20
SCROLL_BATCH = 1000

EXIT_OK = 0
EXIT_BOTH_UNREACHABLE = 2


@dataclass
class FaceResult:
    """单侧采集结果；status=no_evidence 时 reason 必填（降级不冒充）。"""

    status: str  # "ok" | "no_evidence"
    face: dict[str, Any] = field(default_factory=dict)
    ids: set[int] = field(default_factory=set)
    reason: str = ""


def _iso(value: Any) -> str | None:
    """datetime → ISO 字符串；None/其它原样语义化。"""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.isoformat()
    return str(value)


def collect_pg_face(conn: Any, *, now: datetime) -> FaceResult:
    """PG 面：行数 + ingest 水位 + DLQ 深度/最老年龄 + 全量 id 集（只读 SELECT）。

    conn 为 SQLAlchemy Connection 语义（execute(text(sql))）；测试注入 fake。
    """
    row_count = int(conn.execute(text(SQL_PG_COUNT)).scalar_one())
    waterline = conn.execute(text(SQL_PG_WATERLINE)).scalar_one()
    ids = {int(r[0]) for r in conn.execute(text(SQL_PG_IDS)).all()}
    dlq_row = conn.execute(text(SQL_PG_DLQ)).one()
    depth = int(dlq_row.depth)
    oldest = dlq_row.oldest
    oldest_age: float | None = None
    if oldest is not None:
        if oldest.tzinfo is None:
            oldest = oldest.replace(tzinfo=UTC)
        oldest_age = max(0.0, (now - oldest).total_seconds())
    face = {
        "status": "ok",
        "row_count": row_count,
        "ingest_waterline": {
            "column": "ops_knowledge_chunks.embedded_at",
            "max": _iso(waterline),
        },
        "dlq": {
            "table": "ops_qdrant_dlq",
            "depth": depth,
            "oldest_created_at": _iso(oldest),
            "oldest_age_seconds": round(oldest_age, 3) if oldest_age is not None else None,
            "verdict": ("empty" if depth == 0 else "backlogged"),
        },
    }
    return FaceResult(status="ok", face=face, ids=ids)


def collect_qdrant_face(client: Any, *, collection: str) -> FaceResult:
    """Qdrant 面：points count + 全量 id 集（只用 count/scroll 读 API）。

    scroll 全程 with_payload=False, with_vectors=False（只取 id，零数据搬运）。
    测试注入桩客户端；桩上的写方法调用由 E5 断言为零。
    """
    count = int(client.count(collection_name=collection, exact=True).count)
    ids: set[int] = set()
    offset: Any = None
    while True:
        points, offset = client.scroll(
            collection_name=collection,
            limit=SCROLL_BATCH,
            offset=offset,
            with_payload=False,
            with_vectors=False,
        )
        ids.update(int(p.id) for p in points)
        if offset is None:
            break
    face = {
        "status": "ok",
        "collection": collection,
        "points_count": count,
        "scrolled_ids": len(ids),
    }
    return FaceResult(status="ok", face=face, ids=ids)


def reconcile(
    pg: FaceResult,
    qdrant: FaceResult,
    *,
    sample_limit: int = DEFAULT_SAMPLE_LIMIT,
) -> dict[str, Any]:
    """对账：计数差 + 双向差集（计数 + 抽样）。单侧无实证则 skipped 不冒充。"""
    if pg.status != "ok":
        return {"status": "skipped", "reason": "PG 面无实证，对账跳过"}
    if qdrant.status != "ok":
        return {"status": "skipped", "reason": "Qdrant 面无实证，对账跳过"}
    pg_count = pg.face["row_count"]
    q_count = qdrant.face["points_count"]
    pg_only = sorted(pg.ids - qdrant.ids, key=str)
    qdrant_only = sorted(qdrant.ids - pg.ids, key=str)
    return {
        "status": "ok",
        "pg_count": pg_count,
        "qdrant_count": q_count,
        "count_diff": pg_count - q_count,
        "verdict": ("match" if not pg_only and not qdrant_only else "mismatch"),
        "pg_only_in_qdrant_missing": {
            "count": len(pg_only),
            "sample": pg_only[:sample_limit],
        },
        "qdrant_only_in_pg_missing": {
            "count": len(qdrant_only),
            "sample": qdrant_only[:sample_limit],
        },
        "note": "差集只记录不处置（FP-6）；处置动作另 task。",
    }


def _redact_url(url: str) -> str:
    """报告只留 host:port 语义，剥离可能内嵌的 user:pass。"""
    try:
        parts = urlsplit(url)
        host = parts.hostname or ""
        port = f":{parts.port}" if parts.port else ""
        return urlunsplit((parts.scheme, host + port, parts.path, "", ""))
    except Exception:
        return "<unparseable>"


def _git_sha() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True, timeout=10
        ).strip()
        return out or None
    except Exception:
        return None


@contextmanager
def _default_pg_connect(database_url: str) -> Iterator[Any]:
    """真实 PG 只读连接（psycopg 同步驱动；connect() 不开写事务）。"""
    sync_url = database_url.replace("+asyncpg", "+psycopg")
    engine = create_engine(sync_url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            yield conn
    finally:
        engine.dispose()


def _default_qdrant_client(*, url: str, api_key: str | None, timeout: float) -> Any:
    from qdrant_client import QdrantClient

    return QdrantClient(url=url, api_key=api_key, timeout=timeout)


def _no_evidence(face_name: str, reason: str) -> FaceResult:
    return FaceResult(
        status="no_evidence",
        face={"status": "no_evidence", "reason": reason},
        reason=f"{face_name} 面无实证：{reason}",
    )


def build_report(
    *,
    env: str,
    now: datetime,
    pg: FaceResult,
    qdrant: FaceResult,
    rec: dict[str, Any],
    qdrant_url: str,
    collection: str,
    database_url_set: bool,
) -> dict[str, Any]:
    degraded_notes = [r.reason for r in (pg, qdrant) if r.status != "ok"]
    report = {
        "kind": "vector_waterline",
        "template_version": "v1",
        "recorded_at": _iso(now),
        "environment": env,
        "executed_by": getpass.getuser(),
        "git_sha": _git_sha(),
        "config": {
            "database_url_set": database_url_set,
            "qdrant_url": _redact_url(qdrant_url),
            "qdrant_collection": collection,
        },
        "status": ("degraded" if degraded_notes else "ok"),
        "pg_face": pg.face,
        "qdrant_face": qdrant.face,
        "reconcile": rec,
        "degradation": {
            "degraded": bool(degraded_notes),
            "notes": degraded_notes,
        },
        "disclaimer": (
            "本报告为只读核查证据；差集/DLQ 处置动作另 task（FP-6）。"
            "本地/compose 环境产物不得当作生产证据（TC-WL-5 与 TC-WL-8 分离）。"
        ),
    }
    return report


def write_report(report: dict[str, Any], *, report_dir: Path, env: str, now: datetime) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    ts = now.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = report_dir / f"vector_waterline_{env}_{ts}.yaml"
    path.write_text(
        yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    return path


def main(
    argv: list[str] | None = None,
    *,
    pg_connect: Callable[[str], Any] | None = None,
    qdrant_factory: Callable[..., Any] | None = None,
    now: datetime | None = None,
) -> int:
    parser = argparse.ArgumentParser(description="向量水位/对账只读核查（prod-vector-waterline-check）")
    parser.add_argument("--env", default="local", help="环境标识（local/prod/...），入报告与文件名")
    parser.add_argument("--sample-limit", type=int, default=DEFAULT_SAMPLE_LIMIT, help="差集抽样上限")
    parser.add_argument("--report-dir", type=Path, default=Path("reports"), help="报告落盘目录")
    parser.add_argument("--timeout", type=float, default=10.0, help="Qdrant 客户端超时秒")
    args = parser.parse_args(argv)

    now = now or datetime.now(UTC)
    connect = pg_connect or _default_pg_connect
    q_factory = qdrant_factory or _default_qdrant_client

    database_url = (os.environ.get("WATERLINE_DATABASE_URL") or os.environ.get("DATABASE_URL") or "").strip()
    qdrant_url = (os.environ.get("QDRANT_URL") or DEFAULT_QDRANT_URL).strip()
    collection = (os.environ.get("QDRANT_COLLECTION") or DEFAULT_COLLECTION).strip() or DEFAULT_COLLECTION
    api_key = (os.environ.get("QDRANT_API_KEY") or "").strip() or None

    # ---- PG 面（不可达/凭证缺失 → 降级标注，不冒充） ----
    if not database_url:
        pg = _no_evidence("PG", "WATERLINE_DATABASE_URL/DATABASE_URL 均未配置")
    else:
        try:
            with connect(database_url) as conn:
                pg = collect_pg_face(conn, now=now)
        except Exception as exc:
            pg = _no_evidence("PG", f"{type(exc).__name__}: {exc}")

    # ---- Qdrant 面（不可达/凭证缺失 → 降级标注，不冒充） ----
    try:
        client = q_factory(url=qdrant_url, api_key=api_key, timeout=args.timeout)
        qdrant = collect_qdrant_face(client, collection=collection)
    except Exception as exc:
        qdrant = _no_evidence("Qdrant", f"{type(exc).__name__}: {exc}")

    # ---- 双侧均无实证：非零退出 + 显式错误，不出半份冒充报告（FP-4） ----
    if pg.status != "ok" and qdrant.status != "ok":
        print(
            "ERROR: PG 与 Qdrant 双侧均无实证，核查失败（不出报告）。\n"
            f"  PG: {pg.reason}\n"
            f"  Qdrant: {qdrant.reason}",
            file=sys.stderr,
        )
        return EXIT_BOTH_UNREACHABLE

    rec = reconcile(pg, qdrant, sample_limit=args.sample_limit)
    report = build_report(
        env=args.env,
        now=now,
        pg=pg,
        qdrant=qdrant,
        rec=rec,
        qdrant_url=qdrant_url,
        collection=collection,
        database_url_set=bool(database_url),
    )
    path = write_report(report, report_dir=args.report_dir, env=args.env, now=now)

    print(f"报告: {path}")
    print(f"status: {report['status']}")
    if pg.status == "ok":
        print(f"PG 行数: {pg.face['row_count']} · ingest 水位: {pg.face['ingest_waterline']['max']}")
        dlq = pg.face["dlq"]
        print(f"DLQ 深度: {dlq['depth']} · 最老年龄(s): {dlq['oldest_age_seconds']}")
    if qdrant.status == "ok":
        print(f"Qdrant[{collection}] points: {qdrant.face['points_count']}")
    if rec.get("status") == "ok":
        print(
            f"对账: diff={rec['count_diff']} · PG独有={rec['pg_only_in_qdrant_missing']['count']}"
            f" · Qdrant独有={rec['qdrant_only_in_pg_missing']['count']} · verdict={rec['verdict']}"
        )
    for note in report["degradation"]["notes"]:
        print(f"降级标注: {note}", file=sys.stderr)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
