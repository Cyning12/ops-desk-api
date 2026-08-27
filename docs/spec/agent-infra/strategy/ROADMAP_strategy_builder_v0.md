# ROADMAP：Strategy Builder（L2 · 可拆 task）

> **层级**：L2 路线（strategy 域）  
> **状态**：`active`（S0 签收 · 随 [`../03_strategy_and_intent_plan_v0.md`](../03_strategy_and_intent_plan_v0.md)；**不**直接授权 30）  
> **架构边界**：[`../00_architecture_and_boundaries.md`](../00_architecture_and_boundaries.md) §4 / §4.1

### 人工闸（S0）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | approved | 2026-08-27 · **00 代签 · 维护者 Prompt 授权** |

### 落地状态

| 波次 | 状态 | 说明 |
|---|---|---|
| S0 | **DONE** | 03 + 本 ROADMAP 签收 · 2026-08-27 |
| S1 | **DONE** | 2026-08-27 · [#78](https://github.com/Cyning12/ops-desk-api/pull/78) **MERGED** · allowlist 闭环 |
| S2–S4 | pending | 非本棒 |

---

## 1. 目标

落地 **Strategy Builder**：本轮可见 capability/skill 白名单进入 state；Work Planner（`supervisor_node`）只消费该集；可选 Critic 回环（同 catalog / rebind）；目录支持 manifest 动态加载。

### 非目标

- 替代 H2 Policy  
- Builder LLM 直接 `register` / 改 Host policy 键  
- 每请求动态 compile 新图  
- 完整 Skill 引擎（仍 H5 边界）  
- 无预算全图 ReAct

---

## 2. 交付项

| ID | 内容 | 验收 |
|---|---|---|
| S1-a | `LgRagState`（或等价）增加 `allowed_capability_ids`（及可选 `allowed_skill_ids`） | 类型 + 单测 |
| S1-b | Strategy Builder 节点（首版可规则/配置）：写 allowlist；须 ⊆ Registry ∩ Policy 可见 | 非法 id 剔除 + span |
| S1-c | `supervisor_node`：`list_capabilities(filter)` **∩** state allowlist；空 allowlist 语义钉死（拒绝 tool / fallback） | 单测 |
| S1-d | tool id Host 校验改为相对 **本轮可见集**（继承 H1） | 非法 → fallback 语义不回归 |
| S2-a | Intent schema v1（域 · 需 tool/skill · 复合 · 风险提示等）+ `parse_only`/`acomplete` 选型 | schema 单测 |
| S2-b | 与粗 `router`（`rag|direct|refuse`）并存策略文档化 | GUIDE 或本 ROADMAP 附录 |
| S3-a | YAML/JSON capability manifest 加载 → `register`；与 `defaults.py` 迁移策略 | 单测 + 无密钥进仓 |
| S3-b | 热加载版本号 / 观测字段（可选） | metadata |
| S4-a | Critic：达标判定 stub（规则或 LLM+SO） | mock |
| S4-b | 条件边：同 catalog → supervisor；缺能力 → Builder rebind；预算耗尽 → END | 单测无死循环 |
| S4-c | span：`rebinding_count` · `strategy_builder_catalog_count` · `critic_*` | 与 tracing 兼容 |

---

## 3. 建议 task 颗粒度

| slug（建议） | 覆盖 | 前置 |
|---|---|---|
| `strategy-builder-allowlist` | S1-a–d | H1 CLOSE · 本 ROADMAP S0 签收 |
| `intent-schema-v1` | S2-a–b | S1 |
| `catalog-manifest-yaml` | S3-a–b | S1 |
| `critic-rebind` | S4-a–c | S1 + 建议 S2 |

`graph_change_layer`：多为 `G-L1`（`lg_rag` / 新 `strategy` 模块备注）。  
`test_strategy`：`required` · mock LLM + registry。

---

## 4. 与 H1 filter 的关系

现 H1：

```text
_SUPERVISOR_CAP_FILTER = CapabilityFilter(
    node_role="supervisor",
    kinds=frozenset({"local_fn"}),
    deny_high_risk=True,
)
```

S1 后：

```text
visible = list_capabilities(filter=_SUPERVISOR_CAP_FILTER)
if state.allowed_capability_ids is not None:
    visible = [s for s in visible if s.capability_id in allowlist]
```

**00 定夺（S1 · 2026-08-27）**：

- `None` allowlist：**不**再兼容「仅 filter」；supervisor 图路径 **强制**经 Builder 写 list（缺字段视为实现错误，测试须覆盖 Builder 前置）。  
- 空 allowlist `[]`：禁止 `type=tool`；整 plan **fallback 单 rag**（继承 H1 非法 tool 语义，不回归）。

---

## 5. Manifest 草案形状（非契约终态）

```yaml
version: 1
capabilities:
  - id: utc_now_iso
    kind: local_fn
    description: 只读 UTC ISO
    tags: [readonly, time]
    risk_level: low
    enabled: true
    adapter: local_fn:app.ops.capability.defaults:utc_now_iso
```

- 解析与 `register` 仅 Host 路径；CI 默认加载内置/fixture，不连外网。  
- adapter 指针白名单，禁止任意代码执行路径（安全闸另文）。

---

## 6. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 初版：对齐 03 规划 · S1–S4 交付项 |
| 2026-08-27 | S0 签收 · 落地状态表 · 钉死 None/空 allowlist 语义 |
| 2026-08-27 | S1 实现 00 验收 PASS · [#78](https://github.com/Cyning12/ops-desk-api/pull/78) **MERGED** |
