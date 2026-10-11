# Invoke：10-task · testing-write-capability

| 字段 | 值 |
|------|-----|
| **时间** | 2026-10-09 |
| **帽** | 10-task |
| **task_slug** | `testing-write-capability` |
| **git_branch** | `task/testing-write-capability`（worktree：ops-desk-api-worktrees/d2-testing-write-capability · base master 57fbf84） |
| **task** | `docs/tasks/active/task_testing_write_capability.md` |
| **上游** | `docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md` 偏差登记（阶段 3 全链未验 → 「注册非只读测试 capability → 另立 task」） |
| **禁区** | 未改 `app/` / `tests/` / `docker-compose.yml`；未代签 `HG-TASK-DRAFT` / `HG-AUDIT-R1` / `HG-GRAPH-MODULES`（三闸全 pending）；未 push |

---

## 本帽交付

| 项 | 结果 |
|----|------|
| task 落稿 | 背景 / 现状锚点（10 处逐行实读）/ 钉死契约 9 条 / 范围 F1–F6 / 非范围 / failure_paths 8 条 / B1 旧测影响面 10 文件 / 验收 A1–A7 可机断 / R0–R5 全轮 early_stop at R5 |
| 人工闸 | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均保持 `pending`（本帽不代签）· HG-PILOT-OPSDESK-GLAYER n/a |
| `graph_change_layer` | `l1`（capability 模块内增量 · 边界不变） |
| `invoke_retention_profile` | `default`（required_invoke_hats=`10,20,30,40`） |

---

## Judgment（10）

- **裁定一 · manifest 独立文件**：`testing.v1.yaml` 经 `OPS_CAPABILITY_EXTRA_MANIFESTS` 显式加载；并入 builtin 会破 `tests/test_capability_manifest.py:83` `capability_manifest_count == 5` 且 off 非零 diff → 否
- **裁定二 · 可见性放行=env 门控 tag 白名单**：新增 `CapabilityFilter.allow_write_tags_any` + `OPS_CAPABILITY_ALLOW_WRITE_TAGS`（默认空=判序零 diff）；全局松 deny_write / 加 DOMAIN_ALLOW_TAGS / enabled=false 三岔路均实证否掉；`deny_high_risk` 永不设豁免口
- **裁定三 · adapter 罐头**：`defaults.py` 纯函数零 IO（复用 `utc_now_iso` 范式）；HITL 触发只读 manifest 声明的 `side_effect: write`，语义 mock 足够
- **R3 交叉验证新发现**：`risk_level` 不得标 `high`（deny_high_risk 判序在 deny_write 前且无豁免口 → 可见性永不达）· 已钉死契约
- **触发链复核**：`nodes.py:287-288` tool∉effective_scope 不走 HITL → 可见性放行是全链验收不可省前提；BUILDER/SUPERVISOR filter 为模块级常量 → env 须 import app 前生效（钉死契约 + failure_paths 双落）

---

## 下一棒

**20-task-audit** → 审查文落盘 `docs/harness/reviews/` → 人签 HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES → GATE_VERIFY → 派 30

| 2026-10-09 | 10 落稿首版 |
