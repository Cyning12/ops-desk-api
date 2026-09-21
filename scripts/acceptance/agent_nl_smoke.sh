#!/bin/bash
# 自然语言入口 · 端到端冒烟（起 API → 等就绪 → 登录 → 提交自然语言 → 收 SSE → 杀进程）
#
# 与其它验收脚本的分工：
#   A 九层 / B 落库 / C 出网 / D 审批 / E 回流 —— 单测级、CD 级或**进程内直调**
#   本脚本                                      —— **唯一**从自然语言入口进去的那条
#
# ⚠️ 会**真的调用 LLM**（花钱、有延迟，单次通常 10–60s）。
# 默认 query 只依赖 builtin 的 5 个 local_fn 能力，所以不需要 mock-oa / OA 凭证。
#
# 用法：
#   ./scripts/acceptance/agent_nl_smoke.sh
#   ./scripts/acceptance/agent_nl_smoke.sh --query "查一下 issue 12 的状态" --expect-tool
#   OPS_NL_SMOKE_TRACING=1 ./scripts/acceptance/agent_nl_smoke.sh   # 保留 .env 里的 trace 上报
set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY="$ROOT/.venv/bin/python"
LOGDIR="$(mktemp -d)"

export AGENT_PORT="${AGENT_PORT:-8123}"

# 出口代理会把打 127.0.0.1 的请求送到代理去（拿到看不懂的 502）
export no_proxy="127.0.0.1,localhost"
export NO_PROXY="127.0.0.1,localhost"

# 追踪：**默认跟随 .env**（这条冒烟是给人看的，trace 正是要看的东西之一）。
# 想要"零外部副作用"就跑 `OPS_NL_SMOKE_NO_TRACING=1`。
# 机制：空值同样能压住 .env —— python-dotenv 的 override=False 只认"键是否存在"。
if [ "${OPS_NL_SMOKE_NO_TRACING:-0}" = "1" ]; then
  export OPS_CHAT_TRACER=""
fi

require_free_port() {
  # ⚠️ 起服务前必须确认端口空着：uvicorn bind 失败会秒退，而就绪探针是"内容型"的，
  # 一个**残留的旧服务**同样能满足它 ⇒ 整轮在跟别人的服务说话。
  local p="$1"
  if lsof -nP -iTCP:"$p" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "端口 ${p} 已被占用 —— 本次要起的 API 起不来，但残留进程会骗过就绪探针。"
    echo "占用者："
    lsof -nP -iTCP:"$p" -sTCP:LISTEN | tail -n +2
    echo "先清掉它，或换端口（AGENT_PORT=8124 …）再跑。"
    return 1
  fi
  return 0
}

wait_ready() {
  local url="$1" needle="$2" i
  for i in $(seq 1 120); do
    if "$PY" - "$url" "$needle" <<'PYEOF' 2>/dev/null
import json, sys, urllib.request
url, needle = sys.argv[1], sys.argv[2]
o = urllib.request.build_opener(urllib.request.ProxyHandler({}))
try:
    if needle == "__health__":
        sys.exit(0 if json.loads(o.open(url, timeout=3).read()).get("status") == "ok" else 1)
    spec = json.loads(o.open(url, timeout=3).read())
    sys.exit(0 if any(needle in p for p in spec.get("paths", {})) else 1)
except Exception:
    sys.exit(1)
PYEOF
    then
      return 0
    fi
    sleep 0.5
  done
  echo "就绪超时：${url}（needle=${needle}）"
  return 1
}

require_free_port "$AGENT_PORT" || exit 1

cd "$ROOT" || exit 1
"$PY" -m uvicorn app.main:app --host 127.0.0.1 --port "$AGENT_PORT" \
  >"$LOGDIR/api.log" 2>&1 &
API_PID=$!

cleanup() {
  kill "$API_PID" 2>/dev/null
  wait "$API_PID" 2>/dev/null
}
trap cleanup EXIT

wait_ready "http://127.0.0.1:${AGENT_PORT}/health" "__health__" \
  || { echo "API 起不来，日志："; tail -20 "$LOGDIR/api.log"; exit 1; }
wait_ready "http://127.0.0.1:${AGENT_PORT}/openapi.json" "/lg-rag/stream" \
  || { echo "自然语言入口没注册上，日志："; tail -20 "$LOGDIR/api.log"; exit 1; }
echo "API 就绪（agent=${AGENT_PORT}），自然语言入口已确认；日志目录：${LOGDIR}"
echo

"$PY" "$(dirname "$0")/agent_nl_smoke.py" "$@"
