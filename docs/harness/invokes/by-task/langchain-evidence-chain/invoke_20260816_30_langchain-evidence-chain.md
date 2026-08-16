# Invoke：30 · langchain-evidence-chain

| 字段 | 值 |
|---|---|
| hat_id | 30 |
| task_slug | `langchain-evidence-chain` |
| task_paths | `docs/tasks/active/task_langchain_evidence_chain.md` |
| related_review_or_none | `docs/harness/reviews/task_langchain_evidence_chain_audit_R1_20260814.md` |
| git_branch | `task/langchain-evidence-chain` |
| created_utc_or_local | 2026-08-16 |
| notes | 维护者手写主码；Agent 辅助调试/验收基建；不改 graph |

## GATE_VERIFY（首输出 · 真值在 task 表）

| human_gate_id | task表status | blocks_30 | 30可开工？ |
|---|---|---|---|
| HG-TASK-DRAFT | approved | N | Y |
| HG-AUDIT-R1 | approved | Y | Y |

reviews R1：是 · pre-30 invoke 10：是 · 结论：可开工

## 交付范围（30）

1. 包 `app/ops/lc_evidence_chain/`：retrieve → grade/decide → answer（LCEL）
2. 复用 `hybrid_recall` + 可选 CE；包内 `decide_grade`（不改 graph）
3. `scripts/lc_evidence_smoke.py` · `tests/test_lc_evidence_chain.py`
4. G-L1：`docs/_tech_graph/l1/01_modules.md` 旁路模块与契约
5. `answer_partial`：注入「仅部分证据」约束

## 执行人区分（commit）

| commit | 执行人 | 说明 |
|---|---|---|
| `ede6f89` | 维护者 30 | 旁路主码 + Relevance 共用扩展 |
| `1f9bf96` | Agent 辅助 | 单测 / smoke / G-L1 / IMPL |
| （后续） | Agent 辅助 | answer_partial + 关账工程 |

## 禁止

- 改 `app/ops/chat/graph.py` 拓扑
- 默认切换生产 `chat/stream` 到本链
