# SPEC：scenario stage 裁剪死代码处置（v0）

> **状态**：`signed`（HG-SPEC-SIGNOFF=**approved** · 2026-10-19 维护者会话签收 · **裁定分支 (a) 摘除** · 20-spec-audit R2 pass）
> **track**：`cleanup`（死代码处置：摘除或重接，二选一由本 SPEC 裁定；不新增路由 / 表 / event_type）
> **上游**：2026-10-19 supervisor 全流程审核疑点 #3：supervisor-first（PR #282）摘除 `intent_node` 后，scenario stage 裁剪的触发键 `state.intent` 失去唯一写入方，`_apply_scenario_stage` 恒不触发——**名存实亡**
> **建议序**：**3/5**
> **现状锚点**：
> - `app/ops/strategy/builder.py:111-128` `_apply_scenario_stage`：键取 `state.intent+intent_fallback`，off 短路 / observe 记 would_strip / enforce 剔除；
> - `builder.py:161` 注释自认「D1 图内无 intent_node」，`agent_type` 固定 `None`；
> - supervisor 图不再挂 intent_node（`app/ops/lg_rag/multi/graph.py:82` 注释「IntentV1 模块保留，本图不再挂载」、拓扑 :96-104）；
> - SPEC supervisor-first-fail-closed D3 已定「无本轮 intent 时 scenario **短路、不裁**」——即现状语义是「恒短路」，代码留着 observe/enforce 分支是死路径；
> - `app/ops/strategy/intent.py` 模块保留但 lg_rag 三图均无挂载（chat 图另有同名节点 `app/ops/chat/nodes.py:56`，chat 已 410 收口 legacy）。
> **下游**：20-spec-audit / HG-SPEC-SIGNOFF → 00 出 task → 20-task-audit → HG-AUDIT-R1 → 30
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `scenario-stage-rewire` |
| **invoke_slug** | `scenario-stage-rewire` |
| **test_strategy** | `required` |
| **test_strategy_note** | 摘除分支：allowlist=基线可见∩candidates 逐值回归（scenario env 三档均不再影响结果）· 重接分支：写入方单测 + observe/enforce 行为恢复断言 · 两分支都要求 `mode=router/basic` 零 diff |
| **默认分支** | `task/scenario-stage-rewire` |
| **graph_change_layer** | `none` 预期（不增路由/表/event_type；`01_modules.md` strategy 行备注更新） |
| **freeze_id** | 无契约变更 |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | approved（2026-10-19 维护者） | 维护者会话签收并**裁定分支 (a) 摘除**；审查文 `spec_scenario-stage-rewire_audit_R1_20261019`（R2 pass · N1–N4 移交 task 吸收） |

---

## 1. 背景与目标

scenario stage 裁剪（S1–S5 按意图场景收窄能力菜单）依赖 `state.intent`，而 supervisor-first 后 lg_rag 图内不再有 intent 写入方。`builder.py:161` 注释已自认这一事实。留着死分支的代价：

1. **观测假象**：env 三档（off/observe/enforce）看起来在工作，实际恒短路——与 memory 注入疑点同属「静默无效」类；
2. **认知负担**：读者要花力气推断「到底会不会触发」；
3. **后续误用**：未来有人按「scenario 生效」假设写代码。

### 一句话目标

消除「scenario stage 名存实亡」状态：二选一——**(a) 摘除**（删 `_apply_scenario_stage` 调用与死分支，`scenario.py` 模块归档保留供后续波次）或 **(b) 重接**（给 `state.intent` 找一个新写入方恢复裁剪语义）；本 SPEC **推荐 (a) 摘除**，理由见 §4；(b) 仅在维护者明确「近期要恢复场景裁剪」时选用。

---

## 2. 范围

单 task。

### D1 · 分支（a）：摘除（推荐）

| 项 | 约定 |
|---|---|
| 删 | `builder.py` 内 `_apply_scenario_stage` 调用与 scenario 相关分支；allowlist 语义固定为 `candidates ∩ visible_ids`（基线可见 ∩ candidates，与现行恒短路行为**逐值等价**） |
| 留 | `app/ops/strategy/scenario.py` 模块本体不删（后续「意图恢复」波次可能复用），文件头加 dormant 注释 |
| env | `LG_RAG_VISIBILITY_SCENARIO_MODE` env 键标注 deprecated（读取处删除，文档登记） |
| 图谱 | `01_modules.md` strategy 行备注「scenario 裁剪已摘除（恒短路清理 · 2026-10-xx）」 |

### D2 · 分支（b）：重接（备选，需维护者点名）

| 项 | 约定 |
|---|---|
| 前提 | 维护者明确近期恢复场景裁剪，且有新信号源（如 planner plan 类型分布 / 显式 scenario 参数） |
| 禁止 | **禁止**把「没跑意图」映射成 S1 空集（沿用 supervisor-first-fail-closed D3 铁律） |
| 写入方 | 新写入方必须是确定性信号或独立 LLM 节点（设计在 task 阶段展开，本 SPEC 只锁前提） |

