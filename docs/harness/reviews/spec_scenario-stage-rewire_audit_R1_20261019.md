# 20-spec-audit R1 书面审：SPEC-scenario-stage-rewire v0

> **hat_id**：20-spec-audit（R1 · 轻量路径：10-spec 思考轮 R0–R5 已内联 SPEC §8，单轮 R1）
> **审查对象**：`docs/spec/scenario-stage-rewire/SPEC-scenario-stage-rewire_v0.md`（draft · 166 行 · HG-SPEC-SIGNOFF=pending）
> **审查日期**：2026-10-19 · **审查人**：Harness 20-spec-audit（书面审 · 不改 SPEC 实质 · **不代签** HG-SPEC-SIGNOFF）
> **结论**：**conditional_pass** · 「恒短路」前提与「摘除后逐值等价」断言全部代码坐实 · 分支 a/b 裁定明确留签收 · **阻塞项 B1（env 键名事实错误 · 一行可修）须退回 10-spec 修订** · 非阻塞 N1–N4 移交 00 起草 task 时吸收 · B1 修订后**建议维护者可签 HG-SPEC-SIGNOFF（签收时一并裁定分支 a/b）**
> **实证复核范围**：SPEC 全文 166 行逐行 · 源码实读 `app/ops/strategy/builder.py:90-179`（_apply_scenario_stage + strategy_builder_node）· `app/ops/strategy/scenario.py` 全文 128 行（S1–S5 + scenario_mode + ENV_SCENARIO_MODE）· `app/ops/lg_rag/multi/graph.py:70-105`（拓扑）· `app/ops/chat/nodes.py:45-69`（同名 intent_node）· 全仓 grep：`"intent"/intent_fallback` 写入方、`scenario` 引用点、`OPS_STRATEGY_SCENARIO` / `LG_RAG_VISIBILITY_SCENARIO_MODE` 两 env 键、tests 引用 · `app/ops/lg_rag/graph.py`（basic/router 图）intent 挂载核查 · git log 核 PR #282 · 上游闭合件（`docs/tasks/done/task_supervisor_first_fail_closed.md:129` TC6 · `spec_supervisor-first-fail-closed_audit_R1_20261019.md`）

## 一、委托方点名重点核对

### 1. 「恒短路」事实是否已在代码坐实（逐值等价断言的前提）· **PASS**

| 核对点 | SPEC 位置 | 实证 |
|---|---|---|
| 裁剪键只取两键 | 锚点行「键取 `state.intent+intent_fallback`」 | builder.py:121-122 `scenario_trim(visible, state.get("intent"), bool(state.get("intent_fallback")))` 逐字在册 |
| 无 intent 全短路 | 锚点行「恒短路」· §1「名存实亡」 | scenario.py:71-75：supervisor-first（D3）注释 + `if intent is None or (isinstance(intent, dict) and not intent): return specs, []`——**S1–S5 全短路，含 S4 缺省 risk_hint→high 收紧路径**（注释逐字钉死）。注意短路在 scenario_trim 内部，**与 env 档位无关**：off 档 builder.py:119-120 提前 return；observe/enforce 档进 scenario_trim 仍逐值短路（audit 空列表 no-op，scenario.py:104-105） |
| 唯一写入方已失 | 上游行「`state.intent` 失去唯一写入方」 | 全仓 grep：lg_rag 运行时路径中唯一写 `intent`/`intent_fallback` 的是 `app/ops/strategy/intent.py:94` `return {**bump, "intent": intent, "intent_fallback": fallback}`，而该节点 supervisor-first 后**两图均无挂载**（multi/graph.py:87-95 add_node 清单无 intent_node；`app/ops/lg_rag/graph.py` 全文 grep intent 零命中）。`chat/nodes.py:72` 写 `intent` 但属 ChatState（chat 图 · 410 legacy · SPEC §3 非范围已排除）。sse_stream.py:64/95 为事件名映射非 state 写入 |
| 上游闭合件互证 | 锚点行引 supervisor-first-fail-closed D3 | 已签 R1 审查文 §一.2 逐规则推演 S1–S4；`docs/tasks/done/task_supervisor_first_fail_closed.md:129` TC6 已把「无 intent 轮（含 enforce 档）visible 进=出逐 id 对拍 · allowlist ≡ 基线∩candidates」落成机验断言，对应测试在 `tests/test_strategy_scenario.py:296-300`、:333 |

