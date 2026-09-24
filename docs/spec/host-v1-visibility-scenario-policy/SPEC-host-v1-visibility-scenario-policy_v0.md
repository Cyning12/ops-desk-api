# SPEC：Agent Host V1-B · 可见集两阶段 + manifest 可撤销性四字段（visibility-scenario-policy）（v0）

> **层级**：L1 波次 SPEC（07 L0 规划的 V1-B 波 · 依赖 V1-A CLOSE）  
> **状态**：`signed`（HG-SPEC-SIGNOFF=**approved** · 2026-09-23 · **00 代录** · 维护者令原话：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」+ 本窗令「继续，完成后自行进行下一波，无特殊情况无需停下等待接收命令」· 承 07/08/V1-A 同令代录先例）  
> **种子**：[`../agent-infra/08_host_v1_wave_spec_outlines_v0.md`](../agent-infra/08_host_v1_wave_spec_outlines_v0.md) §2（signed · 本 SPEC 为其正式展开，冲突以本 SPEC 为准）  
> **上游**：[`../agent-infra/07_host_v1_landing_plan_v0.md`](../agent-infra/07_host_v1_landing_plan_v0.md)（signed）· [`03_strategy_and_intent_plan_v0.md`](./03_strategy_and_intent_plan_v0.md)（active · S1–S4 CLOSE · **风险档对齐真值**）· [`../host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md`](../host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md)（signed · V1-A · requested_scope 是本波裁剪输入）  
> **下游**：HG-SPEC-SIGNOFF → 00 出 task → 20-task-audit → HG-AUDIT-R1 → 30（委派子 Agent · 分支 `task/host-v1-visibility-scenario-policy`）→ 40 → PR+CI 绿+merge → 图谱回写（00 代录）→ CLOSE  
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `host-v1-visibility-scenario-policy` |
| **invoke_slug** | `host-v1-visibility-scenario-policy`（task 阶段） |
| **test_strategy** | `required` |
| **test_strategy_note** | 两阶段裁剪矩阵断言 · 安全默认断言（fallback/歧义→空集）· 剔除台账断言 · 四字段加载期校验断言（非法→ManifestError · 矛盾声明拒绝 · 缺失兼容）· 缺失默认 HITL 三档模式断言 · off 零 diff 回归 |
| **默认分支** | `task/host-v1-visibility-scenario-policy`（自 `master` 分出；**禁止 master/main 直改**） |
| **graph_change_layer** | `G-L1` 行备注（`capability` 行：manifest 四字段 schema+加载期校验 · `lg_rag` 行：场景维第二阶段裁剪+剔除台账；**不新增一级模块**（strategy 承 C2 裁定归属 lg_rag 行）；HG-GRAPH-MODULES 随 30 回写 00 代录） |
| **freeze_id** | 无（manifest 格式**向后兼容演进**——缺字段不报错 · 不改 freeze 契约 · SSE 零新事件类型 · 零新 HTTP 路由 · 零新表） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | **approved**（2026-09-23 · 00 代录） | 维护者令原话留痕（见状态行 · 双令）；开放裁定 Q1/Q2/Q3 已答；00 可拆 task |

---

## 1. 背景与目标

### 现状与差距（承大纲 v0.2 #2/#3/#14 + 测评点 3/4）

Builder allowlist（Registry∩Policy · `strategy/builder.py` + `capability/baseline.py`）只是**身份维单阶段**裁剪；缺**场景维**（按请求意图/风险二次裁剪）两阶段管线与「宁可退化成无工具」安全默认的显式承诺；manifest 缺**可撤销性声明**（`reversible`/`execution_type`/`max_reversal_latency`/`requires_stop_support`——直接决定预授权模型与撤销窗口）。

### 关键实证（2026-09-23 本帽真读 · U2 消解）

