# invoke · 10-task · D1 chat_ws 根因定位（四层）

> hat=10 · 2026-09-22 · 读码 + 探针实证

## L1 断言过期（主根因 · 实证坐实）

- `tests/test_chat_ws.py:160` 期望 `[run.start, thinking, thinking, answer, answer, done]`，写于 2026-07-18（`ecdbc9e`）。
- 2026-08-10 `b04715f`（R-3 检索链接线）把 general/overview 改线 `retrieve→grade→gate`（`app/ops/chat/graph.py:45-46`），retrieve 节点必发 `tool_result`（`rag_nodes.py:107`）。
- **交叉验证**：手工补 `ops_knowledge_chunks` 表 + 净化代理 env 后重跑 → 实得 index 2 = `tool_result` ≠ `thinking`。环境层全修后断言仍不匹配 → 断言过期为不可省略的主根因。验证毕已 DROP 表恢复红基线。

## L2 宿主代理 env 污染

- 宿主 `no_proxy=localhost,127.0.0.1,::1,[::1]` 含裸 IPv6 `::1` → httpx(trust_env=True) 建 Client 时 `URLPattern('all://::1')` 抛 `InvalidURL: Invalid port: ':1]'`（栈：`httpx/_client.py:697` `_mounts` dictcomp）。
- 触发点：retrieve 节点 `app/ops/rag/embedder.py:92` `httpx.post`。
- 实证：宿主 env 下 `httpx.Client()` 即炸；`env -u http_proxy -u https_proxy -u all_proxy -u no_proxy -u NO_PROXY` 后恢复。CI runner 无此 env。

## L3 测试库 schema 漂移

- `ops_knowledge_chunks` 由 `alembic/versions/20260808_rag_chunks.py:35` 裸 SQL 建，**无 ORM 模型**（grep app/db 零命中）→ conftest `create_all` 不含 → retrieve SQL `FROM ops_knowledge_chunks` 炸 `UndefinedTableError`（qdrant 补水与 pg fallback 两路同炸）。
- 实证：`pg_tables` 查询 26 表无 knowledge；tenant-readonly-predicate 40（2026-09-18）已首记 `relation "o..."` 缺失。

## L4 CI 假绿

- `.github/workflows/pytest.yml:26` `DATABASE_URL` 指 localhost:5432 但 workflow **无 postgres service** → conftest `DB_AVAILABLE=False` → chat_ws 全部 skip。「CI 绿」= skip 绿，三缺陷从未在 CI 真跑。

## 噪音定性

`_portal_engine`（test_chat_ws.py:64-75）跨 loop dispose 的 RuntimeError 是失败后的 teardown  fallout，非根因；L1–L3 修复后须顺带确认消失。
