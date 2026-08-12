# Invoke：30（含 40）· rag-zhparser-arm-a

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40 自检） |
| task_slug | `rag-zhparser-arm-a` |
| task_paths | `docs/tasks/active/task_rag_zhparser_arm_a.md` |
| related_review_or_none | `docs/harness/reviews/task_rag_zhparser_arm_a_audit_R1_20260812.md` |
| git_branch | `task/rag-zhparser-arm-a` |
| created_utc_or_local | 2026-08-12 |
| notes | 维护者签收后派工；镜像/灌库/r4-A **实跑由维护者**；30 交付产物+单测 |

---

## GATE_VERIFY（首输出摘要）

| human_gate_id | task表status | blocks_30 | 30可开工？ |
|---|---|---|---|
| HG-TASK-DRAFT | approved | N | Y |
| HG-AUDIT-R1 | approved | Y | Y |

reviews R1：是 · `task_rag_zhparser_arm_a_audit_R1_20260812.md` · pre-30 invoke 10：是 · 结论：可开工

---

## 交付范围（30）

1. `Dockerfile.pg-zhparser`（task §1 口径）
2. 影子库初始化 SQL + COPY 灌库辅助脚本（禁全量 pg_dump）
3. `app/ops/rag/retrieve.py`：`RAG_FTS_CONFIG`（默认 `simple`）驱动关键词路 regconfig
4. 单测：配置切换 / 默认不回归 simple
5. 40：跑可本地跑的 pytest；镜像构建与 r4-A **标记待维护者实跑**，回填 `### 自检结论（执行者）`
6. 本 invoke 完工后更新为含验证摘要

禁止：碰主库端口 5432 写操作；改 RRF/语义路；实现 C 臂；直推 master。

---

## 验证摘要（30/40 完工 · 2026-08-12）

### GATE_VERIFY

| 闸 | status | 结论 |
|---|---|---|
| HG-TASK-DRAFT | approved | 可开工 |
| HG-AUDIT-R1 | approved | 可开工 |
| harness verify | PASS | may_start_30 |

### 落地产物

- `Dockerfile.pg-zhparser`
- `experiments/rag_compare/zhparser_arm_a/`（init / schema_no_fts / add_fts_chinese / shadow_copy_chunks.sh / README）
- `app/ops/rag/retrieve.py`：`RAG_FTS_CONFIG`（默认 `simple`）驱动 `plainto_tsquery` / `to_tsquery` regconfig
- `tests/test_rag_fts_config.py`

### 40

| 命令 | 退出码 |
|------|--------|
| `uv run pytest tests/test_rag_fts_config.py tests/test_golden_eval_runner.py -q --tb=short` | 0（16 passed） |
| `uv run ruff check app/ops/rag/retrieve.py` | 0 |

### 未测 / 阻塞

- docker build / 影子库探针 / COPY 灌库 / r4-A：**维护者实跑**
- 本轮未 commit（父 agent / 维护者决定）
