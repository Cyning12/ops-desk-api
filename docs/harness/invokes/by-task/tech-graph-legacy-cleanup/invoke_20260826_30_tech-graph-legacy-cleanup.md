# Invoke · 30-execute · tech-graph-legacy-cleanup

**task_slug**: `tech-graph-legacy-cleanup`  
**hat**: `30-execute`  
**timestamp**: 2026-08-26T06:15:00Z  
**actor**: Auto  
**outcome**: success

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | 本窗授权代签 | Y | N | Y |
| HG-AUDIT-R1 | approved | 本窗授权代签 | Y | Y | Y |
| HG-GRAPH-MODULES | approved（l1/01_modules） | — | Y | Y | Y |

reviews：`task_tech_graph_legacy_cleanup_audit_R1_20260826.md` 存在且 PASS · 是  
pre-30 invoke：10 齐全 · 是  
verify：PASS  

结论：可进入改码

## 变更摘要

- 停 `graph_yaml_to_json.py` 根双写；删 `docs/_tech_graph/graph.json`
- 删 `01_struct.md`；更新 README / `02_version` / `99_mermaid_protocol` / `01_modules` / `00_main` Sub-graph Links / AGENTS 闸路径句
- 删 `.cyning-harness/QUICKREF.md` + `backups/`；gitignore `backups/`
- 删 `scripts/legacy/` 全套 bak + README；更新 compile 脚本注释
