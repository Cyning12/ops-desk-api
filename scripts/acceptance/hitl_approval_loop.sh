#!/bin/bash
# HITL 审批回路·真进程联调（起服务 → 等就绪 → 跑驱动 → 杀进程）
#
#   ops-desk-api（FastAPI）  ← 申请落库 / 拉待办 / 接收审批结果
#   ops-desk-mock-oa（Java） ← 获取申请 / 审批申请 / 回调代理侧
#
# 为什么必须有这一层（它一次抓出两个真 bug，都是单测抓不到的）：
#   1. JDK HttpClient 默认带 `Upgrade: h2c`，uvicorn 的 h11 见到 Upgrade 就
#      **不读请求体** ⇒ 回调恒定 422 "Field required"，报错完全不提示原因；
#   2. InMemoryHitlStore.adecide 无条件覆写，DbHitlStore 却有
#      `WHERE status='pending'` 守卫 ⇒ 两套存储语义分叉，
#      联调（memory）放行、生产（db）拒绝。
#
# 用法：
#   ./scripts/acceptance/hitl_approval_loop.sh
#   MOCK_OA_JAR=/path/to/mock-oa.jar ./scripts/acceptance/hitl_approval_loop.sh
#
# 前提：ops-desk-mock-oa 已 `mvn package`（脚本只吃 jar，不替你构建）。
set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY="$ROOT/.venv/bin/python"
JAR="${MOCK_OA_JAR:-$ROOT/../ops-desk-mock-oa/target/mock-oa-0.0.1-SNAPSHOT.jar}"
LOGDIR="$(mktemp -d)"

# 端口：8000 长期被 Docker Desktop 占着，别用；这里选两个不常用的
export AGENT_PORT="${AGENT_PORT:-8123}"
export OA_PORT="${OA_PORT:-18081}"

# 出口代理会把打 127.0.0.1 的请求送到代理去（拿到看不懂的 502）
export no_proxy="127.0.0.1,localhost"
export NO_PROXY="127.0.0.1,localhost"
export PATH="/opt/homebrew/bin:$PATH"

if [ ! -f "$JAR" ]; then
  echo "找不到 mock-oa jar：$JAR（先在 ops-desk-mock-oa 跑 mvn package，或用 MOCK_OA_JAR 指定）"
  exit 1
fi

wait_ready() {
  # ⚠️ 不能用「端口有人在听」当就绪探针：8000 被 Docker Desktop 长期占着，
  # uvicorn 根本没起来，lsof 却一直成功 —— 于是我在跟别人的服务说话。
  # 就绪 = **内容**对得上。
  local url="$1" needle="$2" i
  for i in $(seq 1 120); do
    if "$PY" - "$url" "$needle" <<'PYEOF' 2>/dev/null
import json, sys, urllib.request
url, needle = sys.argv[1], sys.argv[2]
o = urllib.request.build_opener(urllib.request.ProxyHandler({}))
try:
    if needle == "__http200__":
        o.open(url, timeout=3).read()
        sys.exit(0)
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

cd "$ROOT" || exit 1

# HITL_RESUME_PG=1 ⇒ 开 PG checkpointer，验**真进程里的 PG 恢复路径**
# （默认关：内存 saver 下恢复必然失败，那条断言验的是"不许假装成功"）
CKPT_ENV="${LG_RAG_HTTP_CHECKPOINTER:-}"
if [ "${HITL_RESUME_PG:-0}" = "1" ]; then
  CKPT_ENV=postgres
fi
# 导出：驱动脚本也要读它来决定第 9 步的期望值
export LG_RAG_HTTP_CHECKPOINTER="$CKPT_ENV"

OPS_HITL_PERSISTENCE=memory \
OPS_HITL_CALLBACK_SECRET=s3cr3t \
OPS_ADMIN_SYNC_TOKEN=admintok \
"$PY" -m uvicorn app.main:app --host 127.0.0.1 --port "$AGENT_PORT" \
  >"$LOGDIR/agent.log" 2>&1 &
API_PID=$!

# SERVER__PORT=65367 会被环境变量注入并被 Spring 宽松绑定当成 server.port，
# 命令行参数优先级最高，所以显式 --server.port
MOCK_OA_AGENT_BASE_URL="http://127.0.0.1:${AGENT_PORT}/api/ops" \
OPS_HITL_CALLBACK_SECRET=s3cr3t \
java -jar "$JAR" --server.port="$OA_PORT" >"$LOGDIR/oa.log" 2>&1 &
OA_PID=$!

cleanup() {
  kill "$API_PID" 2>/dev/null
  kill "$OA_PID" 2>/dev/null
  wait "$API_PID" 2>/dev/null
  wait "$OA_PID" 2>/dev/null
}
trap cleanup EXIT

wait_ready "http://127.0.0.1:${AGENT_PORT}/health" "__health__" || { tail -20 "$LOGDIR/agent.log"; exit 1; }
wait_ready "http://127.0.0.1:${AGENT_PORT}/openapi.json" "/hitl/callback" || { tail -20 "$LOGDIR/agent.log"; exit 1; }
wait_ready "http://127.0.0.1:${OA_PORT}/actuator/health" "__http200__" || { tail -20 "$LOGDIR/oa.log"; exit 1; }
echo "两端就绪（agent=${AGENT_PORT}, mock-oa=${OA_PORT}），路由已确认"
echo "日志目录：$LOGDIR"

"$PY" "$(dirname "$0")/hitl_approval_loop.py"
