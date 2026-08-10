#!/usr/bin/env python3
"""R-2 RAG 入库管线 CLI（契约 rag-knowledge-contract-v1）。

用法：
    # 只看计数，不写库、不加载模型
    python scripts/rag_ingest.py --dry-run

    # 单条试跑（验证管线正确性）
    python scripts/rag_ingest.py --only issues --source-id 2720

    # 全量灌库（含 docs）
    python scripts/rag_ingest.py \
      --docs-root ../ops-desk-workspace/docs/05-plan \
      --docs-root ../ops-desk-workspace/docs/contracts
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import settings  # noqa: E402
from app.ops.rag.embedder import ApiEmbedder, SentenceTransformerEmbedder  # noqa: E402
from app.ops.rag.ingest import (  # noqa: E402
    ingest,
    load_doc_units,
    load_issue_units,
    load_pull_units,
)
from app.ops.rag.tokenizer import BgeM3TokenCounter  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Ops RAG 入库管线（R-2）")
    parser.add_argument(
        "--docs-root",
        action="append",
        type=Path,
        default=[],
        help="docs 语料根目录（可多次）；source_id = 根目录名/相对路径",
    )
    parser.add_argument("--only", choices=["issues", "pulls", "docs"], action="append")
    parser.add_argument("--source-id", help="只处理指定编号（试跑用，如 2720）")
    parser.add_argument("--limit", type=int, help="每类源最多处理条数")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--embedder", choices=["st", "api"], default="st")
    parser.add_argument("--dry-run", action="store_true", help="只出计数，不写库不加载模型")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    # R-2 D5：CLI 走同步引擎；app 的 asyncpg URL 转 psycopg
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg")
    engine = create_engine(sync_url)

    embedder = (
        SentenceTransformerEmbedder(batch_size=args.batch_size)
        if args.embedder == "st"
        else ApiEmbedder()
    )
    counter = BgeM3TokenCounter()

    only = set(args.only or ["issues", "pulls", "docs"])
    with Session(engine) as session:
        units = []
        if "issues" in only:
            units += load_issue_units(session, args.limit, args.source_id)
        if "pulls" in only:
            units += load_pull_units(session, args.limit, args.source_id)
        if "docs" in only:
            if not args.docs_root:
                logging.warning("--only 含 docs 但未给 --docs-root，跳过 docs")
            else:
                units += load_doc_units(args.docs_root)
        report = ingest(session, embedder, counter, units, dry_run=args.dry_run)

    print(f"报告: {report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
