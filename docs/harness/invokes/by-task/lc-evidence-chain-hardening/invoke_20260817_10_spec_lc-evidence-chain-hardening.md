# Invoke：10-spec · lc-evidence-chain-hardening

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 10-spec |
| task_slug / spec_slug | `lc-evidence-chain-hardening` |
| task_paths | （task 由新 00 起草 · 本窗不出） |
| related_review_or_none | 上游评审 `docs/guides/REVIEW_lc_evidence_chain_third_party_20260816.md` |
| git_branch | `task/lc-evidence-chain-hardening` |
| created_utc_or_local | 2026-08-17 |
| notes | 生产旁路已稳；按仓内复核后的采纳表出 SPEC；不改码 |

---

## 裁决

- **从 10-spec 起**：硬化项跨 `llm.complete` 观测与旁路闸语义，需 SPEC 锁「不改 graph / 不升 freeze / 不把错误 P0 做进去」。
- 真值来源：三方原文 **不可直接当 backlog**；以评审 §3 修订表为准，并剔除已完成的 Trace 树。
- 下一棒：已签收；新 00 出 task。本窗 **禁 30**。

## 结论摘要

必做：`complete()` 聚合上报 usage；grader 异常 fail-closed 为 refuse（HTTP 200）；`kept` 按 `relevance.level` 降序。  
明确不做：timeout 60、单例、lru_cache、CE→EXACT、接回 Graph。

## 交付

- `docs/spec/SPEC-lc-evidence-chain-hardening_v1.md`（accepted · HG-SPEC-SIGNOFF=approved）
- `docs/guides/REVIEW_lc_evidence_chain_third_party_20260816.md`（从 tracing 分支 `3cc9219` 恢复，master 线此前未合入）

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-08-17 | 10-spec 首稿 |
| 2026-08-17 | 人签后回填 accepted；task 交新 00 |
