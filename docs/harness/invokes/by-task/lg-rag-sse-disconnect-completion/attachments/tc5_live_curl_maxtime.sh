#!/bin/bash
set -euo pipefail
B=http://127.0.0.1:8051
ATT=docs/harness/invokes/by-task/lg-rag-sse-disconnect-completion/attachments
J=/tmp/disc_tc5b.jar
rm -f "$J"
INV=$(uv run python scripts/create_initial_user.py | tail -1)
USER=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['username'])" "$INV")
TOK=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['invite_token'])" "$INV")
curl -sS --noproxy '*' -c "$J" -b "$J" -X POST "$B/api/ops/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USER\",\"invite_token\":\"$TOK\"}" >/tmp/login_ok.json
echo "login=$(cat /tmp/login_ok.json)"

# max-time 5 forces TCP close mid-stream
set +e
curl -sN --noproxy '*' --max-time 5 -D /tmp/c_stream.hdr -b "$J" -X POST "$B/api/ops/lg-rag/stream" \
  -H "Content-Type: application/json" \
  -d '{"query":"请分二十个章节、每章至少三段，详细论述软件工程与 ops-desk，尽量写长。","mode":"basic"}' \
  -o /tmp/c_live.sse
EC=$?
set -e
echo "curl_exit=$EC"
RUN=$(grep -i "x-ops-lg-rag-run-id" /tmp/c_stream.hdr | tr -d '\r' | awk '{print $2}')
echo "RUN=$RUN"
cp /tmp/c_stream.hdr "$ATT/tc5_curl_disconnect_stream.hdr"
cp /tmp/c_live.sse "$ATT/tc5_curl_disconnect_live_partial.sse"
# poll
for i in $(seq 1 20); do
  CODE=$(curl -sS --noproxy '*' -o /tmp/c_replay.sse -w "%{http_code}" -b "$J" \
    -X POST "$B/api/ops/lg-rag/replay" -H "Content-Type: application/json" \
    -d "{\"run_id\":\"$RUN\",\"after_seq\":0}")
  echo "t=$((i*5))s HTTP=$CODE"
  if [ "$CODE" = "200" ]; then
    curl -sS --noproxy '*' -D "$ATT/tc5_curl_disconnect_replay.hdr" -b "$J" \
      -X POST "$B/api/ops/lg-rag/replay" -H "Content-Type: application/json" \
      -d "{\"run_id\":\"$RUN\",\"after_seq\":0}" -o "$ATT/tc5_curl_disconnect_replay.sse" >/dev/null
    python3 - <<PY
import json
frames=[json.loads(l[5:]) for l in open("$ATT/tc5_curl_disconnect_replay.sse") if l.startswith("data:")]
print("TYPES",[f.get("event_type") for f in frames])
d=[f for f in frames if f.get("event_type")=="done"]
print("STATUS",(d[-1].get("payload") or {}).get("status") if d else None)
print("PAYLOAD", d[-1].get("payload") if d else None)
PY
    exit 0
  fi
  sleep 5
done
echo "CURL_PATH_FAIL"
exit 1
