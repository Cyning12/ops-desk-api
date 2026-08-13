#!/usr/bin/env python3
"""检查 ops_qdrant_dlq 表是否存在（影子写前置）。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check ops_qdrant_dlq schema")
    parser.add_argument("--database-url", default="")
    args = parser.parse_args()

    from sqlalchemy import create_engine, text

    from app.config import settings

    db_url = (args.database_url or settings.database_url).replace("+asyncpg", "+psycopg")
    engine = create_engine(db_url)
    with engine.connect() as conn:
        exists = conn.execute(
            text(
                "SELECT EXISTS ("
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_name = 'ops_qdrant_dlq')"
            )
        ).scalar_one()
    if not exists:
        print("MISSING: ops_qdrant_dlq — run: alembic upgrade head", file=sys.stderr)
        return 1
    print("OK: ops_qdrant_dlq exists")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
