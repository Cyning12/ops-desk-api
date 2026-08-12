# Invoke：50 · rag-zhparser-arm-a（初步验收）

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 50 |
| task_slug | `rag-zhparser-arm-a` |
| task_paths | `docs/tasks/active/task_rag_zhparser_arm_a.md` |
| related_30 | [30-agent](b69d0698-c4f5-4e6f-b6c3-804c49a4c5d4) |
| git_branch | `task/rag-zhparser-arm-a` |
| created_utc_or_local | 2026-08-12 |
| notes | 初验：产物与单测；**不含**维护者实跑镜像/灌库/r4-A |

---

## 50 初验结论：**PASS（附条件）**

条件：镜像构建、影子分词探针、COPY 灌库、`reports/r4-A.yaml` 对比由维护者实跑后再做终验 / 判读。

### 对照验收标准

| 验收项 | 50 判定 | 证据 |
|---|---|---|
| 分词探针 `to_tsvector('chinese', …)` | **deferred** | SQL/README 已备；未实连影子库 |
| r4-A 与 r4-2/r4-D 对比 | **deferred** | runner env 说明已备；未跑评测 |
| 结论回写契约 Q6 | **deferred** | 待有数据后 |
| 未碰主库/生产 | **pass** | 脚本只读 PRIMARY；代码无写主库路径 |
| 30 产物完整度 | **pass** | 见下表 |
| 单测/静态检查 | **pass** | 复跑 16 passed · ruff 0 |

### 产物抽查

| 产物 | 判定 | 备注 |
|---|---|---|
| `Dockerfile.pg-zhparser` | pass | root + libscws-dev + zhparser + 清理 |
| `init_chinese_fts.sql` | pass | 有 Mapping；配置非幂等（重跑会炸）— 实跑注意一次即可 |
| `schema_chunks_no_fts.sql` | pass | 对齐 alembic 列；无 fts 生成列 |
| `add_fts_chinese.sql` | pass | `chinese` GENERATED + GIN |
| `shadow_copy_chunks.sh` | pass | 可执行；排除 fts；只读主库 |
| `README.md` | pass | 步骤 1–6 清晰 |
| `retrieve.py` `RAG_FTS_CONFIG` | pass | 默认 simple；标识符校验；未改 RRF |
| `tests/test_rag_fts_config.py` | pass | default / chinese / invalid / expand |

### 50 复跑命令

| 命令 | 退出码 |
|---|---|
| `uv run pytest tests/test_rag_fts_config.py tests/test_golden_eval_runner.py -q --tb=line` | 0（16 passed） |
| `uv run ruff check app/ops/rag/retrieve.py` | 0 |
| `npx @cyning/harness@2.22.0 verify --task …/task_rag_zhparser_arm_a.md` | PASS |

### 风险提醒（实跑时）

1. `init_chinese_fts.sql` 的 `CREATE TEXT SEARCH CONFIGURATION chinese` **非幂等**
2. COPY 含 `embedding vector` → CSV 后，导入后建议 `SELECT count(*)` 与主库对齐；必要时 `setval` 修 serial
3. 评测必须同时：`DATABASE_URL→5433` + `RAG_FTS_CONFIG=chinese` + `RAG_KW_EXPAND=false`

### 给维护者的最短实跑清单

见 `experiments/rag_compare/zhparser_arm_a/README.md` 第 1–6 步；产出 `reports/r4-A.yaml` 后按 task 判读三档（≥15 / ≥10 / +5～8 弃 A）。

### 50 不通过项

无（范围外 deferred 项不记 fail）。
