# Task：supervisor-first-fail-closed（主编排优先 · 规划失败即失败 · 意图后置）

> **状态**：draft（10-task 起草 · 待 20-task-audit + 维护者签 HG-AUDIT-R1 · **签前 30 拒改码**）
> **类型**：feature（supervisor 图入口顺序 + 首次规划失败语义；**不**新增路由 / 表 / 一级模块 / SSE `event_type`）
> **依据**：SPEC `docs/spec/supervisor-first-fail-closed/SPEC-supervisor-first-fail-closed_v0.md`（signed · HG-SPEC-SIGNOFF=approved 2026-10-19）· 20-spec-audit R1 审查 `docs/harness/reviews/spec_supervisor-first-fail-closed_audit_R1_20261019.md`（conditional_pass · N1–N4 移交）· 00 三条定夺 `docs/harness/invokes/by-task/supervisor-first-fail-closed/invoke_20261019_00_start.md`（**00 定夺 2026-10-19**）
> **分支**：`task/supervisor-first-fail-closed`（已切好）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `supervisor-first-fail-closed` |
| **git_branch** | `task/supervisor-first-fail-closed` |
| **implement_repo** | `ops-desk-api` |
| **spec** | `docs/spec/supervisor-first-fail-closed/SPEC-supervisor-first-fail-closed_v0.md`（signed） |
| **test_strategy** | `required` |
| **test_strategy_note** | 承 SPEC 元信息：supervisor 图边断言（无前置 intent 节点）· 首次规划耗尽 → SSE `error` 且 `stage=supervisor_plan` · 默认开关下禁止出现 `supervisor_fallback` 单 rag · 重规划沿用后缀与首次失败分叉单测 · 缺 intent 时 scenario 短路不裁（S1–S5 全短路，含 S4 缺省 risk_hint→high 收紧，00 定夺 2026-10-19 / R1-N1）· `mode=router`/`basic` 零 diff。假 LLM / 抛错注入即可机断，**不打真模型** |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` 预期（复用既有 `error` 事件类型，只扩 `error.stage` 字面量 `supervisor_plan`；不增路由/表/一级模块）。若 30 需新增 SSE `event_type` → 回 SPEC 判 G-L* 并升 freeze，**禁** silent 扩 |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` `lg_rag` 行备注回写 `error{stage:supervisor_plan}`（承 R1-N3 · 00 定夺 2026-10-19） |
| **graph_delta_note** | 无模块增删仅备注；预期 graph_change_layer=none，若实现越出须回本 SPEC |
| **wiki_delta** | `n/a`（30 实判，可选 volatile 短注） |
| **wiki_delta_note** | 契约真值回写以 05 §4.2 为准（见 N3 验收条） |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `required` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿（本文件）→ 20-task-audit R1 → 维护者签 HG-AUDIT-R1 → 30（红测先行）→ 40 → PR+CI 绿 → CLOSE → **下游棒**：ops-desk-web 另 task 同步对外展示 |
| **freeze_id** | 对照 `lg-rag-sse-v1`：**不**升 freeze、**不**新增 `event_type`、仅扩 `error.stage` 字面量（承 run-worker / disconnect-completion 先例 · R1-N3 · 00 定夺 2026-10-19）；扩字面量须回写 05 §4.2 词表 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-SPEC-SIGNOFF | approved | 10, 20 | 2026-10-19 维护者本窗指示「其他条目都按照建议来执行」· 00 代签 · 见 SPEC 闸表 |
| **HG-AUDIT-R1** | **pending** | **30** | 待本 task 草稿 → 20-task-audit → 维护者人签；**签前 30 拒改码** |
| HG-GRAPH-MODULES | approved | 30 | 01_modules.md:79 · 2026-08-30（graph_change_layer=none 预期，不再签） |

---

## 背景与目标

### 问题

默认请求已走 supervisor 图，但图内第一个 LLM 仍是细意图（`intent_node`），且 `supervisor_node` 在规划 LLM 失败时**静默改成单 rag**（`supervisor_fallback`）——用户看到的像一次正常作答，观测上却已换了规划器，与「主编排是唯一规划脑、失败必须可见」的契约冲突。