- **意图风险档已存在**：`IntentV1.risk_hint: Literal["low","medium","high"]`（`app/ops/lg_rag/schemas/intent.py:25-28` · 03 轨 S2 落地）——承 07 §1.3「若 03 先落地风险档，V1-B 直接消费」，**本波不新增意图字段**。
- **fallback 裂缝**：`intent.py:22-24` fallback intent 默认 `risk_hint="low"`——SO/LLM 失败时风险档虚假宽松；场景维必须以 `intent_fallback` 标记区分「模型明确判 low」与「fallback 默认 low」。
- **能力侧危险度已有二维**：`CapabilitySpec.risk_level`（low/medium/high）与 `side_effect`（none/read/write/irreversible）不可互相代理（`types.py:7-13` 钉死）；`hitl_required` 已有加载期强校验与执行侧消费。
- **基线已是只读**：`baseline_filter` deny_high_risk + deny_write（`baseline.py:33-44`）——场景维是在此之上的**第二轮收窄**，不是替代。

### 一句话目标

可见集升级**两阶段**：身份维（既有基线）→ 场景维（意图风险档+意图健康度驱动的确定性收窄 · 安全默认「宁可无工具」· 剔除项进台账）；manifest 可撤销性四字段 schema 化 + 加载期强制校验（非法/拒 · 缺失兼容但默认 HITL_REQUIRED 走观测灰度）。

### 设计纪律（跨波公共约束继承 · 签收时锁死）

1. **Host 权威**：裁剪是纯代码确定性函数（零 LLM · 可重放可机验）；策略键不可由模型写入；`requested_scope`（V1-A）只作为场景维的输入上界之一。
2. **默认关/观测模式上线**：场景维 `LG_RAG_VISIBILITY_SCENARIO_MODE=off|observe|enforce` 默认 off；四字段缺失默认 HITL `OPS_CAPABILITY_REVERSIBILITY_MODE=off|observe|enforce` 默认 off；非法值回退 off。
3. **审计记动作不记内容**：剔除项记 capability_id + 裁剪原因码（id 与原因码非内容）；四字段缺失记 undeclared 标记。
4. **零 freeze 动**：不改 freeze 契约；SSE 零新事件类型；零新路由；零新表；manifest 演进向后兼容。
5. **与 03 轨边界**：意图 schema 演以 03 现行 `IntentV1` 为准（本波只消费不改 schema）；若未来 03 轨调整 risk 档口径，裁剪表随之对齐（冲突回 10-spec）。

---

## 2. 范围（D 块展开 · 承 08 §2.2）

### D1 · 意图风险档消费（必做 · U2 已消解）

- **不新增意图字段**：直接消费 `IntentV1.risk_hint`（3 档 low/medium/high · Q1 裁定对齐 03 现行 schema）。
- `intent_node` 增写 state channel `intent_fallback: bool`（区分模型明判 vs fallback 默认 · 堵住 §1 裂缝）；state 增 channel（承 V1-A state.py 先例 · LgRagState 可选键）。
- **档位口径文档化**（随 SPEC 附带 · 进 builder docstring）：low=常规检索问答 · medium=跨域聚合/多步操作 · high=涉写意图/敏感域/模糊高影响请求。

### D2 · 场景维第二阶段裁剪（必做 · 核心）

新纯函数 `scenario_trim(base_visible: list[CapabilitySpec], intent: dict, intent_fallback: bool) -> tuple[list[CapabilitySpec], list[tuple[str, str]]]`（返回 最终可见集 + 剔除项 (id, reason) · 零 LLM 零 IO · 承 step_contract/delegation 纯函数形态），落 `app/ops/strategy/scenario.py`（strategy 薄包内 · 归属 lg_rag 行）。

**两阶段管线与落点**（2026-09-23 R1 审查 B-1 澄清 · 语义零改）：最终可见集语义 = **基线 ∩ 场景维 ∩ requested_scope**（三重交集 · 交换律等价 · 只收窄不放宽）。实现落点按数据可得性钉死：① **Builder 内**（图序 intent→builder · 意图已可得）：基础可见集（stage 1 · 既有 baseline_filter）→ 场景维（stage 2 · 本函数）→ **有效可见集**（供 supervisor 规划）；② **supervisor 节点内**（`multi/nodes.py:933-948` · V1-A 已 merge 真值 · requested_scope 仅在 supervisor LLM 产出后存在）：`delegation_scope = requested_scope ∩ 有效可见集`（交集输入由裸 allowlist 改为**场景维后的有效可见集**——保证委派令牌不越场景维 · 对 V1-A 的唯一接线改动）。

