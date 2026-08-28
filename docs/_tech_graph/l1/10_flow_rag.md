---
graph_id: 10_flow_rag
version: 2026-08-25
generated_at: 2026-08-28T02:18:29Z
source: 10_flow_rag.graph.yaml
---

# RAG 混合检索摘要流程（hybrid_recall）

RAG 查询侧摘要流（选项 A 独立 flow · spec modules/rag.md §3 拍板）：query → embed（bge-m3）→ hybrid_recall → dense（Qdrant 默认 | pgvector 即时降级）/ FTS·sparse 第二路（PG）→ RRF k=60 融合 →（可选）CE rerank → RetrievedChunk[] top-5；Qdrant 命中经 PG hydrate 回表取正文。ingest 侧不展开（摘要粒度）。消费方：chat/rag_nodes.retrieve_node · lc_evidence_chain。

## Mermaid

```mermaid
flowchart TB
    caller["调用方（chat/rag_nodes · lc_evidence_chain）"]
    embed_query["query embed（bge-m3）"]
    hybrid_recall["hybrid_recall（入口）"]
    backend_gate["search_dense_with_fallback（即时降级）"]
    dense_qdrant["dense · Qdrant Cosine（默认）"]
    dense_pgvector["dense · pgvector fallback"]
    fts_pg["FTS / sparse 第二路（PG）"]
    hydrate["PG hydrate（Qdrant 命中回表）"]
    rrf_fuse["RRF 融合（k=60 · 两路等权）"]
    rerank["rerank（可选 · CE 精排）"]
    result["RetrievedChunk[]（fused top-5）"]
    siliconflow["SiliconFlow（/embeddings · /rerank）"]
    qdrant["Qdrant"]
    db["PostgreSQL（ops_knowledge_chunks）"]
    main_doc[">../l0/00_main.md"]

    caller -->|"query"| embed_query
    %% → app/ops/chat/rag_nodes.py#L68
    embed_query -->|"POST /embeddings（默认 ApiEmbedder；RAG_EMBED_BACKEND=local → 本机 ST）"| siliconflow
    %% → app/ops/rag/embedder.py#L92
    embed_query -->|"qvec"| hybrid_recall
    %% → app/ops/chat/rag_nodes.py#L73
    hybrid_recall -->|"dense 路选择"| backend_gate
    %% → app/ops/rag/retrieve.py#L200
    %% → app/ops/rag/backend.py#L57
    backend_gate -->|"[默认 qdrant · 失败再试 1 次]"| dense_qdrant
    %% → app/ops/rag/backend.py#L63
    %% → app/ops/rag/backend.py#L68
    backend_gate -->|"[err → 即时降级 #124; RAG_VECTOR_BACKEND=pgvector]"| dense_pgvector
    %% → app/ops/rag/backend.py#L64
    %% → app/ops/rag/backend.py#L78
    dense_qdrant -->|"query_points（hnsw_ef · with_payload 仅小字段）"| qdrant
    %% → app/ops/rag/retrievers/qdrant_retriever.py#L75
    dense_qdrant -->|"hit ids"| hydrate
    %% → app/ops/rag/retrievers/qdrant_retriever.py#L109
    hydrate -->|"SELECT ... WHERE id = ANY(:ids)"| db
    %% → app/ops/rag/retrievers/qdrant_retriever.py#L113
    hybrid_recall -->|"第二路 [fts 默认 #124; sparse C 臂]"| fts_pg
    %% → app/ops/rag/retrieve.py#L204
    fts_pg -->|"tsvector @@ plainto_tsquery（可选 glossary 展开）"| db
    %% → app/ops/rag/retrieve.py#L214
    hydrate -->|"semantic 路（k_each）"| rrf_fuse
    %% → app/ops/rag/retrieve.py#L217
    dense_pgvector -->|"semantic 路（k_each）"| rrf_fuse
    %% → app/ops/rag/retrieve.py#L217
    fts_pg -->|"keyword 路（k_each）"| rrf_fuse
    %% → app/ops/rag/retrieve.py#L217
    rrf_fuse -->|"[RAG_RERANK_ENABLED → 粗排 top-M 精排]"| rerank
    %% → app/ops/chat/rag_nodes.py#L76
    rrf_fuse -->|"[rerank off → 粗排 top-5]"| result
    %% → app/ops/chat/rag_nodes.py#L78
    rerank -->|"POST /rerank（[err] fail-closed 回退粗排）"| siliconflow
    %% → app/ops/rag/reranker.py#L171
    %% → app/ops/rag/reranker.py#L260
    rerank -->|"top-5（顶分地板 + 相对顶分过滤）"| result
    %% → app/ops/rag/reranker.py#L277
    %% → app/ops/rag/reranker.py#L287
    result -->|"RetrievedChunk[]（.fused）"| caller
    %% → app/ops/rag/retrieve.py#L233
    hybrid_recall -->|"加载"| main_doc

    classDef phase fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef doc fill:#fff8e1,stroke:#ff6f00,stroke-width:1px
    classDef infra fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px
    class embed_query,hybrid_recall,backend_gate,dense_qdrant,dense_pgvector,fts_pg,hydrate,rrf_fuse,rerank phase
    class caller,result,siliconflow,qdrant,db,main_doc infra
```

