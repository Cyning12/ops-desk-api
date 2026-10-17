#!/usr/bin/env python3
"""R-4 结案级汇总脚本（task rag-golden-eval-r4-r5 · E1）。

读 run_eval.py 产出的报告 YAML（reports/r4*.yaml 或 runner 新跑产物），
逐象限聚合 recall@5 / min_relevance / citation_in_hits / 拒答正确率，
对路线 §P1-RAG R-4「ZH问→EN文档 跨语言 ≥1/3」门槛显式判定，
小样本老实标 confidence（Wilson 95% 区间），出结案报告 YAML + Markdown 摘要。

纪律：
- 只读报告产物做聚合，不旁路重写检索/评级/拒答路径，不连库不连 LLM。
- FP-2：报告残缺/非法 → 显式报错非零退出，不静默跳过条目冒充全量。
- FP-7：报告头部写死样本量与 confidence；小样本不得当「已达标」引用。
- FP-8：SPEC-evaluation-observation 真值文件两仓未检索到 → 观测口径注记
  「照登：无实证 · 以路线 A-P1-3 引用口径为准」。

用法：
  .venv/bin/python evals/golden/summarize_r4.py --report reports/r4-1.yaml
  .venv/bin/python evals/golden/summarize_r4.py  # 默认取 reports/r4*.yaml 最新一份
  .venv/bin/python evals/golden/summarize_r4.py --report X --out-yaml Y --out-md Z
"""
from __future__ import annotations

import argparse
import math
import os
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORTS_DIR = ROOT / "reports"

QUADRANTS = ("zh2en", "zh2zh", "en2en", "negative")
TRI_STATES = {None, "pass", "fail"}
GATE_ACTIONS = {None, "answer", "answer_partial", "refuse"}
VERDICTS = {"pass", "fail"}

# 路线 §P1-RAG R-4：ZH问→EN文档 跨语言 recall@5 命中率 ≥ 1/3
ZH2EN_THRESHOLD = 1.0 / 3.0

# FP-8：SPEC-evaluation-observation 真值文件未检索到的固定注记
SPEC_OBSERVATION_NOTE = (
    "SPEC-evaluation-observation 真值文件在 api 仓与 workspace 仓均未检索到"
    "（照登：无实证）；观测三字段按路线 A-P1-3 引用口径对齐"
    "（measurement_source / confidence / comparability 透传自源报告）"
)


@dataclass
class QuadrantMetrics:
    """单象限聚合结果（分母 = 该指标非 null 的条数，与 runner 口径一致）。"""

    quadrant: str
    n: int = 0
    recall_n: int = 0
    recall_pass: int = 0
    min_rel_n: int = 0
    min_rel_pass: int = 0
    cite_n: int = 0
    cite_pass: int = 0
    verdict_pass: int = 0


@dataclass
class RefusalMetrics:
    """拒答正确率与误拒/误答分类。"""

    negative_n: int = 0
    refuse_correct: int = 0  # 负样本 gate_action=refuse
    false_answer_ids: list[str] = field(default_factory=list)  # 误答：负样本未拒答
    false_refusal_ids: list[str] = field(default_factory=list)  # 疑似误拒：正样本被拒答


