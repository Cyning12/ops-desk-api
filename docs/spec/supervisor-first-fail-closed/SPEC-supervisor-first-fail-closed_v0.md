# SPEC：主编排优先 · 规划失败即失败 · 意图后置（v0）

> **状态**：`signed`（**HG-SPEC-SIGNOFF=approved** · 2026-10-19 维护者本窗指示 · 00 代签 → 下一棒 00 起草 task）
> **track**：`feature`（supervisor 图入口顺序 + 规划失败语义；**不**新增路由 / 表 / 一级模块）
> **上游（本窗讨论锁死）**：SSE 主线默认 `mode=supervisor`；规划器不可用时禁止静默单 rag 冒充规划成功；细意图不再作为图内第一个 LLM 节点；不 failover 到 `mode=router` 粗路由
> **现状锚点**：`app/ops/lg_rag/multi/graph.py`（`START → intent_node → strategy_builder → supervisor`）· `app/ops/strategy/intent.py`（SO 失败写 `intent_fallback`）· `app/ops/lg_rag/multi/nodes.py` `supervisor_node`（LLM/解析失败 → 首次规划 fallback 单 rag）· `app/ops/strategy/builder.py` / `scenario.py`（可见集依赖 `state.intent`）
> **下游**：人签或 20-spec-audit → 00 出 task → 20-task-audit → HG-AUDIT-R1 → 30
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `supervisor-first-fail-closed` |
| **invoke_slug** | `supervisor-first-fail-closed` |
| **test_strategy** | `required` |
| **test_strategy_note** | supervisor 图边断言（无前置 intent 节点）· 首次规划耗尽 → SSE `error` 且 `stage=supervisor_plan` · 默认开关下禁止出现 `supervisor_fallback` 单 rag · 重规划沿用后缀与首次失败分叉单测 · 缺 intent 时 scenario **不得**按 `intent_fallback` 清空 allowlist · `mode=router`/`basic` 零 diff |
| **默认分支** | `task/supervisor-first-fail-closed` |
| **graph_change_layer** | `none` 预期（复用既有 `error` 事件类型，只新增 stage 词 `supervisor_plan`；不增路由/表/一级模块）。若 30 新增 SSE `event_type` → 回本 SPEC 判 G-L* 并升 freeze |
| **freeze_id** | 对照 `lg-rag-sse-v1`：不新增 `event_type`。`error.stage=supervisor_plan` 若被 freeze 词表锁死，则本波先改 SPEC 再动码 |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | **approved** | 2026-10-19 维护者本窗指示「其他条目都按照建议来执行」（R1 审查 conditional_pass · 三条 00 定夺落 invoke_20261019_00_start.md）· 00 代签 |

---

## 1. 背景与目标

默认请求已走 supervisor 图，但图内第一步仍是细意图 LLM（`intent_node`），且 `supervisor_node` 在规划 LLM 失败时**静默改成单 rag**（`supervisor_fallback`）。这和「主编排是唯一规划脑、失败必须可见」不一致：用户看到的像一次正常作答，观测上却已换了规划器。

### 一句话目标

supervisor 图改为 **无 LLM 的 Builder → supervisor**；**首次规划**在工厂重试/跨档耗尽后发 `error`**（**`stage=supervisor_plan`**）并停图**；细意图 **退出主路径阻塞位**（不删模块概念、不并进 supervisor 同一次调用、不切到 router 粗路由）。

---

## 2. 范围

单 task。三块一起做，否则「意图拿掉但失败仍静默单 rag」或「失败改 error 但意图仍挡在前面」都不闭合。

### D1 · 图入口：Builder 在前，第一个 LLM 是 supervisor

| 项 | 约定 |
|---|---|
| 边 | `START → strategy_builder → supervisor → …`（其后 join / observe / aggregator / critic **不改拓扑**） |
| 去掉 | supervisor 图 **不再**挂前置 `intent_node` |
| 保留 | `mode=router` 的粗路由图、`mode=basic` **零改动**（对照轨，不是本失败的 failover） |
| HTTP | `POST /api/ops/lg-rag/stream` 默认 `mode=supervisor` 不变；不换路径 |

### D2 · 首次规划失败 = 失败（默认）

