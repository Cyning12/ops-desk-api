# PROMPT · 30 · specwave-upgrade-3-0-0

复制区（整段粘贴给 30 Agent）：

你是 Harness **30** 执行帽。Open Folder / cwd 必须是：

  /Users/cyning/Desktop/Ops-desk/ops-desk-api-specwave-3-0-0

分支已是 `task/specwave-3-0-0`（base origin/master）。禁止在含 budget 脏改的主仓工作区改码。

## GATE_VERIFY（首输出）

真值 = task 人工闸表（非聊天声称）：

| gate | 期望 |
|------|------|
| HG-TASK-DRAFT | approved |
| HG-AUDIT-R1 | approved |

任一 pending → 拒开工（TEMPLATE_30_gate_stop）。

再跑：`npx spec-wave verify --target . --task docs/tasks/active/task_specwave_upgrade_3_0_0.md`
（若本地仍是 2.4.2 bin，可先钉版再 verify；顺序以 task 范围 A→B→C 为准。）

必读：
- docs/tasks/active/task_specwave_upgrade_3_0_0.md（全范围 + 验收 + failure_paths）
- docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md
- docs/harness/reviews/task_specwave_upgrade_3_0_0_audit_R1_20260918.md
- 包内 MIGRATION.md（钉版 → upgrade --yes → 字面 → refresh/skills/sync）

## 执行顺序（严格）

1. package.json exact `"3.0.0"` → npm install → lock 对齐
2. npx spec-wave upgrade --yes（manifest version=3.0.0 · from_version=2.4.2；不删 .cyning-harness）
3. refresh-ide-blocks dry-run → 审 → --yes；确认 cyning-harness-local 块零变化
4. sync prompts --yes；核对 HG-GRAPH-MODULES 仍在 30-execute-code.md；冲补丁则 STOP（拒 --force）
5. skills install
6. CI lint-wiki-delta.yml 三处 @2.4.2 → @3.0.0
7. tests/test_capability_harness_cli.py 全部 2.4.2 字面 → 3.0.0（禁改测试语义）
8. 不改 app/（确认 harness_cli 仍为 spec-wave@{_kit_pin()}）
9. 验收命令全跑：--version / check / pytest / graph-compile.sh / verify --task / assets verify / pins check
10. FEEDBACK 落盘 docs/spec/doc-health/feedback/
11. 落盘 invoke：docs/harness/invokes/by-task/specwave-upgrade-3-0-0/invoke_20260918_30_implement_specwave-upgrade-3-0-0.md
12. 未另令不 commit / 不 push / 不 merge

## 回报（≤15 行）

- GATE_VERIFY 结果
- 验收勾选完成数 / 总数
- --version · check · pytest · verify 退出码
- FEEDBACK 路径
- 偏差 / 阻塞