**裁定**：「恒短路」不是 SPEC 自述，是代码 + 已签上游 + 在测断言三重坐实。分支 (a) 摘除后 allowlist=基线可见∩candidates 与现行行为**逐值等价**的断言成立（零风险定性有据）。

### 2. 分支 a/b 裁定是否明确留给签收 · **PASS**

三处互锁：§1 一句话目标「本 SPEC **推荐 (a) 摘除**…(b) 仅在维护者明确…时选用」· §7 风险表「维护者签 HG-SPEC-SIGNOFF 时一并裁定分支」· R5「**签收时必须一并裁定分支 a/b**」。推荐与备选的理由（§4 A/B/C 对比 · C 弃因机制性）充分，未越权替人签做决定。

### 3. 代码锚点（file:line）抽查 · **一致 8 条 · 漂移 0 条 · 错误 1 条（B1）**

| # | SPEC 锚点 | 实证 | 裁定 |
|---|---|---|---|
| 1 | `builder.py:111-128` `_apply_scenario_stage`：off 短路/observe would_strip/enforce 剔除 | 逐行在册（off :119-120 · observe :124-126 · enforce :127-128） | ✅ |
| 2 | `builder.py:161` 注释「D1 图内无 intent_node」· `agent_type` 固定 None | :161 注释逐字 · :165 `agent_type=None` | ✅ |
| 3 | `multi/graph.py:82` 注释「IntentV1 模块保留，本图不再挂载」 | :82 逐字在册 | ✅ |
| 4 | `multi/graph.py:96-104` 拓扑无 intent_node | START→strategy_builder→supervisor→subtask_join→…→critic_node，全边清单在册 | ✅ |
| 5 | `chat/nodes.py:56` chat 图另有同名节点 | :56 `async def intent_node(state: ChatState)` | ✅ |
| 6 | 「lg_rag 三图均无挂载」 | multi/graph.py（supervisor）与 lg_rag/graph.py（basic/router）均无 intent 挂载 | ✅ |
| 7 | 上游 PR #282 | git log：35b8f95 `feat(supervisor-first-fail-closed)…(#282)` | ✅ |
| 8 | `scenario.py` 模块保留 · 三档 off/observe/enforce 语义 | scenario.py:49-52 默认 off 非法回退；:64-68 规则表 S1–S5 | ✅ |
| 9 | D1 env 行「`OPS_STRATEGY_SCENARIO_*` 相关 env 键」 | **全仓 grep 零命中，该键族不存在**。真值=`LG_RAG_VISIBILITY_SCENARIO_MODE`（scenario.py:38 `ENV_SCENARIO_MODE` · `docs/guides/GUIDE_env_inventory_v1.md:35` 在册 · 上游 SPEC §2） | ❌ → B1 |

## 二、结构核对表（范围 / 非范围 / 验收 / failure_paths / 思考轮）

