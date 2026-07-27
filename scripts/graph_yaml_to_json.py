#!/usr/bin/env python3
"""递归扫描 docs/_tech_graph/**/*.graph.yaml，写出 shared/graph.json（C1）。"""

from __future__ import annotations

import datetime
import json
import os
import sys
from pathlib import Path

import yaml


def _iter_graph_yaml(graph_dir: Path) -> list[Path]:
    return sorted(graph_dir.rglob("*.graph.yaml"))


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

    out = {
        "schema_version": "graph_v2",
        "freeze_id": (
            f"OPS_DESK_API_TECH_GRAPH_FREEZE_"
            f"{datetime.datetime.now(datetime.UTC).strftime('%Y%m%d')}_V1"
        ),
        "generated_at": datetime.datetime.now(datetime.UTC).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "graphs": graphs,
        "nodes": nodes,
        "edges": edges,
    }

    shared_dir = root / "shared"
    shared_dir.mkdir(parents=True, exist_ok=True)
    shared_path = shared_dir / "graph.json"
    with shared_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # C2 过渡：根目录双写副本，兼容仍读 docs/_tech_graph/graph.json 的工具
    root_path = root / "graph.json"
    with root_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(
        f"generated {shared_path} (+ root copy): "
        f"{len(graphs)} graphs, {len(nodes)} nodes, {len(edges)} edges"
    )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/_tech_graph")
