#!/usr/bin/env python3
"""lg_rag Phase 2 router 准确率评测（DESIGN §4：≥ 90% 验收）。

真 LLM 本地手动跑：
    .venv/bin/python scripts/router_accuracy.py [--labeled evals/router/labeled_router_v1.yaml]
exit 0 = 达标；否则 exit 1 并打印错分明细。
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from app.ops.lg_rag.nodes import _ISSUE_NO_RE, _classify_route  # noqa: E402

THRESHOLD = 0.90


async def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--labeled", default="evals/router/labeled_router_v1.yaml")
    args = p.parse_args()
    cases = yaml.safe_load(Path(args.labeled).read_text(encoding="utf-8"))["cases"]
    wrong: list[tuple[str, str, str]] = []
    for c in cases:
        q, expect = c["query"], c["route"]
        if _ISSUE_NO_RE.search(q):
            got = "rag"
        else:
            try:
                got, _raw, _fb = await _classify_route(q)
            except Exception as exc:
                got = "rag"
                print(f"[warn] LLM 异常 fallback=rag: {q[:40]!r} err={exc!r}")
        if got != expect:
            wrong.append((q, expect, got))
    total = len(cases)
    acc = (total - len(wrong)) / total if total else 0.0
    print(f"accuracy: {total - len(wrong)}/{total} = {acc:.1%} (threshold {THRESHOLD:.0%})")
    for q, expect, got in wrong:
        print(f"  WRONG expect={expect} got={got} query={q[:60]!r}")
    return 0 if acc >= THRESHOLD else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
