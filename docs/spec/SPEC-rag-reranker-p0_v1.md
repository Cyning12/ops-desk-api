# SPEC：RAG P0 Cross-Encoder Reranker（粗排扩候选 → 精排 top-5）（v1）

> **状态**：`signed`（HG-SPEC-SIGNOFF=approved · 生产默认 `RAG_RERANK_ENABLED=false`）  
> **track**：`feature`（检索质量 · 排序层）  
> **上游**：Q6 A/C/D 对照结案 · `experiments/rag_compare/REPORT_q6_arms_vs_baseline_20260812.md`（P0 优先于 HyDE / C 默认化）  
> **基线报告**：`reports/r4-2.yaml`（Normal · dense + FTS/`simple`）  
> **对照勿混入**：本波评测默认 **不**开 `RAG_SECOND_PATH=sparse`、`RAG_KW_EXPAND`、`RAG_FTS_CONFIG=chinese`  
> **下游**：人签 SPEC → 00 出 task → 30 实现 → 金样 `reports/r4-R.yaml`（拟定）  
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息


| 字段                         | 值                                                                                  |
| -------------------------- | ---------------------------------------------------------------------------------- |
| **spec_slug**              | `rag-reranker-p0`                                                                  |
| **invoke_slug**            | `rag-reranker-p0`（task 阶段）                                                         |
| **test_strategy**          | `required`                                                                         |
| **test_strategy_note**     | 单测：rerank 排序稳定、env 关闭时行为=现状；金样：同 73 条对标 r4-2（recall@5 / best_relevance / negative） |
| **Open Folder（实现）**        | `ops-desk-api/`                                                                    |
| **默认分支**                   | `task/rag-reranker-p0`（自 C 臂归档提交分出；合入前可 rebase `master`）                           |
| **graph_change_layer（建议）** | `none` 或 `G-L2` 文档增量（实现时由 task 裁定；本波不改对外 REST 契约）                                  |




### 人工闸（SPEC 阶段）


| human_gate_id       | status   | 说明                                |
| ------------------- | -------- | --------------------------------- |
| **HG-SPEC-SIGNOFF** | approved | 维护者签收本 SPEC 后方可 00 出 task / 30 改码 |


---



## 1. 背景与目标



### 现状


| 层       | 现状                                                               |
| ------- | ---------------------------------------------------------------- |
| 主路      | bge-m3 dense → pgvector cosine；`k_each=10`                       |
| 第二路（默认） | PG FTS `simple`；中文 query 几乎空命中                                   |
| 融合      | RRF k=60、两路 1:1 → **直接 top_n=5** 进 grader / 回答                   |
| Q6 结论   | A/D 不继续；C sparse 第二路可活但 negative 回退、不上默认；总 pass 仍靠 dense         |
| 痛点      | 金样上 recall@5 已不低，但 **排序精度不足**（exact 被挤后、弱相关进 top-5）；扩辅路不如抬精排 ROI |




### 一句话目标

在 **不改嵌入列 / 不改默认第二路** 的前提下，把「RRF（或等价粗排）候选」扩到 top-M，经 **bge-reranker-v2-m3** Cross-Encoder 精排后取 top-5，提升 `best_relevance` 与可归因的召回稳定性，并保证 negative 不劣于基线。

---



## 2. 范围



### D1 · 检索链插入精排（必做）

现网链路：

```text
embed(query) → hybrid_recall(k_each=10, top_n=5) → grade_chunks(top-5) → decide
```

目标链路（P0）：

```text
embed(query)
  → hybrid_recall(k_each=K, top_n=M)     # 粗排候选池，M≥5
  → rerank(query, candidates) → top-5    # Cross-Encoder
  → grade_chunks(top-5) → decide         # 闸与回答面不变
```


| 项         | 约定（草案 · 可签收时锁死）                                                                       |
| --------- | ------------------------------------------------------------------------------------- |
| 模型        | **BAAI/bge-reranker-v2-m3**（与 bge-m3 同族；中英混合友好）                                       |
| 候选池 M     | 默认 **20**（粗排融合后取 20；可用 env 覆盖）                                                        |
| 每路 k_each | 默认提到 **20**（使两路有足够互异候选进 RRF；避免 M=20 但每路只有 10）                                         |
| 精排输出      | 固定 **5**（与现 grader / 契约 top-5 对齐）                                                     |
| 插入点       | `retrieve_node` 内、`hybrid_recall` 之后；或 `hybrid_recall` 返回粗排后由独立 `rerank_chunks` 纯函数消费 |
| 分数        | rerank score **仅观测/日志**（对齐 RRF：不进闸、不上用户卡片）                                            |
| 加载        | 进程内懒加载单例（对齐 embedder Q3）；首次检索才加载权重                                                    |




