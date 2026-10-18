# invoke_20261018_40_rebuild · local-rag-knowledge-rebuild（40 实证执行棒）

- **时间**：2026-10-18 15:00–15:32 (+08:00) · **棒型**：40 单棒（裁定=零落码）· **worktree**：ops-desk-api-worktrees/t-rag-rebuild（分支 task/local-rag-knowledge-rebuild · base master fa0aadb）
- **闸**：HG-TASK-DRAFT=approved · HG-AUDIT-R1=approved · HG-GRAPH-MODULES=n/a（m01159 授权链代录）· `npx spec-wave verify` EXIT=0（VERIFY: PASS）
- **disclaimer**：本地 compose 开发库口径，不得外推生产（FP-9）。

## 执行摘要

F1 前置三面全绿（容器 healthy · .env 密钥/影子开关 · collection green dim=1024 points=0 · PG 零点基线 0/0 对齐 20261018T005534Z）。
F2 dry-run scanned=2755=to_upsert（unchanged/to_delete=0），与语料面 881+1855+19 精确匹配。
F3 经两次环境级失败（NO_PROXY IPv6 触发 httpx 解析 bug → 零落码清洗；api embedder 无批切全量单请求超时 → 零落码分批 --limit 递增）与一次本人编排事故（standalone --only docs 触发墓碑对账删 2736 单元 · 源表零损失 · DLQ=0 · 已全量恢复），最终 25/25 步全 OK。
F4 水位 verdict=match：PG 8648 == Qdrant 8648 == ingest 累计 8429+219 · diff=0 · DLQ=0 · degraded=false。
F5 rag_smoke 因环境缺 langchain 不可全链 → FP-7 降级纯向量检索（显式标注）：top-1/top-3 双中锚 issue#2720（0.7431/0.6958）。

## 三数与裁定

| chunks_written（恢复轮） | PG 行数 | Qdrant points | 水位 | 规模区间 |
|---|---|---|---|---|
| 8429（+docs 219 = 8648） | 8648 | 8648 | match | 8648 ∈ [6000,12000] ✅ |

## 证据索引（evidence/）

- f2_dryrun.txt — dry-run 报告全文
- f3_ingest.log — 首次全量尝试（ httpx.InvalidURL 栈全文 ）
- f3_retry_note.md — NO_PROXY bug 根因与零落码修复对照实证
- f3_steps_summary.log + f3_step_*.log — 首轮分批台账（28/28 OK + docs 事故步）
- f3_incident_tombstone.md — 墓碑对账事故分析（根因/影响面/恢复）
- f3r_steps_summary.log + f3r_step_*.log — 恢复轮 25 步台账（全 attempt=1）
- f4_waterline.yaml — 水位报告拷贝（reports/vector_waterline_local_20261018T072903Z.yaml）
- f5_smoke.txt — rag_smoke 全链失败原文（langchain 缺失）
- f5_vector_smoke.txt — 降级向量抽检 top-5（锚双中）

## 关键命令台账

```bash
npx spec-wave verify --target . --task docs/tasks/active/task_local_rag_knowledge_rebuild.md   # EXIT=0
uv sync --extra dev                                                                            # EXIT=0
uv run python scripts/rag_ingest.py --dry-run --docs-root <05-plan> --docs-root <contracts>    # scanned=2755
# F3 分批（NO_PROXY 清洗 · 步长 75 · 不带 --only · docs-root 常随）：
NO_PROXY='localhost,127.0.0.1' uv run python scripts/rag_ingest.py --limit <75..1875> --docs-root ... --embedder api
uv run python scripts/check_vector_waterline.py --env local                                    # verdict=match 8648/8648
uv run pytest tests/test_check_vector_waterline.py -q                                          # 13 passed
npx --yes spec-wave task lint --file docs/tasks/active/task_local_rag_knowledge_rebuild.md     # LINT: PASS
```

## 偏差照登

1. rag_smoke 全链不可用（缺 langchain · Langfuse 集成）→ 降级向量抽检，形态显式标注，未冒充全链。
2. 编排事故致 ~8.4k chunks 返工重嵌入（+2.9M tokens 量级），已恢复并实证终态一致。
3. --embedder api 无内部批切为既存管线特性；内部批切属改码，FP-8 纪律未落，建议另立 task。
