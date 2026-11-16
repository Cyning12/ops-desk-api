# invoke_30 · 实现（fix-planframe-truncation）

## 内容

1. **修法裁定（R 节）**：落库全文 · SSE 帧面截断保持——持久化层不丢信息，
   展示/推送面保留既有上限。
2. **修复**：
   - `app/ops/lg_rag/sse_stream.py`：拆两常量——`_PAYLOAD_MAX=800`（SSE 帧面 ·
     数值不动）/ 新增 `_PERSIST_PAYLOAD_MAX=32_000`（落库保险丝 · 对齐
     `_ANSWER_MAX` 先例）；`_summarize_payload(node_output, max_len=...)` 参数化
     （answer_preview 上限 min(200, max_len)）；新增 `persist_node_payload(
     node_name, node_output)`（subtask 节点 = 32_000 摘要 + status=done +
     build_subtask_done_message 全文 dict · answer 节点同 `_ANSWER_MAX` 截断 ·
     其余 = 32_000 摘要）；`emit` 增 kw-only `persist_payload=None`（None 时落
     payload 本体 · 其余帧型零 diff）；主循环双面计算传入。
   - `app/ops/hitl/resume.py`：`ResumeEventSink._emit` 改落
     `persist_node_payload(...)` 全文（恢复段无 SSE 推送面）。
   - `app/ops/lg_rag/history.py`：`summarize_subtasks` 读时截断——新增常量
     `SUBTASK_RESULT_MAX_CHARS=800` / `ANSWER_PREVIEW_MAX_CHARS=200` 与
     `_truncate_str` / `_read_safe_summary`（结构值 json.dumps ≤上限保留否则降级
     截断字符串 · 承 SSE 旧口径），保 history 响应尺寸契约。
3. **测试**（真 PG · 五键 blank 前缀 · 新增五例）：
   - test_lg_rag_sse_stream.py::test_plan_frame_sse_truncated_but_persisted_full
     （"很"*900 subtasks · SSE 面 str≤800 尾"…" · persist kwargs payload.subtasks
     ==原 list · seq 对齐 · answer 帧 SSE/落库同 payload 零 diff 对照）
   - test_lg_rag_sse_stream.py::test_persist_node_payload_subtask_done_shape
     （done 帧 status/message 齐 · subtask_result 全文 dict）
   - test_hitl_resume_events.py::test_resume_persists_full_plan_payload
     （ResumeEventSink 落全文）
   - test_chat_history_api.py::test_summarize_subtasks_read_truncates_full_payload
     （读时截断 800/200）
   - test_chat_history_api.py::test_summarize_subtasks_small_payload_passthrough
     （小 payload 结构化透传对照）
4. **图谱**：`docs/_tech_graph/l1/01_modules.md` lg_rag 行（:35）fix-planframe
   备注 + HG-GRAPH-MODULES 签收行（承 :45 先例）。
5. **freeze 核实**：05 spec 钉 answer 32_000/message ≤200/input·detail 截断预览，
   未钉 node.progress 键值 800 上限 → freeze 词表不受影响 · workspace 契约文档
   无需同步（范围第五条裁定）。

## 验证台账

| 项 | 结果 |
|---|---|
| 新增五例（真 PG · 五键 blank 前缀） | 5 passed |
| 目标七件（sse_stream/sse_token_stream/sse_subtask_message/hitl_resume_events/chat_history_api/lg_rag_run_store/lg_rag_runs_readonly_api） | 109 passed |
| `ruff check app tests` | All checks passed |
| 全量 pytest | （40 收口时回填） |

## 偏差

- D1（承 10）：resume.py 内发射器实际类名为 `ResumeEventSink`（10 草稿记
  `_ResumeEmitter` 为描述性称呼 · 同物）。
- D2：`_read_safe_summary` 对结构值采 json.dumps ≤上限保留、超限降级截断
  字符串（承 SSE 面 `_summarize_payload` 旧口径 · 非逐键 800）。

## 结果

30 实现完成，进 40 收口。
