# Task：supervisor planner string-args 触发 `args_schema_invalid`（八段真落笔阻断 · prompt 资产面）

> **状态**：`draft`（10 落稿 · 四闸 pending · NO-GO 20/30）
> **类型**：fix / 缺陷修复（prompt 资产面 · planner 产出 string-args 致 gateway args_schema fail-closed 拒执行 · 预存在非回归）
> **上游**：issue [#339](https://github.com/Cyning12/ops-desk-api/issues/339)（backlog 正文 + 维护者 comment `6673790438` 令起草 · 受理依据 = 维护者 2026-11-06 08:48 授权（lead 全程代行签收与验收））
> **分支**：10/00 走 `agent/planner-args-fix-task-0796db4a2434`（本 PR · 部署绑定末段=工单名）· 30 实分支预登记 `fix/planner-args-schema`（待闸签收后另行授权）
> **10 注**：2026-11-06 · 承 issue #339 维护者 comment `6673790438` 令起草 fix task（**10 帽活** · 只产 task 档 + 10 invoke + lint PASS + PR · 禁改业务码）· 30 改码待闸签收后另行授权
> **诊断声明（10 档只读实扫 · 承维护者令「先诊断 prompt 资产根因再定修复面」）**：根因承载面已锚至 **prompt 资产层**（详见背景节机制链 · file:line 全锚）——两份 supervisor 资产 v2 均未文档化 `args` 结构化字段；**处置形态（拒收并约束输入 / 修复资产 / 转独立设计任务）留设计闸 HG-PLANNER-ARGS-DESIGN 裁决**，10 档不越权定修复面。

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `fix-planner-args-schema` |
| **git_branch** | `agent/planner-args-fix-task-0796db4a2434`（10 起草 PR 分支 · 部署绑定要求末段=工单名；30 实分支预登记 `fix/planner-args-schema`） |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 红测先行：负样本（维护者红线）=「planner 输出 args 通过 schema 校验（端到端）」——经**真规划→派发→执行路径**驱动（禁直造 state 直调 · 同链单测盲区教训）：先红（planner 产出 string-args → gateway `args_schema_invalid` fail-closed 拦截实证 · 复现 issue #339 两轮一致形态）后绿（裁决形态落地后 args 通过 schema 校验 · 真落笔执行断言达成）；gateway `args_schema` fail-closed 语义**永不放宽**（既有负样本组 `test_capability_gateway` / `test_capability_harness_cli` 全绿承接）；live 面留 40 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none`（预期：prompt 资产 md 修订 ± 解析层小改 · 无路由/表/事件类型/一级模块面；若 30 实扫出现图谱面须先回闸再动） |
| **graph_delta** | `n/a` |
| **graph_delta_note** | 模块边界不变（planner 提示词资产 / 子任务解析面内增量）；不触发图谱同步义务（承 AGENTS.md：仅新增路由/表/事件类型须同步）；HG-GRAPH-MODULES 以 `none` 口径随档签认 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 workspace contracts / freeze；本波零 wiki 面 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿（本 PR · task 档 + 10 invoke）→ 20-R1 书面审（审查文落盘 `docs/harness/reviews/`）→ 维护者签 **HG-PLANNER-ARGS-DESIGN**（处置形态裁决 · 设计闸）+ 三常闸（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES）→ PR 出货待审 → **30 改码须待闸签收后另行授权**（`fix/planner-args-schema` · GATE_VERIFY 闸据=本档闸表）→ 40 → CLOSE |
| **freeze_id** | `lg-rag-sse-v1`（**零 diff 红线**：SSE 事件表/帧形态） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **pending** | 20-R1, 30 | 初稿未经 20-task-audit 审查与维护者签收 |
| HG-AUDIT-R1 | **pending** | **30** | 20-task-audit R1 审查文未落盘 |
| HG-GRAPH-MODULES | **pending** | **30** | `none` 口径待签（无图谱面 · 承 seen-surface 先例；若 30 实扫出图谱面须回签） |
| **HG-PLANNER-ARGS-DESIGN** | **pending** | **30** | **设计闸（issue #339 维护者令设）· 处置形态裁决三案**：①拒收并约束输入（解析/契约层识别 string-args → 拒收并反哺 planner 重规划 · 复用 supervisor_replan_error_feedback 既有反哺面）/ ②修复资产（supervisor 两份 prompt 资产文档化 `args` 结构化对象 ± 目录块注入 args_schema · 改码面最小）/ ③转独立设计任务（诊断显示修复面溢出 prompt 资产 ± 解析层小改承载力时 · 本 task 转诊断销项另立设计）；**影响面签认**：全部写能力（stage-w `ops.write.run_note` 等）的 40 真落笔验证都等本修复 |

---

## 背景与目标

issue #339（backlog）：**live 八段真落笔中 supervisor planner 产出 string-args，`args_schema_invalid` 拒绝，两轮一致**（run `5bc63c8b…` 23:01 / `f193a5b9…` 23:04）——后果：**所有写能力的端到端真落笔验证被阻断**（机制面仍可实证）。stage-w 40 观察③同源，系 prompt 资产类预存在问题，**非 #332 引入、非回归**。

**10 档只读诊断（机制链 · 逐环锚定 · 承维护者令「先诊断 planner 提示词资产对 args 形态的约束在哪一层失效」）**：

1. **失效层 = prompt 资产（根因环）**：`app/ops/prompts/assets/lg_rag.supervisor.system.md:10`（v2 · 「type=tool：……input 为工具入参描述」）与 `app/ops/prompts/assets/lg_rag.supervisor.suffix.system.md:14`（v2 · 同句）——**两份资产均未文档化 `args` 结构化对象字段**；模型按提示词字面把入参即兴序列化为 JSON 字符串写进 `input`。stage-w 40 invoke 观察③（`docs/harness/invokes/by-task/stage-w-write-expand/invoke_20261105_40_verify.md`）早已登记「supervisor system prompt 未文档化 `args` 字段（写工具结构化入参靠提示词即兴）」。
2. **schema 侧从未阻拦（放行环）**：`app/ops/lg_rag/schemas/subtasks.py:21`（`input: str` min_length=1）——string-args 写在 `input` **完全合法**；`:23`（`args: dict[str, Any] | None`）存在但 prompt 从未提及 → 模型基本不产出 `args` 对象；`_parse_subtasks`（`app/ops/lg_rag/multi/nodes.py:186-231` · `:219-220` 仅当 `item.args` 非 None 才 `dict(item.args)`）对「input 内嵌 JSON 串」形态零识别。
3. **目录块信息缺口（加剧环）**：`_format_capability_catalog`（`nodes.py:104-121`）注入 planner 的目录块只有 id·description·risk·output_fields——**不含各能力 `args_schema`**；即便 prompt 文档化 `args` 字段，模型仍无从得知字段名/类型（修复资产案的连带面 · 裁决时须一并评估）。
4. **执行面回退（放大环）**：`tool_exec_node`（`nodes.py:1970-1974`）——`raw_args` 非 dict 时兼容回退 `call_args = result["input"]`（字符串）。
5. **fail-closed 拦截（显症环 · 正确行为）**：Gateway `_prepare_call`（`app/ops/capability/gateway.py:446` → `schema_validate.py:43`）invoke 模式 `validate_capability_args` 对 str 校验 → `args_schema_invalid: 期望 type=['object']，实际=str` → 真落笔被拦（**该 fail-closed 是抓出本缺陷的安全属性 · 红线：永不放宽**）。

**结论**：缺陷 = planner 提示词资产对 args 形态的约束缺失（第 1 环）+ 目录块 args_schema 信息缺口（第 3 环）的合力；解析/执行/网关三环节行为均符既有契约。**修复面处置形态（拒收约束 / 修资产 / 转设计）留设计闸裁决**——10 档不越权。

本 task = 该缺陷的最小修复竖切：**处置形态裁决后落地**（prompt 资产修订 ± 解析层小改 · 以签认为准）+ 红测负样本（端到端：planner 输出 args 通过 schema 校验）+ 常规路径零漂移对拍 + 全部写能力 40 真落笔解锁。

---

## 范围（竖切 · 四闸齐后才 30）

- [ ] **D-fix-1 · 处置形态落地**（30 · 形态以 HG-PLANNER-ARGS-DESIGN 签认为准 · 候选三案见闸表）：①拒收并约束输入案——解析/契约层识别 tool 步 string-args → 拒收并按统一口径处理（拒/修/转 · 反哺面复用 supervisor_replan_error_feedback 既有机制）；②修复资产案——两份 supervisor prompt 资产文档化 `args` 结构化对象（type=tool 必填语义 ± 目录块注入 args_schema 评估）；③转独立设计任务案——诊断显示修复面溢出时，本 task 转诊断销项、修复另立设计 task（签认时须明示承接编号）。
- [ ] **D-fix-2 · 红测负样本 + 常规对拍**（30 · 先红后绿留 invoke）：负样本（维护者红线）= 经真规划→派发→执行路径驱动 planner string-args 形态，端到端断言修复前 `args_schema_invalid` 拦截实证（先红）→ 修复后 args 通过 schema 校验、真落笔执行断言达成（后绿）；常规对拍 = 既有合法路径（对象 args 直驱 / 仅 input 的 legacy 兼容形态）与修复前零漂移。
- [ ] **D-fix-3 · 旧测适配**（30 实扫如实登记）：`tests/test_capability_gateway.py` / `test_capability_harness_cli.py`（args_schema 负样本组）/ supervisor 规划面测试族影响面逐枚列出 · 零适配或适配清单如实留痕。

### 非范围

- ❌ Gateway `args_schema` fail-closed 校验语义任何放宽（`validate_capability_args` / `_prepare_call` 拦截面 · 抓出本缺陷的安全属性 · 永不放宽）
- ❌ SSE 事件表 / 帧形态 / `event_store` 写入面（`lg-rag-sse-v1` freeze）
- ❌ HITL 消费语义 freeze 不动（写审批闸 / 消费门 / 幂等 / 台账键语义）
- ❌ resume 单路径（禁第二实现 / HTTP 自调 / 旁路线程）
- ❌ 改码面收敛边界外扩（闸链 / HITL 表 / 状态机 / auto-resume / 委派令牌 / worker freeze 面禁碰）
- ❌ 结构化输出网关（structured output gateway）级改造 / capability manifest schema 体系变更（若诊断显示必须走此面 → 设计闸转独立设计任务案 · 不在本 task 内自作主张）
- ❌ web 仓 / iOS / 平台项

---

## failure_paths

| # | 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|----------|----------|--------|----------|
| FP-1 | 四闸任一 pending 即 30 | **拒开工** | 是（签闸后） | 是 |
| FP-2 | **SSE 事件表出现 diff**（`lg-rag-sse-v1` 破） | 审查拒收 · 退回（红线） | 是 | 否 |
| FP-3 | **HITL 消费语义被改动**（写审批闸 / 消费门 / 幂等 / 台账键语义 freeze 面破） | 红线对拍 diff 非空 · 审查拒收退回（红线） | 是 | 否 |
| FP-4 | **resume 第二实现**（新恢复路径 / HTTP 自调 / 旁路线程） | 红线对拍红 · 审查拒收退回（红线） | 是 | 否 |
| FP-5 | **改码面外溢**（闸链 / HITL 表 / 状态机 / auto-resume / 委派令牌 / worker freeze 面被碰） | 红线对拍 diff 非空 · 审查拒收 | 是 | 否 |
| FP-6 | **Gateway args_schema fail-closed 被放宽**（str 放行 / 校验跳过 / fail-open 化 · 「让 string-args 能执行」当修复） | 红测拦截 · 审查拒收退回（红线 · 治标不治本且破安全属性） | 是 | 否 |
| FP-7 | 负样本未转绿即出货（planner string-args 仍致 `args_schema_invalid` 阻断真落笔） | 红测拦截 · 审查拒收 | 是 | 否 |
| FP-8 | 30 未经闸签收**自行裁决处置形态**（拒/修/转三案越过 HG-PLANNER-ARGS-DESIGN 自选定案） | 审查拒收 · 退回（决策点是闸的 · 30 只执行签认形态） | 是 | 否 |
| FP-9 | 修复资产案落地时**只改 prompt 字面不改信息缺口**（文档化 `args` 字段但目录块仍不给 args_schema → 模型仍不知字段名/类型 → 换个形态失败） | 负样本端到端仍红 · 审查拒收 | 是 | 否 |
| FP-10 | 拒收并约束输入案落地时**拒收变成静默吞单**（识别 string-args 后不留痕不反哺 · 计划悄悄缺步） | 负样本/对拍红 · 审查拒收（拒/修/转须按统一口径留痕 · 决策点留设计闸的口径落地） | 是 | 是（计划缺步可被用户察觉） |
| FP-11 | planner 输出解析失败/重规划兜底路径被本修复波及（fallback / carry / 保号语义漂移） | 关联回归红 · 审查拒收 | 是 | 否 |

---

## 验收标准

- [ ] 人工闸：HG-TASK-DRAFT · HG-AUDIT-R1 · HG-GRAPH-MODULES · **HG-PLANNER-ARGS-DESIGN** 均 approved（处置形态签认留档 · 影响面 = 全部写能力 40 验证等待已确认）
- [ ] 红测负样本（**维护者红线**）：planner 输出 args 通过 schema 校验（端到端 · 经真规划→派发→执行路径驱动）——先红（string-args → `args_schema_invalid` 实证）后绿（schema 校验通过 · 真落笔执行断言达成）
- [ ] 处置形态按签认落地（拒收约束 / 修资产 / 转设计三案之一 · FP-8 未越权自裁）
- [ ] 四红线零 diff 对拍：SSE 事件表（`event_store`/`sse_*` 零 diff）· HITL 消费语义 freeze 面零 diff · resume 单路径（`router.py`/`resume.py` 零 diff）· 改码面收敛（`git diff` 面 = 签认承载面唯一）
- [ ] Gateway args_schema fail-closed 既有负样本组全绿不放宽（`test_capability_gateway` / `test_capability_harness_cli`）
- [ ] 旧测适配如实登记（D-fix-3 清单）；supervisor 规划面 / tool_exec / 消费门测试族关联回归全绿
- [ ] 工程面：`ruff check app tests` 零；`pytest tests` 全量零新增红（如实登记）；`./scripts/graph-compile.sh` EXIT=0；`npx spec-wave task lint` PASS
- [ ] 40 复跑：全部写能力端到端真落笔验证解锁（issue #339 两轮一致形态不再复现 · 偏差登记口径承 #329/#334 先例）

---

## 依赖

| 依赖 | 说明 |
|------|-----|
| 缺陷源 | issue [#339](https://github.com/Cyning12/ops-desk-api/issues/339)（正文 + 维护者 comment `6673790438` 立项令：先诊断根因再定修复面 / 设计闸处置形态裁决 / task 档六要素 / 红测负样本 / 红线入 failure_paths / lint PASS 出货） |
| 同源证据 | issue #329 40 复跑实测（[`invoke_20261105_40_verify.md`](../../harness/invokes/by-task/fix-worker-state-send-run-id/invoke_20261105_40_verify.md) · 偏差② · 两轮 run 一致）· issue #334 偏差②（[`invoke_20261106_40_verify.md`](../../harness/invokes/by-task/fix-delegation-resume-approval-id/invoke_20261106_40_verify.md) · 维护者 item 3 口径）· issue #335 偏差② · stage-w 40 观察③（[`invoke_20261105_40_verify.md`](../../harness/invokes/by-task/stage-w-write-expand/invoke_20261105_40_verify.md)） |
| 同链先例 | [`task_fix_seen_surface_idempotency.md`](../done/task_fix_seen_surface_idempotency.md)（CLOSE · 设计闸两决策点 + 红线 + 红测端到端形态 + 10 档实扫声明先例）· [`task_supervisor_replan_error_feedback.md`](../done/task_supervisor_replan_error_feedback.md)（CLOSE · 拒收反哺面先例 · 拒收并约束输入案复用面） |
| 改码面（预期） | prompt 资产 md ± `_parse_subtasks` 解析层小改（以设计闸签认为准 · 候选锚点见背景节机制链）+ 新增回归测试 |
| freeze 参照 | SSE `lg-rag-sse-v1`（事件表）· HITL 消费语义 freeze · resume 单路径 |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 关联跟踪 | issue #323/#329/#334/#335 偏差链同源 · 本 task 修复后四单 40 真落笔面可复跑销项 |

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. 本 task（钉死契约 · 闸 · 非范围 · failure_paths · 背景机制链五环）
3. issue #339 全文（缺陷定性 · 维护者立项令与红线）
4. 代码：`app/ops/prompts/assets/lg_rag.supervisor.system.md` · `lg_rag.supervisor.suffix.system.md`（根因环 · 均未文档化 args）· `app/ops/lg_rag/schemas/subtasks.py:10-26`（`input: str` / `args: dict` schema）· `app/ops/lg_rag/multi/nodes.py:186-231`（`_parse_subtasks` 放行环）· `:104-121`（`_format_capability_catalog` 目录块信息缺口环）· `:1969-1975`（`tool_exec_node` 兼容回退环）· `app/ops/capability/gateway.py:443-460`（`_prepare_call` args_schema 校验 · fail-closed 永不放宽）· `app/ops/capability/schema_validate.py`（`validate_capability_args`）
5. 测试面：`tests/test_capability_gateway.py` / `tests/test_capability_harness_cli.py`（args_schema 负样本组）· supervisor 规划面测试族（`_parse_subtasks` / fallback / carry / 保号）
6. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 本 task = 维护者 issue #339 定性的 prompt 资产面缺陷（非回归 · 预存在）：planner string-args → args_schema_invalid 阻断全部写能力 40 真落笔；**10 档只读诊断已锚五环机制链**（prompt 资产未文档化 args = 根因环 · file:line 全锚）——缺陷真实承载面与「约束在哪一层失效」已实锤至资产层；模型为何选 string 形态的最终确认随 30 红测/40 复跑闭环 | no | — | 处置形态三案取舍取决于设计闸签认（影响面 = 全部写能力 40 验证等待 · 不轻裁） |
| R1 | 范围 = 处置形态落地（闸签为准）+ 红测负样本 + 常规对拍 + 条件旧测适配；非范围十一条锁定（gateway fail-closed 永不放宽 / SSE / HITL 消费 freeze / resume 单路径 / 改码面收敛 / 结构化网关级改造禁自作主张 / web 面） | no | — | none |
| R2 | 设计闸决策点 = **处置形态裁决三案**（issue #339 维护者令 · 决策点留闸不留 30）：①拒收并约束输入——解析/契约层识别 string-args 拒收 + 统一口径（拒/修/转）+ 反哺重规划（复用 supervisor_replan_error_feedback 面 · 代价=多一轮 LLM 往返 · 真落笔仍须模型下轮产出对象 args）；②修复资产——prompt 资产文档化 args ± 目录块注入 args_schema（代价=目录块字节变化须评估对既有 prompt 回归测试影响 · 模型遵循度非 100%）；③转独立设计任务——修复面溢出（结构化网关 / manifest 体系级）时转诊断销项另立设计 | no | — | 三案均非银弹：①治表（prompt 仍不发 args）②治本但遵循度不确定（live 两轮证据显示模型当前只认 input 字面）——签认时须带 30 探针证据择案或组合 |
| R3 | failure_paths 锚既有语义：四闸拒开工（FP-1）/ SSE 零 diff（FP-2）/ HITL 消费 freeze（FP-3）/ resume 第二实现（FP-4）/ 改码面外溢（FP-5）/ gateway fail-closed 放宽（FP-6）/ 负样本未绿出货（FP-7）/ 30 越权自裁形态（FP-8）/ 修资产只改字面不改信息缺口（FP-9）/ 拒收变静默吞单（FP-10）/ 解析兜底路径波及（FP-11） | no | — | none |
| R4 | 可测性：负样本必须经**真规划→派发→执行路径**驱动（禁直造 state 直调）；先红后绿（红 = 复现 issue #339 两轮一致 string-args 拦截形态 · 留 invoke）；常规对拍防过紧语义（legacy 仅 input 兼容形态 / 对象 args 直驱形态零漂移）；live 面留 40（全部写能力真落笔解锁销项） | no | — | 本地产能既有红基线如实登记口径沿用 |
| R5 | 起草落稿 · 四闸 pending · NO-GO 20/30；lint PASS 后出 PR 待审；30 改码须待闸签收后**另行授权**（issue #339 维护者令 · 受理依据 = 2026-11-06 08:48 授权 · lead 全程代行签收与验收） | no | — | 无 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：处置形态取舍待设计闸签认（R2 · 影响面 = 全部写能力 40 验证等待）

### R0 · 问题框定

issue #339 由维护者定性（backlog）：live 八段真落笔 supervisor planner 产出 string-args → `args_schema_invalid` 拒绝（两轮一致），阻断所有写能力端到端真落笔验证；stage-w 40 观察③同源，prompt 资产类预存在问题，非 #332 引入。维护者令「先诊断 planner prompt 资产侧根因再定修复面」——10 档只读实扫已完成：机制链五环逐环锚定（根因环 = 两份 supervisor prompt 资产 v2 均未文档化 `args` 字段 · `:10`/`:14`），「约束在哪一层失效」实锤至资产层；这与 stage-w 40 观察③的登记互相印证。

### R1 · 范围/非范围

范围三件套（处置形态落地 / 红测负样本 + 常规对拍 / 条件旧测适配）收敛为最小竖切；非范围把「会被顺手扩大」的面全部锁死：gateway fail-closed 永不放宽（FP-6 · 破安全属性的伪修复）、SSE 事件表、HITL 消费语义 freeze、resume 单路径、改码面收敛边界、结构化输出网关级改造（溢出走转设计案 · 不自作主张）、web 面。

### R2 · 方案对比（设计闸 · 处置形态裁决三案）

- **案 ① 拒收并约束输入**：解析/契约层识别 tool 步 string-args（input 内嵌 JSON 串形态 / args 非对象形态）→ 拒收并按统一口径处理（拒/修/转 · 口径由签认定），反哺面复用 supervisor_replan_error_feedback 既有机制（A 层前缀失败摘要段 + B 层契约闸 detail）。优点：不赌模型遵循度、fail-closed 方向一致、复用既有反哺面。代价：真落笔仍须模型下轮产出对象 args（多一轮往返）；治标不治 prompt 资产层（R0 根因环仍在）。
- **案 ② 修复资产**：两份 supervisor prompt 资产文档化 `args` 结构化对象（type=tool 时 args 为 JSON 对象 · 字段名/类型来源须解决——连带面 = `_format_capability_catalog` 目录块注入 args_schema · nodes.py:104-121）。优点：直击根因环、正路径零额外往返。代价：目录块字节变化波及既有 prompt 回归测试（TC 主路径 prompt 逐字节零 diff 类断言）；模型遵循度非 100%（live 两轮证据显示当前模型只认 input 字面 → 须 30 红测实证遵循率）。
- **案 ③ 转独立设计任务**：若 30 探针显示修复面溢出 prompt 资产 ± 解析层小改承载力（如须动结构化输出网关 / capability manifest schema 体系），本 task 转诊断销项、修复另立设计 task，签认时明示承接编号。优点：不硬塞大范围。代价：全部写能力 40 验证继续等待（影响面成本最高 · 签认须明示接受）。

### R3 · 边界/失败路径

FP-1~FP-11 逐条锚既有语义（见表）：核心边界 = gateway args_schema fail-closed 是抓出本缺陷的安全属性，任何「让它能过」的放宽都是伪修复（FP-6）；处置形态是闸的决策，30 只执行签认形态（FP-8）；拒收案须防静默吞单（FP-10）；修资产案须防只改字面不改信息缺口（FP-9）。

### R4 · 验收/可测性

核心可测性风险 = 重犯单测盲区：负样本必须经真规划→派发→执行路径驱动（禁直造全 state 直调）。红测先行：先以负样本红（string-args → `args_schema_invalid` · 复现 issue #339 两轮一致形态）锁定缺陷，修复后绿（args 通过 schema 校验 + 真落笔执行断言）。常规对拍（legacy 仅 input 兼容形态 / 对象 args 直驱形态零漂移）防过紧语义。live 全写能力真落笔解锁留 40 销项。

### R5 · 签收就绪

task 档落稿 · 10 invoke 落盘 · 四闸 pending · NO-GO 20/30；`spec-wave task lint` PASS 后出 PR 待审；30 改码须待闸签收后**另行授权**（issue #339 维护者令 · 受理依据 = 维护者 2026-11-06 08:48 授权（lead 全程代行签收与验收））。

---

### 自检结论（执行者）

> **hat 10（10 起草）** · 已落稿：task 档 + 10 invoke · 10 档只读诊断完成（机制链五环 file:line 全锚 · 承维护者令「先诊断再定修复面」）· 未改 `app/` / `tests/` · 未签任何 human_gate（四闸 pending · NO-GO 20/30）。

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_fix_planner_args_schema.md` | 0 | LINT: PASS（2026-11-06 · 10 起草自检） |
| `npx --yes spec-wave@3.5.0 task lint-wiki-delta --target .` | 0 | LINT: PASS（scope all · 本档 wiki_delta 预填） |

---

## 修订记录

| 日期 | 说明 |
|------|-----|
| 2026-11-06 | 10 落稿：承 issue #339 维护者 comment `6673790438` 令起草 fix task（10 帽活 · 只产 task 档 + 10 invoke + lint PASS + PR · 禁改业务码）· **10 档只读诊断五环机制链**（prompt 资产未文档化 args = 根因环 · file:line 全锚）· 设计闸 HG-PLANNER-ARGS-DESIGN 处置形态裁决三案（拒收并约束输入 / 修复资产 / 转独立设计任务 · 影响面 = 全部写能力 40 验证等待）· 红测负样本（planner 输出 args 通过 schema 校验 · 端到端）入 test_strategy · 四红线（SSE 事件表零 diff / HITL 消费语义 freeze / resume 单路径 / 改码面收敛）+ gateway fail-closed 永不放宽入 failure_paths · R0–R5 全轮 · 四闸 pending · NO-GO 20/30 |
