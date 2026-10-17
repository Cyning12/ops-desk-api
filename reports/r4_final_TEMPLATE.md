# R-4 结案报告模板（rag-knowledge-golden-eval · 路线 §P1-RAG R-4）

> 用法：结案评审时（HG-EVAL-LIVE-RUN approved 后）由 `evals/golden/summarize_r4.py` 生成初稿
> （`reports/r4_final_<run_slug>.{yaml,md}`），人工补齐「结论与签字」后归档。
> 本模板本身只是格式真值；不要把过程稿数值填进来冒充结案。

## 1. 运行标识

| 字段 | 值 | 说明 |
|------|----|------|
| run id | `<eval-rag-YYYYMMDD-HHMMSS-rN>` | run_eval.py 生成的运行标识 |
| 版本 / commit | `<git rev-parse HEAD 短哈希>` | 评测时工作树 commit |
| embedder | `<BAAI/bge-m3 …>` | 报告头 embed 字段 |
| grader | `<模型 + prompt 版本 v1/v2>` | 报告头 grader 字段 |
| 语料 | `ops_knowledge_chunks(N=<n>)` | 报告头 corpus 字段，N 必须显式 |
| arm / rerank | `<baseline_arm / rerank_on…>` | 报告头 arm 字段 |
| 源报告 | `reports/<rN.yaml>` | 聚合输入 |

## 2. 逐象限指标

| 象限 | n | recall@5 命中率 | min_relevance | citation_in_hits | verdict |
|------|---|-----------------|---------------|------------------|---------|
| zh2en | `<n>` | `<k>/<n>（<pct>）` | `<k>/<n>` | `<k>/<n>` | `<k>/<n>` |
| zh2zh | `<n>` | `<k>/<n>（<pct>）` | `<k>/<n>` | `<k>/<n>` | `<k>/<n>` |
| en2en | `<n>` | `<k>/<n>（<pct>）` | `<k>/<n>` | `<k>/<n>` | `<k>/<n>` |
| negative | `<n>` | n/a（分母 0） | n/a | n/a | `<k>/<n>` |

## 3. 门槛判定（路线 R-4 显式断言）

| 门槛 | 实测 | 判定 | 样本量 / confidence |
|------|------|------|--------------------|
| ZH问→EN文档 跨语言 recall@5 ≥ 1/3 | `<k>/<n>（<pct>）` | `<MET / NOT_MET / NO_DATA>` | `n=<n> · Wilson 95% CI=[lo, hi] · confidence=<low/medium>` |
| 负样本拒答正确率 | `<k>/<n>（<pct>）` | `<记录值，不设硬门槛>` | `n=<n> · Wilson 95% CI=[lo, hi]` |
| 误答（负样本未拒答） | `<G-id 列表或「无」>` | — | — |
| 疑似误拒（正样本被拒答） | `<G-id 列表或「无」>` | — | 供人工复核，不改默认参数 |

## 4. 未达成项与原因

| case | 象限 | fail_reasons | 归因（检索 / 评级 / 金标 / 语料） |
|------|------|--------------|----------------------------------|
| `<G-id>` | `<quadrant>` | `<fail_reasons>` | `<人工归因>` |

## 5. 观测口径注记（小样本老实标）

- measurement_source：`<observed / …>`；confidence：`<low/medium>`；comparability：`<not_comparable / …>`
- SPEC-evaluation-observation 真值文件在 api 仓与 workspace 仓均未检索到（照登：无实证）；
  观测三字段按路线 A-P1-3 引用口径对齐。
- ⚠️ 小样本（n<50）结论置信有限，任何「已达标」表述必须同时引用 n 与 Wilson CI。

## 6. 契约漂移

- 结论：`<零漂移 / 有漂移>`（对照 `../ops-desk-workspace/docs/contracts/rag-knowledge-contract-v1.md`）
- 若有漂移：逐条记录（契约条目 / 实现位置 / 差异）→ **FP-5 上抛维护者，本 task 不改契约、不改实现**
- 已知观察项（非漂移）：`Relevance.UNRATED` 为内部标记（level=-1，never 出现在 grader 输出），不计漂移。

## 7. 结论与签字

- R-4 整体判定：`<通过 / 有条件通过（列条件）/ 不通过>`
- 后续动作：`<调参 task / 语料补齐 task / 无>`
- 签字：`<维护者> · <日期>`（对应 HG-EVAL-LIVE-RUN 闸态）
