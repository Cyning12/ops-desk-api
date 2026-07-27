---
name: s-l0-project-map
description: ops-desk-api 全局地图；大型需求、跨仓、G-L0 变更、onboarding 时使用。
pdd_default: 0
pdd_escalate_to: 1
---

# S-L0 · 项目地图（ops-desk-api）

> **一句话**：先弄清本仓在 Ops-desk 中的位置，再下钻模块。  
> **何时用**：跨仓、架构、新人、改 G-L0。  
> **不要**：粘贴整份 `00_main` Mermaid；禁止双写拓扑（真值在 `_tech_graph`）。

## PDD-0

1. Open Folder = `ops-desk-api/`
2. 读 `AGENTS.md` → active task → `docs/_tech_graph/README.md`
3. G-L0：`l0/00_main.md` + `l0/POINTERS_cross_repo.md`
4. 配对仓：web（契约消费）· ios（未分层）· workspace（编排）

## PDD-1

| 先读 | 路径 |
|------|------|
| 分层约定 | `docs/_tech_graph/LAYER_README.md` |
| 模块表 | `docs/_tech_graph/l1/01_modules.md` |
| 规格长文 | `Projects/.../graph_skill_layering_v1/`（POINTER） |

Phase：本仓为 **α** 主执行；web=γ；ios=δ 后置。