| 项 | 裁定 | 摘要 |
|---|---|---|
| 范围 D1/D2 内聚 | ✅（附 B1/N1） | 摘除/重接二选一互斥清晰；D1「删/留/env/图谱」四行除 env 键名错误外均可执行；D2 前提（维护者点名+新信号源）与「禁止映射 S1 空集」铁律承 supervisor-first D3，防误用锁死 |
| 非范围与范围互斥 | ✅ | §3 五条与 D1/D2 无重叠；「❌ 删 scenario.py」与 D1「留」行互锁；「❌ 恢复 intent_node」与上游已定后置互锁；「❌ 顺手清理」防 scope creep |
| 验收可机断 | ✅ | 五条全部可假 state/单测机断（逐值回归、import 存活、router/basic 零 diff、pytest 绿），无人工判断依赖；分支 b 验收条件化标注正确 |
| failure_paths 充分 | ✅（附 N2） | FP-1~FP-5 覆盖：逐值回归/env 失效/对照轨/import 存活/分支 b 安全默认。FP-1 与 TC6 既有断言同构，回归底座现成 |
| R0–R5 思考轮闭合 | ✅ | §8 表 + 各轮小节齐全；`actual_last_round=R5`；R5 reason=「人签未发生」residual=「HG-SPEC-SIGNOFF=pending · 分支裁定在签收时」——诚实标记 draft；R2 方案对比弃案理由机制性 |
| 人工闸纪律 | ✅ | HG-SPEC-SIGNOFF=pending 在表；本帽不代签；SPEC §8 R5 声明「本文件不授权改 app/」 |
| graph_change_layer 判定 | ✅ | `none` 预期合理：不增路由/表/event_type；图谱义务仅 01_modules.md 备注更新（措辞精度见 N1） |

## 三、阻塞项（退回 10-spec 修订 · 本帽不改 SPEC 实质）

| ID | 位置 | 内容 | 修法 |
|---|---|---|---|
| **B1** | §2 D1 env 行（SPEC:62） | env 键名事实错误：`OPS_STRATEGY_SCENARIO_*` 全仓不存在。真值 `LG_RAG_VISIBILITY_SCENARIO_MODE`（scenario.py:38 · GUIDE_env_inventory 在册）。范围表是指给 30 的执行面，写错键名会让 30 grep 错目标、漏删真读取点（FP-2「env 读取点已删」的真读取点即 scenario.py:51 `os.environ.get(ENV_SCENARIO_MODE)`） | 10-spec 一行修订为 `LG_RAG_VISIBILITY_SCENARIO_MODE`（可顺带点名 `ENV_SCENARIO_MODE` 常量与 scenario.py:51 读取处）。事实错误虽小，**不应带病人签成 signed truth** |

## 四、非阻塞 nits（移交 00 起草 task 吸收；不阻塞 B1 修订后的人签）

| ID | 位置 | 内容 |
|---|---|---|
| N1 | §2 D1 图谱行 | 「`01_modules.md` strategy 行备注」措辞不精确：图谱无独立 strategy 一级模块行，strategy 是 `lg_rag` 行内「路径覆盖补记」段（01_modules.md:35）。建议 task 写「lg_rag 行 strategy 段备注追加『scenario 裁剪已摘除（恒短路清理 · 日期）』」 |
| N2 | §5/§6 vs 既有测试 | `tests/test_strategy_scenario.py:35` 直接 `from app.ops.strategy.builder import _apply_scenario_stage`，且 :196-:268（observe/enforce 台账断言）、:342（delegation_scope ∩ scenario_trim）等用例绑定被删函数与 env 三档行为。分支 (a) 摘除后该文件必红，SPEC 范围/验收未交代处置口径。建议 task 验收条显式写：删 `_apply_scenario_stage`/env 三档台账用例、保留 `scenario_trim` 纯函数 S1–S5 用例与 TC6 短路断言（改造为对 Builder 直出 allowlist 的逐值回归） |
| N3 | 观察项（无责） | `app/ops/lg_rag/sse_stream.py:64` 仍存 `"intent_node": "intent"` 事件名映射（supervisor-first 后死映射）。非本 SPEC 范围（不增删 event_type 约束下保留正确）；可在 task 的 grep 引用清单（§7 风险表已要求落 invoke）中登记为「已知残留 · 不动」 |
| N4 | invoke_slug | `docs/harness/invokes/by-task/scenario-stage-rewire/` 未见（SPEC 阶段思考轮已内联 §8，轻量路径可接受）。按仓纪律 pre-30 invoke 缺失拒改码——移交 00 起草 task 时同步补 invoke 文件 |

## 五、HG-SPEC-SIGNOFF 建议

**B1 修订（10-spec 一行改 env 键名）后，建议维护者可签 HG-SPEC-SIGNOFF，签收时按 SPEC 既定约定一并裁定分支 a/b（本帽复核：推荐 (a) 的「零风险逐值等价」论证成立，(b) 仅维护者点名近期恢复场景裁剪时选用）**。本帽**不代签**；人签前维持：不出 task / 不改码 / 30 拒开工。

