#!/usr/bin/env python3
"""Ops Desk GitHub sync sender：拉取 kimi-code Issue/PR 并 POST /api/ops/admin/sync。

环境：
  GITHUB_TOKEN           GitHub 读取 token
  OPS_API_BASE_URL       API 根（脚本拼 /api/ops/admin/sync）
  OPS_ADMIN_SYNC_TOKEN   Bearer（与 API 同源）
  OPS_SYNC_REPO          默认 MoonshotAI/kimi-code
  OPS_SCAN_INDEX_PATH    可选 md；缺失则 payload 不带 scan_snapshot
  OPS_GRAPH_JSON_PATH    可选 graph.json；缺失则不带 graph_snapshot
  SYNC_MODE              incremental | full（可被 --mode 覆盖）
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ops.admin.sender.runner import run_sync  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch GitHub issues/PRs and POST SyncPayload to ops-desk-api"
    )
    parser.add_argument(
        "--mode",
        choices=("incremental", "full"),
        default=None,
        help="incremental=utcnow-48h；full=since 为空。默认读 SYNC_MODE 或 incremental",
    )
    args = parser.parse_args(argv)
    sync_type = (args.mode or os.getenv("SYNC_MODE") or "incremental").strip()
    if sync_type not in ("incremental", "full"):
        print(f"invalid SYNC_MODE: {sync_type}", file=sys.stderr)
        return 1
    return run_sync(sync_type=sync_type)


if __name__ == "__main__":
    sys.exit(main())
