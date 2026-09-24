# Invoke · 10（10-spec + 10-task）· host-v1-llm-factory-closure（V1-C 波 · 与 V1-B 并行）

> **日期**：2026-09-23  
> **帽**：00 统筹（亲起 10-spec/10-task · 30 起委派子 Agent）  
> **维护者令（原话留痕）**：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」（2026-09-23）·「授权00可以签收所有过程文档」·「继续，完成后自行进行下一波，无特殊情况无需停下等待接收命令」（本窗）  
> **SPEC**：`docs/spec/host-v1-llm-factory-closure/SPEC-host-v1-llm-factory-closure_v0.md`（signed · 00 代录）  
> **task**：`docs/tasks/active/task_host_v1_llm_factory_closure.md`（draft · HG-TASK-DRAFT approved 00 代录 · HG-AUDIT-R1 **pending**）  
> **并行说明**：与 V1-B 并行（07 §3.1 授权 · 文件面零交叠——B 触 strategy/capability/lg_rag · 本波仅 app/llm）

## 必读（按序 · 已读）

1. `AGENTS.md` ✓ · 2. 07 规划 ✓ · 3. 08 §3（本波种子）✓ · 4. 大纲 v0.2（#12/#22/#23/#24）✓ · 5. 工程架构 ✓ · 6. `01_modules.md` ✓

## 开放裁定（SPEC §4 · 全部作答）

| Q | 裁定 |
|---|---|
| Q1 预算检查点层位 | **llm 层单检查点**（`app/llm/budget.py` · usage ContextVar 同源；双检查点弃——口径漂移） |
| Q2 缓存适用范围 | **只缓存 plan/参数模板（结构化产物）· 不缓存流式终答**（时效性证据 · 承 fallback B2 纪律） |
| Q3 规则引擎档形态 | **固定文案模板档 `rule:<name>`**（承 fallback ACTION_STATIC 先例 · 规则 DSL 弃） |

## 30 前置闸

HG-TASK-DRAFT=approved（00 代录）· HG-AUDIT-R1=**pending**（待 20-task-audit）· HG-GRAPH-MODULES=approved（llm 行备注义务随 30 落盘）；分支 `task/host-v1-llm-factory-closure`（30 开工前必切）。

## 下一棒

20-task-audit → 00 代录 HG-AUDIT-R1 → 30 委派子 Agent（实现序 D4→D1→D2→D3→D5→D6）。

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-23 | 10 棒 invoke 落盘（V1-C · 开放裁定全答 · SPEC 代录 signed · lint PASS · 与 V1-B 并行） |
