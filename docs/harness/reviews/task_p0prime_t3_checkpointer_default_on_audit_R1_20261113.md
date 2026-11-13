# Audit R1：P0' T3 PG checkpointer 默认翻开

- **日期**：2026-11-13
- **task_slug**：p0prime-t3-checkpointer-default-on
- **review_hat**：20 · **audit_profile**：human_only
- **HG-AUDIT-R1**：approved（维护者会话签收 m00177「签收，开始」，覆盖 P0' T1–T7 全部任务卡）

## 审查范围

纯 env 默认值翻转（LG_RAG_HTTP_CHECKPOINTER unset=postgres）+ 测试面卫生 + 脚本/docs/图谱同步。零 DDL · 零新表/迁移 · hitl 链路行为码零 diff（503 fail-closed 保留）。

## 签认要点

1. **翻转语义**：unset→开；显式 postgres（大小写/空白）→开；其余任意值（含空串）→关。空值回退口保留，.env 压制/测试卫生手法不变。
2. **测试面兜底**：conftest autouse fixture setenv 空值；delenv 站点全部手术（delenv 会吃到新默认）。
3. **反向对照改写**：test_sse_does_not_open_pg_saver_by_default 语义反转 → test_sse_does_not_open_pg_saver_when_explicitly_off（验回退口有效）。
4. **风险与残留**：CI 无 PG service（skip 绿缺口既有注记，另 task 议）；N-R2-1 真 PG 复测本地不可行 → 偏差登记 issue #23；灰度三步 ②③ 属运营侧。
5. **裁定依据**：issue Cyning12/ops-desk-workspace#23 R4 评论裁定 P2（纯 env 翻转无 DDL · 存量 run 无 checkpoint 属预期 · 503 防御保留）。
