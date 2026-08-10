#!/usr/bin/env python3
"""自建管线查询侧（对照实验 · 只读，不入库）。

走生产同款路径：bge-m3 嵌 query → retrieve.py 的语义+关键词两路 SQL
→ RRF 融合 → 打印 top-5。对照 LI 版的内存索引检索。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.ops.rag.embedder import SentenceTransformerEmbedder  # noqa: E402
from app.ops.rag.retrieve import (  # noqa: E402
    _KEYWORD_SQL,
    _SEMANTIC_SQL,
    _row_to_chunk,
    rrf_fuse,
)

DB_URL = "postgresql+psycopg://ops:ops_password@localhost:5432/opsdesk"
G01_QUERY = "Kimi Code 自动压缩被取消并报错 This operation was aborted 是什么原因?"


def local_bge_m3_path() -> str:
    root = Path.home() / ".cache/huggingface/hub/models--BAAI--bge-m3/snapshots"
    for snap in root.iterdir():
        has_weights = (snap / "pytorch_model.bin").exists() or (snap / "model.safetensors").exists()
        has_config = (snap / "config.json").exists() and (snap / "tokenizer.json").exists()
        if has_weights and has_config:
            return str(snap)
    raise SystemExit("本地无完整 bge-m3 快照")


def main() -> None:
    embedder = SentenceTransformerEmbedder(model_name=local_bge_m3_path())
    qvec = embedder.embed([G01_QUERY])[0]
    print(f"== query 向量 == dim={len(qvec)}\n")

    engine = create_engine(DB_URL)
    with Session(engine) as session:
        sem = [_row_to_chunk(r) for r in session.execute(_SEMANTIC_SQL, {"qvec": json.dumps(qvec), "k": 10})]
        kw = [_row_to_chunk(r) for r in session.execute(_KEYWORD_SQL, {"q": G01_QUERY, "k": 10})]
        fused = rrf_fuse(sem, kw, top_n=5)

    print(f"== 语义路 top3 = {[ (c.anchor) for c in sem[:3] ]}")
    print(f"== 关键词路 top3 = {[ (c.anchor) for c in kw[:3] ]}（中文 query 走 'simple' 分词，预期弱）\n")
    print("== RRF 融合 top-5 ==")
    for c in fused:
        first = c.content.split("Content: ", 1)[-1].strip().splitlines()[0][:50]
        print(f"  {c.anchor} · rrf={c.rrf_score:.4f} · sem#{c.semantic_rank} kw#{c.keyword_rank} · {first}")

    hit = any(c.source_id == "2720" for c in fused)
    print(f"\n== G01 断言 == 2720 ∈ top5: {'PASS' if hit else 'FAIL'}")


if __name__ == "__main__":
    main()
