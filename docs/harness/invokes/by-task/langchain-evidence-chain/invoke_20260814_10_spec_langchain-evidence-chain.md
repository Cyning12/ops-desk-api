# Invoke：10-spec · langchain-evidence-chain

| 字段 | 值 |
|---|---|
| hat_id | 10-spec |
| task_slug / spec_slug | langchain-evidence-chain |
| git_branch | task/langchain-evidence-chain |
| 产出 | docs/spec/lc-evidence-chain/SPEC-langchain-evidence-chain_v1.md（draft） |

## 裁决

- **从 10-spec 起**：新并行架构（LCEL vs LangGraph）、非范围含「勿改 graph」，需要 SPEC 锁边界。  
- 下一棒：人签 `HG-SPEC-SIGNOFF` → 完善 task（已预置 draft）→ 20-task-audit → 人签 `HG-AUDIT-R1` → **维护者执行 30（按 IMPL）**。

## 结论摘要

采用并行 LangChain evidence+answer 链；复用 hybrid_recall；evidence 兼容 sources；默认不挂 chat/stream。
