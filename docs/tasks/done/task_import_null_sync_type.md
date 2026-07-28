# Task：修复 Supabase 导入 sync_type NULL 失败

> **状态**：completed  
> **类型**：紧急修复（fix/ 分支）  
> **关联**：`scripts/import_from_supabase.py` · task `supabase-initial-import`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `import-null-sync-type` |
| **test_strategy** | `required` |
| **test_strategy_note** | 单测：NULL sync_type → "legacy"；集成：scratch 源含 NULL 行可导入 |
| **code_quality_bar** | `L2_backend` |
| **orchestration** | 单 task |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack |
| **git_branch** | `fix/import-null-sync-type` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 修复不涉及模块边界（沿用 task `supabase-initial-import` 签核） |
| **HG-AUDIT-R1** | approved | **30** | 用户 2026-07-24 确认方案：sync_type NULL → 默认值 "legacy" |

---

## 背景与目标

真实 Supabase 导入时 `ops_sync_runs` 失败：源历史行 `sync_type IS NULL`（2026-06 早期记录），本地列为 `NOT NULL`，触发 `NotNullViolationError`，该表整体回滚（其余 5 表已成功）。

**修复**：`normalize_row` 对 `ops_sync_runs.sync_type` 为 NULL 时填默认值 `"legacy"`（显式标记历史遗留）。

**完成态**：

- [x] `_VALUE_DEFAULTS` 机制 + `sync_type` 默认值
- [x] 单测 + 集成测试
- [x] invoke 落盘 + `harness task close` 归档

**不做**：表结构 nullable 迁移；跳过 NULL 行。

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 源行 sync_type NULL | 写入 "legacy" | — | 无 |

---

## 验收标准

- [x] `pytest tests` 通过
- [x] `ruff check app tests scripts` 通过
- [x] NULL sync_type 源行导入后本地值为 "legacy"

---

### 自检结论（执行者）

- `pytest tests` 78 passed（新增 1 单测：NULL sync_type → legacy；集成测试 scratch 源加 NULL 行覆盖导入断言）。
- `ruff check app tests scripts` 通过。
- 修复后用户重跑导入即可幂等补齐 `ops_sync_runs`（其余表 skip/update）。

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-07-24 | 真实导入暴露 sync_type NULL；用户批准默认值 "legacy" 方案 |
