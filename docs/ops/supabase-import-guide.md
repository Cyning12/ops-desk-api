# Supabase 初始数据导入指引

> **用途**：将 Supabase 上的历史数据（repos / issues / PRs / sync_runs / scan / graph 快照）一次性导入本地 PostgreSQL。  
> **脚本**：`scripts/import_from_supabase.py`（只读源库，幂等，可重复执行）

---

## 1. 获取 Supabase 连接串

1. 打开 [Supabase Dashboard](https://supabase.com/dashboard) → 选择项目。
2. 左侧 **Project Settings**（齿轮图标）→ **Database**。
3. 找到 **Connection string** 区域，有两种选择：

| 方式 | 地址形态 | 适用 | 注意 |
|---|---|---|---|
| **Session Pooler**（推荐） | `aws-0-<region>.pooler.supabase.com:5432` | 本地开发 / CI | 兼容 IPv4；用户名为 `postgres.<project-ref>` |
| Direct Connection | `db.<project-ref>.supabase.co:5432` | 服务器常驻 | **仅 IPv6**，免费层本地网络通常不可达 |

4. 复制 **URI** 形式的连接串，替换其中的 `[YOUR-PASSWORD]` 为数据库密码。
   - 忘记密码：同页面 **Reset database password** 可重置（会影响其他使用该密码的服务，谨慎）。

**推荐（Session Pooler）**：

```
postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
```

> ⚠️ **安全**：连接串含数据库密码，**不要**提交到 git。只通过环境变量传入。脚本对源库只执行 `SELECT`，如需更严格可在 Supabase SQL Editor 创建只读账号。

---

## 2. 执行导入

```bash
# 1. 确保本地 PG 已启动且已迁移
docker compose up -d db
.venv/bin/alembic upgrade head   # 或先 source .venv/bin/activate

# 2. 设置源库 DSN（仅在当前 shell 会话有效）
export SUPABASE_DATABASE_URL="postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres"

# 3. 先 dry-run：只输出每张表的 insert/update/skip 计数，不写入
.venv/bin/python scripts/import_from_supabase.py --dry-run

# 4. 确认计数符合预期后正式导入
.venv/bin/python scripts/import_from_supabase.py

# 可选：只导入部分表 / 调整批大小
.venv/bin/python scripts/import_from_supabase.py --only ops_repos,ops_issues --batch-size 200
```

---

## 3. 导入范围与幂等规则

**导入**：`ops_repos` → `ops_sync_runs` → `ops_issues` / `ops_pull_requests` → `ops_scan_snapshots` / `ops_graph_snapshots`

**不导入**：`ops_users` / `ops_invite_tokens` / `ops_sessions`（auth 用 `scripts/create_initial_user.py` 重新初始化）、`ops_sessions_chat` / `ops_runs` / `ops_run_events`（chat 历史）、`rag_*` / 向量表。

| 表 | 冲突键 | 重复执行行为 |
|---|---|---|
| ops_repos | `full_name` | 更新字段，保留本地 id；子表外键自动 remap |
| ops_issues / ops_pull_requests | `(repo_id, number)` | 更新字段 |
| ops_sync_runs | 源 `id` | 跳过 |
| ops_scan_snapshots / ops_graph_snapshots | 源 `id` | 跳过 |

时区处理：源 `timestamptz` 统一转为 naive UTC 写入（与 admin sync 语义一致）；NULL 的 JSONB 字段写为 `{}`。

---

## 4. 验证导入结果

```bash
# 启动 API 后直接查只读接口（需先登录拿 cookie）
curl -b /tmp/cookies.txt http://localhost:8000/api/ops/issues | jq '.total'
curl -b /tmp/cookies.txt http://localhost:8000/api/ops/pulls | jq '.total'
curl -b /tmp/cookies.txt http://localhost:8000/api/ops/graph | jq '.repo_id'
```

或在数据库中抽查：

```bash
docker compose exec db psql -U ops -d opsdesk \
  -c "SELECT count(*) FROM ops_issues; SELECT count(*) FROM ops_sync_runs;"
```

---

## 5. 常见问题

| 现象 | 原因与处理 |
|---|---|
| `缺少 SUPABASE_DATABASE_URL`（exit 2） | 未设置环境变量；见第 2 节 |
| `源库连接失败` + `Network is unreachable` | 用了 Direct Connection（仅 IPv6）；改用 Session Pooler 地址 |
| `源库连接失败` + 认证错误 | 密码错误或未替换 `[YOUR-PASSWORD]`；用户名须为 `postgres.<project-ref>`（pooler） |
| `[warn] 源库缺表 ops_xxx` | 源库 schema 漂移；该表跳过，不影响其他表 |
| `[warn] 源列在本地不存在` | 源有多余列（如旧字段），按列名交集忽略，属预期 |
| 单表失败（exit 3） | 该表已回滚，其余表不受影响；修复后重跑即可（幂等） |

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-07-24 | 初版（task `supabase-initial-import`） |
