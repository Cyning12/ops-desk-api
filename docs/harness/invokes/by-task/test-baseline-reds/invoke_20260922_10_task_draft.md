# invoke · 10-task · task 落稿记录

> hat=10 · 2026-09-22

- 落稿：`docs/tasks/active/task_test_baseline_reds.md`（bugfix 双轨跳 SPEC · 依据=40 观察项五份 + 本批 10 复现 invoke）
- 格式基准：`docs/tasks/done/task_memory_fuse_tz_fix.md`（bugfix 先例）
- 闸表：HG-TASK-DRAFT / HG-AUDIT-R1 落稿时待签（blocks 30 · 00 代录）· HG-GRAPH-MODULES approved（none 代录 · 只改 tests/ 实扫无图谱改动）· HG-PILOT-OPSDESK-GLAYER n/a
- 验收 8 条断言化：A1/A2 前红→后绿 · A3 flaky 20 连跑 + 全量 3 连跑零复发 · A4 双环境 · A5 全量回归 · A6 改动边界 + ruff + lint
- 思考轮 R0–R3（early_stop at R3：三根因实证闭环 · R3 含 D1 反向交叉验证）
- B1 旧测影响面实扫落盘（见 b1 invoke 与 task 正文表）

## 收尾（lint / README / commit 回填）

- `npx spec-wave task lint --file docs/tasks/active/task_test_baseline_reds.md`：**PASS**（首轮 E5 缺自检结论节 → 补占位节后 PASS）
- active README 加行：已落（task 表首行）
- commit：本文件所在 commit（fix/test-baseline-reds 头 · docs-only · 未 push）
