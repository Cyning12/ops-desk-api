# Task Audit R1：lc-evidence-retrieve-langfuse

> **task**：`docs/tasks/active/task_lc_evidence_retrieve_langfuse.md`  
> **日期**：2026-08-19 · 审查：00 代签（维护者会话「签收」授权推进 30+40）  
> **结论**：`pass` · 建议 `HG-AUDIT-R1=approved`

---

## 核对

| 项 | 审阅 |
|---|---|
| 上游 | 旁路 Langfuse 已合入（`task_lc_evidence_langfuse_tracing`）；grade/answer 已有 generation 先例 |
| 范围 | 仅 `retrieve.py`：embed + 条件 rerank 包 `trace_span(run_type=llm)` · 单测 mock |
| 非范围 | Chat `rag_nodes.py`（本签收明示不同步）· SDK v4 · 改 hybrid_recall / graph |
| 验收 | embed/rerank generation · rerank 关则无 rerank span · tracing 关零依赖 · ruff/pytest · 不改 graph.py |
| failure_paths | 未配置/ImportError/上报失败均不阻断业务 |
| 开关 | 复用 `OPS_CHAT_TRACER` + `trace_span` no-op；**不**另造主开关 |
| `wiki_delta` | `n/a` · `graph_change_layer=none` |

## 条件

- 30 对齐 `answer.py` / `grader.py` 的 `trace_span(..., run_type="llm", model=...)`
- 本机 Langfuse UI 抽检为人工项（不挡机械 40）
- **父窗验收通过后** CLOSE / PR / merge master

## HG-AUDIT-R1 建议

**approved**（维护者会话「签收」· 范围锁定仅旁路 `retrieve.py` · 本文件留痕）
