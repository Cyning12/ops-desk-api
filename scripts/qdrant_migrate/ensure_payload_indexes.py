#!/usr/bin/env python3
"""仅为过滤字段建 payload index。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

ALLOWED = ("source_type", "repo", "source_id", "chunk_index")


def main() -> int:
    parser = argparse.ArgumentParser(description="Ensure Qdrant payload indexes")
    parser.add_argument("--url", default="http://127.0.0.1:6333")
    parser.add_argument("--collection", default="ops_knowledge")
    parser.add_argument("--fields", default="source_type,repo,source_id")
    args = parser.parse_args()

    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qm

    fields = [f.strip() for f in args.fields.split(",") if f.strip()]
    for f in fields:
        if f not in ALLOWED:
            print(f"forbidden index field: {f}", file=sys.stderr)
            return 2

    client = QdrantClient(url=args.url)
    for field in fields:
        # keyword for text filters
        schema = qm.PayloadSchemaType.KEYWORD
        if field == "chunk_index":
            schema = qm.PayloadSchemaType.INTEGER
        client.create_payload_index(
            collection_name=args.collection,
            field_name=field,
            field_schema=schema,
        )
        print(f"payload index ok: {field} ({schema})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
