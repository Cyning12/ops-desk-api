# Task：Ops sync sender 迁移（GHA 改 POST /api/ops/admin/sync）

> **状态**：completed（2026-08-28 · 00 机械验收 PASS · PR #88）  
> **类型**：技术债 / 基础设施（数据链断尾根治）  
> **关联**：`app/ops/admin/sync.py`（接收端 2026-07-17 已实现）· 旧仓 `ai-ink-brain-api-python/.github/workflows/ops_sync_kimi_code.yml` · workspace `docs/02-backend-analysis/00-current-state.md` §8.1  
> **分支**：`task/ops-sync-sender-migration`  
> **编排**：capability lookup 已 CLOSE（#87）。本 task CLOSE 后 Eval E0/E1 可开（生产 secrets 同验仍为维护者）。  
> **00**：本波 **未** 改 `app/` / `tests/` 业务码；30 实现，00 统筹 / 验收 / PR。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `ops-sync-sender-migration` |
| **git_branch** | `task/ops-sync-sender-migration` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | GitHub JSON → SyncPayload 映射单测；Bearer token 鉴权；sender POST mock（无外网、无真 GitHub）；生产 workflow_dispatch 为合入后维护者步骤，**不挡** 30 CLOSE |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` · `docs/_tech_graph/l1/11_flow_sync_to_chat.graph.yaml` |
| **graph_delta_note** | `admin` 行备注：本仓 GHA sender + Bearer 机读 token；flow 增 GHA 节点；**不**新增一级模块 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 不改 coding_wiki 正文；secrets 清单写 `.env.example` + task 完成态 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无 |
| **orchestration** | 迁移旧 runner 进本仓；旧仓 GHA 仅标 deprecated |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-28 · **00 代签 · 维护者令开工 sync、迁移旧 runner、00 不实现**（R1 pass） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-28 · **00 代签** · 见 `docs/harness/reviews/task_ops_sync_sender_migration_audit_R1_20260828.md` |
| HG-GRAPH-MODULES | approved | 30 | 仅 G-L1 `admin` 备注 + `11_flow_sync_to_chat` 增 GHA 节点；不新增一级模块 · **00 代签** |

---

## 背景与目标

新 PG 数据链断尾（2026-08-08 查证，见 workspace `00-current-state.md` §8.1）：

- 日更 GHA 在**旧仓** `ai-ink-brain-api-python`，直写 Supabase；
- 新 API 只有接收端 `POST /api/ops/admin/sync`，**无发送方**；
- 新库靠一次性快照 `import_from_supabase.py` 续命，水位定格。

本 task 让 sender 改道：**本仓移植旧 runner 的 GitHub 抓取 → 对齐 SyncPayload → POST `/api/ops/admin/sync`**，新 PG 获得自己的持续数据源。

**方案定稿（2026-08-28 · 维护者）**：**迁移旧仓 `api/ops/sync/` runner 进本仓**。不采用「旧仓脚本 + POST 适配层」。

---

## 00 定夺（30 不得改写）

| 项 | 值 |
|---|---|
| 方案 | **迁移旧 runner 进 `ops-desk-api`**；禁止继续以旧仓 `store.py` 直写 Supabase 作为新路径 |
| 落点 | `app/ops/admin/sender/`（GitHub client + GitHub JSON→SyncPayload 映射 + HTTP POST）；`scripts/ops_sync_kimi_code.py` CLI；`.github/workflows/ops_sync_kimi_code.yml` |
| 参考（只读） | `/Users/cyning/Desktop/Projects/ai-ink-brain-api-python/api/ops/sync/github_client.py` · `runner.py` · `store.py` 的 **字段映射**（勿拷贝 Supabase 写入）；`.github/workflows/ops_sync_kimi_code.yml` |
| 写库 | runner **只** POST `SyncPayload`；禁止 sender 直连 PG / 禁止拷 `store.py` |
| 机读鉴权 | 仅本 endpoint：`Authorization: Bearer ${OPS_ADMIN_SYNC_TOKEN}`。env `ops_admin_sync_token` 空则 Bearer 路径禁用（cookie maintainer 仍可用）。`secrets.compare_digest`；**禁止**打日志输出 token |
| Cookie | 现有 `MaintainerUser` **保留**；现有 cookie 单测不破 |
| 增量 | **不**扩 `ops_sync_runs` 表加 cursor 列。cron / 默认 `incremental`：`since = utcnow - 48h`。`workflow_dispatch` 输入 `sync_mode`：`incremental`（48h）\| `full`（`since=None`，timeout 已 30min） |
| 目标仓 | 默认 `MoonshotAI/kimi-code`（与旧 runner 一致）；可用 env 覆盖 |
| HTTP 栈 | GitHub + POST 用 **httpx**（仓内已有）；**不要**加 `requests` |
| scan / graph | **可选**：checkout 文件缺失或 token 空 → skip，payload 不带 snapshot，GHA **不失败**（与旧 cron 兼容）。文件在则 `ScanSnapshotIn.raw_markdown` / `GraphSnapshotIn.payload`。**不**移植旧仓对 `ops_issues.scan_tags` 的副作用 |
| 旧仓 GHA | **不**在本仓禁用另一仓库 workflow；文档标注 deprecated + 回滚说明；维护者事后在旧仓关 cron |
| 生产同验 | 30 交付 workflow + secrets 文档 + mock 单测。**真实** `workflow_dispatch` 对生产 API = 合入后维护者（secrets 配齐）；**不挡** 30 CLOSE |
| 禁止混改 | RAG / Eval / capability / deferred RAG / `chat/graph.py` 拓扑 |

### SyncPayload 字段对齐（旧 runner 产出 → 新 schema）

| SyncPayload | 来源 | 说明 |
|---|---|---|
| `repo` | 固定/env：`MoonshotAI/kimi-code` | `owner` / `name` / `full_name`；`github_repo_id` 可空 |
| `issues[]` | `GET /repos/.../issues` 排除 PR | `number`/`title`/`body`/`state`；`labels`=name 列表；`author`=`user.login`；`assignees`=login 列表；`html_url`；`github_issue_id`=`id`；时间戳；`raw_payload`=原始 dict。旧 `milestone` 只进 `raw_payload` |
| `pull_requests[]` | `GET /repos/.../pulls` | 同上映射；`draft`；`merged_at`；GitHub `state` 原样（open/closed）；`github_pr_id`=`id`。旧 `head_ref`/`base_ref`/`labels` 只进 `raw_payload`。`ci_status`/`reviewers` 本波可空 |
| `sync_run` | runner 本地组装 | `sync_type`=`incremental`\|`full`（或 cron/manual）；`status`；`started_at`/`finished_at`；`summary` 可含 counts + since ISO |
| `scan_snapshot` | 可选 md 文件 | 缺失则 `null` |
| `graph_snapshot` | 可选 `graph.json` | 缺失则 `null` |

### GHA secrets 清单（本仓）

| Secret / env | 用途 |
|---|---|
| `GITHUB_TOKEN` | 内置；读 `MoonshotAI/kimi-code` issues/PRs |
| `OPS_API_BASE_URL` | 生产/预发 API 根（如 `https://…`，脚本拼 `/api/ops/admin/sync`） |
| `OPS_ADMIN_SYNC_TOKEN` | Bearer；与 API `OPS_ADMIN_SYNC_TOKEN` 同源 |
| `WORKSPACE_REPO_TOKEN` | 可选；ISSUE_SCAN checkout |
| `KIMI_META_REPO_TOKEN` | 可选；graph.json checkout |

