# 规划：前端可用的 RAG API（不改码草案）

> **日期**：2026-08-14  
> **状态**：planning only · **未开 task · 禁止本文件驱动 30 改码**  
> **2026-08-31 注（T6）**：`POST /api/ops/chat/stream` 已 **410 下线**；本文凡引导走 chat/stream 的表述以 `POST /api/ops/lg-rag/stream` 为准（见 `docs/spec/agent-infra/05` §10.5）  
> **背景**：Qdrant 切流已完成；前端 chat 尚未联调 RAG 体验  
> **问题**：当前是否已有「给前端用的 RAG API」？若要编写，现有能力与新增步骤是什么？

---

## 1. 结论（先看这）

| 问法 | 答案 |
|---|---|
| 有没有**独立的** RAG HTTP API（如 `POST /rag/search`）？ | **没有** |
| 前端能不能已经「用到 RAG」？ | **能**：原经 Chat `POST /api/ops/chat/stream`（已 410 · T6）；现经 `POST /api/ops/lg-rag/stream`（retrieve/grade 事件同流） |
| 前端现在接好了吗？ | **传输层已接 SSE**；**引用卡片 / RAG 态 UI 多半未专门消费** `tool_result`（retrieve/grade） |
| 下一步最小路径 | **优先 A：消费现有 SSE 事件**；需要调试台/纯检索 UI 再开 **B：独立检索 API** |

---

## 2. 现状：已有 vs 没有

### 2.1 已有（后端 · 生产同路径）

```text
用户消息
  → POST /api/ops/chat/stream（cookie 鉴权）⚠️ 已 410 下线（T6）→ 现走 POST /api/ops/lg-rag/stream
  → LangGraph
       intent
         ├─ issue_qa → load_context（精确 issue，不走 hybrid RAG）
         └─ general / overview
              → retrieve（hybrid：Qdrant|pgvector dense + PG FTS/sparse）
              →（可选）CE rerank
              → grade（LLM 枚举闸）
              → answer | refuse
  → SSE 事件流
```

已对前端暴露、且与 RAG 相关的**事件形态**（嵌在 chat 里，不是独立 REST）：

| SSE `event_type` | `agent_role` | payload 要点 | 前端用途建议 |
|---|---|---|---|
| `tool_result` | `retrieve` | `tool=retrieve` · `hits=[anchor…]` · `rerank_enabled` | 「正在检索 / 命中锚点」 |
| `tool_result` | `grade` | `sources[]`（type/id/title/snippet/url/relevance）· gate 信息 | **引用卡片** |
| `answer` / `thinking` / `done` / `error` | — | 既有 chat 契约 | 主对话区 |

实现真值：`app/ops/chat/rag_nodes.py` · `app/ops/chat/graph.py` · `app/ops/rag/*`  
向量后端：`RAG_VECTOR_BACKEND`（生产已 `qdrant`）。

鉴权：与 chat 相同（session cookie）。  
前端入口（2026-08-31 前）：`ops-desk-web` · `useOpsChatSse.ts` → `POST /api/ops/chat/stream`（均已随 T2/T6 切换/下线：web 走 lg-rag SSE，chat stream 410）。

### 2.2 没有（若「RAG API」指独立接口）

| 能力 | 现状 |
|---|---|
| `POST /api/ops/rag/search`（只检索、不答） | 无 |
| `GET /api/ops/rag/chunks/{id}` | 无（hydrate 仅内部） |
| `GET /api/ops/rag/health`（backend/qdrant/fallback 计数） | 无（仅通用 `/health`） |
| 同步 JSON 版「检索+引用」非 SSE | 无 |
| 公开匿名 RAG | 无（也不建议） |
| Ingest / 管理面 API | 无（CLI `rag_ingest.py`） |

内部可调用、但**未挂路由**：`hybrid_recall` / `hybrid_recall_detail` / rerank / grader。

---

## 3. 目标分层（选一条主路径）