### 目标（承 SPEC §1–§2）

supervisor 图改为 **无 LLM 的 Builder → supervisor**；**首次规划**在工厂重试/跨档耗尽后发 `error`（**`stage=supervisor_plan`**）并停图；细意图**退出主路径阻塞位**（不删模块概念、不并进 supervisor 同一次调用、不切到 router 粗路由）。

---

## 范围

单 task，三块一起做（承 SPEC §2 D1/D2/D3；任缺一块即假成功或误清空）：

### D1 · 图入口：Builder 在前，第一个 LLM 是 supervisor

- 图边改为 `START → strategy_builder → supervisor → …`；其后 join / observe / aggregator / critic **不改拓扑**。
- supervisor 图**不再**挂前置 `intent_node`（`intent_node` 可留在包内供对照/后续波，supervisor 图默认编译路径不得调用）。
- `POST /api/ops/lg-rag/stream` 默认 `mode=supervisor` 不变，不换路径。

### D2 · 首次规划失败 = 失败（默认）

- 触发（首次规划，无 locked 前缀）：LLM 异常、工厂重试/跨档耗尽、输出无法解析、非法 tool id 导致整 plan 作废。
- 默认行为：**不**写入单 rag 子任务；图收口为失败；SSE 一帧 `error`，`stage=supervisor_plan`，再终态（沿用现有 done/error 收流纪律，不发明新 `event_type`）。
- 可观测：span/log 含 `supervisor_plan_failed=true`；**禁止**同时标 `supervisor_fallback=true` 且继续 aggregator 出「完整答案」。
- 重规划例外：已有 locked 前缀时，规划失败**沿用未解决后缀**（现网分支保留）。分叉判据保持 `if locked:` **不扩**为 `locked or preserved`（R1-N2 边缘形态归 error · **00 定夺 2026-10-19**）。
- 灾备开关 `LG_RAG_SUPERVISOR_PLAN_ON_FAIL`：`error`（**默认**）| `single_rag`。 `single_rag` 仅显式打开；必须 `degraded=true` 进 span/终帧元数据，且**不得扩权**（allowlist 只许更窄）。非法值 / 未设回退 `error`。

### D3 · 意图后置（主路径不阻塞）

- supervisor 主路径**不写** `intent` / 不把缺省当成 `intent_fallback=true`。
- Builder 不再因 `needs_tool is False`（来自前置意图）清空 allowlist；allowlist = 基线可见 ∩ candidates。
- scenario：无本轮 intent 时**短路、不裁**（等价本轮不做 S1–S5，**含 S4 缺省 risk_hint 视同 high 的收紧路径**，R1-N1 · 00 定夺 2026-10-19）；**禁止**把「没跑意图」映射成 S1 空集或任何非基线裁剪。

## 非范围

- ❌ 把意图物理合并进 `supervisor_node` 同一次 completion
- ❌ 工人侧局部意图 / 下沉 `IntentV1`（另 SPEC）
- ❌ 删 `IntentV1` schema、删 `mode=router` 粗路由、改 router 的 `#数字` 快路径
- ❌ 用粗意图图承接 supervisor 失败（不切 `mode=router`，不跑 `rag|direct|refuse` 粗分类当 failover）
- ❌ 改六道门、Policy、委派令牌、HITL 挂起语义
- ❌ 为 high 风险能力新开「进菜单」豁免（`deny_high_risk` 维持）
- ❌ 改 SSE 路径、新增 `event_type`、改鉴权、升 freeze
- ❌ 重规划沿用后缀改成也硬失败（本波保留现网该分支）
- ❌ 扩展分叉判据为 `locked or preserved`（00 定夺 2026-10-19 明确不扩）
- ❌ **前端 / ops-desk-web 任何改码**（对外展示同步为下游棒 · 另 task · 见下）
- ❌ **本起草阶段零 `app/` 改码**（仅 docs）

### 下游 / 后续棒（00 定夺 2026-10-19 第 1 条 · **不进本 task 范围**）

