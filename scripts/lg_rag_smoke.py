#!/usr/bin/env python3
"""lg_rag Phase1 冒烟：StateGraph → rag_node → Evidence Chain。

说明书：docs/guides/IMPL_langgraph-lg-rag-phase1_v1.md S6/S8。
--parity：同 query 直连 ainvoke_evidence_answer 对比 answer（级别 A 对齐）。
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv()

from app.ops.lg_rag import ainvoke_basic_agent  # noqa: E402
from app.ops.tracing import flush_traces, tracing_enabled  # noqa: E402

DEFAULT_QUERY = "Kimi Code 自动压缩被取消并报错 This operation was aborted 是什么原因?"


def _extract_refs(text: str) -> set[str]:
    """提取 answer 中的 issue/PR 编号引用（≥4 位数字，如 2720）。"""
    import re

    return set(re.findall(r"\d{4,}", text))


async def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--query", default=DEFAULT_QUERY)
    p.add_argument("--thread-id", default="lg-rag-smoke")
    p.add_argument("--parity", action="store_true", help="直连 LCEL 对比 answer（级别 A）")
    args = p.parse_args()
    print(f"tracing: {'on' if tracing_enabled() else 'off'}")
    out = await ainvoke_basic_agent(args.query, thread_id=args.thread_id)
    msg = out["messages"][-1]
    text = getattr(msg, "content", "") or ""
    print(text[:1200])
    ok = bool(text.strip())

    if args.parity:
        from app.ops.lc_evidence_chain.chain import ainvoke_evidence_answer

        direct = await ainvoke_evidence_answer(args.query)
        direct_text = direct.answer or ""
        # LLM 生成本身非确定：两次调用措辞通常不同，不断言整串相等。
        # 检索侧确定（同 query 同库 → 同证据集），故比对 answer 引用的
        # issue/PR 编号（如 2720、#2720）是否重叠作为对齐信号。
        refs_direct = _extract_refs(direct_text)
        refs_graph = _extract_refs(text)
        overlap = refs_direct & refs_graph
        both_non_empty = bool(direct_text.strip()) and bool(text.strip())
        refs_aligned = not refs_direct or bool(overlap)  # 无引用可比对时退化为非空判定
        print(f"\n[parity] both_non_empty={both_non_empty} refs_direct={sorted(refs_direct)} refs_graph={sorted(refs_graph)} overlap={sorted(overlap)}")
        if refs_direct and not overlap:
            print("[parity] WARN: 引用标识无重叠，请人工判读两侧 answer")
            print(f"[parity] direct  answer[:200]: {direct_text[:200]}")
            print(f"[parity] via_graph answer[:200]: {text[:200]}")
        ok = ok and both_non_empty and refs_aligned

    if tracing_enabled():
        flush_traces()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
