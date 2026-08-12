# Task：RAG P0 Cross-Encoder Reranker（粗排扩候选 → 精排 top-5）

> **状态**：active（30/40 已交 · **关账前停** · r4-R 待维护者复测）  
> **类型**：feature（检索质量 · 排序层）  
> **关联**：`docs/spec/SPEC-rag-reranker-p0_v1.md`（HG-SPEC-SIGNOFF=approved）· Q6 报告 `experiments/rag_compare/REPORT_q6_arms_vs_baseline_20260812.md` · 基线 `reports/r4-2.yaml`  
> **分支**：`task/rag-reranker-p0`

---

## Harness 元信息


| 字段                           | 值                                                                 |
| ---------------------------- | ----------------------------------------------------------------- |
| **task_slug**                | `rag-reranker-p0`                                                 |
| **git_branch**               | `task/rag-reranker-p0`                                            |
| **test_strategy**            | `required`                                                        |
| **test_strategy_note**       | 单测：fake CE 排序/截断 + `RAG_RERANK_ENABLED=false` 不调 CE；金样 r4-R vs r4-2 |
| **code_quality_bar**         | `standard`                                                        |
| **graph_change_layer**       | `none`                                                            |
| **graph_delta**              | `none`                                                            |
| **graph_delta_note**         | 不改对外 REST；精排插在 retrieve 内，契约 top-5 不变                              |
| **wiki_delta**               | `n/a`                                                             |
| **wiki_delta_note**          | 本波不改 coding_wiki；实验说明落 `experiments/rag_compare/`                  |
| **review_hat**               | `20`                                                              |
| **required_invoke_hats**     | `10,30`                                                           |
| **invoke_retention_profile** | `minimal`                                                         |
| **orchestration**            | 单 task · SPEC 签后 00 出卡 · 30 实现 · 金样复测维护者执行                        |



### 人工闸


| human_gate_id | status   | blocks_hats | 说明                                                                 |
| ------------- | -------- | ----------- | ------------------------------------------------------------------ |
| HG-TASK-DRAFT | approved | 22-R1       | 00 代签（维护者授权：SPEC 已签 · 00 统筹 · 签收 30 等节点）· 范围对齐 SPEC D1–D4         |
| HG-AUDIT-R1   | approved | 30          | 00 代签（同上授权）· 审查文 `docs/harness/reviews/task_rag_reranker_p0_audit_R1_20260812.md` |


---



## 目标

在不改嵌入列、不改默认第二路的前提下，将 RRF 粗排候选扩到 top-M，经 **BAAI/bge-reranker-v2-m3** Cross-Encoder 精排后取 top-5，提升排序精度；生产默认开关保持 **false**，直至 r4-R 过 §6 门槛再议改默认。

## 范围（对齐 SPEC D1–D4）

1. **D1**：`retrieve_node` 内 `hybrid_recall(k_each=K, top_n=M)` → `rerank_chunks` → top-5；分数仅观测/日志  
2. **D2**：env `RAG_RERANK_ENABLED`（默认 false）/ `RAG_RERANK_MODEL` / `RAG_RERANK_CANDIDATES=20` / `RAG_RECALL_K_EACH=20`（仅开启时）  
3. **D3**：评测产出 `reports/r4-R.yaml`（因子隔离：fts/simple、无 KW_EXPAND、无 sparse）；grader 同 r4-2  
4. **D4**：fake reranker 单测 + 实验短文；可选更新 Q6「下一步」指针  

## 非范围

- 不上默认 C sparse / 不改 FTS 分词 / 不扩 glossary  
- 不做 HyDE / query rewrite  
- 不改 decide / grader 枚举 / 拒答文案  
- 不改 chunk 切分、dense 重嵌、对外 REST  
- 不引入远端 rerank API / ES  
- 不做 rerank 分数进闸  
- 本波不关账（维护者跑完 r4-R 后再 CLOSE）

## 签收锁死（生产默认）

| 项 | 值 |
|---|---|
| 生产 / 合入默认 `RAG_RERANK_ENABLED` | **false** |
| 实验复测 | 维护者本地 `=true` 跑 r4-R |

## 实施步骤

1. 新增 `app/ops/rag/reranker.py`：懒加载 CE 单例 + 纯函数 `rerank_chunks`；加载失败回退粗排 top-5  
2. 改 `retrieve_node`：按 env 切换 k_each/M 与精排；span metadata 区分 rrf_top / rerank_top  
3. 单测 + `experiments/rag_compare/` 短文（开关/依赖/与 Q6 P0 关系）  
4. **维护者**：`RAG_RERANK_ENABLED=true` 跑金样 → `reports/r4-R.yaml` → 按 SPEC §6 裁决  

