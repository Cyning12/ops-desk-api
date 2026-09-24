# invoke · 40 · host-v1-sli-four-metrics · 自检/验收

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-24 |
| **帽** | 40 自检/验收（独立真跑） |
| **task** | `docs/tasks/active/task_host_v1_sli_four_metrics.md` |
| **分支** | `task/host-v1-sli-four-metrics` |
| **触 app/** | **否**（`git diff master -- app/` 空） |
| **结论** | **PASS** |
| **commit / push / merge** | **未**（禁） |
| **CLOSE 归档** | **未**（待 merge 后） |

---

## GATE

| human_gate_id | task 表 status | blocks | 40 判定 |
|---------------|----------------|--------|---------|
| HG-TASK-DRAFT | approved | 20-R1, 30 | OK |
| HG-AUDIT-R1 | **approved** | 30 | OK · 可验收码/文档项 |
| HG-GRAPH-MODULES | approved | 30 | OK（本波 none） |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | — |

---

## 真跑命令（cwd = 仓根）

```text
npx spec-wave verify --target . --task docs/tasks/active/task_host_v1_sli_four_metrics.md
→ VERIFY: PASS · exit 0
  HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES = approved

.venv/bin/python -m pytest tests/eval/test_host_v1_sli.py tests/test_llm_budget.py -q --tb=short
→ 37 passed in 0.12s · exit 0

.venv/bin/ruff check evals/agent/sli tests/eval/test_host_v1_sli.py
→ All checks passed! · exit 0
  （注：宽扫 `tests/eval/` 会命中既有 redlines 文件 F811 等，非本波触及面）

git diff master -- name-only -- app/
→ （空）· APP_DIFF_EMPTY=yes
```

---

## 验收对照 D1–D5 / 验收表

| 项 | 结果 | 证据 |
|----|------|------|
| D1 定义表 | **pass** | `SLI_host_v1_four_metrics_v1.md` + `sli_host_v1_four_metrics_v1.yaml`（四项 formula/labels/success/data_source） |
| D2 有数 | **pass** | `evals/agent/sli/aggregate_sli.py` + fixture；Cost 对拍 `cost_per_successful_task`（单测断言） |
| D3 看板 | **pass** | `GUIDE_host_v1_sli_dashboard_v1.md` 三步 + 字段清单；`docs/guides/` 指针 |
| D4 热路径 | **pass** | docs-only · 未改 `app/` · B1 n/a · `graph_change_layer=none` |
| D5 测试/图谱 | **pass** | pytest 37 · ruff 触及面净增 0 · graph none |
| Cost 口径 | **pass** | aggregate 调用 `app.llm.budget.cost_per_successful_task` |
| 出口 G1 CLOSED | **hold** | 40 PASS · **待 merge 后** CLOSE 回写；本窗不归档 |

---

## 出口报告注记

`docs/reports/host_v1_exit_review/REPORT_host_v1_exit_review_20260924_v1_zh.md` GAP **G1** 旁注明：  
**「40 验收 PASS · 待 merge 后 closed」**（勿提前 CLOSE）。

---

## 非范围 / 禁令遵守

未 commit / push / merge · 未改 `app/` 生产语义 · 未重开 V1-A~E · 未伪造 Cost 0。

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-24 | 40 独立真跑 · **PASS** · invoke 落盘 · G1 注记 · 未 CLOSE |
