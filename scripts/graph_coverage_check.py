#!/usr/bin/env python3
"""Graph 语义覆盖检查（一期 · warn only，exit 恒 0）。

spec 真值：docs/spec/inform-graph-backfill/ci/coverage_check.md

背景：
  tech-graph.yml / graph-compile.sh 不读 app/ 源码，漏画 flow 时 compile 仍可 exit 0。
  本脚本补「语义覆盖」可观测性：对比 app/ops/router.py 的 include_router 集合
  与 G-L0 00_main.graph.yaml 的子路由节点，并做旁路 flow / 模块表 / retrieve 节点抽查。

规则（一期 · 全部 warn）：
  R1  router.py 每个 include 在 G-L0 有对应子路由节点（反向：多余节点也 warn）
  R2  00_main 中 ::triggers 指向的 10_flow_* yaml 必须存在
  R3  01_modules.md 中 chat/rag/lc/lg 行备注含 START→ 长拓扑但无对应 flow 文件
  R4  10_flow_chat.graph.yaml 须含 retrieve 节点 id

二期（不做）：anchors 行号比对、indexes↔implementedBy 双向 diff、全仓 glob 覆盖、
--strict 门禁化（维护者拍板前 CI 以 || true / continue-on-error 接入）。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

IMPORT_RE = re.compile(r"^from (app\.ops[\w.]*) import router as (\w+)", re.M)
INCLUDE_RE = re.compile(r"^router\.include_router\((\w+)\)", re.M)
FLOW_LABEL_RE = re.compile(r"^>\.\./l1/(10_flow_[\w]+)\.md$")
START_TOPO_RE = re.compile(r"START\s*→")


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _router_includes(router_py: Path) -> list[dict]:
    """解析 app/ops/router.py：import 别名 → 模块路径；include_router 调用序列。"""
    text = router_py.read_text(encoding="utf-8")
    imports = {m.group(2): m.group(1) for m in IMPORT_RE.finditer(text)}
    includes = []
    for m in INCLUDE_RE.finditer(text):
        var = m.group(1)
        line = text.count("\n", 0, m.start()) + 1
        includes.append({"var": var, "module": imports.get(var, ""), "line": line})
    return includes


def _node_candidates(var: str, module: str) -> set[str]:
    """include 变量名 → G-L0 子路由节点 id 候选集。

    约定（现行 00_main 节点命名）：
      auth_router→auth · admin_sync_router→admin_sync · chat_router→chat_router
    """
    cands = {var}
    if var.endswith("_router"):
        cands.add(var[: -len("_router")])
    parts = module.split(".")  # app.ops.<domain>[.x]
    if len(parts) >= 3 and parts[2]:
        domain = parts[2]
        cands.add(domain)
        cands.add(f"{domain}_router")
    return cands


def rule_r1(root: Path, warns: list[str]) -> None:
    router_py = root / "app/ops/router.py"
    main_yaml = root / "docs/_tech_graph/l0/00_main.graph.yaml"
    includes = _router_includes(router_py)
    g0 = _load_yaml(main_yaml)
    sub_nodes = [e["to"] for e in g0.get("edges", []) if e.get("from") == "ops_router"]

    matched: set[str] = set()
    for inc in includes:
        cands = _node_candidates(inc["var"], inc["module"])
        hit = next((n for n in sub_nodes if n in cands), None)
        if hit is None:
            warns.append(
                f"R1 router.py:{inc['line']} include_router({inc['var']}) "
                f"在 00_main 无对应子路由节点（候选 {sorted(cands)}）"
            )
        else:
            matched.add(hit)
    for node in sub_nodes:
        if node not in matched:
            warns.append(f"R1 00_main 子路由节点 {node!r} 在 router.py 无对应 include_router（多余？）")

    print(f"[R1] router.py includes={len(includes)} · 00_main 子路由节点={len(sub_nodes)}")


def rule_r2(root: Path, warns: list[str]) -> None:
    main_yaml = root / "docs/_tech_graph/l0/00_main.graph.yaml"
    g0 = _load_yaml(main_yaml)
    nodes = {n["id"]: n for n in g0.get("nodes", [])}
    checked = 0
    for e in g0.get("edges", []):
        if e.get("mark") != "::triggers":
            continue
        target = nodes.get(e.get("to"), {})
        m = FLOW_LABEL_RE.match(str(target.get("label", "")))
        if not m:
            continue
        checked += 1
        flow_yaml = root / "docs/_tech_graph/l1" / f"{m.group(1)}.graph.yaml"
        if not flow_yaml.is_file():
            warns.append(f"R2 00_main ::triggers → {e['to']} 指向的 {flow_yaml.relative_to(root)} 不存在")
    print(f"[R2] ::triggers flow 引用检查 {checked} 处")


def _module_rows(modules_md: Path) -> list[tuple[str, str]]:
    """解析 01_modules.md 模块表：返回 (module_id, 备注) 列表（按未转义 | 切列）。"""
    rows = []
    for line in modules_md.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `"):
            continue
        cells = re.split(r"(?<!\\)\|", line)
        if len(cells) < 6:
            continue
        module_id = cells[1].strip().strip("`")
        remark = cells[5].strip()
        rows.append((module_id, remark))
    return rows


def rule_r3(root: Path, warns: list[str]) -> None:
    modules_md = root / "docs/_tech_graph/l1/01_modules.md"
    checked = 0
    for module_id, remark in _module_rows(modules_md):
        if not (module_id in ("chat", "rag") or module_id.startswith(("lc", "lg"))):
            continue
        if not START_TOPO_RE.search(remark):
            continue
        checked += 1
        cands = [root / "docs/_tech_graph/l1" / f"10_flow_{module_id}.graph.yaml"]
        if module_id.endswith("_chain"):
            cands.append(
                root / "docs/_tech_graph/l1" / f"10_flow_{module_id[: -len('_chain')]}.graph.yaml"
            )
        if not any(p.is_file() for p in cands):
            warns.append(
                f"R3 01_modules 行 {module_id!r} 备注含 START→ 长拓扑但无对应 10_flow_* yaml"
            )
    print(f"[R3] 模块表 START→ 长拓扑行检查 {checked} 行")


def rule_r4(root: Path, warns: list[str]) -> None:
    chat_yaml = root / "docs/_tech_graph/l1/10_flow_chat.graph.yaml"
    if not chat_yaml.is_file():
        warns.append("R4 10_flow_chat.graph.yaml 不存在")
        print("[R4] 10_flow_chat retrieve 节点检查（文件缺失）")
        return
    g = _load_yaml(chat_yaml)
    ids = {n.get("id") for n in g.get("nodes", [])}
    if "retrieve" not in ids:
        warns.append("R4 10_flow_chat.graph.yaml 缺 retrieve 节点 id（RAG 检索链未入图）")
    print(f"[R4] 10_flow_chat 节点数={len(ids)} · retrieve={'在' if 'retrieve' in ids else '缺'}")


def main() -> int:
    ap = argparse.ArgumentParser(description="tech graph 语义覆盖检查（一期 warn only）")
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument(
        "--strict",
        action="store_true",
        help="二期门禁化预留：有 warn 时 exit 1（维护者拍板前勿接入 CI）",
    )
    args = ap.parse_args()
    root = args.root.resolve()

    if yaml is None:
        print("[ERROR] 需要 PyYAML：pip install pyyaml", file=sys.stderr)
        return 2

    warns: list[str] = []
    print(f"== graph coverage check (warn only) · root={root} ==")
    for rule in (rule_r1, rule_r2, rule_r3, rule_r4):
        rule(root, warns)

    print("-- 结果 --")
    if warns:
        for w in warns:
            print(f"[WARN] {w}")
        print(f"共 {len(warns)} 条 warn（一期不 fail；--strict 为二期拍板项）")
    else:
        print("[OK] 无缺失/多余：router includes 与 G-L0 子路由节点一致，flow 引用齐全")
    return 1 if (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
