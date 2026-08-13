# Task：金样查询集 v1（真实 query 生成 · R-4 评测与 A/C 对比共用）

> **状态**：completed  
> **类型**：评测资产（数据任务）+ R-4 eval runner  
> **关联**：契约 `rag-knowledge-contract-v1.md` Q5/Q6 · `experiments/rag_compare/` · R-4 eval runner  
> **合入**：走 PR（禁直推 master）  
> **git_branch**：`task/golden-query-set-v1`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `golden-query-set-v1` |
| **git_branch** | `task/golden-query-set-v1` |
| **test_strategy** | `required` |
| **test_strategy_note** | runner 能加载并跑通查询集；四象限覆盖断言；卫生过滤单测 |
| **code_quality_bar** | `standard` |
| **graph_change_layer** | `none` |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 评测资产 + runner；不改 coding_wiki 正文 |
| **graph_delta** | `none` |
| **graph_delta_note** | 评测资产 / runner；不改业务图谱节点或边 |
| **invoke_retention_profile** | `minimal` |
| **required_invoke_hats** | `30` |
| **orchestration** | 抽样 → LLM 生成 → 人审标注 → runner 验证 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 维护者 2026-08-11 签收：规模放宽至 71 条（原 40）+ 四象限配比以 yaml 为准；同日 G67 双审修订为 73（26/20/16/11） |
| HG-AUDIT-R1 | approved | 30 | 维护者 2026-08-11 签收；审查文 `docs/harness/reviews/task_golden-query-set-v1_audit_R1_20260811.md` |

### H6 人节点

| 节点 | 人必须交付 |
|------|-----------|
| expect_hit 标注 | LLM 生成的每条 query，人核对期望命中文档 |
| 负样本撰写 | 语料中不存在的事，人写（防泄漏进语料） |
| 四象限配比 | 人审定分布：初签 71（25/20/16/10）；G67 双审后定稿 73（26/20/16/11，yaml 为准） |

---

## 背景与目标

R-4 评测与 A/C（zhparser vs 稀疏向量）对比都需要一套**有代表性的真实查询集**。
G01–G05 全是单文档（2720）多角度，测不出语料区分度（契约 Q5 评审注记已记缺口）。

**产出**：`evals/golden/queries_v1.yaml`——73 条分象限标注的查询（G01–G05 从契约迁入同格式）+ `evals/golden/run_eval.py`。

## 规模与配比（定稿 2026-08-11 · 73 条）

| 象限 | 条数 | 说明 |
|------|------|------|
| ZH问 → EN文档 | 26 | 跨语言主战场（含 G73：157 cron/reminder 转正） |
| ZH问 → ZH/混合文档 | 20 | 未来中文为主的主象限 |
| EN问 → EN文档 | 16 | 基线对照 |
| 负样本拒答 | 11 | 语料不存在的事；含 G72 PPT 替换样本 |

初签 71（25/20/16/10）；同日 G67 双审：原番茄钟负样本语义近亲 → 换录音转写/PPT，157 转正为 G73 → **71+2=73**。

## 三路来源

1. **真实历史**：本地 `ops_runs.query` 62 条 + 生产库导出（人跑 SQL 导出脱敏）——真实用户问法
2. **LLM 生成**：从语料抽样 issue（覆盖纯英/混合/中文）→ LLM 生成用户口吻问题 → **人审标注 expect_hit**
3. **手写**：负样本必须人写（写了就可能进语料，人控制措辞）

## 格式（沿用契约 Q5 字段 + 象限标签）

```yaml
- id: G06
  query: "……"
  quadrant: zh2en        # zh2en | zh2zh | en2en | negative
  expect_hit: { source_type: issue, source_id: "2676" }
  assert: { recall_at: 5, min_relevance: relevant, citation_in_hits: true }
  expect_relevance: relevant
  note: "来源：真实历史 ops_runs / LLM 生成人审 / 手写"
```

## 完成态

- [x] 73 条入库 `evals/golden/queries_v1.yaml`（含迁入的 G01–G05；G67 双审后定稿）
- [x] 四象限配比符合上表（26/20/16/11）
- [x] 每条 expect_hit 经人核对（抽查率 100% · 2026-08-11 人签；G72/G73 同日双审）
- [x] **评测卫生**：`evals/golden/hygiene_denylist.yaml` + runner 断言前过滤含金样原文 hit（契约#13）
- [x] runner 落地：`evals/golden/run_eval.py`（单测覆盖加载/卫生/断言/报告；首跑报告 `reports/r4.yaml`）

**不做**：

- 不追求条数膨胀（质量优先；本波定稿 73）
- 不把负样本写进任何会被灌库的文档（防泄漏）
- 不在本任务实现 A/C 臂改造（属后续对比任务）

## 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| LLM 生成质量差（问题不像人话） | 该批弃用，调 prompt 重生成 | Y |
| expect_hit 标注分歧 | 以人复核为准，分歧条目记 note | Y |

---

## 验收标准

- [x] `evals/golden/queries_v1.yaml` 加载条数 = 73，象限 26/20/16/11
- [x] `evals/golden/run_eval.py` + `hygiene_denylist.yaml` 落地
- [x] `.venv/bin/pytest tests/test_golden_eval_runner.py` 全绿（含 `test_load_golden_73`）
- [x] 首跑报告 `reports/r4.yaml` 存在（首跑 71 时代；后续对照报告沿用同 runner）

---

### 自检结论（执行者）

| 项 | 内容 |
|---|---|
| **日期** | 2026-08-13（关账复核） |
| **yaml** | 73 条 · zh2en=26 / zh2zh=20 / en2en=16 / negative=11 |
| **pytest** | `.venv/bin/pytest tests/test_golden_eval_runner.py` → **13 passed** |
| **报告** | `reports/r4.yaml` 存在（summary pass 37/71 为首跑）；下游 r4-A/C/R 已按 73 对照 |
| **闸** | HG-TASK-DRAFT / HG-AUDIT-R1 = approved；`invoke_retention_profile=minimal` → hats=`30` 已落盘 |
| **已知未测** | 本关账轮未重跑完整 R-4 线上 retrieve（属后续臂任务实跑） |

### KPI

| 项 | 分 |
|---|---|
| Task_KPI% | 100 |

## 修订

| 日期 | 说明 |
|------|------|
| 2026-08-11 | 初版（AI 起草 · 待 HG-TASK-DRAFT 人审） |
| 2026-08-11 | 人签闸；规模 71；落地 R-4 runner + 卫生 denylist + 单测 |
| 2026-08-11 | G67 双审 → 73（commit cc4f30f）；task 卡关账前对齐 |
| 2026-08-13 | CLOSE：slug 文件名对齐、验收/自检/KPI/graph_delta_note 补齐后 `task close` |