### D2 · 开关与配置（必做）


| env                     | 默认                                | 含义                         |
| ----------------------- | --------------------------------- | -------------------------- |
| `RAG_RERANK_ENABLED`    | `false`（首合入）或 SPEC 签收时人定是否 `true` | 关闭时行为必须与现网一致（top_n=5、无 CE） |
| `RAG_RERANK_MODEL`      | `BAAI/bge-reranker-v2-m3`         | 可覆盖                        |
| `RAG_RERANK_CANDIDATES` | `20`                              | 粗排 top-M                   |
| `RAG_RECALL_K_EACH`     | `20`（仅当 rerank 开启时生效；关闭时保持现网 10）  | 每路召回条数                     |
| `RAG_RERANK_MIN_SCORE`  | `0.6`                             | 顶分地板：`max < 此值` → 真空拒答   |
| `RAG_RERANK_SCORE_RATIO`| `0.75`                            | 相对顶分：保留 `score ≥ max * ratio` |


**签收锁死（2026-08-12）**：实验复测时 `RAG_RERANK_ENABLED=true` 跑 r4-R；**生产 / 合入默认仍 false**，直至金样通过裁决再改默认。

### D3 · 评测（必做）

- Runner：现有 `evals/golden/run_eval.py`；产出 `reports/r4-R.yaml`
- 对照：`reports/r4-2.yaml`（主）；可选旁注 r4-A/C/D，但 **因子隔离**：评测 R 时 `RAG_SECOND_PATH=fts`、`RAG_KW_EXPAND=false`、`RAG_FTS_CONFIG=simple`
- 报告字段：沿用现有；日志/观测需能区分 `rrf_top` vs `rerank_top`（至少在 retrieve span metadata）
- grader：与 r4-2 **同一模型字符串**（当前 `qwen3.7-max`），避免 C 臂版本偏移重演



### D4 · 测试与文档（必做）

- 单测：fake reranker（固定分数）验证排序与 top-5 截断；`RAG_RERANK_ENABLED=false` 不调用 CE
- 文档：`experiments/rag_compare/` 或 `docs/` 短文：开关、依赖、与 Q6 P0 关系；更新 `REPORT_q6_…`「下一步」指针到本 SPEC
- **不**强制 alembic / 新 DB 列



### D5 · 依赖（实现裁定）


| 选项                                                     | 说明                      |
| ------------------------------------------------------ | ----------------------- |
| A · FlagEmbedding / sentence-transformers CrossEncoder | 与现有本地模型栈一致；CPU 可跑       |
| B · 远端 rerank API                                      | 本波 **不做**（延迟/密钥/不可复现评测） |


实现优先本地 CE；权重可与 bge-m3 一样走 HF cache。

---



## 3. 非范围

- 不上默认 C sparse / 不改 FTS 分词器 / 不扩 glossary  
- 不做 HyDE / query rewrite（P1）  
- 不改 `decide` / grader 枚举语义 / 拒答文案  
- 不改 chunk 切分、dense 重嵌、对外 REST schema  
- 不引入 Elasticsearch / 独立检索服务  
- 不做「rerank 分数进闸」的阈值拒答（若 negative 仍差，另开 P2/闸实验）  
- 不在本 SPEC 内扩金样到 200+（可另 task）

---



## 4. 方案对比（R2）


| 方案                           | 做法          | 收益            | 代价           | 裁决     |
| ---------------------------- | ----------- | ------------- | ------------ | ------ |
| **S1 · CE Reranker（本 SPEC）** | 粗排 M→CE→5   | 专治排序；不改库      | ~1GB 模型；+延迟  | **推荐** |
| S2 · 只加大 k_each/top_n 仍 RRF  | 无 CE        | 几乎无           | 噪声进 top-5 更糟 | 弃      |
| S3 · 直接上 HyDE                | LLM 改写再检索   | 可能助专有名词       | 贵、方差大、难归因    | 置后 P1  |
| S4 · C sparse 默认化            | 第二路换 sparse | zh2zh 曾 +10pp | negative 红线  | 不上默认   |
| S5 · 远端 rerank API           | 托管 CE       | 运维省本地内存       | 评测不可复现、密钥    | 本波弃    |


---



## 5. 边界 / 失败路径 / 安全


