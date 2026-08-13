# Task：RAG 第二路 C 臂——bge-m3 稀疏向量对照实验

> **状态**：completed  
> **类型**：对照实验（契约 Q6 裁决链路 · A 已否决上生产 · C 实测结案）  
> **关联**：契约 Q6 · `experiments/rag_compare/REPORT_q6_arms_vs_baseline_20260812.md` · 基准 `reports/r4-2.yaml` · A `reports/r4-A.yaml` · C 定稿 `reports/r4-C.yaml` · D `reports/r4-D.yaml`  
> **分支**：`task/rag-sparse-arm-c`（自 `master` 新开；勿在 A 臂分支上直接改 C 实现）

---

## Harness 元信息


| 字段                           | 值                                                        |
| ---------------------------- | -------------------------------------------------------- |
| **task_slug**                | `rag-sparse-arm-c`                                       |
| **git_branch**               | `task/rag-sparse-arm-c`                                  |
| **test_strategy**            | `required`                                               |
| **test_strategy_note**       | sparsevec 灌满断言 + r4-C 与 r4-2/r4-A/r4-D 分象限对比；runner 逐条落盘 |
| **code_quality_bar**         | `standard`                                               |
| **graph_change_layer**       | `none`                                                   |
| **graph_delta**              | `none`                                                   |
| **graph_delta_note**         | 对照实验：影子列/env 开关；不改 G-L1 模块边界与对外契约路由                      |
| **wiki_delta**               | `n/a`                                                    |
| **wiki_delta_note**          | 对照实验（稀疏向量路）；不改 coding_wiki 正文                            |
| **review_hat**               | `20`                                                     |
| **required_invoke_hats**     | `10,30`                                                  |
| **invoke_retention_profile** | `minimal`                                                |
| **orchestration**            | 单 task · A 已结案后执行                                        |




### 人工闸


| human_gate_id | status   | blocks_hats | 说明                                  |
| ------------- | -------- | ----------- | ----------------------------------- |
| HG-TASK-DRAFT | approved | 22-R1       | 维护者确认 C 臂方案（含 A 否决后的判读口径与 A 入口保留策略） |
| HG-AUDIT-R1   | approved | 30          | 维护者 2026-08-12 签收；审查文 `docs/harness/reviews/task_rag_sparse_arm_c_audit_R1_20260812.md` |


---



## 目标

同一 runner、同一金样（73 条）、同一嵌入模型（bge-m3），**只替换第二路**：tsvector 关键词路 → bge-m3 **稀疏向量路**（lexical weights），验证「免分词 + 跨语言词项扩展」能否修复第二路；产出 `reports/r4-C.yaml`，支撑 Q6 **采 C / 维持 dense+glossary** 裁决。

## 前置事实（含 A 臂实测）


| 项        | 状态                                                                                                                         |
| -------- | -------------------------------------------------------------------------------------------------------------------------- |
| A 臂结论    | zh2zh recall@5 **+0pp**（17/20）；kw 仍几乎全死（zh2zh 0/20）→ **弃 A 上生产**                                                           |
| 病灶本质     | 第二路（lexical）未贡献；dense 已撑起大部分 recall；换分词不够                                                                                  |
| pgvector | 0.8.5，已支持 `sparsevec` + 内积/距离算子（本地已验版本）                                                                                    |
| bge-m3   | 多密度：dense + sparse lexical weights；`sentence-transformers` **不暴露** sparse → 需 **FlagEmbedding**                            |
| 机制优势     | 稀疏路自带语义词项扩展、多语言训练 → 理论上覆盖 ZH→EN/混合，**绕开分词**                                                                                |
| A 入口保留   | **不删** `Dockerfile.pg-zhparser` / `experiments/rag_compare/zhparser_arm_a/` / `RAG_FTS_CONFIG`；生产默认仍 `simple`；C 用独立开关切换第二路 |
| runner   | 已支持 `--out` 逐条落盘 · `--resume` · `--from-log`（额度耗尽可续）                                                                       |




