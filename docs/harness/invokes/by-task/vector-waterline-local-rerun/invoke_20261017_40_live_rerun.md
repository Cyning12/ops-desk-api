---
hat: 40
task_slug: vector_waterline_local_rerun
date: 2026-10-17
---

# invoke · 40 实证棒 · vector_waterline_local_rerun（TC-LR-1~6 本地/compose 亲跑实录）

## GATE_VERIFY（首输出 · 真值 = task 人工闸表）

| human_gate_id | status | blocks_hats | 核验 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20, 40 | docs/tasks/active/task_vector_waterline_local_rerun.md :39（维护者授权 00 代录 m00823 · 20 R1 审查文 PASS） |
| HG-AUDIT-R1 | approved | 40 | 同档 :40 |
| HG-GRAPH-MODULES | approved | 40 | 同档 :41 · 全局真值 docs/_tech_graph/l1/01_modules.md:63 approved · graph_change_layer=none |

三闸全 approved（已代录）→ 开工合法。母体 HG-PROD-READONLY-ACCESS 仍 pending，仅阻 TC-WL-8 生产执行，本 task 零涉生产不受阻。

## TC-LR-1（机断 · 起服核验）— PASS

`docker ps` 实录：`ops-desk-api-qdrant-1` Up 29 hours **(healthy)** · 镜像 **qdrant/qdrant:v1.19.0** · 0.0.0.0:6333-6334 映射；`ops-desk-api-db-1` Up 29 hours **(healthy)** · pgvector/pgvector:pg15 · 0.0.0.0:5432 映射。两服已 healthy，按 task 档「可复用」不重建（FP-6 兜底未触发）。

## TC-LR-2（实证 · runbook §2 命令亲跑）— PASS（exit 0 · 含一次降级照登偏差，见下）

runbook §2 local 形态命令逐字亲跑（`DATABASE_URL='postgresql+psycopg://ops:ops_password@127.0.0.1:5432/opsdesk' QDRANT_URL='http://127.0.0.1:6333' uv run python scripts/check_vector_waterline.py --env local`）：

- **首跑（逐字 · 12:35:38Z）**：exit 0，但 Qdrant 面 `no_evidence`（`InvalidURL: Invalid port: ':1]'`）→ status=**degraded** 如实落盘 reports/vector_waterline_local_20261017T123538Z.yaml（FP-2 不假绿）。
- **根因定位（探针实证 · 非脚本 bug）**：本机 shell 注入代理变量（`http_proxy/all_proxy=http://127.0.0.1:7890`，`NO_PROXY=localhost,127.0.0.1,::1,[::1]`）；qdrant-client 底层 httpx 构造 Client 时解析 NO_PROXY 中 IPv6 项 `[::1]` 触发 `httpx.InvalidURL: Invalid port: ':1]'`。curl 直连 `http://127.0.0.1:6333/collections/ops_knowledge` 返回 HTTP 200 —— Qdrant 服务本身健康，系**执行机 shell 环境污染**，脚本零改码可解（未触发 STOP 另立 task）。
- **重跑（命令本体逐字不变 · 仅以 `env -u` 剥除代理变量 · 12:36:49Z）**：exit 0，双侧实证齐全，status=**ok**，报告落 reports/vector_waterline_local_20261017T123649Z.yaml。

## TC-LR-3（实证+机断 · 模板逐键对拍）— PASS 全中

基准 reports/vector_waterline_TEMPLATE.yaml（template_version=v1）vs 实跑报告 vector_waterline_local_20261017T123649Z.yaml：

| 模板键 | 实值 | 判 |
|--------|------|----|
| kind | vector_waterline | ✓ |
| template_version | v1 | ✓ |
| recorded_at | 2026-10-17T12:36:49.236845+00:00 | ✓ |
| environment | **local** | ✓ 钉死 |
| executed_by | cyning（系统用户名实值） | ✓ |
| git_sha | d3fd056（master HEAD 实值） | ✓ |
| config.database_url_set | true（布尔 · 不落连接串） | ✓ |
| config.qdrant_url | http://127.0.0.1:6333（无凭证可剥） | ✓ |
| config.qdrant_collection | ops_knowledge | ✓ |
| status | ok ∈ {ok,degraded} | ✓ |
| pg_face | status=ok · row_count=0 · ingest_waterline{column=ops_knowledge_chunks.embedded_at, max=null} · dlq{table=ops_qdrant_dlq, depth=0, oldest_created_at=null, oldest_age_seconds=null, verdict=empty} | ✓ 四键+verdict 齐 |
| qdrant_face | status=ok · collection=ops_knowledge · points_count=8574 · scrolled_ids=8574 | ✓ 两数一致 |
| reconcile | status=ok · pg_count=0 · qdrant_count=8574 · count_diff=-8574 · verdict=mismatch · 双向差集{count,sample} 齐（sample 20 条 point_id） | ✓ |
| degradation | degraded=false · notes=[] | ✓ 与双侧 ok 自洽 |
| disclaimer | 含「本地/compose 环境产物不得当作生产证据（TC-WL-5 与 TC-WL-8 分离）」原文 | ✓ FP-8 钉死 |

