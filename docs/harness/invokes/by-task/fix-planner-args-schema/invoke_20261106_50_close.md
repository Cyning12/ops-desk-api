# Invoke · 50 帽 · CLOSE 收口（fix-planner-args-schema）

| 项 | 内容 |
|----|------|
| **帽** | 50-close · **日期** 2026-11-06 |
| **task** | `docs/tasks/done/task_fix_planner_args_schema.md`（active → done 归档） |
| **分支** | `agent/planner-args-fix-task-0796db4a2434`（关账 PR 出货 · 待 lead 验收） |
| **依据** | issue #339 维护者 comment `6675685940`（40 全绿 → 关账：active→done 归档 + CLOSE 档 + 40/50 invoke + 双 README + 关账 PR 待 lead 验收） |

---

## 1. 收口动作清单

| 动作 | 状态 |
|------|------|
| task 档 active → done 归档（`git mv docs/tasks/active/ → docs/tasks/done/`） | ✅ |
| task 档 40 回填（40 注 + 验收最后一条勾选 + hat 40 自检表 + 修订记录） | ✅ |
| CLOSE 档 `docs/tasks/close/close_fix_planner_args_schema_20261106.md` | ✅ |
| 40 invoke `invoke_20261106_40_verify.md` | ✅ |
| 50 invoke（本档） | ✅ |
| 双 README（`docs/tasks/active/README.md` 关账行 + `docs/tasks/done/README.md` 关账行） | ✅ |
| `spec-wave task lint` + `lint-wiki-delta` 复检 | ✅（见 §2） |

## 2. 终态自检

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx --yes spec-wave@3.5.0 task lint --file docs/tasks/done/task_fix_planner_args_schema.md` | 0 | LINT: PASS（40/50 回填后 · 零 warn） |
| `npx --yes spec-wave@3.5.0 task lint-wiki-delta --target .` | 0 | LINT: PASS（scope all · 归档后路径） |

## 3. 全棒链留痕索引

| 棒 | 交付 | 留痕 |
|----|------|------|
| 10 起草 | task 档 + 10 invoke（诊断五环锚定 · 四闸 pending） | PR #348 squash `6533d44` |
| 20 审查 | 20-R1 审查文 + 20 invoke | `docs/harness/reviews/task_fix_planner_args_schema_audit_R1_20261106.md` + PR #349 随船 |
| 30 实现 | 案②修复资产（prompt v2→v3 ×2 + 目录块 args_schema 注入 · 红测先红后绿 · 六条件全过） | PR #349 squash `36ef90d` |
| 40 复跑 | 机制面 PASS + live 八段真落笔达成（不再撞 args_schema_invalid） | `invoke_20261106_40_verify.md` |
| 50 收口 | 归档 + CLOSE 档 + 双 README + 40/50 invoke（本 PR） | 关账 PR 待 lead 验收 |

## 修订

| 日期 | 说明 |
|------|------|
| 2026-11-06 | 50 落档：承 40 全绿销项令关账 · 全棒链同日闭环（10→20→30→40→50）· issue #329/#334/#335 偏差②×3 实质销项 |
