# 过程 · Skill 与 task 字段策略

> **Wave**：W0  
> **目标**：防止补齐后再次滑回「只改模块表半句」

---

## 1. 问题陈述

2026-08 旁路域 task 模式：

```text
graph_change_layer: G-L1
graph_delta: docs/_tech_graph/l1/01_modules.md
graph_delta_note: …不新增一级模块…
```

验收：`graph-compile.sh` 绿 + 模块表备注更新 → **不要求** `10_flow_*`。

---

## 2. W0 补丁清单（维护者签收）

### 2.1 `docs/skills/s-l1-tech-graph-ops/SKILL.md`

在「层判定」表后增 **POINTER**（不展开长文）：

| 场景 | 最低图谱动作 |
|------|--------------|
| 新 `POST/GET` 路由（新域） | G-L0 挂节点 + 新建或更新 `10_flow_*` |
| 新 LangGraph / LCEL 拓扑 | `10_flow_*` yaml · **禁止**只写 `01_modules` 长备注 |
| 仅改节点实现、同 symbol | `none` 或不动 G-L2 |
| chat 入口 symbol 变更 | 更新 `10_flow_chat` + `l2/indexes` |

链到：`docs/spec/inform-graph-backfill/README.md`

### 2.2 功能 task 模板（`docs/harness/` 或维护者口传）

`graph_delta` 禁止默认仅 `01_modules.md` 当：

- 新增 `app/ops/<domain>/router.py` HTTP 端点
- 改 `StateGraph` 条件边
- 新增一级 `module_id`

应写：

```text
graph_delta:
  - docs/_tech_graph/l0/00_main.graph.yaml
  - docs/_tech_graph/l1/10_flow_<domain>.graph.yaml
graph_delta_note: 见 docs/spec/inform-graph-backfill/modules/<domain>.md
```

### 2.3 PR 模板（可选）

```markdown
- [ ] 涉及路由/Agent 拓扑 → 已按 inform-graph-backfill spec 更新 _tech_graph
- [ ] `./scripts/graph-compile.sh` 绿
```

---

## 3. `HG-GRAPH-MODULES` 语义（不变）

- 仍只挡 **模块表未签** 的 30 改码
- 补齐棒完成后：签备注改为「flow 已建 · 见 10_flow_*」

不请求把 HG 扩成 flow 覆盖机械闸（那是 W5 coverage 脚本职责）。

---

## 4. 与 AGENTS.md 关系

`AGENTS.md` 已有「新增路由/表/事件须同步 `_tech_graph/`」— W0 把 **最低文件集** 写清，减少 Agent 误判为「改备注即可」。

---

## 5. 验收清单（W0）

- [ ] Skill POINTER 已合并（或维护者明确延期）
- [ ] 下一棒功能 task 试用新 `graph_delta` 格式
- [ ] 本 spec 包在 `README.md` 被 `AGENTS.md` 或 `docs/spec/` 索引（可选 POINTER）

---

## 6. 非范围

- 修改 `HG-GRAPH-MODULES` 闸定义（产品 harness 层）
- 强制 pre-commit
