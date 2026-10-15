#!/bin/bash
# TC8 round7 · 驳回 resume 收工链（rejected → resume → verdict==settle → done{settled}）
set -u
A=docs/harness/invokes/by-task/hitl-resume-async/attachments
B=http://127.0.0.1:8050
J=$A/tc8.jar
N=7
echo "=== round $N: start echo run ==="
curl -s -b $J -N -X POST $B/api/ops/lg-rag/stream -H "Content-Type: application/json" \
  -d '{"query":"这是一个需要调用工具的任务（就像查询 issue 状态一样）：请调用工具 testing.write.echo 回显一条备注 note=tc8-r7","mode":"supervisor","history":[],"kb_scope":"ops"}' \
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
echo "=== round $N: decide rejected ==="
curl -s -b $J -X POST $B/api/ops/hitl/requests/$RID/decide -H "Content-Type: application/json" \
  -d '{"decision":"rejected","note":"tc8 r7 reject-chain"}' -o $A/r${N}_decide.json -w "DECIDE_HTTP=%{http_code}\n"
python3 -c "import json; d=json.load(open('$A/r${N}_decide.json')); print('request.status=',(d.get('request') or {}).get('status'))"
echo "=== round $N: resume（计时）==="
curl -s -b $J -X POST $B/api/ops/hitl/requests/$RID/resume -H "Content-Type: application/json" -d '{}' \
  -o $A/r${N}_resume.json -w "RESUME_HTTP=%{http_code} time=%{time_total}\n" | tee $A/r${N}_resume.timing
python3 -c "
import json
d=json.load(open('$A/r${N}_resume.json'))
r=d.get('resume') or {}
print('resume.status=',r.get('status'),'rejected=',r.get('rejected'),'approved=',r.get('approved'))
"
echo "=== round $N: 等沉降（replay 出现 done{settled}）==="
SETTLED=0
for i in $(seq 1 60); do
  curl -s -b $J -X POST $B/api/ops/lg-rag/replay -H "Content-Type: application/json" -d "{\"run_id\":\"$RUN\",\"after_seq\":0}" -o $A/r${N}_poll.sse 2>/dev/null
  if grep -q '\"status\": \"settled\"' $A/r${N}_poll.sse 2>/dev/null; then echo "SETTLED_DONE@poll$i"; SETTLED=1; cp $A/r${N}_poll.sse $A/r${N}_full.sse; break; fi
  sleep 2
done
[ "$SETTLED" = "0" ] && echo "FAIL: no done{settled} within 120s"
python3 -c "
import json
frames=[json.loads(l[5:]) for l in open('$A/r${N}_full.sse') if l.startswith('data:')]
seqs=[f.get('seq') for f in frames]
print('FRAMES=',len(frames),'SEQ_CONTIGUOUS=',seqs==list(range(1,len(frames)+1)))
for f in frames:
    if f.get('event_type')=='done':
        p=f.get('payload') or {}
        print('seq',f.get('seq'),'done status=',p.get('status'),'latency_ms=',p.get('latency_ms'),type(p.get('latency_ms')).__name__,'keys=',sorted(p.keys()),'model_present=','model' in p)
print('hitl.resumed=',len([f for f in frames if f.get('event_type')=='hitl.resumed']))
"
echo "=== round $N: 沉降后二次 resume（预期 409 驳回收口）==="
curl -s -b $J -X POST $B/api/ops/hitl/requests/$RID/resume -H "Content-Type: application/json" -d '{}' \
  -o $A/r${N}_dup.json -w "DUP_HTTP=%{http_code}\n"
cat $A/r${N}_dup.json; echo
echo "=== round $N done ==="
