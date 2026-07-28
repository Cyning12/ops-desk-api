# Task：Harness 升级至 2.18.x（api）+ wiki_delta 存量迁移

> **状态**：completed  
> **类型**：基础设施（过程轨 upgrade + task 字段迁移）  
> **关联**：npm `@cyning/harness@2.18.0`→`2.18.2` · wiki_delta close 闸 · 姊妹 `harness-upgrade-2.19.0` / `wikitrack-enable-p0`  
> **合入**：PR #22

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `harness-upgrade-2-18-migrate` |
| **git_branch** | `task/harness-upgrade-2-18-migrate` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 仅过程轨 sync / manifest / task 元字段；不改业务图谱 |
| **wiki_delta** | `none` |
| **wiki_delta_note** | 本 task 仅 upgrade/存量字段；WikiTrack 入口由姊妹 task `wikitrack-enable-p0` 改 `docs/coding_wiki` |
| **review_hat** | `20` |
| **thinking_profile** | `shortest` |
| **invoke_retention_profile** | `minimal` |
| **required_invoke_hats** | `30` |
| **experience_capture** | `recommended` |
| **test_strategy** | `recommended` |
| **test_strategy_note** | `upgrade --yes`（不带 `--ide`）；`check`；`verify --task`；`ruff` + `pytest tests` |
| **code_quality_bar** | `not_applicable` |
| **orchestration** | 与 wikitrack-p0 / 2.19.0 同波 CLOSE |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 00 代签：仅过程轨；不改业务模块边界 |
| HG-TASK-DRAFT | approved | 22-R1 | 维护者 2026-07-28：升级 @cyning/harness@2.18.0 + wiki_delta 存量迁移 |
| **HG-AUDIT-R1** | approved | **30** | 00 代签：基础设施 upgrade；无业务 API 改码 |

---

## 背景与目标

本仓 `manifest=2.17.0`；本波钉 **2.18.0→2.18.2**（`wiki_delta` / 晋升指针 / 两层目录约定）。后续钉 2.19.0 见姊妹 task。

**完成态**：

- [x] manifest → `2.18.0` → `2.18.1` → **`2.18.2`**
- [x] `upgrade --yes` 一把过
- [x] 存量 `docs/tasks/**/task_*.md` 补 `wiki_delta` + `wiki_delta_note`
- [x] `harness check` 已是最新（当时 2.18.2）
- [x] 代表性 `verify --task` PASS
- [x] `ruff` + `pytest tests` 绿
- [x] invoke + 自检；PR #22

**不做**：业务 API；默认 `--allow-wiki-gap`

---

## 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| S5 dirty 挡 upgrade | 先 commit/stash | 是 |
| upgrade 冲 overlay | 恢复 | 是 |
| 缺 wiki_delta | 批量补；不用 `--allow-wiki-gap` 当绿路径 | 是 |

---

## 验收标准

- [x] manifest 2.18.x · preset=`fullstack-node-py` · ide 三轨未裁
- [x] check 已是最新（升级当下）
- [x] 全部 task_*.md 含 wiki_delta / wiki_delta_note
- [x] verify --task PASS
- [x] ruff + pytest 绿；纪律层 PR

---

### 自检结论（执行者）

| 项 | 内容 |
|---|---|
| **日期** | 2026-07-28 |
| **manifest（本 task 终点）** | `2.18.2`（起点 2.17.0） |
| **check / verify** | PASS |
| **质量门** | ruff OK · pytest 87 passed |
| **wiki 迁移** | 存量 done → `n/a` + note；后由 WikiTrack P0 启用 |
| **overlay** | 保留 pre-30 / G-L0 / `l1/01_modules` |

### 经验节（执行者）

- 存量缺 `wiki_delta` 须自补；`upgrade` 不代写。
- overlay 每次 upgrade 后必 diff 恢复。

### KPI

| 项 | 分 |
|---|---|
| Task_KPI% | 100 |

## CLOSE

| 项 | 内容 |
|---|---|
| **日期** | 2026-07-28 |
| **PR** | [#22](https://github.com/Cyning12/ops-desk-api/pull/22) |
| **manifest（本 task）** | `2.18.2`（后续见 2.19.0 task） |
