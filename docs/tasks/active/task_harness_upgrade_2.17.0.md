# Task：Harness 升级至 2.17.0（api）

> **状态**：ready  
> **类型**：基础设施（过程轨 upgrade）  
> **关联**：npm `@cyning/harness@2.17.0` · 维护者指示升到最新

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `harness-upgrade-2.17.0` |
| **git_branch** | `task/harness-upgrade-2.17.0` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 仅过程轨 sync / manifest；不改业务图谱 |
| **review_hat** | `20` |
| **thinking_profile** | `shortest` |
| **invoke_retention_profile** | `minimal` |
| **required_invoke_hats** | `30` |
| **test_strategy** | `recommended` |
| **test_strategy_note** | `upgrade --yes`（不带 `--ide`）；`check` 已是最新；可选 `status --json` / `status --check` 冒烟 |
| **code_quality_bar** | `not_applicable` |
| **orchestration** | 单 task；00 代签双闸（维护者当面：升到最新） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 00 代签：仅过程轨；不改业务模块边界 |
| HG-TASK-DRAFT | approved | 22-R1 | 维护者 2026-07-28：更新 cyning-harness 到最新版 |
| **HG-AUDIT-R1** | approved | **30** | 00 代签：基础设施 upgrade；无业务改码 |

---

## 背景与目标

本仓 `manifest=2.16.1`；npm latest = **2.17.0**。升到最新并冒烟。

**完成态**：

- [ ] manifest → `2.17.0`
- [ ] `upgrade --yes`（无 `--ide`）一把过
- [ ] `harness check` 已是最新
- [ ] 冒烟记录；invoke + 自检；PR

**不做**：web/ios 升级；业务改码；强制 pre-commit；P3b

---

## 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| S5 dirty | 先 commit/stash；人判 `--force` | 是 |
| ide 被裁 | 记录，不擅自 `--ide` 重跑 | 人判 |

---

## 验收标准

- [ ] manifest 2.17.0 · preset=`fullstack-node-py`
- [ ] check 已是最新
- [ ] 纪律层 commit + PR
