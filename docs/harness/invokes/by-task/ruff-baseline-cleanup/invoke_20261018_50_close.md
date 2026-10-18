# invoke：50-close（ruff-baseline-cleanup 关账 · 2026-10-18）

> 帽：50-CLOSE · 执行人：00（维护者授权 m01131「合并」）

## 一、前置核验

| 项 | 证据 |
|---|---|
| PR #274 MERGED | squash `b73bb8a` · CI 4/4 绿 · 235 文件 |
| 30 交付 | TC-RC-1~8 全 PASS · invoke_20261018_30_ruff_cleanup.md · check 52→0 · format 223→0 · pytest 红集逐名全等 |
| R1 审查 | task_ruff_baseline_cleanup_audit_R1_20261018.md 签收零阻塞 nit×1 顺手精化（CI 钉 ruff==0.15.21） |
| 三闸 | HG-TASK-DRAFT/HG-AUDIT-R1 approved（m01101「全A」授权 00 代录）· GRAPH n/a · verify EXIT=0 PASS |

## 二、关账动作清单

- [x] `git mv` task → docs/tasks/done/
- [x] 状态行 → done CLOSED
- [x] 修订记录 +CLOSED 行
- [x] docs/tasks/active/README.md 登记
- [x] CLOSE 档 docs/tasks/close/close_ruff_baseline_cleanup_20261018.md
- [x] 本 invoke 落盘

## 三、质量钉

- `npx spec-wave task lint --file docs/tasks/done/task_ruff_baseline_cleanup.md` → **LINT: PASS**
- `npx spec-wave verify --target .` → **EXIT=0 VERIFY: PASS**（存量豁免留痕无新增）

## 四、移交

- N818 CircuitOpen 改名如需→另立 task（API 语义变更）
- CI ruff 闸已生效防回归 · 存量面清零闭环
