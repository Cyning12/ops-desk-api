# SPEC Audit R1：lc-evidence-chain-hardening

> **hat_id**：20-spec-audit  
> **SPEC**：`docs/spec/SPEC-lc-evidence-chain-hardening_v1.md`（v1）  
> **对照**：`docs/guides/REVIEW_lc_evidence_chain_third_party_20260816.md` §3  
> **日期**：2026-08-17  
> **签收**：维护者会话「SPEC签收」→ HG-SPEC-SIGNOFF=approved

---

## 结论

| 项 | 值 |
|---|---|
| **判定** | **pass** |
| **HG-SPEC-SIGNOFF** | **approved**（维护者已签 · 本审查文留痕） |
| **下一棒** | 新 00 在独立 worktree 起草 task → 20-task-audit → 人签/代签 HG-AUDIT-R1 → 派 30。本起草窗 **不实现** |

## 核对

| 项 | 审阅 |
|---|---|
| 范围 D1–D4（usage / grader refuse / kept 排序 / G-L1） | OK |
| 非范围（勿改 graph、不升 freeze、timeout 60、lru_cache、CE→EXACT、接回 Graph） | OK |
| 方案：complete 副作用上报；异常 ≡ 空 grades；同档稳定排序 | OK |
| 验收可测（pytest mock 三组 + graph diff） | OK |
| failure_paths（grader 200 vs answer 500 已区分） | OK |
| 思考轮控制 R0–R5 · early_stop=no | OK |
| Trace 树已完成故排除 | OK（与 2026-08-17 UI 关账一致） |
| 真值用复核表而非三方原文错误 P0 | OK |

## 残余风险（不挡签）

- `complete()` usage 依赖调用时已在 generation span 内  
- 句边界截断 / 检索缓存仍为后续 backlog  
- 起草 SPEC 的 agent 与 20 审同窗：人已签收覆盖；实现交新 00

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-17 | 首审 pass · 对齐维护者签收 |
