# PROMPT · 30 · ops-sync-sender-migration

> **给谁**：新开的 **30**（可含 40）。  
> **Open Folder**：`ops-desk-api/` 仓根。  
> **分支**：`task/ops-sync-sender-migration`。

---

## 复制区（整段粘贴）

`````text
你是 ops-desk-api 的 30（可含 40）。只实现 ops-sync-sender-migration。

工作目录：以维护者 worktree 为准的 ops-desk-api 仓根
分支：task/ops-sync-sender-migration。勿 push；未授权勿 commit。

GATE_VERIFY（首输出必填表 · 真值读 task 人工闸表）
  + npx dsh-coding-kit verify --target . --task docs/tasks/active/task_ops_sync_sender_migration.md
落盘 docs/harness/invokes/by-task/ops-sync-sender-migration/invoke_20260828_30_40_ops-sync-sender-migration.md

必读
  docs/tasks/active/task_ops_sync_sender_migration.md（00 定夺表 + SyncPayload 对齐表 + secrets 清单）
  docs/harness/reviews/task_ops_sync_sender_migration_audit_R1_20260828.md
  app/ops/admin/sync.py
  app/ops/admin/schema.py（IssueIn / PullRequestIn / SyncPayload）
  app/ops/admin/service.py
  app/ops/deps.py（MaintainerUser · 勿拆掉 cookie）
  app/config.py
  tests/test_admin_sync.py
  docs/_tech_graph/l1/11_flow_sync_to_chat.graph.yaml
  docs/_tech_graph/l1/01_modules.md（admin 行）
  docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md
  docs/standards/CODING_BACKEND_L2_v1_zh.md
  只读参考（本机旧仓，禁止拷贝 store.py / 禁止写 Supabase）：
    /Users/cyning/Desktop/Projects/ai-ink-brain-api-python/api/ops/sync/github_client.py
    /Users/cyning/Desktop/Projects/ai-ink-brain-api-python/api/ops/sync/runner.py
    /Users/cyning/Desktop/Projects/ai-ink-brain-api-python/.github/workflows/ops_sync_kimi_code.yml

范围（严格按 task 00 定夺）
  app/ops/admin/sender/：GitHub 分页拉取（httpx；retry 对齐旧客户端：401/422 fail-fast；403/502/504 退避最多 5 次）
    fetch_issues 排除 pull_request 键；fetch_pull_requests 无 since 则客户端按 updated_at 过滤
    默认仓 MoonshotAI/kimi-code
  映射：GitHub JSON → IssueIn / PullRequestIn / SyncPayload；raw_payload 保留原 dict
    旧 milestone / head_ref / base_ref / PR labels 只进 raw_payload
    ci_status / reviewers 本波可空
  CLI scripts/ops_sync_kimi_code.py：组装 payload → POST {OPS_API_BASE_URL}/api/ops/admin/sync
    Header Authorization: Bearer ${OPS_ADMIN_SYNC_TOKEN}
    非 2xx → 退出码非 0
    scan/graph 文件缺失 → 不带 snapshot，不失败
  接收端：仅 POST /api/ops/admin/sync 增加 Bearer 旁路（OPS_ADMIN_SYNC_TOKEN；空则禁用 Bearer）
    secrets.compare_digest；禁止日志打印 token
    cookie MaintainerUser 保留；现有 test_admin_sync cookie 用例不破
  Settings + .env.example：OPS_ADMIN_SYNC_TOKEN
  .github/workflows/ops_sync_kimi_code.yml：cron 0 2 * * * + workflow_dispatch sync_mode incremental|full
    无 Supabase env；可选 WORKSPACE_REPO_TOKEN / KIMI_META_REPO_TOKEN 与旧 workflow 同结构
    incremental：since = utcnow-48h；full：since=None
  G-L1：admin 行备注 + 11_flow_sync_to_chat 增 GHA sender 节点 + graph-compile
  旧路径 deprecated：workflow 或 docs 短注（不改另一仓库）
  单测（无外网）：映射 fixture；Bearer 202 / 错 token 401 / 未配置 token 时 Bearer 401；cookie 回归；sender POST mock

硬约束
  禁止 sender 直连 PG / 拷贝 store.py / 写 Supabase
  禁止扩表 / Alembic
  禁止加 requests 依赖
  禁止改 chat/graph.py、lg_rag 拓扑、capability、RAG、Eval、deferred RAG
  禁止真实打 GitHub / 生产 API
  中文注释简洁

40
  pytest 触及路径 + ruff + graph-compile
  报告 00。简体中文。勾选 task 验收项（生产同验保持未勾）。勿伪造测试结果。
`````

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-28 | 初版 30 Prompt |