**裁剪规则表（v1 裁定 · 确定性 · 按序适用）**：

| # | 条件 | 动作 | reason 码 |
|---|---|---|---|
| S1 | `intent_fallback=True`（SO/LLM 失败 · 意图不可信） | **退化为空集**（安全默认 · 宁可无工具） | `intent_fallback` |
| S2 | `needs_tool=False` | 空集（既有行为承接 · 不新增语义） | `needs_tool_false` |
| S3 | `domain=unknown` 且 `needs_tool=True`（意图域不可识别仍要工具 = 歧义） | **退化为空集** | `domain_unknown` |
| S4 | `risk_hint=high` | 剔除 `risk_level ∈ {medium}` 能力（high 已被基线剔除 · 只留 low） | `risk_high_tighten` |
| S5 | `risk_hint ∈ {low, medium}` | 不追加裁剪（基线即终态） | — |

- `is_composite`/`summary` **不作裁剪键**（自由文本/复杂度不作安全键 · 仅 span 观测）；Q2 裁定：场景维输入**仅意图+健康度标记，不含会话上下文**（见 §4 Q2）。
- 模式：off=跳过 stage 2（现状零 diff）· observe=计算剔除但放行（台账记 `would_strip`）· enforce=剔除生效。
- 性能：纯代码 <10ms（承工程方案 P2 出口 · 无循环外 IO）。

### D3 · 剔除项审计（必做 · #11 审计清单第一项落地）

- 剔除项 `(capability_id, reason)` 全量进台账：logger 结构化行（`visibility_scenario_stripped ids=[...] reasons={...}` · off 零日志）+ span metadata（`scenario_stripped_count`/`scenario_stripped_reasons`/`would_strip`）。
- 记动作不记内容：只记 id + 原因码 + 计数；不记 query/intent 原文。

### D4 · manifest 可撤销性四字段（必做）

`CapabilitySpec` 增四字段（frozen dataclass 兼容 · 默认 None=未声明）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `reversible` | bool \| None | 是否可撤销 |
| `execution_type` | str \| None | `instant \| target \| process` 三值词表（Q3 裁定映射见 §4） |
| `max_reversal_latency` | int \| None | 最大可接受撤销时延（秒 · 非负） |
| `requires_stop_support` | bool \| None | 是否需要 stop 支持（持续进程类能力） |

- **加载期强制校验**（`manifest.py` 新增校验面 · 承既有 V9/V10 纪律）：① 字段若声明则类型/词表合法（execution_type 三值 · reversible/requires_stop_support bool · max_reversal_latency 非负 int）——非法 → `ManifestError` 整文件失败（不留半套）；② **矛盾声明拒绝**：`side_effect=irreversible` 且 `reversible=true` → ManifestError（声明自相矛盾）；③ `execution_type=process` 且 `requires_stop_support` 缺失/false → ManifestError（process 必须声明 stop 支持）。
- **缺失兼容**：未声明 → **不报错**；运行时按 `OPS_CAPABILITY_REVERSIBILITY_MODE`：off=无行为 · observe=台账记 `reversibility_undeclared would_default_hitl` · enforce=该能力 `hitl_required` **派生为 True**（默认 HITL · 执行侧既有消费 · 不改执行语义）。
- **存量补齐**：`manifests/builtin.v1.yaml` 全量能力补四字段声明（数据面 · 保证 enforce 升级路径不误伤存量）；`hitl_required` 加载期强校验（write/irreversible/high 必须 True · 既有）与派生缺口的冲突以**声明优先**裁（显式声明四字段且合法 → 不派生）。
- **CI 静态面**：加载断言进 pytest（非法 manifest 拒 · 矛盾拒 · 缺失兼容 · builtin 四字段全覆盖断言）。

