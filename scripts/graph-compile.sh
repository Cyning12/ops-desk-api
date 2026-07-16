#!/usr/bin/env bash
set -euo pipefail

# graph-compile.sh
# 编译 docs/_tech_graph/*.graph.yaml -> *.md + graph.json

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
GRAPH_DIR="${ROOT_DIR}/docs/_tech_graph"

cd "${ROOT_DIR}"

echo "[harness] compiling graph yaml -> md"
npx @cyning/harness graph yaml compile --input "${GRAPH_DIR}" --all

echo "[custom] generating graph.json from yaml sources"
python3 "${SCRIPT_DIR}/graph_yaml_to_json.py" "${GRAPH_DIR}"

echo "[harness] checking graph consistency"
npx @cyning/harness graph yaml check --input "${GRAPH_DIR}" --all

echo "done"
