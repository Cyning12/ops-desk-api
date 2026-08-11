# Task：金样查询集 v1（真实 query 生成 · R-4 评测与 A/C 对比共用）

> **状态**：active（draft · 待人审）  
> **类型**：评测资产（数据任务）  
> **关联**：契约 `rag-knowledge-contract-v1.md` Q5/Q6 · `experiments/rag_compare/` · R-4 eval runner  
> **合入**：走 PR（禁直推 master）

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `golden-query-set-v1` |
| **test_strategy** | `required` |
| **test_strategy_note** | runner 能加载并跑通查询集；四象限覆盖断言 |
| **code_quality_bar** | `not_applicable`（数据任务） |
| **graph_change_layer** | `none` |
| **wiki_delta** | `n/a` |
| **orchestration** | 抽样 → LLM 生成 → 人审标注 → runner 验证 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | pending | 22-R1 | 维护者确认规模与标注口径 |

### H6 人节点

| 节点 | 人必须交付 |
|------|-----------|
| expect_hit 标注 | LLM 生成的每条 query，人核对期望命中文档 |
| 负样本撰写 | 语料中不存在的事，人写（防泄漏进语料） |
| 四象限配比 | 人审定 40 条的分布 |

---

## 背景与目标

R-4 评测与 A/C（zhparser vs 稀疏向量）对比都需要一套**有代表性的真实查询集**。
G01–G05 全是单文档（2720）多角度，测不出语料区分度（契约 Q5 评审注记已记缺口）。

**产出**：`evals/golden/queries_v1.yaml`——40 条分象限标注的查询（G01–G05 从契约迁入同格式）。

## 规模与配比（待人审）

| 象限 | 条数 | 说明 |
|------|------|------|
| ZH问 → EN文档 | 10 | 跨语言主战场（Q6 裁决闸门的数据源） |
| ZH问 → ZH/混合文档 | 10 | 未来中文为主的主象限 |
| EN问 → EN文档 | 10 | 基线对照 |
| 负样本拒答 | 10 | 语料不存在的事，期望最高评级 ≤ weak → 拒答 |

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

- [ ] 40 条入库 `evals/golden/queries_v1.yaml`（含迁入的 G01–G05）
- [ ] 四象限配比符合上表
- [ ] 每条 expect_hit 经人核对（抽查率 100%）
- [ ] **评测卫生**：文件登记含金样原文清单，runner 断言时过滤对应文档（自引用污染规则）
- [ ] runner 加载跑通（报告含分象限 recall@5）

**不做**：

- 不追求条数（40 条够了再扩，质量优先）
- 不把负样本写进任何会被灌库的文档（防泄漏）
- 不在本任务实现 A/C 臂改造（属后续对比任务）

## 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| LLM 生成质量差（问题不像人话） | 该批弃用，调 prompt 重生成 | Y |
| expect_hit 标注分歧 | 以人复核为准，分歧条目记 note | Y |

## 修订

| 日期 | 说明 |
|------|------|
| 2026-08-11 | 初版（AI 起草 · 待 HG-TASK-DRAFT 人审） |
