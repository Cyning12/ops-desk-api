# Task Audit R1：langchain-evidence-chain

> **hat_id**：20-task-audit  
> **task**：`docs/tasks/active/task_langchain_evidence_chain.md`  
> **SPEC**：`docs/spec/SPEC-langchain-evidence-chain_v1.md`（已签）  
> **日期**：2026-08-14

---

## 结论

| 项 | 值 |
|---|---|
| **判定** | **pass** |
| **建议 HG-AUDIT-R1** | **approved**（范围清晰 · 30 交维护者手写 · IMPL 齐全） |
| **下一棒** | 维护者确认闸表后按 `IMPL_langchain-evidence-chain_v1.md` S0–S6 开工 |

## 核对

| 项 | 审阅 |
|---|---|
| 与 SPEC 对齐 | OK |
| 非范围含勿改 graph | OK |
| 验收可勾选 | OK |
| failure_paths | OK |
| S0–S6 指引 + IMPL 分文件 | OK |
| `task lint` | PASS（起草时） |
| 思考轮 / 自检结论 | OK |

## 条件（写入签收说明即可）

1. 30 不得修改 `app/ops/chat/graph.py` 拓扑  
2. 必须调用 `hybrid_recall`，禁止复制召回 SQL  
3. 默认不切换生产 `chat/stream`

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-14 | 首审 pass |