### D5 · 测试（必做）

1. 两阶段裁剪矩阵断言（S1–S5 × 能力 risk_level 组合 · 含 requested_scope 交集）
2. 安全默认断言：fallback/歧义 → 空集且台账可查；observe 模式 would_strip 不生效
3. 剔除台账断言：id+reason+计数（caplog/span）
4. 四字段加载期校验断言：非法值 ManifestError · 矛盾声明拒 · process 无 stop 拒
5. 缺失默认 HITL 三档断言：off 无行为 · observe 台账 · enforce 派生 hitl_required=True 且显式声明能力不派生
6. builtin.v1.yaml 四字段全覆盖断言
7. off 模式零 diff 回归（既有用例零改动全绿）
8. 冻结回归：SSE 零新事件 · 零新路由 · 零新表

---

## 3. 非范围

- ❌ HITL 三档执行侧全体系（PRE_AUTHORIZED / HITL_EXEMPT · 本波只做 **manifest 声明面**与缺失默认兜底 · 执行侧分级消费后续波）
- ❌ 意图 schema 演进（`IntentV1` 字段零改动 · 风险档消费不新增；演进属 03 轨）
- ❌ 场景维引入会话上下文/用户画像（Q2 裁定 · 留 V1-D 情景记忆后复盘）
- ❌ 动态 StateGraph compile · 跨进程可见集下发
- ❌ 改既有 freeze 契约 / 新 SSE 事件 / 新路由 / 新表
- ❌ 能力撤销执行机制（`reversible` 等是**声明**；撤销动作执行器不在本波）
- ❌ 改 03 轨 prompt 资产（`lg_rag.intent.system` 零改动 · risk_hint 口径已内嵌）

---

## 4. 开放裁定（必答题 · 全部作答）

### Q1 · 风险档粒度

| 方案 | 做法 | 裁决 |
|---|---|---|
| **S1 · 3 档 low/medium/high（对齐 `IntentV1.risk_hint` 现行 schema）** | 直接消费既有词表 · 零 schema 改 | **推荐（裁定）**：03 轨 S2 已落地该词表（07 §1.3「03 先落地 V1-B 直接消费」）；与能力侧 `risk_level` 三档天然对位 |
| S2 · 新增 4-5 档细分 | 改 IntentV1 + prompt 资产 | 弃选：改 03 轨 schema 越界（非范围）· 细分档位无裁剪规则承载（规则表只有「收紧/不收紧」两态语义） |

### Q2 · 场景维输入是否含会话上下文

| 方案 | 做法 | 裁决 |
|---|---|---|
| **S1 · 仅意图 + 意图健康度（intent_fallback）** | 裁剪键 = needs_tool/domain/risk_hint + fallback 标记 | **推荐（裁定）**：确定性可重放可机验（Host 权威）；会话上下文（历史轮/画像）引入不可控维度且无可证伪的裁剪规则 |
| S2 · 意图 + 会话上下文 | 历史轮次/用户画像参与裁剪 | 弃选：裁剪规则无法确定性定义（「历史聊过什么」如何映射剔除集？）· 留 V1-D 情景记忆产出证据后复盘 |

### Q3 · `execution_type` 三值与既有危险度标注的映射

**裁定**：`execution_type` 与 `side_effect`/`risk_level` **正交不代理**（承 types.py「两维不可互代」纪律），映射为**默认期望 + 加载期一致性校验**而非派生：

| `execution_type` | 语义 | 与 `side_effect` 默认期望 | 加载期一致性规则 |
|---|---|---|---|
| `instant` | 瞬时完成 · 无持续效果 | none/read（典型）· write 瞬时单发亦可 | 无硬约束（观测 span） |
| `target` | 作用于目标对象 · 有可逆窗口 | write（典型） | `reversible=false` 时告警（target 通常可逆 · 观测级不拒） |
| `process` | 持续进程 · 需 stop 支持 | write/irreversible（典型） | **硬规则**：`requires_stop_support` 必须 true（缺→ManifestError） |

