# Invoke · 30 · lg-rag-sse-subtask-message

- **hat**：30（实现）
- **task_slug**：`lg-rag-sse-subtask-message`
- **日期**：2026-09-08
- **分支**：`task/lg-rag-sse-subtask-message`（已核对 `git branch --show-current`）

## GATE_VERIFY

| human_gate_id | task 表 status | blocks_hats | 结论 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | ✅ |
| HG-AUDIT-R1 | approved | 30 | ✅ 可 30 |
| HG-GRAPH-MODULES | approved | — | ✅ |

- `npx dsh-coding-kit verify --target . --task docs/tasks/active/task_lg_rag_sse_subtask_message.md` → **VERIFY: PASS**（exit 0）
- pre-30 invoke：10 / 00 齐全（见本目录与维护者授权记录）

## 工作

- 新模块 `app/ops/lg_rag/subtask_message.py`：确定性模板（纯同步 · 无 LLM · 无 CoT/evidence 全文）· `SUBTASK_MESSAGE_MAX_LEN = 200` 截断 · 未知 step / 缺 detail 兜底短句（含 step 名，禁空串）。
- 挂载三态：`emit_subtask_running` / `emit_subtask_step`（progress_stream）+ `sse_stream.map_node_update` done；message 生成失败打日志降级、帧仍发、不中断节点。
- 单测 `tests/test_lg_rag_sse_subtask_message.py`（20 例，mock，不连真 LLM）。
- 文档：05 §10.7 payload 表 message 行 + 联调项 + 旧客户端忽略未知键 + §11.4 修订行；G-L1 `01_modules.md` / `10_flow_lg_rag.graph.yaml` 备注；G-L2 indexes 增 3 个 build 符号；`volatile.md` 短注。
