# Task：Harness 升级至 2.13.0（api）

> **状态**：active  
> **类型**：基础设施（过程轨 upgrade）  
> **关联**：`Projects/docs/harness/guides/CHECKLIST_harness_pilot_dogfood_v1_zh.md` · npm `@cyning/harness@2.13.0`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `harness-upgrade-2.13.0` |
| **test_strategy** | `recommended` |
| **test_strategy_note** | 干净仓 `upgrade --yes`（不带 `--ide`，避 F1b）一把过；`harness check` 已是最新；可选摸底 `lifecycle show` / `discipline show` / `lifecycle dry-run`；`ruff`/`pytest` 不因过程轨同步而红 |
| **code_quality_bar** | `not_applicable` |
| **orchestration** | 单 task；00 代签双闸（RUNBOOK 基础设施惯例） |
| **git_branch** | `task/harness-upgrade-2.13.0` |
| **experience_capture** | `recommended` |
| **invoke_retention_profile** | `minimal` |
| **required_invoke_hats** | `30` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 00 代签：仅过程轨 / IDE starter，不改业务模块边界 |
| HG-TASK-DRAFT | approved | 22-R1 | 维护者指示升至 2.13.0 + 回填 checklist（仅 api） |
| **HG-AUDIT-R1** | approved | **30** | 00 代签（用户 2026-07-26 授权）：基础设施 upgrade，无业务逻辑 |

---

## 背景与目标

产品包 **2.13.0**（含 2.12.x invoke hats 留档闸 · `lifecycle dry-run` close_* 接线）已发布。本仓当前 `manifest.version=2.11.1`，需升级并回填 dogfood checklist。**本轮仅 api**；web 暂不升。

**完成态**：

- [ ] `.cyning-harness/manifest.json` → `version: 2.13.0`
- [ ] 干净工作区单次 `upgrade --yes`（无 `--ide`）**一把过**（无 S5）
- [ ] `npx @cyning/harness check` → 已是最新
- [ ] `npx @cyning/harness verify --target . --task <本文件>` PASS（或仅闸/审计类可解释 warn）
- [ ] 可选摸底：`lifecycle show` · `discipline show` · `lifecycle dry-run`（close 旁路）
- [ ] invoke 落盘 + 自检回填
- [ ] Projects checklist 回填（api → 2.13.0；web 仍 2.11.1）

**不做**：

- 业务 API / DB 改码
- ops-desk-web / ios 升级（用户明示本轮仅 api）
- 产品仓修 F1b

---

## 范围

- `.cyning-harness/*` · `docs/harness/prompts/*` · IDE starter（若 sync 触及）
- 本 task / invoke / review 文档
- `Projects/docs/harness/guides/CHECKLIST_harness_pilot_dogfood_v1_zh.md` 回填

## 非范围

- `app/**` · `tests/**` 业务逻辑
- 产品仓 cyning-harness 改码
- web / ios 仓 upgrade

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 工作区非干净即 upgrade | S5 中止 | 是 | 先 commit/stash |
| 带 `--ide` 触发 F1b | S5（profile 自脏） | 是 | 本轮不带 `--ide` |
| verify 因缺 review | 补 R1 文 | 是 | 按 2.11+ 要求 |

## 验收标准

- [ ] manifest `version` = `2.13.0`，仅 schema 五字段
- [ ] 单次 upgrade 退出码 0，无 S5 中止
- [ ] `harness check` 已是最新
- [ ] checklist 状态/版本/修订记录已回填（注明仅 api）
- [ ] `ruff check app tests` · `pytest tests` 仍绿（过程轨不影响业务）

---

### 自检结论（执行者）

（30/40 后回填）

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-07-26 | 首版 · 升至 2.13.0（仅 api）+ checklist 回填 |
