# Invoke：30 执行编码 · llm-provider-v1（补录）

> **补录说明**：本文件为 2026-07-20 流程补录。执行时未按纪律落盘 invoke，现按 `TEMPLATE_invoke.md` 补齐，交付摘要为当时实际结果。

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40 自检闭环） |
| task_slug | `llm-provider-v1` |
| freeze_id | — |
| task_paths | `docs/tasks/active/task_llm_provider_v1.md` |
| related_review_or_none | 无 |
| git_branch | `task/llm-provider-and-chat-answer` |
| worktree_root | — |
| created_utc_or_local | 2026-07-16（执行日） |
| notes | 已合并：PR #1 |

---

## 可复制 Prompt 快照

```text
## 30 开工（签闸后 · 须 GATE_VERIFY）

@docs/tasks/active/task_llm_provider_v1.md
@docs/harness/prompts/30-execute-code.md
@docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md
@docs/_tech_graph/01_struct.md

【开工前】
1. 首输出 FRAGMENT_30_gate_verify 闸扫描表（读 task 人工闸表，比对用户声称）
2. 仅当 HG-AUDIT-R1=approved（task 表）→ 可改码

【实现】
- 分支：task/llm-provider-and-chat-answer · 仅 task 所列路径
- 范围：SiliconFlow / 百炼 Provider、工厂与 fallback、Chat StateGraph 节点、
  SSE 事件映射、ops_runs / ops_run_events 持久化、Chat 测试
- test_strategy: required → 先红后绿

【Verify】
- pytest tests · ruff check app tests · ./scripts/graph-compile.sh
```

---

## 交付摘要（本帽结束时填）

- **验证命令**：`pytest tests`（绿）· `ruff check app tests`（绿）· `./scripts/graph-compile.sh`（绿）
- **变更路径**：`app/llm/**`（providers、factory、model_catalog、schema）、`app/ops/chat/**`（graph/nodes/service/sse/router）、`tests/test_chat_*.py`、`tests/test_llm_providers.py`、`docs/_tech_graph/10_flow_chat.*`
- **下一棒**：CLOSE（PR #1 已合并 master）

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-20 | 流程补录：执行时未落盘 invoke，按模板补齐 |
