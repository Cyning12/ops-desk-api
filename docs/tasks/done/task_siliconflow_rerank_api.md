# Task：SiliconFlow API 精排（替换本地 CrossEncoder）

> **状态**：completed（维护者本地验收通过 · 2026-08-17）  
> **类型**：feature / RAG 排序层  
> **上游**：`docs/spec/SPEC-rag-reranker-p0_v1.md`（signed · 过滤策略方案 B）· 生产 2C4G 本地 CE OOM/meta tensor  
> **分支**：`task/siliconflow-rerank-api`  
> **编排**：闸齐 → 30+40 → 维护者验收 → CLOSE / PR

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `siliconflow-rerank-api` |
| **git_branch** | `task/siliconflow-rerank-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 单测 mock `POST /rerank`：排序/index 对齐、HTTP 失败回退粗排 top-5、`RAG_RERANK_ENABLED=false` 不发请求；不打真实 SiliconFlow |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 不新增一级模块；仍在既有 `rag` 精排函数内换打分后端 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 不改 coding_wiki；env 句落 `.env.example` 与 reranker 模块注释 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `minimal` |
| **thinking_profile** | `shortest` |
| **experience_capture** | `recommended` |
| **orchestration** | 轻量 · 默认远程精排；本地 CE 可保留为显式后端 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-17 00 代签：维护者指示统筹完成；精排走 SiliconFlow `POST /v1/rerank`，默认模型仍 `BAAI/bge-reranker-v2-m3` |
| HG-AUDIT-R1 | approved | 30 | 2026-08-17 00 代签：20 R1 内容 pass（`docs/harness/reviews/task_siliconflow_rerank_api_audit_R1_20260817.md`）；维护者指示统筹完成 |
| HG-GRAPH-MODULES | approved | 30 | 真值 `docs/_tech_graph/l1/01_modules.md`；不新增一级模块 |

---

## 背景与目标

生产 2C4G 无法同进程驻留 bge-m3 + 本地 `CrossEncoder`（meta tensor / 回退粗排）。嵌入已有 SiliconFlow HTTP 先例（`ApiEmbedder`）。精排改为同一供应商的 **rerank 模型 HTTP**，过滤策略（地板 0.4 / 相对顶分 0.75 / top-5）保持 SPEC 方案 B。

**完成态**：`RAG_RERANK_ENABLED=true` 时默认不加载本地 CE；打分来自 SiliconFlow；失败仍 fail-closed 粗排 top-5；关闭开关行为与现网一致。

---

## 范围

1. `app/ops/rag/reranker.py`：打分后端可切换；**默认 `siliconflow`**（生产目标）。  
2. HTTP：`SILICONFLOW_BASE_URL` + `POST {base}/rerank`，`Authorization: Bearer $SILICONFLOW_API_KEY`。  
3. 请求体：`model`（`RAG_RERANK_MODEL`，默认 `BAAI/bge-reranker-v2-m3`）、`query`、`documents`（与现 `_chunk_text_for_rerank` 同文）、`top_n` 对齐候选数。  
4. 响应：按 `results[].index` + `relevance_score` 填回候选顺序，再走既有地板/相对顶分/截断。  
5. env：`RAG_RERANK_BACKEND=siliconflow|local`（默认 siliconflow）；`local` 仅给有内存的本机。  
6. `.env.example` + 生产 compose 透传 `RAG_RERANK_BACKEND`（若尚未透传）。  
7. 单测 mock httpx；不改 hybrid_recall SQL、不改 grader 闸。

---

## 非范围

- 升配机器 / 挂 HF volume / 再烘本地 CE  
- 改 `RAG_RERANK_MIN_SCORE` / `SCORE_RATIO` 默认值  
- 改 Qdrant / 嵌入模型 / Chat SSE 契约  
- 强制跑全量金样 `reports/r4-R.yaml`（可后续独立评测 task）  
- 换供应商（百炼 rerank）  
- 前端超时 120s 调整

---

## 依赖

| 项 | 说明 |
|---|---|
| SPEC 过滤策略 | `docs/spec/SPEC-rag-reranker-p0_v1.md` 方案 B |
| 现实现 | `app/ops/rag/reranker.py` |
| HTTP 先例 | `app/ops/rag/embedder.py` · `ApiEmbedder` |
| 密钥 | 既有 `SILICONFLOW_API_KEY`（缺 key 且 enabled → 失败回退粗排，打日志） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 文档 | SiliconFlow `POST /v1/rerank` |

---

## 实施步骤（建议 · 30）

1. 抽 `_score_siliconflow`：httpx POST `/rerank`，超时与重试对齐 embedder 量级。  
2. `_default_score_fn`：backend=siliconflow 走 HTTP；`local` 仍 CrossEncoder。  
3. 缺 key / 4xx/5xx / 超时 → 现有 `rerank failed; fallback to coarse top-5`。  
4. 单测：mock 乱序 `results` 仍按 index 对齐；enabled=false 零 HTTP。  
5. example + 生产 compose 透传。

---

## 验收标准

- [x] `RAG_RERANK_ENABLED=false`：不发起 `/rerank`、不加载 CrossEncoder  
- [x] `ENABLED=true` 且 `BACKEND=siliconflow`：不调用 `sentence_transformers.CrossEncoder`  
- [x] mock 响应乱序 index 时，过滤后顺序与分数一致  
- [x] HTTP 失败：回退粗排 top-5，不 500 整条 retrieve  
- [x] 缺 `SILICONFLOW_API_KEY`：回退粗排 + 明确日志  
- [x] `pytest` 覆盖 rerank 相关用例绿；不改 `app/ops/chat/graph.py`

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| SiliconFlow 超时/429/5xx | 回退粗排 top-5；打 exception 日志 | Y | 召回略差，问答仍出 |
| 模型名下架/404 | 同上 | N（改 `RAG_RERANK_MODEL`） | 同上 |
| 缺 API key | 同上 | N（配 key） | 同上 |
| 本地 backend 再 OOM | 仅 `BACKEND=local`；默认路径不走 | Y | 若误开 local，同现网 CE 失败 |

---

## 给执行帽必读

1. 本 task  
2. `docs/spec/SPEC-rag-reranker-p0_v1.md` D2 过滤 env  
3. `app/ops/rag/reranker.py`  
4. `app/ops/rag/embedder.py` · `ApiEmbedder`  
5. SiliconFlow rerank：`POST /v1/rerank` · model `BAAI/bge-reranker-v2-m3`

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R5 |
| **early_stop** | yes |
| **early_stop_reason** | 范围=打分后端换 HTTP；过滤策略与开关语义不变 |
| **residual_risks** | 远程延迟叠加 LC Evidence 120s；须短超时+失败回退 |

### R0
2C4G 不能本地 CE；精排改为 SiliconFlow rerank HTTP，模型名仍 bge-reranker-v2-m3。

### R1
范围=reranker 打分函数 + env + 单测 mock；非范围=金样全量、换供应商、改超时前端。

### R2
默认 `RAG_RERANK_BACKEND=siliconflow`；`local` 显式才加载 CrossEncoder。

### R3
失败回退粗排（与现 CE 失败路径一致）；缺 key 不抛到 HTTP 500。

### R4
pytest mock 绿；生产打开 Flag 后不再出现 CrossEncoder meta tensor。

### R5
闸未签前禁 30。

---

### 自检结论

> 10-task 起草自检 · **未**签发 HG-AUDIT-R1。

- [x] 验收 / failure_paths / 非范围 / 依赖齐全
- [x] 思考轮 R0–R5 + 控制表已写
- [x] 10-task invoke 已落档
- [x] HG-TASK-DRAFT approved（2026-08-17 00 代签 · 维护者统筹完成）
- [x] HG-AUDIT-R1 approved（2026-08-17 00 代签 · 20 R1 pass）
- [x] HG-GRAPH-MODULES approved（不新增一级模块）

---

### 自检结论（执行者）

> 30+40 同上下文 · 2026-08-17 · 维护者本地验收通过 · 本波 CLOSE

| 命令 | cwd | 退出码 | 摘要 |
|---|---|---|---|
| `ruff check app/ops/rag/reranker.py tests/test_rag_reranker.py` | `ops-desk-api` | 0 | All checks passed |
| `.venv/bin/pytest tests/test_rag_reranker.py -q` | `ops-desk-api` | 0 | **17 passed** in 0.07s |
| `git diff -- app/ops/chat/graph.py` | `ops-desk-api` | 0 | 空 |

验收表：6/6 pass（mock httpx；不打真实 SiliconFlow）。方案 B 默认 0.4 / 0.75 / top-5 未改。

已知未测：

- 未跑全量金样 `reports/r4-R.yaml`
- 未在生产容器实测 Flag（切流见「生产切流备忘」）
- 429 短退避路径无单独单测（HTTP 超时 / 5xx / 缺 key 已覆盖）

跨仓：`ops-desk-workspace` 须透传 `RAG_RERANK_BACKEND`（compose / `.env.example`）；与 env-reload 文档同 PR 或另 PR。

---

## 生产切流备忘（维护者本地验收后）

2026-08-17 现网：`RAG_RERANK_ENABLED` 容器值已 `'false'`。关精排后 recreate `api`，前端仍红（3 次里成功 1 次）——**不是精排**，是 HF 缓存丢失后重拉 `bge-m3`：`IncompleteRead(45609510 bytes read, 2225462342 more expected)` = 下载截断（约 2.2 GB），**不是**内存不足。

内存不足的明确句是本地 CE：`Cannot copy out of meta tensor`（bge-m3 已占 RAM 再加载 reranker）。`No active span` 是 Langfuse，可忽略。

API 精排上生产时：

1. 先预热 `SentenceTransformer('BAAI/bge-m3')`，再开 `RAG_RERANK_ENABLED=true` + `RAG_RERANK_BACKEND=siliconflow`
2. `up -d --no-deps api`（见 workspace `docs/04-infrastructure/02-prod-env-reload.md`）
3. 日志**不应**再有 `loading reranker` / `meta tensor`；若再红，先查 `IncompleteRead`（嵌模型下载）而不是 SiliconFlow

---

### KPI

| 项 | 分 |
|---|---|
| Task_KPI% | 100 |

### 经验

- Wiki: n/a
- 2C4G 不要本机 CE + bge-m3 同进程；精排走 SiliconFlow `/rerank`。改 `.env` 必须 `compose up` 才进容器。

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-17 |
| 定稿 | 默认 `RAG_RERANK_BACKEND=siliconflow`；模型仍 `BAAI/bge-reranker-v2-m3`；方案 B 0.4/0.75 |
| 归档 | `docs/tasks/done/task_siliconflow_rerank_api.md` |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-17 | 10-task 首稿：SiliconFlow `/rerank` 替换本地 CE |
| 2026-08-17 | 00 统筹：签 HG-TASK-DRAFT；派 20；人本地验收前不 CLOSE |
| 2026-08-17 | 20 R1 pass → 00 代签 HG-AUDIT-R1 → 30+40 完成；交维护者本地验收 |
| 2026-08-17 | 30+40：默认 SiliconFlow HTTP 精排；pytest 17 passed；未 CLOSE / 未 commit |
| 2026-08-17 | 维护者本地验收通过；CLOSE |
