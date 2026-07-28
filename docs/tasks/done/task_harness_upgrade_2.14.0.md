# Task：Harness 升级至 2.14.0（api）+ pre-30 硬闸 dogfood

> **状态**：completed  
> **类型**：基础设施（过程轨 upgrade）  
> **关联**：npm `@cyning/harness@2.14.0` · SPEC-verify-pre30-invoke-hats-gate · Phase α glayer

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `harness-upgrade-2.14.0` |
| **test_strategy** | `recommended` |
| **test_strategy_note** | `upgrade --yes`（不带 `--ide`）；`check` 最新；pre-30 dogfood（缺 10 BLOCK / 有 10 PASS）；无业务 pytest 义务 |
| **code_quality_bar** | `not_applicable` |
| **git_branch** | `task/harness-upgrade-2.14.0` |
| **graph_change_layer** | `none` |
| **review_hat** | `20` |
| **review_hat_reason** | `""` |
| **thinking_profile** | `shortest` |
| **invoke_retention_profile** | `minimal` |
| **required_invoke_hats** | `30` |
| **experience_capture** | `recommended` |

| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack |
### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 仅过程轨 sync；不改业务模块边界 |
| HG-TASK-DRAFT | approved | 22-R1 | 维护者告知产品已发 2.14.0，要求本仓跟进 |
| **HG-AUDIT-R1** | approved | **30** | 基础设施 upgrade + dogfood；无业务逻辑 |

---

## 背景与目标

产品 **2.14.0**：`verify --task` 对 pre-30 invoke（`required ∩ {10,20,00}`）硬闸。本仓 `manifest=2.13.0`，需 upgrade 并对 glayer task dogfood。

**完成态**：

- [x] manifest → `2.14.0`
- [x] `upgrade --yes`（无 `--ide`）一把过
- [x] `harness check` 已是最新
- [x] FRAGMENT_30 对齐 2.14 pre-30 行（保留本仓 `l1/01_modules` 闸路径）
- [x] dogfood：glayer task 有 10 → PASS；暂移 10 → BLOCK；恢复
- [x] invoke + 自检回填

**不做**：web/ios 升级；业务改码

---

## 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| S5 dirty 挡 upgrade | 先 commit/stash | 是 |
| dogfood 缺 10 仍 PASS | 升级未生效 / 查 npx 缓存 | 是 |

---

## 验收标准

- [x] manifest 2.14.0 · check 最新
- [x] dogfood BLOCK / PASS 证据写入自检
- [x] FRAGMENT 含 pre-30 硬闸与「开工≠闸」

---

### 自检结论（执行者）

| 项 | 内容 |
|---|---|
| **日期** | 2026-07-27 |
| **manifest** | `2.14.0`（from 2.13.0） |
| **check** | 已是最新 |
| **dogfood PASS** | glayer task · `VERIFY: PASS` · `invoke_pre30_ok=true` · `invoke_pre30_required=["10"]` |
| **dogfood BLOCK** | 暂移 10 invoke → `VERIFY: BLOCKED · missing pre-30 invoke hats · 缺 10（pre-30 要求 10 · 已有 30,40）`；已恢复 |
| **FRAGMENT** | 已含 pre-30 /「开工≠闸」；HG-GRAPH 路径写回 `l1/01_modules` |
| **下一棒** | 维护者审 diff → commit/PR |
