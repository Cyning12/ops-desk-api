# 20 invoke · hitl-approval-consumption（SPEC 书面审 R1 · 签发审批消费回路）

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 20-spec-audit |
| task_slug / spec_slug | `hitl-approval-consumption` |
| 对象 SPEC | `docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v0.md`（v0 · draft · commit 2fd69c8） |
| related_review_or_none | `docs/harness/reviews/spec_hitl-approval-consumption_audit_R1_20261009.md` |
| git_branch | `spec/hitl-approval-consumption`（worktree spec-hitl-approval-consumption · base master ca4148f） |
| created_utc_or_local | 2026-10-09 |
| notes | 审查 PASS-WITH-NITS；不代签 HG-SPEC-SIGNOFF；不附 30 Prompt |

---

## 结论

判定 **PASS-WITH-NITS**。起草者留转六条逐条裁定全 PASS（payload 增键不越界 · TTL 3600s 读时过期成立 · async 化冲击面有界 · unlock 形态守卫完备 · env 追加集不削弱 fail-closed 默认面 · 读时活状态可审计）；通用核对 10 项全过；反回归三面 + decide 落库不动以源码实读钉死。非阻塞 nits N1–N4（锚点行号精度 · async 波及面点名 · TTL 上下界数值 · decided_at 双 store 类型归一）移交 task 阶段。

**HG-SPEC-SIGNOFF 维持 pending**，待维护者人签；签录后下一棒：**新 00** 起草 task（`task/hitl-approval-consumption` 自 master 分出 · 携带 N1–N4）→ 20-task-audit → HG-AUDIT-R1 → 30。本窗不实现。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-09 | 20-spec-audit R1 落盘：审查文 + 本 invoke；不 push 不开 PR；留维护者人签 HG-SPEC-SIGNOFF |
