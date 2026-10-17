# CLOSE：vector-waterline-local-rerun（TC-WL-5 开账 · 本地/compose 亲跑向量水位核查）

> 关账日期：2026-10-17 · 关账人：00（维护者授权 m00847「合并 + 立核查 task」）
> 体例承 [close_hitl_resume_async_20261015.md](close_hitl_resume_async_20261015.md)

## 一、任务信息

| 项 | 值 |
|---|---|
| task | [task_vector_waterline_local_rerun.md](../done/task_vector_waterline_local_rerun.md)（已归档 done/） |
| 性质 | 运维实证核查 · **零改码 · 40 轨单棒** · 复用既有只读脚本与模板 |
| 上游 | `task_prod_vector_waterline_check` TC-WL-5（40 轨本地/compose 亲跑）关账移交开账 |
| PR | [#268](https://github.com/Cyning12/ops-desk-api/pull/268) MERGED · squash `e20bc4d` · CI 4/4 绿 |
| 审查 | R1 [task_vector_waterline_local_rerun_audit_R1_20261017.md](../../harness/reviews/task_vector_waterline_local_rerun_audit_R1_20261017.md) PASS 零阻塞 |
| 闸 | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸 approved（维护者 m00823 授权 00 代录 · 承 m00238 总授权） |

## 二、交付清单

| 产物 | 说明 |
|---|---|
| `reports/vector_waterline_local_20261017T123649Z.yaml` | **真实报告**（亲跑产物 · 对 `reports/vector_waterline_TEMPLATE.yaml` 逐键全中 · environment=local · disclaimer 钉死） |
| `reports/vector_waterline_local_20261017T123538Z.yaml` | 降级照登报告（首跑降级实证 · 保留作证） |
| `docs/harness/invokes/by-task/vector-waterline-local-rerun/invoke_20261017_40_rerun.md` | 40 棒 invoke 留痕 |
| 既有资产零改码 | `scripts/check_vector_waterline.py`（366 行只读）/ runbook §2 / 模板 / 桩测 13 测全复用 |

## 三、验收核验（TC-LR-1 ~ TC-LR-6 全 PASS · 零假绿）

| TC | 核验结果 |
|---|---|
| TC-LR-1 容器环境 | PASS · db + qdrant Up healthy · qdrant:v1.19.0 镜像逐字一致 |
| TC-LR-2 runbook §2 命令逐字亲跑 | PASS · exit 0 |
| TC-LR-3 真实报告对模板逐键全中 | PASS · environment=local · disclaimer 钉死 |
| TC-LR-4 降级三态真实生效不假绿 | PASS · 首跑降级如实落盘 no_evidence 未粉饰（见 §四.1） |
| TC-LR-5 桩测回归 | PASS · pytest tests/test_check_vector_waterline.py 13 passed |
| TC-LR-6 零越界 | PASS · 零 app/ 改码 · 零 git 范围外操作 |

**关键实录**：PG `ops_knowledge_chunks` **0 行** · DLQ 空 · Qdrant `ops_knowledge` **8574 points** · count_diff=-8574 · verdict=**mismatch**（Qdrant 独有 8574 · PG 独有 0）。

## 四、偏差与照登

1. **首跑降级照登（不假绿 · 非脚本 bug）**：执行机代理变量 `NO_PROXY` 含 `[::1]` 炸 httpx `InvalidURL: Invalid port ':1]'` → 剥代理重跑双侧齐全。降级报告 `123538Z` 保留作证，零改码。
2. **容器复用照登**：复用运行中 db+qdrant 容器（Up 24h healthy），未重建，如实记录。
3. **mismatch 数据态**：Qdrant 8574 vs PG 0。疑为墓碑/脏点（历史写入未清）或本地 DB 重建清空的正常态，**本 task 不处置**，FP-7 上抛 → 维护者授权另立 `task_local_vector_data_state_audit` 核查溯源（m00847）。

## 五、遗留移交

| 项 | 去向 |
|---|---|
| mismatch 8574 来源核查（墓碑点 vs DB 重建 · 处置方案另行裁定） | 另立 `task_local_vector_data_state_audit`（10-task 起草中 · m00847 授权） |
| `HG-PROD-READONLY-ACCESS`（生产水位真跑） | 仍 pending · 移交维护者（承 `task_prod_vector_waterline_check` 关账开账） |

## 六、维护者 checklist

- [x] 验收核验完毕（TC-LR-1~6 全 PASS 零假绿）
- [x] 真实报告落盘且对模板逐键全中
- [x] 降级照登不假绿（首跑降级报告保留作证）
- [x] 零改码零越界核验
- [x] mismatch 上抛另立核查 task（m00847 授权）
- [x] PR 合并（squash e20bc4d）· 归档 done/ · README 登记 · 50 invoke 落盘