## 六、下一棒

1. **退回 10-spec**：修订 B1（v0.1 · 仅 env 键名一处）；
2. 维护者人签（含分支 a/b 裁定）→ **00 起草 task**（slug=`scenario-stage-rewire`，分支 `task/scenario-stage-rewire`）：吸收 N1–N4 进 task 验收/failure_paths；按 §7 风险表把 scenario 全仓引用点清单落 invoke；补 invoke 文件；
3. task 草稿 → 20-task-audit → HG-AUDIT-R1 人签 → 30。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-10-19 | R1：恒短路前提代码坐实（scenario.py:71-75 + 唯一写入方已失 + TC6 在测）· 逐值等价断言成立 · 分支 a/b 裁定留签收确认 · 锚点 8 一致 / 0 漂移 / 1 错误；conditional_pass · 阻塞 B1（env 键名 `OPS_STRATEGY_SCENARIO_*` 不存在，真值 `LG_RAG_VISIBILITY_SCENARIO_MODE`）退回 10-spec · N1–N4 移交 task · 不代签 HG-SPEC-SIGNOFF |

---

## R2 复核（2026-10-19）：B1 闭合情况 + 最终结论

> **触发**：10-spec 完成 B1 修订（v0.1）后，父 Agent 请窄幅复核。复核范围仅限 B1 闭合，不重开全量审查。

### B1 闭合实测（三项全部 PASS）

| 核查 | 实证 | 裁定 |
|---|---|---|
| SPEC:62 env 行正名 | :62 现为「`LG_RAG_VISIBILITY_SCENARIO_MODE` env 键标注 deprecated（读取处删除，文档登记）」 | ✅ |
| `OPS_STRATEGY_SCENARIO` 零残留 | 全仓 grep 仅命中本审查文自身历史记录（:7/:38/:56/:83 四行为 R1 事实留痕，非残留）；SPEC / app/ / 其余 docs 零命中 | ✅ |
| 真值未漂移 | `app/ops/strategy/scenario.py:38` 仍 `ENV_SCENARIO_MODE = "LG_RAG_VISIBILITY_SCENARIO_MODE"`，与正名后键名一致 | ✅ |

附记：SPEC 全文 167 行（v0 → v0.1 净增 1 行），§9 追加 v0.1 修订记录（:167 逐字点名 B1 与本审查文），D1 删/留/图谱三行与 §1–§8 其余内容对照 R1 复核时状态零改动——修订面与 R1 要求精确一致，无夹带。N1（图谱行「strategy 行」措辞）维持非阻塞、移交 task 吸收的处置不变。

### 最终结论

**pass** · 阻塞项清零（B1 闭合）· 非阻塞 N1–N4 按 R1 既定路径移交 00 起草 task 吸收 · **建议维护者可签 HG-SPEC-SIGNOFF**（本帽**不代签**；签收时按 SPEC §1/§7/R5 既定约定一并裁定分支 a/b——本帽复核意见：推荐 (a) 摘除的「恒短路逐值等价 · 零风险」论证经 R1 代码坐实，成立）。

### 下一棒（维持 R1 §六，B1 环节已闭环）

维护者人签（含分支 a/b 裁定）→ 00 起草 task（slug=`scenario-stage-rewire`）：吸收 N1–N4 进验收/failure_paths · scenario 全仓引用点清单落 invoke · 补 `docs/harness/invokes/by-task/scenario-stage-rewire/` → 20-task-audit → HG-AUDIT-R1 人签 → 30。

| 日期 | 摘要 |
|------|------|
| 2026-10-19 | R2 窄幅复核：B1 三项实测全部闭合（SPEC:62 正名 · 错误键零残留 · scenario.py:38 真值未漂移）· v0.1 修订面无夹带 · 最终结论 **pass** · 建议可签 HG-SPEC-SIGNOFF（不代签 · 分支 a/b 裁定留签收） |
