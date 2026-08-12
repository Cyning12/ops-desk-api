# Task Audit R1：rag-reranker-p0

> **task**：`docs/tasks/active/task_rag_reranker_p0.md`  
> **日期**：2026-08-12 · 审查：00 代签（维护者授权：SPEC 已签 · 00 统筹 · 签收 30 等节点）  
> **结论**：`pass` · 建议 `HG-AUDIT-R1=approved`

---

## 核对

| 项 | 审阅 |
|---|---|
| 上游 | SPEC `HG-SPEC-SIGNOFF=approved`；Q6 P0=CE 精排 |
| 范围 | D1 插入点 · D2 env · D3 r4-R · D4 单测+短文 |
| 非范围 | HyDE / C 默认 / 改闸 / 远端 API / 分数进闸 |
| 验收 | 关开关回归 · 开开关 M→CE→5 · r4-R vs r4-2 门槛 |
| failure_paths | CE 加载失败回退粗排 top-5；额度 resume |
| 生产默认 | **false**（签收锁死）；实验 `true` 跑 r4-R |
| `wiki_delta` | `n/a` · `graph_change_layer=none` |

## 条件

- 全量金样 `reports/r4-R.yaml` 由**维护者**实跑；30 须交付开关 + 可测代码 + 复测命令  
- 评测因子隔离：`RAG_SECOND_PATH=fts` · `RAG_KW_EXPAND=false` · `RAG_FTS_CONFIG=simple`  
- grader 模型字符串对齐 r4-2  
- **本波不关账**；待 r4-R 裁决后再 CLOSE / 议改默认

## HG-AUDIT-R1 建议

**approved**（维护者会话授权 00 代签 · 本文件留痕）