复测命令（维护者执行 · 本 task 不代跑）：

```bash
export RAG_RERANK_ENABLED=true
export RAG_SECOND_PATH=fts
export RAG_KW_EXPAND=false
export RAG_FTS_CONFIG=simple
# grader 对齐 r4-2（勿换模型字符串）
.venv/bin/python evals/golden/run_eval.py --out reports/r4-R.yaml --stability 0
```

## 验收标准

- [x] `RAG_RERANK_ENABLED=false`：行为与现网一致（单测）  
- [x] `=true`：粗排 M→CE→5；日志/span 可见 rerank 前后锚点（单测 mock + 代码）  
- [x] grader 仍只见 top-5；闸逻辑未改  
- [x] ruff + 相关 pytest 绿  
- [ ] `reports/r4-R.yaml` 产出（**维护者复测**）并对标 r4-2：negative ≥ 基线；zh2zh recall@5 ≥ 基线；总 pass 或 best_relevance 至少一项明显改善  

## 失败路径


| 触发 | 行为 | 可重试 |
| ---- | ---- | --- |
| CE 权重下载/加载失败 | fail-closed：错误日志；回退粗排 top-5 | Y |
| 候选 < 5 | 有几条评几条 | — |
| 超时（若实现上限） | 回退粗排 top-5；日志 `rerank_timeout` | Y |
| GPU 不可用 | CPU 推理允许 | — |
| 与 sparse 同开 | 允许但不作本波验收矩阵 | — |
| r4-R 未达门槛 | 不改生产默认；开关可合入 | — |
| grader 额度耗尽 | `--out` 逐条落盘 + `--resume` | Y |


## 风险


| 触发 | 行为 | 可重试 |
| ---- | ---- | --- |
| CPU 延迟偏高 | 文档标明；默认保持 false | — |
| M/K 默认需调参 | 以 env 覆盖再跑一版 | Y |
| 小样本 confidence low | 裁决诚实标注 | — |


### 自检结论（执行者）

> 30/40 回填区（命令、退出码、验收摘要、已知未测项）。

- [x] 闸已签 · verify PASS（`npx @cyning/harness verify --task docs/tasks/active/task_rag_reranker_p0.md` → `VERIFY: PASS`）
- [x] 单测绿（关开关 / fake 排序 / 失败回退 / retrieve_node 接线）
- [x] ruff 相关文件绿
- [x] runner 已接 CE（`evals/golden/run_eval.py` · `RAG_RERANK_ENABLED`）
- [x] r4-R — **方案 B（floor=0.6/ratio=0.75）复测完成** `reports/r4-R.yaml`
  - vs misrun：pass **54/73 持平**；neg **11/11 持平**；zh2zh recall 17→18
  - **G65**：fail→**pass**（空 top5 拒答）；pre-floor 曾 10/11 已修
  - 未达「总 pass +2」→ **不改生产默认 false**
  - 归档：`r4-R-misrun-no-ce.yaml` · `r4-R-pre-floor.yaml`（55/73 但 neg 掉）

**40 命令与退出码**

| 命令 | 退出码 |
|------|--------|
| `npx @cyning/harness verify --target . --task docs/tasks/active/task_rag_reranker_p0.md` | 0（VERIFY: PASS） |
| `.venv/bin/python -m ruff check app/ops/rag/reranker.py app/ops/rag/retrieve.py app/ops/chat/rag_nodes.py tests/test_rag_reranker.py` | 0 |
| `.venv/bin/python -m pytest tests/test_rag_reranker.py -q --tb=short` | 0（8 passed） |

**交付摘要**：`RAG_RERANK_ENABLED`（默认 false）· `app/ops/rag/reranker.py` · `retrieve_node` 粗排 M→CE→5 · span `rrf_top`/`rerank_top` · `experiments/rag_compare/reranker_p0/README.md`。生产默认未改 true。**本波不关账**。

**维护者复测**

```bash
export RAG_RERANK_ENABLED=true
export RAG_SECOND_PATH=fts
export RAG_KW_EXPAND=false
export RAG_FTS_CONFIG=simple
.venv/bin/python evals/golden/run_eval.py --out reports/r4-R.yaml --stability 0
```

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-08-12 | 00 起草（承接 SPEC 签收）；闸代签；派 30/40；关账前停 · r4-R 维护者执行 |
