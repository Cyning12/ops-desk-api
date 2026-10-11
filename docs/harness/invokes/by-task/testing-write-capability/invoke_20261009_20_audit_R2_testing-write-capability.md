# 20-task-audit invoke · testing-write-capability（R2 复审 · 裁定四=乙落盘质量核查）

> **帽**：20-task-audit（R2）· **task**：docs/tasks/active/task_testing_write_capability.md（修订版 commit 2bc48e5）
> **分支**：task/testing-write-capability（worktree d2-testing-write-capability）
> **日期**：2026-10-09 · **结论**：**PASS**（内容零阻塞 · 观察项 O5–O7）· 审查文 `docs/harness/reviews/task_testing_write_capability_audit_R2_20261009.md`

---

## 触发

30 GATE_STOP（loader V1/V2/V7 夹击实证 · invoke_20261009_30 · commit 599df9b）→ 维护者裁定四=乙（manifest 顶层 idempotency_key + V1 二选一放宽）→ 10-task 修订（2bc48e5）留转 R2 复审七要点。

## 实证面（本帽实读/实跑留证）

- `manifest.py:823-830` V1 门控（is_write · http_block=spec.http or {}）· :832-836 V2 · :533-540 V7 原始数据校验 · :870-874 V8——task 锚点全中。
- `types.py:76-133` CapabilitySpec frozen dataclass 全字段带默认（增可选字段后向兼容 · V1-B SPEC :94 先例同形态）。
- `defaults.py:77-155` _DEFAULT_SPECS 五枚全 side_effect=read；`delegation.py:488-514` auto_approve_ok 不读幂等键。
- grep 实证：manifests/（builtin 5×local_fn read · oa.readonly 3×http read）无顶层 idempotency_key → V8 对称适配零误伤；loader 无顶层未知键白名单校验 → 新增解析无冲突。
- golden eval 文案钉死面（观察项 O5）：`evals/agent/golden/capability/baseline_v1.json:102,134` + `tests/eval/test_eval_agent_golden.py:26,36`。
- failure_paths 表实 10 行（:111-120）与 R4「十条」一致（O4 闭环）；R1 观察项 O1/O2/O4 勘正复核正确。

## 机械闸复跑

- `npx spec-wave task lint --file docs/tasks/active/task_testing_write_capability.md` → **LINT: PASS · EXIT=0**
- `npx spec-wave verify --target . --task docs/tasks/active/task_testing_write_capability.md` → **VERIFY: BLOCKED · EXIT=2**（HG-TASK-DRAFT / HG-AUDIT-R1 pending · 闸回退属实时序 · 符合预期）

## 本帽边界

- 未改 task 实质内容；未代签任何 human_gate；未执行 30；未触 `app/`/`tests/`。
- 交付：R2 审查文 + 本 invoke（task lint PASS 后落盘）。

## 留转

1. 维护者重签 HG-TASK-DRAFT / HG-AUDIT-R1（清单见审查文文末）。
2. 重签后下发 30：交付面 F1–F7 全量（含 loader V1/V8 适配 + A8 单测 + 01_modules.md 同步）；30 注意 O5（V1/V8 文案逐字节不变）与 O6（字段族文档三处口径）。
