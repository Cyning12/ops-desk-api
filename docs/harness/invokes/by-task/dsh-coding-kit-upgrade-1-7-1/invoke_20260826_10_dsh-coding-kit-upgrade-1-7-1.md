# invoke · 10 · dsh-coding-kit-upgrade-1-7-1

| 字段 | 值 |
|---|---|
| hat | 10（task 创建） |
| 时间 | 2026-08-26（task 起草已入 master 一提交；本窗补 10 快照） |
| 执行者 | 00（父窗，维护者授权代签过程文档） |

## 摘要

- 触发：维护者粘贴 `PROMPT_00_30_upgrade_kit_1_7_1.md` 复制区（1.6.1→1.7.1 + doc-health 试点迁移 + CLOSE dogfood + Starter 00）
- 产出：`docs/tasks/active/task_dsh_coding_kit_upgrade_1_7_1.md`（取代未执行的 1.7.0 草稿）
- 闸：HG-TASK-DRAFT / HG-AUDIT-R1 00 代签；R1 文 `docs/harness/reviews/task_dsh_coding_kit_upgrade_1_7_1_audit_R1_20260826.md`
- 范围：过程轨 upgrade + `docs/spec/doc-health/` 对齐 1.7.0+ READY/PASS / Hub / PR；不改 `app/`；不搬根级裸 SPEC
- 执行棒：同会话 30（升级 + 文档 + dry-run CLOSE: READY）；40 与 30 合并快照；关账须 PR MERGED 后再 `--yes`
