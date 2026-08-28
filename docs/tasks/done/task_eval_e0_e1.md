# Task：Eval E0 签收 + E1 SLI 字典

> **状态**：completed（2026-08-28 · 00 文档验收 · 禁 30 改 `app/`）  
> **类型**：规划签收 / 观测契约  
> **上游**：`docs/spec/agent-infra/04_eval_and_observability_plan_v0.md` · `eval/ROADMAP_eval_observability_v0.md`  
> **分支**：`docs/eval-e0-e1`  
> **无关**：勿拉 DEF-003/004 RAG；勿开 Langfuse SDK v4（DEF-001）；禁止改 `chat/graph.py`；禁止本波改 `tracing.py` / `app/`。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `eval-e0-e1` |
| **git_branch** | `docs/eval-e0-e1` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `none` |
| **test_strategy_note** | 纯文档；字典对照已有 span 键，无 runner |
| **code_quality_bar** | `standard` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 不改 coding_wiki 正文 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无 |
| **orchestration** | E0 签收 + E1 字典同一 PR；运维备忘另 commit 同 PR |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-28 · **00 代签 · 维护者令签收 spec 并统筹 E0+E1** |
| HG-AUDIT-R1 | approved | 30 | 2026-08-28 · **00 代签** · 见 `docs/harness/reviews/task_eval_e0_e1_audit_R1_20260828.md`（本波无 30） |
| HG-SPEC-SIGNOFF | approved | 00 | 2026-08-28 · 04 + eval ROADMAP · **00 代签 · 维护者令** |
| HG-GRAPH-MODULES | approved | — | 不改图谱 · **00 代签** |

---

## 范围

**E0**：签收 04 与 `eval/ROADMAP`（Langfuse 默认、混合 harness、E0–E5 波次、硬约束）。策略轨已收官，主线改为 E2。

**E1-a**：ROADMAP §3 升级为签收真值：metadata / score / `module` 对照源码标 **已埋 / 缺口**。

**E1-b**：缺口清单；**00 定夺不改 `app/`**（补 `module=` 随 E2；score 封装随 E3/E4）。

**同 PR 另 commit**：`docs/deployment/ops-sync-gha-config.md`（sync 运维备忘，与 Eval 正文解耦）。

---

## 验收标准

- [x] 04 状态 `active` · `HG-SPEC-SIGNOFF=approved`
- [x] ROADMAP §3 已埋/缺口表与 `builder` / `intent` / `supervisor` / `gateway` / `critic` 源码一致
- [x] E1-b 写明本波不改码
- [x] agent-infra README 测评轨回写
- [x] 无 `app/` / `tests/` 业务 diff（conftest 除外；本 task 无）
- [ ] E2 金标（**非本波**）

---

## 下一棒

`eval-goldenset-lg-rag`（E2）：`golden/router` · `golden/strategy_builder` · 1 条 E2E；可顺带补 `module=`。

---

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-28 |
| 定稿 | E0 签收 + E1 字典；不改 tracing |
| 归档 | `docs/tasks/done/task_eval_e0_e1.md` |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-28 | 00 统筹 E0+E1 文档收官 |
