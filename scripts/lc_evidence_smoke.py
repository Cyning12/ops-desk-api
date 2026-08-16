#!/usr/bin/env python3
"""LangChain evidence chain 冒烟：retrieve → grade → answer（不挂 graph）。

前置：
  - .env：DATABASE_URL、LLM（grader/bailian + answer provider）、
    RAG_VECTOR_BACKEND / Qdrant（若用 qdrant）
  - 本机语料已 ingest；可选 RAG_RERANK_ENABLED

用法：
  .venv/bin/python scripts/lc_evidence_smoke.py --query "自动压缩被取消怎么办"
  .venv/bin/python scripts/lc_evidence_smoke.py   # 默认 G01 问法
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()  # 必须先于 langfuse 相关 import

from app.ops.lc_evidence_chain import ainvoke_evidence_answer  # noqa: E402
from app.ops.tracing import flush_traces, tracing_enabled  # noqa: E402

DEFAULT_QUERY = "Kimi Code 自动压缩被取消并报错 This operation was aborted 是什么原因?"


def _dump(obj: object, limit: int) -> str:
    text = json.dumps(obj, ensure_ascii=False, indent=2, default=str)
    if len(text) > limit:
        return text[:limit] + f"\n…(truncated, total {len(text)} chars)"
    return text


async def main() -> int:
    parser = argparse.ArgumentParser(description="lc_evidence_chain smoke")
    parser.add_argument("--query", default=DEFAULT_QUERY, help="用户问题")
    parser.add_argument(
        "--max-chars",
        type=int,
        default=6000,
        help="stdout JSON 截断长度（默认 6000）",
    )
    args = parser.parse_args()

    tracing_on = tracing_enabled()
    print(f"tracing: {'on' if tracing_on else 'off'} (OPS_CHAT_TRACER + LANGFUSE_* keys)")
    print(f"query: {args.query}")
    result = await ainvoke_evidence_answer(args.query)

    print("\n== meta ==")
    print(_dump(result.meta, 800))

    print(f"\n== evidence ({len(result.evidence)}) ==")
    for e in result.evidence:
        rel = e.grade.relevance.value if e.grade else "unrated"
        reason = (e.grade.reason if e.grade else "")[:80]
        print(f"  - {e.anchor} · {rel} · {e.title or ''}")
        if reason:
            print(f"    reason: {reason}")

    print("\n== answer ==")
    print((result.answer or "")[:1200])

    print("\n== full json (truncated) ==")
    print(_dump(result.model_dump(mode="json"), args.max_chars))

    if tracing_on:
        flush_traces()
        print("flushed Langfuse traces (tag/run_name=lc-evidence-chain)")

    ok = bool(result.answer)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
