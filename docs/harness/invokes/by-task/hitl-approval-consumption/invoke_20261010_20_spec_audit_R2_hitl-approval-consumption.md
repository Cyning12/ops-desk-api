# invoke · 20-spec-audit R2 书面审 hitl-approval-consumption SPEC v1（2026-10-10）

> **帽**：20-spec-audit（R2 · 重派 · 前任子 Agent 卡滞已由 00 interrupt，本棒接手重跑）
> **对象**：`docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md`（commit 6eb509f · draft · HG-SPEC-SIGNOFF=pending）
> **审查文**：[`spec_hitl-approval-consumption_audit_R2_20261010.md`](../../../reviews/spec_hitl-approval-consumption_audit_R2_20261010.md)
> **结论**：**R2 PASS-WITH-NITS**（八条全 PASS · R2-N1~N3 移交 task）· 建议维护者签 HG-SPEC-SIGNOFF（本帽不代签）

## 令与纪律执行

- 令：00 派发 R2 八条重点逐条裁定（源码实读核实），不改 SPEC 实质；审查文 + 本 invoke 落盘；commit docs(review)；不 push 不开 PR。
- 骨架先行：开工先写审查文骨架（结论表 + 八条占位），其后逐条裁定即 edit 落盘，无攒全文。
- 实证复核：SPEC v1 全文 259 行 · R1 审查文全文 · 终局 §4 :77-86 · handoff PROMPT 全文 · 源码（router.py decide/callback/resume 三端点 · delegation.py:85-107 · store.py:55-169 · db/models.py:464-487 · resume.py:1-80 · nodes.py:277-301,1397-1471 · strategy/config.py:1-45 · builder.py:170-189）· `git log b1d74be..6eb509f -- app/ tests/` 为空（R1 后代码零漂移）。

## 八条裁定摘要

| # | 审查点 | 裁定 |
|---|---|---|
| 1 | D5 三件套闭合性 | PASS（触发器/行锁/补偿扫描三环齐备 · 纪律 6 锁无状态） |
| 2 | 配置面 fail-closed + decide 零 diff | PASS（_DecidePayload 实读成立 · 附 R2-N1/N2） |
| 3 | A9/A10 可机断性 | PASS |
| 4 | FP-8~FP-11 充分性 | PASS（并发三源同幂等兜底 · TTL 过期双层闭合） |
| 5 | v0 存续性 | PASS（R1 六裁定无破坏 · 代码零漂移） |
| 6 | N3/N4 吸收正确性 | PASS（delegation.py:107 · store.py:98/:159-163 逐字对拍） |
| 7 | 终局 §4 :82-83 逐字对齐 | PASS（七要素全命中） |
| 8 | handoff 验收令落实 | PASS（A9+A3 双模式钉 done{completed}） |

## 非阻塞 nits（移交 task · 与 R1 留存 N1/N2 叠加携带）

- **R2-N1**：resume_mode 未知值 400 vs decide 端点 Pydantic 422 先例（router.py:113,115）形态落差——task 钉实现路径。
- **R2-N2**：OA /callback dict 面（router.py:236-238）是否承接 resume_mode / 触发器挂点（decide 端点 vs adecide 成功点）——task 裁定。
- **R2-N3**：FOR UPDATE SKIP LOCKED 仓内无先例——task 给行锁锚点与并发断言基建。

## 过程留痕

- 前任 R2 子 Agent 卡滞 · 00 interrupt 后重派本棒；父窗补充情报（两条候选 nit）经本帽独立实读复核后采纳为 R2-N1/N2（非照抄：422/400 双先例定位与 D1 来源无关性不对称为本帽实读新证）。
- 闸态：HG-SPEC-SIGNOFF 仍 **pending**，待维护者人签（00 依授权代录口径 · 本帽不代签）。
