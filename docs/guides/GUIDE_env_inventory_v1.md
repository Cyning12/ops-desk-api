# GUIDE · 全仓 env 清单（V1-E D4 盘点）

> **任务**：`host-v1-splittability-hardening` D4 · 2026-09-24
> **口径**：`.env.example` ∪ `app/` getenv/ENV_/常量字符串 ∪ 动态 `OPS_LLM_TIER_*` ∪ `OPS_LLM_STRATEGY_PACK`
> **优先级**：env > 策略包 > 代码默认；缺省不设策略包 = 现状逐字节
> **非法回退**：各模块 `_env_int`/strip —— 空/非法回默认（不炸请求）

## 清单（84 键 · 按归属面）

| 名称 | 归属面 | .env.example 默认 | 备注 |
|------|--------|-------------------|------|
| `LG_RAG_DELEGATION_TOKEN_MODE` | capability | `—（代码/动态）` | V1-A~C |
| `LG_RAG_DELEGATION_TOKEN_SECRET` | capability | `—（代码/动态）` | V1-A~C |
| `LG_RAG_DELEGATION_TOKEN_TTL_SECONDS` | capability | `—（代码/动态）` | V1-A~C |
| `OPS_CAPABILITY_PERSISTENCE` | capability | `—（代码/动态）` |  |
| `OPS_CAPABILITY_REVERSIBILITY_MODE` | capability | `—（代码/动态）` | V1-A~C |
| `OPS_CHAT_WS_ENABLED` | chat | `true` |  |
| `OPS_HITL_CALLBACK_SECRET` | hitl | `—（代码/动态）` |  |
| `OPS_HITL_PERSISTENCE` | hitl | `—（代码/动态）` |  |
| `CORS_ORIGINS` | infra | `http://localhost:5173,http://127.0.0.1:5173` |  |
| `DATABASE_URL` | infra | `postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk` |  |
| `DSH_CODING_KIT_VERSION` | infra | `—（代码/动态）` |  |
| `GITHUB_TOKEN` | infra | `—（代码/动态）` |  |
| `OPS_ADMIN_SYNC_TOKEN` | infra | `` |  |
| `OPS_DESK_AUTH_MODE` | infra | `db` |  |
| `OPS_DESK_SECRET` | infra | `change-me-in-production` |  |
| `OPS_GRAPH_JSON_PATH` | infra | `—（代码/动态）` |  |
| `OPS_SCAN_INDEX_PATH` | infra | `—（代码/动态）` |  |
| `OPS_SYNC_REPO` | infra | `—（代码/动态）` |  |
| `LG_RAG_HTTP_CHECKPOINTER` | lg_rag | `postgres（P0' T3 默认翻开）` | unset=postgres · 显式空值/off=内存 saver 回退口 |
| `LG_RAG_MAX_RETRIES` | lg_rag | `—（代码/动态）` |  |
| `LG_RAG_REACT_SATISFACTION` | lg_rag | `—（代码/动态）` |  |
| `LG_RAG_ROUTER_MODEL` | lg_rag | `—（代码/动态）` |  |
| `LG_RAG_ROUTER_PROVIDER` | lg_rag | `—（代码/动态）` |  |
| `LG_RAG_VISIBILITY_SCENARIO_MODE` | lg_rag | `—（代码/动态）` | V1-A~C · **已废弃 deprecated（2026-10-20 · scenario 阶段摘除 · 生产零消费 · scenario.py 本体 dormant 保留）** |
| `LG_RAG_WRITE_REPLAY_GUARD_ENABLED` | lg_rag | `—（代码/动态）` | delegation-naming-boundary（2026-10-20）· write 孪生重放护栏独立开关（真门控仅 nodes.py 两处 · 与 delegation 解耦）· 布尔默认 true=开 · 非法值回退开（fail-closed 反向 + warning · 解析承 SESSION_SUMMARY_ENABLED 先例方向相反）· FP-2：delegation off 下护栏由从不生效变默认生效 |
| `SESSION_COOKIE_SECURE` | lg_rag | `false` |  |
| `SESSION_SUMMARY_ENABLED` | lg_rag | `—（代码/动态）` |  |
| `BAILIAN_API_KEY` | llm | `sk-xxxxxxxx` |  |
| `BAILIAN_BASE_URL` | llm | `https://dashscope.aliyuncs.com/compatible-mode/v1` |  |
| `BAILIAN_MODEL` | llm | `qwen-plus` |  |
| `OPS_LLM_BUDGET_ENFORCE_TASKS` | llm | `—（代码/动态）` | V1-A~C |
| `OPS_LLM_BUDGET_MODE` | llm | `—（代码/动态）` | V1-A~C |
| `OPS_LLM_BUDGET_SESSION_TOKENS` | llm | `—（代码/动态）` | V1-A~C |
| `OPS_LLM_BUDGET_TASK_TOKENS` | llm | `—（代码/动态）` | V1-A~C |
| `OPS_LLM_INFER_CACHE_ENABLED` | llm | `—（代码/动态）` | V1-A~C |
| `OPS_LLM_INFER_CACHE_MAX_ENTRIES` | llm | `—（代码/动态）` | V1-A~C |
| `OPS_LLM_INFER_CACHE_TTL_SECONDS` | llm | `—（代码/动态）` | V1-A~C |
| `OPS_LLM_PROVIDER` | llm | `siliconflow` |  |
| `OPS_LLM_STRATEGY_PACK` | llm | `—（代码/动态）` | V1-E 策略包路径 · 未设=不加载 |
| `OPS_LLM_TIER_ANSWER_MODEL` | llm | `—（代码/动态）` | 动态档覆盖 |
| `OPS_LLM_TIER_EXTRACT_MODEL` | llm | `—（代码/动态）` | 动态档覆盖 |
| `OPS_LLM_TIER_GRADER_MODEL` | llm | `—（代码/动态）` | 动态档覆盖 |
| `OPS_LLM_TIER_STRUCTURED_MODEL` | llm | `—（代码/动态）` | 动态档覆盖 |
| `OPS_LLM_TIER_SUMMARY_MODEL` | llm | `—（代码/动态）` | 动态档覆盖 |
| `RAG_GRADER_MODEL` | llm | `Qwen/Qwen3.6-27B` |  |
| `SILICONFLOW_API_KEY` | llm | `sk-xxxxxxxx` |  |
| `SILICONFLOW_BASE_URL` | llm | `https://api.siliconflow.cn/v1` |  |
| `SILICONFLOW_MODELS` | llm | `—（代码/动态）` |  |
| `MEMORY_EPISODES_ENABLED` | memory | `—（代码/动态）` | V1-D |
| `MEMORY_EPISODES_MAX_ITEMS` | memory | `—（代码/动态）` | V1-D |
| `MEMORY_EPISODES_WRITE_ENABLED` | memory | `—（代码/动态）` | V1-D |
| `MEMORY_FACTS_ENABLED` | memory | `—（代码/动态）` |  |
| `MEMORY_FACTS_EXTRACT_ENABLED` | memory | `—（代码/动态）` |  |
| `MEMORY_FACTS_MAX_ITEMS` | memory | `—（代码/动态）` |  |
| `MEMORY_FACTS_MAX_VALUE_CHARS` | memory | `—（代码/动态）` |  |
| `MEMORY_FACTS_VECTOR_RECALL_ENABLED` | memory | `—（代码/动态）` |  |
| `LANGFUSE_ENV` | observability | `prod` |  |
| `LANGFUSE_TRACING_ENVIRONMENT` | observability | `—（代码/动态）` |  |
| `HF_ENDPOINT` | rag | `https://hf-mirror.com` |  |
| `HF_HUB_OFFLINE` | rag | `0` |  |
| `QDRANT_API_KEY` | rag | `—（代码/动态）` |  |
| `QDRANT_COLLECTION` | rag | `ops_knowledge` |  |
| `QDRANT_HNSW_EF` | rag | `—（代码/动态）` |  |
| `QDRANT_URL` | rag | `http://127.0.0.1:6333` |  |
| `RAG_EMBED_BACKEND` | rag | `siliconflow` |  |
| `RAG_EMBED_MODEL` | rag | `—（代码/动态）` |  |
| `RAG_FTS_CONFIG` | rag | `simple` |  |
| `RAG_GRADER_PROMPT` | rag | `v1` |  |
| `RAG_GRADER_PROVIDER` | rag | `siliconflow` |  |
| `RAG_KW_EXPAND` | rag | `false` |  |
| `RAG_LC_ANSWER_MODEL` | rag | `—（代码/动态）` |  |
| `RAG_LC_ANSWER_PROMPT` | rag | `—（代码/动态）` |  |
| `RAG_LC_ANSWER_PROVIDER` | rag | `—（代码/动态）` |  |
| `RAG_QDRANT_SHADOW_WRITE` | rag | `true` |  |
| `RAG_RERANK_BACKEND` | rag | `siliconflow` |  |
| `RAG_RERANK_ENABLED` | rag | `true` |  |
| `RAG_RERANK_MIN_SCORE` | rag | `0.4` |  |
| `RAG_RERANK_MODEL` | rag | `—（代码/动态）` |  |
| `RAG_RERANK_SCORE_RATIO` | rag | `0.75` |  |
| `RAG_SECOND_PATH` | rag | `—（代码/动态）` |  |
| `RAG_SPARSE_FP16` | rag | `—（代码/动态）` |  |
| `RAG_SPARSE_MODEL` | rag | `—（代码/动态）` |  |
| `RAG_VECTOR_BACKEND` | rag | `qdrant` |  |
| `SECURITY_INPUT_ISOLATION_ENABLED` | security | `—（代码/动态）` |  |

## 扫描基线留痕

- 日期：2026-09-24
- 计数：union **84**
- 策略包：`app/llm/packs/llm_tiers.v0.yaml`（schema_version=`0`）

## 修订

| 日期 | 说明 |
|------|------|
| 2026-09-24 | V1-E D4 初版盘点落盘 |
| 2026-10-20 | delegation-naming-boundary：lg_rag 段新增 `LG_RAG_WRITE_REPLAY_GUARD_ENABLED`（84 键） |
