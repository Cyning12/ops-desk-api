# Task Audit R1：siliconflow-rerank-api

> **hat_id**：20-task-audit  
> **task**：`docs/tasks/active/task_siliconflow_rerank_api.md`  
> **对照 SPEC**：`docs/spec/SPEC-rag-reranker-p0_v1.md`（signed · 过滤策略方案 B）  
> **日期**：2026-08-17  
> **分支**：`task/siliconflow-rerank-api`  
> **审查**：书面审查 · **不**改 `app/` · **不**代签 `HG-AUDIT-R1`  
> **结论**：内容 **`pass`** · 流程闸 **`pending`** · 建议 00 代签 `HG-AUDIT-R1=approved`

---

## 结论摘要

| 维度 | 判定 | 说明 |
| --- | --- | --- |
| **内容可执行** | **pass** | 范围/非范围/验收/failure_paths/test_strategy/必读齐全；现 `reranker.py` 插入点清晰，30 可执行 |
| **流程闸 `HG-AUDIT-R1`** | **pending** | 真值在 task 人工闸表；本审仅建议，**禁止**改表 |
| **思考轮审查** | **pass** | 控制表闭合（R5 / early_stop=yes）；理由与 residual_risks 齐全 |
| **与 SPEC 方案 B** | **无冲突** | 不改 `MIN_SCORE=0.4` / `SCORE_RATIO=0.75`；打分后端换 HTTP 后仍走既有过滤 |
| **是否退回 10-task** | **否** | 无内容阻塞；**禁止**本文件附 30 Prompt |
| **建议代签** | **是** | 内容零阻塞；00 读本结论后可将 `HG-AUDIT-R1` 改为 approved |

---

## 元信息核对

| 字段 | task 值 | 审阅 |
| --- | --- | --- |
| `task_slug` | `siliconflow-rerank-api` | OK |
| `git_branch` | `task/siliconflow-rerank-api` | OK（与当前分支一致） |
| `test_strategy` | `required` | OK |
| `test_strategy_note` | mock `POST /rerank`；不打真实 SiliconFlow | OK；可执行 |
| `code_quality_bar` | `L2_backend` | OK |
| `graph_change_layer` | `none` | OK：仍在既有 `rag` 精排函数内换打分后端 |
| `graph_delta` | `none` | OK |
| `wiki_delta` | `n/a` | OK：env 句落 `.env.example` + 模块注释 |
| `review_hat` | `20` | OK |
| `required_invoke_hats` | `10,30` | OK（不含 20；本审不强制 20 invoke） |
| `thinking_profile` | `shortest` | OK；与 early_stop 一致 |
| `HG-TASK-DRAFT` | approved | OK（2026-08-17 00 代签） |
| `HG-AUDIT-R1` | pending | 正确；blocks 30 |
| `HG-GRAPH-MODULES` | approved | OK；不新增一级模块 |
| 上游 SPEC | signed · 方案 B | OK；见下节「方案 B / D5」 |

---

## 核对表

### 1 · 范围

| task 范围项 | 审阅 | 说明 |
| --- | --- | --- |
| `reranker.py` 打分后端可切换；默认 `siliconflow` | **pass** | 现 `_default_score_fn` 仅走本地 `CrossEncoder`；抽 `_score_siliconflow` + backend 分支即可 |
| HTTP：`SILICONFLOW_BASE_URL` + `POST {base}/rerank` + Bearer | **pass** | 与 `ApiEmbedder` 先例一致（base 默认 `https://api.siliconflow.cn/v1`，路径 `/embeddings` → 本波 `/rerank`） |
| 请求体：`model` / `query` / `documents` / `top_n` 对齐候选数 | **pass** | `documents` 须用现 `_chunk_text_for_rerank`；`top_n=len(documents)` 才能把全量分填回再走方案 B |
| 响应：`results[].index` + `relevance_score` 填回候选顺序 | **pass** | SiliconFlow 文档字段一致；**必须**产出 `len(scores)==len(candidates)` 的 list，否则现实现会 length mismatch → 粗排回退 |
| env `RAG_RERANK_BACKEND=siliconflow\|local`（默认 siliconflow） | **pass** | `local` 显式才加载 CE；与完成态一致 |
| `.env.example` + 生产 compose 透传 `RAG_RERANK_BACKEND` | **pass** | 跨仓路径见 §跨仓；**不阻塞**内容 |
| 单测 mock httpx；不改 hybrid_recall SQL、不改 grader | **pass** | 与验收「不改 `graph.py`」一致（retrieve 入口在 `rag_nodes.py` / LC retrieve，本波也不必改：已按 `rerank_enabled()` 调用 `rerank_chunks`） |

