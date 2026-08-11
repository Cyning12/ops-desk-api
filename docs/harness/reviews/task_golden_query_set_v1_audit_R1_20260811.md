# Task Audit R1：golden-query-set-v1

> **task**：`docs/tasks/active/task_golden_query_set_v1.md`  
> **日期**：2026-08-11 · 审查：维护者签收（会话内「签收，在新分支进行」）  
> **结论**：`pass` · 建议 `HG-AUDIT-R1=approved`

---

## 核对

| 项 | 审阅 |
|---|---|
| 范围 | 金样 yaml + R-4 eval runner；不改生产检索主路径语义 |
| 非范围 | A/C 臂、glossary 先手、灌库改造 |
| 验收 | runner 加载 71 条；断言 recall@5 / min_relevance / citation_in_hits / must_refuse；卫生过滤；分象限报告 + SPEC 三字段 |
| failure_paths | LLM 生成质量 / 标注分歧 — 可重试 |
| `invoke_retention_profile` | `minimal` |
| `graph_change_layer` | `none` |

## 条件

- 规模由 40→71 已写入 task 表（人签）
- expect_hit 人核仍为开放人节点；不挡 runner 实现

## HG-AUDIT-R1 建议

**approved**（维护者已口头签收 · 本文件留痕）
