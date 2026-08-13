#!/usr/bin/env python3
"""C 臂：批算 ops_knowledge_chunks.sparse_embedding（断点续写）。

只写 sparse_embedding；**不动** dense embedding 列。
默认跳过已非 NULL 行（断点续写）。目标约 8574 块。

用法（仓根 · 隔离 venv 见 README）：

    export DATABASE_URL=postgresql+psycopg://ops:ops_password@localhost:5432/opsdesk
    python experiments/rag_compare/sparse_arm_c/embed_sparse.py
    python experiments/rag_compare/sparse_arm_c/embed_sparse.py --batch-size 8 --limit 32  # 冒烟
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import Engine  # noqa: E402

from app.ops.rag.sparse_vec import encode_texts_sparse  # noqa: E402

DEFAULT_TARGET = 8574


def _sync_url(url: str) -> str:
    """asyncpg DSN → psycopg 同步驱动。"""
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "+psycopg", 1)
    if url.startswith("postgresql://") and "+psycopg" not in url:
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _progress(engine: Engine) -> tuple[int, int, int]:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT count(*) AS total, "
                "count(sparse_embedding) AS filled, "
                "count(*) FILTER (WHERE sparse_embedding IS NULL) AS nulls "
                "FROM ops_knowledge_chunks"
            )
        ).one()
        return int(row.total), int(row.filled), int(row.nulls)


def _column_missing(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return "sparse_embedding" in msg and (
        "does not exist" in msg or "undefinedcolumn" in msg
    )


def run(
    *,
    database_url: str,
    batch_size: int,
    limit: int | None,
    model_name: str,
    dry_run: bool,
) -> int:
    engine = create_engine(_sync_url(database_url), future=True)
    try:
        total, filled, nulls = _progress(engine)
    except Exception as exc:
        if _column_missing(exc):
            print(
                "ERROR: column sparse_embedding missing. "
                "先在本地/影子库执行 add_sparse_embedding.sql（勿对生产库）。"
            )
            return 2
        raise
    print(f"progress: total={total} filled={filled} nulls={nulls} target≈{DEFAULT_TARGET}")
    if nulls == 0:
        print("all rows have sparse_embedding; nothing to do")
        return 0

    # 断点：只取尚未灌入的行
    sql = text(
        "SELECT id, content FROM ops_knowledge_chunks "
        "WHERE sparse_embedding IS NULL "
        "ORDER BY id "
        "LIMIT :lim"
    )
    remaining = nulls if limit is None else min(nulls, limit)
    done = 0
    with engine.begin() as conn:
        while done < remaining:
            fetch_n = min(batch_size, remaining - done)
            rows = conn.execute(sql, {"lim": fetch_n}).all()
            if not rows:
                break
            ids = [int(r.id) for r in rows]
            texts = [str(r.content) for r in rows]
            if dry_run:
                print(f"dry-run batch ids[{ids[0]}..{ids[-1]}] n={len(ids)}")
                done += len(ids)
                continue
            vecs = encode_texts_sparse(texts, model_name=model_name, batch_size=batch_size)
            for cid, svec in zip(ids, vecs, strict=True):
                conn.execute(
                    text(
                        "UPDATE ops_knowledge_chunks "
                        "SET sparse_embedding = CAST(:svec AS sparsevec) "
                        "WHERE id = :id AND sparse_embedding IS NULL"
                    ),
                    {"svec": svec, "id": cid},
                )
            done += len(ids)
            print(f"wrote {done}/{remaining} (last_id={ids[-1]})")

    total, filled, nulls = _progress(engine)
    print(f"done: total={total} filled={filled} nulls={nulls}")
    if total == DEFAULT_TARGET and nulls == 0:
        print(f"OK: sparse_embedding 灌满 {DEFAULT_TARGET}")
    elif nulls:
        print(f"NOTE: 仍有 {nulls} 行 NULL（可继续重跑本脚本续写）")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="C 臂 sparse_embedding 批重嵌（断点续写）")
    p.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", "postgresql+psycopg://ops:ops_password@localhost:5432/opsdesk"),
        help="同步或 asyncpg DSN（脚本内转 psycopg）",
    )
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--limit", type=int, default=None, help="本轮最多处理行数（冒烟用）")
    p.add_argument("--model", default=os.getenv("RAG_SPARSE_MODEL", "BAAI/bge-m3"))
    p.add_argument("--dry-run", action="store_true", help="不加载模型、不写库")
    args = p.parse_args()
    return run(
        database_url=args.database_url,
        batch_size=args.batch_size,
        limit=args.limit,
        model_name=args.model,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    raise SystemExit(main())
