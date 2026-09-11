# 对比实验：自建管线 vs LlamaIndex（rag_compare）

| 项 | 内容 |
|----|------|
| **状态** | `active` · 学习实验，不进生产 |
| **日期** | 2026-08-10 |
| **目的** | 把「框架默认能到哪」从感觉变成证据；对比产物进面试叙事 |
| **被对照方** | 自建管线 `app/ops/rag/`（真值，不动） |

## 方法

**同源语料**：issue #2720（DB 直读，两条管线同一输入）。
**同问题**：golden G01（"Kimi Code 自动压缩被取消并报错 This operation was aborted 是什么原因？"）。

## 对比维度（2026-08-10 实测已填）

| 维度 | 自建 `app/ops/rag` | LlamaIndex 默认 |
|------|--------------------|-----------------|
| chunk 数 / 边界 | 7 块 · 全起于 `###` 章节 · 小章节按 E2 合并 | 11 块 · 逐标题成块，**4 个 69–146 字符的微型块未合并** |
| fence 完整性 | 原子不拆（规则保证） | #2720 上 0/11 切断——**侥幸**（各块 token≤800）；**无 fence 原子规则**（#43 未切亦是 token≤800，非护栏） |
| 表格处理 | 行切+重复表头 | 本样本未超限未触发；无表头重复规则 |
| 图片/HTML | 锚点化 + 清洗 | 本样本无图未触发；默认 HTML 原文进向量 |
| tokenizer 口径 | bge-m3 同源（E5） | **tiktoken（默认）**，与被嵌模型不同源 |
| G01 检索命中 | **8,574 块/2,748 单元中召回**：2720 sem#1/#3，top5 占两席 | 单文档内存索引（命中无区分度）；**top-5 全是微型标题块，Root cause / Suggested fixes 未进榜** |
| 关键词路 | tsvector + RRF 双路融合 | 无（仅语义单路） |
| 可测性 | 纯函数 + 注入 fake counter，8 条单测零模型零库 | 切分/检索绑定框架对象，单测需穿框架抽象 |

### 结论（实测）

1. **决定性差距在「微型块」**：LI 默认不合并小章节 → 检索 top-5 被标题+一行的浅水块占据，真正含答案的块落榜。我们的 E2 合并 + 前缀注入正是针对此。
2. fence 完整、表格表头等规则在 LI 里要靠自定义 NodeParser 另写——框架默认值在本语料上会漏。
3. LI 仍肯定了 bge-m3 跨语言能力：中文 query 对英文语料，两管线的语义路都能命中。
4. 附赠收获：实验撞出生产 SQL bug（`plainto_tsquery` 误写 `plainto_tsvector`），已修。

### fence 专题（#43 / #1089 / #2540 / #699 实测）

| 样本 | 结构 | 自建 | LI |
|------|------|------|-----|
| #43 | 整篇几乎一个大 fence；字符多、有效内容少 | 1 块（E1 原子 + 8192 保险丝） | 1 块——**不是 fence 护栏**，见下方「#43 未切」 |
| #1089 | fence 标记 9 个（奇数 · 源畸形） | 边界落在嵌套 ``` 处（CommonMark 语义，无内容丢失） | 同位置被迫切 + 尺寸驱动切割叠加（node 5 从 diff 正文中间续起） |
| #2540 / #699 | fence 均 ≤800 | 完整 | 完整 |

#### #43 未切：LI 怎么「做到」的（2026-08-10 源码+复测）

先前用「字符/4 ≈ 2.5k tokens」高估了；复测：

| 口径 | 数值 |
|------|------|
| body 字符 | 9,678（MarkdownNodeParser 后节点 9,290） |
| 其中空白 | **83.3%**（粘贴进 fence 的宽空白/对齐） |
| 非空白 | 1,620 |
| LI 默认 tokenizer（tiktoken `cl100k_base`） | **656 ≤ chunk_size=800** → 不切 |
| bge-m3 | 595（同样 <800） |

机制（`llama_index/.../text/sentence.py` · `SentenceSplitter._split`）：

