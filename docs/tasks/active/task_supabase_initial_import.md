# Task：Supabase 初始数据导入脚本（直连 DB）

> **状态**：in_progress  
> **类型**：工具脚本  
> **关联**：`app/db/models.py` · `ops_desk_ddl.sql` · `../ops-desk-workspace/docs/02-backend-analysis/00-current-state.md`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `supabase-initial-import` |
| **test_strategy** | `required` |
| **test_strategy_note** | 映射函数单元测试（伪造 source 行）；空源 dry-run 集成测试；真实 Supabase 导入为人工验收 |
| **code_quality_bar** | `L2_backend` |
| **orchestration** | 单 task |
| **git_branch** | `task/supabase-initial-import` |
| **experience_capture** | `recommended` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 用户确认：scripts/ 工具类改动仅登记，不新增 graph 模块 |
| **HG-AUDIT-R1** | approved | **30** | 用户确认：范围含直连 Supabase + 配置指引文档 |

---

## 背景与目标

本地 PG 已就绪但无历史数据。Supabase 侧表名与本地一致（`ops_repos` / `ops_issues` / `ops_pull_requests` / `ops_sync_runs` / `ops_scan_snapshots` / `ops_graph_snapshots`），需一次性导入历史数据，供 Overview / Issues / PRs / Graph / Chat 上下文使用。

用户已确认：

- **数据源**：直连 Supabase DB（需详细配置指引文档）
- **导入范围**：repos + issues + PRs + scan/graph 快照 + sync_runs 历史
- **不导入**：`ops_users` / `ops_invite_tokens` / `ops_sessions`（auth 重新初始化）、`ops_sessions_chat` / `ops_runs` / `ops_run_events`（chat 历史不迁移）、`rag_*` / 向量表（v1 不迁移）

目标：

1. `scripts/import_from_supabase.py`：从源库读取 → 列映射 → 写入本地 PG。
2. 幂等：重复执行不产生重复数据（repo 按 `full_name`，issue/PR 按 `(repo_id, number)`，sync_run/快照按源 `id` 跳过已存在）。
3. ID 策略：**保留源 UUID**，使 `repo_id` / `scan_run_id` / `graph_run_id` 引用关系原样成立。
4. 时区：源 `timestamptz` → 本地 `TIMESTAMP WITHOUT TIME ZONE`（naive UTC，复用 `_to_naive_utc` 语义）。
5. `--dry-run`：只输出每张表将导入/跳过的计数，不写入。
6. 配置指引文档：Supabase 连接串获取、pooler 选择、安全注意事项。

**完成态**：

- [ ] `scripts/import_from_supabase.py`
- [ ] 列映射与类型归一化（含 JSONB / ARRAY / datetime）
- [ ] 幂等 upsert 逻辑
- [ ] `--dry-run` / `--only <tables>` / `--batch-size` 参数
- [ ] `.env.example` 增加 `SUPABASE_DATABASE_URL`（不含真实值）
- [ ] 配置指引文档 `docs/ops/supabase-import-guide.md`
- [ ] 单元测试 + dry-run 集成测试
- [ ] 真实 Supabase 导入人工验收（维护者执行）
- [ ] `### 自检结论` 回填

**不做**：

- 增量/定时同步（一次性导入；后续同步仍走 GHA sync payload）
- Supabase 侧任何写操作（只读）
- users/auth/chat 历史迁移

---

## 范围

- [ ] `scripts/import_from_supabase.py`（新增）
- [ ] `app/ops/admin/service.py`（复用 `_to_naive_utc`，如需要抽到公共位置）
- [ ] `.env.example`
- [ ] `docs/ops/supabase-import-guide.md`（新增）
- [ ] `tests/test_import_from_supabase.py`（新增）

## 非范围

- 新增 API 端点
- Alembic migration（目标表结构不变）
- 前端/iOS

---

## 关键设计

### 源连接与凭据

