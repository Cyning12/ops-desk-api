# Agent Infra · 长期 SPEC 索引

> **用途**：LangGraph 旁路（`lg_rag` 等）之上的**应用层基础设施**契约；与单次业务 task 解耦，可跨版本迭代。  
> **状态约定**：`draft` → `active` → `stable`；大改升文件版本号（`_v0` → `_v1`），小改在文内「修订记录」追加。  
> **上游讨论**：`docs/discussions/`  
> **下游落地**：须另开 `docs/tasks/active/task_*.md` + 人工闸；**本目录本身不授权 30 改码**。

---

## 命名边界（强制）

| 名称 | 管什么 | 不是什么 |
|---|---|---|
| **Capability Gateway** | 节点 ↔ 外置能力（local_fn / MCP / sandbox / CLI / 日后 skill） | 业界 LLM Gateway（LiteLLM 类） |
| **Structured Output Gateway** | LLM 文本 → 校验/纠偏/预算重试 → 结构化结果 | Agently Skill；不是业务 Prompt 全集 |
| **LLM Gateway**（本仓另议） | 应用 ↔ 模型供应商（路由/failover/计费） | 本子目录当前**不**立 SPEC |

---

## 当前 SPEC

| ID | 文件 | 版本 | 状态 | 一句话 |
|---|---|---|---|---|
| `capability-gateway` | [SPEC-capability-gateway_v0.md](./SPEC-capability-gateway_v0.md) | v0 | active（已签 · 排队） | 能力注册 / 筛选 / 统一 invoke |
| `structured-output-gateway` | [SPEC-structured-output-gateway_v0.md](./SPEC-structured-output-gateway_v0.md) | v0 | active（已签 · **本波优先**） | parse → validate → repair/retry |

---

## 迭代规则

1. **只改契约与边界**写进本目录；实现细节进 DESIGN/IMPL 或 task。  
2. 每次实质修订：文首版本不变时追加「修订记录」一行；破坏性变更 → 新文件 `_vN` 并在本 README 换链。  
3. 与 Agently 对照只作**思想对齐**，禁止把 Agently 整仓拖进 ops-desk 依赖。  
4. 首批接入面优先：`lg_rag` supervisor `tool_exec` / JSON 节点；**不**默认改 `chat/graph.py`。

---

## 关联

| 类型 | 路径 |
|---|---|
| 讨论小结 | `docs/discussions/2026-08-26_lg-rag-agent-capability-architecture.md` |
| Phase 4 设计 | `docs/guides/DESIGN_langgraph-lg-rag-phase4-multiagent_v1.md` |
| 现状工具草稿 | `app/tools/` · `app/ops/lg_rag/multi/nodes.py` `MOCK_TOOLS` |