报告为脚本实跑生成（uv run 子进程），非 TEMPLATE 拷贝、非手改（两份报告 git_sha/executed_by 均为脚本自采实值）。

## TC-LR-4（机断 · 真实性核验）— PASS

- 降级不假绿实证：首跑报告（123538Z）qdrant_face.status=no_evidence → status=degraded 且 degradation.notes 非空（「Qdrant 面无实证：InvalidURL: Invalid port: ':1]'」）· reconcile.status=skipped + reason —— 三态降级链路真实生效，未冒充绿。
- 空表如实记 0（FP-6）：PG ops_knowledge_chunks row_count=0 · ingest_waterline.max=null · DLQ depth=0 verdict=empty —— 零水位不伪造。
- 数值自洽：count_diff = pg_count - qdrant_count = 0 - 8574 = **-8574** ✓；qdrant_only count=8574 = points_count ✓；points_count=scrolled_ids=8574 ✓。

## TC-LR-5（机断 · 三门）— PASS

| 门 | 命令 | 结果 |
|----|------|------|
| ruff | `uv run ruff check scripts/check_vector_waterline.py tests/test_check_vector_waterline.py` | All checks passed! EXIT=0 |
| pytest | `uv run --extra dev pytest tests/test_check_vector_waterline.py -q` | **13 passed** in 0.83s · EXIT=0 |
| spec-wave verify | `npx --yes spec-wave verify --target .` | VERIFY: PASS · EXIT=0 |
| task lint | `npx --yes spec-wave task lint --file docs/tasks/active/task_vector_waterline_local_rerun.md` | LINT: PASS · EXIT=0 |

## TC-LR-6（机断 · 零越界）— PASS

`git status` 实录：tracked 零 diff；untracked 仅白名单 —— 新增 reports/vector_waterline_local_20261017T123538Z.yaml + reports/vector_waterline_local_20261017T123649Z.yaml + docs/harness/invokes/by-task/vector-waterline-local-rerun/（含本 invoke 与 10/20 两棒）+ docs/tasks/active/task_vector_waterline_local_rerun.md（勾选回填）+ docs/harness/reviews/task_vector_waterline_local_rerun_audit_R1_20261017.md（20 棒产物）。`scripts/ tests/ app/ alembic/ docker-compose.yml` 零 diff ✓。

## 偏差与上抛（照登 · 不假绿不处置）

1. **代理环境污染偏差（已消解）**：首跑逐字命令因执行机 shell 代理变量（NO_PROXY 含 `[::1]` 触发 httpx 解析 bug）致 Qdrant 面降级；非脚本缺陷（探针实证 curl 200 + 剥代理后双侧实证齐全），脚本零改码，未触发「须改码即 STOP」。降级报告 123538Z 保留作不假绿证据，未删除未手改。
2. **数据态发现（FP-7 上抛 · 本 task 不处置）**：本地 Qdrant `ops_knowledge` 8574 points vs PG ops_knowledge_chunks 0 行 → reconcile verdict=**mismatch**（方向 = Qdrant 有 PG 无 8574 条 · 疑墓碑未删/脏点或本地 DB 重建清空所致）。按非范围只记录上抛，建议维护者另立处置 task 核查本地数据态来源；DLQ depth=0 无积压。
3. 环境注记：uv 告警 `Ignoring dangling temporary directory: ~anggraph_prebuilt-1.1.0.dist-info`（venv 残留 · 不影响结果 · 非本 task 范围）。

## 交付落位

- 分支 task/vector-waterline-local-rerun（base master d3fd056）· commit 含两份真实报告 + 本 invoke + task 档勾选/自检结论/修订记录回填 → push + gh pr create --base master（禁 merge）。
- task 档 TC-LR-1~6 全勾选 · 自检结论回填 · 修订记录加 40 实证一行。
