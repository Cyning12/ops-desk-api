# Capability Gateway · 域夹索引（L1）

> **track**：`agent-infra` / capability  
> **实现包**：`app/ops/capability/`  
> **对照**：Agently Action（Registry + Dispatcher + Executor）；**非**业界 LLM Gateway

---

## 本夹文件

| 文件 | 层级 | 说明 |
|---|---|---|
| [`SPEC-capability-gateway_v0.md`](./SPEC-capability-gateway_v0.md) | L2 现行契约 | P0–P3 已落地；接口与失败语义真值 |
| [`ROADMAP_portable_core_v0.md`](./ROADMAP_portable_core_v0.md) | L2 升级 | Mode A 可迁移内核；隔离 LG 桥；真 MCP 后续 |

上级：[`../README.md`](../README.md) · [`../00_architecture_and_boundaries.md`](../00_architecture_and_boundaries.md) · [`../01_upgrade_roadmap.md`](../01_upgrade_roadmap.md)

---

## 现状一句话

`tool_exec_node` 已走 `capability.invoke`；默认能力在 `defaults`；P2 mock 探针默认关闭；P3 skill stub。下一优先：**可迁移内核（去 LangGraph 核心依赖）**。
