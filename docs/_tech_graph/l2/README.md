# G-L2 indexes · 说明

> 默认不要整目录加载。按 path / symbol 命中后再打开对应 yaml。  
> 试点域：`chat`（`10_flow_chat`，**含 RAG 子链**节点 `retrieve` / `grade` / `refuse_answer` → `app/ops/chat/rag_nodes.py`）。  
> 拓扑变更须同步更新 **flow yaml + indexes**（`implementedBy` 集合 ⊆ indexes 集合，双向一致）。