| 项 | 约定 |
|---|---|
| 触发 | 首次规划（无 locked 前缀）：LLM 异常、工厂重试/跨档耗尽、输出无法解析、非法 tool id 导致整 plan 作废 |
| 默认行为 | **不**写入单 rag 子任务；图收口为失败；SSE 一帧 `error`，`stage=supervisor_plan`，再终态（沿用现有 done/error 收流纪律，不发明新 `event_type`） |
| 可观测 | span/log 含 `supervisor_plan_failed=true`；**禁止**同时标 `supervisor_fallback=true` 且继续 aggregator 出「完整答案」 |
| 重规划例外 | 已有 locked 前缀时，规划失败 **沿用未解决后缀**（现网防「失败被抹掉」）。这不是新规划成功，也不是首次失败的单 rag 兜底 |
| 灾备开关 | `LG_RAG_SUPERVISOR_PLAN_ON_FAIL`：`error`（**默认**）\| `single_rag`。`single_rag` 仅显式打开；必须 `degraded=true` 进 span/终帧元数据，且 **不得扩权**（allowlist 只许更窄）。非法值回退 `error` |
| 明确不做 | 不切 `mode=router`；不跑 `rag\|direct\|refuse` 粗分类当 failover |

### D3 · 意图后置（主路径不阻塞）

| 项 | 约定 |
|---|---|
| 语义 | 大纲 M15「意图」名称保留；**本波不实现**工人侧完整 `IntentV1`，也不把意图字段并进 supervisor 同一次 LLM |
| 状态 | supervisor 主路径 **不写** `intent` / 不把缺省当成 `intent_fallback=true` |
| Builder | 不再因 `needs_tool is False`（来自前置意图）清空 allowlist。allowlist = 基线可见 ∩ candidates（scenario 见下） |
| scenario | 无本轮 intent 时 **短路、不裁**（等价本轮不做 S1–S5）。**禁止**把「没跑意图」映射成 S1 空集 |
| 代码去向 | `intent_node` 可留在包内供对照/后续波，但 supervisor 图默认编译路径不得调用 |

---

## 3. 非范围

- ❌ 把意图物理合并进 `supervisor_node` 同一次 completion
- ❌ 工人侧局部意图 / 下沉 `IntentV1`（另 SPEC）
- ❌ 删 `IntentV1` schema、删 `mode=router` 粗路由、改 router 的 `#数字` 快路径
- ❌ 用粗意图图承接 supervisor 失败
- ❌ 改六道门、Policy、委派令牌、HITL 挂起语义
- ❌ 为 high 风险能力新开「进菜单」豁免（`deny_high_risk` 维持）
- ❌ 改 SSE 路径、新增 `event_type`、改鉴权
- ❌ 重规划沿用后缀改成也硬失败（本波保留现网该分支）

---

## 4. 方案对比（R2 落盘）

| 方案 | 内容 | 裁定 |
|---|---|---|
| A 现网 | intent → builder → supervisor；规划失败静默单 rag | **弃**。假成功，和主编排契约冲突 |
| B 失败切 router 粗意图 | supervisor 挂了走 `rag\|direct\|refuse` | **弃**。换闸链；粗路由自身也吃 LLM |
| C 本 SPEC | Builder（无前置意图）→ supervisor；首次规划耗尽默认 `error`；可选 `single_rag` 显式降级；意图退出阻塞位 | **采纳** |
| D 意图并进 supervisor 一次调用 | 省一次 LLM | **本波弃**。失败语义与分类信号缠在一起；可作后续优化 SPEC |

---

## 5. failure_paths

| ID | 路径 | 期望 |
|---|---|---|
| FP-1 | 首次 `supervisor` LLM 抛错 / 链耗尽 | `error.stage=supervisor_plan`；无单 rag plan；无 aggregator 终答冒充成功 |
| FP-2 | 首次输出非法 JSON 或 tool id 全非法 | 同 FP-1（默认 `error`） |
| FP-3 | env=`single_rag` | 允许单 rag；终态/span `degraded=true`；allowlist 不得比失败前更宽 |
| FP-4 | env 非法 / 未设 | 行为同 `error` |
| FP-5 | 已有 locked 前缀的重规划失败 | **沿用未解决后缀**；不发 `supervisor_plan` 错误终态；不收缩成只剩前缀 |
| FP-6 | 主路径无 intent | scenario 不把目录裁空；`intent_fallback` 不为 true |
| FP-7 | `mode=router` 或 `basic` | 与改前逐行为一致（不套用 D2） |
| FP-8 | 模型在 plan/ctx 顶层写 `allow_write` 等 | 仍不生效（Policy Host-only **零改动**，回归断言） |

