# CLOSE：local-vector-data-state-audit（本地 Qdrant 8574 vs PG 0 数据态溯源核查）

> 关账日期：2026-10-17 · 关账人：00（维护者授权 m00954「合并 + 立清理 task」）
> 体例承 [close_hitl_resume_async_20261015.md](close_hitl_resume_async_20261015.md)

## 一、任务信息

| 项 | 值 |
|---|---|
| task | [task_local_vector_data_state_audit.md](../done/task_local_vector_data_state_audit.md)（已归档 done/） |
| 性质 | 本地数据态核查 · **全程只读 · 零改码 · 40 实证棒** |
| 上游 | `task_vector_waterline_local_rerun` FP-7 上抛（PR #268/#269 已 CLOSE） |
| PR | [#270](https://github.com/Cyning12/ops-desk-api/pull/270) MERGED · squash `1570f82` · CI 4/4 绿 · 19 文件全新增 |
| 审查 | R1 [task_local_vector_data_state_audit_audit_R1_20261017.md](../../harness/reviews/task_local_vector_data_state_audit_audit_R1_20261017.md) 签收零阻塞 nit 2 已修正 |
| 闸 | 三闸 approved（维护者 m00914 授权 00 代录 · 承 m00238 总授权） |

## 二、交付清单

| 产物 | 说明 |
|---|---|
| `reports/local_vector_data_state_audit_20261017T135118Z.md` | 结论报告（双 disclaimer 本地口径钉死） |
| `docs/harness/invokes/by-task/local-vector-data-state-audit/evidence/` e00–e05 | 证据 13 件（命令台账 + 原始输出钉死可复现） |
| `invoke_20261017_40_audit.md` | 40 棒 invoke 留痕 |
| 既有资产零改码 | scripts//app//alembic//compose 零 diff（TC-DA-6 白名单机断） |

## 三、验收核验（TC-DA-1 ~ TC-DA-6 全 PASS · 零假绿）

**F1 · Qdrant 8574 点来源 = 历史正常写入（迁移期 export_vectors.py→bulk_upsert.py）**：决定性指纹=150/150 抽样 payload 恰 4 键 {source_type,repo,source_id,chunk_index} 与 export_vectors.py:12 ALLOWED_PAYLOAD 逐键相等（影子写 filter_payload 恒产 5 键含 tenant_id → 排除）；WAL/全部 7 段存储 mtime 钉死 2026-08-18 02:54Z 单次批量此后零写入；现 qdrant_data 卷 CreatedAt=08-16 晚于 08-13 先例 → 08-13 对账系旧卷，现 8574 点为 08-18 重迁。

**F2 · PG 空表成因 = 表级清空，非库重建**（头号假设证伪）：pgdata 卷/PG_VERSION mtime=2026-07-16 钉死 initdb 未重建；ops_knowledge_chunks 堆文件 0 字节 mtime=2026-09-07 02:19:59Z → 清空窗 (2026-08-13, 2026-09-07]；checkpoint/ops_lg_rag_run_events/ops_llm_usage 等表有数 → 非整库清空；DLQ 文件 mtime=08-13 先于清空窗 → 影子写无失败痕迹；alembic head=20260923_memory_episodes（清空后库仍正常升级）。

**F3 · 处置建议 = 清理脚本**（重建索引因本地源数据已空无支撑 · 保持原样持续 mismatch 噪音 · **执行另立 task**）。

**机制一句话**：8574 点=08-18 迁移期正当重迁写入；PG 表其后于 09-07 前被表级清空（绕过应用层无影子删除）→ 迁移遗留点+PG 清空叠加成 mismatch；**点非脏写、库非重建**。

## 四、偏差与照登

1. tenant_id 缺失偏差照实记（抽样 4 键无 tenant_id，与 filter_payload 5 键对照构成排除性证据而非缺陷）。
2. 清空路径 DELETE+VACUUM vs DROP+重建空表两解不硬判（同属表级清空，FP-5 无法判定合法出口）。
3. 容器开工/收工双 healthy 无瞬态；计数 8574/0/-8574 与立案报告逐键一致。

## 五、遗留移交

| 项 | 去向 |
|---|---|
| 8574 遗留点清理（快照备份前置 · dry-run · 删后复跑核验） | 另立 `task_local_qdrant_orphan_points_cleanup`（10-task 起草中 · m00954 授权） |
| HG-PROD-READONLY-ACCESS（生产水位/生产核查） | 仍 pending · 移交维护者 · 本 task 零涉生产不消解 |

## 六、维护者 checklist

- [x] 验收核验完毕（TC-DA-1~6 全 PASS 零假绿）
- [x] 证据 13 件命令+输出钉死可复现
- [x] 结论报告落盘双 disclaimer 本地口径
- [x] 零改码零越界核验（白名单机断）
- [x] 处置建议三选一附实证支撑 · 执行另立 task
- [x] PR 合并（squash 1570f82）· 归档 done/ · README 登记 · 50 invoke 落盘
