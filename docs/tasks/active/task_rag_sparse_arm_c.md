# Task：RAG 第二路 C 臂——bge-m3 稀疏向量对照实验

> **状态**：active（draft · 待人审）  
> **类型**：对照实验（契约 Q6 裁决链路 · A/C 互斥候选）  
> **关联**：契约 Q6 · A 臂任务卡 `task_rag_zhparser_arm_a.md` · 基准 `reports/r4-2.yaml`  
> **分支**：`task/rag-sparse-arm-c`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `rag-sparse-arm-c` |
| **git_branch** | `task/rag-sparse-arm-c` |
| **test_strategy** | `required` |
| **test_strategy_note** | sparsevec 灌满断言 + r4-C 与 r4-2/r4-A/r4-D 分象限对比 |
| **code_quality_bar** | `standard` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 对照实验（稀疏向量路）；不改 coding_wiki 正文 |
| **review_hat** | `20` |
| **orchestration** | 单 task · 在 A 臂后顺序执行 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | pending | 22-R1 | 维护者确认 C 臂方案与判读口径（draft · 待人审） |

---

## 目标

同一 runner、同一金样（73 条）、同一嵌入模型，**只替换第二路**：tsvector 关键词路 → bge-m3 稀疏向量路（lexical weights），验证「免分词 + 跨语言词项扩展」对召回的修复效果，与 A 臂数据对比，支撑 Q6 的 A/C 互斥裁决。

## 前置事实

| 项 | 状态 |
|----|------|
| pgvector | 0.8.5，已支持 `sparsevec` + `<#>` 算子（本地库已验证版本） |
| bge-m3 | 多密度输出（dense + sparse lexical weights）；sentence-transformers **不暴露** sparse → 需 FlagEmbedding |
| 机制优势 | 稀疏路自带语义词项扩展，多语言训练 → 理论上覆盖 ZH→EN/混合全象限，**完全绕开分词问题** |
| 待定风险 | 跨语言词项扩展**强度**是经验问题，必须金样实测 |

## 实施步骤

1. **依赖**：`uv add FlagEmbedding`（实验期可先 `uv pip install`，定稿再入 pyproject）
2. **影子列**：migration 加 `sparse_embedding sparsevec`（本地库；不动生产）
3. **稀疏重嵌**：`BGEM3FlagModel` 批量算 8.5k chunks 的 lexical weights（Mac 本地跑，dense 已有不动）写影子列
4. **查询路**：retrieve 加 sparse 路 SQL（`sparse_embedding <#> CAST(:qvec AS sparsevec)`），env 开关 `RAG_KW_PATH=sparse` 切换
5. **跑评测**：r4-C.yaml，与基准 / r4-A 同表对比

## 验收

- [ ] sparsevec 列灌满 8,574 块（无 NULL）
- [ ] r4-C.yaml 分象限 recall@5 + 负样本拒答率，与 r4-2 / r4-A / r4-D 四列对比
- [ ] 结论回写契约 Q6：A vs C 裁决建议

**判读口径（预先约定）**：

- C 在 zh2en + zh2zh 双象限均优于 A（或 A 未达 10pp 而 C 达）→ 采 C，tsvector 路退役
- 两者都微弱 → 维持 dense 单路 + glossary，A/C 都缓

## 不做

- 不动 dense embedding 列；不动生产；不与 A 臂并行施工（先 A 后 C，顺序执行）

## 风险

| 触发 | 行为 | 可重试 |
|---|---|---|
| FlagEmbedding 与现有 torch 版本冲突 | 隔离 venv 跑重嵌脚本，产物写库即可 | Y |
| 稀疏权重维度超 sparsevec 上限 | pgvector sparsevec 上限 30k 非零元素，bge-m3 词表内安全 | — |
| 跨语言扩展实测弱 | 数据说话，回退 dense+glossary | — |

## 修订

| 日期 | 说明 |
|------|------|
| 2026-08-12 | 初版（AI 起草 · 待人审） |
