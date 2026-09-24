# Invoke · 10（10-spec + 10-task）· host-v1-visibility-scenario-policy（V1-B 波）

> **日期**：2026-09-23  
> **帽**：00 统筹（亲起 10-spec/10-task · 30 起委派子 Agent）  
> **维护者令（原话留痕）**：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」（2026-09-23）·「授权00可以签收所有过程文档」（本窗）·「继续，完成后自行进行下一波，无特殊情况无需停下等待接收命令」（本窗）  
> **SPEC**：`docs/spec/host-v1-visibility-scenario-policy/SPEC-host-v1-visibility-scenario-policy_v0.md`（signed · 00 代录）  
> **task**：`docs/tasks/active/task_host_v1_visibility_scenario_policy.md`（draft · HG-TASK-DRAFT approved 00 代录 · HG-AUDIT-R1 **pending**）  
> **前置**：V1-A CLOSE（PR #179/#180 · requested_scope 已备）

## 必读（按序 · 已读）

1. `AGENTS.md` ✓ · 2. 07 规划 ✓ · 3. 08 §2（本波种子）✓ · 4. 大纲 v0.2 ✓ · 5. 工程架构 ✓ · 6. `01_modules.md` ✓ · 7. **V1-B 加读** `03_strategy_and_intent_plan_v0.md`（active · S1–S4 CLOSE）✓

## 开放裁定（SPEC §4 · 全部作答）

| Q | 裁定 |
|---|---|
| Q1 风险档粒度 | **3 档 low/medium/high**——直接消费 `IntentV1.risk_hint`（03 轨现行 schema · U2 实证消解 · 不新增字段） |
| Q2 场景维输入 | **仅意图 + intent_fallback 健康度标记**；不含会话上下文（确定性可重放 · 留 V1-D 复盘） |
| Q3 execution_type 映射 | 与 side_effect/risk_level **正交不代理**：instant/target/process 默认期望表 + 硬规则（process 必须 requires_stop_support=true · irreversible+reversible=true 矛盾拒） |

**关键安全作答**：fallback 裂缝（SO 失败默认 risk_hint=low 虚假宽松）→ S1 规则 fallback=空集 + `intent_fallback` state channel。

## 30 前置闸

HG-TASK-DRAFT=approved（00 代录）· HG-AUDIT-R1=**pending**（待 20-task-audit）· HG-GRAPH-MODULES=approved（图谱新签义务随 30 落盘）；分支 `task/host-v1-visibility-scenario-policy`（30 开工前必切）。

## 下一棒

20-task-audit → 00 代录 HG-AUDIT-R1 → 30 委派子 Agent（实现序 D1→D4→D2→D3→D5）。

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-23 | 10 棒 invoke 落盘（V1-B · 开放裁定全答 · SPEC 代录 signed · lint PASS） |