**去掉**旧仓 `NEXT_PUBLIC_SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY`（新路径不用）。

`.env.example` 增加 `OPS_ADMIN_SYNC_TOKEN=` 注释（空=仅 cookie）。

---

## 范围 / 非范围

**范围**：

- 移植 GitHub 分页拉取（retry：401/422 fail-fast；403/502/504 退避，语义对齐旧 `github_client.py`）
- 映射 + POST；CLI + 本仓 GHA（cron `0 2 * * *` + `workflow_dispatch` + `sync_mode`）
- 接收端 Bearer 旁路（仅 sync POST）
- 单测 + G-L1 + graph-compile + ruff
- 文档：secrets、旧路径 deprecated

**非范围**：

- 扩表 / Alembic cursor 列  
- 下线旧仓 GHA / 删 Supabase  
- 评论抓取、RAG、Eval、capability  
- 00 改 `app/`/`tests/`  
- 生产环境真实打一枪（维护者合入后）

---

## 验收标准

- [x] GitHub issue fixture → `IssueIn` 字段对齐（含 labels/author/assignees/`github_issue_id`）
- [x] GitHub PR fixture → `PullRequestIn`（含 draft/merged_at/`github_pr_id`）
- [x] sender 组装完整 `SyncPayload`（repo + sync_run）；scan/graph 缺失不报错
- [x] POST mock：Bearer 头正确；失败非 2xx 退出码非 0
- [x] 接收端：cookie maintainer 仍 202；正确 Bearer 仍 202；错误/空 token 配置下 Bearer 401；无凭证 401
- [x] 本仓存在 `.github/workflows/ops_sync_kimi_code.yml`；无 Supabase env
- [x] `.env.example` 含 `OPS_ADMIN_SYNC_TOKEN` 注释
- [x] G-L1 `admin` 备注 + `11_flow_sync_to_chat` GHA 节点 + graph-compile
- [x] 旧路径 deprecated 说明（task 或短文档 / workflow 注释）
- [x] ruff / pytest 触及路径绿（无外网）
- [ ] 生产同验：合入后维护者 secrets + `workflow_dispatch`（不挡 CLOSE）

---

## 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| GitHub 5xx / 403 | 退避后仍失败 → CLI 非 0 → GHA 失败；下次 cron 重试（upsert 幂等） | Y |
| endpoint 5xx / 网络 | 同上 | Y |
| payload 422 | GHA 失败；修映射 | Y |
| token 泄漏 | 只走 GHA secrets；轮换即失效 | — |
| scan/graph 文件缺失 | skip；issue/PR 仍 POST；GHA 成功 | — |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-08 | 初版（AI 起草 · 待 HG-TASK-DRAFT 人审）：源自 RAG 前置查证发现的数据链断尾 |
| 2026-08-28 | RAG 两草案迁 deferred；本 task 仍为数据链 active |
| 2026-08-28 | **方案定稿**：迁移旧 runner；机读 Bearer；48h 增量；00 不实现；闸代签 |
| 2026-08-28 | 30/40 PASS · 00 机械验收 · PR #88 |

---

## 自检结论

> 2026-08-28 · 00 机械复检 · **PASS**

- [x] pytest `test_admin_sync.py` + `test_admin_sync_sender.py` **20 passed**
- [x] ruff 0 · graph-compile `11_flow_sync_to_chat` OK
- [x] 00 未改 `app/`/`tests/`；sender 不直连 PG

**50 结论**：PASS · 生产 secrets + `workflow_dispatch` 留给维护者；**Eval E0/E1 现可开**（sync + capability 均 CLOSE）

---

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-28 |
| 定稿 | 本仓 GHA sender → Bearer POST `/api/ops/admin/sync`；cookie 保留 |
| 归档 | `docs/tasks/done/task_ops_sync_sender_migration.md` |
| PR | [#88](https://github.com/Cyning12/ops-desk-api/pull/88) |
