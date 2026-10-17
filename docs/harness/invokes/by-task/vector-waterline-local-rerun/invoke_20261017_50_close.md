# invoke：50-close（vector-waterline-local-rerun 关账 · 2026-10-17）

> 帽：50-CLOSE · 执行人：00（维护者授权 m00847「合并 + 立核查 task」）

## 一、前置核验

| 项 | 证据 |
|---|---|
| PR #268 MERGED | squash `e20bc4d` · CI 4/4 绿 · mergedAt 2026-10-17 |
| 40 实证 | TC-LR-1~6 全 PASS 零假绿 · invoke_20261017_40_rerun.md · 真实报告 reports/vector_waterline_local_20261017T123649Z.yaml |
| R1 审查 | task_vector_waterline_local_rerun_audit_R1_20261017.md PASS 零阻塞 |
| 三闸 | approved（m00823 授权 00 代录）· verify EXIT=0 VERIFY: PASS |

## 二、关账动作清单

- [x] `git mv` task → docs/tasks/done/
- [x] 状态行 → done CLOSED（PR 号/squash/验收摘要）
- [x] 修订记录 +CLOSED 行
- [x] docs/tasks/active/README.md 登记（单档关账行）
- [x] CLOSE 档 docs/tasks/close/close_vector_waterline_local_rerun_20261017.md（六节体例承 close_hitl_resume_async_20261015.md）
- [x] 本 invoke 落盘

## 三、质量钉

- `npx spec-wave task lint --file docs/tasks/done/task_vector_waterline_local_rerun.md` → **LINT: PASS**（2026-10-17 实跑）
- `npx spec-wave verify --target .` → **EXIT=0 VERIFY: PASS**（4 条存量基线豁免留痕 · 无新增豁免）

## 四、移交

- 另立 task_local_vector_data_state_audit（mismatch 8574 溯源 · 10-task 起草中）
- HG-PROD-READONLY-ACCESS 生产水位真跑仍 pending 移交维护者