- 源 DSN 从环境变量 `SUPABASE_DATABASE_URL` 读取（**不写入任何提交文件**）。
- 指引文档说明两种连接方式：
  - **Session Pooler**（推荐，`*.pooler.supabase.com:5432`）：兼容 IPv4，适合本地/CI；
  - **Direct Connection**（`db.<ref>.supabase.co:5432`）：仅 IPv6，免费层本地常不可用。
- 建议创建只读账号或使用现有凭据；脚本只执行 `SELECT`。

### 列映射策略

- 按**列名交集**拷贝：源有而本地无的列忽略；本地有而源缺的列用默认值（`labels`/`assignees`/`reviewers` → `[]`，`raw_payload` → `None`）。
- 执行首步做 schema 探测：`SELECT column_name FROM information_schema.columns` 对比并输出差异报告，防止静默丢列。
- datetime： aware → naive UTC；`None` 保持 `None`。
- `ops_scan_snapshots.parsed_summary` / `ops_graph_snapshots.payload` 本地为 `NOT NULL DEFAULT {}`：源为 NULL 时写 `{}`。

### 导入顺序（满足 FK）

`ops_repos` → `ops_sync_runs` → `ops_issues` / `ops_pull_requests` → `ops_scan_snapshots` / `ops_graph_snapshots`

### 幂等规则

| 表 | 冲突键 | 行为 |
|---|---|---|
| ops_repos | `full_name` | 存在则更新字段（保留本地 id；若源 id ≠ 本地 id 则子表按本地 id 重写外键） |
| ops_issues / ops_pull_requests | `(repo_id, number)` | 存在则更新 |
| ops_sync_runs | 源 `id` | 存在则跳过 |
| ops_scan_snapshots / ops_graph_snapshots | 源 `id` | 存在则跳过 |

> repo 已存在且 id 不同（如先前 smoke 数据）时：子表外键映射到**本地** repo_id，避免 UUID 冲突；脚本输出 remap 计数。

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|---|---|---|
| `SUPABASE_DATABASE_URL` 未设置 | 退出码 2 + 指引文档路径提示 | 是 | CLI 报错 |
| 源库不可达（网络/IPv6/凭据） | 退出码 1 + 连接诊断建议（pooler vs direct） | 是 | CLI 报错 |
| 源表缺失（schema 漂移） | 跳过该表 + warn；不中断其他表 | 是 | warn 日志 |
| 单表写入失败 | 该表回滚，其余表继续；末尾汇总失败表 | 是 | 非零退出码 + 报告 |
| `--dry-run` | 不写任何数据 | — | 计数报告 |

---

## 验收标准

- [ ] `pytest tests` 通过（含新增映射单测）
- [ ] `ruff check app tests scripts` 通过
- [ ] `./scripts/graph-compile.sh` 通过
- [ ] 未设置 `SUPABASE_DATABASE_URL` 时退出码 2 且提示指引文档
- [ ] `--dry-run` 对本地 docker PG（伪造源）输出正确计数且不写入
- [ ] 重复执行幂等（计数第二次全为 skip/update，无 insert）
- [ ] 配置指引文档可独立按步骤操作（含 pooler/direct 说明、IPv6 坑、只读建议）
- [ ] 维护者用真实 Supabase DSN 完成导入，`GET /api/ops/issues` 返回历史数据

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
3. `app/db/models.py`
4. `ops_desk_ddl.sql`
5. `app/ops/admin/service.py`（`_to_naive_utc` / upsert 模式）
6. `../ops-desk-workspace/docs/02-backend-analysis/00-current-state.md` §2

---

## 实现备忘

| 项 | 状态 | 备注 |
|---|---|---|
| 导入脚本 | ⏳ | `scripts/import_from_supabase.py` |
| 列映射 + schema 探测 | ⏳ | 列名交集 + 差异报告 |
| 幂等 upsert | ⏳ | 见幂等规则表 |
| 配置指引 | ⏳ | `docs/ops/supabase-import-guide.md` |
| 测试 | ⏳ | 映射单测 + dry-run 集成 |

---

### 自检结论（执行者）

（30/40 回填）

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-07-24 | 创建 task，匹配分支 `task/supabase-initial-import`；数据源与范围经用户确认 |
