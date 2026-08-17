# Task Audit R1：rag-embed-api-backend

> **hat_id**：20-task-audit  
> **task**：`docs/tasks/active/task_rag_embed_api_backend.md`  
> **对照**：冷启动记录 `ops-desk-workspace/docs/04-infrastructure/04-rag-embed-cold-start_note_20260817.md`；先例 `task_siliconflow_rerank_api`  
> **日期**：2026-08-17  
> **分支**：`task/rag-embed-api-backend`  
> **审查**：书面审查 · **不**改 `app/`（本文件成稿时闸仍可由 00/子 agent 代签）  
> **结论**：内容 **`pass`**

---

## 结论摘要

| 维度 | 判定 | 说明 |
| --- | --- | --- |
| **内容可执行** | **pass** | 范围/非范围/验收/failure_paths/test_strategy/必读齐全；`ApiEmbedder` 已存在，插入点在两处 `_get_embedder`，30 可执行 |
| **思考轮审查** | **pass** | 控制表闭合（R5）；residual_risks 写明禁隐式回落 ST、模型名锁 bge-m3 |
| **与精排先例** | **对齐** | `RAG_*_BACKEND=siliconflow\|local` 模式；复用 `SILICONFLOW_*`；compose 透传同套路 |
| **是否退回 10-task** | **否** | 无内容阻塞 |
| **建议代签** | **是** | 维护者已授权子 agent 实现且 00 只验收 PR 关账 → 可签 `HG-TASK-DRAFT` + `HG-AUDIT-R1` |

---

## 元信息核对

| 字段 | task 值 | 审阅 |
| --- | --- | --- |
| `task_slug` | `rag-embed-api-backend` | OK |
| `git_branch` | `task/rag-embed-api-backend` | OK |
| `test_strategy` | `required` | OK |
| `test_strategy_note` | mock `POST /embeddings`；不打真实 SiliconFlow | OK；可执行 |
| `code_quality_bar` | `L2_backend` | OK |
| `graph_change_layer` | `G-L1` | OK：一句备注，不新增一级模块 |
| `graph_delta` | `docs/_tech_graph/l1/01_modules.md` | OK |
| `wiki_delta` | `n/a` | OK |
| `review_hat` | `20` | OK |
| `required_invoke_hats` | `10,30` | OK |
| `invoke_retention_profile` | `default` | OK（须有 10 等 pre-30 invoke） |
| `HG-GRAPH-MODULES` | approved | OK；不新增一级模块 |

---

## 核对表

### 1 · 范围

| task 范围项 | 审阅 | 说明 |
| --- | --- | --- |
| `get_query_embedder()` 按 `RAG_EMBED_BACKEND` | **pass** | 默认 siliconflow → `ApiEmbedder`；local → ST |
| 接线 `retrieve.py` + `rag_nodes.py` | **pass** | 现均硬编码 ST；须改走工厂 |
| env + 复用 `SILICONFLOW_*`；模型默认 `BAAI/bge-m3` | **pass** | 与库 fingerprint 一致；可 `RAG_EMBED_MODEL` |
| 缺 key / HTTP 明确失败；**无**隐式回落 ST | **pass** | 与冷启动根因对策一致 |
| `.env.example` + 生产 compose 透传 | **pass** | compose 在 workspace 跨仓；不阻塞内容 |
| 单测 mock httpx；不改 hybrid_recall / grader / Qdrant | **pass** | |
| G-L1 一句 + graph-compile | **pass** | |

**现实现可执行性（只读）**

- `ApiEmbedder`：sync `httpx.post` `/embeddings`、按 `index` 保序、缺 key 构造期 `RuntimeError`、失败重试日志。查询侧用 `asyncio.to_thread(embed, …)` 可沿用。  
- 缺 key：**不要** import 期无条件炸；懒加载工厂首次取实例时失败即可（可测）。  
- **本波只改查询路径**；`scripts/rag_ingest.py` 已有 `--api` 开关，默认 ST，保持即可。

### 2 · 非范围

| 非范围项 | 审阅 |
| --- | --- |
| 全量重灌 / 改维 | **pass** |
| ingest 默认改远程 | **pass**（本波可不改） |
| lifespan 预热 / HF volume / 升配 | **pass** |
| 换百炼 embeddings | **pass** |
| 改 SSE / LC HTTP freeze / `graph.py` | **pass** |

### 3 · 验收标准

| 验收 | 审阅 |
| --- | --- |
| 默认 siliconflow 不加载本地 ST | **pass** · 单测断言不调 `SentenceTransformer` |
| mock 向量 shape / 保序 | **pass** |
| 缺 key / HTTP 可测失败且不隐式 ST | **pass** |
| `BACKEND=local` stub ST | **pass** |
| 两入口接线 | **pass** |
| env + compose | **pass** |
| 不改 `graph.py` | **pass** |
| ruff + pytest + graph-compile | **pass** |
| 人工小机抽检 | **pass**（留给 00/运维） |

### 4 · failure_paths

与「不隐式回落本地」一致；超时/5xx/缺 key → 查询失败可重试；模型名错 → 打回。**pass**。

### 5 · 思考轮

R0–R5 闭合；early_stop=no；residual_risks 充分。**pass**。

---

## 非阻塞提醒（30）

1. `ApiEmbedder` 构造缺 key 即 raise：工厂应懒加载，避免模块 import 炸全站。  
2. 失败**禁止** catch 后改建 `SentenceTransformerEmbedder`。  
3. 跨仓 compose 改完须在交还 00 时单列说明（workspace 另 commit）。  
4. 勿动 `app/ops/chat/graph.py`、`task_ops_sync_sender_migration`、未跟踪 `lg_rag/`。

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-17 | R1 书面审 · 内容 pass |