| 棒 | 内容 | 时序 |
|---|------|------|
| ops-desk-web 另 task | 对外 Web 展示同步新 `error{stage:supervisor_plan}` 帧的呈现，用户可区分「编排不可用」与「检索答完」 | 本后端 task 完成后，在 ops-desk-web 仓**另立 task** 处理 |

---

## 失败路径（failure_paths）

承 SPEC §5 FP-1~FP-8，并按实现粒度细化（FP-1b 为 **00 定夺 2026-10-19 第 2 条 · R1-N2** 显式落表）：

| ID | 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----|----------|----------|--------|----------|
| FP-1 | 首次 `supervisor` LLM 抛错 / 工厂重试·跨档耗尽 | SSE `error.stage=supervisor_plan` 后终态；无单 rag plan；无 aggregator 终答冒充成功；span/log `supervisor_plan_failed=true` | 用户重问 | 一帧 error（stage 可机读） |
| FP-1b | **locked 空 + preserved 非空**（hitl 批准单步写形态）的重规划失败 | **同 FP-1**：归「首次失败 → error」，`error.stage=supervisor_plan`；分叉判据保持 `if locked:` **不扩**（00 定夺 2026-10-19 · R1-N2） | 用户重问 | 一帧 error |
| FP-2 | 首次输出非法 JSON 或 tool id 全非法 | 同 FP-1（默认 `error`） | 用户重问 | 一帧 error |
| FP-3 | env=`single_rag` | 允许单 rag；终态/span `degraded=true`；allowlist 不得比失败前更宽 | 用户重问 | 正常作答但 `degraded` 可机读 |
| FP-4 | env 非法 / 未设 | 行为同 `error`（FP-1） | 用户重问 | 一帧 error |
| FP-5 | 已有 locked 前缀的重规划失败 | **沿用未解决后缀**；不发 `supervisor_plan` 错误终态；不收缩成只剩前缀；观测不冒充成功 | 用户重问 | 现网行为保持 |
| FP-6 | 主路径无 intent | scenario 短路不裁（S1–S5 全短路，含 S4 缺省 risk_hint→high 收紧 · R1-N1）；不把目录裁空；`intent_fallback` 不为 true | — | 工具菜单 = 基线∩candidates |
| FP-7 | `mode=router` 或 `basic` | 与改前逐行为一致（不套用 D2） | — | 零 diff |
| FP-8 | 模型在 plan/ctx 顶层写 `allow_write` 等 | 仍不生效（Policy Host-only **零改动**，回归断言） | — | 无越权 |
| FP-9 | HG-AUDIT-R1 未签即 30 | GATE_VERIFY 拒开工 | 是 | — |

---

## 验收标准

全部可机断（假 LLM / 抛错注入 / 夹具，**不打真模型**）：

