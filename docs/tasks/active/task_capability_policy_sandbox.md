# Task：Agent Host H2 · Capability Policy 与高危执行

> **状态**：active（draft · H1 CLOSE ✓ · 可 20 审）  
> **类型**：feature / agent-host-plan · H2  
> **上游规划**：`docs/spec/agent-infra/02_agent_host_plan_v0.md`  
> **ROADMAP**：`docs/spec/agent-infra/capability/ROADMAP_policy_and_sandbox_v0.md`  
> **SPEC**：`docs/spec/agent-infra/capability/SPEC-capability-gateway_v0.md`  
> **分支**：`task/capability-policy-sandbox`  
> **前置 task**：`task_lg_rag_supervisor_capability_catalog` CLOSE ✓

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `capability-policy-sandbox` |
| **git_branch** | `task/capability-policy-sandbox` |
| **test_strategy** | `required` |
| **test_strategy_note** | policy 单测；high risk 默认 block；sandbox env 默认关；CI 零外网 shell |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta_note** | `capability` / `lg_rag` 备注 policy 门；不新增一级模块 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **orchestration** | agent-host-plan 第二棒 = H2 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | pending | 22-R1 | H1 关账后再 20 审 |
| HG-AUDIT-R1 | pending | 30 | |
| HG-GRAPH-MODULES | approved | 30 | 仅备注 |

---

## 背景与目标

`invoke` 前统一 **Policy 门**；sandbox/cli/code 注册到 Capability，**高危默认 blocked**，env 显式放开。

---

## 范围 / 非范围

**范围**：`policy.py` + `invoke` 统一校验 · blocked → `ok=False` + `policy_blocked` · sandbox/cli 样例（默认关）· span metadata · `test_lg_rag_multi` 不回归

**非范围**：生产容器沙箱全集 · 模型写 policy · 默认 CI 真 shell · 改 chat/graph 拓扑

---

## 验收标准

- [ ] H2-a：`check_invoke` 单测 high risk 默认 block
- [ ] H2-b：`invoke` 统一过 policy
- [ ] H2-c：Host-only 策略键文档 + 单测 plan 不可写
- [ ] H2-d：sandbox/cli 样例注册 env 默认关
- [ ] H2-e：span metadata
- [ ] H2-f：multi 单测绿

---

## failure_paths

| 触发 | 行为 |
|---|---|
| policy block | `ok=False` · error 含 `policy_blocked` |
| sandbox env 关 | invoke 不执行或 stub block |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 00 拆 task · 依赖 H1 |
