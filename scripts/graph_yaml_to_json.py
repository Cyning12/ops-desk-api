#!/usr/bin/env python3
"""递归扫描 docs/_tech_graph/**/*.graph.yaml，写出 shared/graph.json（真值）。

确定性纪律（task_graph_json_freeze_date_pin · 2026-10-17）：
freeze_id / generated_at 由 graphs/nodes/edges 规范化内容 sha256 派生
（对齐图谱编译产出 md `generated_at: sha256-<16hex>` 内容戳先例，
docs/_tech_graph/shared/99_mermaid_protocol.md:137），同输入字节级稳定
（跨日 / 跨机 / CI/本地一致）。本脚本生成路径禁止 wall-clock 时钟
调用（时钟模块整体不导入）；grep 时钟调用零命中为可复跑防回归断言
（TC-5）。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml


def _iter_graph_yaml(graph_dir: Path) -> list[Path]:
    return sorted(graph_dir.rglob("*.graph.yaml"))


def _content_digest(
    schema_version: str, graphs: list[dict], nodes: list[dict], edges: list[dict]
) -> str:
    """graphs/nodes/edges 规范化内容 sha256 前 16 hex（确定性内容戳）。

    序列化钉死 sort_keys / separators / ensure_ascii，列表序由
    _iter_graph_yaml 的 sorted 相对路径决定（绝对路径仅共同前缀，
    不影响相对排序），同输入跨机字节级稳定（FP-3）。
    """
    canonical = json.dumps(
        {
            "schema_version": schema_version,
            "graphs": graphs,
            "nodes": nodes,
            "edges": edges,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def main(graph_dir: str) -> None:
    root = Path(graph_dir)
    graphs: list[dict] = []
    nodes: list[dict] = []
    edges: list[dict] = []

    for path in _iter_graph_yaml(root):
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        graph_id = data["graph_id"]
        rel = path.relative_to(root).as_posix()
        graphs.append(
            {
                "id": graph_id,
                "title": data.get("title", ""),
                "source_yaml_path": rel,
                "layer": data.get("layer") or data.get("primary_layer") or "",
            }
        )

        for node in data.get("nodes", []):
            nodes.append(
                {
                    "graph_id": graph_id,
                    "id": node["id"],
                    "label": node.get("label", ""),
                }
            )

        for edge in data.get("edges", []):
            edges.append(
                {
                    "graph_id": graph_id,
                    "from": edge["from"],
                    "to": edge["to"],
                    "mark": edge.get("mark", "->"),
                    "type": edge.get("type", "depends_on"),
                    "label": edge.get("label", ""),
                    "anchors": edge.get("anchors", []),
                    "sync": True,
                }
            )

    digest = _content_digest("graph_v2", graphs, nodes, edges)
    out = {
        "schema_version": "graph_v2",
        # 骨架兼容：前缀 OPS_DESK_API_TECH_GRAPH_FREEZE_ 与 _V1 后缀语义不破
        # （FP-1）；日期段替换为内容戳，内容变则 freeze_id 变。
        "freeze_id": f"OPS_DESK_API_TECH_GRAPH_FREEZE_{digest}_V1",
        # 对齐 md generated_at 内容戳先例（sha256-<16hex>）。
        "generated_at": f"sha256-{digest}",
        "graphs": graphs,
        "nodes": nodes,
        "edges": edges,
    }

    shared_dir = root / "shared"
    shared_dir.mkdir(parents=True, exist_ok=True)
    shared_path = shared_dir / "graph.json"
    text = json.dumps(out, ensure_ascii=False, indent=2)
    shared_path.write_text(text, encoding="utf-8")

    print(
        f"generated {shared_path}: "
        f"{len(graphs)} graphs, {len(nodes)} nodes, {len(edges)} edges"
    )
    # N-3 取证：stdout 打产出 sha256，40 可从 CI run 日志与本地比对（TC-4）。
    print(f"  freeze_id={out['freeze_id']}")
    print(f"  graph.json sha256={hashlib.sha256(text.encode('utf-8')).hexdigest()}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/_tech_graph")
