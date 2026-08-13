# Task Audit R1：rag-zhparser-arm-a

> **task**：`docs/tasks/active/task_rag_zhparser_arm_a.md`  
> **日期**：2026-08-12 · 审查：维护者签收（会话内「签收」）  
> **结论**：`pass` · 建议 `HG-AUDIT-R1=approved`

---

## 核对

| 项 | 审阅 |
|---|---|
| 范围 | 自建 zhparser 镜像 · 影子库（5433）· COPY 灌库 · `RAG_FTS_CONFIG` · r4-A 对照 |
| 非范围 | 主库/生产 · C 臂并行 · RRF/语义路/嵌入模型 · ES |
| 验收 | 分词探针 · r4-A 分象限对比 · 结论回写 · 不碰主库 |
| failure_paths | 编译失败 / COPY 漂移 / query-index 配置不一致 / +5～8pp 弃 A |
| `invoke_retention_profile` | `minimal` |
| `graph_change_layer` | `none` |
| `wiki_delta` | `n/a` |

## 条件

- 维护者已补充 Dockerfile / COPY / 判读三档（含 +5～8pp 弃 A）
- **实跑镜像构建、灌库、金样评测由维护者执行**；30 只交付可运行产物与单测
- query/index 必须同 `chinese`（`RAG_FTS_CONFIG`），不得只改 DSN

## HG-AUDIT-R1 建议

**approved**（维护者已口头签收 · 本文件留痕）
