# RAG 检索方案对比评估报告（A/C/D vs Normal Baseline）

> **落盘说明**：下文「原文」为 2026-08-12 第三方对照稿，作决策参考归档。  
> 「勘误」与「下一步」为维护者对照 `reports/r4-*.yaml` 实测后的修订意见，**以勘误为准读结论**。

| 项 | 值 |
|----|----|
| 报告日期 | 2026-08-12 |
| 评估对象 | `ops_knowledge_chunks` (N=8,574) |
| 嵌入模型 | BAAI/bge-m3 |
| 金样 | 73 条（zh2en / zh2zh / en2en / negative） |
| 原始报告 | `reports/r4-2.yaml`（Normal）· `r4-A.yaml` · `r4-C.yaml` · `r4-D.yaml` · 早期 `r4-1.yaml` |

---

## 原文（第三方对照稿 · 归档）

RAG 检索方案对比评估报告（A/C/D vs Normal Baseline）  
报告日期：2026-08-12  
评估对象：ops_knowledge_chunks (N=8,574)  
嵌入模型：BAAI/bge-m3  
评估器：qwen3.7-max  
黄金测试集：73 条（含 zh2en/zh2zh/en2en/negative 四象限）  
RRF 参数：k=60，两路 1:1 等权

### 一、实验背景与目的

本实验旨在解决一个核心痛点：simple 分词器对中文 Query 分词失明，导致关键词路（keyword_hits）几乎无法召回中文内容。我们设计了四个方案进行对比，以评估各方案对中文检索 recall@5 的提升效果及副作用。

| 方案代号 | 方案名称 | 核心机制 |
|----------|----------|----------|
| Normal | 基线方案 | simple 分词器 + 无额外优化 |
| D | Glossary 补丁 | 中文 Query 手动扩英文候选词喂给 simple 分词器 |
| A | zhparser 中文分词 | 影子库部署 zhparser 扩展，fts_tokens 用 chinese 配置重建 |
| C | 稀疏向量 / 替代方案 | 不依赖 fts_tokens，采用其他检索机制（数据同构，实现不同） |

### 二、核心指标总览

| 方案 | 总通过率 | 变化 | 关键象限 | 问题记录 |
|------|----------|------|----------|----------|
| Normal | 52/71 (73.2%) | — | zh2en 19/25；zh2zh 17/20；en2en 15/16；negative 10/10 | 稳定，无异常 |
| D | 54/73 (74.0%) | ↑ +0.8pp | zh2en 19/26；zh2zh 17/20；en2en 15/16；negative 11/11 | 边际增益极微 |
| A | 54/73 (74.0%) | ↑ +0.8pp | 同上 | 排序质量退化（G25/G29/G31 exact→relevant/weak） |
| C | 53/73 (72.6%) | ↓ -0.6pp | zh2en 18/26；zh2zh 19/20；en2en 15/16；negative 9/11 | zh2zh 最高，negative 误报 2 条 |

### 三、各方案详细解读（原文摘要）

1. **Normal**：语义路扛大旗；关键词路几乎瘫痪；最安全零运维基线。  
2. **D**：投入产出比最低，不建议继续。  
3. **A**：召回未涨、排序反降；不推荐上线。  
4. **C**：zh2zh 最强，但拒答失控不可接受；保留长期候选，需拒答阈值。

### 四、综合结论（原文）

当前最佳：维持 Normal，放弃 A/C/D 硬件扩展。  
痛点定位：不在分词，在「语义路排序精度不足」——关键词路无论怎么优化绝对命中率仍极低，优化主路径比修补辅路径更有效。

### 五、下一步行动建议（原文）

- 短期：HyDE 查询改写  
- 中期：Cross-Encoder Reranker（bge-reranker-v2-m3）  
- 长期：C 安全化（拒答阈值）后再验  

### 六～七（原文）

样本量小、confidence:low；grader 版本可能偏移。  
推荐：Normal + HyDE + Reranker；淘汰 D；搁置 A；C 长期候选。

---

## 勘误（对照 `reports/r4-*.yaml` · 2026-08-12）

