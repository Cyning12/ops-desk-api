#!/usr/bin/env python3
"""聚合 Host 大纲 + tech_graph → dist/site-data.json，并复制 web 静态壳。

用法（仓根）:
  python3 docs/arch-browser/scripts/build_site.py
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
ARCH = ROOT / "docs" / "arch-browser"
CATALOG = ARCH / "catalog"
WEB = ARCH / "web"
DIST = ARCH / "dist"
GRAPH_JSON = ROOT / "docs" / "_tech_graph" / "shared" / "graph.json"
MODULES_MD = ROOT / "docs" / "_tech_graph" / "l1" / "01_modules.md"
INDEX_DIR = ROOT / "docs" / "_tech_graph" / "l2" / "indexes"
MODULES_DIR = ROOT / "docs" / "discussions" / "agent-host-current-architecture" / "modules"
ARCH_OVERVIEW_MD = (
    ROOT / "docs" / "discussions" / "2026-09-24_agent-host_current_architecture_v1_zh.md"
)

# §1.2 flowchart 节点 id → Host #（与总览 MD 图一致；缺号由 chip 备用列表覆盖）
_CONCEPT_NODE_TO_HOST: dict[str, int] = {
    "REG": 1,
    "LOAD": 2,
    "VIS": 3,
    "PROMPT": 4,
    "SO": 5,
    "DG": 6,
    "EG": 7,
    "POLICY": 8,
    "MEM": 9,
    "EVAL": 10,
    "OBS": 11,
    "COST": 12,
    "SBX": 13,
    "SP": 14,
    "INTENT": 15,
    "OA": 17,
    "SA": 18,
    "FB_LLM": 19,
    "MREG": 20,
    "MROUTE": 21,
    "MDEG": 22,
    "MCACHE": 23,
    "MBUDGET": 24,
    "MEVAL": 25,
    "MSEC": 26,
    # PROV 四格对应本域接入面，统一落到 #30；垂域 27–29 见 chip
    "PV1": 30,
    "PV2": 30,
    "PV3": 30,
    "PV4": 30,
    "FB1": 31,
    "FB2": 32,
    "FB3": 33,
    "FB4": 34,
}


def _extract_first_mermaid(md_text: str) -> str:
    """抽出文档中首个 ```mermaid 代码块正文。"""
    m = re.search(r"```mermaid\s*\n(.*?)```", md_text, re.S)
    return (m.group(1).strip() if m else "")


def _display_status(raw: str) -> str:
    """对外展示标签：不适用 → 暂未排期（真值 crosswalk 仍可写不适用）。"""
    s = (raw or "未知").strip()
    if s == "不适用":
        return "暂未排期"
    return s


# ---- 演示面命名政策（D1 已锁 · 名实分离）----
# 只影响 Host 对照展示的 display 字段；tech_modules/flows/paths/code_paths 真值字段
# 原样保留，供反向索引（tech_to_host / flow→Host）与工程钻取层使用；crosswalk.yaml 不改。
_DEMO_HIDE_TECH: frozenset[str] = frozenset({"chat"})  # legacy 旧主线 · 演示面隐藏
_DEMO_TECH_LABEL: dict[str, str] = {
    "lg_rag": "Agent 工作台",
    "lc_evidence_chain": "证据链（工人）",
}
_DEMO_HIDE_FLOW: frozenset[str] = frozenset({"10_flow_chat"})
_DEMO_FLOW_LABEL: dict[str, str] = {
    "10_flow_lg_rag": "Agent 工作台（SSE 流式运行）",
    "10_flow_lc_evidence": "证据链（工人）",
}
_DEMO_HIDE_PATH_RE = re.compile(r"lg_rag|lc_evidence|ops/chat/")
_DEMO_TEXT_RE = re.compile(r"lg[_-]rag|LG RAG|LC Evidence|lc_evidence_chain|legacy Chat", re.I)


def _demo_text(s: str) -> str:
    """叙事展示文案去旧栈名（展示层改写；源文档/discussions 真值不动）。"""
    if not s:
        return s

    def _sub(m: re.Match) -> str:
        t = m.group(0).lower()
        if "evidence" in t:
            return "证据链"
        if "chat" in t:
            return "旧版对话"
        return "Agent Host"

    return _DEMO_TEXT_RE.sub(_sub, s)


def _demo_chips(items: list[str], hide: frozenset[str], labels: dict[str, str], kind: str) -> list[dict]:
    """生成演示面 chip（label 用演示口径，href 仍指工程钻取层真值 id）。"""
    out: list[dict] = []
    for it in items or []:
        if it in hide:
            continue
        out.append({"label": labels.get(it, it), "href": f"#/eng/{kind}/{it}"})
    return out


def _status_class_token(status: str) -> str:
    """与前端 badge / mermaid classDef 对齐。"""
    s = _display_status(status)
    if "已落地" in s:
        return "ok"
    if "部分" in s:
        return "partial"
    if "缺失" in s:
        return "missing"
    if s in {"暂未排期", "不适用"} or "排期" in s:
        return "na"
    return "na"


# 与 web/style.css badge 色一致（mermaid classDef）
_MERMAID_CLASSDEF = """
    classDef ok fill:#1e3a2f,stroke:#7ec8a3,color:#e7ecf3
    classDef partial fill:#3a2f1e,stroke:#d4a15b,color:#e7ecf3
    classDef missing fill:#3a1e1e,stroke:#d47a7a,color:#e7ecf3
    classDef na fill:#2a2f36,stroke:#6b7280,color:#9aa8bc
    classDef entry fill:#1e2a3a,stroke:#5b9fd4,color:#e7ecf3
""".strip(
    "\n"
)


def _concept_mermaid_with_clicks(body: str, status_by_host: dict[int, str]) -> str:
    """追加状态着色 classDef + click → #/host/{n}（需 mermaid securityLevel=loose）。"""
    if not body:
        return ""
    # 演示面口径（D1 锁定）：入口层节点标签去旧栈名；discussions 源 MD 不动
    body = re.sub(
        r"(\bE1\s*)\[[^\]]*\]",
        r'\1["用户请求 · Agent 工作台（SSE 流式运行）"]',
        body,
        count=1,
    )
    clicks: list[str] = []
    by_class: dict[str, list[str]] = {}
    for node_id, host_id in _CONCEPT_NODE_TO_HOST.items():
        if not re.search(rf"\b{re.escape(node_id)}\b", body):
            continue
        title = f"Host #{host_id}"
        clicks.append(f'    click {node_id} "#/host/{host_id}" "{title}"')
        cls = _status_class_token(status_by_host.get(host_id, "未知"))
        by_class.setdefault(cls, []).append(node_id)
    if re.search(r"\bE1\b", body):
        by_class.setdefault("entry", []).append("E1")

    parts = [body.rstrip(), "", "    %% arch-browser status colors + clicks", _MERMAID_CLASSDEF]
    for cls, nodes in by_class.items():
        parts.append(f"    class {','.join(nodes)} {cls}")
    if clicks:
        parts.append("")
        parts.extend(clicks)
    return "\n".join(parts) + "\n"


def _read_one_liner(md_path: Path) -> str:
    if not md_path.is_file():
        return ""
    text = md_path.read_text(encoding="utf-8")
    m = re.search(r"##\s*1\.\s*一句话\s*\n+([^\n#]+)", text)
    return (m.group(1).strip() if m else "")


def _read_code_paths(md_path: Path) -> str:
    if not md_path.is_file():
        return ""
    text = md_path.read_text(encoding="utf-8")
    m = re.search(r"\*\*包路径\*\*[：:]\s*`([^`]+)`", text)
    return (m.group(1).strip() if m else "")


def _read_gap(md_path: Path) -> str:
    if not md_path.is_file():
        return ""
    text = md_path.read_text(encoding="utf-8")
    m = re.search(r"##\s*5\.\s*相对目标的残余缺口\s*\n+(.*?)(?=\n##\s|\Z)", text, re.S)
    if not m:
        return ""
    body = m.group(1).strip()
    if body in {"—", "-", "无", ""}:
        return ""
    # 取首非空行
    for line in body.splitlines():
        line = line.strip().lstrip("-* ").strip()
        if line and line not in {"—", "-"}:
            return line
    return ""


def _parse_modules_table(md: str) -> list[dict]:
    """从 01_modules.md 抽 module_id 行（粗解析）。"""
    rows: list[dict] = []
    in_table = False
    for line in md.splitlines():
        if line.startswith("| module_id"):
            in_table = True
            continue
        if in_table:
            if not line.startswith("|"):
                break
            if re.match(r"^\|\s*-+", line):
                continue
            parts = [p.strip() for p in line.strip("|").split("|")]
            if len(parts) < 4:
                continue
            mid = parts[0].strip("` ")
            if not mid or mid == "module_id":
                continue
            rows.append(
                {
                    "module_id": mid,
                    "name": parts[1],
                    "paths_glob": parts[2].strip("` "),
                    "deps": parts[3],
                    "note": parts[4] if len(parts) > 4 else "",
                }
            )
    return rows


def _load_indexes() -> dict:
    out: dict[str, dict] = {}
    if not INDEX_DIR.is_dir():
        return out
    for path in sorted(INDEX_DIR.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception as exc:  # noqa: BLE001
            out[path.name] = {"error": str(exc)}
            continue
        # 压缩：只保留 by_path / by_symbol 的键列表 + 少量样例
        summary: dict = {
            "file": str(path.relative_to(ROOT)),
            "graph_id": data.get("graph_id"),
            "layer": data.get("layer"),
            "version": data.get("version"),
        }
        if "by_path" in data and isinstance(data["by_path"], dict):
            keys = list(data["by_path"].keys())
            summary["by_path_count"] = len(keys)
            summary["by_path"] = {
                k: data["by_path"][k]
                for k in keys[:80]  # 上限防爆
            }
        if "by_symbol" in data and isinstance(data["by_symbol"], dict):
            keys = list(data["by_symbol"].keys())
            summary["by_symbol_count"] = len(keys)
            summary["by_symbol"] = {
                k: data["by_symbol"][k]
                for k in keys[:80]
            }
        out[path.stem] = summary
    return out


def build() -> Path:
    outline = json.loads((CATALOG / "host_outline.json").read_text(encoding="utf-8"))
    crosswalk = yaml.safe_load((CATALOG / "crosswalk.yaml").read_text(encoding="utf-8"))
    graph = json.loads(GRAPH_JSON.read_text(encoding="utf-8"))
    modules_md = MODULES_MD.read_text(encoding="utf-8") if MODULES_MD.is_file() else ""
    eng_modules = _parse_modules_table(modules_md)

    # 充实 Host 模块：摘要 + crosswalk
    cw_by_id = {int(m["host_id"]): m for m in crosswalk.get("modules", [])}
    host_modules = []
    for mod in outline["modules"]:
        hid = int(mod["id"])
        slug = mod["slug"]
        md_path = MODULES_DIR / f"{slug}.md"
        cw = cw_by_id.get(hid, {})
        one = _read_one_liner(md_path)
        code_paths = _read_code_paths(md_path) or ", ".join(cw.get("paths") or [])
        gap_md = _read_gap(md_path)
        future = cw.get("future") or {}
        host_modules.append(
            {
                **mod,
                "status": _display_status(cw.get("status", "未知")),
                "status_raw": cw.get("status", "未知"),
                "one_liner": one,
                "code_paths": code_paths,
                "gap": gap_md or (future.get("gap_summary") or ""),
                "tech_modules": cw.get("tech_modules") or [],
                "flows": cw.get("flows") or [],
                "paths": cw.get("paths") or [],
                "sources": cw.get("sources")
                or [
                    f"docs/discussions/agent-host-current-architecture/modules/{slug}.md"
                ],
                "future_wave": future.get("wave"),
                "future_gap": future.get("gap_summary") or "",
                "mapped": bool(cw.get("tech_modules") or cw.get("flows") or cw.get("paths")),
                "source_md_rel": str(md_path.relative_to(ROOT)) if md_path.is_file() else None,
                # 演示面展示字段（旧栈名不出现在 Host 对照展示；上方真值字段不动）
                "display": {
                    "tech_chips": _demo_chips(
                        cw.get("tech_modules") or [], _DEMO_HIDE_TECH, _DEMO_TECH_LABEL, "module"
                    ),
                    "flow_chips": _demo_chips(
                        cw.get("flows") or [], _DEMO_HIDE_FLOW, _DEMO_FLOW_LABEL, "flow"
                    ),
                    "code_paths": ", ".join(
                        p
                        for p in re.split(r"[,，]\s*", code_paths)
                        if p and not _DEMO_HIDE_PATH_RE.search(p)
                    ),
                    "paths": [
                        p for p in (cw.get("paths") or []) if not _DEMO_HIDE_PATH_RE.search(p)
                    ],
                    "one_liner": _demo_text(one),
                    "gap": _demo_text(gap_md or (future.get("gap_summary") or "")),
                },
            }
        )

    # 按 graph_id 分桶 nodes/edges
    nodes_by_g: dict[str, list] = {}
    edges_by_g: dict[str, list] = {}
    for n in graph.get("nodes", []):
        nodes_by_g.setdefault(n["graph_id"], []).append(n)
    for e in graph.get("edges", []):
        edges_by_g.setdefault(e["graph_id"], []).append(e)

    graphs_detail = []
    for g in graph.get("graphs", []):
        gid = g["id"]
        graphs_detail.append(
            {
                **g,
                "nodes": nodes_by_g.get(gid, []),
                "edges": edges_by_g.get(gid, []),
            }
        )

    # reverse: tech_module → host_ids
    tech_to_host: dict[str, list[int]] = {}
    for hm in host_modules:
        for tm in hm["tech_modules"]:
            tech_to_host.setdefault(tm, []).append(hm["id"])
    hints = crosswalk.get("tech_module_hints") or {}
    for mid, hint in hints.items():
        tech_to_host.setdefault(mid, list(hint.get("host_ids") or []))

    overview_text = (
        ARCH_OVERVIEW_MD.read_text(encoding="utf-8") if ARCH_OVERVIEW_MD.is_file() else ""
    )
    status_by_host = {int(m["id"]): m["status"] for m in host_modules}
    concept_mermaid = _concept_mermaid_with_clicks(
        _extract_first_mermaid(overview_text), status_by_host
    )

    narrative_path = CATALOG / "home_narrative.json"
    home_narrative = (
        json.loads(narrative_path.read_text(encoding="utf-8"))
        if narrative_path.is_file()
        else {}
    )

    site = {
        "schema_version": "arch_browser_site_data_v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "freeze_id": graph.get("freeze_id"),
        "graph_generated_at": graph.get("generated_at"),
        "sources": {
            "host_outline": "docs/arch-browser/catalog/host_outline.json",
            "crosswalk": "docs/arch-browser/catalog/crosswalk.yaml",
            "home_narrative": "docs/arch-browser/catalog/home_narrative.json",
            "graph_json": "docs/_tech_graph/shared/graph.json",
            "modules_md": "docs/_tech_graph/l1/01_modules.md",
            "architecture_overview": "docs/discussions/2026-09-24_agent-host_current_architecture_v1_zh.md",
            "extension_strategy": "docs/discussions/2026-09-24_agent-host_extension_strategy_v1_zh.md",
        },
        "entry": outline.get("entry"),
        "layers": outline.get("layers"),
        "waves": outline.get("waves"),
        "home_narrative": home_narrative,
        "concept_mermaid": concept_mermaid,
        "host_modules": host_modules,
        "tech_module_hints": hints,
        "tech_to_host": tech_to_host,
        "eng_modules": eng_modules,
        "graphs": graphs_detail,
        "l2_indexes": _load_indexes(),
        "discipline": {
            "concept_truth": "docs/discussions/*",
            "engineering_truth": "docs/_tech_graph/shared/graph.json",
            "html_is": "衍生只读视图 · 禁止在 HTML 手改架构结论",
        },
    }

    DIST.mkdir(parents=True, exist_ok=True)
    out_json = DIST / "site-data.json"
    out_json.write_text(
        json.dumps(site, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # 复制 web 壳
    for name in ("index.html", "app.js", "style.css"):
        src = WEB / name
        if src.is_file():
            shutil.copy2(src, DIST / name)

    print(f"OK wrote {out_json.relative_to(ROOT)}")
    print(f"  freeze_id={site['freeze_id']}")
    print(f"  host_modules={len(host_modules)} graphs={len(graphs_detail)}")
    print(f"  concept_mermaid_chars={len(concept_mermaid)}")
    return out_json


if __name__ == "__main__":
    build()
