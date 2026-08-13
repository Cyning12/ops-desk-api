#!/usr/bin/env bash
# Phase0：fio 4K randread 磁盘门禁（SPEC C3）
# 通过：IOPS>=3000 且 p95<=1ms；或声明预配 IOPS>=5000
# 本机无 fio 时：打印 WARN，写跳过记录，exit 0（禁止据此切流）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT_DIR="${ROOT}/reports/qdrant_migrate"
mkdir -p "${OUT_DIR}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RECORD="${OUT_DIR}/fio_gate_${STAMP}.yaml"
TARGET_DIR="${FIO_TARGET_DIR:-${ROOT}}"
SIZE="${FIO_SIZE:-256M}"
RUNTIME="${FIO_RUNTIME:-30}"
PROVISIONED_IOPS="${PROVISIONED_IOPS:-}"

pass_msg() {
  echo "PASS: $*"
}

fail_msg() {
  echo "FAIL: $*" >&2
}

if [[ -n "${PROVISIONED_IOPS}" ]]; then
  if [[ "${PROVISIONED_IOPS}" -ge 5000 ]]; then
    cat > "${RECORD}" <<EOF
gate: fio_randread
status: pass
mode: provisioned_iops
provisioned_iops: ${PROVISIONED_IOPS}
threshold_iops: 5000
note: "预配 IOPS 达标；跳过实测 fio"
recorded_at: ${STAMP}
EOF
    pass_msg "provisioned IOPS=${PROVISIONED_IOPS} >= 5000 → ${RECORD}"
    exit 0
  fi
fi

if ! command -v fio >/dev/null 2>&1; then
  cat > "${RECORD}" <<EOF
gate: fio_randread
status: skipped
reason: "fio not installed"
warn: true
note: "本地无 fio；禁止据此灌库/切流；维护者须在目标盘重跑或提供 PROVISIONED_IOPS>=5000"
recorded_at: ${STAMP}
target_dir: ${TARGET_DIR}
EOF
  echo "WARN: fio not found; wrote skip record ${RECORD}" >&2
  echo "WARN: do NOT cut over to qdrant based on this skip" >&2
  exit 0
fi

TMP_JOB="$(mktemp)"
trap 'rm -f "${TMP_JOB}"' EXIT
cat > "${TMP_JOB}" <<EOF
[randread]
rw=randread
bs=4k
iodepth=32
direct=1
ioengine=posixaio
runtime=${RUNTIME}
time_based=1
size=${SIZE}
directory=${TARGET_DIR}
filename=fio_qdrant_gate.tmp
group_reporting=1
EOF

RAW_JSON="$(fio --output-format=json "${TMP_JOB}" || true)"
PARSE_OUT="$(FIO_JSON="${RAW_JSON}" python3 - <<'PY'
import json, os
raw = os.environ.get("FIO_JSON") or ""
try:
    data = json.loads(raw)
    job = data["jobs"][0]
    read = job.get("read") or {}
    iops = float(read.get("iops") or 0)
    lat = read.get("lat_ns") or read.get("clat_ns") or {}
    pct = lat.get("percentile") or {}
    p95 = pct.get("95.000000") or pct.get("95.0") or 0
    p95_ms = float(p95) / 1e6
except Exception:
    iops, p95_ms = 0.0, 9999.0
print(f"{iops} {p95_ms}")
PY
)"
IOPS="$(echo "${PARSE_OUT}" | awk '{print $1}')"
P95_MS="$(echo "${PARSE_OUT}" | awk '{print $2}')"

STATUS="fail"
NOTE="IOPS or p95 below gate"
if python3 -c "import sys; iops=float('${IOPS}'); p95=float('${P95_MS}'); sys.exit(0 if (iops >= 3000 and p95 <= 1.0) else 1)"; then
  STATUS="pass"
  NOTE="fio 4K randread gate ok"
fi

cat > "${RECORD}" <<EOF
gate: fio_randread
status: ${STATUS}
mode: fio
iops: ${IOPS}
p95_ms: ${P95_MS}
threshold_iops: 3000
threshold_p95_ms: 1.0
target_dir: ${TARGET_DIR}
recorded_at: ${STAMP}
note: "${NOTE}"
EOF

if [[ "${STATUS}" == "pass" ]]; then
  pass_msg "IOPS=${IOPS} p95_ms=${P95_MS} → ${RECORD}"
  exit 0
fi
fail_msg "IOPS=${IOPS} p95_ms=${P95_MS}；禁止灌库/切流 → ${RECORD}"
exit 1