跨字段唯一硬矛盾：`side_effect=irreversible` + `reversible=true` → ManifestError（自相矛盾）。其余组合只观测不拒（契约不推测 · 承 R10 纪律）。

---

## 5. failure_paths（承 08 §2.4 · 全部正面裁定）

| # | 路径 | 裁定 |
|---|---|---|
| FP-1 | 意图风险档误判导致过度裁剪 | 安全默认方向正确（宁缺毋滥）；误判进剔除台账可复盘；observe 期收集 would_strip 报告后再进 enforce |
| FP-2 | 03 轨风险档演进冲突 | 以 03 现行 `IntentV1.risk_hint` 为准；03 若改口径 → 裁剪表对齐回 10-spec（本波锁三档词表） |
| FP-3 | 四字段缺失存量 manifest 批量默认 HITL 致可用性降 | **灰度三档**：off 起步 → observe（台账告警）→ enforce 前必须 builtin.v1.yaml 四字段全量补齐（本波 D4 含补齐义务 · 升级路径零误伤） |
| FP-4 | 裁剪耗时 | 纯代码无 IO · 目标 <10ms（承工程方案 P2 出口 · 单测注记级 smoke） |
| FP-5 | intent_fallback 裂缝（fallback 默认 low 虚假宽松） | D1 增 `intent_fallback` state channel + S1 规则空集兜底 · 断言化（fallback→空集） |
| FP-6 | 场景维与 V1-A requested_scope 叠加顺序歧义 | 语义=三重交集（基线 ∩ 场景维 ∩ requested_scope · 交换律等价 · 只收窄不放宽）；落点按数据可得性：Builder 内 基线→场景维（intent 图序已可得）· supervisor 内 delegation_scope = requested_scope ∩ 场景维后有效可见集（R1 审查 B-1 澄清 · 2026-09-23） |
| FP-7 | 派生 hitl_required 与显式声明冲突 | 声明优先：显式四字段合法 → 不派生；仅未声明且 enforce → 派生 True（断言化） |
| FP-8 | observe→enforce 灰度误伤主线 | 双开关独立灰度（场景维 / 四字段分离）；enforce 前观察期报告（承观测模式先例） |

---

## 6. 验收标准（可机验）

1. 两阶段裁剪矩阵断言通过（S1–S5 全规则 × risk_level 组合）
2. 安全默认生效：fallback/歧义 → 空集 + 台账可查；observe 不生效
3. 剔除项台账可查（id + reason 码 + 计数 · logger/span 双通道）
4. 四字段加载期强制：非法 → ManifestError · 矛盾声明拒 · process 无 stop 拒
5. 缺失默认 HITL 三档：off 无行为 · observe 台账 · enforce 派生 True（显式声明不派生）
6. builtin.v1.yaml 四字段全覆盖断言通过
7. off 模式零 diff（既有 1420 基线用例零改动全绿）
8. `pytest tests` 全绿 + `ruff check app tests` 净增 0
9. 图谱回写完成（capability/lg_rag 行备注 + HG-GRAPH-MODULES 00 代录）+ graph-compile 绿
10. PR 到 master 经 CI 绿后 merge

---

## 7. 思考轮回填（R0–R5）

- **R0（读人聊/目标）**：维护者令长程授权（含「完成后自行进行下一波」）；V1-A CLOSE（requested_scope 已备）；08 §2 种子 + 03 轨加读毕。
- **R1（范围/非范围）**：D1–D5 承种子展开；U2 实证消解（risk_hint 已存在 · 不新增字段）；HITL 三档执行侧/意图 schema 演进/会话上下文显式排除。
- **R2（方案对比）**：Q1/Q2/Q3 全部两案以上对比并作答；fallback 裂缝两案（fallback 视为 low 放行 vs fallback 空集）裁定为空集（安全默认）；风险档来源两案（intent 内嵌 vs 独立分类器）承种子 R2 裁定为内嵌（risk_hint 已内嵌 · 独立分类器弃——多一次 LLM 调用且 03 已立）。
- **R3（边界/失败路径）**：FP-1~FP-8 全裁定；最锋利边界 = fallback 裂缝（FP-5）与存量误伤（FP-3 灰度+存量补齐双保险）。
- **R4（验收/可测性）**：验收 10 条全可机验；裁剪规则表五行五行皆有否定性断言（安全默认两条是变异检验式：fallback 必须空集）。
- **R5（签收就绪）**：与 03 轨边界确认（只消费不演进）；图谱义务定（两行备注 · 无新一级模块）；可交 00 代录 HG-SPEC-SIGNOFF 后拆 task。