1. `MarkdownNodeParser`：无标题可切 → **1 个 md node**（与 fence 无关）
2. `SentenceSplitter`：**先** `_token_size(text)`；`<= chunk_size` 则整段原样返回（early return）
3. **没有**「遇 \`\`\` 则原子保留」的规则；本样本只是 token 预算没超

若把同结构写成密代码、tiktoken >800，且几乎无 `\n\n`，LI 会沿 段落 → 句子 → 次级正则 → 空格 → 字符 递归切，**会从 fence 中间切断**。自建则走 E1：原子超限整块保留，再靠 8192 保险丝。

- 非平衡 fence 全库 5/881（0.6%），系源格式问题，任何解析器（含 GitHub 渲染）行为一致
- 公平性注记：LI 侧为「默认-ish」装配（MarkdownNodeParser→SentenceSplitter），不代表调优后上限
- 核心差异不变：**well-formed fence 上，自建永不切（规则），LI 只认 token 预算（无 fence 规则）**；#43 未切是预算巧合，不是能力

## 运行

```bash
# 依赖（实验用，见本目录 requirements.txt；不进根 requirements.txt）
uv pip install -r experiments/rag_compare/requirements.txt

# bge-m3 权重已缓存（R-2 灌库时下载过），不会重复下载
.venv/bin/python experiments/rag_compare/llamaindex_pipeline.py
```

脚本输出三块：① LI 切分结果（对照 chunker 输出）② fence 完整性自检 ③ G01 检索 top-5。

## 纪律

- 本目录是**学习对照**，不引入 app 代码路径；LI 依赖只写在本目录 `requirements.txt`，不进根 `requirements.txt` / `pyproject.toml` 主依赖
- 结论回填上表后，同步进 `ops-desk-workspace/docs/05-plan/05-rag-pipeline-walkthrough_v1_zh.md` §1

## Q6 第二路对照（A/C · 2026-08-12）

| 臂 | 报告 | 结论 |
|---|---|---|
| 基准 | `reports/r4-2.yaml` | zh2zh recall@5 17/20；negative 9/10 |
| D glossary | `reports/r4-D.yaml` | 边际；kw 仍约 5/73 → 不继续投入 |
| **A zhparser** | `reports/r4-A.yaml` | zh2zh **+0pp**；kw 仍死 → **弃 A 上生产** |
| **C sparse** | `reports/r4-C.yaml` | 第二路 73/73 非空；zh2zh **+10pp**；negative 9/11 → **不上默认**，开关保留 |

综合对照（第三方稿 + 勘误 + 下一步）：`experiments/rag_compare/REPORT_q6_arms_vs_baseline_20260812.md`  
P0 Reranker SPEC（signed · 生产默认 false）：`docs/spec/rag-reranker-p0/SPEC-rag-reranker-p0_v1.md`  
P0 实现说明：`experiments/rag_compare/reranker_p0/README.md` · 真 CE 金样 `reports/r4-R.yaml` · 误跑归档 `reports/r4-R-misrun-no-ce.yaml`

**A 入口保留（可调用，不删）**：

- 镜像：`Dockerfile.pg-zhparser` · 脚本：`experiments/rag_compare/zhparser_arm_a/`
- 运行时：`RAG_FTS_CONFIG=chinese`（生产默认 `simple`）
- 说明：`experiments/rag_compare/zhparser_arm_a/README.md`

**C 入口（实验）**：

- 脚本：`experiments/rag_compare/sparse_arm_c/`（加列 SQL · 断点重嵌 · README）
- 运行时：`RAG_SECOND_PATH=sparse`（默认 `fts`）；评测建议 `RAG_KW_EXPAND=false`
- 说明：`experiments/rag_compare/sparse_arm_c/README.md`

## 修订

| 日期 | 说明 |
|------|------|
| 2026-08-10 | 首版 |
| 2026-08-10 | 增补本目录 requirements.txt；安装 llama-index-core 0.14.23 + embeddings-huggingface 0.7.0 |
| 2026-08-10 | fence/#43：纠正「超 800 未切」误判；根因是 tiktoken=656≤800 early return，非 fence 护栏 |
| 2026-08-12 | Q6：A 臂实测弃上生产；保留 A 入口；指向 C 臂 task |
| 2026-08-12 | C 臂入口：`sparse_arm_c/`（SQL/重嵌/README）；`RAG_SECOND_PATH=sparse` |
| 2026-08-12 | 落盘 Q6 综合报告 `REPORT_q6_arms_vs_baseline_20260812.md`；更新 C 实测结论 |
| 2026-08-12 | 挂链 P0 SPEC `docs/spec/rag-reranker-p0/SPEC-rag-reranker-p0_v1.md` |
| 2026-08-12 | P0 CE 落地说明 `reranker_p0/README.md`；SPEC signed · 默认 false |
