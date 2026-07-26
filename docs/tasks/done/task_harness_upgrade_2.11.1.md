# Task：Harness 升级至 2.11.1 + F1/F2 遗留回归

> **状态**：completed  
> **类型**：基础设施（过程轨 upgrade）  
> **关联**：`Projects/docs/harness/guides/CHECKLIST_harness_pilot_dogfood_v1_zh.md` ·  
> `ANALYSIS_upgrade_wizard_friction_20260725_v1_zh.md` · npm `@cyning/harness@2.11.1`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `harness-upgrade-2.11.1` |
| **test_strategy** | `recommended` |
| **test_strategy_note** | F1：干净仓 `upgrade --yes` 一把过（无 S5 自脏中止）；F2：有死字段时 stdout 见 WARN 清单；`harness check` 已是最新；`ruff`/`pytest` 不因过程轨同步而红 |
| **code_quality_bar** | `not_applicable` |
| **orchestration** | 单 task；00 代签双闸（RUNBOOK 基础设施惯例） |
| **git_branch** | `task/harness-upgrade-2.11.1` |
| **experience_capture** | `recommended` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 00 代签：仅过程轨 / IDE starter，不改业务模块边界 |
| HG-TASK-DRAFT | approved | 22-R1 | 维护者指示升级 + 遗留回归 |
| **HG-AUDIT-R1** | approved | **30** | 00 代签（用户 2026-07-26 授权）：基础设施 upgrade，无业务逻辑 |

---

## 背景与目标

产品包 **2.11.1** 已修 upgrade 摩擦 **F1**（先 apply 再写 `local.json`）与 **F2**（manifest 重写前 WARN 死字段）。本仓当前 `manifest.version=2.2.1`，需升级并做遗留回归；试点仓 `ops-desk-web`（2.11.0）同步升至 2.11.1 勾 checklist。

**完成态**：

- [x] `.cyning-harness/manifest.json` → `version: 2.11.1`
- [x] F1 回归：干净工作区单次 `upgrade --yes` **一把过**（无「因自身 local.json 脏而 S5 中止」）
- [x] F2 回归：若升级前有 schema 外字段 → stdout 出现 WARN 清单；升级后仅五字段
- [x] `npx @cyning/harness check` → 已是最新
- [x] `npx @cyning/harness verify --target . --task <本文件>` PASS（或仅闸/审计类可解释 warn）
- [x] 可选摸底：`lifecycle show` · `discipline show`
- [x] invoke 落盘 + 自检回填

**不做**：

- 业务 API / DB 改码
- F3（ide 裁剪提示）产品补丁（未进 2.11.1 范围）；本仓用 `--ide cursor,claude,agents` 对齐既有 ide

---

## 范围

- `.cyning-harness/*` · `docs/harness/prompts/*` · IDE starter（Cursor/Claude/AGENTS 嵌入段）
- 本 task / invoke / review 文档
- （跨仓）`ops-desk-web` 同步 upgrade 作 dogfood 回归证据（不改 web 业务码）

## 非范围

- `app/**` · `tests/**` 业务逻辑
- 产品仓 cyning-harness 改码

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 工作区非干净即 upgrade | S5 中止 | 是 | 先 commit/stash |
| F1 仍复现（S5 因 local.json） | 记失败 + 回产品 | 是 | 摩擦未关 |
| verify 因缺 review | 补 R1 文 | 是 | 按 2.11+ 要求 |

## 验收标准

- [x] manifest `version` = `2.11.1`，仅 schema 五字段
- [x] F1：单次 upgrade 退出码 0，日志无「因 local.json 脏」S5 中止
- [x] F2：死字段场景有 WARN（api 升级前已是五字段 → 注入死字段复现 WARN）
- [x] `harness check` 已是最新
- [x] `ruff check app tests` · `pytest tests` 仍绿（过程轨不影响业务）

---

### 自检结论（执行者）

- **F1 PASS**：api 干净仓 `npx @cyning/harness@2.11.1 upgrade --yes --ide …` 一把过；日志顺序为 apply →「已更新 local.json」→「升级完成」，无 S5。
- **F2 PASS**：临时注入 `name/harness_version/tech_graph_dir/tasks_dir/hooks` 后重跑，stdout：`WARN: manifest 以下非标准字段将被移除（2.3+ 仅五字段 · 见 ONBOARDING）: name, harness_version, tech_graph_dir, tasks_dir, hooks`；落盘恢复五字段。
- **web dogfood**：`2.11.0→2.11.1` 在 profile 已 commit 后一把过；`check` 已是最新。
- **新摩擦 F1b**：`--ide` 在 apply 前写脏 `profile.json` 仍会 S5（web 首次复现）；建议产品下一 patch 与 F1 同序。
- Verify：`harness check` 已是最新；`verify --task` PASS；`lifecycle show` / `discipline show` OK；`ruff` + `pytest tests` **87 passed**。
- 已删 obsolete 帽 `10-requirements.md` / `22-task-audit.md`；V2 新帽已 sync。

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-07-26 | 首版 · 2.11.1 发布后业务仓 upgrade + F1/F2 回归 |
| 2026-07-26 | 30/40 完成 · F1/F2 PASS · 记 F1b |
