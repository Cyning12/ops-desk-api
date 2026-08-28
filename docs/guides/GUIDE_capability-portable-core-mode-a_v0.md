# GUIDE：Capability · 可迁移内核 Mode A（filter / plan-in-state）v0

> **状态**：active  
> **上游**：[`../spec/agent-infra/capability/ROADMAP_portable_core_v0.md`](../spec/agent-infra/capability/ROADMAP_portable_core_v0.md) §U1–U2  
> **架构**：[`../spec/agent-infra/00_architecture_and_boundaries.md`](../spec/agent-infra/00_architecture_and_boundaries.md) §3–§4

---

## 1. Mode A 主路径（可带走）

```text
register(spec, adapter)
list_capabilities(filter=…)   → 赋能列表（纯数据）
schemas_for_llm(filter=…)     → OpenAI 风格 schema（纯数据 · 无 LG）
invoke(id, args, ctx=…)       → CapabilityResult（未知 id → ok=False）
```

目录可由 Host `load_capability_manifest`（YAML/JSON）register；Builder 只读 `list_capabilities`，不解析 YAML。契约见 [`../spec/agent-infra/strategy/ROADMAP_strategy_builder_v0.md`](../spec/agent-infra/strategy/ROADMAP_strategy_builder_v0.md) §8。禁止每请求加载；显式 `reload_capability_manifest` 仅测试/运维。

默认包 `from app.ops.capability import …` **零 langgraph**。  
可选 FC / ToolNode（Mode B）须显式：

```text
from app.ops.capability.extras.langchain import as_structured_tools, as_tool_node
```

---

## 2. Filter 推荐（planner / tool_exec）

| 场景 | 推荐 `CapabilityFilter` | 说明 |
|---|---|---|
| Supervisor / planner 赋能列表 | `kinds=frozenset({"local_fn"})` + `tags_any=…`（按业务域裁剪） | 给模型看「能调什么」；宜窄不宜全表 |
| tool_exec 执行侧 | 同上或按 plan 中已选 id 直接 `invoke` | 主路径是 **按 id invoke**，不必再 list 全量 |
| 探针 / skill | `kinds=frozenset({"mcp"|"sandbox"|"cli"|"skill"})` | 默认不进 defaults；须显式 register |

字段约定（现行 `_match_filter`）：

| 字段 | 行为 |
|---|---|
| `kinds` | 精确匹配 `spec.kind` |
| `tags_any` | 与 `spec.tags` 有交集即过 |
| `deny_high_risk` | 剔除 `risk_level=high` |
| `enabled=False` | 带 filter 时不可见；`invoke` → `ok=False` + `blocked=disabled` |
| `node_role` / `mode` | **占位**：单独传入**不裁剪**；写入 ctx / 观测用；裁剪请用 `kinds`/`tags_any` |

示例：

```python
from app.ops.capability import CapabilityFilter, list_capabilities, invoke

# planner：仅 local_fn + issue 标签
planner_caps = list_capabilities(
    filter=CapabilityFilter(
        node_role="supervisor",  # 占位记录角色；真正裁剪靠 kinds/tags
        kinds=frozenset({"local_fn"}),
        tags_any=frozenset({"issue"}),
    )
)

# tool_exec：按 plan 子任务 id 调用
result = invoke("mock_get_issue_status", "查 #128", ctx={"node_role": "tool_exec"})
```

---

## 3. Plan-in-state（不是新图）

```text
静态图：planner → dispatch ⇄ workers(tool_exec/…) → aggregator → END
              ↑____________________|
```

1. Planner 读 `list_capabilities(filter=…)` → 产出 **plan 数据**（子任务 / capability_id 列表）写入 **state**。  
2. 固定 `dispatch` / `tool_exec` 解释 state 中的 plan，逐条 `invoke`。  
3. **默认禁止**每个请求 `StateGraph().compile()` 出一张新图。  
4. 未知 `capability_id` → `ok=False`，不中断后续子任务（见 failure_paths）。

心智模型：编排壳（已 compile）+ Capability Gateway（可插拔）+ plan 数据（state）≠ 动态构图。

---

## 4. 与 extras 的边界

| 路径 | 依赖 | 用途 |
|---|---|---|
| `app.ops.capability` | 无 langgraph | Mode A 可迁移内核 |
| `app.ops.capability.extras.langchain` | langgraph ToolNode | 可选 Mode B smoke / 外部自建 FC |

`schemas_for_llm` 留在内核：纯 dict 列表，供外部自建 `bind_tools`，不内置 ToolNode。

---

## 5. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-26 | 初版：U2 filter 推荐 + plan-in-state；配合 portable-core U1 |
| 2026-08-28 | S3：一行指针回 ROADMAP §8（manifest 加载 · Builder 不解析 YAML） |
