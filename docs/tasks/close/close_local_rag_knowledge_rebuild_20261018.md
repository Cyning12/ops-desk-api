# CLOSE：local-rag-knowledge-rebuild（B2 · 本地 RAG 知识库重建）

> 关账日期：2026-10-18 · 关账人：00（维护者 m01159 授权链自动推进）
> 体例承 [close_hitl_resume_async_20261015.md](close_hitl_resume_async_20261015.md)

## 一、任务信息

| 项 | 值 |
|---|---|
| task | [task_local_rag_knowledge_rebuild.md](../done/task_local_rag_knowledge_rebuild.md)（已归档 done/） |
| 性质 | 本地运维重建（含写动作 PG+Qdrant 双侧重灌 · **零落码 40 单棒**） |
| 上游 | 本地向量数据态三线闭合后双零对齐无知识可检 · 维护者 m01159 自动推进队列 B2 |
| PR | [#276](https://github.com/Cyning12/ops-desk-api/pull/276) MERGED · squash `8ac8ec0` · CI 4/4 绿 · 13 文件 +646/−0 全 docs/reports |
| 审查 | R1 [task_local_rag_knowledge_rebuild_audit_R1_20261018.md](../../harness/reviews/task_local_rag_knowledge_rebuild_audit_R1_20261018.md) 签收零阻塞 nit×4 照登 · 锚点 13/13 命中 |
| 闸 | HG-TASK-DRAFT/HG-AUDIT-R1 approved（m01159 授权链 00 代录 · 签注 embedder=api bge-m3 · docs roots=05-plan+contracts）· HG-GRAPH-MODULES n/a |

## 二、验收核验（TC-RK-1~7 全 PASS · 零假绿）

| 项 | 结果 |
|---|---|
| 三对照 | chunks_written 8429(恢复轮)+219(docs) == **PG 8648** == **Qdrant 8648** |
| 水位复跑 | [vector_waterline_local_20261018T072903Z.yaml](../../reports/vector_waterline_local_20261018T072903Z.yaml)：verdict=**match** · diff=0 · DLQ=0 · degraded=false |
| 规模裁定 | 8648 ∈ [6000,12000]（对照历史常态 8574 · +0.9%） |
| 检索抽检 | rag_smoke 因环境缺 langchain 降级纯向量检索显式标注（FP-7 路径）· G01 top-1/top-3 双中锚 issue#2720（0.7431/0.6958） |
| 零越界 | app/scripts/alembic/compose 零 diff · pytest 13 passed · task lint PASS |

## 三、过程偏差照登（三条均零落码解决 · 诚实录）

1. **httpx InvalidURL ':1]'**：shell NO_PROXY 含 [::1] 触发代理解析 bug → 清洗 NO_PROXY 解决（非仓码缺陷 · 与前棒代理污染同类环境面）。
2. **ApiEmbedder 无内部批切**：ingest.py:225 全量单请求 ~8.6k 文本超时（探测实证 API 单批上限≈500）→ 分批 --limit 75 步递增（25/25 步 · 248s · 利用 content_hash 水位幂等跳过）。**内部批切改码建议另立 task**。
3. **40 棒编排事故**：首轮收尾 standalone --only docs 触发墓碑对账删 2736 单元（源表零损失 · DLQ=0 · 影子删正常）→ 纠偏轮全量恢复并实证终态一致 · 返工 +2.9M tokens 照登。
4. 嵌入成本：总 17077 chunks ≈ 6.0M tokens（含返工）· 速率 ~34 chunks/s。

## 四、产物

- 重建报告 [local_rag_knowledge_rebuild_20261018T0731Z.md](../../reports/local_rag_knowledge_rebuild_20261018T0731Z.md)
- 40 invoke + 证据 8 类：docs/harness/invokes/by-task/local-rag-knowledge-rebuild/

## 五、遗留移交

| 项 | 去向 |
|---|---|
| ApiEmbedder 内部批切 | 另立 task 候选（ingest.py:225 全量单请求超时面） |
| HG-EVAL-LIVE-RUN rag 73 条真跑 | **前置已备**（知识库 8648 就位）· 闸 pending 待维护者授权窗口 |
| HG-PROD-READONLY-ACCESS 生产水位 | pending · 本地重建不与生产外推 |

## 六、维护者 checklist

- [x] 验收核验完毕（TC-RK-1~7 全 PASS 零假绿）
- [x] 三对照 8648 逐数相等 · 水位 match
- [x] 规模落裁定区间 · 越限即停纪律未触发
- [x] 事故与返工成本诚实照登
- [x] PR 合并（squash 8ac8ec0）· 归档 done/ · README 登记 · 50 invoke 落盘
