# coding_wiki · stable

> **层**：stable · 每次会话可注入的短摘要（≤15 行正文建议）

## 相关页

- 读序总览：[[README]]
- 主题索引：[[_index]]
- 项目指针：[[context]]
- 本 task 易变上下文：[[volatile]]
- 目录约定：[[topics/wiki_layout]]

## 编码底线（摘要）

1. 最小改动 · 不扩 scope  
2. 类型严格 · 禁滥用 Any / 缺注解  
3. 错误结构化返回（HTTPException / SSE error）  
4. 测试策略见 task `test_strategy`  
5. 图谱优先于纯文本臆造；改路由/表/事件先对 `_tech_graph`

完整条文（**真值，勿在此复制**）：

- L1：[`../standards/CODING_BASELINE_L1_v1_zh.md`](../standards/CODING_BASELINE_L1_v1_zh.md)
- L2：[`../standards/CODING_BACKEND_L2_v1_zh.md`](../standards/CODING_BACKEND_L2_v1_zh.md)

## IDE 入口

- Cursor：`.cursor/rules/*`
- Claude Code：`CLAUDE.md`
- 通用：`AGENTS.md`
