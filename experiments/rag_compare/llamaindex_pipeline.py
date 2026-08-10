#!/usr/bin/env python3
"""LlamaIndex 版 RAG 管线（对照实验 · 不进生产）。

与自建管线同输入（DB 里的 #2720）、同模型（bge-m3，复用 HF 缓存）、
同问题（golden G01），观察框架默认行为的差距。

对照点（结果回填 README 对比表）：
  ① chunk 边界与数量   ② fence 是否被拦腰切   ③ G01 检索 top-5 命中
"""
from __future__ import annotations

import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

DB_DSN = "host=localhost port=5432 dbname=opsdesk user=ops password=ops_password"
G01_QUERY = "Kimi Code 自动压缩被取消并报错 This operation was aborted 是什么原因?"


def local_bge_m3_path() -> str:
    """从 HF 缓存解析完整快照路径（绕开 hub 版本解析）。

    教训（2026-08-10）：镜像/官方源混用导致缓存里有两个 revision 快照，
    离线模式下 transformers 会解析到缺权重的那个。直接喂本地路径最稳。
    """
    root = Path.home() / ".cache/huggingface/hub/models--BAAI--bge-m3/snapshots"
    for snap in root.iterdir():
        has_weights = (snap / "pytorch_model.bin").exists() or (snap / "model.safetensors").exists()
        has_config = (snap / "config.json").exists() and (snap / "tokenizer.json").exists()
        if has_weights and has_config:
            return str(snap)
    raise SystemExit("本地无完整 bge-m3 快照，先在线跑一次灌库")


def load_issue_body(number: int) -> tuple[str, str]:
    with psycopg.connect(DB_DSN) as conn:
        row = conn.execute(
            "SELECT title, body FROM ops_issues WHERE number = %s", (number,)
        ).fetchone()
    if not row:
        raise SystemExit(f"issue #{number} 不在库中")
    return row[0], row[1] or ""


def main() -> None:
    from llama_index.core import Document, Settings, VectorStoreIndex
    from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    number = int(sys.argv[1]) if len(sys.argv) > 1 else 2720
    title, body = load_issue_body(number)
    print(f"== 输入 == #{number} · {len(body)} 字符\n")

    # LI 默认两阶段：MarkdownNodeParser（按标题）→ SentenceSplitter（按尺寸）
    # 注意：SentenceSplitter 默认用 tiktoken 数 token，与 bge-m3 tokenizer 口径不同（对照 E5）
    Settings.embed_model = HuggingFaceEmbedding(model_name=local_bge_m3_path())
    doc = Document(text=body, metadata={"source_id": str(number), "title": title})

    md_nodes = MarkdownNodeParser().get_nodes_from_documents([doc])
    nodes = SentenceSplitter(chunk_size=800, chunk_overlap=0).get_nodes_from_documents(
        [Document(text=n.text, metadata=n.metadata) for n in md_nodes]
    )

    print(f"== ① 切分结果 == {len(nodes)} 块")
    for i, node in enumerate(nodes):
        first_line = node.text.strip().splitlines()[0][:60] if node.text.strip() else "(空)"
        fence_marks = node.text.count("```")
        fence_flag = "✓" if fence_marks % 2 == 0 else "✗ FENCE 被切断"
        print(f"  node {i}: {len(node.text)} 字符 · fence标记={fence_marks} {fence_flag} · 起: {first_line}")

    broken = sum(1 for n in nodes if n.text.count("```") % 2 != 0)
    print(f"\n== ② fence 完整性 == 被切断的块: {broken}/{len(nodes)}")

    index = VectorStoreIndex(nodes)
    hits = index.as_retriever(similarity_top_k=5).retrieve(G01_QUERY)
    print(f"\n== ③ G01 检索 top-{len(hits)} ==")
    for h in hits:
        first_line = h.node.text.strip().splitlines()[0][:50]
        print(f"  score={h.score:.4f} · {first_line}")


if __name__ == "__main__":
    main()