**现实现可执行性（只读）**

- `rerank_chunks` 已把「打分」与「方案 B 过滤」分开：`score_fn` 可注入；异常 → `rerank failed; fallback to coarse top-5`。30 只需换默认 `score_fn`，**不要**重写地板/相对顶分。
- `ENABLED=false` 闸在调用方（`app/ops/chat/rag_nodes.py`、`app/ops/lc_evidence_chain/retrieve.py`）：不进入 `rerank_chunks`，因此不发 `/rerank`、不加载 CE。验收第 1 条与现结构对齐。
- `ApiEmbedder`：sync `httpx.post`、timeout=60、最多 3 次指数退避、缺 key **构造期** `RuntimeError`。精排走 `asyncio.to_thread(rerank_chunks, …)`，sync httpx 可沿用；**缺 key / 超时策略不要原样照抄**（见非阻塞提醒）。

### 2 · 非范围

| 非范围项 | 审阅 |
| --- | --- |
| 升配 / HF volume / 再烘本地 CE | **pass** |
| 改 `RAG_RERANK_MIN_SCORE` / `SCORE_RATIO` 默认值 | **pass**（锁死方案 B） |
| 改 Qdrant / 嵌入 / Chat SSE | **pass** |
| 强制全量金样 `reports/r4-R.yaml` | **pass**（可后续独立评测） |
| 换供应商（百炼 rerank） | **pass** |
| 前端超时 120s 调整 | **pass**（延迟风险改由短超时+回退消化） |

### 3 · 验收标准

| 验收 | 审阅 | 说明 |
| --- | --- | --- |
| `ENABLED=false`：不发起 `/rerank`、不加载 CE | **pass** | 调用方已短路；单测可 assert mock httpx 零调用 + 不 patch 到 `CrossEncoder` |
| `ENABLED=true` 且 `BACKEND=siliconflow`：不调用 `CrossEncoder` | **pass** | 默认路径禁止懒加载 `_load_cross_encoder` |
| mock 乱序 `index`：过滤后顺序与分数一致 | **pass** | 先按 index 填回再 `sorted(..., reverse=True)` + 方案 B |
| HTTP 失败：回退粗排 top-5，不 500 整条 retrieve | **pass** | 现 `except Exception` 已覆盖；30 让 `_score_siliconflow` 抛出即可 |
| 缺 `SILICONFLOW_API_KEY`：回退粗排 + 明确日志 | **pass** | 须在 score 路径触发既有 fallback，**不要**在模块 import 期炸 |
| pytest 相关绿；不改 `graph.py` | **pass** | |

### 4 · failure_paths

| 触发 | task 行为 | 审阅 |
| --- | --- | --- |
| 超时 / 429 / 5xx | 回退粗排 top-5；exception 日志；可重试 | **pass** · 与现 CE 失败路径一致 |
| 模型 404 | 同上；不可靠重试（改 `RAG_RERANK_MODEL`） | **pass** |
| 缺 API key | 同上；配 key | **pass** |
| `BACKEND=local` 再 OOM | 仅误开 local；默认路径不走 | **pass** |

用户可见：「召回略差，问答仍出」——与 SPEC 失败路径「不拖垮 chat」一致。