### 思考轮控制

| 轮 | 状态 | 说明 |
|---|---|---|
| R0 | done | 维护者令 + 07/08 + 03 轨 + V1-A SPEC + 代码实证已读 |
| R1 | done | 范围 D1–D5 / 非范围锁死 |
| R2 | done | Q1/Q2/Q3 ≥2 案对比 + 裁定 |
| R3 | done | FP-1~FP-8 裁定 |
| R4 | done | 验收 10 条 + test_strategy=required |
| R5 | done | 签收就绪 → 00 代录 HG-SPEC-SIGNOFF |
| early_stop | no | — |

---

## 8. 关联

- 规划/种子：[`../agent-infra/07_host_v1_landing_plan_v0.md`](../agent-infra/07_host_v1_landing_plan_v0.md) · [`../agent-infra/08_host_v1_wave_spec_outlines_v0.md`](../agent-infra/08_host_v1_wave_spec_outlines_v0.md) §2（双 signed）
- 03 策略轨：[`03_strategy_and_intent_plan_v0.md`](./03_strategy_and_intent_plan_v0.md)（risk_hint 真值 · S1–S4 CLOSE）
- 前波：[`../host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md`](../host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md)（signed · V1-A · requested_scope 真值）
- 启动 invoke：[`../../harness/invokes/by-task/host-v1-landing/invoke_20260923_00_host-v1-landing.md`](../../harness/invokes/by-task/host-v1-landing/invoke_20260923_00_host-v1-landing.md)
- 代码锚点：`app/ops/lg_rag/schemas/intent.py:25-28`（risk_hint）· `app/ops/strategy/intent.py:22-24`（fallback 裂缝）· `app/ops/strategy/builder.py`（两阶段落点）· `app/ops/capability/baseline.py`（stage 1 基线）· `app/ops/capability/types.py:72-118`（CapabilitySpec）· `app/ops/capability/manifest.py`（加载期校验面）· `app/ops/capability/manifests/builtin.v1.yaml`（存量补齐对象）
- 图谱：`docs/_tech_graph/l1/01_modules.md`（capability/lg_rag 行）

## 修订记录

| 日期 | 版本 | 内容 |
|---|---|---|
| 2026-09-23 | v0 | 10-spec 初稿：以 08 §2 种子展开 D1–D5；U2 实证消解（risk_hint 已存在直接消费）；开放裁定 Q1（3 档对齐 03）/Q2（仅意图+健康度 · 不含会话上下文）/Q3（execution_type 正交映射 + 一致性硬规则）全部作答；fallback 裂缝（S1 空集）正面作答；FP-1~FP-8 裁定；R0–R5 回填 |
| 2026-09-23 | v0 | **00 代录 HG-SPEC-SIGNOFF=approved**（维护者双令原话留痕见状态行与人工闸表）；下一棒：00 起草 task（`docs/tasks/active/task_host_v1_visibility_scenario_policy.md`）→ 20-task-audit |
| 2026-09-23 | v0 | **R1 审查 B-1 澄清**（20-task-audit FAIL 阻塞项 · 00 代录同令）：管线落点勘正——requested_scope 交集真值在 supervisor 节点（`multi/nodes.py:933-948`）非 Builder；三重交集交换律等价语义零改 · 规则表 S1–S5/四字段/非范围全不动；仅 D2 管线段落与 FP-6 措辞勘正 |