### 路线 A · 前端接好「Chat 内 RAG」（推荐先做）

**目标**：用户在网页聊天时能看到检索过程与引用，无需新后端路由。

**适合**：产品问答体验、验证生产 Qdrant 切流。

### 路线 B · 独立检索 API（调试 / 知识浏览）

**目标**：前端或内部工具可 `query → hits/sources`，不跑完整答问 LLM（或可选开关 grade）。

**适合**：检索调试台、金样可视化、运营抽检。

### 路线 C · 观测 / 运维 API（薄）

**目标**：`backend=qdrant|pgvector`、fallback 计数、collection 点数、DLQ 积压。

**适合**：运维面板；可与 A/B 并行小做。

---

## 4. 路线 A：现有步骤 + 需新增（规划）

### 4.1 已有（可直接用）

1. 后端 RAG 链已在 `general/overview` 意图跑通  
2. SSE 已发 `tool_result`（retrieve / grade + `sources`）  
3. Web 已能建连、解析 SSE 通用帧  
4. 生产 Flag 已切 qdrant（配置侧）

### 4.2 需新增 / 核对（前端为主）

| # | 步骤 | 仓 | 说明 |
|---|---|---|---|
| A1 | 核对 SSE 契约文档与实发 payload | api/web | 对照 `rag_nodes` 与 ios/web 契约文，列字段表 |
| A2 | UI：引用卡片列表 | web | 消费 `agent_role=grade` 的 `sources` |
| A3 | UI：检索态 | web | 消费 `retrieve` 的 `hits` / loading |
| A4 | UI：拒答 | web | gate refuse / `REFUSAL_TEXT` 展示 |
| A5 | 意图分流说明 | 产品 | `issue_qa` 不走 hybrid；避免「为何无引用」误解 |
| A6 | 生产联调 | 跨仓 | 登录 → 问知识题 → 日志无 fallback + 前端有 sources |
| A7 |（可选）契约单测 | web | 对 mock SSE 帧断言卡片渲染 |

### 4.3 后端可能的小补（非必须，开 task 再做）

- 成功路径打一条 INFO：`rag_backend=qdrant hits=N`（便于无前端时验收）  
- `sources` 事件是否与现网 web/iOS 字段一字对齐（若契约有漂移则改一边）

**不需要**为了 A 先做独立 `/rag/search`。

---

## 5. 路线 B：独立 RAG 检索 API（规划）

### 5.1 建议契约（草案 · 待 task/SPEC）

    POST /api/ops/rag/search
    Auth: 与 chat 相同（session）
    Body:
      query: string
      top_n?: int          # 默认 5
      rerank?: bool        # 默认跟 env RAG_RERANK_ENABLED
      include_grades?: bool # 默认 false；true 则多一次 grader 调用
    Response 200:
      backend: "qdrant" | "pgvector"
      fallback: bool
      hits: [{ id, anchor, source_type, source_id, chunk_index, rrf_score?, rerank_score? }]
      sources?: [引用卡片 · 与 grade 同形]   # 仅 include_grades
      took_ms: { embed, recall, rerank?, grade? }

可选附属：

    GET /api/ops/rag/health
      → { vector_backend, qdrant_url?, qdrant_points?, fallback_total, shadow_write }

### 5.2 现有可复用

| 模块 | 复用方式 |
|---|---|
| `SentenceTransformerEmbedder` | 与 chat 同进程单例策略 |
| `hybrid_recall` / detail | 召回核心 |
| `rerank_chunks` | 可选精排 |
| `grade_chunks` + `_to_source` | 可选评级与卡片 |
| `vector_backend` / fallback | 响应里回传，便于前端展示 |

### 5.3 需新增步骤（后端）

