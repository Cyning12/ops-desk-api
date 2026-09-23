# Invoke · 10（10-spec + 10-task）· host-v1-delegation-token（V1-A 波 · Agent Host v1.0 五波之首）

> **日期**：2026-09-23  
> **帽**：00 统筹（亲起 10-spec/10-task · 承 harness-00-delegate-only「无初稿时起草第一步」例外；30 阶段起一律委派子 Agent）  
> **维护者令（原话留痕）**：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」（2026-09-23 · 承启动 invoke `../host-v1-landing/invoke_20260923_00_host-v1-landing.md`）  
> **SPEC**：`docs/spec/host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md`（signed · HG-SPEC-SIGNOFF=approved · 00 代录 · 本窗）  
> **task**：`docs/tasks/active/task_host_v1_delegation_token.md`（draft · HG-TASK-DRAFT approved 00 代录 · HG-AUDIT-R1 **pending**）

## 必读（按序 · 已读）

1. `AGENTS.md` ✓
2. `docs/spec/agent-infra/07_host_v1_landing_plan_v0.md`（signed）✓
3. `docs/spec/agent-infra/08_host_v1_wave_spec_outlines_v0.md` §1（signed · 本波种子）✓
4. `docs/discussions/2026-09-23_agent-host-full-framework-outline_v0.md`（v0.2 · #6 差距 + D3 Tier 1）✓
5. `docs/discussions/2026-09-23_agent-host-multi-service-engineering-architecture_v0.md`（C2/C6）✓
6. `docs/_tech_graph/l1/01_modules.md`（capability/lg_rag 行 · 签录链）✓

## 开放裁定（SPEC §4 · 全部作答）

| Q | 裁定 |
|---|---|
| Q1 签名机制 | HMAC-SHA256 对称（Ed25519 弃 · 图内对称足够 · kid/version 预留 v2.0 上楼） |
| Q2 签发审批口径 | 分级：scope 内 ∩ 全只读 ∩ 非沙箱/cli → 安全域自动；其余 → HITL_REQUIRED（复用 hitl 回路）；off→observe→enforce 灰度 |
| Q3 委派网关是否立新一级模块 | **不立**：签发/验签入 `capability`（delegation.py）· 分发接线入 `lg_rag`；图谱义务=两行备注+人签新行；不新增一级模块 · 不增 implementedBy |

## 30 前置闸（GATE_VERIFY 首输出已报）

- HG-TASK-DRAFT=approved（00 代录）· HG-AUDIT-R1=**pending**（待 20-task-audit → 00 代录）· HG-GRAPH-MODULES=approved（模块表已建置真读 · 图谱新签义务随 30 落盘）
- 分支：30 开工前必须 `task/host-v1-delegation-token`（禁 master/main 直改）
- 30 不亲自：00 委派子 Agent（承 harness-00-delegate-only）

## 下一棒

20-task-audit（书面审 task · 落盘 `docs/harness/reviews/`）→ 00 代录 HG-AUDIT-R1 → 30 委派子 Agent。

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-23 | 10 棒 invoke 落盘（10-spec + 10-task 同窗完成 · 开放裁定全答 · SPEC 代录 signed） |
