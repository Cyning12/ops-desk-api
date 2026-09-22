---
hat: 50
task_slug: security-input-isolation
date: 2026-09-22
---

# invoke · 50+CLOSE · security-input-isolation（L7 W1 输入结构隔离）

## 收口结论
- 五棒全通：10-spec（signed c4d42df · 四波全景裁定 W1–W4 · 实扫定最大敞口=RAG 片段+工具回执两面裸奔 · 诚实定性 W1 不声称防住注入）→ 10-task（25 验收 · B1 11 行）→ 20-audit（R1 PASS 零退回 · 零请求双断言可测性成立）→ 30（slots.py+四面接线 · 1ae6487+ad17eef · 双断言实测 · off 三态对拍 · 变异×3）→ 40（PASS 25/25 亲核 · 变异①复做 18 挂→55 绿）。
- 闸链：HG-SPEC-SIGNOFF / HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES（lc_evidence_chain +prompts 备注级边 · 52d1b45 00 ratify）全 approved（维护者授权 00 代录）。
- PR [#161](https://github.com/Cyning12/ops-desk-api/pull/161)：CI 全绿 → merge master `c530203`（2026-09-22）。
- 归档：task → done/；active README / spec 索引同步（SPEC 全景仍 active：W2/W3/W4 待后续波次；占位表下一建议序 2 = memory-compliance-delete）。

## 移交
- **灰度前必处置**：on 态非 str 结构化工具回执（内建 mock capability 真实返回 dict）经 tool_exec 保结构后 aggregator 显式炸整单（fail-closed 方向安全 · 默认关兜住）——归 W2/灰度 task。
- 图谱缺口留痕承前：lg_rag 出边缺 memory · memory 出边缺 structured_output（非本波义务）。
- 3 条本地基线红（chat_ws×2 + capability proxy）+ memory_backfill 偶发 flaky：fix 候选清单累计，建议单独 fix task 清理。
- 队列下一棒：memory-compliance-delete（M4 · 合规物理删除权）。