| # | 原文说法 | 实测 | 影响 |
|---|----------|------|------|
| 1 | Normal negative **10/10** | `r4-2`：**9/10**（G67 fail） | 基线并非「拒答满分」 |
| 2 | A/C/D grader 均为 `…-2026-05-20`，Normal 为 `qwen3.7-max` | **仅 C** 为 `qwen3.7-max-2026-05-20`；A/D 与 Normal 同为 `qwen3.7-max` | 尺度偏移主要威胁 **C vs 基线**，不是 A/D |
| 3 | 「无论哪种关键词优化，keyword 命中率仍极低」 | **C：`keyword_hits` 非空 73/73**（每条约 10 条，且大量与 dense 不重叠）；A/D/基线仍约 5/73（contract 污染） | **C 已证明第二路可活**；不能据此否定「辅路径」 |
| 4 | C 的收益叙事偏「中文理解更深」 | C 第二路 = **bge-m3 sparsevec**（`RAG_SECOND_PATH=sparse`）；zh2zh +10pp（17→19）主要来自 sparse 块进 RRF（如 G36/G37） | 机制应写清，避免与「神秘替代方案」混淆 |
| 5 | 报告头 `confidence:low` / `comparability:not_comparable` 暗示各跑不可比 | runner **写死占位**（`run_eval.py`），各报告相同 | **不要用这两字段做方案裁决** |
| 6 | 「痛点全在语义路排序」 | 部分成立（dense 已扛大部分 recall）；但 C 说明 **lexical/sparse 仍能动 zh2zh**，代价是噪声与 negative 回退 | 下一步应是「主路强化 + 辅路控噪」，不是二选一 |

**C negative 失败样例（红线属实）**：G62、G66 → `gate_action=answer_partial`，top 命中相关块导致拒答失败。

---

## 下一步改进方案（再思考）

### 裁决（承接 Q6 task 口径 + 勘误）

| 方案 | 裁决 | 理由 |
|------|------|------|
| Normal（dense + FTS/simple） | **现网默认保留** | 总 pass 稳；运维零；辅路虽死但 dense 兜底 |
| D glossary | **不继续投入**；开关常闭可留 | +0pp 级；维护贵 |
| A zhparser | **不上生产**；入口保留 | recall 不动 + 运维重；可留对照 |
| C sparse | **不上默认**；开关保留；优先「控噪」再谈默认 | zh2zh 达标线（+10pp）但 negative −；总 pass 未赢 |

### 推荐路线（按 ROI，可并行但有次序）

**P0 · 不改召回、先抬排序（中期原文的 Reranker 提前）**

- RRF/ dense top-20（或 top-30）→ **bge-reranker-v2-m3** → top-5 再进 prompt。  
- 直接针对「exact→relevant/weak」与 C 噪声挤榜；**不改库、不加第二路复杂度**。  
- 验收：同金样对比 `best_relevance` 分布 + recall@5 + negative；对标 `r4-2`。

**P1 · 查询侧（原文 HyDE 可做，但排在 Reranker 后或小样先行）**

- HyDE / 轻量 query rewrite：延迟与费用更高，且改写质量方差大。  
- 建议：先在 **zh2zh fail / zh2en fail 子集**（含 G39、G56 类）离线 A/B，再决定是否进主链。  
- 勿与 `RAG_KW_EXPAND`、sparse 默认同时全开，避免因子纠缠。

**P2 · C 安全化（仅当 P0 后仍缺冷门实体）**

不要先「加一套拒答 LLM」，优先便宜旋钮：

1. **降权**：sparse RRF 权重低于 dense（非 1:1）。  
2. **截断**：sparse 只取更小的 top-k′，或加内积分数阈值。  
3. **门控**：仅当 dense 最高分低于阈值 τ 时启用 sparse（冷启动补召回）。  
4. 再验 negative（G62/G66）与 zh2zh 是否仍 ≥ 基线 +5～10pp。

**P3 · 评测基建（便宜、高杠杆）**

- C 与基线 **同一 grader 字符串** 重跑或子集复核（消除版本偏移争议）。  
- 金样扩到 200+ 前，裁决只标 `confidence: low`（诚实），但对照仍用分象限差分。  
- runner 若以后改 `comparability`，应真实计算「相对哪份 baseline」，勿继续写死。

### 明确不做（本阶段）

- 不为 +1pp 再堆分词器 / 同义词表。  
- 不把 C 直接改成生产默认。  
- 不并行开 HyDE + sparse 默认 + glossary（无法归因）。

### 一句话

**现网维持 Normal；下一刀优先 Cross-Encoder 重排；辅路径（sparse）只做控噪实验；HyDE 小样验证后再谈上线。**

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-08-12 | 落盘第三方对照稿 + 勘误 + 下一步再思考 |
