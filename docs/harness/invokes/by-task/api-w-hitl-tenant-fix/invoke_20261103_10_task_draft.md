# Invoke · 10 帽 · task 起草（api-w-hitl-tenant-fix）

| 字段 | 值 |
|------|-----|
| hat_id | `10`（task/文档 · 起草棒 · 纯文档轨零业务码） |
| task_slug | `api-w-hitl-tenant-fix` |
| task_paths | `docs/tasks/active/task_api_w_hitl_tenant_fix.md` |
| related_review_or_none | `docs/harness/reviews/task_api_w_hitl_tenant_fix_audit_R1_20261103.md`（R1 后补 · 双址规约） |
| git_branch | `agent/hitl-tenant-fix-task-955c1cd011b6`（10 起草 PR #312 · MERGED squash `04245ef`） |
| created_utc_or_local | 2026-11-03 |
| notes | 维护者 issue #311 令起草；授权边界：只产 task 档 + lint PASS + PR，30 改码待四闸签收后另行授权 |

---

## §1 · 起草摘要

- **task 档**：`docs/tasks/active/task_api_w_hitl_tenant_fix.md`（10 起草壳 · commit `9b74a78` · 零 `app/` diff · +219 行）
- **缺陷源**：联调实证双缺陷（workspace C8 invoke §C6/§2）——N-R2-1（resume 执行体零 tenant 还原 · 回执 `d6bd262904544232` 错标）+ F3（delegation 建单 `tenant_id=''` 真空 · 实扫 40 行）+ 守卫真空（`nodes.py:499-504` 仅 capability_write 类查租户）
- **起草内容**：范围/非范围/验收/failure_paths/人工闸表（四闸 pending 起 + HG-W-TENANT-DESIGN 设计闸三决策点）/R0–R3 思考轮（R3 early_stop）；红测先行入 test_strategy；双 freeze 红线（SSE event_type / hitl-browser-decide-v1）入 failure_paths；证据锚全引 workspace C8 invoke §C6/§2 + 终验 invoke §2 + backlog B2
- **PR**：#312（https://github.com/Cyning12/ops-desk-api/pull/312 · 2026-11-03 MERGED · squash `04245ef`）

## §2 · 验证

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx spec-wave task lint --file docs/tasks/active/task_api_w_hitl_tenant_fix.md` | 0 | LINT: PASS（2026-11-03 · 起草棒 · 闸表签收修订后复跑同 PASS） |
| `git diff master...HEAD --stat`（起草 PR） | 0 | 仅 task 档 1 文件 +219 · 零 `app/` diff |

## §3 · 下一棒

`20`（20-R1 审查 · 维护者亲自执行 · 审查文 invoke_20261103_20_r1_audit.md + 址A `docs/harness/reviews/task_api_w_hitl_tenant_fix_audit_R1_20261103.md`）

---

### 修订

| 日期 | 说明 |
|------|------|
| 2026-11-03 | 10 起草棒 invoke 补落档（起草当时走 PR #312 直达 · 本档按 invokes/by-task/ 结构补登记供 verify 消费 · 内容回录自 PR #312） |