## 与 A 的关系（入口策略）


| 开关                    | 含义                                       | 默认                     |
| --------------------- | ---------------------------------------- | ---------------------- |
| `RAG_FTS_CONFIG`      | tsvector regconfig（`simple` / `chinese`） | `simple`               |
| `RAG_KW_EXPAND`       | glossary 展开（D 臂）                         | 评测 C 时建议 `false`（变量隔离） |
| `RAG_SECOND_PATH`（拟定） | `fts`（现状）| `sparse`（C 臂）                 | `fts`                  |


- C 实现时：**加** sparse 路与 `RAG_SECOND_PATH=sparse`，**不移除** FTS 路与 A 相关代码/脚本。  
- 评测 C：第二路走 sparse；A 的 chinese FTS 不参与本轮对照。



## 实施步骤

1. **依赖**：实验期 `uv pip install FlagEmbedding`（或隔离 venv）；定稿再入 `pyproject` / 可选 extra
2. **影子列（不碰生产主路径）**：本地/影子库 `ALTER TABLE … ADD COLUMN sparse_embedding sparsevec` + 合适索引（按 pgvector 文档选 `<#>` / 内积算子与索引类型）
3. **稀疏重嵌**：`BGEM3FlagModel` 批算 8,574 chunks 的 lexical weights → 写 `sparse_embedding`；**不动** dense `embedding`
4. **查询路**：`retrieve.py` 增加 sparse 路 SQL；`RAG_SECOND_PATH=sparse` 时第二路用 sparse，否则保持现有 FTS（含 `RAG_FTS_CONFIG`）
5. **跑评测**（逐条落盘）：

```bash
export DATABASE_URL=...   # 含 sparse 列的库
export RAG_SECOND_PATH=sparse
export RAG_KW_EXPAND=false
.venv/bin/python evals/golden/run_eval.py --out reports/r4-C.yaml --stability 0
```

1. **对比判读**：r4-C vs r4-2 / r4-A / r4-D；结论回写契约 Q6 + `experiments/rag_compare/README.md`



## 验收标准

- [x] `sparse_embedding` 灌满 8,574 块（无 NULL）——维护者实跑；`r4-C` corpus `N=8574` + sparse 路 73/73 非空命中  
- [x] `reports/r4-C.yaml` 产出；分象限 recall@5 + 第二路命中率（sparse hits）与 r4-2 / r4-A / r4-D 同表对比（见 Q6 报告）  
- [x] A 相关入口仍可调用（`RAG_FTS_CONFIG` / 影子 zhparser 脚本未删）  
- [x] 结论回写契约 Q6 + `experiments/rag_compare/README.md`（裁决：**不上默认**；开关保留）  
- [x] 未写生产库主路径默认；dense 列未改；`RAG_SECOND_PATH` 默认仍 `fts`  


**判读口径（预先约定 · 承接 A 否决）**：


| 条件                                                                         | 裁决                                      |
| -------------------------------------------------------------------------- | --------------------------------------- |
| C 在 **zh2zh** recall@5 相对 r4-2 **≥ +10pp**，或 zh2en+zh2zh **双象限**均明显优于 A/基准 | **采 C**；第二路默认改 sparse（FTS/A 入口保留为开关）    |
| C 提升落在 **+5～8pp** 灰色带                                                      | 维持 dense + glossary；C 不急上生产，入口保留可开      |
| C **< +5pp / 与 A 同级微弱**                                                    | **维持 dense 单路 + glossary**；A/C 都缓；第二路可关 |


主看 **zh2zh**（与 A 同一闸门）；zh2en 作辅证。务必报告 **sparse 路非空命中率**（对标 A 的 kw_nonempty，避免「总分没动、第二路仍死」假阳性）。

## 不做

