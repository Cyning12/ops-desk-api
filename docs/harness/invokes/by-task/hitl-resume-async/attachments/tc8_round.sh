#!/bin/bash
# TC8 round: $1=round index; $2=approved|rejected; $3=inherit|immediate|<unknown>
N=${1:?round index}; MODE=${2:-approved}; RMODE=${3:-inherit}
unset NO_PROXY no_proxy http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
A=docs/harness/invokes/by-task/hitl-resume-async/attachments
B=http://127.0.0.1:8050
J=$A/tc8.jar
rm -f $A/r${N}_live.sse $A/r${N}.hdr

echo "=== round $N: start echo run (supervisor) ==="
curl -sN -m 300 -D $A/r${N}.hdr -b $J -X POST $B/api/ops/lg-rag/stream -H "Content-Type: application/json" \
  -d "{\"query\":\"这是一个需要调用工具的任务（就像查询 issue 状态一样）：请调用工具 testing.write.echo 回显一条备注 note=tc8-r$N\",\"mode\":\"supervisor\"}" \
  > $A/r${N}_live.sse 2>/dev/null &
CPID=$!
for i in $(seq 1 30); do grep -q "run.start" $A/r${N}_live.sse 2>/dev/null && break; sleep 1; done
RUN=$(grep -i "x-ops-lg-rag-run-id" $A/r${N}.hdr | tr -d "\r" | awk "{print \$2}")
echo "RUN=$RUN"

