#!/usr/bin/env bash
#
# Capability 层一键验收。
#
# 一条命令跑完五层，出一份**带证据**的 Markdown 报告，退出码可直接接 CI：
#
#   0  全部通过
#   1  有条目失败
#   2  前置条件不满足（缺 venv 等）
#
# 五层分开报，**不合并成一个"通过率"**——它们回答的是五个不同问题：
#   单测      内部逻辑对不对
#   黑盒题集  出口产出有没有变
#   红线      有没有踩到否决项
#   DB 持久化 跨实例那条链路是不是真的通
#   桩服务联调 **真的发得出网吗**（唯一能证明这点的）
#
# 用法：
#   scripts/acceptance/capability_acceptance.sh
#   MOCK_OA_DIR=/path/to/ops-desk-mock-oa MOCK_OA_PORT=18080 scripts/.../capability_acceptance.sh
#   SKIP_SMOKE=1 scripts/.../capability_acceptance.sh     # 只跑不需要桩服务的四层

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MOCK_OA_DIR="${MOCK_OA_DIR:-$ROOT/../ops-desk-mock-oa}"
MOCK_OA_PORT="${MOCK_OA_PORT:-18080}"
MOCK_OA_JAR="mock-oa-0.0.1-SNAPSHOT.jar"
VENV_PY="$ROOT/.venv/bin/python"
# 报告写到独立目录：`reports/` 里有 **tracked 的基准产物**（qdrant/r4 等），别往里塞
REPORT_DIR="${ACCEPTANCE_REPORT_DIR:-$ROOT/.acceptance-reports}"
STAMP="$(date +%Y%m%d-%H%M%S)"
REPORT="$REPORT_DIR/capability-acceptance-$STAMP.md"
TMP="$(mktemp -d)"
MOCK_PID=""

declare -a ROWS=()
FAILED=0
SKIPPED=0

cleanup() {
  [[ -n "$MOCK_PID" ]] && kill "$MOCK_PID" 2>/dev/null
  rm -rf "$TMP"
}
trap cleanup EXIT

hr() { printf '─%.0s' {1..72}; echo; }

# 等**真实监听**：不能在用 curl——有出口代理时连未监听端口也返 502，而 curl 退出码仍是 0
wait_listen() {
  local i
  for i in $(seq 1 40); do
    lsof -nP -iTCP:"$MOCK_OA_PORT" -sTCP:LISTEN >/dev/null 2>&1 && return 0
    sleep 1
  done
  return 1
}

run_step() {
  local layer="$1" name="$2" note="$3"
  shift 3
  local log="$TMP/$(echo "$name" | tr -c 'a-zA-Z0-9' '_').log"
  printf '▶ %-10s %-28s ' "$layer" "$name"
  "$@" >"$log" 2>&1
  local code=$?
  if [[ $code -eq 0 ]]; then
    echo "PASS"
    ROWS+=("| $layer | $name | ✅ PASS | ${note} |")
  else
    echo "FAIL (exit=$code)"
    ROWS+=("| $layer | $name | ❌ FAIL | 证据：\`$(basename "$log")\` · ${note} |")
    FAILED=$((FAILED + 1))
  fi
  echo "----- [$layer/$name] exit=$code -----" >>"$TMP/full.log"
  cat "$log" >>"$TMP/full.log"
}

skip_step() {
  local layer="$1" name="$2" why="$3"
  printf '› %-10s %-28s SKIP (%s)\n' "$layer" "$name" "$why"
  ROWS+=("| $layer | $name | ⏭️ SKIP | $why |")
  SKIPPED=$((SKIPPED + 1))
}

echo "Capability 层验收 · $(date '+%F %T')"
hr

# ---------------- 前置条件 ----------------

if [[ ! -x "$VENV_PY" ]]; then
  echo "缺 venv：${VENV_PY}（先 cd ${ROOT} && python -m venv .venv && .venv/bin/pip install -e '.[dev]'）" >&2
  exit 2
fi
mkdir -p "$REPORT_DIR"

# 能力清单：只读三项（联调用）
export OPS_CAPABILITY_EXTRA_MANIFESTS="$ROOT/app/ops/capability/manifests/oa.readonly.v1.yaml"
export OPS_CAP_CRED_OA_GATEWAY_TOKEN="${OPS_CAP_CRED_OA_GATEWAY_TOKEN:-local-dev-token}"
export OA_BASE="${OA_BASE:-http://127.0.0.1:$MOCK_OA_PORT}"
export PYTHONPATH="$ROOT"
export PYTEST_ADDOPTS="--basetemp=$ROOT/.pytest-tmp -q"

# 前置提示：桩服务的 jar 需要 Java 25+，而系统默认 java 往往更低。
# 不设 JAVA_HOME 时联调层会"起不来但看不出为什么"——所以先说出来。
if [[ -z "${JAVA_HOME:-}" ]]; then
  echo "⚠️  JAVA_HOME 未设置：桩服务 jar 需要 Java 25+，系统默认 java 可能是 21 → 联调层会跳过"
  echo "    正确写法：export JAVA_HOME=/opt/homebrew/opt/openjdk"
  echo
