# G-L2 indexes · 说明

> **默认不要整目录加载。** 按 path / symbol 命中后再打开**对应域** yaml。  
> **禁止**把多域倒排汇总进单一 `by_path.yaml` / `by_symbol.yaml`。

## 试点域（分文件）

| 域 | graph_id | path 倒排 | symbol 倒排 | 覆盖策略 |
|---|---|---|---|---|
| `chat` | `10_flow_chat` | [`indexes/by_path.yaml`](./indexes/by_path.yaml) | [`indexes/by_symbol.yaml`](./indexes/by_symbol.yaml) | flow 全部 `implementedBy` |
| `lg_rag` | `10_flow_lg_rag` | [`indexes/by_path_lg_rag.yaml`](./indexes/by_path_lg_rag.yaml) | [`indexes/by_symbol_lg_rag.yaml`](./indexes/by_symbol_lg_rag.yaml) | **全量** `implementedBy`（传输 Spec 系列 §9 硬约束） |

- **chat**：含 RAG 子链节点 `retrieve` / `grade` / `refuse_answer`。  
- **lg_rag**：P2 第二试点；与 [`05_lg_rag_transport_and_session_plan_v0.md`](../../spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md) **§9** 绑定——本系列改节点必须同步本域 indexes。

## 一致性

1. 拓扑变更须同步 **对应域的 flow yaml + indexes**。  
2. 该域 `implementedBy` 集合 ⊆ 该域 indexes（`by_path` 按 node_id 条；共享 symbol 允许多 node_id，`by_symbol` 用 `also_node_ids`）。  
3. chat 与 lg_rag **不得**交叉写入对方 yaml。
