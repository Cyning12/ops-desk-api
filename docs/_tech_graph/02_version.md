# 图谱版本时间线

| 日期 | 版本 | 事件 |
|---|---|---|
| 2026-07-16 | v1.0.0 | 初始版本，基于当前源码生成 `00_main` 与 `10_flow_chat`；`answer_node` 与 LLM Provider 为 TODO |

## 机器轨

- schema: `inform_graph.v3`
- source yaml: `docs/_tech_graph/*.graph.yaml`
- compiled md: `docs/_tech_graph/*.md`
- graph.json: `docs/_tech_graph/graph.json`（兼容 harness v2 `graph yaml check`）
- compile script: `scripts/graph-compile.sh`
