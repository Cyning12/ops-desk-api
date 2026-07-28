# Task：Harness 升级至 2.18.0（api）+ wiki_delta 存量迁移

> **状态**：in_progress  
> **类型**：基础设施（过程轨 upgrade + task 字段迁移）  
> **关联**：npm `@cyning/harness@2.18.0` · wiki_delta close 闸 · 维护者指示钉版本升级

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `harness-upgrade-2-18-migrate` |
| **git_branch** | `task/harness-upgrade-2-18-migrate` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 仅过程轨 sync / manifest / task 元字段；不改业务图谱 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack |
| **review_hat** | `20` |
| **thinking_profile** | `shortest` |
| **invoke_retention_profile** | `minimal` |
| **required_invoke_hats** | `30` |
| **experience_capture** | `recommended` |
| **test_strategy** | `recommended` |
| **test_strategy_note** | `upgrade --yes`（不带 `--ide`）；`check` 已是最新；`verify --task`；`ruff` + `pytest tests` |
| **code_quality_bar** | `not_applicable` |
| **orchestration** | 单 task；00 代签双闸（维护者当面：钉 2.18.0 + wiki_delta 迁移） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 00 代签：仅过程轨；不改业务模块边界 |
| HG-TASK-DRAFT | approved | 22-R1 | 维护者 2026-07-28：升级 @cyning/harness@2.18.0 + wiki_delta 存量迁移 |
| **HG-AUDIT-R1** | approved | **30** | 00 代签：基础设施 upgrade；无业务 API 改码 |

---

## 背景与目标

本仓 `manifest=2.17.0`；目标钉 **2.18.0**（`wiki_delta` / 晋升指针关账闸）。只做接入与文档迁移，不做可视化、不强制新建 WikiTrack、不改业务 API。

**完成态**：

- [x] manifest → `2.18.0`
- [x] `upgrade --yes`（无 `--ide`）一把过
- [x] 存量 `docs/tasks/**/task_*.md` 补 `wiki_delta` + `wiki_delta_note`
- [x] `harness check` 已是最新
- [x] 代表性 `verify --task` PASS
- [x] `ruff` + `pytest tests` 绿
- [x] invoke + 自检；PR（写明缺 wiki_delta → close BLOCK；勿默认 `--allow-wiki-gap`）

**不做**：ops-desk-web / cyning-harness 产品仓；Obsidian / 力导向 UI；强制新建 WikiTrack

---

## 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| S5 dirty 挡 upgrade | 先 commit/stash；人判 `--force` | 是 |
| upgrade 冲掉本仓 AGENTS/FRAGMENT overlay | 恢复 `l1/01_modules` + pre-30 / G-L0 关键词 | 是 |
| 存量 task 缺 wiki_delta 导致 close BLOCK | 批量补 `n/a` + note；**不**用 `--allow-wiki-gap` 当绿路径 | 是 |

---

## 验收标准

- [x] manifest 2.18.0 · preset=`fullstack-node-py` · ide 三轨未裁
- [x] check 已是最新
- [x] 全部 task_*.md 含 wiki_delta / wiki_delta_note
- [x] verify --task 本文件 PASS（无业务图谱改 → 不加 `--graph`）
- [x] ruff + pytest 绿；纪律层 PR（待开）

---

### 自检结论（执行者）

| 项 | 内容 |
|---|---|
| **日期** | 2026-07-28 |
| **manifest** | `2.18.0`（from 2.17.0）· preset=`fullstack-node-py` · ide 三轨未裁 |
| **check** | 已是最新 · exit 0 |
| **verify** | PASS · exit 0（未加 `--graph`：graph_change_layer=none） |
| **质量门** | ruff All checks passed · pytest 87 passed |
| **wiki 迁移** | 存量 21 个 done task + 本 active → `n/a` +「本仓未启用 WikiTrack」；无 experience=required∩path |
| **overlay** | 恢复 AGENTS pre-30 / G-L0 关键词；FRAGMENT `l1/01_modules` |
