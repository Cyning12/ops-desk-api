#!/usr/bin/env python3
"""lg_rag Phase 3 漏召回改善 eval（PLAN 3.3：G37/G39 等改善 ≥3 条）。

对比同一 query：basic 图（单次检索，无回环）vs router 图（evaluate/rewrite 自纠错）。
改善定义：basic 侧 low（gate=refuse 或 kept=0）→ router 侧非 low（answer/partial 或 kept>0）。

用法：
    .venv/bin/python scripts/lg_rag_retry_eval.py                 # 默认候选池（weak ∪ G37/G39）
    .venv/bin/python scripts/lg_rag_retry_eval.py --ids G37 G39   # 指定 case
    .venv/bin/python scripts/lg_rag_retry_eval.py --min-improved 3
exit 0 = 改善数达标；否则 exit 1。
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

from app.ops.lg_rag import ainvoke_basic_agent, ainvoke_router_agent  # noqa: E402
from app.ops.tracing import flush_traces, tracing_enabled  # noqa: E402

GOLDEN = Path("evals/golden/queries_v1.yaml")
PLAN_IDS = {"G37", "G39"}


def _is_low(meta: dict) -> bool:
    """low = 零命中（hit_count=0 / kept 缺失）或 gate=refuse；空 meta 视为 low（不知即 low）。

    注意：route != rag 时不调用本函数（direct/refuse 分流不参与改善判定）。
    """
    if not meta:
        return True
    gate = str(meta.get("gate_action") or "")
    return gate == "refuse" or not meta.get("kept_count")


def _gate(meta: dict) -> str:
    return str((meta or {}).get("gate_action") or "-")


async def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--ids", nargs="*", default=None)
    p.add_argument("--min-improved", type=int, default=3)
    args = p.parse_args()

    cases = yaml.safe_load(GOLDEN.read_text(encoding="utf-8"))
    if isinstance(cases, dict):
        cases = cases.get("cases") or cases.get("queries") or cases.get("golden") or []
    pool = []
    for c in cases:
        cid = str(c.get("id") or "")
        if args.ids is not None:
            if cid in set(args.ids):
                pool.append(c)
        elif cid in PLAN_IDS or c.get("expect_relevance") == "weak":
            pool.append(c)
    print(f"候选池: {len(pool)} 条（{'--ids 指定' if args.ids else 'weak ∪ G37/G39'}）")

    improved = 0
    via_retry = 0
    routed = 0
    low_basic = 0
    for c in pool:
        cid, q = str(c.get("id")), str(c.get("query"))
        try:
            out_b = await ainvoke_basic_agent(q, thread_id=f"p3eval-{cid}-basic")
            out_r = await ainvoke_router_agent(q, thread_id=f"p3eval-{cid}-router")
        except Exception as exc:
            print(f"{cid}: ERROR {exc!r}")
            continue
        mb, mr = out_b.get("chain_meta") or {}, out_r.get("chain_meta") or {}
        rc = out_r.get("retry_count") or 0
        route = out_r.get("route") or "rag"
        low_b = _is_low(mb)
        low_basic += 1 if low_b else 0
        if route != "rag":
            # router 分到 direct/refuse：未走检索，不能算 RAG 改善（可能是误分流）
            mark = f"ROUTED-{route}"
            routed += 1
        else:
            better = low_b and not _is_low(mr)
            improved += 1 if better else 0
            if better and rc > 0:
                via_retry += 1
            mark = (
                ("IMPROVED(retry)" if rc > 0 else "IMPROVED(variance)")
                if better
                else ("low->low" if low_b and _is_low(mr) else "-")
            )
        print(
            f"{cid}: basic[{_gate(mb)},kept={mb.get('kept_count')}] "
            f"router[{_gate(mr)},kept={mr.get('kept_count')},retry={rc},route={route}] {mark}"
        )
    print(
        f"\nbasic 侧 low: {low_basic}/{len(pool)}；"
        f"改善: {improved} 条（其中 retry 驱动 {via_retry} 条；阈值 ≥{args.min_improved}）；"
        f"误分流出 rag: {routed} 条"
    )
    if tracing_enabled():
        flush_traces()
    return 0 if improved >= args.min_improved else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
