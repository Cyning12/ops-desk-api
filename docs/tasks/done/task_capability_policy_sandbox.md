# Task：Agent Host H2 · Capability Policy 与高危执行

> **状态**：completed（2026-08-27 · 00 CLOSE PASS · 已归档）  
> **类型**：feature / agent-host-plan · H2  
> **上游规划**：`docs/spec/agent-infra/02_agent_host_plan_v0.md`  
> **ROADMAP**：`docs/spec/agent-infra/capability/ROADMAP_policy_and_sandbox_v0.md`  
> **分支**：`task/capability-policy-sandbox`  
> **前置 task**：`task_lg_rag_supervisor_capability_catalog` CLOSE ✓ · PR #70

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `capability-policy-sandbox` |
| **git_branch** | `task/capability-policy-sandbox` |
| **test_strategy** | `required` |
| **graph_change_layer** | `G-L1` |
| **wiki_delta** | `n/a` |
| **orchestration** | agent-host-plan 第二棒 = H2 |

### 人工闸

| human_gate_id | status |
|---|---|
| HG-TASK-DRAFT | approved |
| HG-AUDIT-R1 | approved |
| HG-GRAPH-MODULES | approved |

---

## 验收标准

- [x] H2-a：`check_invoke` 单测 high risk 默认 block
- [x] H2-b：`invoke` 统一过 policy
- [x] H2-c：Host-only 策略键 + plan 顶层不可写单测
- [x] H2-d：sandbox/cli 探针 env 默认关 · 显式 env 可 invoke
- [x] H2-e：span metadata `policy_blocked` · `risk_level`
- [x] H2-f：CI pytest 绿

---

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-27 |
| 定稿 | `policy.py` + `invoke` 统一 Policy 门 |
| 归档 | `docs/tasks/done/task_capability_policy_sandbox.md` |
| PR | 待 #71 merge |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 30/40 PASS · CLOSE |
