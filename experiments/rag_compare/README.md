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
| fence 完整性 | 原子不拆（规则保证） | 0/11 切断——**但系侥幸**（各块恰好 <800）；无原子规则，更大 fence 必断（库内实测最大 4,019 字符） |
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
| #43 | 整篇一个 4,019 字符 fence | 1 块（E1 有意裁决 + 8192 保险丝） | 1 块，但 9,290 字符 ≈2.5k tokens **远超其自设 chunk_size=800 未切**，无护栏说明 |
| #1089 | fence 标记 9 个（奇数 · 源畸形） | 边界落在嵌套 ``` 处（CommonMark 语义，无内容丢失） | 同位置被迫切 + 尺寸驱动切割叠加（node 5 从 fence 正文中间续起） |
| #2540 / #699 | fence 均 ≤800 | 完整 | 完整 |

- 非平衡 fence 全库 5/881（0.6%），系源格式问题，任何解析器（含 GitHub 渲染）行为一致
- 公平性注记：LI 侧为「默认-ish」装配（MarkdownNodeParser→SentenceSplitter），不代表调优后上限
- 核心差异不变：**well-formed fence 上，自建永不切（规则），LI 尺寸不够必切（无规则）**

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

## 修订

| 日期 | 说明 |
|------|------|
| 2026-08-10 | 首版 |
| 2026-08-10 | 增补本目录 requirements.txt；安装 llama-index-core 0.14.23 + embeddings-huggingface 0.7.0 |
