# Invoke：30（含 40）· lg-rag-sse-token-stream（T5）

| 字段 | 值 |
|---|---|
| hat_id | 30（含 40） |
| task_slug | `lg-rag-sse-token-stream` |
| task_paths | `docs/tasks/active/task_lg_rag_sse_token_stream.md` |
| related_review_or_none | `docs/harness/reviews/task_lg_rag_sse_token_stream_audit_R1_20260831.md` |
| git_branch | `task/lg-rag-sse-token-stream` |
| created_utc_or_local | 2026-08-31 |
| notes | 00 代签 HG-AUDIT-R1 后派发；**仅 T5 answer token delta**；禁止 T6 / C0–C4 / 重开 T3·T4 / 改 chat/graph.py / 新 event_type / 新 freeze id / 新依赖边 / cancel；前一棒 30 被运行时中断，本棒先核对部分实现（answer_stream.py + nodes.py import 行）再继续 |

---

## 人工闸扫描（GATE_VERIFY · 30 重填 · 读 task 表）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---|---|---|---|---|---|
| HG-TASK-DRAFT | approved | 00 代签 | Y | N | Y |
| HG-AUDIT-R1 | approved | 00 代签 + R1 文 pass | Y | Y | Y |
| HG-GRAPH-MODULES | approved | 不新增一级模块 · 00 代签 | Y | N | Y |

reviews：`task_lg_rag_sse_token_stream_audit_R1_20260831.md` 存在且内容 pass？ **是**

pre-30 invoke：00 + 10 已落盘？ **是**

机械：`npx dsh-coding-kit@1.10.0 verify --target . --task docs/tasks/active/task_lg_rag_sse_token_stream.md` → **VERIFY: PASS**（exit 0 · 本棒复跑）

结论：**可进入读码/改码**（30 首输出已重扫本表）

---

## 可复制 Prompt 快照

hat_id：30（含 40 自检）  
task_slug：lg-rag-sse-token-stream  
本帽禁区：不越 T5；不 import chat/session；不新增 event_type；不改 Vue；不直推 master；不切分支不 push

首动作：GATE_VERIFY（FRAGMENT_30_gate_verify）→ 通过再改码。

00 定夺摘要：
- `answer` 单 event_type：delta 多帧 `{"delta"}` + 终帧 `{"content", final:true}`（T2 兼容）
- aggregator 必做 / direct_answer 同协议或降级（自检写理由）；basic 占位帧不变
- token 仅归属终答 LLM；无新依赖边；降级整段兜底 + 日志
- 全帧共享单调 seq；落盘/replay 含 delta；freeze 扩展 lg-rag-sse-v1
- PR 勿 auto-merge；可 api-only 先合

验证：相关 pytest · ruff · graph-compile · 旧测零破坏 · chat/graph.py 零 diff

完成后：回填本 invoke 交付摘要 + task「自检结论（执行者）」；**不 CLOSE（留给 00）**；不 push。

## 签收栏

00 代签落盘 · 维护者 Prompt 授权 · 2026-08-31 · VERIFY PASS

---

## 交付摘要

| 项 | 结果 |
|---|---|
| GATE_VERIFY | PASS · 可开工（HG-AUDIT-R1/GRAPH/DRAFT approved · verify exit 0） |
| 部分实现核对 | `answer_stream.py`（前一棒 30 留）与 00 定夺一致，保留；`multi/nodes.py` import 行保留并完成接线 |
| 实现 | provider 流式桥接：`complete_stream` + contextvar token sink；sse_stream emit 循环挂 sink、delta 帧与下一 update 竞速吐出；`map_node_update` aggregator/direct_answer → 终帧 `{content, final:true}`；aggregator / **direct_answer 同协议（未降级）**；流式异常桥内降级整段 + 日志；basic 占位帧不变 |
| 测试 | 新增 `tests/test_lg_rag_sse_token_stream.py`（12 测：桥无 sink/有 sink/异常降级 · delta 帧序+拼接==终帧 · 并存不串台 · HTTP 降级 · direct_answer 同协议 · basic 占位不变 · 终帧外形 · replay 含 delta · 401/404 不变）；五文件 **46 passed** |
| 自检 | verify exit 0 · ruff PASS · pytest 46 passed · graph-compile exit 0 · lint-wiki-delta PASS |
| chat 依赖 | `app/ops/chat/graph.py` **零 diff**；`app/ops/lg_rag/**` **无** import chat/session（既有 ast 测试绿） |
| 文档/图谱 | 05 §4.2 answer 行 + T5 冻结补充 + §10.4「api 提供」实现句 + 修订记录；`01_modules.md` lg_rag 备注 + 人签记录；`10_flow_lg_rag.graph.yaml`（+生成物 md / graph.json）；G-L2 `by_path_lg_rag` / `by_symbol_lg_rag` 同步 |
| 已知未测项 | 真 LLM 联调（task 钉死不连真 LLM → §11 T5 联调段）；TCP 断连时 sink 队列冲刷时序 |
| 收尾 | task 验收 12 条全勾 + 自检结论（执行者）表 + 修订记录 30+40 行；**不 CLOSE（留给 00）**；commit 不 push |

关键路径：
- `app/ops/lg_rag/answer_stream.py`（新）· `sse_stream.py` · `nodes.py`（direct_answer）· `multi/nodes.py`（aggregator）
- `tests/test_lg_rag_sse_token_stream.py`（新）
- `docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §4.2/§10.4 · `docs/_tech_graph/l1/01_modules.md` · `10_flow_lg_rag.graph.yaml` · G-L2 indexes
