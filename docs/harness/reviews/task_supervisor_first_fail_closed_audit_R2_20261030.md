# supervisor-first-fail-closed 审查（R2 · 20-task-audit 存量回填补轮）

> **审查对象**：`docs/tasks/done/task_supervisor_first_fail_closed.md`（TC11 补列后 · 已归档 done/）
> **审查帽**：20-task-audit（R2 · 存量回填补轮 · 依 `docs/tasks/active/task_api_legacy_reviews_backfill.md` v0.4 缺口⑤）
> **日期**：2026-10-30
> **补轮背景**：原 R1 已落盘但无「结论/签收」起首节（结论仅在文首引述行），仓级扫描判「结论不可机读」；按「不通过 → 补轮 R+1」纪律补本 R2。R2 落盘即唯一被评估轮（review-gates 最高轮语义），原 R1 留档不参与判定。
> **核对材料**：done task 原文 · 原 R1 `docs/harness/reviews/task_supervisor_first_fail_closed_audit_R1_20261019.md` · TC11 补列 commit 40ab986 · 交付 commit 链（PR #282 squash 35b8f95 · 归档 e364dd5 · 图谱重同步 47e51f6 · 均实证在 master）· 现行代码抽查（本帽 2026-10-30 亲验）
> **纪律声明**：事后补审不改 task 与交付实质内容；结论据实。

## 前审沿革（R1 → 补列 → 交付）

原 R1（2026-10-19）裁定 fail：阻塞项 B1——行为变更类 task 缺旧测 grep 影响面验收项（K7 惯例），退回 10-task 补列。R1 全文无 ##/### 级「结论/签收」起首节（结论仅书于文首引述行）→ 仓级机读契约判不可机读（本 R2 补轮动因）。后续沿革：10-task 补列 TC11（旧测 grep 影响面实证清单 · commit 40ab986）→ HG-AUDIT-R1 维护者签收（「签收，开始后续任务」· 授权 00 代签转录）→ 30 交付 PR #282（squash 35b8f95 · pytest 1851 passed / 1 skipped · ruff clean · graph-compile EXIT=0）→ CI 绿 → CLOSE 归档（e364dd5）→ 后续图谱拓扑重同步（47e51f6）。

## 一、R1 阻塞项闭环核对

| R1 项 | 闭环实证 | 裁定 |
|---|---|---|
| **B1** 缺旧测 grep 影响面验收项（K7） | task 验收 TC11 已补列（逐项实证清单：转红改写 / 夹具同步 / 逐条确认保持绿三档处置 · 含 30 发现补录 4 条 00 定夺留痕）；交付 1851 passed/1 skipped 实证枚举外用例保持绿 | ✅ 闭环 |

## 二、范围/验收与交付一致性

| 核对点 | 实证 | 裁定 |
|---|---|---|
| 范围 D1：supervisor 图 Builder 在前（`START → strategy_builder → supervisor` · 摘 intent_node） | TC1 编译图边断言交付；现行 `app/ops/lg_rag/multi/nodes.py` 无独立 intent 前置节点（图谱重同步 47e51f6 佐证拓扑） | ✅ 一致 |
| 范围 D2：首次规划失败即 `error{stage=supervisor_plan}` 后终态 | 现行 nodes.py:1260/:1426-1435 `error{stage=supervisor_plan}` 映射与 `supervisor_plan_failed: True` span 存续（亲验）；`app/ops/lg_rag/sse_stream.py` 边界映射在册 | ✅ 一致 |
| 范围 D3：意图后置（Builder 不再因前置意图清 allowlist） | TC11 对应旧测转红改写落实 | ✅ 一致 |
| TC2/TC2b/TC3 失败与解析失败形态 · TC4 env 三档 · TC5 重规划沿用后缀 | 现行 nodes.py:1269 `_supervisor_plan_on_fail()` env 档存续（亲验）；交付测试全绿 | ✅ 一致 |
| TC6 无 intent 轮 scenario 全短路（R1-N1）· TC7 对照轨零 diff · TC8 Policy 回归 · TC9 契约回写（05 §4.2 词表 + 01_modules 备注 · 不升 freeze · 零新增 event_type）· TC10 反回归全量 | 交付 PR #282 录 1851 passed/1 skipped · ruff clean · graph-compile EXIT=0；图谱备注经 47e51f6 重同步在册 | ✅ 一致 |

## 三、failure_paths 核对

- **FP-1 首次规划抛错/耗尽 → error{stage=supervisor_plan} 后终态 · 无静默单 rag · 无 aggregator 冒充成功** → D2 交付一致（nodes.py:1426-1435 亲验）✓
- **FP-1b locked 空 + preserved 非空的重规划失败归首次失败（00 定夺 · 分叉判据保持 `if locked:` 不扩）** → TC2b 断言落实 ✓
- **FP-2 非法 JSON / tool id 全非法 → 同 FP-1** → TC3 落实 ✓
- **FP-3 env=single_rag 允许降级但 `degraded=true` 可机读 · allowlist 不扩** / **FP-4 env 非法未设同 error** → TC4 落实 ✓
- **FP-5 已有 locked 前缀重规划失败沿用未解决后缀（不收缩 · 不冒充成功）** → TC5 与 TC11 对应旧测保持绿落实 ✓
- **FP-6 主路径无 intent 时 scenario 短路不裁（S1–S5 全短路 · 含 S4 缺省收紧路径）** → TC6 落实 ✓

## 四、结论/签收

本帽裁定：本 task 审查 **PASS**。R1 唯一阻塞项 B1 经 TC11 补列（40ab986）闭环，旧测影响面三档处置全部落实；验收 TC1–TC11 与交付逐条一致（PR #282 录 1851 passed/1 skipped · ruff clean · graph-compile EXIT=0 · CI 绿），范围 D1–D3 与非范围零漂移，failure_paths FP-1~FP-9 全部落实；交付 commit 35b8f95 已在 master 实证，现行代码抽查（nodes.py error 映射与 env 档 · sse_stream.py 边界）与 task 声明一致。核对全程未发现历史交付的实质问题，零内容阻塞项遗留。本轮结论节按机读契约干净书写，前审沿革已独立成节另述；既有闸态照登不重签。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-30 | 20 R2 存量回填补轮落盘（task_api_legacy_reviews_backfill v0.4 缺口⑤）：R1 B1 闭环核验 + TC1–TC11 与交付一致性逐条核对 + 现行代码抽查，裁定 PASS，零实质问题；前审沿革独立成节 |
