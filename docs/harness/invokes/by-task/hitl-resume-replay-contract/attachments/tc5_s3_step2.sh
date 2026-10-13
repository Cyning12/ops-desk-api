#!/bin/bash
unset NO_PROXY no_proxy http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
J=/tmp/tc5.jar
B=http://127.0.0.1:8050
RID=hitl_81aea17536024f969e9f
RUN=d0d824d405d842a39a2139c972d12d97

echo "=== step5: decide approved (inherit · 不送 resume_mode) ==="
curl -s -b $J -X POST $B/api/ops/hitl/requests/$RID/decide -H "Content-Type: application/json" \
  -d '{"decision":"approved","note":"tc5 s3 inherit"}' -o /tmp/tc5_s3_decide.json -w "HTTP=%{http_code}\n"
python3 -c "import json; d=json.load(open('/tmp/tc5_s3_decide.json')); print('request.status=',(d.get('request') or {}).get('status'),'resume=',json.dumps(d.get('resume'),ensure_ascii=False)[:300])"

echo "=== step6: resume (capture SSE) ==="
curl -sN -m 240 -b $J -X POST $B/api/ops/hitl/requests/$RID/resume -H "Content-Type: application/json" -d '{}' -o /tmp/tc5_s3_resume.sse -w "HTTP=%{http_code}\n"
python3 - <<'PYEOF'
import json
frames=[json.loads(l[5:]) for l in open('/tmp/tc5_s3_resume.sse') if l.startswith('data:')]
print('RESUME_FRAMES=',len(frames))
for f in frames:
    et=f.get('event_type')
    if et=='done':
        p=f.get('payload') or {}
        print('FINAL_DONE status=',p.get('status'),' latency_ms=',p.get('latency_ms'),' type=',type(p.get('latency_ms')).__name__,' keys=',sorted(p.keys()),' model_present=','model' in p)
    if et in ('hitl.resumed','hitl.waiting','error'):
        print('seq',f.get('seq'),et,str(f.get('payload'))[:120])
PYEOF

echo "=== step7: full replay after resume settle (expect 200 + final done carries latency_ms) ==="
curl -s -b $J -X POST $B/api/ops/lg-rag/replay -H "Content-Type: application/json" \
  -d "{\"run_id\":\"$RUN\",\"after_seq\":0}" -o /tmp/tc5_s3_full.sse -w "HTTP=%{http_code}\n"
python3 - <<'PYEOF'
import json
frames=[json.loads(l[5:]) for l in open('/tmp/tc5_s3_full.sse') if l.startswith('data:')]
seqs=[f.get('seq') for f in frames]
print('FULL_FRAMES=',len(frames),'SEQ_CONTIGUOUS=',seqs==list(range(1,len(frames)+1)))
d=[f for f in frames if f.get('event_type')=='done']
for x in d:
    p=x.get('payload') or {}
    print('seq',x.get('seq'),'done status=',p.get('status'),'latency_ms=',p.get('latency_ms'),'model_present=','model' in p)
h=[f for f in frames if f.get('event_type')=='hitl.resumed']
print('hitl.resumed_frames=',len(h))
PYEOF
