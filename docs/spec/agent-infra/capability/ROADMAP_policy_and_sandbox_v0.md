# ROADMAP：Capability · Policy 与高危执行（H2）

> **层级**：L2 路线（capability 域 · 波次 H2）  
> **状态**：`active`（task → [`task_capability_policy_sandbox.md`](../../../tasks/active/task_capability_policy_sandbox.md) · 阻塞 H1 CLOSE）
> **上游**：[`../02_agent_host_plan_v0.md`](../02_agent_host_plan_v0.md) · H1 完成后  
> **现行契约**：[`SPEC-capability-gateway_v0.md`](./SPEC-capability-gateway_v0.md)

---

## 1. 目标

在 `invoke` 前统一 **Policy 门**；bash/code/sandbox/cli 走同一 Capability 面，**高危默认 blocked**，仅 env/Host 配置显式放开。

### 非目标

- 生产级容器沙箱全集  
- 模型可写 policy 字段  
- 默认 CI 执行真 shell  

---

## 2. 交付项

| ID | 内容 | 验收 |
|---|---|---|
| H2-a | 新模块 `policy.py`（或 gateway 内聚）：`check_invoke(spec, ctx) → allow|block|reason` | 单测 high risk 默认 block |
| H2-b | `invoke()` 入口统一过 policy；blocked → `ok=False` + `error` 含 `policy_blocked` | 不抛垮调用方 |
| H2-c | Host-only 策略键（对齐 SPEC §3.4）；plan/state **不可**写入 | 单测 + 文档 |
| H2-d | 注册 sandbox/cli 能力样例（env 默认关）；`app/tools/run_code` 收敛或废弃 POINTER | 默认关 |
| H2-e | span：`policy_blocked` · `risk_level` · `capability_id` | Langfuse metadata |
| H2-f | `test_lg_rag_multi` 不回归 | pytest 绿 |

---

## 3. 建议 task

- **slug**：`capability-policy-sandbox`  
- **依赖**：H1 完成（supervisor 已消费 catalog）

---

## 4. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 初版 H2 条文 |
