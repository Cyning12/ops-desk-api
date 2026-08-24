#!/usr/bin/env bash
set -euo pipefail

# graph-compile.sh
# 递归编译 docs/_tech_graph/**/*.graph.yaml -> 同目录 *.md
# graph.json 真值：shared/graph.json（根目录过渡双写）
#
# 2026-08-24：compile 后跑 graph_mermaid_normalize.py（IDE 预览兼容过渡层）。
# 备份：scripts/legacy/graph-compile.sh.20260824.pre-mermaid-normalize.bak
# 治根 / 反哺：docs/spec/SPEC-harness-to-dsh-kit-graph-migrate_v0.md（DEF-023）

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
GRAPH_DIR="${ROOT_DIR}/docs/_tech_graph"
GRAPH_JSON="${GRAPH_DIR}/shared/graph.json"

cd "${ROOT_DIR}"

# harness CLI --all 仅扫一层；对含 *.graph.yaml 的子目录逐个 compile/check（C4/B1）
GRAPH_INPUT_DIRS=()
while IFS= read -r dir; do
  [[ -n "${dir}" ]] || continue
  GRAPH_INPUT_DIRS+=("${dir}")
done < <(
  find "${GRAPH_DIR}" -type f -name '*.graph.yaml' -print |
    sed 's|/[^/]*\.graph\.yaml$||' |
    sort -u
)

if [[ ${#GRAPH_INPUT_DIRS[@]} -eq 0 ]]; then
  echo "error: no *.graph.yaml under ${GRAPH_DIR}" >&2
  exit 1
fi

echo "[harness] compiling graph yaml -> md (${#GRAPH_INPUT_DIRS[@]} dir(s))"
for dir in "${GRAPH_INPUT_DIRS[@]}"; do
  rel="${dir#"${ROOT_DIR}"/}"
  echo "  compile --input ${rel}"
  npx @cyning/harness graph yaml compile --input "${dir}" --all
done

echo "[normalize] Mermaid IDE preview compatibility (post-compile)"
python3 "${SCRIPT_DIR}/graph_mermaid_normalize.py" "${GRAPH_DIR}"

echo "[custom] generating shared/graph.json from yaml sources (recursive)"
python3 "${SCRIPT_DIR}/graph_yaml_to_json.py" "${GRAPH_DIR}"

echo "[harness] checking graph consistency"
for dir in "${GRAPH_INPUT_DIRS[@]}"; do
  rel="${dir#"${ROOT_DIR}"/}"
  echo "  check --input ${rel}"
  npx @cyning/harness graph yaml check --input "${dir}" --all --graph-json "${GRAPH_JSON}"
done

echo "[normalize] verify mermaid fences"
python3 "${SCRIPT_DIR}/graph_mermaid_normalize.py" --check "${GRAPH_DIR}"

echo "done"
