# invoke · 30 · tech-graph-recent-sync · 2026-09-21

- **hat**：30（实现 · 图谱维护，无 app/ 代码改动）
- **闸扫描（首输出）**：HG-TASK-DRAFT=approved · HG-AUDIT-R1=approved · HG-GRAPH-MODULES=approved（均 2026-09-21 维护者令「不切分支，直接在当前分支开始」· 00 代签，落 task 人工闸表）→ **开工**
- **分支**：`chore/upgrade-langgraph-1.2`（维护者令不切分支）
- **工作面**：`docs/_tech_graph/l1/01_modules.md` · `l1/10_flow_capability.graph.yaml` · `l1/10_flow_lg_rag.graph.yaml` · `shared/02_version.md`；md 由 `./scripts/graph-compile.sh` 重新生成，不手改 `shared/graph.json`
- **禁区**：不改 `app/` `tests/` `alembic/`；图谱陈述与代码冲突时改图谱不改码并记录
