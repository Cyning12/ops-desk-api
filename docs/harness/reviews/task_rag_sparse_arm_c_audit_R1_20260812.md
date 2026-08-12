# Task Audit R1：rag-sparse-arm-c

> **task**：`docs/tasks/active/task_rag_sparse_arm_c.md`  
> **日期**：2026-08-12 · 审查：维护者签收（会话内「已签收C」）  
> **结论**：`pass` · 建议 `HG-AUDIT-R1=approved`

---

## 核对

| 项 | 审阅 |
|---|---|
| 范围 | FlagEmbedding 稀疏重嵌 · `sparse_embedding` 影子列 · `RAG_SECOND_PATH=sparse` · r4-C |
| 非范围 | 删 A 入口 · 改 dense · 写生产 · 默认并进 `RAG_KW_EXPAND` |
| 验收 | 8574 无 NULL · r4-C 分象限 + sparse 命中率 · A 入口仍可调 · 结论回写 |
| failure_paths | torch 冲突 / sparse 限 / 第二路仍死 / &lt;+5pp / 额度耗尽 resume |
| 承接 | A 臂 zh2zh +0pp 已否决上生产 |
| `wiki_delta` | `n/a` · `graph_change_layer=none` |

## 条件

- **实跑**稀疏重嵌与全量 r4-C 由维护者或 30 在可用算力/额度下执行；30 须交付可运行脚本 + 开关 + 单测
- 不删除 `RAG_FTS_CONFIG` / zhparser 镜像与脚本
- 评测须 `--out` 逐条落盘；稳定性可 `--stability 0`

## HG-AUDIT-R1 建议

**approved**（维护者已口头签收 · 本文件留痕）
