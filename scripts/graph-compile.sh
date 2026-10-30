#!/usr/bin/env bash
set -euo pipefail

# graph-compile.sh
# 递归编译 docs/_tech_graph/**/*.graph.yaml -> 同目录 *.md
# graph.json 真值：shared/graph.json（根目录双写已于 tech-graph-legacy-cleanup 移除）
#
# 2026-08-25：命令面正式切换 @cyning/harness -> spec-wave
#   （SPEC-harness-to-dsh-kit-graph-migrate_v0 §6；kit 1.6.1 已修
#   DEF-023/031/032/033，emit 直接满足 IDE 预览契约，见
#   docs/harness/evidence/FEEDBACK_dsh_coding_kit_1_6_1_from_ops_desk_api_20260825.md）。
#   normalize 过渡层降级为 check-only 护栏（只校验不改写）。
#   graph.json 仍由本仓 graph_yaml_to_json.py 生成（kit export 与本仓 json
#   存在 layer 字段 / freeze_id 语义差异，见 task 报告）。
# 回退口：GRAPH_CLI 环境变量切换 CLI（默认 spec-wave；SPEC §6.2）：
#   GRAPH_CLI=@cyning/harness ./scripts/graph-compile.sh
#   注意：harness emit 不满足 IDE 预览契约；legacy 脚本备份已清理。
# 2026-10-11：GRAPH_CLI 默认值钉 spec-wave@3.0.1（对齐 package.json 与
#   .github/workflows/lint-wiki-delta.yml 既有钉法）——裸 npx spec-wave 随上游
#   漂移：spec-wave 3.2.0 发布致 check/tech-graph 红（implementedBy object
#   schema 收紧 · 非本仓 diff 引入；master run 38069798037 装 3.1.0 仍绿）。
#   GRAPH_CLI 环境变量回退口保留（显式覆盖优先）。
# 2026-10-17：GRAPH_CLI 默认值钉版对齐 3.3.0（task ci-specwave-pin-align ·
#   对齐 package.json/.coding-kit/manifest.json/pnpm-lock 已生效版本，消除
#   CI/脚本钉版分裂致的形状闸静默降级；历史钉法缘由见上 2026-10-11 段）。
# 2026-10-30：GRAPH_CLI 默认值钉版对齐 3.5.0（task specwave-upgrade-3-5-0 ·
#   对齐 package.json/.coding-kit/manifest.json 已生效版本；3.4.0 review-gates
#   址B 双址扫描 + 3.5.0 图谱锚点检查 graph_anchor 条件触发，无强制迁移）。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
GRAPH_DIR="${ROOT_DIR}/docs/_tech_graph"
GRAPH_JSON="${GRAPH_DIR}/shared/graph.json"
GRAPH_CLI="${GRAPH_CLI:-spec-wave@3.5.0}"

cd "${ROOT_DIR}"

# CLI --all 仅扫一层；对含 *.graph.yaml 的子目录逐个 compile/check（C4/B1）
GRAPH_INPUT_DIRS=()
while IFS= read -r dir; do
  [[ -n "$dir" ]] || continue
  GRAPH_INPUT_DIRS+=("$dir")
done < <(
  find "${GRAPH_DIR}" -type f -name '*.graph.yaml' -print |
    sed 's|/[^/]*\.graph\.yaml$||' |
    sort -u
)

if [[ ${#GRAPH_INPUT_DIRS[@]} -eq 0 ]]; then
  echo "error: no *.graph.yaml under ${GRAPH_DIR}" >&2
  exit 1
fi

echo "[${GRAPH_CLI}] compiling graph yaml -> md (${#GRAPH_INPUT_DIRS[@]} dir(s))"
for dir in "${GRAPH_INPUT_DIRS[@]}"; do
  rel="${dir#"${ROOT_DIR}"/}"
  echo "  compile --input $rel"
  npx "${GRAPH_CLI}" graph yaml compile --input "$dir" --all
done

echo "[custom] generating shared/graph.json from yaml sources (recursive)"
python3 "${SCRIPT_DIR}/graph_yaml_to_json.py" "${GRAPH_DIR}"

echo "[${GRAPH_CLI}] checking graph consistency"
for dir in "${GRAPH_INPUT_DIRS[@]}"; do
  rel="${dir#"${ROOT_DIR}"/}"
  echo "  check --input $rel"
  npx "${GRAPH_CLI}" graph yaml check --input "$dir" --all --graph-json "${GRAPH_JSON}"
done

echo "[normalize] guard: verify mermaid fences (check-only, no rewrite)"
python3 "${SCRIPT_DIR}/graph_mermaid_normalize.py" --check "${GRAPH_DIR}"

echo "done"