fi

# ---------------- 五层 ----------------

run_step "单测" "capability 单测" "内部逻辑" \
  "$VENV_PY" -m pytest "$ROOT/tests" -k capability

run_step "题集" "黑盒题集（含基线 diff）" "出口产出漂移" \
  "$VENV_PY" -m pytest "$ROOT/tests/eval/test_eval_capability_golden.py"

run_step "红线" "红线（否决项）" "7 条 hard line" \
  "$VENV_PY" -m pytest "$ROOT/tests" -m redline

run_step "持久化" "DB 版 store/sink" "跨实例防重" \
  "$VENV_PY" -m pytest "$ROOT/tests/test_capability_persistence_db.py"

# ---------------- 桩服务联调（唯一能证明"真发得出去"的一层）----------------

if [[ "${SKIP_SMOKE:-0}" == "1" ]]; then
  skip_step "联调" "真桩服务 26 项" "SKIP_SMOKE=1"
elif [[ ! -d "$MOCK_OA_DIR" ]]; then
  skip_step "联调" "真桩服务 26 项" "找不到桩服务目录 $MOCK_OA_DIR"
elif [[ ! -f "$MOCK_OA_DIR/target/$MOCK_OA_JAR" ]]; then
  skip_step "联调" "真桩服务 26 项" "桩服务未构建（先 cd $MOCK_OA_DIR && mvn package -DskipTests）"
else
  echo "▶ 联调       启动桩服务 ..."
  (
    cd "$MOCK_OA_DIR" || exit 1
    if [[ -n "${JAVA_HOME:-}" ]]; then JAVA="$JAVA_HOME/bin/java"; else JAVA="java"; fi
    nohup "$JAVA" -jar "target/$MOCK_OA_JAR" \
      --server.port="$MOCK_OA_PORT" --server.address=127.0.0.1 \
      >"$TMP/mock-oa.log" 2>&1 &
    echo $!
  ) >"$TMP/mock.pid"
  MOCK_PID="$(cat "$TMP/mock.pid")"

  if wait_listen; then
    echo "  （桩服务已监听 ${MOCK_OA_PORT}，pid=${MOCK_PID}）"
    run_step "联调" "真桩服务 26 项" "真实出网" \
      "$VENV_PY" "$MOCK_OA_DIR/scripts/agent-integration-smoke.py"
  else
    skip_step "联调" "真桩服务 26 项" "桩服务 40s 内未监听 ${MOCK_OA_PORT}（原因见下方日志）"
    echo
    echo "  ── 桩服务启动日志（最后 20 行）──"
    tail -20 "$TMP/mock-oa.log" 2>/dev/null | sed 's/^/  | /' || echo "  | (无日志)"
    echo "  ── 常见原因 ──"
    echo "  | 1) JAVA_HOME 没设/低于 25 → jar 需 Java 25+，系统默认 java 可能是 21"
    echo "  |    正确写法：export JAVA_HOME=/opt/homebrew/opt/openjdk"
    echo "  | 2) 端口被占：lsof -nP -iTCP:${MOCK_OA_PORT} -sTCP:LISTEN"
    echo "  | 3) jar 未构建：cd ${MOCK_OA_DIR} && mvn package -DskipTests"
    echo
    {
      echo
      echo "### 联调层跳过原因：桩服务启动日志"
      echo
      echo '```'
      tail -40 "$TMP/mock-oa.log" 2>/dev/null || echo "(无日志)"
      echo '```'
    } >>"$TMP/mock-failure.md"
  fi
fi

rm -rf "$ROOT/.pytest-tmp"

# ---------------- 报告 ----------------

{
  echo "# Capability 层验收报告"
  echo
  echo "- 时间：$(date '+%F %T')"
  echo "- 仓库：\`$ROOT\`"
  echo "- 桩服务：\`$MOCK_OA_DIR\` @ 127.0.0.1:$MOCK_OA_PORT"
  echo "- 结论：**$([[ $FAILED -eq 0 ]] && echo '通过' || echo '不通过')**（失败 ${FAILED} · 跳过 ${SKIPPED}）"
  echo
  echo "> 五层分开看，**不合并成一个通过率**——它们回答五个不同问题。"
  echo "> 跳过 ≠ 通过：桩服务未就绪时联调被显式标为 SKIP，而不是记成失败、也不假装通过。"
  echo
  echo "| 层 | 内容 | 结果 | 说明 |"
  echo "|---|---|---|---|"
  printf '%s\n' "${ROWS[@]}"
  echo
  echo "## 明细"
  echo
  echo '```'
  cat "$TMP/full.log" 2>/dev/null || echo "(无)"
  echo '```'
  # 联调层跳过时把桩服务的启动日志一并附上——否则"未监听"就成了无从下手的结论
  [[ -f "$TMP/mock-failure.md" ]] && cat "$TMP/mock-failure.md"
} >"$REPORT"

hr
printf '失败 %d · 跳过 %d\n' "$FAILED" "$SKIPPED"
echo "报告：$REPORT"

[[ $FAILED -gt 0 ]] && exit 1
exit 0
