#!/bin/bash
# HITL **落库这条线**·本地冒烟（起 API → 等就绪 → 跑驱动 → 杀进程）
#
# 只依赖：PostgreSQL 在跑 + 库已 `alembic upgrade head`。
# **不依赖** mock-oa、不依赖 LLM —— 所以它是"落库这条线到底通没通"最快的判据。
#
# 与 hitl_approval_loop.sh 的分工：
#   本脚本      —— 申请落得下吗、列表端点的 SQL 跑得通吗（agent 侧，秒级）
#   approval_loop —— 挂起 → OA 批准 → 恢复的**长**链路（要 mock-oa jar + 真 LLM）
#
# 用法：
#   ./scripts/acceptance/hitl_persistence_smoke.sh
#   AGENT_PORT=8123 ./scripts/acceptance/hitl_persistence_smoke.sh
set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY="$ROOT/.venv/bin/python"
LOGDIR="$(mktemp -d)"

export AGENT_PORT="${AGENT_PORT:-8123}"

# 出口代理会把打 127.0.0.1 的请求送到代理去（拿到看不懂的 502）
export no_proxy="127.0.0.1,localhost"
export NO_PROXY="127.0.0.1,localhost"

# ⚠️ 用**显式环境变量**固定本次冒烟的前置，不依赖 .env 当前写的是什么：
#   - 空值同样能压住 .env（python-dotenv 的 override=False 只认"键是否已存在"），
#     所以 OPS_CHAT_TRACER= 就能把 .env 里的 langfuse 关掉 —— 验收不该有外部副作用。
#   - OPS_HITL_PERSISTENCE=db 是本脚本的**断言前提**，不能让它随 .env 漂。
export OPS_HITL_PERSISTENCE=db
export OPS_HITL_CALLBACK_SECRET="${OPS_HITL_CALLBACK_SECRET:-s3cr3t}"
export OPS_ADMIN_SYNC_TOKEN="${OPS_ADMIN_SYNC_TOKEN:-admintok}"
export OPS_CHAT_TRACER=""

require_free_port() {
  # ⚠️ 必须**先**确认端口空着。否则 uvicorn bind 失败秒退，而就绪探针是"内容型"的
  # —— 一个**残留的旧服务**同样能满足"内容对得上"，于是脚本会全程在跟别人的服务说话，
  # 报出来的失败跟你改的代码毫无关系（实测踩到过：内存模式却得到 409）。
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
  # ⚠️ 不能用"端口有人在听"当就绪探针（8000 被 Docker Desktop 长期占着，
  # uvicorn 起不来的情况下 lsof 仍成功）。就绪 = **内容**对得上。
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
wait_ready "http://127.0.0.1:${AGENT_PORT}/openapi.json" "/hitl/callback" \
  || { echo "路由没注册上，日志："; tail -20 "$LOGDIR/api.log"; exit 1; }
echo "API 就绪（agent=${AGENT_PORT}），路由已确认；日志目录：${LOGDIR}"

"$PY" "$(dirname "$0")/hitl_persistence_smoke.py"