---

## 6. 验收

- [ ] supervisor 图编译边为 `START → strategy_builder → supervisor`，默认路径无 `intent_node`
- [ ] 默认 env：模拟 supervisor 规划失败 → SSE `error` 且 `stage=supervisor_plan`；state 无 fallback 单 rag；不进入 aggregator 成功终答
- [ ] `LG_RAG_SUPERVISOR_PLAN_ON_FAIL=single_rag`：单 rag + `degraded=true`
- [ ] 重规划 + locked 前缀：失败沿用后缀（现有用例保持绿）
- [ ] 无 intent 的一轮：allowlist 与「只跑基线 ∩ candidates」一致，不被 S1 清空
- [ ] `mode=router` / `basic` 既有测试无行为差
- [ ] 不新增 SSE `event_type`；`pytest` 覆盖上述路径为绿

---

## 7. 风险

| 风险 | 缓解 |
|---|---|
| 模型抖动导致用户可见失败变多 | 默认诚实失败；灾备仅显式 `single_rag`；工厂重试/跨档仍先于本闸 |
| 去掉前置意图后，原 `needs_tool=false` 不再清空工具菜单 | 接受：菜单上界改由基线+candidates；收菜单不再靠前置 Intent |
| 误把「未跑意图」当成 fallback 空集 | FP-6 否决 |
| SSE 客户端不认新 stage | 仍用 `error` 事件；stage 为附加字段，文档写明 |

回滚：图边恢复 `intent_node` 在前；`PLAN_ON_FAIL` 默认改回等价于现网单 rag（若已发布，用 env 而非默改代码语义）。

---

## 8. 思考轮控制

| 轮 | 结论 | early_stop | reason | residual_risks |
|---|---|---|---|---|
| R0 | 目标=主编排优先且失败可见；意图退出第一步阻塞 | no | | |
| R1 | 范围=图边 + 首次规划失败语义 + 无 intent 时 scenario 短路；router/basic/闸链非范围 | no | | |
| R2 | 采纳方案 C；弃静默单 rag、弃切粗路由、弃本波合并意图 | no | | 工人侧意图另案 |
| R3 | 首次失败 vs 重规划沿用后缀必须分开；防 S1 误清空 | no | | 客户端对 stage 的展示未产品化 |
| R4 | 验收可单测图边与失败帧；不依赖真 LLM | no | | |
| R5 | draft 可交 20-spec-audit；**不可**当已签收 | no | 人签未发生 | HG-SPEC-SIGNOFF=pending |

`actual_last_round`：R5

### R0

讨论锁定：默认 supervisor 不是「总能答」；规划耗尽应失败。意图是控制面信号，不该挡在第一个 LLM。

### R1

角色：运维问答主路径。成功=规划成功后的现有工人链。失败=用户能区分「编排不可用」与「检索答完」。

### R2

见 §4。灾备 `single_rag` 保留为开关，避免把「默认硬失败」写成「永远不能降级」。

### R3

安全：不扩权、不读模型放行字段、high 可见性不动。依赖：既有 LLM 重试/熔断仍在本失败判定之前。

### R4

`test_strategy=required`。假 LLM/抛错注入即可测 FP-1，不必打真模型。

### R5

SPEC 为 draft。下一棒是书面审查或维护者签 `HG-SPEC-SIGNOFF`，然后 00 起草 task。本文件不授权改 `app/`。

---

## 9. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-19 | v0 draft：对齐本窗「supervisor 失败即失败 + 意图后置」 |
| 2026-10-19 | HG-SPEC-SIGNOFF approved（维护者本窗指示 · 00 代签）；三条 00 定夺（web 完成后同步 · N2 归 error · N1/N3/N4 按建议）落 invoke，task 起草吸收 |
