# Task：Admin GitHub 数据同步（GHA Sync Payload）

> **状态**：completed  
> **类型**：功能实现  
> **关联**：`docs/_tech_graph/01_struct.md` · `app/ops/admin/sync.py` · `app/db/models.py`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `admin-github-sync` |
| **test_strategy** | `required` |
| **test_strategy_note** | sync endpoint 单元/集成测试；upsert 幂等性测试 |
| **code_quality_bar** | `L2_backend` |
| **orchestration** | 单 task |
| **git_branch** | `task/admin-github-sync` |
| **experience_capture** | `recommended` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 用户确认：admin/sync 模块及新增 issues/pulls/graph 只读接口纳入 graph |
| **HG-AUDIT-R1** | approved | **30** | 用户确认：范围含 issues/pulls/graph 只读接口与 iOS 联调整体验收 |

---

## 背景与目标

当前 `app/ops/admin/sync.py` 仅返回空响应，未实现真实 upsert。本任务实现接收 GitHub Actions sync payload 并写入本地 PG，为 Overview / Issues / PRs / Graph / Chat 上下文提供真实数据：

1. 定义 `SyncPayload` Pydantic Schema，覆盖 repo / issues / PRs / sync_run / scan / graph。
2. `POST /api/ops/admin/sync` 接收 payload，按 `repo_full_name` upsert `ops_repos`。
3. 按 `(repo_id, number)` 唯一键 upsert `ops_issues` 与 `ops_pull_requests`。
4. 写入 `ops_sync_runs`、`ops_scan_snapshots`、`ops_graph_snapshots`。
5. 保留 `raw_payload` 字段。
6. 提供 iOS 可感知的 Chat 上下文验证方式（登录 → sync 导入 → chat 查询 issue）。

**完成态**：

- [x] `SyncPayload` Schema 定义
- [x] `POST /api/ops/admin/sync` 主入口实现
- [x] repo upsert 逻辑
- [x] issue upsert 逻辑（按 `repo_id` + `number`）
- [x] PR upsert 逻辑（按 `repo_id` + `number`）
- [x] sync_run / scan / graph snapshot 写入
- [x] 幂等性保证
- [x] `GET /api/ops/issues` 只读接口
- [x] `GET /api/ops/pulls` 只读接口
- [x] `GET /api/ops/graph` 只读接口
- [x] 单元/集成测试
- [x] `docs/_tech_graph/01_struct.md` / graph yaml 更新
- [x] `./scripts/graph-compile.sh` 通过
- [x] `### 自检结论` 回填

**不做**：

- 定时任务 / 增量 diff 算法
- 自动重试策略
- 前端/iOS 页面
- 复杂数据清洗

---

## 范围

- [x] `app/ops/admin/sync.py`
- [x] `app/ops/admin/schema.py`（新增）
- [x] `app/ops/issues.py`
- [x] `app/ops/pulls.py`
- [x] `app/ops/graph.py`
- [x] `app/db/models.py`（如需要新增字段）
- [x] `tests/test_admin_sync.py`
- [x] `tests/test_issues.py`
- [x] `tests/test_pulls.py`
- [x] `tests/test_graph.py`

## 非范围

- OAuth / GitHub App 接入
- 前端页面
- Chat 回答生成逻辑（已在 Epic 6 完成）

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|---|---|---|
| payload schema 校验失败 | 返回 422，不写入任何数据 | 是 | 422 Unprocessable Entity |
| repo upsert 失败 | 返回 500 | 是 | 500 Internal Server Error |
| issue/PR 部分写入失败 | 事务回滚，返回 500 | 是 | 500 Internal Server Error |
| 非 maintainer 调用 | 返回 403 | 否 | 403 Forbidden |

---

## 验收标准

- [x] `pytest tests` 通过
- [x] `ruff check app tests` 通过
- [x] `./scripts/graph-compile.sh` 通过
- [x] maintainer 可调用 `POST /api/ops/admin/sync` 导入示例 payload
- [x] 导入后 `GET /api/ops/issues` 返回对应 issue 数据
- [x] 导入后 `GET /api/ops/pulls` 返回对应 PR 数据
- [x] 导入后 `GET /api/ops/graph` 返回对应 graph snapshot
- [x] Chat 在导入后可基于 issue 上下文回答（可通过 stream 事件中的 `tool_result` 验证）
- [x] iOS 登录 + sync + chat 全链路本地可跑通

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
3. `docs/_tech_graph/01_struct.md`
4. `app/db/models.py`
5. `app/ops/admin/sync.py`
6. `app/ops/deps.py`

---

## 实现备忘

| 项 | 状态 | 备注 |
|---|---|---|
| SyncPayload Schema | ✅ | `app/ops/admin/schema.py` |
| repo upsert | ✅ | 按 `full_name` 唯一键；若未命中且 `github_repo_id` 存在则二次匹配 |
| issue upsert | ✅ | 按 `(repo_id, number)` 唯一键 |
| PR upsert | ✅ | 按 `(repo_id, number)` 唯一键 |
| sync_run / scan / graph | ✅ | `app/ops/admin/service.py` 关联 `repo_id` |
| 测试 | ✅ | `tests/test_admin_sync.py` / `test_issues.py` / `test_pulls.py` / `test_graph.py` |

---

### 自检结论（执行者）

- 后端 `pytest tests` 全绿（66 passed）。
- `ruff check app tests` 全绿。
- `./scripts/graph-compile.sh` 通过，生成 4 个 graph 文档。
- iOS smoke test 本地验证：登录 → `POST /admin/sync` → `GET /issues` / `pulls` / `graph` → `POST /chat/stream` 成功加载 `#1` issue 上下文并返回 `tool_result`。
- 过程中修复：
  - 测试 fixture 使用随机 `github_repo_id` 并在 int32 范围内，避免唯一约束冲突与溢出。
  - 新增 `clean_sync_data` fixture 在 DB 集成测试前清空 `ops_repos`，避免历史数据影响 `total` 断言。
  - `process_sync_payload` 增加 `github_repo_id` 二次匹配，支持仓库重命名场景。

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-07-17 | 创建 task，匹配分支 `task/admin-github-sync` |

