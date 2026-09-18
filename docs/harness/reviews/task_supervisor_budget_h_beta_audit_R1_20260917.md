# Task Audit R1：supervisor-budget-h-beta

> **hat_id**：20-task-audit  
> **task**：`docs/tasks/active/task_supervisor_budget_h_beta.md`  
> **上游**：`docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md` §5 波次 β 项 6 · §8 阶段 H  
> **10 invoke**：`docs/harness/invokes/by-task/supervisor-budget-h-beta/invoke_20260917_10_task_supervisor-budget-h-beta.md`  
> **00 invoke**：`docs/harness/invokes/by-task/supervisor-budget-h-beta/invoke_20260917_00_open_supervisor-budget-h-beta.md`  
> **日期**：2026-09-17 · 审查人：20-task-audit  
> **分支**：`task/supervisor-budget-h-beta`（本帽核实 · `git branch --show-current`）  
> **task lint**：本帽复跑 `npx --yes spec-wave@2.4.2 task lint --file docs/tasks/active/task_supervisor_budget_h_beta.md` → **PASS**  
> **task 回填**：无硬伤 · **未改** task 正文 / 人工闸表

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **PASS-with-nits** · **零内容阻塞** · 可请 00 签闸后开工 30 |
| **流程闸（审查当时）** | 20 帽不代签；签收真值见文末「签收」节与 task 人工闸表 |
| **lint** | `spec-wave@2.4.2 task lint` → **PASS** |

**总评**：阶段 H 波次 β（supervisor 总预算）竖切可执行；钉死契约自洽（总步 32 · 耗尽→aggregate · 墙钟降级 · 与 4·1+1 优先级）；非范围锁死 T/W/P 与 SSE/`chat/graph.py`；与 α CLOSE 无冲突；残留风险（默认 32 / env≤0）已写清。下列 nits 供 30 知情，**不构成硬伤**。

本审查文结论/签收节按 spec-wave 2.4.x 机读口径书写（通过词落节内 · 实质充足 · 无否定共现）。

---

## 审查核对（对照 10 钉死 · 用户审查要点 · 代码锚点只读）

| # | 审查点 | 结论 |
|---|--------|------|
| 1 | 总步默认 32 / 计数范围 / 耗尽→aggregate / 墙钟降级 / 与 4·1+1 优先级 | **通过**。钉死表：`MAX_SUPERVISOR_STEPS` 默认 32；env `LG_RAG_SUPERVISOR_MAX_STEPS` 非法/≤0 回退 32；仅计 8 类 supervisor 图节点入口、不计 `rag_subtask` 内 router；主闸 `route_next_subtask` → `"aggregate"`；墙钟非硬门、默认 0=关；与 `MAX_SUBTASKS=4` 并存；全局耗尽优先于 critic retry/rebind（辅闸→`"end"`）；critic 局部 1+1 耗尽仍 END。~22 最坏路径推算与「4·1+1 + 缓冲→32」自洽 |
| 2 | 非范围锁死 T/W/P、SSE freeze、`chat/graph.py` | **通过**。非范围专节 + 验收零 diff + failure_paths「误扩/改 freeze → 拒收」；30 建议落点明示 bump intent/builder **勿**改 `chat/graph.py`（lg_rag `intent_node` 在 `strategy/intent.py`，与 chat 同名异文件） |
| 3 | failure_paths / 验收 / test_strategy 可执行 | **通过**。failure_paths 覆盖闸拒开工、总步/墙钟耗尽→aggregate、辅闸、局部 1+1、env 无限、误扩；验收可勾选 + 点名 pytest/ruff/graph-compile/lint-wiki-delta；`test_strategy=required` 且 note：先单测 route 耗尽再改图 |
| 4 | 诱扩 β 外 / 与 α CLOSE 冲突 | **未扩 · 无冲突**。范围锁 B1–B4（B2 可选）；B5 项 7–8 标「零码可顺手、非硬门」+ 跟进节；α 归档明确 β 曾挂账本波承接。未拉 T/W/P / 服务化 Registry / 跨 run confirmation |
| 5 | 残留风险（默认 32、env≤0） | **通过**。R4 residual + failure_paths「默认过小」「env 非法→无限」+ 钉死「禁静默无限」均写清 |
| 6 | 代码锚点与现状一致（只读抽查） | **通过**。`nodes.py` L48 `MAX_SUBTASKS=4` · L156 截断 · L277–286 `route_next_subtask` 仅子任务耗尽→aggregate（尚无总步守卫）；`graph.py` `_DISPATCH_MAP`/`_CRITIC_MAP` · L77–79 回边；`critic.py` L14–15 · `decide_critic_verdict` 超限→`end`；`state.py` 有 `inner_retry_count`/`rebinding_count`、**无**总步字段——与 task 缺口陈述一致 |
| 7 | R0–R5 / 元信息 / 人工闸 | **通过**。early_stop@R4 + residual；`graph_change_layer=G-L1` 仅备注不新增一级模块；闸三行 pending；10 未代签 |

