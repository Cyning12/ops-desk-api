# Invoke · 10（10-spec + 10-task）· host-v1-episodic-memory-feedback（V1-D 波）

> **日期**：2026-09-23  
> **帽**：00 统筹（亲起 10-spec/10-task · 30 起委派子 Agent）  
> **维护者令（原话留痕）**：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」（2026-09-23）·「授权00可以签收所有过程文档」·「继续，完成后自行进行下一波，无特殊情况无需停下等待接收命令」（本窗）  
> **SPEC**：`docs/spec/host-v1-episodic-memory-feedback/SPEC-host-v1-episodic-memory-feedback_v0.md`（signed · 00 代录）  
> **task**：`docs/tasks/active/task_host_v1_episodic_memory_feedback.md`（draft · HG-TASK-DRAFT approved 00 代录 · HG-AUDIT-R1 **pending**）  
> **并行说明**：V1-B/C 在轨并行（文件面零交叠 · 本波=memory/db/scripts）· V1-A CLOSE（run 归因载体已备）

## 必读（按序 · 已读）

1. `AGENTS.md` ✓ · 2. 07 规划 ✓ · 3. 08 §4（本波种子）✓ · 4. 大纲 v0.2（#9/#32/#33/#34 · D3 Tier 2）✓ · 5. 工程架构 ✓ · 6. `01_modules.md` ✓ · 事实记忆面（memory-facts-p0 SPEC signed · preference-profile · session-summary off 态先例）✓

## 开放裁定（SPEC §4 · 全部作答）

| Q | 裁定 |
|---|---|
| Q1 episode 粒度 | **run 级**（一 run 一 episode · 工具序列作字段 · 归因=V1-A run_id 同源；subtask 级弃——写入放大+噪声） |
| Q2 聚类选型 | **指纹规则**（failure_class×context_fingerprint 确定性分组+频次阈值≥3 · embedding 弃——不可机验） |
| Q3 注入预算上限 | **三闸**：默认 3 条 · 单条 ≤200 字符 · 整块 ≤800 字符（承 step_contract 整块预算先例 · 动态百分比弃） |

**铁律**：闸/库物理分离零互写（U4 · 双向断言+import 守护）· 双开关默认关（写/召回分立）· 人工确认闸（建议零自动回写）· **本波唯一 alembic 义务**（off 态 drop 安全承 session_summaries）。

## 30 前置闸

HG-TASK-DRAFT=approved（00 代录）· HG-AUDIT-R1=**pending**（待 20-task-audit）· HG-GRAPH-MODULES=approved（memory/db 行备注义务随 30 落盘）；分支 `task/host-v1-episodic-memory-feedback`（30 开工前必切 · worktree 隔离承 B/C 先例）。

## 下一棒

20-task-audit → 00 代录 HG-AUDIT-R1 → 30 委派子 Agent（实现序 D1→D2→D3→D4→D5→D6）。

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-23 | 10 棒 invoke 落盘（V1-D · 开放裁定全答 · SPEC 代录 signed · lint PASS） |
