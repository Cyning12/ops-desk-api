#!/usr/bin/env python3
"""自建管线查询侧（对照实验 · 只读，不入库）。

用法：
    custom_pipeline.py          → G01 全库检索验证（语义+关键词+RRF）
    custom_pipeline.py 1089     → 先看该 issue 已入库的切分结果，再跑检索
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import create_engine, text  # noqa: E402
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


def show_stored_chunks(session: Session, number: int) -> None:
    """打印指定 issue 的已入库切分结果（与 LI 输出同格式，便于逐块对照）。"""
    rows = session.execute(
        text(
            "SELECT chunk_index, content FROM ops_knowledge_chunks "
            "WHERE source_type = 'issue' AND source_id = :sid ORDER BY chunk_index"
        ),
        {"sid": str(number)},
    ).all()
    if not rows:
        print(f"#{number} 无入库 chunk")
        return
    broken = 0
    print(f"== 自建切分结果 == #{number} · {len(rows)} 块")
    for idx, content in rows:
        body = content.split("Content: ", 1)[-1]
        marks = body.count("```")
        if marks % 2 != 0:
            broken += 1
        flag = "✓" if marks % 2 == 0 else "✗（嵌套/非平衡源 · E9）"
        first = body.strip().splitlines()[0][:55] if body.strip() else "(空)"
        print(f"  chunk {idx}: {len(body)} 字符 · fence标记={marks} {flag} · 起: {first}")
    print(f"  → fence 奇数标记块: {broken}/{len(rows)}\n")


def local_bge_m3_path() -> str:
    root = Path.home() / ".cache/huggingface/hub/models--BAAI--bge-m3/snapshots"
    for snap in root.iterdir():
        has_weights = (snap / "pytorch_model.bin").exists() or (snap / "model.safetensors").exists()
        has_config = (snap / "config.json").exists() and (snap / "tokenizer.json").exists()
        if has_weights and has_config:
            return str(snap)
    raise SystemExit("本地无完整 bge-m3 快照")


def main() -> None:
    issue = int(sys.argv[1]) if len(sys.argv) > 1 else None
    engine = create_engine(DB_URL)

    if issue is not None:
        with Session(engine) as session:
            show_stored_chunks(session, issue)

    embedder = SentenceTransformerEmbedder(model_name=local_bge_m3_path())
    qvec = embedder.embed([G01_QUERY])[0]
    print(f"== query 向量 == dim={len(qvec)}\n")

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
