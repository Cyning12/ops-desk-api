#!/bin/bash
# TC8 round8 · resume_mode 白名单（未知值 turbo）
set -u
A=docs/harness/invokes/by-task/hitl-resume-async/attachments
B=http://127.0.0.1:8050
J=$A/tc8.jar
N=8
echo "=== round $N: start echo run ==="
curl -s -b $J -N -X POST $B/api/ops/lg-rag/stream -H "Content-Type: application/json" \
  -d '{"query":"这是一个需要调用工具的任务（就像查询 issue 状态一样）：请调用工具 testing.write.echo 回显一条备注 note=tc8-r8","mode":"supervisor","history":[],"kb_scope":"ops"}' \
  -D $A/r$N.hdr -o $A/r${N}_live.sse &
CURL_PID=$!
RUN=""
for i in $(seq 1 20); do
  RUN=$(grep -i "x-ops-lg-rag-run-id" $A/r$N.hdr 2>/dev/null | tr -d '\r' | awk '{print $2}')
  [ -n "$RUN" ] && break; sleep 1
done
echo "RUN=$RUN"; echo "$RUN" > $A/r$N.run
WAITED=0
for i in $(seq 1 120); do
  if grep -q waiting_approval $A/r${N}_live.sse 2>/dev/null; then WAITED=1; break; fi
  sleep 1
done
kill $CURL_PID 2>/dev/null; wait $CURL_PID 2>/dev/null
[ "$WAITED" = "0" ] && { echo "FAIL: no waiting_approval within 120s"; exit 1; }
RID=$(python3 -c "
import json
frames=[json.loads(l[5:]) for l in open('$A/r${N}_live.sse') if l.startswith('data:')]
w=[f for f in frames if f.get('event_type')=='hitl.waiting']
print(w[-1]['payload']['requests'][0]['id'] if w else '')
")
echo "RID=$RID"; echo "$RID" > $A/r$N.rid
[ -z "$RID" ] && { echo "FAIL: no RID"; exit 1; }
echo "=== round $N: decide 未知 resume_mode=turbo（预期 4xx）==="
curl -s -b $J -X POST $B/api/ops/hitl/requests/$RID/decide -H "Content-Type: application/json" \
  -d '{"decision":"approved","note":"tc8 r8 badmode","resume_mode":"turbo"}' -o $A/r${N}_badmode.json -w "BADMODE_HTTP=%{http_code}\n" | tee $A/r${N}_badmode.code
cat $A/r${N}_badmode.json; echo
echo "=== round $N: 同 RID 合法 decide（证明坏 decide 未消费申请）==="
curl -s -b $J -X POST $B/api/ops/hitl/requests/$RID/decide -H "Content-Type: application/json" \
  -d '{"decision":"approved","note":"tc8 r8 good","resume_mode":"inherit"}' -o $A/r${N}_decide.json -w "DECIDE_HTTP=%{http_code}\n"
python3 -c "import json; d=json.load(open('$A/r${N}_decide.json')); print('request.status=',(d.get('request') or {}).get('status'),'resume_mode=',(d.get('request') or {}).get('resume_mode'))"
echo "=== round $N: resume（计时）==="
curl -s -b $J -X POST $B/api/ops/hitl/requests/$RID/resume -H "Content-Type: application/json" -d '{}' \
  -o $A/r${N}_resume.json -w "RESUME_HTTP=%{http_code} time=%{time_total}\n" | tee $A/r${N}_resume.timing
python3 -c "
import json
d=json.load(open('$A/r${N}_resume.json'))
r=d.get('resume') or {}
print('resume.status=',r.get('status'),'rejected=',r.get('rejected'),'approved=',r.get('approved'))
"
echo "=== round $N done ==="
