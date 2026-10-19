# CLOSE：rag-golden-eval-live-run（R-4 结案真跑 + R-5 Demo 证据表 · 2026-10-19）

> 关账日期：2026-10-19 · 关账人：00（goal-eb568703 · HG-EVAL-LIVE-RUN 已签）· 体例承 close_hitl_resume_async_20261015.md

## 一、任务信息

| 项 | 值 |
|---|---|
| task | [task_rag_golden_eval_live_run.md](../done/task_rag_golden_eval_live_run.md)（已归档 done/） |
| 性质 | R-4 四类 golden 结案级真跑 + R-5 Demo 证据表（**零落码 40 单棒** · 承 task_rag_golden_eval_r4_r5 PR #262 移交） |
| PR | [#280](https://github.com/Cyning12/ops-desk-api/pull/280) MERGED · squash `4ab5f3a` · CI 4/4 绿 |
| 审查 | R1 [task_rag_golden_eval_live_run_audit_R1_20261019.md](../../harness/reviews/task_rag_golden_eval_live_run_audit_R1_20261019.md) 通过零阻塞（锚点 14/14） |
| 闸 | 四闸 approved 含 **HG-EVAL-LIVE-RUN**（授权链 00 代录 · 真 LLM key+配额消耗授权）· HG-PROD-READONLY-ACCESS pending 照登零涉生产 |

## 二、交付清单

- `reports/r4_live_20261019T032150Z.yaml`（全量真跑产物 · 73/73 partial=false）
- `reports/r4_final_live_20261019T032150Z.{yaml,md}`（结案报告七节齐全 · §7 签字位留维护者）
- `reports/demo_evidence_20261019T033800Z.md`（R-5 Demo 证据 4 条四象限齐：G01/G21/G41 + G62 拒答演示 · 契约 4c 文案三面逐字一致）
- `invoke_20261019_40_live_run.md` + 证据附件（617 行真跑日志 + 冒烟 yaml）· 10/20 invoke + R1 审查文随档
- **零落码零 diff**：app/scripts/alembic/管线四件/双模板/契约 git diff 空输出实证（TC-LR-5）

## 三、验收核验（TC-LR-1~6 全 PASS）

- TC-LR-1 前置：双容器 Up healthy · SILICONFLOW_API_KEY 存在（值零落档）· **PG 8648 == Qdrant 8648**（green/dim=1024/Cosine）· 现集 73 条（zh2en=26/zh2zh=20/en2en=16/negative=11）
- TC-LR-2 全量真跑：冒烟 3 条过 → 全量 7/73 处 LLM 中断 EXIT=1 如实记（incomplete chunked read · 本地代理长连接不稳）→ 全洗代理直连 + --resume 续跑 → **73/73 · partial=false · ≈56.6min** · 配额台账照登（embed×83 + rerank×73 + grader×73）
- TC-LR-3 结案报告七节齐全 · pytest 12+13 复跑全绿零新增红
- TC-LR-4 Demo 证据 4 条四象限齐 · case id 交叉引用 · 复现命令可执行
- TC-LR-6 留档+lint PASS

**核心判定**：zh2en **MET** —— **19/26（73.08%）** vs 门槛 ≥1/3 · n=26 · Wilson 95% CI=[0.54, 0.86] · **confidence=low（小样本老实标）**。拒答正确率 **10/11（90.91% · CI=[0.62, 0.98]）**。误答=G63；疑似误拒=G03/G05/G37/G44/G47/G49/G56/G57/G61（9 条供复核）。verdict 54/73 · 19 条 fail 全列 §4。**整体判定建议「有条件通过」**。

## 四、偏差与照登

1. NO_PROXY/no_proxy shell 双写 → 先例单洗不足需双洗（增量教训）。
2. 本地代理长连接不稳 → 真跑建议全洗直连（7/73 中断实证）。
3. demo_evidence_TEMPLATE.md 示例 --only/--report 参数现版 run_eval.py 不支持（模板 nit 上抛 · 零 diff 未改模板）。
4. 旧过程稿 18 份（71 条）未冒充结案（FP-9 · 现集 73 条为准）。
5. 契约漂移=**零漂移**（§4c 三面逐字一致 + 上游 TC-R4-6 在案）。

## 五、遗留移交

| 项 | 去向 |
|---|---|
| 结案报告 §7 签字位（有条件通过定稿） | 维护者签字 |
| G63 误答 + 9 疑似误拒归因复核 · 金标校准复核 | 另 task 候选（维护者定夺） |

## 六、维护者 checklist

- [x] 73/73 全量真跑 partial=false（中断处置如实记未凑数）
- [x] zh2en MET 19/26（Wilson CI+confidence=low 老实标）
- [x] 拒答正确率 10/11 · 误答/误拒清单照登
- [x] 结案报告+Demo 证据四象限齐
- [x] 零落码零 diff 实证
- [x] PR 合并 · 归档 done/ · README 登记 · 50 invoke 落盘
