# Invoke：00 · eval-goldenset-lg-rag

| 字段 | 值 |
|---|---|
| hat_id | 00 |
| task_slug | eval-goldenset-lg-rag |
| git_branch | `task/eval-goldenset-lg-rag` |
| 授权 | 维护者令「继续开始E2」· 代签过程闸 |
| 角色 | **00 只统筹/签收，不实现**（不写 `evals/agent` fixture、不改 `app/`） |

---

## GATE_VERIFY

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | 开始 E2 | Y | N | Y（待 30 窗） |
| HG-AUDIT-R1 | approved | 00 代签 | Y | Y | Y（**00 本人不改码**） |
| HG-GRAPH-MODULES | approved | 不改图 | Y | — | — |

reviews：`task_eval_goldenset_lg_rag_audit_R1_20260828.md` 存在且 pass？ **是**

pre-30 invoke：`required ∩ {10,20,00}` = 10,00 齐全？ **是**（另有 20 审查文）

verify：`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_eval_goldenset_lg_rag.md`

结论：**可派 30**（新会话）。本窗 00 **零** `app/` / 金标 fixture diff。

---

## 00 定夺（摘要）

见 task 正文。金标根 `evals/agent/golden/`；四切片最小集；确定性评估器；不含 E3–E5；`module=` 本波默认不做。

---

## 下一棒

| 谁 | 何时 | 做什么 |
|---|---|---|
| **30** | 新窗口 · 现在 | 粘贴 `PROMPT_30_execute.md` · 写 fixture |
| **00** | 30 pytest 绿后 | 机械验收 → CLOSE → 才允许 merge [#93](https://github.com/Cyning12/ops-desk-api/pull/93) |
| **00** | E2 **合入后** | 新会话粘贴 `_prompts/PROMPT_00_eval-after-e2.md` · **仅拆 E3** |

本窗与后续 00 窗：**不落地**（不写 `evals/agent/`、不改 `app/`、不起草 E3/E4/E5 active task）。

| 2026-08-28 | 00 起草并代签 · 派 30 · 本人不实现 |
| 2026-08-28 | 维护者令：继续 00 统筹后续 · 钉 §4.1 · 仍不落地 |
