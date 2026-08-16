# Task Audit R1：lc-evidence-langfuse-tracing

> **task**：`docs/tasks/active/task_lc_evidence_langfuse_tracing.md`  
> **日期**：2026-08-16 · 审查：00 代签（维护者会话「签收」授权推进 30+40）  
> **结论**：`pass` · 建议 `HG-AUDIT-R1=approved`

---

## 核对

| 项 | 审阅 |
|---|---|
| 上游 | 旁路 `lc_evidence_chain` 已合入 master（PR #33） |
| 范围 | ainvoke/CLI CallbackHandler · 独立 tag/`run_name` · 单测开关路径 · G-L1 备注 |
| 非范围 | HTTP · 改 graph · Prompt/Score 平台 · 强制开 tracing |
| 验收 | 关=零回调 · 开=config 契约 · flush · 不改 graph · ruff/pytest |
| failure_paths | 未配置/ImportError/上报失败均不阻断业务 |
| 开关 | 复用 `OPS_CHAT_TRACER` + keys；**不**另造主开关 |
| `wiki_delta` | `n/a` · `graph_change_layer=G-L1`（模块备注增量） |

## 条件

- 30 优先 LangChain `CallbackHandler`；RunnableLambda 抓不到 LLM 时再补 `@traceable`/`trace_span`
- 本机 Langfuse UI 抽检为人工项（不挡机械 40）；50 可标「待维护者 keys 确认」
- **本窗 50 后等维护者确认再 CLOSE/合入**

## HG-AUDIT-R1 建议

**approved**（维护者会话授权 · 本文件留痕）
