# Task：检索层长自然语言 query 零命中（针对性分析 · 非修复）

> **状态**：active（draft · 待人审）  
> **类型**：技术债 / 检索质量 · **分析型 task（只诊断与出报告，不改码）**  
> **来源**：lg_rag Phase 3 40 验收中 G37 诊断（2026-08-21）  
> **关联**：`app/ops/rag/`（hybrid_recall / FTS / dense）· `evals/golden/queries_v1.yaml`  
> **实现仓**：本仓  
> **分支**：另开 `task/retrieval-longquery-analysis`（启动时再切）

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `retrieval-longquery-analysis` |
| **test_strategy** | `n/a`（分析型；产出为报告） |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **wiki_delta** | `n/a`（发现可沉淀到 RAG 相关文档时另议） |
| **review_hat** | `20` |
| **required_invoke_hats** | `10` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | pending | 22-R1 | 维护者确认分析范围 |

---

## 背景与证据

Phase 3 漏召回 eval 中 G37 三轮均未改善，深挖确认**检索层对长自然语言 query 零命中**：

| query | hits | top |
|---|---|---|
| `readPullRequest` | 2 | issue 87（期望证据）✓ |
| `readPullRequest ENOTDIR` | 1 | issue 87 ✓ |
| G37 原始整句（中文包裹 + 复合三问） | **0** | — |

证据存在且精确词可命中，但中文叙述包裹的长句完全零命中。同类 case：golden 中多条 `expect_relevance: weak` 的 zh2zh 复合问（G57/G62/G64/G65/G71 等 eval 中也呈零命中/低 kept）。

**目标（完成态）**：

- [ ] 定位零命中根因层：dense  embedding 稀释 / FTS 中文分词与英文 token 混排 / 融合排序门槛，逐项实验拆解
- [ ] 量化影响面：golden 全集中受同一根因影响的 case 清单与占比
- [ ] 修复方案候选对比（不改码）：如 query 预处理抽词、FTS 配置、融合权重、chunk 策略；各方案成本/风险/预期收益
- [ ] 分析报告落盘 `reports/`，供后续修复 task 立项

**不做**：不改任何代码（含实验性改动——实验用一次性脚本放 `scripts/` 可议）；不动 golden 语义；不做修复实施。

## failure_paths

| 触发 | 行为 |
|---|---|
| 根因跨多层叠加 | 报告分层归因，修复方案按层拆解 |
| 实验需临时脚本 | 一次性脚本允许落 `scripts/` 并注明 disposable |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-21 | 初版（AI 起草 · 待人审）：源自 lg_rag Phase 3 G37 诊断；维护者指示「先简易 task，专门分析不修复」 |