## Structured Data

### Nodes

| ID | Label | Kind |
|----|-------|------|
| caller | 调用方（chat/rag_nodes · lc_evidence_chain） | external |
| embed_query | query embed（bge-m3） | flow |
| hybrid_recall | hybrid_recall（入口） | flow |
| backend_gate | search_dense_with_fallback（即时降级） | flow |
| dense_qdrant | dense · Qdrant Cosine（默认） | flow |
| dense_pgvector | dense · pgvector fallback | flow |
| fts_pg | FTS / sparse 第二路（PG） | flow |
| hydrate | PG hydrate（Qdrant 命中回表） | flow |
| rrf_fuse | RRF 融合（k=60 · 两路等权） | flow |
| rerank | rerank（可选 · CE 精排） | flow |
| result | RetrievedChunk[]（fused top-5） | external |
| siliconflow | SiliconFlow（/embeddings · /rerank） | external |
| qdrant | Qdrant | external |
| db | PostgreSQL（ops_knowledge_chunks） | external |
| main_doc | >../l0/00_main.md | external |

### Edges

| From | To | Mark | Type | Label | Anchors |
|------|----|------|------|-------|---------|
| caller | embed_query | -> | depends_on | query | 1 anchor(s) |
| embed_query | siliconflow | -> | depends_on | POST /embeddings（默认 ApiEmbedder；RAG_EMBED_BACKEND=local → 本机 ST） | 1 anchor(s) |
| embed_query | hybrid_recall | -> | depends_on | qvec | 1 anchor(s) |
| hybrid_recall | backend_gate | -> | depends_on | dense 路选择 | 2 anchor(s) |
| backend_gate | dense_qdrant | ?> | branches | [默认 qdrant · 失败再试 1 次] | 2 anchor(s) |
| backend_gate | dense_pgvector | ?> | branches | [err → 即时降级 \| RAG_VECTOR_BACKEND=pgvector] | 2 anchor(s) |
| dense_qdrant | qdrant | -> | depends_on | query_points（hnsw_ef · with_payload 仅小字段） | 1 anchor(s) |
| dense_qdrant | hydrate | -> | depends_on | hit ids | 1 anchor(s) |
| hydrate | db | -> | depends_on | SELECT ... WHERE id = ANY(:ids) | 1 anchor(s) |
| hybrid_recall | fts_pg | -> | depends_on | 第二路 [fts 默认 \| sparse C 臂] | 1 anchor(s) |
| fts_pg | db | -> | depends_on | tsvector @@ plainto_tsquery（可选 glossary 展开） | 1 anchor(s) |
| hydrate | rrf_fuse | -> | depends_on | semantic 路（k_each） | 1 anchor(s) |
| dense_pgvector | rrf_fuse | -> | depends_on | semantic 路（k_each） | 1 anchor(s) |
| fts_pg | rrf_fuse | -> | depends_on | keyword 路（k_each） | 1 anchor(s) |
| rrf_fuse | rerank | ?> | branches | [RAG_RERANK_ENABLED → 粗排 top-M 精排] | 1 anchor(s) |
| rrf_fuse | result | ?> | branches | [rerank off → 粗排 top-5] | 1 anchor(s) |
| rerank | siliconflow | -> | depends_on | POST /rerank（[err] fail-closed 回退粗排） | 2 anchor(s) |
| rerank | result | -> | depends_on | top-5（顶分地板 + 相对顶分过滤） | 2 anchor(s) |
| result | caller | -> | depends_on | RetrievedChunk[]（.fused） | 1 anchor(s) |
| hybrid_recall | main_doc | -> | depends_on | 加载 |  |
