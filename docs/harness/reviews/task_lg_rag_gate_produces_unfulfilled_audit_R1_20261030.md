# lg-rag-gate-produces-unfulfilled 审查（R1 · 20-task-audit 存量回填）

> **审查对象**：`docs/tasks/done/task_lg_rag_gate_produces_unfulfilled.md`（已归档 done/ · CLOSED 2026-10-30）
> **审查帽**：20-task-audit（R1 · 存量回填补审 · 文档健康度整理窗口：归档触发仓级 reviews 扫描缺口 1「missing R<n>」，承 task_api_legacy_reviews_backfill 补审体例，不走豁免）
> **日期**：2026-10-30
> **补审背景**：本 task 交付期（2026-10-27/28）仓级 reviews 机读扫描对 active/ 目录不要求 R 档落盘，HG-AUDIT-R1 由维护者会话签收（m00811「签收，删除草稿」）；归档 done/ 后进入扫描面判缺口，按回填纪律补审落盘。
> **核对材料**：done task 原文 · CLOSE 档 `docs/tasks/close/close_lg_rag_gate_produces_unfulfilled_20261030.md` · PR [#297](https://github.com/Cyning12/ops-desk-api/pull/297) 交付链（squash `0a5d6109` · `git merge-base --is-ancestor` 实证在 master）· 现行代码抽查（本帽 2026-10-30 亲验）
> **纪律声明**：事后补审不改 task 与交付实质内容；范围/验收/failure_paths 逐条对照交付实证核对，结论据实。

## 一、范围与非范围核对

| task 声明 | 交付实证 | 裁定 |
|---|---|---|
| B1 判定3收窄：未兑现字段未被本步 consumes 引用 → 降级观察留痕放行 | 现行 `app/ops/lg_rag/multi/step_contract.py:256` `def unfulfilled_produces(`（亲验）；编排层 `app/ops/lg_rag/multi/nodes.py:1182` `_record_span_metadata({"step_contract_produces_unfulfilled": ...})` 复用既有 span 通道（亲验） | ✅ 一致 |
| B2 逃生口指引：失败摘要段附「重发前驱步」指引 | 现行 `app/ops/lg_rag/multi/nodes.py:867-871`「以修正后的 produces 重发前驱步（作为新步、新 subtask_id）」（亲验） | ✅ 一致 |
| 非范围：不动 capability manifest output_schema（task A 地盘）· 不动前缀不可变语义 · 判定1/2 不动 · critic/预算不动 | PR #297 交付面仅 step_contract.py / nodes.py / 钉测；task A（PR #294）独立合并互不越界 | ✅ 一致 |
| 观察留痕不新增事件类型（graph_delta=n/a） | span 复用 `_record_span_metadata` 通道，无新事件类型注册 | ✅ 一致 |

**根因与修复对因核对**：task 钉案死锁四环——判定3 对全部前驱校验 produces 兑现不管本步 consumes 是否引用（d3a49 run 实证）→ 已终态前驱锁定重规划改不动 → 修复点在模型够不到处 → 两轮照抄 budget_exhausted。B1 收窄拦因（未被消费的未兑现声明无实际数据流、拦截无防御收益），B2 给带内逃生口径，机制对因；非症状性打补丁。

## 二、验收标准与交付一致性

| 验收 | 实证 | 裁定 |
|---|---|---|
| 1. 单测复刻 d3a49 闸场景：放行 + 观察留痕断言 | `tests/test_gate_produces_unfulfilled.py` 现存于仓（亲验）；PR #297 录红测先行 9 failed → 全绿 | ✅ |
| 2. 零回归：consumes 引用缺失字段仍拦（判定2）· prefix_touch_required 分类不变 · 判定1 不动 | PR #297 录目标组 57 passed | ✅ |
| 3. 失败摘要段指引文案 + 无失败步主路径 prompt 逐字节零 diff | PR #297 录 TC4 钉死（承 PR #293 FP 口径） | ✅ |
| 4. ruff（钉 0.15.21）绿 + pytest 不引入新红 | PR #297 录全量 28F/1958P/3s = 基线 28F/1948P + 10 新测零新红 | ✅ |
| 5. 40 live 复跑 #2140 query（t2 write 执行、不再 budget_exhausted） | PR 验证节明示「验收⑤ 40 live 复跑留签收后」，合并时未附实证 | **OPEN**（移交 CLOSE 档维护者 checklist · 不美化为 PASS） |

## 三、failure_paths 核对

- **放行后下游隐式需要未兑现字段** → task 安全性论证：worker 只见 `collect_values` 按 consumes 显式绑定且真实存在的字段（`step_contract.py` 原 :273-279 口径），未消费声明不构成数据流：论证与交付语义一致 ✓
- **B2 指引被模型忽视（照抄惯性）** → 观察留痕可度量 + budget 闸兜底终局：span 通道已落 ✓
- **与 task A 联序（A 消猜 / B 救回，独立可合）** → A 以 PR #294 于同日先合、B 以 PR #297 后合，两 PR 独立无冲突：落实 ✓

## 四、结论/签收

本帽裁定：本 task 审查 **PASS-WITH-OPEN-ITEM**。验收 ①–④ 与交付逐条一致，范围与非范围零漂移，failure_paths 防护落实；交付 commit `0a5d6109`（PR #297）已在 master 实证，现行代码抽查（`step_contract.py:256` 纯函数 · `nodes.py:1182` span 留痕 · `nodes.py:867-871` 指引文案 · 钉测文件存续）与 task 声明一致。验收⑤ 40 live 复跑为唯一未核销项，task 原文自声明「LLM 弹性项」，已移交 CLOSE 档维护者 checklist 挂号跟进。HG-AUDIT-R1 当时维护者签收（task 人工闸表 m00811 转录）与本审查结论相容；本件为存量回填审查，既有闸态照登不重签。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-30 | 20 R1 存量回填补审落盘（文档健康度整理窗口 · 归档触发仓级扫描缺口 1）：done task + CLOSE 档 + PR #297 交付链 + 现行代码抽查逐条核对，裁定 PASS-WITH-OPEN-ITEM（验收⑤ OPEN 移交），零实质阻塞 |