---

## 阻塞

无。

---

## nits（30 可跟可不跟）与硬伤

### 硬伤（须改 task 后重审）

无。

### nits（30/00 知情即可）

1. **必读列表未点名** `app/ops/strategy/intent.py` · `app/ops/strategy/builder.py`：钉死计数含 `intent_node`/`strategy_builder`，30 建议落点已写 bump，但必读锚点表缺这两文件——30 开工前自行打开即可，不强制改 task。  
2. **行号微偏**：task 写 `_DISPATCH_MAP` L41–47，实扫为 **L42–47**（语义正确）。  
3. **主闸 aggregate vs 辅闸 end**：全局耗尽主路径必须经 aggregator；辅闸在 **已综合后** 禁 retry/rebind→`end`。正文已分主/辅，30 勿把辅闸 `end` 误读成「可跳过 aggregator」（非范围已禁耗尽直跳 END）。  
4. **墙钟检测点**：若 30 实现 B2，建议与主闸同落 `route_next_subtask`（或等价 dispatch 前），避免在 critic 之后再「同姿态→aggregate」绕回；未实现墙钟仍可勾降级跳过。

---

## 非阻塞风险（知情即可）

1. **默认 32 金样**：若真实金样仍被误杀，须 **回调 task/钉死表** 再改常量，禁 30 静默改小（failure_paths 已钉）。  
2. **env≤0 / 非法**：实现必须回退 32；审查/verify 拒收无上限路径。  
3. **B5 项 7–8**：可选零码一句；00 派 30 时勿升格为硬门或另开文档专竖切进本 PR。

---

## 回填清单

无（内容无硬伤 · **未改** task 实质）。

---

## 签收

**内容签收 · PASS-with-nits**（终轮 R1）。  
范围与钉死契约可执行；建议维护者/00 在 task 人工闸表将 HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 标为 approved 后再下发 30。  

**过程更新（2026-09-17 · 00）**：上述三闸已代签 approved（维护者令开启）· 见 `invoke_20260917_00_gates_sign_dispatch_30.md` · 机读口径已 scrub（F-6）。

---

## 维护者签闸清单（20 后 · 30 前 · 非「签收」节）

- [x] 已读 R1 审查结论（PASS-with-nits · 无硬伤）
- [x] HG-AUDIT-R1 → approved（2026-09-17 · 00 代签 · 维护者令开启）
- [x] HG-TASK-DRAFT → approved
- [x] HG-GRAPH-MODULES → approved（仅 G-L1 备注）
- [ ] commit task/审查文档（待维护者令）
- [x] 再下发 Harness 30 Prompt

30 以 task 人工闸表为准；表内未 approved 时拒开工（见 TEMPLATE_30_gate_stop.md）。