### 5 · test_strategy

| 项 | 审阅 |
| --- | --- |
| `required` + mock `POST /rerank` | **pass** |
| 覆盖：index 对齐 / HTTP 失败回退 / `ENABLED=false` 零请求 | **pass** |
| 不打真实 SiliconFlow | **pass** |
| 既有 `tests/test_rag_reranker.py` | **pass**：已有 fake `score_fn`、地板/ratio、失败回退；30 **增补** backend/httpx mock，勿拆掉方案 B 单测 |
| 建议 fixture 增删 `RAG_RERANK_BACKEND` / `SILICONFLOW_API_KEY` | 非阻塞（现 autouse 未清这两键） |

### 6 · 给执行帽必读

| # | 路径 | 审阅 |
| --- | --- | --- |
| 1 | 本 task | OK |
| 2 | SPEC D2 过滤 env | OK（0.4 / 0.75） |
| 3 | `app/ops/rag/reranker.py` | OK |
| 4 | `app/ops/rag/embedder.py` · `ApiEmbedder` | OK（HTTP 先例；超时/缺 key **勿照抄**） |
| 5 | SiliconFlow `POST /v1/rerank` · `BAAI/bge-reranker-v2-m3` | OK；响应 `results[].index` + `relevance_score`（0–1） |

缺一不可；无「必读空洞」。

### 7 · 思考轮审查（阶段 C）

| 字段 | 值 | 审阅 |
| --- | --- | --- |
| `actual_last_round` | R5 | OK |
| `early_stop` | yes | OK（`thinking_profile=shortest`） |
| `early_stop_reason` | 范围=打分后端换 HTTP；过滤与开关语义不变 | **闭合** · 与范围/非范围一致 |
| `residual_risks` | 远程延迟叠加 LC Evidence 120s；须短超时+失败回退 | **闭合** · 见非阻塞提醒 |
| R0–R4 | 问题→范围→默认 backend→失败回退→单测 | **闭合** |
| R5 | 闸未签前禁 30 | 流程句，可接受 |

**思考轮结论**：通过；不退回 10-task。

---

## 与 SPEC 方案 B（及 D5 选型）

### 方案 B（本审对照焦点）——无冲突

SPEC D2 / 现 `reranker.py` 模块头：

1. 顶分地板 `RAG_RERANK_MIN_SCORE` 默认 **0.4**：`max(score) < 地板` → 空列表（真空拒答）
2. 相对顶分 `RAG_RERANK_SCORE_RATIO` 默认 **0.75**：保留 `score >= max * ratio`，再截断 top-5

task **非范围**明确「不改上述默认值」；范围第 4 条要求填回分数后 **再走既有** 地板/相对顶分/截断。30 不得把过滤前移到 API `top_n=5` 后跳过方案 B。

生产 compose 已透传 `MIN_SCORE=0.4` / `SCORE_RATIO=0.75`，本波保持。

### SPEC D5 / S5「本波不做远端 API」——有意覆盖，非方案 B 冲突

P0 SPEC 实现优先本地 CE，远端 API 当时因「评测不可复现 / 密钥」弃。本 task 是 **P0 落地后的运维增量**（生产 2C4G 本地 CE OOM / meta tensor），只换打分通道，过滤策略仍方案 B。

不构成内容阻塞，也 **不**要求重开 SPEC 签收。审查留痕：过滤锁死仍以 SPEC D2 为准；实现选型以本 task 为准。

### 生产 `RAG_RERANK_ENABLED`

SPEC 签收曾锁「合入默认 false」。现网 compose 已是 `${RAG_RERANK_ENABLED:-true}`，本 task **不改** ENABLED 默认，只改 ENABLED=true 时的打分后端。无冲突。

---

## 跨仓点：生产 compose 透传 `RAG_RERANK_BACKEND`

**是否阻塞 20 内容 / 是否退回 10**：**否**（路径可执行，task 第 6 条已写「若尚未透传」）。

