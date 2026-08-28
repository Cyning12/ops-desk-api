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
| S2 | **DONE** | 2026-08-27 · [#80](https://github.com/Cyning12/ops-desk-api/pull/80) **MERGED** · Intent schema + 节点 |
| S3 | **DONE** | 2026-08-28 · [#82](https://github.com/Cyning12/ops-desk-api/pull/82) **MERGED** · catalog manifest |
| S4 | 00 验收 PASS | `task/critic-rebind` · S4-a–c · 待 PR |

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

## 6. 00 定夺（S2 · Intent · 2026-08-27）

维护者会话「按 S1 的 00 身份继续开始 S2」。

| 项 | 定夺 |
|---|---|
| 挂点 | **仅 supervisor 图**：`START → intent_node → strategy_builder → supervisor → …`（节点 id 不能为 `intent`：LangGraph 禁止与 state key 同名） |
| router 图 | **不改拓扑**；`rag\|direct\|refuse` 仍为 mode=router 外层安全闸 |
| Schema | `IntentV1`：`domain`（`ops_kb\|general\|unknown`）· `needs_tool` · `needs_skill` · `is_composite` · `risk_hint`（`low\|medium\|high`）· `summary` |
| 落点 | schema：`app/ops/lg_rag/schemas/intent.py`；节点：`app/ops/strategy/intent.py`；state：`LgRagState.intent: dict` |
| SO | **新节点**走 `acomplete_structured`（`max_retries=1`）；失败 **不**拒整图：写保守 fallback intent（`domain=unknown` · `needs_tool=False` · `needs_skill=False` · `is_composite=False` · `risk_hint=low` · `summary=""`）+ span `intent_fallback` / `structured_output_fallback` |
| Prompt | H4 槽 `lg_rag.intent.system`；禁止把业务三路 prompt 塞进 Intent 节点硬编码 |
| Builder 消费 | `needs_tool=False` → 空 capability allowlist（沿用 S1 空表 fallback 单 rag）；`needs_tool=True` → 仍 ⊆ Registry∩Policy（S1 候选求交）；`needs_skill=True` 本波 **仍写空** `allowed_skill_ids`（不实现 Skill 引擎）；`risk_hint` **不得**绕过 Policy |
| 图谱 | G-L1 仅 `lg_rag` 备注 + `10_flow_lg_rag` 增 `s_intent`；**不**新增一级模块 |

---

## 7. 附录 · 细 Intent 与粗 router 并存（S2-b）

| 图 | 职责 | S2 是否改 |
|---|---|---|
| **router**（mode=`router`） | 外层安全闸：`rag` / `direct` / `refuse` | **否**（拓扑与 `RouteDecision` 保持） |
| **supervisor**（mode=`supervisor`） | 细 Intent → Builder allowlist → Work Planner | **是**（插 `intent` 节点） |
| **basic** | 对照单 rag | **否** |

原则：一个 prompt **不**兼做安全三路与策略输入。Intent 失败走保守 fallback，**不**映射为 router 的 `refuse`（refuse 只存在于 router 图）。

详规可与本附录并列：实现时可落 `docs/guides/GUIDE_intent-vs-router-coexistence_v0.md`（与本表一致即可）。

---

## 8. 00 定夺（S3 · Catalog manifest · 2026-08-28）

维护者会话「继续 S3」。

| 项 | 定夺 |
|---|---|
| 职责 | Host 加载 YAML/JSON → `register`；Builder **只读** `list_capabilities`，不解析 manifest |
| 落点 | `app/ops/capability/manifest.py`（Host 路径）；内置 `app/ops/capability/manifests/builtin.v1.yaml` |
| 格式 | YAML + JSON；`yaml.safe_load`（仓内已有 pyyaml）；无密钥字段 |
| kind | **仅 `local_fn`**（MCP/sandbox/cli/skill **不**走本波 manifest） |
| adapter 白名单 | 形如 `local_fn:<module>:<attr>`；**仅**前缀 `app.ops.capability.defaults`；禁止任意模块 import / eval |
| `enabled: false` | 跳过，不 register |
| defaults 迁移 | builtin YAML 为三枚默认能力**目录真值**；`ensure_default_capabilities` **优先** load builtin（幂等 skip 已注册）；文件缺失才回退 `_DEFAULT_SPECS` 硬编码 |
| 热加载 | **禁止**每请求加载。S3-b：load 结果带 `version` + `capability_manifest_count`（模块级 metadata / span）；可提供 **显式** `reload_capability_manifest` 供测试/运维，不挂 HTTP 路径 |
| 图谱 | G-L1 **`capability` 行备注** + `10_flow_capability` 增 load 节点；**不**改 supervisor/router/chat 图拓扑；不新增一级模块 |

非法 adapter / 未知 kind / 缺 id → 该条拒绝并记录；不中断其余合法条目（或整文件失败——**00：整文件失败更安全**，避免半套目录；单测覆盖）。

---

## 9. 00 定夺（S4 · Critic rebind · 2026-08-28）

维护者会话「继续 S4」。

| 项 | 定夺 |
|---|---|
| 挂点 | **仅 supervisor 图**：`aggregator → critic_node` 条件边（替换 `aggregator → END`） |
| 节点 id | `critic_node`（避让 state key）；state：`critic_verdict: dict` · `inner_retry_count: int` · `rebinding_count: int` |
| 判定 | **规则 stub**（无 LLM）；不实现 intent→② 回环 |
| verdict | `pass` → END；`retry_planner` → supervisor（同 catalog）；`rebind` → strategy_builder；`end` → END |
| 预算 | `MAX_INNER_RETRIES=1` · `MAX_REBINDING=1`；超预算强制 `end`（单测无死循环） |
| 重置 | 回环时覆盖 `subtasks=[]`；`subtask_results` 自定义 reducer：`None` = 清空，否则 append（否则 `add` 无法重拆 plan） |
| 规则 | 无 `error` → pass；有 error 且空 allowlist → rebind（未超预算）；有 error 且非空 allowlist → retry_planner；已超预算 → end |
| rebind 语义 | **结构闭环**（再跑 Builder）；本波 **不**自动扩权绕过 Policy |
| Prompt/SO | 本波不强制 LLM Critic；可留 `CriticVerdict` schema 供后波 |
| 图谱 | G-L1 `lg_rag` 备注 + `10_flow_lg_rag` 增 `s_critic`；不新增一级模块；**不**改 chat/router/basic 拓扑 |

span：`critic_outcome` · `inner_retry_count` · `rebinding_count`（`strategy_builder_catalog_count` 已有）。

---

## 10. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 初版：对齐 03 规划 · S1–S4 交付项 |
| 2026-08-27 | S0 签收 · 落地状态表 · 钉死 None/空 allowlist 语义 |
| 2026-08-27 | S1 实现 00 验收 PASS · [#78](https://github.com/Cyning12/ops-desk-api/pull/78) **MERGED** |
| 2026-08-27 | S2 开工：00 定夺挂点 / SO / Builder 消费 · 并存附录 |
| 2026-08-27 | S2 00 验收 PASS（pytest 48 · graph-compile）；[#80](https://github.com/Cyning12/ops-desk-api/pull/80) **MERGED** |
| 2026-08-28 | S3 开工：00 定夺 loader / adapter 白名单 / 热加载边界 |
| 2026-08-28 | S3 00 验收 PASS（pytest 63 · graph-compile）；[#82](https://github.com/Cyning12/ops-desk-api/pull/82) **MERGED** |
| 2026-08-28 | S4 开工：00 定夺 critic stub / 预算 / 回环重置 |
| 2026-08-28 | S4 00 验收 PASS（pytest 29 · graph-compile） |