def load_report(path: Path) -> dict[str, Any]:
    """加载并校验报告（FP-2：残缺/非法显式报错，SystemExit 非零退出）。"""
    if not path.exists():
        raise SystemExit(f"报告不存在: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise SystemExit(f"报告 YAML 解析失败: {path}: {e}") from e
    if not isinstance(data, dict):
        raise SystemExit(f"报告顶层非映射: {path}")
    results = data.get("results")
    if not isinstance(results, list) or not results:
        raise SystemExit(f"报告 results 缺失或为空（不静默冒充全量）: {path}")
    for i, row in enumerate(results):
        if not isinstance(row, dict):
            raise SystemExit(f"报告 results[{i}] 非映射: {path}")
        cid = row.get("id")
        if not cid:
            raise SystemExit(f"报告 results[{i}] 缺 id: {path}")
        quad = row.get("quadrant")
        if quad not in QUADRANTS:
            raise SystemExit(f"报告 {cid} quadrant 非法: {quad!r}（期望 {QUADRANTS}）")
        verdict = row.get("verdict")
        if verdict not in VERDICTS:
            raise SystemExit(f"报告 {cid} verdict 非法: {verdict!r}（期望 {VERDICTS}）")
        for key in ("recall_at5", "min_relevance", "citation_in_hits", "must_refuse"):
            if row.get(key) not in TRI_STATES:
                raise SystemExit(
                    f"报告 {cid} {key} 非法: {row.get(key)!r}（期望 pass/fail/null）"
                )
        if row.get("gate_action") not in GATE_ACTIONS:
            raise SystemExit(
                f"报告 {cid} gate_action 非法: {row.get('gate_action')!r}"
            )
    return data


def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    """Wilson score 区间；n<=0 返回 None。"""
    if n <= 0:
        return None
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, center - margin), min(1.0, center + margin)


def confidence_note(k: int, n: int) -> str:
    """小样本老实标（FP-7）：n 与 Wilson 95% CI 显式可见。"""
    ci = wilson_interval(k, n)
    if ci is None:
        return "n=0 · 无样本，不可判（confidence=none）"
    lo, hi = ci
    level = "low" if n < 50 else "medium"
    return (
        f"n={n} · Wilson 95% CI=[{lo:.2f}, {hi:.2f}] · "
        f"confidence={level}（小样本老实标，勿当已达标引用）"
    )


def _rate(k: int, n: int) -> float | None:
    return round(k / n, 4) if n > 0 else None


def aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    """逐象限聚合 + zh2en 门槛判定 + 拒答正确率分类（纯函数，可测）。"""
    quads: dict[str, QuadrantMetrics] = {q: QuadrantMetrics(quadrant=q) for q in QUADRANTS}
    refusal = RefusalMetrics()
    failures: list[dict[str, Any]] = []
    for row in results:
        q = quads[row["quadrant"]]
        q.n += 1
        if row.get("recall_at5") is not None:
            q.recall_n += 1
            q.recall_pass += row["recall_at5"] == "pass"
        if row.get("min_relevance") is not None:
            q.min_rel_n += 1
            q.min_rel_pass += row["min_relevance"] == "pass"
        if row.get("citation_in_hits") is not None:
            q.cite_n += 1
            q.cite_pass += row["citation_in_hits"] == "pass"
        q.verdict_pass += row["verdict"] == "pass"
        gate = row.get("gate_action")
        if row["quadrant"] == "negative":
            refusal.negative_n += 1
            if gate == "refuse":
                refusal.refuse_correct += 1
            else:
                refusal.false_answer_ids.append(str(row["id"]))  # 误答
        elif gate == "refuse":
            refusal.false_refusal_ids.append(str(row["id"]))  # 疑似误拒
        if row["verdict"] == "fail":
            failures.append(
                {
                    "id": str(row["id"]),
                    "quadrant": row["quadrant"],
                    "fail_reasons": [str(x) for x in row.get("fail_reasons") or []],
                }
            )

    out_quads: dict[str, Any] = {}
    for name in QUADRANTS:
        m = quads[name]
        if m.n == 0:
            continue
        out_quads[name] = {
            "n": m.n,
            "recall_at5": {
                "pass": m.recall_pass,
                "total": m.recall_n,
                "rate": _rate(m.recall_pass, m.recall_n),
                "confidence": confidence_note(m.recall_pass, m.recall_n),
            },
            "min_relevance": {
                "pass": m.min_rel_pass,
                "total": m.min_rel_n,
                "rate": _rate(m.min_rel_pass, m.min_rel_n),
            },
            "citation_in_hits": {
                "pass": m.cite_pass,
                "total": m.cite_n,
                "rate": _rate(m.cite_pass, m.cite_n),
            },
            "verdict_pass": f"{m.verdict_pass}/{m.n}",
        }

    zh = quads["zh2en"]
    zh_rate = _rate(zh.recall_pass, zh.recall_n)
    # 判定用未舍入原始比率（展示值 _rate 舍入到 4 位会让恰好 1/3 误判 NOT_MET）
    zh_rate_raw = zh.recall_pass / zh.recall_n if zh.recall_n > 0 else None
    if zh.recall_n == 0:
        zh_verdict = "NO_DATA"
    elif zh_rate_raw is not None and zh_rate_raw >= ZH2EN_THRESHOLD:
        zh_verdict = "MET"
    else:
        zh_verdict = "NOT_MET"

    acc = _rate(refusal.refuse_correct, refusal.negative_n)
    return {
        "quadrants": out_quads,
        "gates": {
            "zh2en_crosslingual_recall_at5": {
                "requirement": "路线 §P1-RAG R-4：ZH问→EN文档 跨语言 recall@5 ≥ 1/3",
                "threshold": ">=1/3",
                "hits": zh.recall_pass,
                "n": zh.recall_n,
                "rate": zh_rate,
                "verdict": zh_verdict,
                "confidence": confidence_note(zh.recall_pass, zh.recall_n),
            }
        },
        "refusal": {
            "negative_n": refusal.negative_n,
            "refuse_correct": refusal.refuse_correct,
            "accuracy": acc,
            "confidence": confidence_note(refusal.refuse_correct, refusal.negative_n),
            "false_answer_ids": refusal.false_answer_ids,
            "false_refusal_ids": refusal.false_refusal_ids,
            "classification_note": (
                "误答=负样本 gate_action≠refuse；疑似误拒=正样本（有金标命中）"
                "gate_action=refuse，供人工复核，不改默认参数（FP-3）"
            ),
        },
        "failures": failures,
    }


