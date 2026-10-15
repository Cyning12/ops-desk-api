#!/bin/bash
unset NO_PROXY no_proxy http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
J=/tmp/tc5.jar
B=http://127.0.0.1:8050
rm -f /tmp/tc5_s3_live.sse /tmp/tc5_s3.hdr

echo "=== step1: start echo run (supervisor) ==="
curl -sN -m 300 -D /tmp/tc5_s3.hdr -b $J -X POST $B/api/ops/lg-rag/stream -H "Content-Type: application/json" \
  -d '{"query":"这是一个需要调用工具的任务（就像查询 issue 状态一样）：请调用工具 testing.write.echo 回显一条备注 note=tc5-s3","mode":"supervisor"}' \
  > /tmp/tc5_s3_live.sse 2>/dev/null &
CPID=$!
for i in $(seq 1 30); do grep -q "run.start" /tmp/tc5_s3_live.sse 2>/dev/null && break; sleep 1; done
RUN=$(grep -i "x-ops-lg-rag-run-id" /tmp/tc5_s3.hdr | tr -d '\r' | awk '{print $2}')
echo "RUN=$RUN"

echo "=== step2: replay WHILE in flight (expect 409 + Retry-After) ==="
curl -s -D /tmp/tc5_s3_409.hdr -b $J -X POST $B/api/ops/lg-rag/replay -H "Content-Type: application/json" \
  -d "{\"run_id\":\"$RUN\",\"after_seq\":0}" -o /tmp/tc5_s3_409.body -w "HTTP=%{http_code}\n"
echo "--- status + Retry-After ---"; grep -iE "HTTP/|retry-after" /tmp/tc5_s3_409.hdr
echo "--- body ---"; cat /tmp/tc5_s3_409.body; echo

echo "=== step3: wait for done{waiting_approval} ==="
for i in $(seq 1 90); do grep -q "waiting_approval" /tmp/tc5_s3_live.sse 2>/dev/null && break; sleep 2; done
kill $CPID 2>/dev/null; wait $CPID 2>/dev/null
python3 - <<'PYEOF'
import json
frames=[json.loads(l[5:]) for l in open('/tmp/tc5_s3_live.sse') if l.startswith('data:')]
print('LIVE_FRAMES=',len(frames))
w=[f for f in frames if f.get('event_type')=='hitl.waiting']
if w:
    r=w[-1]['payload']['requests'][0]
    print('RID='+r['id'])
    print('REASON='+str(r.get('reason'))[:100])
d=[f for f in frames if f.get('event_type')=='done']
if d: print('DONE_STATUS=',d[-1]['payload'].get('status'),'latency_ms=',d[-1]['payload'].get('latency_ms'),'keys=',sorted(d[-1]['payload'].keys()))
PYEOF

echo "=== step4: replay while WAITING (suspended = closed semantics, expect 200) ==="
curl -s -b $J -X POST $B/api/ops/lg-rag/replay -H "Content-Type: application/json" \
  -d "{\"run_id\":\"$RUN\",\"after_seq\":0}" -o /tmp/tc5_s3_suspended_replay.sse -w "HTTP=%{http_code}\n"
python3 - <<'PYEOF'
import json
frames=[json.loads(l[5:]) for l in open('/tmp/tc5_s3_suspended_replay.sse') if l.startswith('data:')]
seqs=[f.get('seq') for f in frames]
print('SUSPENDED_REPLAY_FRAMES=',len(frames),'SEQ_CONTIGUOUS=',seqs==list(range(1,len(frames)+1)))
PYEOF
