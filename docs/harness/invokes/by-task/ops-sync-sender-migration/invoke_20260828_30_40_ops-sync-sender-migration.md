# Invoke：30/40 · ops-sync-sender-migration

| 字段 | 值 |
|---|---|
| hat_id | 30/40 |
| task_slug | ops-sync-sender-migration |
| git_branch | `task/ops-sync-sender-migration` |
| related_review | `task_ops_sync_sender_migration_audit_R1_20260828.md` |

## GATE_VERIFY

```text
## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved | Y | N | ✅ |
| HG-AUDIT-R1 | approved | approved | Y | Y | ✅ |
| HG-GRAPH-MODULES | approved | approved | Y | Y | ✅ |

reviews：task_ops_sync_sender_migration_audit_R1_20260828.md 存在且 R1 通过？ 是
pre-30 invoke：required ∩ {10,20,00} 齐全？ 是（00 + 10；20 审查文作 R1）
结论：可进入读码/改码
```

机械：`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_ops_sync_sender_migration.md`

```text
task: task_ops_sync_sender_migration.md
| gate | status | blocks_30 | 30 影响 |
|------|--------|-----------|--------|
| HG-TASK-DRAFT | approved | 22-R1 | — |
| HG-AUDIT-R1 | approved | 30 | ✅ 可 30 |
| HG-GRAPH-MODULES | approved | — | ✅ |

VERIFY: PASS · task_ops_sync_sender_migration.md
```

## 实现摘要

1. **sender** `app/ops/admin/sender/`：httpx GitHub 分页（401/422 fail-fast；403/502/504 退避最多 5 次）；`fetch_issues` 排除 `pull_request` 键；PR 按 `updated_at` 客户端过滤；映射 GitHub JSON → `IssueIn` / `PullRequestIn` / `SyncPayload`（`raw_payload` 保留原 JSON；milestone / head_ref / base_ref / PR labels 只进 raw；state 保持 open/closed；`ci_status`/`reviewers` 空）。**不直连 PG。**
2. **CLI** `scripts/ops_sync_kimi_code.py`：`GITHUB_TOKEN` + `OPS_API_BASE_URL` + `OPS_ADMIN_SYNC_TOKEN`；POST `{base}/api/ops/admin/sync` Bearer；非 2xx 退出码非 0；incremental `since=utcnow-48h`，full `since=None`；scan/graph 文件缺失 skip。
3. **接收端** 仅 sync POST 增加 Bearer 旁路（`OPS_ADMIN_SYNC_TOKEN` 空则禁用）；`secrets.compare_digest`；cookie `MaintainerUser` 保留。
4. **GHA** `.github/workflows/ops_sync_kimi_code.yml`：cron `0 2 * * *` + `workflow_dispatch` `sync_mode`；无 Supabase env；旧仓路径注释 deprecated。
5. **G-L1**：`01_modules.md` admin 备注 + 人签行；`11_flow_sync_to_chat` 增 `gha_sender` → `admin_sync`。

未改：`chat/graph.py` · lg_rag · capability · Alembic · store.py / Supabase。未真实打 GitHub / 生产 API。未 commit / 未 push。

## 40 验证

| 项 | 结果 |
|---|---|
| ruff（触及路径） | All checks passed |
| pytest admin sync + sender | **20 passed** |
| graph-compile | exit 0 · OK: 11_flow_sync_to_chat |
| workflow 无 Supabase | grep 无匹配 |

命令：

    ruff check app/ops/admin app/ops/deps.py app/config.py tests/test_admin_sync.py tests/test_admin_sync_sender.py scripts/ops_sync_kimi_code.py
    → All checks passed!

    pytest tests/test_admin_sync.py tests/test_admin_sync_sender.py -q --tb=short
    → 20 passed in 0.22s

    ./scripts/graph-compile.sh
    → done / OK: 11_flow_sync_to_chat
    （compile 会刷新其它 flow md 的 generated_at；已 checkout 还原无关 md，仅保留 11_flow_sync_to_chat.md + graph.json）

## task 验收勾选

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
