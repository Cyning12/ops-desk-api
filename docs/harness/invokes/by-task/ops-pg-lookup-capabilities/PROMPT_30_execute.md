# PROMPT · 30 · ops-pg-lookup-capabilities

> **给谁**：新开的 **30**（可含 40）。  
> **Open Folder**：`ops-desk-api/` 仓根。  
> **分支**：`task/ops-pg-lookup-capabilities`。

---

## 复制区（整段粘贴）

`````text
你是 ops-desk-api 的 30（可含 40）。只实现 ops-pg-lookup-capabilities。

工作目录：以维护者 worktree 为准的 ops-desk-api 仓根
分支：task/ops-pg-lookup-capabilities。勿 push；未授权勿 commit。

GATE_VERIFY（首输出必填表 · 真值读 task 人工闸表）
  + npx dsh-coding-kit verify --target . --task docs/tasks/active/task_ops_pg_lookup_capabilities.md
落盘 docs/harness/invokes/by-task/ops-pg-lookup-capabilities/invoke_20260828_30_40_ops-pg-lookup-capabilities.md

必读
  docs/tasks/active/task_ops_pg_lookup_capabilities.md
  docs/harness/reviews/task_ops_pg_lookup_capabilities_audit_R1_20260828.md
  app/ops/capability/gateway.py
  app/ops/capability/adapters/local_fn.py
  app/ops/capability/manifest.py（ADAPTER_PREFIX）
  app/ops/capability/defaults.py
  app/ops/lg_rag/multi/nodes.py（tool_exec_node）
  app/db/models.py（OpsIssue / OpsPullRequest）
  app/db/session.py（AsyncSessionLocal）
  tests/test_overview.py（夹具写法）
  tests/test_capability_manifest.py
  tests/test_lg_rag_supervisor_capability_catalog.py
  docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md
  docs/standards/CODING_BACKEND_L2_v1_zh.md（P-13 禁止 async 里同步 IO）

范围
  lookups.py：async get_issue_by_number / get_pr_by_number
    从 payload 解析第一个整数；多 repo 同号取 updated_at 最新
    未命中 / 解析失败 → 抛受控或返回结构让 Gateway ok=False（与现 invoke 异常→ok=False 一致即可）
    输出摘要字段；禁止 raw_payload；body 截断 500
  Gateway ainvoke：coroutine adapter 则 await；否则走现有 sync invoke（utc_now / mock 不回归）
  tool_exec_node 改 await capability ainvoke
  LocalFnAdapter 支持 async fn
  builtin.v1.yaml + _DEFAULT_SPECS 增加两枚；保留 mock + utc_now_iso
  manifest 允许前缀：
    local_fn:app.ops.capability.defaults:
    local_fn:app.ops.capability.lookups:
    其它前缀仍整文件失败
  G-L1 capability 行备注 + 10_flow_capability 可加 lookup 节点或备注 + graph-compile
  单测：命中 / 未命中 / 无数字 payload / mock 与 utc_now 回归 / manifest 前缀

硬约束
  不改 chat/graph.py、lg_rag/multi/graph.py 的边（可改 tool_exec 函数体）
  禁止 MCP、GitHub API、Eval、sync sender 文件、deferred RAG
  禁止每请求 compile；Builder 不绕过 Policy
  中文注释简洁

40
  pytest 触及路径 + ruff + graph-compile + chat/graph.py 与 multi/graph.py 拓扑 0 diff
  报告 00。简体中文。勾选 task 验收项；勿伪造测试结果。
`````

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-28 | 初版 30 Prompt |
