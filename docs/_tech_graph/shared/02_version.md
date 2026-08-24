# 图谱版本时间线

| 日期 | 版本 | 事件 |
|---|---|---|
| 2026-07-16 | v1.0.0 | 初始版本，基于当前源码生成 `00_main` 与 `10_flow_chat` |
| 2026-07-27 | v1.1.0 | 物理分层 G-L0/G-L1/G-L2：`l0|l1|l2|shared`；模块真值 `l1/01_modules.md`；chat G-L2 indexes；`shared/graph.json`（C1） |
| 2026-08-23 | v1.2.0 | W1：`00_main` 挂 lc/lg 路由；`10_flow_chat` 追平 RAG 链（retrieve→grade→refuse） |

## 机器轨

- schema: `inform_graph.v3`
- source yaml: `docs/_tech_graph/**/*.graph.yaml`（递归）
- compiled md: 与 yaml 同目录
- graph.json 真值: `docs/_tech_graph/shared/graph.json`（根目录过渡双写）
- compile script: `scripts/graph-compile.sh`
