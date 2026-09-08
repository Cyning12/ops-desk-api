# coding_wiki · volatile

> **层**：volatile · **当前 active task** 专属

## 本波 active

- `lg-rag-sse-subtask-steps`（2026-09-08）：§10.7 `status=step` 里程碑 + provider 禁 `aread` 假流式。真值：05 §10.7 · `progress_stream.emit_subtask_step` · `multi/nodes.py` astream · `lc_evidence_chain/step_hook.py` · `llm/providers/base.py`
- `lg-rag-sse-subtask-message`（2026-09-08）：§10.7 三态帧可选 `message` 中文短句——`subtask_message.py` 确定性模板（纯同步 · 截断 `SUBTASK_MESSAGE_MAX_LEN=200` · 未知 step 兜底含 step 名 · 生成失败降级帧仍发 · 旧客户端忽略未知键）。挂载：`emit_subtask_running` / `emit_subtask_step` / `sse_stream.map_node_update` done。真值：05 §10.7 · `tests/test_lg_rag_sse_subtask_message.py`

## 执行帽速链

- Active：`../tasks/active/`
