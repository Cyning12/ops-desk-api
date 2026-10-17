# RUNBOOK · 生产向量水位/对账核查（prod-vector-waterline-check · v1）

> **任务**：task prod-vector-waterline-check（E3 · 只读核查脚本配套 runbook）
> **前置**：HG-PROD-READONLY-ACCESS 已签（生产执行 = 维护者动作）；本仓 scripts/check_vector_waterline.py 在
> **产物**：reports/vector_waterline_<env>_<UTCts>.yaml（模板：reports/vector_waterline_TEMPLATE.yaml）
> **只读**：脚本对 PG 只发 SELECT、对 Qdrant 只用 count/scroll 读 API；禁任何写

## 一句话

维护者持生产只读访问跑一次 scripts/check_vector_waterline.py，一次性回答三个问题：
Qdrant 与 PG 条数对不对得上（差集哪个方向）、DLQ 积没积压、最近 ingest 水位到哪。
**脚本只出证据；差集修复/DLQ 重放等处置动作另 task（FP-6），本 runbook 不含处置步骤。**

## 1. 前置条件

- **授权**：task 档人工闸 HG-PROD-READONLY-ACCESS = approved（pending 时**禁止**生产执行，报告位留空不伪造 · FP-7）。
- **访问**：
  - PG **只读账号**（对 ops_knowledge_chunks / ops_qdrant_dlq 仅 SELECT 权限；写死只读语义——脚本本身无写语句，账号层再兜一层）。
  - Qdrant **只读端点/凭证**（REST 6333；count/scroll 即可，无需写权限 API key）。
- **环境变量清单**：

  | env | 必填 | 说明 |
  |-----|------|------|
  | WATERLINE_DATABASE_URL 或 DATABASE_URL | 是（缺则 PG 面降级） | PG 连接串；asyncpg 形式自动转 psycopg；**报告不落连接串** |
  | QDRANT_URL | 否（缺省 http://127.0.0.1:6333） | 生产须显式指向生产 Qdrant |
  | QDRANT_COLLECTION | 否（缺省 ops_knowledge） | 与 app/ops/rag/backend.py 缺省一致 |
  | QDRANT_API_KEY | 按部署 | 只读权限即可 |

- 执行机依赖：本仓 requirements（sqlalchemy + psycopg + qdrant-client + PyYAML），建议仓根 .venv / uv run。

## 2. 执行步骤

```bash
# 生产（维护者 · HG-PROD-READONLY-ACCESS 已签）
WATERLINE_DATABASE_URL='postgresql+psycopg://<ro_user>:<pass>@<prod-pg>:5432/opsdesk' \
QDRANT_URL='http://<prod-qdrant>:6333' QDRANT_API_KEY='<ro-key>' \
uv run python scripts/check_vector_waterline.py --env prod

# 本地/compose 验证（40 轨 · 非生产证据）
docker compose up -d db qdrant
DATABASE_URL='postgresql+psycopg://ops:ops_password@127.0.0.1:5432/opsdesk' \
QDRANT_URL='http://127.0.0.1:6333' \
uv run python scripts/check_vector_waterline.py --env local
```

- 出口码：0 = 至少一面有实证（含单侧降级）；2 = 双侧均无实证（不出报告）。
- 报告落 reports/vector_waterline_<env>_<UTCts>.yaml；生产报告 environment=prod，
  回填后路线 §P1-RAG「生产向量水位与对账 待人工」方可消解（TC-WL-8）。

## 3. 报告解读

| 字段 | 含义 | 判读 |
|------|------|------|
| pg_face.row_count vs qdrant_face.points_count | 两侧条数 | reconcile.count_diff = pg - qdrant |
| reconcile.pg_only_in_qdrant_missing | **PG 有 Qdrant 无** | 影子写漏/失败积压嫌疑 → 对照看 dlq.depth；count>0 即 mismatch |
| reconcile.qdrant_only_in_pg_missing | **Qdrant 有 PG 无** | 墓碑未删/脏点嫌疑（delete 影子写失败） |
| pg_face.dlq.depth / oldest_age_seconds | DLQ 积压深度 / 最老条目年龄 | depth>0 → verdict=backlogged；**重放处置另 task** |
| pg_face.ingest_waterline.max | 最近 ingest 水位 | 口径 = max(ops_knowledge_chunks.embedded_at)（表无 created_at/updated_at，按表结构实定）；与预期 ingest 节奏对拍 |
| status | ok / degraded | degraded → 读 degradation.notes，先把缺失面补齐再谈对账结论 |

差集 sample 为 point_id 抽样（默认 20，--sample-limit 可调），用于人工核对方向，不是全量清单。

## 4. 降级判读（显式失败不冒充）

| 情形 | 出口码 | 报告 | 处置 |
|------|--------|------|------|
| Qdrant 不可达/凭证缺失 | 0 | PG 单侧水位齐全；qdrant_face.status=no_evidence + notes 含「Qdrant 面无实证：<原因>」 | 修网络/凭证后重跑；**不得**拿 PG 单侧当对账通过 |
| PG 不可达/env 未配置 | 0 | Qdrant 单侧；pg_face.status=no_evidence + 「PG 面无实证」 | 同上；DLQ/水位均无实证 |
| 双侧均不可达 | 2 | **不出报告**；stderr 显式错误 | 排除连通性后重跑 |
| 对账 mismatch | 0 | reconcile.verdict=mismatch + 双向差集计数/抽样 | **另立处置 task**；本脚本不修数据（FP-6） |

## 验证卫生

报告不落连接串/凭证（config 只记 database_url_set 布尔与剥离凭证后的 qdrant_url）；
生产报告含真实 point_id 抽样，属内部运维证据，按仓内 reports/ 惯例留痕不外发。

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-17 | v1 落稿（30 交付 · 承 RUNBOOK_multi_replica_verify_v1 格式先例） |
