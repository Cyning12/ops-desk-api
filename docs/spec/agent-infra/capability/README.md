# Capability Gateway · 域夹索引（L1）

> **track**：`agent-infra` / capability  
> **实现包**：`app/ops/capability/`  
> **对照**：Agently Action（Registry + Dispatcher + Executor）；**非**业界 LLM Gateway

---

## 本夹文件

| 文件 | 层级 | 说明 |
|---|---|---|
| [`SPEC-capability-gateway_v0.md`](./SPEC-capability-gateway_v0.md) | L2 现行契约 | P0–P3 已落地；接口与失败语义真值 |
| [`ROADMAP_portable_core_v0.md`](./ROADMAP_portable_core_v0.md) | L2 升级 | Mode A 可迁移 · **U1–U3 DONE** |
| [`ROADMAP_policy_and_sandbox_v0.md`](./ROADMAP_policy_and_sandbox_v0.md) | L2 Host 轨 H2 | Policy 门 + sandbox/cli/code |

上级：[`../README.md`](../README.md) · [`../02_agent_host_plan_v0.md`](../02_agent_host_plan_v0.md) · [`../03_strategy_and_intent_plan_v0.md`](../03_strategy_and_intent_plan_v0.md)

---

## 现状一句话

`tool_exec_node` 已走 `capability.invoke`；默认能力在 `defaults`；P2 mock 探针默认关闭；P3 skill stub；**真 MCP · 默认关 · CI 不外网**（`McpClientAdapter` + `OPS_CAPABILITY_MCP_ENABLED`）。可迁移内核（Mode A）已落地。  
**Policy ≠ Strategy Builder**：Policy 为 invoke 硬闸；本轮可见集裁剪见 [`../strategy/`](../strategy/)（draft）。  
目录配置化（YAML manifest）规划于策略轨 **S3**，与 `defaults` 迁移对齐。

