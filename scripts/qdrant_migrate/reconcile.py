#!/usr/bin/env python3
"""对账：count + 向量 L∞ + Top-k overlap。"""
from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def _linf(a: list[float], b: list[float]) -> float:
    return max(abs(x - y) for x, y in zip(a, b, strict=True))


def _overlap(a: list[int], b: list[int]) -> float:
    if not a and not b:
        return 1.0
    sa, sb = set(a), set(b)
    return len(sa & sb) / max(len(sa | sb), 1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile PG vs Qdrant")
    parser.add_argument("--pg-dsn", default="")
    parser.add_argument("--qdrant-url", default="http://127.0.0.1:6333")
    parser.add_argument("--collection", default="ops_knowledge")
    parser.add_argument("--sample", type=int, default=500)
    parser.add_argument("--max-l-inf-err", type=float, default=1e-5)
    parser.add_argument("--min-topk-overlap", type=float, default=0.95)
    parser.add_argument("--topk", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    import numpy as np
    from qdrant_client import QdrantClient
    from sqlalchemy import create_engine, text

    from app.config import settings

    pg_dsn = (args.pg_dsn or settings.database_url).replace("+asyncpg", "+psycopg")
    engine = create_engine(pg_dsn)
    client = QdrantClient(url=args.qdrant_url)

    with engine.connect() as conn:
        pg_count = int(conn.execute(text("SELECT count(*) FROM ops_knowledge_chunks")).scalar_one())
    q_count = int(client.count(collection_name=args.collection, exact=True).count)
    count_diff = abs(pg_count - q_count)

    rng = random.Random(args.seed)
    with engine.connect() as conn:
        ids = [
            int(r[0])
            for r in conn.execute(text("SELECT id FROM ops_knowledge_chunks ORDER BY id"))
        ]
    sample_ids = ids if len(ids) <= args.sample else rng.sample(ids, args.sample)

    max_linf = 0.0
    linf_fail = 0
    with engine.connect() as conn:
        for pid in sample_ids:
            row = conn.execute(
                text("SELECT embedding FROM ops_knowledge_chunks WHERE id = :id"),
                {"id": pid},
            ).first()
            if row is None:
                continue
            emb = row[0]
            if hasattr(emb, "tolist"):
                emb = emb.tolist()
            elif isinstance(emb, str):
                emb = json.loads(emb)
            pts = client.retrieve(
                collection_name=args.collection,
                ids=[pid],
                with_vectors=True,
                with_payload=False,
            )
            if not pts:
                linf_fail += 1
                max_linf = max(max_linf, 1.0)
                continue
            qvec = pts[0].vector
            if isinstance(qvec, dict):
                qvec = next(iter(qvec.values()))
            err = _linf(list(emb), list(qvec))
            max_linf = max(max_linf, err)
            if err >= args.max_l_inf_err:
                linf_fail += 1

    # Top-k overlap：用抽样向量作 query
    overlaps: list[float] = []
    query_ids = sample_ids[: min(50, len(sample_ids))]
    with engine.connect() as conn:
        for qid in query_ids:
            row = conn.execute(
                text("SELECT embedding FROM ops_knowledge_chunks WHERE id = :id"),
                {"id": qid},
            ).first()
            if row is None:
                continue
            emb = row[0]
            if hasattr(emb, "tolist"):
                emb = emb.tolist()
            elif isinstance(emb, str):
                emb = json.loads(emb)
            pg_rows = conn.execute(
                text(
                    "SELECT id FROM ops_knowledge_chunks "
                    "ORDER BY embedding <=> CAST(:qvec AS vector) LIMIT :k"
                ),
                {"qvec": json.dumps(list(emb)), "k": args.topk},
            ).all()
            pg_top = [int(r[0]) for r in pg_rows]
            hits = client.search(
                collection_name=args.collection,
                query_vector=list(emb),
                limit=args.topk,
                with_payload=False,
            )
            q_top = [int(h.id) for h in hits]
            overlaps.append(_overlap(pg_top, q_top))

    mean_overlap = float(np.mean(overlaps)) if overlaps else 0.0
    ok = (
        count_diff == 0
        and max_linf < args.max_l_inf_err
        and linf_fail == 0
        and mean_overlap >= args.min_topk_overlap
    )
    report = {
        "status": "pass" if ok else "fail",
        "pg_count": pg_count,
        "qdrant_count": q_count,
        "count_diff": count_diff,
        "sample": len(sample_ids),
        "max_l_inf": max_linf,
        "linf_fail": linf_fail,
        "topk": args.topk,
        "mean_topk_overlap": mean_overlap,
        "thresholds": {
            "max_l_inf_err": args.max_l_inf_err,
            "min_topk_overlap": args.min_topk_overlap,
        },
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    out = args.out or str(
        Path("reports")
        / f"qdrant_reconcile_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.yaml"
    )
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    # 轻量 yaml（无 pyyaml 依赖）
    lines = [f"{k}: {json.dumps(v) if isinstance(v, (dict, list)) else v}" for k, v in report.items()]
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"wrote {out}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