| 触发            | 行为                                                     | 可重试    |
| ------------- | ------------------------------------------------------ | ------ |
| CE 权重下载/加载失败  | fail-closed：打错误日志；**回退**到粗排 top-5（等同关 rerank），不拖垮 chat | Y（修环境） |
| 候选 < 5        | 有几条评几条；不足则原样返回                                         | —      |
| CE 分过滤（方案 B） | `max < min_score` → 空召回拒答；否则 `score ≥ max * ratio` | — |
| 超时（可选上限）      | 回退粗排 top-5；日志标记 `rerank_timeout`                       | Y      |
| GPU 不可用       | CPU 推理允许；须在文档标明延迟预期                                    | —      |
| 与 sparse 同时开启 | **允许但不作为本波验收矩阵**；文档警告因子纠缠                              | —      |
| 用户可见分数泄漏      | 禁止：卡片/SSE 不输出 rerank/rrf 分数                            | —      |


---



## 6. 验收标准



### 功能

- [x] `RAG_RERANK_ENABLED=false`：行为与现网一致（回归单测 + 可选冒烟）
- [x] `=true`：粗排 M→CE→5；span/日志可见 rerank 前后锚点
- [x] grader 仍只见 top-5；闸逻辑未改



### 质量（对标 r4-2，金样 73）


| 指标                          | 门槛（草案）                                                                                 |
| --------------------------- | -------------------------------------------------------------------------------------- |
| **negative_refuse**         | **≥ 基线**（r4-2 为 9/10；若分母 11 则以同集重跑基线为准）——不得出现「乱答变多」                                    |
| **zh2zh recall@5**          | **≥ 基线**（17/20）                                                                        |
| **总 pass 或 best_relevance** | 至少一项相对基线 **明显改善**：总 pass ≥ +2 条，**或** 约定子集（如曾 exact→weak 的 case）`best_relevance` 回升可陈述 |
| 辅看                          | zh2en / en2en 不出现灾难性回退（单象限 recall 掉幅 ≤ 2 条，除非有 case 级解释）                               |


未达门槛 → **不改生产默认**；代码与开关可合入，默认保持 false。

### 工程

- [x] ruff + 相关 pytest 绿  
- [x] 依赖声明清晰（根 requirements 已有 sentence-transformers / CrossEncoder；文档写明）  
- [x] 图谱：`graph_change_layer=none`，本波不改  

---



## 7. 思考轮控制（10-spec）


| 轮              | 结论摘要                                                    | 状态    |
| -------------- | ------------------------------------------------------- | ----- |
| R0             | Q6 后主收益不在分词；P0=精排                                       | done  |
| R1             | 范围=CE 插入点+开关+金样 r4-R；非范围=HyDE/C默认/改闸                    | done  |
| R2             | 推荐 S1；弃纯扩 RRF / 本波 HyDE / C 默认 / 远端 API                 | done  |
| R3             | 加载失败回退粗排；分数不进闸；与 sparse 同开不验收                           | done  |
| R4             | 质量门槛以 negative 不劣化为主约束；recall 保底                        | done  |
| R5             | SPEC draft 可交人签；签后 00 出 task                            | done  |
| early_stop     | no                                                      | —     |
| residual_risks | ① CPU 延迟是否可接受生产；② M/K 默认值可能需一轮调参；③ 小样本 confidence 仍 low | 签收时知悉 |


---



## 8. 下一棒

1. ~~**维护者**：审本 SPEC → 签 `HG-SPEC-SIGNOFF=approved`（并裁定生产默认 true/false）~~ **done**（默认 false）
2. ~~**00**：起草 `docs/tasks/active/task_rag_reranker_p0.md`~~ **done**
3. ~~**30**：实现 D1–D4~~ **done**（关账前停）
4. **维护者**：跑 r4-R → 按 §6 裁决是否改默认 → 再关账 / PR

### 复制区（给维护者 · 复测）

```text
export RAG_RERANK_ENABLED=true
export RAG_SECOND_PATH=fts
export RAG_KW_EXPAND=false
export RAG_FTS_CONFIG=simple
.venv/bin/python evals/golden/run_eval.py --out reports/r4-R.yaml --stability 0
# 对照 reports/r4-2.yaml · SPEC §6 门槛
```

---



## 修订


| 日期         | 说明                            |
| ---------- | ----------------------------- |
| 2026-08-12 | 初稿（P0 CE reranker；承接 Q6 综合报告） |
| 2026-08-12 | HG-SPEC-SIGNOFF 签收；生产默认锁 false；00/30 落地；关账前停 · r4-R 待复测 |


