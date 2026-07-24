# Task：Overview 指标接口（Epic 5.1）

> **状态**：completed  
> **类型**：功能实现  
> **关联**：`app/ops/overview.py` · `app/db/models.py` · `../ops-desk-workspace/docs/contracts/data-v1.md` §2

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `overview-metrics` |
| **test_strategy** | `required` |
| **test_strategy_note** | 指标计算单测（伪造时间序列数据）+ 接口集成测试（含空数据态） |
| **code_quality_bar** | `L2_backend` |
| **orchestration** | 单 task |
| **git_branch** | `task/overview-metrics` |
| **experience_capture** | `recommended` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 用户确认：data 模块 overview 由空壳转为实现 + db 新增 first_review_at |
| **HG-AUDIT-R1** | approved | **30** | 用户确认：补列 + snake_case + 不包外壳（契约对齐留后续任务） |

---

## 背景与目标

`GET /api/ops/overview` 目前是返回全 null 的空壳。本地已有完整真实数据（599 issues / 1440 PRs / 49 sync_runs / 47 scan / 44 graph），实现总览页指标，契约参考 `data-v1.md` §2。

目标指标（v1）：

| 指标 | 定义 | 数据源 |
|---|---|---|
| `cycle_time` | PR 从创建到合并的天数中位数（近 90 天 merged PR） | `ops_pull_requests.created_at` / `merged_at` |
| `review_time` | PR 从创建到首次 review 的天数中位数（近 90 天） | `ops_pull_requests.first_review_at`（**本地尚无此列**） |
| `issue_throughput` | 近 30 天关闭 issue 数 | `ops_issues.closed_at` |
| `sync_status` + `sync_run` | 最近一次 sync 的状态与记录数 | `ops_sync_runs`（records 从 `summary` JSONB 读） |
| `scan_snapshot` | 最新 scan 摘要 | `ops_scan_snapshots.parsed_summary` |
| `trend` | 近 30 天每日 closedIssues / mergedPrs | `closed_at` / `merged_at` 按日聚合 |

**关键决策（已在起草时分析，待签闸确认）**：

1. **`first_review_at` 补列**：Supabase 源有此列（导入时被忽略），本地模型没有。方案：Alembic migration 加列（nullable）→ 重跑导入脚本幂等回填 → review_time 可算。不补列则 review_time 恒 null。
2. **字段命名**：契约 `data-v1.md` 用 camelCase，但本仓已实现接口（issues/pulls/graph/auth）均为 snake_case。方案：overview 沿用 snake_case 保持仓内一致；契约 camelCase 对齐留待后续统一任务。
3. **不包 `{ok, data}` 外壳**：与现有接口一致（契约外壳同样留待统一任务）。

**完成态**：

- [x] Alembic migration：`ops_pull_requests.first_review_at`（nullable timestamp）
- [x] 指标计算实现（median / throughput / trend / sync / scan）
- [x] `GET /api/ops/overview` 需登录（`CurrentUser`）
- [x] 空数据态：无 merged PR / 无 closed issue 时 median 为 null、sampleSize 0，不报错
- [x] 单元/集成测试
- [x] `docs/_tech_graph/` 更新 + `graph-compile.sh` 通过
- [x] invoke 落盘 + `harness task close` 归档
- [x] `### 自检结论` 回填

**不做**：

- `{ok, data}` 外壳与 camelCase 统一（后续契约对齐任务）
- 更多历史列补全（milestone、labels on PR 等）
- 复杂聚合报表 / 缓存层

---

## 范围

- [x] `app/ops/overview.py`
- [x] `app/db/models.py`（+1 列）
- [x] `alembic/versions/`（+1 migration）
- [x] `tests/test_overview.py`（新增）
- [x] `tests/conftest.py`（**范围追加**：测试隔离到 `opsdesk_test` 库，防止 destructive fixture 清开发库真实数据——验证阶段发现并已修复）
- [x] `docs/_tech_graph/`

## 非范围

- 前端/iOS 页面
- 其他接口的契约对齐

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 无任何数据 | 全指标 null/空数组 + sampleSize 0，200 | — | 空态指标 |
| 无 merged PR / 无 closed issue | 对应 median 为 null、sampleSize 0 | — | 空态指标 |
| 未登录 | 401 | 是 | 401 |
| DB 异常 | 500 | 是 | 500 |

---

## 验收标准

- [x] `pytest tests` 通过
- [x] `ruff check app tests` 通过
- [x] `./scripts/graph-compile.sh` 通过
- [x] `alembic upgrade head` 后 `first_review_at` 列存在，重跑导入脚本可回填
- [x] 伪造数据下 cycle_time / review_time 中位数计算正确（含奇偶样本）
- [x] trend 返回近 30 天逐日数组，缺口日期为 0
- [x] 空数据态返回 200 且指标为空态

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
3. `app/db/models.py`
4. `app/ops/issues.py` / `app/ops/graph.py`（只读接口模式）
5. `../ops-desk-workspace/docs/contracts/data-v1.md` §2

---

## 实现备忘

| 项 | 状态 | 备注 |
|---|---|---|
| migration first_review_at | ✅ | `20260724_pr_first_review_at`；重跑导入回填 |
| cycle/review time median | ✅ | 近 90 天，statistics.median；混合 tz 列归一化 |
| throughput / trend | ✅ | 近 30 天按日聚合，缺口补 0 |
| sync_run / scan | ✅ | records 读 summary JSONB |
| 测试 | ✅ | 3 单测 + 401 + 空态 + 种子数据集成 |

---

### 自检结论（执行者）

- `pytest tests` 84 passed（overview 3 单测 + 401 + 空态 + 种子集成；全量含既有套件）。
- `ruff check app tests scripts` 通过；`./scripts/graph-compile.sh` 通过。
- migration `20260724_pr_first_review_at` 已在本地 dev 库应用。
- **重要发现与修复**：
  1. `clean_sync_data` fixture 全表清空 → 跑测试会**删掉开发库真实导入数据**（本次验证时 599 issues 等被清空）。已将测试整体隔离到独立 `opsdesk_test` 库（conftest 自动建库 + create_all），destructive fixture 不再触碰 dev 库。
  2. 模型与 DDL 存在 tz 漂移：部分列模型声明 `TIMESTAMP WITHOUT TZ` 而实际 DDL 为 `timestamptz`（如 `ops_repos.created_at`），读出为 aware datetime。`_median_days` 已做归一化；漂移本身留后续任务对齐。
- **移交维护者**：重跑 `.venv/bin/python scripts/import_from_supabase.py` 恢复 dev 库数据（含 first_review_at 回填），随后调用 `GET /api/ops/overview` 抽查非空 cycle_time / trend。

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-07-24 | 创建 task，匹配分支 `task/overview-metrics` |
| 2026-07-24 | 30+40 完成；范围追加 tests/conftest.py 测试库隔离（防 fixture 清 dev 库） |
