#!/usr/bin/env python3
"""HNSW 压测骨架（P1）：同机对照 pgvector / Qdrant。

本机未跑通真实 80 万灌库时：脚本具备 CLI，实测记录写「未在本机跑通原因」。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Bench HNSW (pgvector baseline + qdrant)")
    parser.add_argument("--n-queries", type=int, default=200)
    parser.add_argument("--baseline", default="pgvector", choices=["pgvector", "none"])
    parser.add_argument("--compare-with", default="reports/r4-2.yaml")
    parser.add_argument("--outs", default="reports/qdrant_bench.yaml")
    parser.add_argument("--qdrant-url", default="http://127.0.0.1:6333")
    parser.add_argument("--collection", default="ops_knowledge")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--skip-live", action="store_true", help="只写占位报告，不连库")
    args = parser.parse_args()

    note = ""
    pg_p95 = None
    qd_p95 = None
    status = "skipped"

    if args.skip_live:
        note = "未在本机跑通原因：--skip-live；维护者环境无生产盘/无全量语料时仅校验脚本入口"
        status = "skipped"
    else:
        try:
            from sqlalchemy import create_engine, text

            from app.config import settings

            db_url = settings.database_url.replace("+asyncpg", "+psycopg")
            engine = create_engine(db_url)
            with engine.connect() as conn:
                n = int(
                    conn.execute(text("SELECT count(*) FROM ops_knowledge_chunks")).scalar_one()
                )
                if n == 0:
                    raise RuntimeError("ops_knowledge_chunks empty")
                rows = conn.execute(
                    text(
                        "SELECT embedding FROM ops_knowledge_chunks "
                        "ORDER BY id LIMIT :n"
                    ),
                    {"n": min(args.n_queries, n)},
                ).all()
            vectors = []
            for (emb,) in rows:
                if hasattr(emb, "tolist"):
                    emb = emb.tolist()
                elif isinstance(emb, str):
                    emb = json.loads(emb)
                vectors.append(list(emb))

            if args.baseline == "pgvector":
                lat = []
                with engine.connect() as conn:
                    for v in vectors:
                        t0 = time.perf_counter()
                        conn.execute(
                            text(
                                "SELECT id FROM ops_knowledge_chunks "
                                "ORDER BY embedding <=> CAST(:q AS vector) LIMIT :k"
                            ),
                            {"q": json.dumps(v), "k": args.top_k},
                        ).all()
                        lat.append((time.perf_counter() - t0) * 1000)
                lat.sort()
                pg_p95 = lat[int(0.95 * (len(lat) - 1))] if lat else None

            from qdrant_client import QdrantClient

            client = QdrantClient(url=args.qdrant_url)
            lat_q = []
            for v in vectors:
                t0 = time.perf_counter()
                client.search(
                    collection_name=args.collection,
                    query_vector=v,
                    limit=args.top_k,
                )
                lat_q.append((time.perf_counter() - t0) * 1000)
            lat_q.sort()
            qd_p95 = lat_q[int(0.95 * (len(lat_q) - 1))] if lat_q else None
            status = "measured"
            note = f"n_queries={len(vectors)} compare_with={args.compare_with}"
        except Exception as exc:
            status = "skipped"
            note = f"未在本机跑通原因：{exc}"

    report = {
        "status": status,
        "baseline": args.baseline,
        "compare_with": args.compare_with,
        "pgvector_search_p95_ms": pg_p95,
        "qdrant_search_p95_ms": qd_p95,
        "p95_budget_ms": 150,
        "note": note,
        "recorded_at": datetime.now(UTC).isoformat(),
        "rerank_enabled_required": False,
    }
    out = Path(args.outs)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for k, v in report.items():
        if isinstance(v, str):
            lines.append(f'{k}: "{v}"')
        else:
            lines.append(f"{k}: {v}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
