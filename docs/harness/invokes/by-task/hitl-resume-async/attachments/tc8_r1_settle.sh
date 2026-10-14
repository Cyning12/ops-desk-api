#!/bin/bash
unset NO_PROXY no_proxy http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
A=docs/harness/invokes/by-task/hitl-resume-async/attachments
B=http://127.0.0.1:8050
J=$A/tc8.jar
RUN=$(cat $A/r1.run); RID=$(cat $A/r1.rid)
echo "=== r1 等真沉降（replay 出现 done{resumed}）==="
SETTLED=0
for i in $(seq 1 150); do
  curl -s -b $J -X POST $B/api/ops/lg-rag/replay -H "Content-Type: application/json" -d "{\"run_id\":\"$RUN\",\"after_seq\":0}" -o $A/r1_poll.sse
  if python3 -c "
import json,sys
frames=[json.loads(l[5:]) for l in open('$A/r1_poll.sse') if l.startswith('data:')]
d=[f for f in frames if f.get('event_type')=='done' and (f.get('payload') or {}).get('status')=='resumed']
sys.exit(0 if d else 1)
"; then echo "RESUMED_DONE_FOUND@poll$i"; SETTLED=1; cp $A/r1_poll.sse $A/r1_full.sse; break; fi
  sleep 2
done
[ "$SETTLED" = "0" ] && echo "FAIL: r1 no done{resumed} within 300s"
python3 -c "
import json
frames=[json.loads(l[5:]) for l in open('$A/r1_full.sse') if l.startswith('data:')]
seqs=[f.get('seq') for f in frames]
print('FRAMES=',len(frames),'SEQ_CONTIGUOUS=',seqs==list(range(1,len(frames)+1)))
for f in frames:
    if f.get('event_type')=='done':
        p=f.get('payload') or {}
        print('seq',f.get('seq'),'done status=',p.get('status'),'latency_ms=',p.get('latency_ms'),type(p.get('latency_ms')).__name__,'keys=',sorted(p.keys()),'model_present=','model' in p)
print('hitl.resumed=',len([f for f in frames if f.get('event_type')=='hitl.resumed']))
"
echo "=== r1 真沉降后二次 resume（预期 409 · preflight not_interrupted 语义）==="
curl -s -b $J -X POST $B/api/ops/hitl/requests/$RID/resume -H "Content-Type: application/json" -d '{}' \
  -o $A/r1_dup_settled2.json -w "DUP_SETTLED_HTTP=%{http_code}\n"
cat $A/r1_dup_settled2.json; echo
