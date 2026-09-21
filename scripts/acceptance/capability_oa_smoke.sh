#!/bin/bash
# OA 能力出网冒烟（起 mock-oa → 等就绪 → 跑驱动 → 杀进程）
#
# 为什么要有这条：手工抄 runbook 里的片段最容易漏掉"先把 mock-oa 起来"这一步，
# 而**漏了它不会报错** —— `oa.doc.search` 声明了静态降级，服务没起时它照样
# 返回 `ok=True`，只是内容是那句"服务暂时不可用"。本脚本把起停服务也包进来，
# 让"漏起服务"这种错不可能发生。
#
# 只依赖：JDK ≥ 21 + mock-oa jar（`mvn -B clean package -DskipTests` 产出）。
#
# 用法：
#   ./scripts/acceptance/capability_oa_smoke.sh
#   MOCK_OA_PORT=18081 ./scripts/acceptance/capability_oa_smoke.sh
set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY="$ROOT/.venv/bin/python"
MOCK_OA_DIR="${MOCK_OA_DIR:-$ROOT/../ops-desk-mock-oa}"
MOCK_OA_JAR="mock-oa-0.0.1-SNAPSHOT.jar"
MOCK_OA_PORT="${MOCK_OA_PORT:-18080}"
LOGDIR="$(mktemp -d)"

# 出口代理会把打 127.0.0.1 的请求送到代理去（拿到看不懂的 502）
export no_proxy="127.0.0.1,localhost"
export NO_PROXY="127.0.0.1,localhost"

# 本次冒烟的前置用**显式环境变量**固定，不依赖 .env 当前写的是什么
# （空值/指定值都能压住 .env：python-dotenv 的 override=False 只认"键是否存在"）
export OPS_CAPABILITY_EXTRA_MANIFESTS="$ROOT/app/ops/capability/manifests/oa.readonly.v1.yaml"
export OPS_CAP_CRED_OA_GATEWAY_TOKEN="${OPS_CAP_CRED_OA_GATEWAY_TOKEN:-local-dev-token}"
export OA_BASE="http://127.0.0.1:${MOCK_OA_PORT}"
export OPS_CHAT_TRACER=""          # 验收不该有外部副作用

if [ ! -f "$MOCK_OA_DIR/target/$MOCK_OA_JAR" ]; then
  echo "找不到桩服务 jar：$MOCK_OA_DIR/target/$MOCK_OA_JAR"
  echo "先在 ops-desk-mock-oa 跑：mvn -B clean package -DskipTests"
  exit 1
fi

require_free_port() {
  # ⚠️ 先确认端口空着：否则桩服务 bind 失败很快退出，而就绪探针是"内容型"的
  # —— 一个**残留的旧桩服务**同样能返回 200，脚本就会在跟别人的服务说话。
  local p="$1"
  if lsof -nP -iTCP:"$p" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "端口 ${p} 已被占用 —— 本次要起的桩服务起不来，但残留进程会骗过就绪探针。"
    echo "占用者："
    lsof -nP -iTCP:"$p" -sTCP:LISTEN | tail -n +2
    echo "先清掉它，或换端口（MOCK_OA_PORT=18081 …）再跑。"
    return 1
  fi
  return 0
}

wait_ready() {
  # ⚠️ 不能用"端口有人在听"当就绪探针。这里直接打 actuator，要到 HTTP 200
  # （body 是 {"status":"UP"}，**大写 UP** —— 别和 FastAPI 的 "ok" 混）。
  local url="$1" i
  for i in $(seq 1 120); do
    if "$PY" - "$url" <<'PYEOF' 2>/dev/null
import sys, urllib.request
o = urllib.request.build_opener(urllib.request.ProxyHandler({}))
try:
    sys.exit(0 if o.open(sys.argv[1], timeout=3).status == 200 else 1)
except Exception:
    sys.exit(1)
PYEOF
    then
      return 0
    fi
    sleep 0.5
  done
  echo "桩服务就绪超时：${url}"
  return 1
}

require_free_port "$MOCK_OA_PORT" || exit 1

cd "$MOCK_OA_DIR" || exit 1
# 环境里有 SERVER__PORT，Spring 宽松绑定会当成 server.port 覆盖 application.yml；
# 命令行参数优先级最高，所以显式 --server.port。
java -jar "target/$MOCK_OA_JAR" --server.port="$MOCK_OA_PORT" \
  >"$LOGDIR/mock-oa.log" 2>&1 &
OA_PID=$!

cleanup() {
  kill "$OA_PID" 2>/dev/null
  wait "$OA_PID" 2>/dev/null
}
trap cleanup EXIT

wait_ready "http://127.0.0.1:${MOCK_OA_PORT}/actuator/health" \
  || { echo "桩服务起不来，日志："; tail -20 "$LOGDIR/mock-oa.log"; exit 1; }
echo "桩服务就绪（mock-oa=${MOCK_OA_PORT}）；日志目录：${LOGDIR}"
echo "（OA_BASE=${OA_BASE} 凭证名 oa_gateway_token）"
echo

cd "$ROOT" || exit 1
"$PY" "$(dirname "$0")/capability_oa_smoke.py"
