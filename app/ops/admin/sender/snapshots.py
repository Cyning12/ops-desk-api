"""可选 scan / graph 快照文件；缺失则返回 None，不失败。"""

from __future__ import annotations

import json
from pathlib import Path

from app.ops.admin.schema import GraphSnapshotIn, ScanSnapshotIn


def load_scan_snapshot(path: str | None) -> ScanSnapshotIn | None:
    """读 md → ScanSnapshotIn.raw_markdown；文件缺失返回 None。"""
    if not path:
        return None
    file_path = Path(path)
    if not file_path.is_file():
        return None
    return ScanSnapshotIn(raw_markdown=file_path.read_text(encoding="utf-8"))


def load_graph_snapshot(path: str | None) -> GraphSnapshotIn | None:
    """读 json → GraphSnapshotIn.payload；文件缺失返回 None。"""
    if not path:
        return None
    file_path = Path(path)
    if not file_path.is_file():
        return None
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"graph json 根必须是 object: {path}")
    return GraphSnapshotIn(payload=payload)
