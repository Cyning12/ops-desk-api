# 图谱版本时间线

| 日期 | 版本 | 事件 |
|---|---|---|
| 2026-07-16 | v1.0.0 | 初始版本，基于当前源码生成 `00_main` 与 `10_flow_chat` |
| 2026-07-27 | v1.1.0 | 物理分层 G-L0/G-L1/G-L2：`l0|l1|l2|shared`；模块真值 `l1/01_modules.md`；chat G-L2 indexes；`shared/graph.json`（C1） |
| 2026-08-23 | v1.2.0 | W1：`00_main` 挂 lc/lg 路由；`10_flow_chat` 追平 RAG 链（retrieve→grade→refuse） |
| 2026-08-26 | v1.2.1 | 清理过渡：停根 `graph.json` 双写；删 `01_struct` stub（真值仍 `l1/01_modules`） |
| 2026-09-21 | v1.3.0 | 追平 09-20~09-21 集中开发（task_tech_graph_recent_sync）：**新增一级模块 `hitl`**；`capability` 治理层（`_prepare_call` 闸链/熔断/降级/配额/幂等/`output_schema`/观测端点/红线 R0–R15）；`lg_rag` supervisor 增 `subtask_join`+`observe`（HITL interrupt/resume 回路 · ReAct 收口）；`db` 补 `ops_hitl_requests`；依赖基线 langgraph 1.2.11 / checkpoint-postgres 3.1.2 |

## 机器轨

- schema: `inform_graph.v3`
- source yaml: `docs/_tech_graph/**/*.graph.yaml`（递归）
- compiled md: 与 yaml 同目录
- graph.json 真值: `docs/_tech_graph/shared/graph.json`
- compile script: `scripts/graph-compile.sh`
