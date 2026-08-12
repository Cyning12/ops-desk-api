#!/usr/bin/env python3
"""对比真 CE 报告 r4-R.yaml 与误跑 Normal r4-R-misrun-no-ce.yaml。"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
A = ROOT / "reports" / "r4-R-misrun-no-ce.yaml"
B = ROOT / "reports" / "r4-R.yaml"


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def main() -> int:
    if not A.exists():
        print(f"missing baseline misrun: {A}", file=sys.stderr)
        return 2
    if not B.exists():
        print(f"missing CE report: {B}（先跑完真 r4-R）", file=sys.stderr)
        return 2
    a, b = load(A), load(B)
    print("=== 报告头 ===")
    for label, d in (("misrun", a), ("r4-R", b)):
        print(
            f"{label}: arm={d.get('arm')} rerank={d.get('rerank_enabled')} "
            f"grader={d.get('grader')} k={d.get('recall_k_each')} "
            f"coarse={d.get('coarse_top_n')} "
            f"floor={d.get('rerank_min_score') or (d.get('summary') or {}).get('rerank_min_score')} "
            f"ratio={d.get('rerank_score_ratio') or (d.get('summary') or {}).get('rerank_score_ratio')}"
        )
        s = d.get("summary") or {}
        print(
            f"  pass={s.get('pass')} recall={s.get('recall_at5_by_quadrant')} "
            f"neg={s.get('negative_refuse')}"
        )

    # 焦点：G65 + negative 汇总
    print("\n=== 焦点 G65 ===")
    for label, d in (("misrun", a), ("r4-R", b)):
        g = next((r for r in d["results"] if r.get("id") == "G65"), None)
        if not g:
            print(f"{label}: G65 missing")
            continue
        print(
            f"{label}: verdict={g.get('verdict')} must_refuse={g.get('must_refuse')} "
            f"gate={g.get('gate_action')} best={g.get('best_relevance')} top5={g.get('top5')}"
        )

    by_a = {r["id"]: r for r in a["results"]}
    by_b = {r["id"]: r for r in b["results"]}
    common = sorted(set(by_a) & set(by_b))
    print(f"\n=== 同 ID 差分 · common={len(common)} ===")
    v_flip = best_flip = recall_flip = 0
    for i in common:
        x, y = by_a[i], by_b[i]
        if x.get("verdict") != y.get("verdict"):
            v_flip += 1
            print(
                f"  verdict {i} {x.get('quadrant')}: "
                f"{x.get('verdict')}→{y.get('verdict')} "
                f"best {x.get('best_relevance')}→{y.get('best_relevance')} "
                f"top5 {x.get('top5')} → {y.get('top5')}"
            )
        if x.get("best_relevance") != y.get("best_relevance"):
            best_flip += 1
        if x.get("recall_at5") != y.get("recall_at5"):
            recall_flip += 1
            if x.get("verdict") == y.get("verdict"):
                print(
                    f"  recall  {i} {x.get('quadrant')}: "
                    f"{x.get('recall_at5')}→{y.get('recall_at5')}"
                )
    print(f"\nverdict_flips={v_flip} best_flips={best_flip} recall_flips={recall_flip}")

    def best_hist(results):
        return Counter(
            r.get("best_relevance")
            for r in results
            if r.get("quadrant") != "negative" and not r.get("must_refuse")
        )

    print("\n=== best_relevance（非负样本）===")
    print("misrun", dict(best_hist(a["results"])))
    print("r4-R  ", dict(best_hist(b["results"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
