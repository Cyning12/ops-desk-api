#!/bin/bash
# 多副本验证 D1/D4 · runbook 轨编排（建镜像 → 建库 → compose 双实例+nginx → LB → 驱动 → 收尾）
#
# 形态对齐 hitl_persistence_smoke.sh 先例（起服务/等就绪/收尾杀进程），
# 拓扑对齐 task D1：2 api 容器共享同一 PG 专用库 + 前置 LB。
#
# 网关形态（诚实标注）：外部 Java 网关 + Eureka 在外部仓且本仓无 Eureka 客户端
# → Eureka 注册条目未覆盖待补；降级形态 = nginx round-robin（无亲和组 · SPEC 命名形态）
# + 自研 Python LB cookie-sticky（亲和组 · vanilla nginx 不支持 cookie 亲和，
# 支持面归属在报告分开标注）。
#
# 用法：./scripts/acceptance/multi_replica_verify.sh
set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY="$ROOT/.venv/bin/python"
LOGDIR="$(mktemp -d)"
COMPOSE_PROJECT=ops-desk-mrv
DB_NAME=opsdesk_mrv
DB_CONTAINER=ops-desk-api-db-1
IMAGE=ops-desk-api-mrv:latest

export MR_PORT_A="${MR_PORT_A:-8101}"
export MR_PORT_B="${MR_PORT_B:-8102}"
export MR_LB_RR="${MR_LB_RR:-8199}"
export MR_LB_COOKIE="${MR_LB_COOKIE:-8200}"
export MR_DB_DSN="postgresql://ops:ops_password@127.0.0.1:5432/${DB_NAME}"
export MR_GIT_SHA="$(git -C "$ROOT" rev-parse --short HEAD)"
# token 哈希 = HMAC(OPS_DESK_SECRET)：驱动（宿主机）与容器必须同一把，否则登录 401
export OPS_DESK_SECRET="${MR_DESK_SECRET:-mr-desk-secret}"
TS="$(date +%Y%m%d_%H%M%S)"
export MR_REPORT="$ROOT/reports/multi_replica_verify/deploy_${TS}.yaml"

# 出口代理会把打 127.0.0.1 的请求送到代理去（拿到看不懂的 502）
export no_proxy="127.0.0.1,localhost"
export NO_PROXY="127.0.0.1,localhost"

LB_CK_PID=""

require_free_port() {
  # 必须先确认端口空着：残留旧服务会骗过内容型就绪探针（smoke 先例同款坑）
  local p="$1"
  if lsof -nP -iTCP:"$p" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "端口 ${p} 已被占用 —— 残留进程会骗过就绪探针。占用者："
    lsof -nP -iTCP:"$p" -sTCP:LISTEN | tail -n +2
    return 1
  fi
  return 0
}

wait_ready() {
  # 就绪 = 内容对得上（/health status==ok），不是端口在听
  local url="$1" i
  for i in $(seq 1 240); do
    if "$PY" - "$url" <<'PYEOF' 2>/dev/null
import json, sys, urllib.request
o = urllib.request.build_opener(urllib.request.ProxyHandler({}))
try:
    sys.exit(0 if json.loads(o.open(sys.argv[1], timeout=3).read()).get("status") == "ok" else 1)
except Exception:
    sys.exit(1)
PYEOF
    then
      return 0
    fi
    sleep 0.5
  done
  echo "就绪超时：${url}"
  return 1
}

compose_cmd() {
  docker compose -p "$COMPOSE_PROJECT"     -f "$ROOT/scripts/acceptance/multi_replica_compose.yml" "$@"
}

cleanup() {
  [ -n "$LB_CK_PID" ] && kill "$LB_CK_PID" 2>/dev/null
  compose_cmd down >/dev/null 2>&1
  docker exec "$DB_CONTAINER" psql -U ops -d postgres     -c "DROP DATABASE IF EXISTS ${DB_NAME}" >/dev/null 2>&1
  echo "收尾：compose down + drop ${DB_NAME}（日志目录 ${LOGDIR}）"
}
trap cleanup EXIT

