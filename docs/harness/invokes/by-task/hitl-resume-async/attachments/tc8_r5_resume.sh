#!/bin/bash
unset NO_PROXY no_proxy http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
A=docs/harness/invokes/by-task/hitl-resume-async/attachments
B=http://127.0.0.1:8050
J=$A/tc8.jar
RUN=$(grep -i "x-ops-lg-rag-run-id" $A/r5.hdr | tr -d '\r' | awk '{print $2}')
echo "R5_RUN=$RUN"
echo "=== 等孤儿 r5 推进到 waiting_approval（RunWorker 解耦佐证）==="
FOUND=0
for i in $(seq 1 90); do
  curl -s -b $J -X POST $B/api/ops/lg-rag/replay -H "Content-Type: application/json" -d "{\"run_id\":\"$RUN\",\"after_seq\":0}" -o $A/r5_poll.sse 2>/dev/null
  if grep -q waiting_approval $A/r5_poll.sse 2>/dev/null; then echo "WAITING_FOUND@poll$i"; FOUND=1; break; fi
  sleep 2
done
[ "$FOUND" = "0" ] && { echo "FAIL: r5 orphan never reached waiting_approval"; exit 1; }
RID=$(python3 -c "
import json
frames=[json.loads(l[5:]) for l in open('$A/r5_poll.sse') if l.startswith('data:')]
w=[f for f in frames if f.get('event_type')=='hitl.waiting']
print(w[-1]['payload']['requests'][0]['id'] if w else '')
")
echo "RID=$RID"
[ -z "$RID" ] && { echo "FAIL: no RID for r5"; exit 1; }
curl -s -b $J -X POST $B/api/ops/hitl/requests/$RID/decide -H "Content-Type: application/json" \
  -d '{"decision":"approved","note":"tc8 r5 orphan-resume"}' -o $A/r5_decide.json -w "DECIDE_HTTP=%{http_code}\n"
curl -s -b $J -X POST $B/api/ops/hitl/requests/$RID/resume -H "Content-Type: application/json" -d '{}' \
  -o $A/r5_resume.json -w "RESUME_HTTP=%{http_code} time=%{time_total}\n" | tee $A/r5_resume.timing
python3 -c "import json; d=json.load(open('$A/r5_resume.json')); print('resume.status=',(d.get('resume') or {}).get('status'))"
echo "$RUN" > $A/r5.run; echo "$RID" > $A/r5.rid
