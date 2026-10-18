# 处置报告：local-qdrant-orphan-points-cleanup（本地 Qdrant ops_knowledge 8574 孤儿点清理 · 40 实证执行）

> **执行时间**：2026-10-18T00:53:20Z – 00:55:34Z（UTC · 会话 ts 20261018T005320Z）
> **执行环境**：本地 compose 开发库（ops-desk-api-qdrant-1 · Qdrant v1.19.0 · REST 127.0.0.1:6333 / ops-desk-api-db-1 · PG opsdesk）
> **口径 disclaimer（FP-7 钉死）**：本报告全链为**本地/compose 开发库口径，不得外推生产**；生产侧任何动作仍属 HG-PROD-READONLY-ACCESS（pending）管辖，本处置不消解该闸。
> **授权链**：维护者 2026-10-18 授权 00 代录三闸 approved（m01000 · 承 m00238 总授权）· 落码裁定=零落码 curl/stdin 一次性执行。
> **证据附件**：`docs/harness/invokes/by-task/local-qdrant-orphan-points-cleanup/evidence/e01–e11`（台账 e00_commands.md 索引全文命令）。

## 1. F1 · 备份硬闸（FP-2 · TC-OC-1）— PASS

| 项 | 值 |
|---|---|
| 容器态前置 | `docker inspect` 双容器 Up (healthy) 42h+ 留证（e01） |
| 快照名 | `ops_knowledge-7885642805251913-2026-10-18-00-53-20.snapshot`（e02 建 · e03 列出复核） |
| host 备份路径 | `backups/local_qdrant_orphan_cleanup_20261018T005320Z/ops_knowledge-7885642805251913-2026-10-18-00-53-20.snapshot`（**二进制 untracked 留本机，不入 git**） |
| size | 82,857,984 bytes（host）== 服务端登记 size 82,857,984（逐字节一致） |
| sha256 | `270b02bd419d1e4a1a94664bc576844467639b65f3bc4838934d567838692e7f`（host shasum）== 服务端 checksum（逐字符一致）（e05 台账） |
| 归档可读性（R1 N2） | `tar -tf` 可解：segments×8 tar + wal + shard_config.json + version.info（e04） |

**硬闸结论**：备份产物存在 + size>0 + sha256 双端一致 + tar 可读 → **准予进入删除**。

## 2. F2 · dry-run 双重一致核验（FP-3 · TC-OC-2）— PASS

- 只读 scroll（`with_payload=false, with_vector=false`，limit=1000）全量 id：9 页 · 8574 个唯一 int id · min=1 max=8593（e06 原始输出）。
- 与上游基准 `e04_scroll_ids_raw.json`（8574 id）**逐集相等**：S−E04 = ∅ · E04−S = ∅（e07 核验输出 verdict=PASS）。
- 计数一致：|S| == 8574 == 立案计数。

## 3. F3 · 白名单分批删除（FP-6 · TC-OC-3）— PASS

`POST /collections/ops_knowledge/points/delete?wait=true`，body `{"points": [<显式 id>]}`，9 批（8×1000 + 1×574），逐批台账（e09）：

| 批 | id 数 | id 范围 | status | operation_id |
|----|------|---------|--------|--------------|
| 1–8 | 1000×8 | 1–8000（连续分段） | ok | 41–48 |
| 9 | 574 | 8001–8593（含 8546–8564 缺口段） | ok | 49 |

- 批次并集 == S（8574 · 逐集相等 · e09 summary verdict=PASS）。
- **零 filter 删除 · 零 delete collection · 零 truncate**（全部为 PointIdsList 显式 id 白名单）。
- 他 collection 零触碰对照（e08 前 / e10 后）：`ops_knowledge, ops_knowledge_scale, ops_knowledge_scale_100k, ops_knowledge_scale_mem, ops_knowledge_scale_sq` 前后完全一致（仅 ops_knowledge 内部点集变化，集合清单零变化）。

## 4. F4 · 删后核验（FP-5 · TC-OC-4）— PASS

| 核验 | 结果 | 证据 |
|---|---|---|
| `GET /collections/ops_knowledge` | **points_count=0** · indexed_vectors_count=0 · status=green | e11 |
| 水位脚本复跑 | `reports/vector_waterline_local_20261018T005534Z.yaml`：pg row_count=**0** · dlq depth=0 verdict=empty · qdrant points_count=scrolled_ids=**0** · count_diff=**0** · verdict=**match** · degraded=**false** · EXIT=0 | 报告全文落档 |

**与立案报告计数对照**：8574 / 0 / -8574（mismatch）→ **0 / 0 / 0（match）**。

## 5. 回滚预案（预写 · TC-OC-5 · 本次未触发）

删后核验全部 PASS，未触发回滚。预案预写如下（快照同时留存 qdrant_data 卷内 `/qdrant/storage/snapshots/ops_knowledge/` 与 host 备份路径）：

```bash
# 容器内卷副本恢复（首选）：
env -u http_proxy -u https_proxy -u all_proxy -u NO_PROXY -u no_proxy \
  curl -sS -X PUT http://127.0.0.1:6333/collections/ops_knowledge/snapshots/recover \
  -H 'Content-Type: application/json' \
  -d '{"location": "file:///qdrant/storage/snapshots/ops_knowledge/ops_knowledge-7885642805251913-2026-10-18-00-53-20.snapshot"}'
# host 备份副本可经上传端点或拷回卷内后同法恢复；恢复后复跑本报告 §4 核验，预期回到 8574。
```

## 6. 执行合规自证

- 零落码：全链 curl + python3 stdlib stdin 一次性脚本（命令全文见 evidence/e00_commands.md）· `scripts//app//alembic//compose` 零 diff（TC-OC-6 git status 白名单实证）。
- 代理污染规避：全链 `env -u http_proxy -u https_proxy -u all_proxy -u NO_PROXY -u no_proxy` 剥离（承 20261017T123649Z 降级先例教训）。
- 不假绿：本报告每一计数/判定均可回溯至 e01–e11 原始输出附件。
- 首次水位复跑 degraded（PG 面无实证 · .env 未在 worktree）如实记录并修正：注入 `DATABASE_URL`（主仓 .env 同值 · asyncpg→psycopg 由脚本 :211 自转）后复跑得全绿；降级报告 `reports/vector_waterline_local_20261018T005444Z.yaml` 一并留档不销毁。

---
*40 实证执行棒 · 2026-10-18 · 本地/compose 口径，不得外推生产*
