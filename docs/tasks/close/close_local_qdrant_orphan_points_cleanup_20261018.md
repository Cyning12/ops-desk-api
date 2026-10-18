# CLOSE：local-qdrant-orphan-points-cleanup（本地 Qdrant 8574 孤儿点清理处置）

> 关账日期：2026-10-18 · 关账人：00（维护者授权 m01029「合并」）
> 体例承 [close_hitl_resume_async_20261015.md](close_hitl_resume_async_20261015.md)

## 一、任务信息

| 项 | 值 |
|---|---|
| task | [task_local_qdrant_orphan_points_cleanup.md](../done/task_local_qdrant_orphan_points_cleanup.md)（已归档 done/） |
| 性质 | 本地运维处置 · **含写动作（删除 8574 孤儿点）· 零落码 curl 裁定**（维护者 m01000 采纳） |
| 上游 | `task_local_vector_data_state_audit` F3 处置建议（PR #270/#271 已 CLOSE） |
| PR | [#272](https://github.com/Cyning12/ops-desk-api/pull/272) MERGED · squash `6ee1f61` · CI 4/4 绿 · 21 文件 |
| 审查 | R1 [task_local_qdrant_orphan_points_cleanup_audit_R1_20261017.md](../../harness/reviews/task_local_qdrant_orphan_points_cleanup_audit_R1_20261017.md) 签收零阻塞 nit 2 已顺手精化 |
| 闸 | 三闸 approved（维护者 m01000 授权 00 代录 · 承 m00238 总授权） |

## 二、交付清单

| 产物 | 说明 |
|---|---|
| `reports/local_qdrant_orphan_points_cleanup_20261018T005320Z.md` | 处置报告（回滚预案预写 §5 · disclaimer 本地口径钉死） |
| `reports/vector_waterline_local_20261018T005534Z.yaml` | 删后水位复跑：pg=0/qdrant=0/count_diff=0/**verdict=match** |
| `reports/vector_waterline_local_20261018T005444Z.yaml` | 降级照登报告（首跑未注入 DATABASE_URL · 保留作证） |
| 证据 e00–e12 | 命令台账+原始输出（docs/harness/invokes/by-task/local-qdrant-orphan-points-cleanup/evidence/） |
| 快照备份 | `backups/local_qdrant_orphan_cleanup_20261018T005320Z/ops_knowledge-7885642805251913-2026-10-18-00-53-20.snapshot`（82,857,984 B · sha256 `270b02bd419d1e4a1a94664bc576844467639b65f3bc4838934d567838692e7f` 双端一致 · tar -tf 可读 · **untracked 留本机不入 git**） |

## 三、验收核验（TC-OC-1 ~ TC-OC-6 全 PASS · 零假绿）

- TC-OC-1 备份硬闸 PASS：快照创建+下载拷出+sha256 双端逐字符一致+tar 可读，全过才进 F3。
- TC-OC-2 dry-run PASS：scroll 9 页 8574 唯一 id（min1/max8593）与上游证据 e04 **双向 diff 空集**。
- TC-OC-3 白名单删除 PASS：`points/delete?wait=true` 显式 id 9 批（8×1000+574 · operation_id 41–49 全 ok · 并集==S）· 零 filter/零 truncate/零 delete collection · 他 collection（ops_knowledge_scale 等 4 实验集合）零触碰。
- TC-OC-4 删后核验 PASS：count=0 · 水位复跑 verdict=match · 计数对照 8574/0/-8574 → 0/0/0。
- TC-OC-5 不假绿+可回滚 PASS：首跑水位 degraded（worktree 无 .env 未注入 DATABASE_URL）如实留档未冒充，注入后复跑全绿；recover 预案预写未触发。
- TC-OC-6 零越界 PASS：scripts//app//alembic//compose 零 diff · pytest 13 passed · task lint PASS。

## 四、偏差与照登

1. **00 关账操作事故（照登）**：清理 40 worktree 时 `git worktree remove --force` 将 untracked 的 host 备份副本一并删除。服务端快照仍在 qdrant_data 卷内（checksum 一致），已从 snapshot API 重下载恢复至主仓 `backups/`，sha256 复验逐字符一致、tar -tf 可读。**回滚能力无损失**。教训：worktree 内有刻意 untracked 产物时禁止 --force 直删，先搬出。
2. 首跑水位降级照登（worktree 不随 .env → DATABASE_URL 缺失 · 非脚本 bug · 降级报告保留作证）。
3. 备份目录 `backups/` 未被 .gitignore 覆盖——本次 PR 按显式路径 add 未混入；后续操作注意勿 `git add .`。

## 五、遗留移交

| 项 | 去向 |
|---|---|
| HG-PROD-READONLY-ACCESS（生产水位/生产核查） | 仍 pending · 移交维护者 · 本地三线（水位亲跑/溯源/清理）已全闭合，生产侧属独立开账 |
| 快照备份保留期 | 留本机 backups/ · 维护者自行裁定保留/清理（本地开发库口径，恢复价值随时间递减） |

## 六、维护者 checklist

- [x] 验收核验完毕（TC-OC-1~6 全 PASS 零假绿）
- [x] 备份硬闸实证（sha256 双端一致+tar 可读 · 事故恢复后复验一致）
- [x] dry-run 逐集相等 · 白名单批删零越界
- [x] 删后核验 verdict=match 0/0/0
- [x] PR 合并（squash 6ee1f61）· 归档 done/ · README 登记 · 50 invoke 落盘