| 文件 | 现状 | 30 必须 |
| --- | --- | --- |
| `ops-desk-api/.env.example` | 有 `RAG_RERANK_ENABLED` / `MIN_SCORE` / `SCORE_RATIO`；**无** `RAG_RERANK_BACKEND` | **必须**补 `RAG_RERANK_BACKEND=siliconflow`（及一句注释：`local` 仅本机有内存时） |
| `../ops-desk-workspace/deploy/docker-compose.prod.yml` | `api.environment` 已有 ENABLED / MIN_SCORE / SCORE_RATIO；**未**声明 `RAG_RERANK_BACKEND` | **必须**透传，例如 `RAG_RERANK_BACKEND: ${RAG_RERANK_BACKEND:-siliconflow}`。只改服务器 `.env`、不改此 yaml → 容器看不到该键 |
| `../ops-desk-workspace/deploy/.env.example` | 与 compose 对齐的生产示例；同样无 BACKEND | **建议**同步补一行（task 未点名；非阻塞） |

代码默认 `siliconflow` 时，即使忘记透传，生产也会走 HTTP 精排（能消 OOM）。透传的意义是：运维可在 `/opt/ops-desk/.env` 显式钉死或临时切 `local`，与 `.env.example` 注释「容器只吃 compose 声明过的键」一致。

Open Folder 仍是 `ops-desk-api/`：30 改 workspace yaml 是 **跨仓文件**，须另 commit 到 `ops-desk-workspace`（或由 00 跟一次）。**不**把跨仓漏改当成 20 内容 fail。

---

## 内容阻塞清单

**无。** 不退回 10-task。本文件 **不**附 30 Prompt。

---

## 非阻塞提醒（30 时注意 · 不挡签闸）

1. **超时 / 重试**：`ApiEmbedder` 为 timeout=60 × 最多 3 次。精排若照抄，最坏可叠穿 LC Evidence **120s**（思考轮 residual_risks 已写）。建议：**短超时**（个位数～十几秒量级）+ 失败即走既有粗排回退；重试 ≤1 或仅对 429 短退避。task 实施步骤「对齐 embedder 量级」以 **httpx 用法 / Bearer / base_url** 为准，不以 60s×3 为准。
2. **compose 透传**：必须改 `ops-desk-workspace/deploy/docker-compose.prod.yml` 的 `api.environment`（见上表）。本仓 `.env.example` 同步。
3. **默认 backend**：未设 env 时为 `siliconflow`；`local` 才 `_load_cross_encoder`。生产切流后不应再出现 CrossEncoder meta tensor。
4. **缺 key**：不要在模块 import / 单例构造期无条件 `raise`（`ApiEmbedder.__init__` 模式）。在 `_score_siliconflow` 内失败，让 `rerank_chunks` 打 `rerank failed; fallback to coarse top-5`。
5. **分数填回**：API 结果可能乱序且 `top_n` 若小于候选数会导致 length mismatch。请求 `top_n` 对齐候选数；按 `index` 写入与 `texts` 等长的 `list[float]` 再交给现过滤。
6. **分数量纲**：SiliconFlow `relevance_score` 文档为 0–1；方案 B 的 0.4/0.75 原按本地 CE 定稿。本波 **禁止 rescale、禁止改默认阈值**；若松紧有感，留给维护者本地验收 / 后续评测 task。
7. **编排**：task 写明本波不 CLOSE；维护者本地验收后再关账。

---

## 签收 / 关闭（本轮为 20 终轮）

- 20 R1 **内容通过**（`pass`）。
- 流程闸仍 **pending**：30 在 `HG-AUDIT-R1=approved` 之前必须拒开工。
- 下一棒：维护者（或 00 代签）签闸后，再下发 Harness 30。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（内容 `pass` · 无退回 10）
- [ ] 在 task 人工闸表将 `HG-AUDIT-R1` 改为 approved（维护者或 00 代签 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 `TEMPLATE_30_gate_stop.md`）。
