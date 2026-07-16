#!/usr/bin/env python3
"""Convert docs/_tech_graph/*.graph.yaml to a graph_v2 compatible graph.json."""

import datetime
import glob
import json
import os
import sys

import yaml


def main(graph_dir: str) -> None:
    graphs = []
    nodes = []
    edges = []

    for path in sorted(glob.glob(os.path.join(graph_dir, "*.graph.yaml"))):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        graph_id = data["graph_id"]
        graphs.append(
            {
                "id": graph_id,
                "title": data.get("title", ""),
                "source_yaml_path": os.path.basename(path),
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
        "freeze_id": f"OPS_DESK_API_TECH_GRAPH_FREEZE_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d')}_V1",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "graphs": graphs,
        "nodes": nodes,
        "edges": edges,
    }

    output_path = os.path.join(graph_dir, "graph.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(
        f"generated {output_path}: {len(graphs)} graphs, {len(nodes)} nodes, {len(edges)} edges"
    )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/_tech_graph")
