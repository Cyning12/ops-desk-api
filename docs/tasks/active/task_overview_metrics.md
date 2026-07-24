# Task：Overview 指标接口（Epic 5.1）

> **状态**：draft  
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
| **HG-GRAPH-MODULES** | pending | **30** | 待确认：data 模块 overview 由空壳转为实现 + db 新增一列 |
| **HG-AUDIT-R1** | pending | **30** | 待确认：范围含 Alembic migration（first_review_at）与契约偏差决策 |

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

- [ ] Alembic migration：`ops_pull_requests.first_review_at`（nullable timestamp）
- [ ] 指标计算实现（median / throughput / trend / sync / scan）
- [ ] `GET /api/ops/overview` 需登录（`CurrentUser`）
- [ ] 空数据态：无 merged PR / 无 closed issue 时 median 为 null、sampleSize 0，不报错
- [ ] 单元/集成测试
- [ ] `docs/_tech_graph/` 更新 + `graph-compile.sh` 通过
- [ ] invoke 落盘 + `harness task close` 归档
- [ ] `### 自检结论` 回填

**不做**：

- `{ok, data}` 外壳与 camelCase 统一（后续契约对齐任务）
- 更多历史列补全（milestone、labels on PR 等）
- 复杂聚合报表 / 缓存层

---

## 范围

- [ ] `app/ops/overview.py`
- [ ] `app/db/models.py`（+1 列）
- [ ] `alembic/versions/`（+1 migration）
- [ ] `tests/test_overview.py`（新增）
- [ ] `docs/_tech_graph/`

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

- [ ] `pytest tests` 通过
- [ ] `ruff check app tests` 通过
- [ ] `./scripts/graph-compile.sh` 通过
- [ ] `alembic upgrade head` 后 `first_review_at` 列存在，重跑导入脚本可回填
- [ ] 伪造数据下 cycle_time / review_time 中位数计算正确（含奇偶样本）
- [ ] trend 返回近 30 天逐日数组，缺口日期为 0
- [ ] 空数据态返回 200 且指标为空态
- [ ] 对当前真实库调用返回非空 cycle_time 与 trend（人工抽查）

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
| migration first_review_at | ⏳ | nullable；重跑导入回填 |
| cycle/review time median | ⏳ | 近 90 天，Statistics median 或 SQL percentile |
| throughput / trend | ⏳ | 近 30 天按日聚合 |
| sync_run / scan | ⏳ | records 读 summary JSONB |
| 测试 | ⏳ | 含空数据态、奇偶样本 |

---

### 自检结论（执行者）

（30/40 回填）

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-07-24 | 创建 task，匹配分支 `task/overview-metrics` |