for p in "$MR_PORT_A" "$MR_PORT_B" "$MR_LB_RR" "$MR_LB_COOKIE"; do
  require_free_port "$p" || exit 1
done

echo "== 1/6 增量镜像 ${IMAGE}（依赖层对齐当前 requirements + COPY 当前代码）"
docker build -t "$IMAGE" -f "$ROOT/scripts/acceptance/multi_replica_Dockerfile" "$ROOT"   >"$LOGDIR/build.log" 2>&1 || { echo "镜像构建失败："; tail -20 "$LOGDIR/build.log"; exit 1; }
export MR_IMAGE_ID="$(docker inspect -f '{{.Id}}' "$IMAGE")"
echo "    image id: ${MR_IMAGE_ID}"

echo "== 2/6 专用库 ${DB_NAME}（drop 重建 + alembic upgrade head）"
docker exec "$DB_CONTAINER" psql -U ops -d postgres   -c "DROP DATABASE IF EXISTS ${DB_NAME}" -c "CREATE DATABASE ${DB_NAME}" || exit 1
(cd "$ROOT" && DATABASE_URL="postgresql+asyncpg://ops:ops_password@127.0.0.1:5432/${DB_NAME}"   "$PY" -m alembic upgrade head) >"$LOGDIR/alembic.log" 2>&1   || { echo "alembic 失败："; tail -20 "$LOGDIR/alembic.log"; exit 1; }
# checkpoint 表预热：saver.setup() 幂等（checkpointer.py :48-53），宿主机先建一遍，
# 容器首请求就不必在请求路径上跑 DDL（冷启动首请求挂起实测坑 · 2026-09-22）
(cd "$ROOT" && DATABASE_URL="postgresql+asyncpg://ops:ops_password@127.0.0.1:5432/${DB_NAME}"   "$PY" -c "import asyncio; from app.ops.lg_rag.checkpointer import apostgres_saver; asyncio.run(apostgres_saver(setup=True).__aenter__())") >"$LOGDIR/ckpt-warm.log" 2>&1   || { echo "checkpoint 预热失败："; tail -10 "$LOGDIR/ckpt-warm.log"; exit 1; }

echo "== 3/6 compose 双实例 + nginx LB（api-a:${MR_PORT_A} api-b:${MR_PORT_B} lb:${MR_LB_RR}）"
compose_cmd up -d >"$LOGDIR/compose.log" 2>&1   || { echo "compose up 失败："; tail -20 "$LOGDIR/compose.log"; exit 1; }

wait_ready "http://127.0.0.1:${MR_PORT_A}/health"   || { echo "api-a 起不来："; compose_cmd logs api-a | tail -30; exit 1; }
wait_ready "http://127.0.0.1:${MR_PORT_B}/health"   || { echo "api-b 起不来："; compose_cmd logs api-b | tail -30; exit 1; }

echo "== 4/6 nginx（rr:${MR_LB_RR}）就绪 + 亲和组 LB（cookie-sticky:${MR_LB_COOKIE}）"
wait_ready "http://127.0.0.1:${MR_LB_RR}/health"   || { echo "nginx LB 不通："; compose_cmd logs lb | tail -20; exit 1; }
"$PY" "$ROOT/scripts/acceptance/multi_replica_lb.py" --port "$MR_LB_COOKIE" --mode cookie   --upstream "api-a=127.0.0.1:${MR_PORT_A}" --upstream "api-b=127.0.0.1:${MR_PORT_B}"   >"$LOGDIR/lb-cookie.log" 2>&1 &
LB_CK_PID=$!
sleep 1

echo "== 5/6 驱动断言（报告 → ${MR_REPORT}）"
(cd "$ROOT" && "$PY" scripts/acceptance/multi_replica_verify.py)
DRIVER_EC=$?

echo "== 6/6 结果：${DRIVER_EC}（0=全过）· 亲和组 LB 命中数："
grep -h 'hits=' "$LOGDIR"/lb-cookie.log 2>/dev/null || true
exit "${DRIVER_EC}"
