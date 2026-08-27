# GUIDE：细 Intent 与粗 router 并存（S2-b）

> **状态**：active  
> **对齐**：`docs/spec/agent-infra/strategy/ROADMAP_strategy_builder_v0.md` §7  
> **规划**：`docs/spec/agent-infra/03_strategy_and_intent_plan_v0.md` §5 / §8

## 两图职责

| 图 | 职责 | S2 是否改 |
|---|---|---|
| **router**（mode=`router`） | 外层安全闸：`rag` / `direct` / `refuse` | **否**（拓扑与 `RouteDecision` 保持） |
| **supervisor**（mode=`supervisor`） | 细 Intent → Builder allowlist → Work Planner | **是**（插 `intent` 节点） |
| **basic** | 对照单 rag | **否** |

拓扑（supervisor，静态 compile）：

    START → intent_node → strategy_builder → supervisor → dispatch → … → END

节点 id 为 ``intent_node``（LangGraph 禁止与 state key ``intent`` 同名）；state 字段仍为 ``intent``。

router 仍为：

    START → router → rag | direct | refuse

## 原则

- 一个 prompt **不**兼做安全三路与策略输入。
- Intent 失败走保守 fallback（`domain=unknown` · `needs_tool/needs_skill/is_composite=False` · `risk_hint=low` · `summary=""`），**不**映射为 router 的 `refuse`（refuse 只存在于 router 图）。
- Builder 读 `needs_tool=False` → 空 capability allowlist（沿用 S1 空表 fallback 单 rag）；`True` → 仍 ⊆ Registry∩Policy。
- `needs_skill` 本波仍写空 `allowed_skill_ids`；`risk_hint` **不得**绕过 Policy。
- Host 校验（SO / allowlist / Policy）不可做成模型可选 tool。

## 非范围

- 改 `app/ops/chat/graph.py` 拓扑
- 改 router / basic 图拓扑
- S3 YAML manifest · S4 Critic rebind · Skill 执行引擎
