#!/usr/bin/env bash
# 聚合 Host 大纲 + tech_graph → docs/arch-browser/dist/
# 建议在 ./scripts/graph-compile.sh 之后运行（本脚本不替代 compile）。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
exec python3 docs/arch-browser/scripts/build_site.py