- [ ] **TC1 图边**：supervisor 图编译边为 `START → strategy_builder → supervisor`；默认编译路径无 `intent_node`（断言编译图边集合，非源码字符串匹配）。
- [ ] **TC2 首次失败（默认 env）**：注入 supervisor 规划 LLM 抛错 / 耗尽 → SSE 恰一帧 `error` 且 `stage=supervisor_plan` 后收终态；state 无 fallback 单 rag（无 `t1` 单 rag plan）；不进入 aggregator 成功终答；span/log 含 `supervisor_plan_failed=true`。
- [ ] **TC2b N2 形态（00 定夺 2026-10-19）**：构造 locked 空 + preserved 非空的重规划失败 → 行为同 TC2（`error.stage=supervisor_plan`）；断言分叉判据仍为 `if locked:`（未扩为 `locked or preserved`）。
- [ ] **TC3 解析失败**：首次输出非法 JSON / tool id 全非法 → 同 TC2。
- [ ] **TC4 env 三档**：`LG_RAG_SUPERVISOR_PLAN_ON_FAIL=single_rag` → 单 rag + `degraded=true`（span/终帧元数据），allowlist 不比失败前更宽；未设 / 非法值 → 行为同 `error`。
- [ ] **TC5 重规划沿用后缀**：已有 locked 前缀时规划失败 → 沿用未解决后缀（不发 `supervisor_plan` 错误终态 · 不收缩成只剩前缀）；既有用例保持绿。
- [ ] **TC6 无 intent 轮 scenario 全短路（R1-N1 · 00 定夺 2026-10-19）**：无 intent 的一轮（含 `LG_RAG_VISIBILITY_SCENARIO_MODE=enforce` 档）：scenario_trim 对 S1–S5 全短路——`visible` 进 = `visible` 出**逐 id 对拍**；allowlist ≡ 基线可见 ∩ candidates；显式覆盖 **S4 缺省 risk_hint→high 收紧**路径（收紧后 allowlist ≠ 基线∩candidates 即红）；`intent_fallback` 不为 true。
- [ ] **TC7 对照轨零 diff**：`mode=router` / `mode=basic` 既有测试无行为差（不套用 D2）。
- [ ] **TC8 Policy 回归**：plan/ctx 顶层 `allow_write` 等模型放行字段仍不生效（Host-only 零改动）。
- [ ] **TC9 契约回写（R1-N3 · 00 定夺 2026-10-19）**：回写 `docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §4.2 `error.stage` 词表（新增 `supervisor_plan` 字面量）+ `docs/_tech_graph/l1/01_modules.md` 备注；**不**升 freeze、**不**新增 SSE `event_type`；`graph-compile` EXIT=0。
- [ ] **TC10 反回归全量**：`pytest` 全量绿（新增覆盖上述路径）；`ruff` 触及路径绿。

## 依赖

- base `task/supervisor-first-fail-closed`（自 master 切出）。
- 锚点（10 未逐行亲读 · 行号录自 R1 审查实证 · 30 按实校正）：
  - `app/ops/lg_rag/multi/graph.py:80-106`（图边 `START → intent_node → strategy_builder → supervisor`，:96-98）
  - `app/ops/lg_rag/multi/nodes.py:1070-1230`（`supervisor_node`；:1094 `locked = _locked_prefix(state)`；:1157-1193 fallback 分叉 `if locked:` → `_carry_plan` / `else` → 单 rag `t1` :1193）
  - `app/ops/strategy/intent.py:52-94`（SO 失败写 `intent_fallback`）
  - `app/ops/strategy/builder.py:111-190`（:121-122 只读 `state.intent` + `state.intent_fallback`；:147 `needs_tool is False` → 空 allowlist）
  - `app/ops/strategy/scenario.py:40-91`（:49-52 默认 `off`；:70-91 S1–S5 规则表；:81-90 S4 缺省 risk_hint 视同 high）
  - `docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §4.2（`error.stage` 词表回写点）
  - `docs/_tech_graph/l1/01_modules.md`（`lg_rag` 行备注回写点）
- 审查/定夺真值：`docs/harness/reviews/spec_supervisor-first-fail-closed_audit_R1_20261019.md` · `docs/harness/invokes/by-task/supervisor-first-fail-closed/invoke_20261019_00_start.md`
- **不**依赖 ops-desk-web 改码开工（下游棒时序=后端完成后）。

## 给执行帽的必读列表