- 不删 A 臂代码/镜像/脚本/`RAG_FTS_CONFIG`  
- 不动 dense embedding 列；不改生产主库数据  
- 不与 A 再并行调参；不把 `RAG_KW_EXPAND=true` 默认并进 C 首跑（先隔离）  
- 不引 ES / 独立检索服务



## 失败路径


| 触发                           | 行为                               | 可重试 |
| ---------------------------- | -------------------------------- | --- |
| FlagEmbedding 与现有 torch 冲突   | 隔离 venv 重嵌，只写库                   | Y   |
| sparse 维度 / 非零数超 sparsevec 限 | 截断或换存储策略；记风险                     | Y   |
| 第二路命中仍近 0                    | 查 query sparse 编码与算子方向（距离 vs 内积） | Y   |
| 提升 < +5pp                    | 按口径缓 C，不硬上                       | —   |
| grader 额度耗尽                  | `--out` 逐条落盘 + `--resume`        | Y   |




## 风险


| 触发              | 行为                                                      | 可重试 |
| --------------- | ------------------------------------------------------- | --- |
| 跨语言扩展强度不足       | 数据说话；回退 dense+glossary                                  | —   |
| Mac 重嵌 8.5k 耗时长 | 批处理 + 断点续写列                                             | Y   |
| 与 FTS 开关组合爆炸    | 评测矩阵只跑：`fts/simple`（基线已有）· `sparse`（本臂）；chinese 不进 C 首表 | —   |




### 自检结论（执行者）

> 30/40 回填区（命令、退出码、验收摘要、已知未测项）。

- [x] 闸已签 · verify PASS（`npx @cyning/harness@2.22.0 verify` → `VERIFY: PASS`）
- [x] sparse 列灌满 8574 / 脚本可断点 — 脚本交付 + 维护者全量重嵌（`r4-C` corpus N=8574）
- [x] `RAG_SECOND_PATH=sparse` 单测绿；默认 `fts` 不回归
- [x] A 入口未删（`Dockerfile.pg-zhparser` · `zhparser_arm_a/` · `RAG_FTS_CONFIG`）
- [x] r4-C — `reports/r4-C.yaml` completed 73/73；Q6 裁决落地

**40 命令与退出码**

| 命令 | 退出码 |
|------|--------|
| `uv run ruff check app/ops/rag/retrieve.py app/ops/rag/sparse_vec.py experiments/rag_compare/sparse_arm_c/embed_sparse.py tests/test_rag_second_path.py tests/test_rag_fts_config.py` | 0 |
| `uv run pytest tests/test_rag_second_path.py tests/test_rag_fts_config.py tests/test_golden_eval_runner.py -q --tb=short` | 0（27 passed） |

**交付摘要**：`RAG_SECOND_PATH`（默认 `fts`）接入 `hybrid_recall_detail`；sparse 路 SQL + `sparse_vec` 格式化/懒编码；实验目录 SQL/重嵌/README；维护者产出 `r4-C` 与 Q6 结案（不上默认）。

### KPI

| 项 | 分 |
|---|---|
| Task_KPI% | 100 |

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-13 |
| 定稿 | `reports/r4-C.yaml` · zh2zh 19/20（+10pp）· sparse hits 73/73 · neg 9/11 |
| 裁决 | **不上默认**；`RAG_SECOND_PATH` 默认仍 `fts`；开关保留待控噪 |
| 归档 | `docs/tasks/done/task_rag_sparse_arm_c.md` |
| Q6 | `experiments/rag_compare/REPORT_q6_arms_vs_baseline_20260812.md` |

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-08-12 | 初版（AI 起草 · 待人审） |
| 2026-08-12 | 承接 A 实测（zh2zh +0pp 弃 A）；补闸字段/判读/入口保留/`RAG_SECOND_PATH`/逐条落盘；待 HG-TASK-DRAFT |
| 2026-08-12 | HG-TASK-DRAFT + HG-AUDIT-R1 签收；00 派 30/40 |
| 2026-08-13 | 维护者 r4-C + Q6 裁决落地；实验结案 CLOSE（不上生产默认） |


