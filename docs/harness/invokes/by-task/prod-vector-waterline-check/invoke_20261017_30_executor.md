---
hat: 30-executor
task_slug: prod_vector_waterline_check
date: 2026-10-17
---

# invoke · 30 执行 · prod_vector_waterline_check（只读核查脚本 + runbook + 模板 + 桩测）

## 闸核验（开工前 GATE_VERIFY · 全放行）

- 分支 task/prod-vector-waterline-check（worktree t-prod-waterline · 未切分支）
- HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均 approved（task 档人工闸表 :39-41 · 全局真值 01_modules.md:63 亲读）
- npx spec-wave verify → VERIFY: PASS · 10/20 invoke 在档 · R1 审查文 docs/harness/reviews/task_prod_vector_waterline_check_audit_R1_20261017.md 签收零阻塞
- HG-PROD-READONLY-ACCESS 保持 pending：仅阻生产执行（TC-WL-8 维护者动作），不阻 30 交付

## 交付物（E1–E5 全落）

| 验收 | 交付 | 实证 |
|------|------|------|
| E1/TC-WL-1 | scripts/check_vector_waterline.py | 只读三断面（PG 行数+ingest 水位 max(embedded_at)+DLQ 深度/最老年龄 · Qdrant count+scroll 全量 id 差集）；pytest 13 用例全绿 |
| E2/TC-WL-2 | 降级三态 | Qdrant 不可达→exit 0 + PG 单侧 + 「Qdrant 面无实证」；PG 不可达/env 缺失→同理单侧；双不可达→exit 2 + stderr 显式错误 + 零报告（CLI 子进程断言） |
| E3/TC-WL-3 | docs/guides/RUNBOOK_prod_vector_waterline_v1_zh.md | 前置条件（闸+env 清单表）/执行步骤/报告解读/降级判读四节齐备 |
| E4/TC-WL-4 | reports/vector_waterline_TEMPLATE.yaml | PG 面/Qdrant 面/对账双向差集/DLQ 面/降级标注位同形状占位 |
| E5 | tests/test_check_vector_waterline.py | FakePgConn + StubQdrantClient（写方法记账）· 只读断言：write_calls==[] + 全 SQL SELECT 词边界扫描 |

## 关键实定与决策

- ingest 水位口径 = max(ops_knowledge_chunks.embedded_at)：表无 created_at/updated_at（alembic/versions/20260808_rag_chunks.py:46 表结构亲读），按 task「30 按表结构实定」授权定口径，runbook §3 标注。
- 报告不落连接串/凭证：config 仅 database_url_set 布尔 + 剥离凭证的 qdrant_url（验证卫生）。
- 差集只记录不处置（FP-6）：处置另 task；disclaimer 字段写死「本地/compose 产物不得当生产证据」。
- TC-WL-6 零 diff 实证：git status 仅 7 个新增路径（scripts/tests/docs/reports），app/ops/rag/** · alembic/** · docker-compose.yml 零 diff。

## 验证记录

- uv run pytest tests/test_check_vector_waterline.py -q → 13 passed（含 CLI 子进程双不可达 exit 2）
- uv run ruff check scripts/check_vector_waterline.py tests/test_check_vector_waterline.py → All checks passed
- 全量 pytest tests -q → 1831 passed / 4 failed 均为基线环境性（test_hitl asyncpg 真库 · test_memory_vector_p1 缺 SILICONFLOW_API_KEY · test_multi_replica_dualproc ×2 双进程环境），与本 task 触及面无关、零新增红
- 桩测中修三处自身 bug：_fake_connect 误挂 @contextmanager · 只读扫描 'CREATE' 子串误判 created_at（改词边界）· 漏 import re / 未用 import pytest

## 交接 40 / 维护者

- 40：本地/compose（docker compose up -d db qdrant）亲跑出真实报告一份（TC-WL-5）；命令见 runbook §2。
- 维护者：签 HG-PROD-READONLY-ACCESS 后按 runbook 跑生产核查 → reports/vector_waterline_prod_*.yaml 回填 → 路线 §P1-RAG「待人工」消解（TC-WL-8）。
