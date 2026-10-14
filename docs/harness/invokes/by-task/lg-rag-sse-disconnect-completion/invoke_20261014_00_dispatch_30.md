# invoke · 00 · 派发 30 · lg-rag-sse-disconnect-completion

| 项 | 内容 |
|----|------|
| **时间** | 2026-10-14 |
| **帽** | 00（delegate-only · 本窗未改 `app/` · 仅编排） |
| **前置** | 三闸 approved · D1=A-only · D2=`done{status:'disconnected'}` · D3=api-only · `verify` **PASS**（签闸后机跑） |
| **签闸留痕** | `invoke_20261014_00_gate_signoff.md` |

## GATE 扫描（00 派发前）

| human_gate_id | task表status | blocks_30 | 30可开工？ |
|---------------|--------------|-----------|------------|
| HG-TASK-DRAFT | approved | Y | Y |
| HG-AUDIT-R1 | approved | Y | Y |
| HG-GRAPH-MODULES | approved | Y | Y |

reviews：R1 存在且机读通过（00 软修结论节后）· **是**  
pre-30 invoke：10 / 20 / 00 齐全 · **是**  
D1：**A-only**（已签 · 禁做 Wave B）

## 下一棒 Prompt 摘要（交子 Agent 30）

- hat **30** · Wave **A only** · 红测先行（TC1）
- 收尾帧钉死：`done` + `status:'disconnected'`（禁 silent 新 `event_type`）
- 锚点：`sse_stream.py` finally/cancel anext · `event_store.run_stream_closed` · replay 409
- 零 diff：HITL waiting_approval · completed · 真在飞 409（TC3）
- 回写：05 §10.3 实然 · `01_modules.md` / flow 备注 · experience
- 参照：web 联调 TC4 `jc_tc4_network.json` / `jc_tc4_inflight_409.png`
- 禁：`uv.lock` · Wave B worker · 改 web · replay≡resume

## 纪律

本窗未改实现码 · 已派子 Agent：**30**