def build_final_report(data: dict[str, Any], source_path: Path) -> dict[str, Any]:
    """结案报告 YAML 结构（头部透传源报告 + 观测口径注记）。"""
    src_summary = data.get("summary") or {}
    agg = aggregate(data["results"])
    return {
        "run": data.get("run"),
        "source_report": str(source_path),
        "embed": data.get("embed"),
        "grader": data.get("grader"),
        "corpus": data.get("corpus"),
        "arm": data.get("arm"),
        "rerank_enabled": data.get("rerank_enabled"),
        "thresholds": {"zh2en_crosslingual_recall_at5": ">=1/3（路线 §P1-RAG R-4）"},
        **agg,
        "observation": {
            "measurement_source": src_summary.get("measurement_source"),
            "confidence": src_summary.get("confidence"),
            "comparability": src_summary.get("comparability"),
            "grade_stability_agree": src_summary.get("grade_stability_agree"),
            "spec_note": SPEC_OBSERVATION_NOTE,
        },
        "contract_drift": "见结案报告 Markdown「契约漂移」节（本 task 零改契约 · FP-5 上抛）",
    }


def _fmt_rate(rate: float | None) -> str:
    return "n/a" if rate is None else f"{rate:.2%}"


def render_markdown(report: dict[str, Any]) -> str:
    """结案报告 Markdown 摘要。"""
    lines: list[str] = []
    lines.append(f"# R-4 结案报告 · {report.get('run')}")
    lines.append("")
    lines.append("## 头部")
    lines.append("")
    lines.append(f"- 源报告：`{report.get('source_report')}`")
    lines.append(f"- embedder：{report.get('embed')} · grader：{report.get('grader')}")
    lines.append(f"- 语料：{report.get('corpus')} · arm：{report.get('arm')}")
    obs = report.get("observation") or {}
    lines.append(
        f"- 观测口径：measurement_source={obs.get('measurement_source')} · "
        f"confidence={obs.get('confidence')} · comparability={obs.get('comparability')}"
    )
    lines.append(f"- 注记：{obs.get('spec_note')}")
    lines.append("")
    lines.append("## 逐象限指标")
    lines.append("")
    lines.append("| 象限 | n | recall@5 | min_relevance | citation_in_hits | verdict |")
    lines.append("|------|---|----------|---------------|------------------|---------|")
    for name, q in (report.get("quadrants") or {}).items():
        r, m, c = q["recall_at5"], q["min_relevance"], q["citation_in_hits"]
        lines.append(
            f"| {name} | {q['n']} | {r['pass']}/{r['total']}"
            f"（{_fmt_rate(r['rate'])}） | {m['pass']}/{m['total']} |"
            f" {c['pass']}/{c['total']} | {q['verdict_pass']} |"
        )
    lines.append("")
    lines.append("## 门槛判定")
    lines.append("")
    g = report["gates"]["zh2en_crosslingual_recall_at5"]
    lines.append(f"- zh2en 跨语言 recall@5：命中 {g['hits']}/{g['n']}"
                 f"（{_fmt_rate(g['rate'])}） vs 门槛 {g['threshold']} → **{g['verdict']}**")
    lines.append(f"  - {g['confidence']}")
    lines.append("")
    lines.append("## 拒答正确率（负样本）")
    lines.append("")
    rf = report["refusal"]
    lines.append(
        f"- 拒答正确率：{rf['refuse_correct']}/{rf['negative_n']}"
        f"（{_fmt_rate(rf['accuracy'])}） · {rf['confidence']}"
    )
    lines.append(f"- 误答（负样本未拒答）：{rf['false_answer_ids'] or '无'}")
    lines.append(f"- 疑似误拒（正样本被拒答）：{rf['false_refusal_ids'] or '无'}")
    lines.append(f"- 分类口径：{rf['classification_note']}")
    lines.append("")
    lines.append("## 未达成项与原因")
    lines.append("")
    fails = report.get("failures") or []
    if not fails:
        lines.append("- 无")
    for f in fails:
        reasons = "；".join(f["fail_reasons"]) or "（无 fail_reasons）"
        lines.append(f"- {f['id']}（{f['quadrant']}）：{reasons}")
    lines.append("")
    lines.append("## 契约漂移")
    lines.append("")
    lines.append(f"- {report.get('contract_drift')}")
    lines.append("")
    return "\n".join(lines)