1. 本 task 全文（含人工闸表 · HG-AUDIT-R1 未签不得 30）。
2. SPEC `docs/spec/supervisor-first-fail-closed/SPEC-supervisor-first-fail-closed_v0.md` 全文（D1/D2/D3 · §3 非范围 · §5 FP · §6 验收 · §7 风险/回滚）。
3. 上列锚点文件全文相关段（禁信转述 · 行号按实校正）。
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`。
5. freeze 先例：`docs/tasks/done/task_lg_rag_sse_run_worker.md` · `docs/tasks/done/task_lg_rag_sse_disconnect_completion.md`（同 freeze 扩 `error.stage` 字面量 + 回写 05 纪律）。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|------|-----------|----------------------|----------------|
| R0 | 目标=主编排优先且失败可见；意图退出第一步阻塞位（承 SPEC R0） | false | — | — |
| R1 | 范围=D1 图边 + D2 首次失败语义 + D3 无 intent 短路；R1 审查 conditional_pass · N1–N4 移交本 task | false | — | N2 形态归属未定（→ 00 定夺收） |
| R2 | 方案承 SPEC 裁定 C；弃静默单 rag、弃切粗路由、弃本波合并意图；三条 00 定夺（2026-10-19）逐条吸收：N2 归 error 判据不扩 · N1/N3 入验收 · web 同步列下游棒 | false | — | 客户端对 stage 的展示未产品化（下游棒） |
| R3 | 反例闭合：首次失败 vs 重规划沿用后缀分叉（`if locked:`）· S1 误清空 + S4 收紧残留（N1 显式断言）· env 三档不扩权 · Policy Host-only 回归 | false | — | — |
| R4 | 验收 TC1–TC10 全部可假 LLM/抛错注入机断；红测先行；不打真模型 | false | — | — |
| R5 | 草稿可交 20-task-audit；**不可**当已签收 | false | — | **HG-AUDIT-R1=pending**（待 20 审 + 维护者人签 · 签前 30 拒改码） |

**actual_last_round**：R5

### R0 · 问题框定

默认 supervisor 不是「总能答」；规划耗尽应诚实失败。意图是控制面信号，不该挡在第一个 LLM（承 SPEC §8 R0）。

### R1 · 证据与审查

现状锚点经 20-spec-audit R1 实证（graph.py / nodes.py / intent.py / builder.py / scenario.py 四处同构）；R1 结论 conditional_pass · 阻塞项 0 · N1–N4 移交。

### R2 · 方案与定夺

承 SPEC §4 方案 C。三条 **00 定夺 2026-10-19** 逐条吸收：① web 同步列下游棒（ops-desk-web 另 task，不进范围）；② N2 边缘形态（locked 空 + preserved 非空）归 error，判据 `if locked:` 不扩；③ N1/N3 写入验收（TC6 / TC9）。

### R3 · 反例与边界

安全面：不扩权、不读模型放行字段、high 可见性不动（FP-8 / TC8）。env `single_rag` 灾备必须 `degraded=true` 且只许更窄 allowlist（FP-3 / TC4）。

### R4 · 验收/可测性

`test_strategy=required`；TC1–TC10 均可用假 LLM / 抛错注入 / 夹具机断；图边断言、SSE error 帧 stage 断言、env 三档、无 intent allowlist 对拍、router/basic 回归、Policy 回归，无一条依赖人工判断。

### R5 · 收口

草稿交 20-task-audit；**HG-AUDIT-R1=pending**，维护者人签前 30 拒改码。本文件不授权改 `app/` / `tests/`。

### 自检结论（10-task · 2026-10-19）

- **范围/非范围互斥**：D1–D3 与非范围十一条无重叠；「不切 mode=router」（D2 明确不做）与非范围「router 粗路由零改」、FP-7/TC7「对照轨零 diff」三方互锁；「不扩判据」与非范围末三条互锁；web 展示同时列入非范围与下游棒。
- **每条验收可机断**：TC1–TC10 全部可假 LLM/抛错注入/夹具断言，无人工判断项。
- **三条 00 定夺逐条可追溯**（文中均标注「00 定夺 2026-10-19」）：① web 同步 → 「下游/后续棒」节 + 非范围；② N2 归 error → FP-1b + TC2b + D2 分叉判据行；③ N1/N3/N4 按建议 → TC6（S4 显式）· TC9（05 §4.2 + 01_modules.md 回写）· 本 invoke 目录文件已在册（N4 由 00 补 `invoke_20261019_00_start.md` 闭环）。
- **R1-N1/N2/N3 落点**：N1→TC6 · N2→FP-1b/TC2b · N3→TC9 + 元信息 freeze_id 行。
- **闸纪律**：HG-AUDIT-R1=pending 在表 · R5 residual 同；本帽未改 `app/` / `tests/`。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-19 | 10-task 草稿（吸收 R1 审查 N1/N3/N4 + 三条 00 定夺）：范围承 SPEC D1/D2/D3 · failure_paths FP-1~FP-9（FP-1b=N2 归 error）· 验收 TC1–TC10（TC6=S4 显式断言 · TC9=05 §4.2+01_modules 回写）· 下游棒=ops-desk-web 展示同步 · HG-AUDIT-R1=pending |
