# ROADMAP：Capability · 可迁移内核（portable core）v0

> **层级**：L2 升级路线（capability 域）  
> **状态**：`draft`（可拆 task · **不**授权 30）  
> **上游**：[`../01_upgrade_roadmap.md`](../01_upgrade_roadmap.md) 波次 `cap-portable-core`  
> **现行契约**：[`SPEC-capability-gateway_v0.md`](./SPEC-capability-gateway_v0.md)（P0–P3 已落地，本文件在其上增量）  
> **架构边界**：[`../00_architecture_and_boundaries.md`](../00_architecture_and_boundaries.md) §3 Mode A

---

## 1. 目标

把 Capability Gateway 收成**可带走的应用层插件面**：任意编排（含非 LangGraph）只依赖 `register` / `list` / `invoke` / `provide`；默认导出路径**零** `langgraph` 依赖。

### 非目标（本 ROADMAP）

- 实现生产级远程 MCP 全集（真 MCP 另波 `cap-mcp-real`）  
- 改 supervisor 拆解算法或动态构图  
- 强制全仓改用 FC / ToolNode  
- 把 Structured Output 校验注册成「可选 capability」

---

## 2. 波次拆分（建议 task 颗粒）

### U1 · 内核去 LangGraph（优先 · = 总表波次 1）

| 项 | 要求 |
|---|---|
| 包边界 | `gateway` / `registry` / `types` / `adapters/local_fn`（及 mcp/sandbox/cli/skill **adapter 实现**）不 import `langgraph` |
| 可选桥隔离 | `adapters/langchain_tools.py`（`as_tool_node` 等）移出默认 `__init__` 导出；改为 `app.ops.capability.extras.langchain` 或文档标明「可选、非核心」 |
| 表面钉死 | Planner / tool_exec 主路径只认 `list(filter=…)` + `invoke`（Mode A） |
| `schemas_for_llm` | 可保留为**纯数据**导出（无 LG）；供外部自建 FC，不内置 ToolNode |
| 验收 | `rg -n 'langgraph' app/ops/capability` 仅命中 extras（或零）；既有 `test_lg_rag_multi` / capability 单测绿；G-L1 备注一句「可迁移内核」 |

### U2 · Planner 赋能列表契约（可与 U1 同 task 或紧随）

| 项 | 要求 |
|---|---|
| Filter | 文档化 `node_role=supervisor|tool_exec` 等给 planner 的推荐裁剪 |
| Plan 数据 | 明确：调用链是 **state 内 plan**，由静态 dispatch 解释；不 compile 新图 |
| 验收 | 短 DESIGN 或本 ROADMAP 附录 + 单测 list+filter；无强制改 supervisor prompt（可另 task） |

### U3 · 真 MCP adapter（总表波次 3 · 后置）

| 项 | 要求 |
|---|---|
| 契约 | 仍 `invoke(id, args, ctx) → CapabilityResult`；换 adapter 不换编排 |
| 与 mock | P2 mock 探针可保留 CI；真 client 默认关闭、env 开关 |
| 验收 | mock 单测 + 可选集成标记；**禁止**默认 CI 打外网 |

---

## 3. 与 v0 SPEC §4 P1 的关系

v0 P1「可选 ToolNode adapter」**不撤销历史落地**，但升级后定性为：

- **非**可迁移主路径；  
- 不得再作为「推荐挂载方式」写在域 README 首页；  
- 核心包出口以 Mode A 为准。

若破坏性调整默认导出 → 考虑升 `SPEC-capability-gateway_v1`；否则本 ROADMAP 完成后在 v0 修订记录追加「portable 完成」一行即可。

---

## 4. 失败与观测（继承 v0）

未知 id / adapter 异常 → `ok=False`，不拖垮图；span metadata 字段集不变。

---

## 5. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-26 | 初版：Mode A 可迁移；隔离 LG 桥；真 MCP 后置 |
