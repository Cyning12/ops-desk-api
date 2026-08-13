# Invoke：CLOSE · rag-sparse-arm-c

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | CLOSE |
| task_slug | `rag-sparse-arm-c` |
| related_30 | invoke_20260812_30_40_rag-sparse-arm-c.md |
| related_50 | invoke_20260812_50_rag-sparse-arm-c.md（PASS 附条件） |
| git_branch | `task/rag-sparse-arm-c`（任务元信息；关账在当前工作树执行） |
| created_utc_or_local | 2026-08-13 |
| notes | 维护者实跑 r4-C + Q6 裁决已落地 → 实验结案；生产第二路默认仍 `fts` |

---

## CLOSE 结论：**PASS（实验结案 · 不上生产默认）**

### 关键证据

| 项 | 值 | 证据 |
|---|---|---|
| `reports/r4-C.yaml` | completed **73/73** · pass **53/73** | `summary.partial=false` |
| zh2zh recall@5 | **19/20（+10pp vs r4-2 17/20）** | `summary.recall_at5_by_quadrant` |
| sparse 路非空命中 | **73/73** | Q6 勘误 #3 · 逐条 `keyword_hits` |
| negative | **9/11**（G62/G66 红线） | Q6 报告 |
| Q6 裁决 | **C sparse 不上默认；开关保留** | `experiments/rag_compare/REPORT_q6_arms_vs_baseline_20260812.md` |

### 裁决摘要（原文一句）

> C sparse | **不上默认**；开关保留；优先「控噪」再谈默认 | zh2zh 达标线（+10pp）但 negative −；总 pass 未赢

### 关账动作

- 验收勾选 + KPI + CLOSE 节回写 task
- `npx @cyning/harness task close --file docs/tasks/active/task_rag_sparse_arm_c.md --yes`
- 归档 → `docs/tasks/done/task_rag_sparse_arm_c.md`
- **不改**生产默认 `RAG_SECOND_PATH=fts`
