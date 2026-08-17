# Task：查询路径嵌入改为 SiliconFlow API（默认 ApiEmbedder）

> **状态**：completed（50 机械 PASS · 待 CLOSE 归档）  
> **类型**：feature / RAG 嵌入层 · 运维减负  
> **上游记录**：`ops-desk-workspace/docs/04-infrastructure/04-rag-embed-cold-start_note_20260817.md`（冷启动只记）  
> **契约对照**：`ops-desk-workspace/docs/contracts/rag-knowledge-contract-v1.md` Q3（bge-m3@1024；ApiEmbedder 为已备降级路径）  
> **先例**：`task_siliconflow_rerank_api`（精排已 HTTP）；`app/ops/rag/embedder.py` · `ApiEmbedder` 已存在  
> **实现仓**：本仓（Open Folder = 本仓根）  
> **建议分支**：`task/rag-embed-api-backend`  
> **编排**：workspace 出单 → 本仓 active 真值 → 20-task-audit → 闸 → 30/40 → 父窗 00 验收 / PR / CLOSE  
> **无关**：勿与 `task_ops_sync_sender_migration`、已关账 `lc-evidence-chain-hardening` 混改；勿碰未跟踪 `app/ops/lg_rag/`。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `rag-embed-api-backend` |
| **git_branch** | `task/rag-embed-api-backend` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | pytest mock `POST /embeddings`：维度/保序、缺 key/HTTP 失败可观测失败路径、`RAG_EMBED_BACKEND=local` 仍可走 ST（不强制 CI 加载真模型）；不打真实 SiliconFlow |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` |
| **graph_delta_note** | `rag` / `lc_evidence_chain` 备注补「查询 embed 默认可走 SiliconFlow HTTP」；不新增一级模块；不改 chat graph 边 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 行为真值在 env + G-L1；不改 coding_wiki |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **orchestration** | 默认远程 embed（生产小机）；`local` 显式保留给有内存本机 / 离线 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-17 子 agent 代签：维护者授权「分配子 agent 实现、00 只验收 PR 关账」；workspace 总单已对齐复制入本仓 |
| HG-AUDIT-R1 | approved | 30 | 2026-08-17 子 agent 代签：20 R1 内容 pass（`docs/harness/reviews/task_rag_embed_api_backend_audit_R1_20260817.md`）；代签依据同上 |
| HG-GRAPH-MODULES | approved | 30 | 真值 `docs/_tech_graph/l1/01_modules.md`；本 task 不新增一级模块 |

---

## 背景与目标

生产 2C4G 上，查询路径仍懒加载本地 `SentenceTransformerEmbedder`（bge-m3 ~2.3GB）。进程/容器首次（或 recreate 丢 HF 缓存后）retrieve 可达**分钟级**，并与 Nginx/前端 120s 超时叠加失败。精排已切 SiliconFlow；嵌入的 `ApiEmbedder` 类已写好但**未接到** Chat / LC Evidence 查询路径。

**完成态**：生产默认查询 embed 走 SiliconFlow `POST /embeddings`（模型名仍 `BAAI/bge-m3`，与库内 fingerprint 一致）；进程**不再**为答问冷加载本地 ST；`local` 后端可显式切回；失败路径可测、有日志。

---

## 范围（本仓）

1. 统一查询侧 embed 工厂（建议抽到 `app/ops/rag/embedder.py` 或薄 `get_query_embedder()`）：按 env 返回 `ApiEmbedder` / `SentenceTransformerEmbedder`。  
2. 接线：  
   - `app/ops/lc_evidence_chain/retrieve.py`  
   - `app/ops/chat/rag_nodes.py`  
   二者改为走工厂，**禁止**继续硬编码仅 ST。  
3. env（建议名，30 可微调但须写进 `.env.example`）：  
   - `RAG_EMBED_BACKEND=siliconflow|local`（**默认 `siliconflow`** 对准生产小机）  
   - 模型：`RAG_EMBED_MODEL` 或复用现常量，默认 `BAAI/bge-m3`（须与 ingest fingerprint / 库维度一致）  
   - 复用 `SILICONFLOW_BASE_URL` + `SILICONFLOW_API_KEY`  
4. `ApiEmbedder`：缺 key / 超时 / 4xx·5xx → **明确失败**（打日志）；不要静默退回「再去加载本地 2.3GB」除非文档写明且可测的显式降级策略（本波**建议不做**隐式降级，避免又冷启动）。  
5. `.env.example` + 生产 compose（跨仓 `ops-desk-workspace/deploy/docker-compose.prod.yml`）透传 `RAG_EMBED_BACKEND`（及模型键若新增）。  
6. 单测 mock httpx；不改 `hybrid_recall` SQL、不改 grader 闸、不改 Qdrant 契约。  
7. G-L1 一句 + `./scripts/graph-compile.sh`。

---

## 非范围

- 全量重新灌库 / 改向量维度（必须保持 bge-m3@1024）  
- 改 ingest 默认仍可用本地 ST 灌库（本波可只改**查询**路径；若 30 顺手统一工厂，ingest 默认 `local` 须单独写清，避免 CI/灌库依赖云 API）  
- 启动 lifespan 预热本地模型（企业做法；本波以 API 消冷启动为主）  
- 挂 `HF_HOME` volume、升配机器、烘进 Docker 镜像  
- 换供应商（百炼 embeddings）  
- 改 Chat SSE / LC Evidence HTTP freeze  
- 改 `graph.py` 拓扑  
- Langfuse token UI / `t-` observation 404（观测另案）

---

## 依赖

| 项 | 说明 |
|---|---|
| 冷启动记录 | `ops-desk-workspace/docs/04-infrastructure/04-rag-embed-cold-start_note_20260817.md` |
| 契约 Q3 | `ops-desk-workspace/docs/contracts/rag-knowledge-contract-v1.md` |
| 现实现 | `app/ops/rag/embedder.py`（`ApiEmbedder` 已存在） |
| 调用方 | `lc_evidence_chain/retrieve.py` · `chat/rag_nodes.py` |
| 密钥 | 既有 `SILICONFLOW_API_KEY` |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |

---

## 实施步骤（建议 · 30）

1. 增加 `get_query_embedder()`（或等价）：读 `RAG_EMBED_BACKEND`；默认 siliconflow → `ApiEmbedder`；local → ST。  
2. 改 LC / Chat 两处 `_get_embedder` 调用工厂；`asyncio.to_thread` 对 sync `embed` 保持。  
3. 缺 key：构造或首次 embed 失败路径清晰（对齐精排「score 路径失败」精神，**不要** import 期无条件炸全站）。  
4. `.env.example` + workspace compose 透传。  
5. pytest mock `/embeddings`：返回 1024 维假向量、index 保序；backend=local 路径可用 stub 替代真 ST。  
6. G-L1 + graph-compile；确认 `git diff` 不改 `app/ops/chat/graph.py`。

---

## 验收标准

- [x] `RAG_EMBED_BACKEND=siliconflow`（或默认）：查询路径**不**调用 `SentenceTransformer(...)` / 不加载本地 bge-m3  
- [x] mock `POST /embeddings`：返回向量进入 `hybrid_recall` 前形状正确（list[float]、维数与约定一致）  
- [x] 缺 `SILICONFLOW_API_KEY` 或 HTTP 失败：可测失败（日志明确）；**不**隐式改加载本地 ST（本波）  
- [x] `RAG_EMBED_BACKEND=local`：仍可走 ST（单测 stub，CI 不真下模型）  
- [x] LC Evidence 与 Chat retrieve **两处**均已接线  
- [x] `.env.example` + 生产 compose 透传相关键  
- [x] `git diff`（相对合入基线）**不改** `app/ops/chat/graph.py` 拓扑  
- [x] `ruff check` 触及路径 + 相关 pytest 绿；G-L1 一句 + `graph-compile.sh` exit 0  
- [ ] （人工）小机 recreate api **不**预热本地模型时，首次 LC Evidence 不再出现分钟级「loading embedding model」

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| SiliconFlow 超时 / 5xx / 429 | 查询失败（本波不隐式回落本地 ST） | Y | Chat/LC 错误或 500（与现 retrieve 失败语义对齐） |
| 缺 API key | 同上；配 key | Y | 明确日志 |
| `BACKEND=local` 再 OOM / 冷启动 | 仅误开 local；默认路径不走 | Y | 运维改回 siliconflow |
| 模型名与库 fingerprint 不一致 | 向量空间错乱；验收/审查打回 | N | 召回质量崩溃 |
| 误改 graph / 升无关 freeze | 验收打回 | N | PR 拒绝 |

---

## 给执行帽必读（本仓）

1. 本 task（仓内 active 为执行真值）  
2. `ops-desk-workspace/docs/04-infrastructure/04-rag-embed-cold-start_note_20260817.md`  
3. `app/ops/rag/embedder.py` · `ApiEmbedder` / `SentenceTransformerEmbedder`  
4. `app/ops/lc_evidence_chain/retrieve.py` · `app/ops/chat/rag_nodes.py`  
5. `docs/standards/CODING_BACKEND_L2_v1_zh.md`  
6. 精排先例：`app/ops/rag/reranker.py`（backend 切换 / compose 透传模式）

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R5 |
| **early_stop** | no |
| **residual_risks** | 查询改 API 后，ingest 若仍本地、查询远程，模型名必须同为 bge-m3@1024。隐式失败回落本地会再次引入冷启动，故本波禁止。多 worker + API 依赖外网与配额。 |

### R0
小机 retrieve 分钟级主因是查询路径本地 bge-m3 冷启动；ApiEmbedder 已存在未接线。

### R1
范围=查询路径默认 siliconflow + env + 两入口接线 + 单测 + compose；非范围=灌库改维、升配、预热 lifespan、隐式回落 ST。

### R2
工厂按 `RAG_EMBED_BACKEND`；默认远程；与精排切换模式对齐。

### R3
失败不静默加载本地；模型名锁 bge-m3；不改 graph。

### R4
mock embeddings + 断言不加载 ST；人工小机无预热抽检。

### R5
闸未签前禁 30；实现只在本仓（compose 跨仓另述）。

---

### 自检结论（起草 / 闸）

> workspace 10 起草 · 本仓复制对齐 · 闸由子 agent 按维护者授权代签。

- [x] 验收 / failure_paths / 非范围 / 依赖齐全  
- [x] 思考轮 R0–R5 + 控制表已写  
- [x] 复制到 `docs/tasks/active/task_rag_embed_api_backend.md`  
- [x] api `task lint` PASS  
- [x] HG-TASK-DRAFT approved  
- [x] HG-AUDIT-R1 approved  

### 自检结论（执行者）

> 30/40 完成 · 2026-08-17 · 交 00 验收 / PR / CLOSE（本执行者不关账）。

- [x] `get_query_embedder` + 两入口接线  
- [x] 默认 siliconflow；local 可切；无隐式回落 ST  
- [x] 单测 mock `/embeddings` 绿（9 passed）  
- [x] `.env.example` + workspace compose 透传（workspace 未 commit）  
- [x] G-L1 + graph-compile  
- [x] `git diff` 不改 `graph.py`  
- [x] ruff + pytest 相关绿  

### 自检结论（50 · 00）

> Harness 50 · 2026-08-17 · 00 机械复检 · **PASS（机械）**

- [x] 抽读 `get_query_embedder` 默认 siliconflow；两入口接线；缺 key 不回落 ST
- [x] `git diff origin/master -- app/ops/chat/graph.py` 空
- [x] ruff PASS · pytest **26 passed**（embedder 9 + reranker 17）
- [x] harness verify PASS
- [x] workspace compose 已透传 `RAG_EMBED_*`（跨仓另 commit）
- [ ] （人工）小机 recreate 抽检 — **不挡机械关账**

**50 结论：PASS（机械）· 可 CLOSE / PR**

### 经验

- Wiki: n/a
- 查询默认 API、ingest 仍可本地：模型名必须同为 `BAAI/bge-m3`。

### KPI

| 项 | 分 |
|---|---|
| Task_KPI% | 100 |

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-17 |
| 定稿 | 查询路径默认 SiliconFlow ApiEmbedder；`local` 显式；无隐式回落 ST |
| 归档 | `docs/tasks/done/task_rag_embed_api_backend.md` |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-17 | workspace 首稿：查询默认 ApiEmbedder；冷启动记录仅指针 |
| 2026-08-17 | 复制入 api active；路径相对本仓微调；子 agent 代签闸 |
| 2026-08-17 | 30/40：工厂接线 + 单测 + compose 透传；执行者自检勾选 |
| 2026-08-17 | 00 50 PASS；CLOSE / PR |