---

## 3. 非范围

- ❌ 删 `scenario.py` 模块文件 / 删 `IntentV1` schema（保留供后续波次）
- ❌ 恢复 intent_node 进 supervisor 图（supervisor-first-fail-closed 已定后置，回退需新 SPEC）
- ❌ 改 `get_candidate_capability_ids` / 基线过滤器语义
- ❌ chat 图（410 legacy）的任何改动
- ❌ 同 task 内顺手做其他 strategy 目录清理

---

## 4. 方案对比（R2 落盘）

| 方案 | 内容 | 裁定 |
|---|---|---|
| A 摘除 | 删死分支，allowlist=基线∩candidates | **推荐**。与现行行为逐值等价（零风险），消除静默无效 |
| B 重接 | 给 intent 找新写入方 | **备选**。无现成信号源，为死功能造新 LLM 节点是本末倒置；除非维护者点名 |
| C 维持现状 | 文档写明「恒短路」 | **弃**。死代码+文档补丁是最差组合，认知负担不减 |

---

## 5. failure_paths

| ID | 路径 | 期望 |
|---|---|---|
| FP-1 | 摘除后 supervisor allowlist | 与摘除前逐值相等（恒短路语义不变的回归断言） |
| FP-2 | scenario env 三档任意值 | 摘除后不再影响结果；env 读取点已删 |
| FP-3 | `mode=router/basic` | 与改前逐行为一致 |
| FP-4 | 后续有人 import scenario.py | 模块仍在可 import（dormant 注释说明状态） |
| FP-5 | 分支（b）被选用时 | 新写入方缺失信号 → 短路不裁（禁止映射 S1 空集） |

---

## 6. 验收

- [ ] （分支 a）`_apply_scenario_stage` 调用点删除；allowlist 回归测试逐值相等
- [ ] （分支 a）`scenario.py` dormant 注释；图谱 strategy 行备注更新
- [ ] （分支 b 仅当维护者点名）新写入方单测 + observe/enforce 恢复断言 + FP-5 断言
- [ ] `mode=router/basic` 既有测试零行为差
- [ ] pytest 绿；不增 event_type/路由/表

---

## 7. 风险

| 风险 | 缓解 |
|---|---|
| 摘除后某隐藏路径仍依赖 scenario 裁剪 | FP-1 逐值回归 + grep 全仓引用点清单落 invoke |
| 未来恢复场景裁剪时要重写 | `scenario.py` 保留；git 历史可查 |
| 分支选择争议 | 本 SPEC 推荐 (a)；维护者签 HG-SPEC-SIGNOFF 时一并裁定分支 → **2026-10-19 已裁定 (a) 摘除** |

回滚：分支 (a) 回滚=git revert（行为本来就逐值等价）。

---

## 8. 思考轮控制

| 轮 | 结论 | early_stop | reason | residual_risks |
|---|---|---|---|---|
| R0 | 疑点 #3：scenario 恒短路，名存实亡 | no | | |
| R1 | 范围=摘除或重接二选一；删模块/恢复意图/chat 非范围 | no | | |
| R2 | 推荐 A 摘除；B 备选需点名；弃 C 维持 | no | | 隐藏依赖靠回归+引用清单挡 |
| R3 | 逐值等价是摘除分支的安全底线 | no | | |
| R4 | 回归断言可全测；不打真 LLM | no | | |
| R5 | draft 可交 20-spec-audit | no | 人签未发生 | HG-SPEC-SIGNOFF=pending；分支裁定在签收时 |

`actual_last_round`：R5

### R0
证据：`builder.py:111-128` 键取 state.intent；`multi/graph.py:82` intent_node 不挂载；`builder.py:161` 自认。

### R1
成功=scenario 状态名实一致（要么真工作，要么不在）；失败=继续静默死分支。

### R2
见 §4。摘除与现行行为逐值等价，是唯一零风险选项。

### R3
不动 Policy/闸链/可见性基线。

### R4
`test_strategy=required`。

### R5
本文件不授权改 `app/`。下一棒：20-spec-audit 或维护者人签（**签收时必须一并裁定分支 a/b**）→ 00 起草 task。

---

## 9. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-10-19 | v0 draft：supervisor 审核疑点 #3 落盘（scenario 恒短路 · 推荐摘除 · 分支裁定留签收） |
| 2026-10-19 | v0.1：20-spec-audit R1 阻塞项 B1 修订（env 键名正名为 `LG_RAG_VISIBILITY_SCENARIO_MODE` · 审查文 `spec_scenario-stage-rewire_audit_R1_20261019`） |
| 2026-10-19 | HG-SPEC-SIGNOFF=approved（维护者会话签收 · R2 pass）· **分支裁定：(a) 摘除**；交 00 起草 task |
