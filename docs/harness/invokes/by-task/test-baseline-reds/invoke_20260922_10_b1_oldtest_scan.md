# invoke · 10-task · B1 旧测影响面实扫

> hat=10 · 2026-09-22 · grep 实扫落盘

| 面 | 命令 | 结果 |
|----|------|------|
| TestClient/websocket | grep `websocket_connect\|TestClient` tests/ | `test_chat_ws.py` · `test_hitl.py` · `test_hitl_resume.py` · `test_hitl_resume_events.py` · `dualproc_server.py`（5 处） |
| 代理 env | grep `OPS_CAPABILITY_HTTP_PROXY\|UrllibHttpTransport` tests/ | `test_capability_http_adapter.py` · `eval/test_capability_redlines.py` |
| run_backfill | grep `run_backfill\|memory_embedding_backfill` tests/ | 仅 `test_memory_embedding_backfill.py`（15 例 · autouse `_clean` 全表清 · opsdesk_test 强制隔离） |
| ops_knowledge_chunks 引用 | grep app/ tests/ | app 侧 retrieve/ingest/qdrant_retriever；tests 零引用（无用例自建该表） |
| 测试库现状 | pg_tables 实查 | 26 表 · 无 knowledge 表 · ORM 无 KnowledgeChunk 模型 |
| SSE 对照 | 读 `test_chat_router.py` | 四例全 410 断言不经图 · 与 WS 用例无共享夹具 |
| 既有先例 | conftest:150-190 | `_create_test_schema` 已有 ALTER 补丁串（BIGINT/embedding 列/kind CHECK）—— 建表补丁同模式追加即可 |

影响结论：conftest 双补丁（env 净化 + 建表）影响面 = 全部 DB 用例（session scope），新增空表对既有断言零影响；env 净化对 integration marker 真连用例须 30 注记。
