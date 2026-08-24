# 跨仓 POINTER（G-L0 · 不复制对端图谱）

> **一句话**：本仓与配对仓的契约入口指针。  
> **禁止**：粘贴对端 `graph.json` / 整份 flow Mermaid。

| 对端 | 路径 / 契约 | 本仓状态 | 备注 |
|------|-------------|----------|------|
| `ops-desk-web` | 消费 `/api/ops/*` · SSE chat · cookie session | 契约消费方 | Phase γ 再物理分层；α 期不在本仓伪造 web 图谱 |
| `ops-desk-ios` | `LatestChatSession` · 只读 issues/PRs/overview | **未分层** | Phase δ 后置；仅契约 POINTER |
| `ops-desk-workspace` | docker-compose · 总文档 · 编排 task | 编排 / 人闸 | 不在 workspace 伪造本仓图谱正文 |
| 规格包 | `Projects/docs/harness/spec/graph_skill_layering_v1/` | 方法论真值 | 短约定见本仓 `LAYER_README.md` |

## 关键跨仓 flow id（本仓）

| flow / 契约 | 本仓资产 |
|-------------|---------|
| Chat SSE/WS | `l1/10_flow_chat.*` + `l2/indexes` |
| Auth session cookie | `l1/10_flow_auth.*` |
| Admin sync → chat context | `l1/11_flow_sync_to_chat.*` |
| LC Evidence HTTP | `l1/10_flow_lc_evidence.*`（**W2 待建** · TBD） |
| LG RAG HTTP | `l1/10_flow_lg_rag.*`（**W2 待建** · TBD） |
