---
name: s-l1-tech-graph-ops
description: 日常需求下如何判定 G-L 层、更新图谱、填写 task 字段、跑 compile。
pdd_default: 0
pdd_escalate_to: 1
---

# S-L1 · 技术图谱日常操作（ops-desk-api）

> **一句话**：改码后同步图谱；拓扑变才改 G-L2。  
> **何时用**：多数功能 task、改某域、更新某 flow。

## PDD-0 检查表

1. 读 `l1/01_modules.md` 确认 module_id  
2. 按需打开 `l1/10_flow_*.md`（禁止默认全开）  
3. chat 域改入口/符号 → 查 `l2/indexes/by_path.yaml` / `by_symbol.yaml`  
4. 改 yaml 后跑 `./scripts/graph-compile.sh`  
5. task 必填：`graph_change_layer` · `review_hat`（默认 20）

## 层判定（简）

| 变更 | graph_change_layer |
|------|-------------------|
| 仅实现细节、同 symbol | `none` 或不动 G-L2 |
| 模块边界 / 新 flow | `G-L1` |
| 入口符号 rename、搬家、implementedBy | `G-L2` |
| 跨仓 POINTER / 00_main 骨架 | `G-L0` |
| 多层 | `mixed` |

## 命令

```bash
./scripts/graph-compile.sh
# graph.json 真值：docs/_tech_graph/shared/graph.json
```

## 热点 flow

- Chat：`docs/_tech_graph/l1/10_flow_chat.graph.yaml`
- Auth：`docs/_tech_graph/l1/10_flow_auth.graph.yaml`
- Sync→Chat：`docs/_tech_graph/l1/11_flow_sync_to_chat.graph.yaml`
