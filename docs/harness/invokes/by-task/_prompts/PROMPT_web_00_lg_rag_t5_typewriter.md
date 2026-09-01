# PROMPT · web 00 · lg-rag T5 打字机（answer delta）

> **产出者**：api 00（串行波次 1 并行交付）· 2026-08-31  
> **执行仓**：`ops-desk-web`（本仓不改 Vue）  
> **前置闸**：开工前 **必须** 先跑 `ops-desk-api/docs/spec/agent-infra/WAVE_READINESS_lg_rag_sse_v0.md` §1（web T4 CLOSE 后查 T5 的唯一入口）  
> **契约真值**：`ops-desk-api/docs/tasks/active/task_lg_rag_sse_token_stream.md` 00 定夺 + `05` §4.2 / §10.4

---

## 背景

api T5 把终答 `answer` 从 **整段单帧**（T2）扩展为 **多帧 delta + 终帧**（freeze `lg-rag-sse-v1` 扩展，**不新增 event_type**）：

| 帧 | payload | 客户端规则 |
|---|---|---|
| delta 帧（0..n） | `{"delta": "<chunk>"}` | **追加**到当前 run 的答案气泡 |
| 终帧（1） | `{"content": "<full>", "final": true}` | **全量替换**（T2 兼容：旧逻辑只看 content 不破） |
| 占位帧（router/basic 无 aggregator 时） | `{"content": "", "note": "no_aggregator"}` | 无 `final` 标记；按 T2 现行为处理 |

**禁止**：把终帧 `content` append 到 delta 拼接结果之后（05 §10.4 常见坑：T2 整段与 T5 delta 混用未分支）。  
**并存**：`node.progress`/`subtask.progress` 照常；所有帧共享单调 `seq`；`done` 后停止追加。  
**replay**：`POST /lg-rag/replay` 重放含 delta 帧，形状与 live 一致；断网恢复复用 T4 cursor 逻辑即可，无需新协议。

## 建议范围（web task 草稿点）

1. Chat 区打字机：见 `delta` 追加渲染；见 `content+final` 全量替换为最终态  
2. 与现有 T2 整段渲染 **分支**（payload 有 `delta` 键 → 增模式；有 `content` → 替换模式）  
3. 降级：无 delta 帧（provider 不支持流式时 api 只发整段）→ UI 自然退化为 T2 行为，**无需**特判  
4. 联调项（05 §10.4）：增量拼接无乱码 · `done` 后停止追加 · 与 `node.progress` 并存不串台 · 断连 replay 后 delta 序列完整

## 非范围

- 改 api 契约（有异议回 api 00 串行轨）· node.progress token 化 · iOS

## 状态

api T5 实现中（分支 `task/lg-rag-sse-token-stream`）；api 合入后本 Prompt 可派 web 30。
