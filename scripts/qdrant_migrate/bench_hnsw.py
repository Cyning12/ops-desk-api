#!/usr/bin/env python3
"""HNSW 压测：Qdrant Top-k P50/P95（可选 pgvector 基线；80 万用 --baseline none）。

client≥1.14 / server 1.19：走 ``query_points`` + ``SearchParams(hnsw_ef)``。
合成库 ``ops_knowledge_scale`` 与现网 ``ops_knowledge`` 对照时写进同一报告。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def _percentile(sorted_ms: list[float], p: float) -> float | None:
    if not sorted_ms:
        return None
    idx = int(p * (len(sorted_ms) - 1))
    return sorted_ms[idx]


def _load_query_vectors(n: int) -> list[list[float]]:
    from sqlalchemy import create_engine, text

    from app.config import settings

    db_url = settings.database_url.replace("+asyncpg", "+psycopg")
    engine = create_engine(db_url)
    with engine.connect() as conn:
        n_db = int(conn.execute(text("SELECT count(*) FROM ops_knowledge_chunks")).scalar_one())
        if n_db == 0:
            raise RuntimeError("ops_knowledge_chunks empty")
        rows = conn.execute(
            text(
                "SELECT embedding FROM ops_knowledge_chunks "
                "ORDER BY id LIMIT :n"
            ),
            {"n": min(n, n_db)},
        ).all()
    vectors: list[list[float]] = []
    for (emb,) in rows:
        if hasattr(emb, "tolist"):
            emb = emb.tolist()
        elif isinstance(emb, str):
            emb = json.loads(emb)
        vectors.append(list(emb))
    return vectors


def _search_latencies_ms(
    client,
    *,
    collection: str,
    vectors: list[list[float]],
    top_k: int,
    hnsw_ef: int,
) -> list[float]:
    from qdrant_client.http import models as qm

    lat: list[float] = []
    for v in vectors:
        t0 = time.perf_counter()
        if hasattr(client, "query_points"):
            client.query_points(
                collection_name=collection,
                query=v,
                limit=top_k,
                with_payload=False,
                with_vectors=False,
                search_params=qm.SearchParams(hnsw_ef=hnsw_ef),
            )
        else:
            client.search(
                collection_name=collection,
                query_vector=v,
                limit=top_k,
                search_params=qm.SearchParams(hnsw_ef=hnsw_ef),
            )
        lat.append((time.perf_counter() - t0) * 1000)
    return lat


def _pg_latencies_ms(vectors: list[list[float]], top_k: int) -> list[float]:
    from sqlalchemy import create_engine, text

    from app.config import settings

    db_url = settings.database_url.replace("+asyncpg", "+psycopg")
    engine = create_engine(db_url)
    lat: list[float] = []
    with engine.connect() as conn:
        for v in vectors:
            t0 = time.perf_counter()
            conn.execute(
                text(
                    "SELECT id FROM ops_knowledge_chunks "
                    "ORDER BY embedding <=> CAST(:q AS vector) LIMIT :k"
                ),
                {"q": json.dumps(v), "k": top_k},
            ).all()
            lat.append((time.perf_counter() - t0) * 1000)
    return lat


def _yaml_dump(report: dict) -> str:
    lines: list[str] = []
    for k, v in report.items():
        if isinstance(v, str):
            lines.append(f'{k}: "{v}"')
        elif isinstance(v, bool):
            lines.append(f"{k}: {str(v).lower()}")
        elif isinstance(v, dict):
            lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
        else:
            lines.append(f"{k}: {v}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Bench HNSW (pgvector baseline + qdrant)")
    parser.add_argument("--n-queries", type=int, default=200)
    parser.add_argument("--baseline", default="pgvector", choices=["pgvector", "none"])
    parser.add_argument("--compare-with", default="reports/r4-2.yaml")
    parser.add_argument("--outs", default="reports/qdrant_bench.yaml")
    parser.add_argument("--qdrant-url", default="http://127.0.0.1:6333")
    parser.add_argument("--collection", default="ops_knowledge")
    parser.add_argument("--contrast-collection", default="ops_knowledge",
                        help="同机对照 collection（scale 压测时默认 8k 现网库）")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--hnsw-ef", type=int, default=0,
                        help="0=读 QDRANT_HNSW_EF 或默认 30")
    parser.add_argument("--p95-budget-ms", type=float, default=150.0)
    parser.add_argument("--rss-log", default="reports/qdrant_migrate/expand_rss.json")
    parser.add_argument("--skip-live", action="store_true", help="只写占位报告，不连库")
    args = parser.parse_args()

    hnsw_ef = args.hnsw_ef
    if hnsw_ef <= 0:
        raw = (os.getenv("QDRANT_HNSW_EF") or "30").strip()
        try:
            hnsw_ef = int(raw)
        except ValueError:
            hnsw_ef = 30
        if hnsw_ef <= 0:
            hnsw_ef = 30

    note = ""
    pg_p95 = None
    qd_p50 = None
    qd_p95 = None
    qd_p95_warm = None
    qd_p99_warm = None
    contrast_p95 = None
    points_count = None
    indexed_vectors_count = None
    source_n = None
    peak_rss = None
    steady_rss = None
    status = "skipped"

    if args.skip_live:
        note = "未在本机跑通原因：--skip-live；维护者环境无生产盘/无全量语料时仅校验脚本入口"
        status = "skipped"
    else:
        try:
            vectors = _load_query_vectors(args.n_queries)
            if args.baseline == "pgvector":
                pg_lat = _pg_latencies_ms(vectors, args.top_k)
                pg_lat.sort()
                pg_p95 = _percentile(pg_lat, 0.95)

            from qdrant_client import QdrantClient

            client = QdrantClient(url=args.qdrant_url)
            info = client.get_collection(args.collection)
            points_count = int(info.points_count or 0)
            indexed_vectors_count = int(getattr(info, "indexed_vectors_count", 0) or 0)

            # 冷/首轮
            lat_q = _search_latencies_ms(
                client,
                collection=args.collection,
                vectors=vectors,
                top_k=args.top_k,
                hnsw_ef=hnsw_ef,
            )
            lat_q_sorted = sorted(lat_q)
            qd_p50 = _percentile(lat_q_sorted, 0.50)
            qd_p95 = _percentile(lat_q_sorted, 0.95)

            # warmup 复测
            lat_w = _search_latencies_ms(
                client,
                collection=args.collection,
                vectors=vectors,
                top_k=args.top_k,
                hnsw_ef=hnsw_ef,
            )
            lat_w_sorted = sorted(lat_w)
            qd_p95_warm = _percentile(lat_w_sorted, 0.95)
            qd_p99_warm = _percentile(lat_w_sorted, 0.99)

            if (
                args.contrast_collection
                and args.contrast_collection != args.collection
            ):
                try:
                    cinfo = client.get_collection(args.contrast_collection)
                    source_n = int(cinfo.points_count or 0)
                    lat_c = _search_latencies_ms(
                        client,
                        collection=args.contrast_collection,
                        vectors=vectors,
                        top_k=args.top_k,
                        hnsw_ef=hnsw_ef,
                    )
                    contrast_p95 = _percentile(sorted(lat_c), 0.95)
                except Exception as exc:
                    note = f"contrast skip: {exc}"

            rss_path = Path(args.rss_log)
            if rss_path.is_file():
                try:
                    rss = json.loads(rss_path.read_text(encoding="utf-8"))
                    peak_rss = rss.get("peak_rss_mb") or rss.get("peak_rss_mb_build")
                    steady_rss = rss.get("steady_rss_mb")
                    if isinstance(rss, list) and rss:
                        peak_rss = max(r.get("rss_mb", 0) for r in rss)
                        steady_rss = rss[-1].get("rss_mb")
                    elif isinstance(rss, dict) and "samples" in rss:
                        samples = rss["samples"]
                        if samples:
                            peak_rss = max(s.get("rss_mb", 0) for s in samples)
                            steady_rss = samples[-1].get("rss_mb")
                        peak_rss = rss.get("peak_rss_mb", peak_rss)
                        steady_rss = rss.get("steady_rss_mb", steady_rss)
                except Exception:
                    pass

            status = "measured"
            parts = [
                f"n_queries={len(vectors)}",
                f"hnsw_ef={hnsw_ef}",
                f"compare_with={args.compare_with}",
            ]
            if note:
                parts.append(note)
            note = "; ".join(parts)
        except Exception as exc:
            status = "skipped"
            note = f"未在本机跑通原因：{exc}"

    p95_pass = (
        qd_p95 is not None and qd_p95 < args.p95_budget_ms
        if status == "measured"
        else None
    )
    baseline_note = ""
    if args.baseline == "none":
        baseline_note = (
            "pgvector skipped: PG corpus N=8574 not comparable to synthetic Qdrant "
            f"N={points_count}"
        )

    report = {
        "status": status,
        "baseline": args.baseline,
        "baseline_note": baseline_note,
        "collection": args.collection,
        "points_count": points_count,
        "indexed_vectors_count": indexed_vectors_count,
        "source_collection": args.contrast_collection,
        "source_n": source_n,
        "compare_with": args.compare_with,
        "hnsw_ef": hnsw_ef,
        "pgvector_search_p95_ms": pg_p95,
        "qdrant_search_p50_ms": qd_p50,
        "qdrant_search_p95_ms": qd_p95,
        "qdrant_search_p95_ms_warmup": qd_p95_warm,
        "qdrant_search_p99_ms_warmup": qd_p99_warm,
        "ops_knowledge_8k_p95_ms": contrast_p95,
        "n_queries": args.n_queries,
        "top_k": args.top_k,
        "p95_budget_ms": args.p95_budget_ms,
        "p95_pass": p95_pass,
        "peak_rss_mb_build": peak_rss,
        "steady_rss_mb": steady_rss,
        "rss_log": args.rss_log,
        "gate": {
            "steady_rss_lt_3200mb": (
                steady_rss is not None and steady_rss < 3200
                if steady_rss is not None
                else None
            ),
            "peak_rss_le_3800mb": (
                peak_rss is not None and peak_rss <= 3800
                if peak_rss is not None
                else None
            ),
            "p95_lt_150ms": p95_pass,
        },
        "note": note,
        "recorded_at": datetime.now(UTC).isoformat(),
        "rerank_enabled_required": False,
    }
    out = Path(args.outs)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(_yaml_dump(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"wrote {out}")
    return 0 if status == "measured" else 1


if __name__ == "__main__":
    raise SystemExit(main())