def write_text_atomic(path: Path, text: str) -> None:
    """原子写入（对齐 run_eval.write_report 形态）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def default_report_path() -> Path:
    """默认取 reports/r4*.yaml 最新一份（排除结案产物 r4_final_*）。"""
    cands = [
        p
        for p in DEFAULT_REPORTS_DIR.glob("r4*.yaml")
        if not p.name.startswith("r4_final_")
    ]
    if not cands:
        raise SystemExit(f"未找到源报告: {DEFAULT_REPORTS_DIR}/r4*.yaml")
    return max(cands, key=lambda p: p.stat().st_mtime)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="R-4 结案级汇总（逐象限聚合 + 门槛判定）")
    p.add_argument("--report", type=Path, default=None, help="源报告 YAML（默认最新 r4*.yaml）")
    p.add_argument("--out-yaml", type=Path, default=None, help="结案 YAML 输出路径")
    p.add_argument("--out-md", type=Path, default=None, help="结案 Markdown 输出路径")
    args = p.parse_args(argv)

    src = args.report or default_report_path()
    data = load_report(src)
    report = build_final_report(data, src)
    run_slug = str(report.get("run") or src.stem).replace("/", "_")
    out_yaml = args.out_yaml or DEFAULT_REPORTS_DIR / f"r4_final_{run_slug}.yaml"
    out_md = args.out_md or DEFAULT_REPORTS_DIR / f"r4_final_{run_slug}.md"

    write_text_atomic(out_yaml, yaml.safe_dump(report, allow_unicode=True, sort_keys=False))
    write_text_atomic(out_md, render_markdown(report))

    g = report["gates"]["zh2en_crosslingual_recall_at5"]
    rf = report["refusal"]
    print(
        f"SUMMARY zh2en={g['hits']}/{g['n']} gate={g['verdict']} "
        f"refuse={rf['refuse_correct']}/{rf['negative_n']} "
        f"out={out_yaml} , {out_md}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
