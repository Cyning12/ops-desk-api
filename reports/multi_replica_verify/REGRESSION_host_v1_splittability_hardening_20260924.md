# multi-replica 回归报告 · V1-E D1（2026-09-24）

| 字段 | 值 |
|------|-----|
| task | host-v1-splittability-hardening |
| git_sha_pre | `4e6d28d4644343910e46bc2d9b05f3ec8e568706`（交付 tip 见 30 invoke） |
| recorded_at | 2026-09-24T03:15+00（约） |
| topology | 双进程 uvicorn · 共享 PG（既有 `tests/dualproc_server.py` · **未重写基建**） |
| gateway_form | 降级 / 直连双进程（承 #165 · **未**声称外部 Java 网关验证通过） |
| result | **BLOCKED-ENV**：9 ERROR · `ops_sessions.tenant_id` NOT NULL（fixture 未写列） |
| evidence | `asyncpg.exceptions.NotNullViolationError` · FINDINGS #1 |
| boundary_guide | `GUIDE_process_local_state_boundaries_v1.md` 已补扫条目 9–11（delegation nonce / llm budget / infer_cache） |
| note | 基建与用例逻辑未改编；失败属阶段 T 后 schema 与 fixture 漂移 · D5 另开 |

## 命令

```
pytest tests/test_multi_replica_dualproc.py -q --tb=short
```
