#!/usr/bin/env python3
"""从 PG 导出 id+embedding+filter 字段（禁止 content/metadata/images）。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

ALLOWED_PAYLOAD = ("source_type", "repo", "source_id", "chunk_index")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export vectors for Qdrant upsert")
    parser.add_argument("--out", required=True)
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument(
        "--payload-fields",
        default="source_type,repo,source_id,chunk_index",
        help="comma-separated filter fields only",
    )
    parser.add_argument("--database-url", default="")
    args = parser.parse_args()

    fields = [f.strip() for f in args.payload_fields.split(",") if f.strip()]
    for f in fields:
        if f not in ALLOWED_PAYLOAD:
            print(f"forbidden payload field: {f}", file=sys.stderr)
            return 2

    from sqlalchemy import create_engine, text

    from app.config import settings

    db_url = (args.database_url or settings.database_url).replace("+asyncpg", "+psycopg")
    engine = create_engine(db_url)
    cols = ", ".join(["id", "embedding", *fields])
    sql = text(
        f"SELECT {cols} FROM ops_knowledge_chunks ORDER BY id "
        "OFFSET :offset LIMIT :limit"
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    offset = 0
    with engine.connect() as conn, out_path.open("w", encoding="utf-8") as fh:
        while True:
            rows = conn.execute(
                sql, {"offset": offset, "limit": args.chunk_size}
            ).mappings().all()
            if not rows:
                break
            for r in rows:
                emb = r["embedding"]
                if hasattr(emb, "tolist"):
                    emb = emb.tolist()
                elif isinstance(emb, str):
                    emb = json.loads(emb)
                payload = {f: r[f] for f in fields}
                # 禁止大字段泄漏
                assert "content" not in payload
                assert "metadata" not in payload
                assert "images" not in payload
                fh.write(
                    json.dumps(
                        {"id": int(r["id"]), "vector": list(emb), "payload": payload},
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                n += 1
            offset += args.chunk_size
    print(f"exported {n} points → {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