for i in $(seq 1 90); do grep -q "waiting_approval" $A/r${N}_live.sse 2>/dev/null && break; sleep 2; done
kill $CPID 2>/dev/null; wait $CPID 2>/dev/null
RID=$(python3 -c "
import json
frames=[json.loads(l[5:]) for l in open('$A/r${N}_live.sse') if l.startswith('data:')]
w=[f for f in frames if f.get('event_type')=='hitl.waiting']
print(w[-1]['payload']['requests'][0]['id'] if w else '')
")
echo "RID=$RID"
[ -z "$RID" ] && { echo "FAIL: no RID round $N"; exit 1; }

echo "=== round $N: decide $MODE (resume_mode=$RMODE) ==="
if [ "$RMODE" = "inherit" ]; then
  PAYLOAD="{\"decision\":\"$MODE\",\"note\":\"tc8 r$N\"}"
else
  PAYLOAD="{\"decision\":\"$MODE\",\"note\":\"tc8 r$N\",\"resume_mode\":\"$RMODE\"}"
fi
curl -s -b $J -X POST $B/api/ops/hitl/requests/$RID/decide -H "Content-Type: application/json" \
  -d "$PAYLOAD" -o $A/r${N}_decide.json -w "DECIDE_HTTP=%{http_code} time=%{time_total}s\n"
python3 -c "import json; d=json.load(open('$A/r${N}_decide.json')); print('request.status=',(d.get('request') or {}).get('status'),'resume=',json.dumps(d.get('resume'),ensure_ascii=False)[:200])" 2>/dev/null || cat $A/r${N}_decide.json

if [ "$RMODE" = "immediate" ]; then
  echo "=== round $N: immediate 模式 · 异步佐证（decide 后立即 replay 应为 409 在飞）==="
  curl -s -D $A/r${N}_imm_409.hdr -b $J -X POST $B/api/ops/lg-rag/replay -H "Content-Type: application/json" \
    -d "{\"run_id\":\"$RUN\",\"after_seq\":0}" -o $A/r${N}_imm_409.body -w "IMM_REPLAY_HTTP=%{http_code}\n"
  grep -iE "retry-after" $A/r${N}_imm_409.hdr; cat $A/r${N}_imm_409.body; echo
  echo "$RUN" > $A/r${N}.run; echo "$RID" > $A/r${N}.rid
  exit 0
fi
if [ "$RMODE" != "inherit" ]; then
  echo "(unknown resume_mode 已在 decide 处验 400 · 本轮止)"
  echo "$RUN" > $A/r${N}.run; echo "$RID" > $A/r${N}.rid
  exit 0
fi

echo "=== round $N: resume（计时 · 断言已受理形）==="
curl -s -b $J -X POST $B/api/ops/hitl/requests/$RID/resume -H "Content-Type: application/json" -d '{}' \
  -o $A/r${N}_resume.json -w "RESUME_HTTP=%{http_code} time=%{time_total}\n" | tee $A/r${N}_resume.timing
python3 -c "
import json
d=json.load(open('$A/r${N}_resume.json'))
print('top_keys=',sorted(d.keys()))
r=d.get('resume') or {}
print('resume.status=',r.get('status'),'resume_keys=',sorted(r.keys()))
rp=d.get('replay') or {}
print('replay.cursor=',rp.get('cursor'),'replay_keys=',sorted(rp.keys()))
"

echo "=== round $N: 在飞即刻 replay（预期 409 + Retry-After: 2）==="
curl -s -D $A/r${N}_409.hdr -b $J -X POST $B/api/ops/lg-rag/replay -H "Content-Type: application/json" \
  -d "{\"run_id\":\"$RUN\",\"after_seq\":0}" -o $A/r${N}_409.body -w "INFLIGHT_REPLAY_HTTP=%{http_code}\n"
grep -iE "retry-after" $A/r${N}_409.hdr; cat $A/r${N}_409.body; echo

if [ "$N" = "1" ]; then
  echo "=== round 1 专项: 在飞二次 resume（预期 409）==="
  curl -s -b $J -X POST $B/api/ops/hitl/requests/$RID/resume -H "Content-Type: application/json" -d '{}' \
    -o $A/r1_dup_inflight.json -w "DUP_INFLIGHT_HTTP=%{http_code}\n"
  cat $A/r1_dup_inflight.json; echo
fi

echo "=== round $N: 等沉降（replay 转 200）==="
SETTLED=0
for i in $(seq 1 120); do
  code=$(curl -s -o /dev/null -w "%{http_code}" -b $J -X POST $B/api/ops/lg-rag/replay -H "Content-Type: application/json" -d "{\"run_id\":\"$RUN\",\"after_seq\":0}")
  if [ "$code" = "200" ]; then echo "SETTLED@poll$i"; SETTLED=1; break; fi
  sleep 2
done
[ "$SETTLED" = "0" ] && echo "WARN: round $N not settled within 240s"

echo "=== round $N: 全量 replay 对拍（seq 连续 · 终帧逐键）==="
curl -s -b $J -X POST $B/api/ops/lg-rag/replay -H "Content-Type: application/json" \
  -d "{\"run_id\":\"$RUN\",\"after_seq\":0}" -o $A/r${N}_full.sse -w "FULL_REPLAY_HTTP=%{http_code}\n"
python3 -c "
import json
frames=[json.loads(l[5:]) for l in open('$A/r${N}_full.sse') if l.startswith('data:')]
seqs=[f.get('seq') for f in frames]
print('FRAMES=',len(frames),'SEQ_CONTIGUOUS=',seqs==list(range(1,len(frames)+1)))
d=[f for f in frames if f.get('event_type')=='done']
for x in d:
    p=x.get('payload') or {}
    print('seq',x.get('seq'),'done status=',p.get('status'),'latency_ms=',p.get('latency_ms'),type(p.get('latency_ms')).__name__,'keys=',sorted(p.keys()),'model_present=','model' in p)
h=[f for f in frames if f.get('event_type')=='hitl.resumed']
print('hitl.resumed_frames=',len(h))
"

echo "=== round $N: 沉降后二次 resume（预期 409 · TC5）==="
curl -s -b $J -X POST $B/api/ops/hitl/requests/$RID/resume -H "Content-Type: application/json" -d '{}' \
  -o $A/r${N}_dup_settled.json -w "DUP_SETTLED_HTTP=%{http_code}\n"
head -c 300 $A/r${N}_dup_settled.json; echo

echo "$RUN" > $A/r${N}.run; echo "$RID" > $A/r${N}.rid
echo "=== round $N done ==="
