# invoke · task_api_w_join_gap_fix 起草与修订（2026-11-02 · 10 帽 · 纯文档）

| 项 | 内容 |
|----|------|
| **时间** | 2026-11-02 |
| **性质** | task 起草 + 20-R1 修订 + 20-R2 配套（纯文档 · 零业务码） |
| **分支** | `task/api-w-join-gap-fix`（PR #307） |
| **背景** | 联调 task（workspace `task_stage_w_e2e_join_acceptance`）C1–C7 实证发现 F11（手动 resume 链 `_preflight_decided_resume` 零 TTL 检查 · app/ops/hitl/router.py:473/:520）· F12（api hitl 面无过期出口 · STATUS_EXPIRED 死码 store.py:22 · web FP-5 不可达）· F13（GET /issues · /pulls · /overview 零 tenant 谓词 · 跨租户泄漏实证 881 行全 A）· 维护者裁决「修复后复测再关」（2026-11-02） |

## 过程

1. 初版起草（PR #307 `80e0996`）：W-fix-1（HITL TTL resume 闸）+ W-fix-2（三端点租户谓词）· 四闸 pending · 红测先行 · A4②/A5 回接条款。
2. 20-R1 FAIL（B1：A5「web FP-5 可达」不可达——web 过期 mapping 只在 decide 路径，onResume 无 mapping）→ 维护者裁决扩范围 → 修订 `8b47be5`（B1 五处联动 + implement_repo 双仓 + web 质量门 + 新增 W-fix-1-web 范围条）。
3. 20-R2 PASS-WITH-MINOR（M4=web 仓需镜像薄壳）→ web 薄壳 `task_web_hitl_resume_expired_mapping.md`（web PR #85 `91e841d`）· orchestration 补闸据行 `0e4b84e`。
4. 维护者三闸同签 + 设计四决策（409+approval_expired · freeze 增补 TTL 条 · resume/消费环 · STATUS_EXPIRED 启用）→ 00 代录 `0c147a6`。
5. 00 机读修复（闸格裸 approved 化 + R2 审查文否定词机读友好化）——本 invoke 补落以满足 pre-30 invoke 帽齐全校验。

## 产出

- task 真值：`docs/tasks/active/task_api_w_join_gap_fix.md`（active · GO 30）
- web 镜像壳：`ops-desk-web/docs/tasks/active/task_web_hitl_resume_expired_mapping.md`