| # | 步骤 | 说明 |
|---|---|---|
| B1 | SPEC / task（含鉴权、限流、是否暴露分数） | 分数默认不对终端用户展示（契约 4c） |
| B2 | Router `app/ops/rag/router.py` + 挂到 `ops` | 与 chat 分离 |
| B3 | Pydantic 请求/响应模型 | 与 SSE `sources` 字段对齐，避免两套卡片 |
| B4 | 服务函数：编排 embed→recall→rerank→(grade) | **禁止**复制一份 SQL；只调现有函数 |
| B5 | 超时 / 并发 / 速率限制 | embed+CE 重；防刷 |
| B6 | 图谱 + 契约文档 + 单测 | G-L1 路由表；pytest mock embed |
| B7 | Web：调试页或 Settings 抽检 | 可选 |
| B8 | 生产 env 文档 | 与 cutover 交叉引用 |

### 5.4 明确不做（B 首版）

- 匿名公开检索  
- 写路径 / ingest API  
- 替代 `chat/stream`（答问仍走 SSE）  
- 把 Qdrant HTTP 直暴给浏览器  

---

## 6. 路线 C：观测 API（薄规划）

| # | 步骤 |
|---|---|
| C1 | `GET /api/ops/rag/health`（或并入 admin） |
| C2 | 读 `RAG_VECTOR_BACKEND`、fallback 计数、可选 Qdrant `points_count`、DLQ `count` |
| C3 | 仅 maintainer / admin 角色（若已有角色模型） |

可与 A 并行；工作量小于 B。

---

## 7. 推荐实施顺序

```text
1) 开短 task：前端消费 chat SSE 的 retrieve/grade（路线 A）
2) 生产联调：证明「前端可用的 RAG」= 聊天+引用（不新开检索路由）
3) 若需要调试台 / 无 LLM 抽检 → 再开 SPEC+task 做路线 B
4) 运维需要面板 → 路线 C
```

**判断「前端可用」的验收：**

- 登录生产/本机 web  
- 问会走 `general` 的知识题（非纯 issue 号精确问答）  
- 界面出现引用卡片；api 日志有 `POST /lg-rag/stream`（原 `POST /chat/stream` 已 410 · T6）且无持续 `qdrant fallback`  

---

## 8. 风险与依赖

| 风险 | 说明 |
|---|---|
| 意图分流 | `issue_qa` 无 hybrid sources，产品文案需说清 |
| Embed 冷启动 | 容器内首次检索加载 bge-m3，延迟大；应用预热或提示 |
| Grader 额度 | `include_grades=true` 或 chat grade 耗 Bailian/SiliconFlow |
| 生产语料来源 | 当前 8574 来自本机拷贝；日更断尾未解时，前端「知识」会陈旧 |
| 双契约漂移 | SSE `sources` 与未来 REST 必须单源字段表 |

---

## 9. 开 task 时建议填写的范围句

**若选 A：**

> 前端消费 `POST /api/ops/lg-rag/stream`（原 `POST /api/ops/chat/stream` 已 410 · T6）已有 RAG `tool_result`（retrieve/grade/sources），补齐引用与检索态 UI；不新增 RAG REST。

**若选 B：**

> 新增 `POST /api/ops/rag/search`（及可选 health），复用 `hybrid_recall`/rerank/grade；鉴权同 chat；与 SSE sources 字段对齐；不做 ingest、不替代 stream。

---

## 10. 相关真值索引

| 文档 / 代码 | 用途 |
|---|---|
| `docs/deployment/qdrant-migration-narrative.md` | 迁移全流程 |
| `docs/deployment/qdrant-cutover.md` | 生产切流 |
| `app/ops/chat/rag_nodes.py` | SSE 侧 RAG 事件 |
| `app/ops/rag/retrieve.py` | 召回核心 |
| `ops-desk-web/src/composables/useOpsChatSse.ts` | 前端 SSE |
| 契约 `rag-knowledge-contract-v1.md`（workspace） | 引用卡片 / 闸语义 |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-14 | 首版规划：澄清「无独立 RAG API、有 Chat 内嵌 RAG」；A/B/C 三路线 |
