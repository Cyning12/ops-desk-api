# Task：Agent Host V1-A · 委派令牌（DelegationToken 六字段 + 签发点 + 验签门 + 审批口径 + 审计台账 + requested_scope 声明∩裁剪）（host-v1-delegation-token）

> **状态**：`active`（2026-09-23 · 20-task-audit R1 **PASS-WITH-NITS**（零阻塞 · N1–N5 已微修留痕）· HG-AUDIT-R1=**approved** 00 代录 · 30 可委派开工）  
> **类型**：feature（图内化新安全面 · **零 alembic 义务**（零新表零列 · 进程内令牌形态 · SPEC §3 锁死）· **有图谱义务按实判**（capability/lg_rag 行备注 + 人签新行 00 代录位 · Q3 裁定不新增一级模块））  
> **上游 SPEC**：`docs/spec/host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md`（**signed** · HG-SPEC-SIGNOFF=approved 2026-09-23 · 00 代录 · 维护者令原话留痕 SPEC 状态行；Q1 HMAC-SHA256 / Q2 只读自动·其余 HITL / Q3 不新增一级模块签收锁死）  
> **长程上下文**：Agent Host v1.0 五波之首（[`../spec/agent-infra/07_host_v1_landing_plan_v0.md`](../spec/agent-infra/07_host_v1_landing_plan_v0.md) signed）；启动 invoke：`docs/harness/invokes/by-task/host-v1-landing/invoke_20260923_00_host-v1-landing.md`  
> **分支**：`task/host-v1-delegation-token`（**禁止 master/main 直改 · 30 由 00 委派子 Agent 执行**）  
> **10 注**：2026-09-23 · 本棒由 00 亲起（无初稿时起草第一步 · 承 harness-00-delegate-only 例外条款）；HG-AUDIT-R1 落稿时待签（10 帽不签）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `host-v1-delegation-token` |
| **git_branch** | `task/host-v1-delegation-token` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 六类拒绝断言（R-a~R-f + 篡改）· 全链路携令牌断言（fake adapter）· 审批留痕断言（只读自动 / 写能力 HITL 双路径）· replan 重签发断言（旧 nonce 作废）· 三档模式断言（off 零 diff / observe would_block / enforce 拒）· requested_scope 声明∩裁剪矩阵；pytest 单测为主不开服务 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` 行备注（Q3 裁定**不新增一级模块**：`capability` 行备注 delegation 令牌模型+验签门 · `lg_rag` 行备注 subtask_join 签发接线+requested_scope；HG-GRAPH-MODULES 人签新行随 30 交付落盘 00 代录位；不增 implementedBy · G-L2 indexes 不扩） |
| **graph_delta** | 有（capability/lg_rag 两行备注 + 人签新行 · 零新一级模块 · 零新跨模块边——`lg_rag→capability` 既有边复用） |
| **graph_delta_note** | **回炉补闸条款**：若 30 实现形态偏离本预判（新增一级模块 · 新增表/列触发 alembic · 新增 SSE 事件类型 · 新增 HTTP 路由 · 改 freeze 契约 · 改六道闸既有语义），不得沿用本裁定——退回 10-spec/10-task 补闸 + `docs/_tech_graph/` 如实登记后续做（承 invoke §6 形态偏离回炉条款） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 SPEC `host-v1-delegation-token`；capability 模块 docstring/README 同步属 D4 范围项非 wiki |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 单 task 直通：10 落稿 → 20-task-audit → HG-AUDIT-R1（00 代录）→ 30（00 委派子 Agent · 承 SPEC §2 序：D1 令牌模型 → D5 requested_scope → D2 签发点 → D3 验签门 → D4 审计 → D6 断言收口）→ 40 → PR + CI 绿 + merge → 图谱回写（00 代录 HG-GRAPH-MODULES）→ CLOSE |
| **freeze_id** | 无（不改 lg-rag-sse-v1 / lg-rag-http-v1 / lc-evidence-http-v1；SSE 零新事件类型；零新 HTTP 路由） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20-R1, 30 | 2026-09-23 · 00 代录（维护者令 2026-09-23 原话：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」· 授权面含 HG-TASK-DRAFT · 承 invoke §授权面） |
| HG-AUDIT-R1 | **approved** | **30** | 2026-09-23 · **00 代录**（维护者令原话：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」· 2026-09-23 本窗追认令「授权00可以签收所有过程文档」）；依据：20-task-audit R1 **PASS-WITH-NITS** 零阻塞（`docs/harness/reviews/task_host_v1_delegation_token_audit_R1_20260923.md` · 六面全核 + 锚点 5+5 亲读亲跑）；N1–N5 非阻塞项已由 00 微修留痕（修订记录） |
| HG-GRAPH-MODULES | approved | **30** | 2026-09-23 真读 `docs/_tech_graph/l1/01_modules.md`：模块表已建置（bootstrap 签 2026-07-16 · 签录链完整至 2026-09-23 主线裁定行）；`capability`/`lg_rag` 行在表；本 task 图谱新签义务（两行备注 + 人签新行 00 代录位）**随 30 交付落盘**；Q3 裁定不新增一级模块 |
| HG-PILOT-OPSDESK-GLAYER | n/a | 物理分层试点改码 | 本 task 不涉物理分层试点改码 |

---

## 背景与目标

现状（SPEC §1 锁死 · 2026-09-23 本帽复核一致）：supervisor→工人分发有 step_contract 校验点（`multi/step_contract.py`）与六道闸执行网关（`capability/gateway.py::_prepare_call` :258），但**无授权产物**——工人能力调用权来自图内位置而非可核验凭据；大纲 v0.2 #6 判「雏形 · 缺授权令牌签发」；工程约束 C2 要求「任何主→子委派都签发令牌，即使图内分发」。

一句话目标（SPEC 锁死）：委派时签发六字段令牌（能力集/TTL/一次性/参数约束/主体绑定/签名），工人执行能力前验签（`_prepare_call` 闸链之前插验签门），签发审批按 Q2 分级口径（只读自动 · 其余 HITL），叠加 A2 `requested_scope` 显式化（Builder 升级「声明∩裁剪」）；**图内化 · 无网络面 · 默认关三档模式**。

设计纪律（30 不得违反 · 承 SPEC §1 签收锁死）：

1. **Host 权威**：验签不做成模型可选 tool；`requested_scope` 只收窄不放宽（有效 scope = 声明 ∩ Host 侧裁剪）；策略键不可由 plan 写入。
2. **默认关上线**：`LG_RAG_DELEGATION_TOKEN_MODE=off|observe|enforce` 默认 `off`（关闭=现状逐字节零 diff）；非法值回退 `off`。
3. **审计记动作不记内容**：令牌只记 token_id/version/集合基数/过期时刻；参数约束命中记字段名哈希；不落新表（既有 logger + span 面）。
4. **Tier 1 语义**：签发序号单调 · 令牌版本化（version/kid）· 同 subtask 重签发=新例生效旧 nonce 作废（supersede 审计）· **禁续期**。
5. **零 freeze 动**：不改 freeze 契约 · SSE 零新事件类型 · 零新路由 · 零新表。
6. **自包含凭据**：令牌可序列化入 state/checkpoint；验签零 IO（禁查库禁网络）；TTL 锚定墙钟。

---

## 现状锚点（只读 · 30 必读 · 10 已扫）

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| 验签门插入位（**D3 落点**） | `app/ops/capability/gateway.py::_prepare_call` :258-385 | 闸链序：lookup→enabled→Policy→熔断→配额/kill switch→args_schema；验签门插 **lookup 之前**（无有效令牌连注册表都不查）；被拒调用不落回执（`_blocked_result` :219-255 先例——闸门拦下=没执行=不留回执） |
| 签发点（**D2 落点**） | `app/ops/lg_rag/multi/graph.py` :94-102（`subtask_join` + `route_next_subtask` 分发）· `multi/nodes.py` | supervisor→subtask_join→条件边分发工人；签发在分发路径为每个待执行子任务签发并注入 state |
| 委派消费点（**D3 接线**） | `app/ops/lg_rag/multi/nodes.py:1050-1091` `tool_exec_node` | 经 `capability_ainvoke(tool_name, call_args, ctx=cap_ctx)`；ctx 已含 `tenant_id`（:1081-1083 · 阶段 T ContextVar 先例）——令牌与 `_delegation_required` 标记随 cap_ctx 注入 |
| plan schema（**D5 落点**） | `app/ops/lg_rag/schemas/subtasks.py` | `SubtasksPlan`（:29-38 · extra=ignore · cap 外坏项不整单作废纪律）；增 `requested_scope: list[str] \| None` |
| Builder 裁剪（**D5 落点**） | `app/ops/strategy/builder.py` | `build_allowlist_from_candidates` :38-59（Registry∩Policy 求交 · stripped 审计先例 :54-58）；升级为「声明∩裁剪」复用同函数形态 |
| Policy 门类（**Q2 边界判定复用**） | `app/ops/capability/policy.py` | 高危/sandbox/cli 默认 blocked · Host-only 策略键；Q2 自动放行边界三条件（scope 内 / 全只读 / 非沙箱·cli）纯代码判定复用此面 |
| HITL 回路（**Q2 审批落点**） | `app/ops/hitl/` | interrupt 真挂起 + `Command(resume)` 真恢复 + `ops_hitl_requests` 留痕；签发审批复用既有回路（**不建新审批面**） |
| step_contract 先例 | `app/ops/lg_rag/multi/step_contract.py` | `_env_int` 非法回退默认（:33-42）· MAX_FIELDS 上限纪律（:23）· 纯函数零 LLM 零 IO（:15）——delegation.py 同形态 |
| env/错误码纪律 | `capability/errors.py` | 错误码词表「七个、不增」先例——验签拒绝用既有码 + meta detail 区分（先例：`result_contract.py:23/:44/:61-62` + `errors.py:102-103`；`gateway.py:557-559` 同形态 · R1 审查 N1 修正） |
| 命名冲突扫 | `grep -rn 'delegation\|requested_scope\|DelegationToken' app/ tests/` | **零命中**（2026-09-23 本帽真跑）；`LG_RAG_DELEGATION_*` env 名零冲突（仅 SPEC 文档命中） |
| 测试基线 | `.venv/bin/python -m pytest tests --collect-only -q` | **1368 collected**（2026-09-23 本帽真跑）；相关面用例见 B1 清单 |
| alembic 义务 | 无 | 零新表零列（SPEC §3 锁死）；迁移 diff 为空入验收断言 |

---

## 钉死契约（自 SPEC §2/§4/§5 锁死；30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **令牌模型（D1）** | `app/ops/capability/delegation.py` 新增 `DelegationToken` frozen dataclass：`token_id/version/kid/capability_set/ttl_seconds/issued_at/expires_at/one_shot/nonce/param_constraints/subject_binding/signature`；不可变；可序列化入 state/checkpoint |
| **签名（Q1 裁定）** | HMAC-SHA256 对 canonical JSON（排序键 · 紧凑分隔符）签名；密钥 env `LG_RAG_DELEGATION_TOKEN_SECRET` 注入 · **禁硬编码**；enforce 缺密钥 → 拒绝签发+告警；`kid` 预留轮换 |
| **签发点（D2）** | `subtask_join` 分发路径逐子任务签发；签发序号单调；同 subtask_id 重签发 → 新例生效 + 旧 nonce 作废 + `token_superseded` 审计；**禁续期**（FP-1） |
| **审批口径（Q2 裁定）** | 自动放行边界 = capability_set ⊆ 有效 scope **且**全 `side_effect ∈ {none, read}` **且**非 sandbox/cli 类；其余 → HITL_REQUIRED（复用 `hitl` 回路 · 留痕 `ops_hitl_requests`） |
| **验签门（D3）** | `_prepare_call` 闸链 **lookup 之前**；仅 ctx 携 `_delegation_required=True` 强制（tool_exec_node 注入）；六类拒绝 R-a~R-f 全部 `ok=False` 不抛异常不拖垮整图；被拒调用**不落回执**（`_blocked_result` 先例） |
| **TTL（FP-2 裁定）** | 墙钟 `expires_at`；`LG_RAG_DELEGATION_TOKEN_TTL_SECONDS` 默认 600 非法回退；resume 后过期即拒 → 分发路径重签发；HITL 挂起不延长令牌寿命 |
| **一次性（FP-1/FP-5 裁定）** | `one_shot` 默认 True（tool_exec 委派一律一次性）；nonce 消费登记进程内 TTL 缓存；replan/resume/重发一律重签发新例 |
| **参数约束（D1）** | v1 子集 = `enum`/`max_len`/`pattern` 三种纯代码校验；未知约束类型 → **拒绝签发**（安全默认） |
| **主体绑定（D1）** | `{tenant_id, user_id, run_id, subtask_id}`；tenant 取自 ctx/ContextVar（阶段 T · C6）；模型产出不得参与身份构造 |
| **requested_scope（D5）** | `SubtasksPlan.requested_scope: list[str] \| None`；有效 scope = 声明 ∩ allowlist；越界 id 剔除+审计（`scope_stripped`）；未声明 → 兼容现状隐式 allowlist；声明上限 `MAX_SCOPE_IDS=64` 截断+审计；只收窄不放宽 |
| **模式开关（D3）** | `LG_RAG_DELEGATION_TOKEN_MODE=off\|observe\|enforce` 默认 `off`；observe = 完整验签只记 `would_block` 不拦；非法值回退 off |
| **审计（D4）** | `token_issued / token_issue_hitl_required / token_superseded / token_verified / token_rejected:<class>` 进 logger + span metadata；记动作不记内容；不落新表 |
| **图谱（D6 随 30）** | `capability` 行备注（delegation 令牌模型+验签门）+ `lg_rag` 行备注（签发接线 + requested_scope）+ HG-GRAPH-MODULES 人签新行（**00 代录位**）；`./scripts/graph-compile.sh` 绿；零新一级模块 |
| **安全** | 无新凭证面（复用 env 注入密钥 · 无新 token 体系）；无新网络面/对外端点；验签零 IO；审计不含参数原值（无 PII 泄漏面） |

---

## 范围（单 task 直通 · SPEC §2 D1–D6）

- [ ] **D1 · 令牌模型（必做 · 核心）**：`capability/delegation.py` —— `DelegationToken` frozen dataclass + canonical 序列化 + HMAC-SHA256 签名/验签纯函数 + 参数约束校验子集（enum/max_len/pattern · 未知类型拒签发）+ nonce 消费 registry（进程内 TTL 清理）
- [ ] **D5 · requested_scope（必做 · A2）**：`SubtasksPlan` 增 `requested_scope`；Builder 升级「声明∩裁剪」（越界剔除+审计 · 未声明兼容现状 · MAX_SCOPE_IDS=64）；有效 scope 写 state 作签发到上界
- [ ] **D2 · 签发点（必做）**：`subtask_join` 分发路径签发 + 审批口径（只读自动 / 其余 HITL_REQUIRED 复用 hitl 回路）+ 签发序号单调 + supersede 审计 + env 密钥纪律
- [ ] **D3 · 验签门（必做）**：`_prepare_call` lookup 前插验签门（`_delegation_required` 口径）+ 六类拒绝 + 三档模式开关 + `tool_exec_node` ctx 注入令牌
- [ ] **D4 · 审计（必做）**：五类动作进 logger + span metadata（记动作不记内容 · 字段哈希化）
- [ ] **D6 · 测试与图谱（必做 · 否决面）**：SPEC §2 D6 八组断言全落 + 图谱两行备注 + HG-GRAPH-MODULES 人签新行（00 代录）+ graph-compile 绿

**竖切结论**：D1→D5→D2→D3→D4→D6 同 task 一次提交；令牌模型不配验签门 = 授权产物无强制面；不配签发审批 = 高危面裸奔；不配六类拒绝断言 = 违反「不能自证的机制等于没装」。耦合面可控（一个新模块文件 + 三处接线 + 测试/图谱），单 PR 可控。

### 非范围

承 SPEC §3（锁死 · 30 越任一条即回炉）：跨服务验签/JWT 公钥体系/网络面令牌传递（v2.0）· 用户态认证令牌 · 令牌持久化表/撤销列表服务 · 动态 StateGraph · 模型可选校验 tool · 改 freeze 契约/新 SSE 事件/新路由/新表 · HITL 三档分级体系（V1-B）· 场景维裁剪（V1-B）· 情景记忆（V1-D）· 历史文档回改。

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` 未签即 30 | **拒开工**（闸真值在本人工闸表 · 非聊天字面） | 是 | 是 |
| B1 旧测影响面未逐条处置即 30 交付 | **拒收**（闸前置 · 30 逐条执行处置并在提交说明回填） | 是 | 是 |
| 验收缺六类拒绝/篡改/重签发/三档模式/声明∩裁剪矩阵/变异检验任一 | **拒收**（防空真规则） | 是 | 是 |
| **replan 重发与一次性冲突**（SPEC FP-1） | 重发/replan 一律**重新签发新例**（新 nonce），旧例 nonce 作废 + `token_superseded` 审计；**禁续期**（续期=防重放开口子） | 是（重签发） | 否 |
| **resume 后令牌过期**（SPEC FP-2 · 墙钟 TTL） | 验签拒 R-c → 子任务失败 `ok=False` 不拖垮整图（承 v0 失败语义）→ critic/ReAct 路径重分发即重签发；HITL 挂起不延长令牌寿命（防挂起囤令牌） | 是（重签发） | 是（子任务失败终态帧 · 既有形态） |
| **进程重启丢 nonce registry**（SPEC FP-5） | resume 重放 tool_exec → nonce 无记录不误拒（重启=registry 清空=旧令牌若未过期仍可验签通过——**一次性防重放窗口=进程生命周期**，如实定性 · 跨进程防重放 v2.0）；重复执行风险由 capability 幂等键面承接（既有 `idempotency.py`） | 是 | 否 |
| **验签性能**（SPEC FP-3 · 每调用一次） | HMAC 对称 + 纯代码约束校验微秒级；禁查库禁网络；observe/enforce 均零 IO | — | 否 |
| **密钥缺失/轮换**（SPEC FP-4） | enforce 缺 `LG_RAG_DELEGATION_TOKEN_SECRET` → 拒绝签发 + 告警（安全默认拒 · 不降级为不签名）；off/observe 不需密钥；轮换=重启（kid 预留） | 是（配密钥重启） | 是（委派不可用 · 告警） |
| **observe 期误判**（SPEC FP-6 · 合法调用被标 would_block） | observe 不拦 + 台账可复盘；进 enforce 前须观察期报告 | 是 | 否 |
| **畸形 requested_scope**（SPEC FP-7） | Builder 交集收敛；上限 64 截断+审计；越界剔除留痕；非 list → None 视同未声明（承 subtasks cap 外宽容纪律） | 是 | 否 |
| **模型伪造 scope/令牌**（Host 权威面） | 令牌签名密钥进程内 · 模型不可见；requested_scope 只收窄不放宽；主体绑定取自 ctx 非模型产出 | — | 否 |
| **签发审批误判写能力为只读** | `side_effect` 来自 manifest 声明（Host 侧真值 · 非模型产出）；manifest 谎报属 capability 既有治理面（非本 task 面 · 承 H 契约硬化轨） | — | 否 |

---

## 验收标准

- [ ] 人工闸：HG-AUDIT-R1 approved 后方可勾选下列码项（HG-GRAPH-MODULES 模块表已建置 approved · 图谱新签义务随 30 交付落盘 00 代录；**若 30 偏离预判（新模块/新表/新 SSE 事件/新路由/freeze 变更）→ 回炉补闸条款生效**）

### D1 · 令牌模型（映射 SPEC §6-1/4）

- [ ] `DelegationToken` frozen dataclass 落 `capability/delegation.py`；六字段 + token_id/version/kid/issued_at/expires_at/nonce 齐全
- [ ] 篡改断言：改 `capability_set`/`expires_at`/`subject_binding` 任一字段 → 验签必拒（**缺本条则「验签通过」是假通过**）
- [ ] 参数约束：enum/max_len/pattern 三态断言；未知约束类型 → 拒绝签发断言
- [ ] 令牌可序列化/反序列化 round-trip（checkpoint 形态）断言

### D2 · 签发点 + 审批（映射 SPEC §6-3）

- [ ] 只读委派（side_effect none/read · scope 内 · 非沙箱 cli）→ 自动签发 + `token_issued` 台账断言
- [ ] 写能力/越界/沙箱类委派 → `token_issue_hitl_required` 台账断言（审批留痕可查）
- [ ] 同 subtask 重签发 → 新例生效 + 旧 nonce 验签拒 R-d + `token_superseded` 审计断言
- [ ] enforce 缺密钥 → 拒绝签发 + 告警断言

### D3 · 验签门（映射 SPEC §6-1/2/5）

- [ ] 六类拒绝断言：R-a 无令牌 · R-b 越集 · R-c 过期 · R-d 重用 · R-e 参数越约束 · R-f 主体不符——全部 `ok=False` 不抛异常 · 不落回执
- [ ] 全链路携令牌断言：supervisor 分发 → tool_exec 携令牌 → capability 验签通过（fake adapter）
- [ ] 三档模式：`off` = 现状零 diff（既有用例零改动全绿即证）；`observe` = 越权放行但 `would_block` 台账可查；`enforce` = 越权拒
- [ ] 非委派调用方（ctx 无 `_delegation_required`）零影响断言
- 注记（承 SPEC FP-3 · 不计验收计数 · R1 审查 N3）：验签朴素计时 smoke 并入新测试文件（<1ms/次量级声明 · 不设硬 CI 阈值）

### D5 · requested_scope（映射 SPEC §6-6）

- [ ] 声明∩裁剪矩阵：声明越界 id 剔除 + `scope_stripped` 审计断言；未声明 → 兼容现状断言；声明收窄生效断言
- [ ] 只收窄不放宽：声明含 allowlist 外 id → 不进入有效 scope（断言）
- [ ] MAX_SCOPE_IDS=64 截断 + 审计断言

### D6 · 图谱 / 工程（映射 SPEC §6-7/8/9）

- [ ] 零 alembic（迁移 diff 为空断言）；`docs/_tech_graph/l1/01_modules.md`：capability 行备注 + lg_rag 行备注 + HG-GRAPH-MODULES 人签新行（00 代录）；`./scripts/graph-compile.sh` 绿
- [ ] 全量 `pytest tests` 绿（基线 **1368 collected** · 2026-09-23 本帽真跑；**无既有用例删除**，新增守护用例数如实入 40 记录）；`ruff check app tests` 绿
- [ ] 生产路径 diff 白名单：`git diff master -- app/` 只含 capability/delegation.py 新增 + gateway.py 验签门 + multi（签发接线 + tool_exec 注入）+ schemas/subtasks.py + strategy/builder.py + **state.py（delegation_scope/delegation_token 两 state channel · Send 载荷必需 · 00 裁定确认白名单扩列 · 2026-09-23 留痕）** + 测试/图谱/文档
- 注记（承 SPEC §6-8/9 · 不计验收计数 · R1 审查 N4）：SSE 零新事件类型由 B1 组 6 回归 + off 零 diff 断言覆盖；PR+CI 绿+merge 由 orchestration 流程承载（承「PR 过 CI 自动 merge」先例）

### 变异检验（不验收空真规则）

- [ ] ① **签名可检**：临时验签恒真 → 六类拒绝断言必挂；恢复后全绿
- [ ] ② **一次性可检**：临时跳过 nonce 消费登记 → R-d 重用断言必挂；恢复后全绿
- [ ] ③ **审计可检**：临时去掉 `token_issued` 台账 → caplog/台账断言必挂；恢复后全绿

### 旧测影响面清单（B1 · 2026-09-23 10-task 实扫落盘）

> 扫描口径（真跑）：`ls tests/ | grep -iE 'capab|lg_rag|strategy|subtask|delegation|gateway|policy|hitl|builder|supervisor'`（命中 32 文件归并 8 组）· 命名冲突扫零命中 · 基线 1368 collected

| # | 锚点 | 本波影响 | 处置 |
|---|------|----------|------|
| 1 | `tests/test_capability_gateway.py`（闸链守护） | `_prepare_call` 前插验签门但默认 off + 仅 `_delegation_required` 口径 → 既有断言零改动全绿 | 回归（零改动） |
| 2 | `tests/test_capability_policy.py` · `test_capability_domain_allowlist.py` · `test_capability_manifest*.py` · `test_capability_visibility_and_receipts.py` · `test_capability_idempotency.py` · `test_capability_persistence_db.py` · `test_capability_http_adapter.py` · `test_capability_harness_cli.py` · `test_capability_lookups.py` · `test_capability_task_writer.py` · `test_admin_capability_observability.py` | capability 面守护；本波新增 delegation.py 纯函数 + 闸门默认 off → 语义零改动 | 回归（零改动） |
| 3 | `tests/test_lg_rag_multi.py` · `test_supervisor_parallel_join.py` · `test_supervisor_budget.py` · `test_lg_rag_supervisor_capability_catalog.py` | supervisor/subtask_join 守护；签发接线默认 off → 分发行为零 diff | 回归（零改动） |
| 4 | `tests/test_strategy_builder.py` | Builder allowlist 守护；`requested_scope` 未声明=现状兼容路径须守护既有断言行 | 回归（零改动 · 未声明兼容断言新增） |
| 5 | `tests/test_hitl*.py`（3 文件）· `test_lg_rag_sse_hitl.py` | HITL 回路守护；签发审批复用既有回路零改动 | 回归（零改动） |
| 6 | `tests/test_lg_rag_sse_*.py`（5 文件）· `test_lg_rag_http.py` · `test_lg_rag_basic.py` · `test_lg_rag_router.py` · `test_lg_rag_retry.py` · `test_lg_rag_session_continuity.py` · `test_lg_rag_structured_output_p2.py` | SSE/HTTP freeze 守护；零新事件类型零契约改 | 回归（零改动） |
| 7 | 新增义务：`tests/test_capability_delegation.py`（令牌模型/签名/六类拒绝/参数约束/篡改/序列化）+ `tests/test_lg_rag_delegation_wiring.py`（签发接线/审批双路径/全链路携令牌/replan 重签发/三档模式/scope 矩阵/变异检验三条） | — | 新增（用例数如实入 40 记录） |
| 8 | alembic 链 | 本波**无迁移义务**（零新表零列 · SPEC §3 锁死） | 无（迁移 diff 为空断言入 D6） |

> 分组注记（R1 审查 N5）：`test_lg_rag_sse_hitl.py` 在组 5/组 6 双计（glob 交叠 · 处置同为回归零改动 · 并集覆盖全 32 文件无缺漏）。

---

## 依赖

| 依赖 | 说明 |
|------|------|
| SPEC | `docs/spec/host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md`（signed · HG-SPEC-SIGNOFF=approved 2026-09-23 00 代录 · Q1/Q2/Q3 裁定锁死） |
| 规划/种子 | `docs/spec/agent-infra/07_host_v1_landing_plan_v0.md`（signed）· `08_host_v1_wave_spec_outlines_v0.md` §1（signed） |
| 启动 invoke | `docs/harness/invokes/by-task/host-v1-landing/invoke_20260923_00_host-v1-landing.md`（维护者令原话 · 授权面） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 图谱 | `docs/_tech_graph/l1/01_modules.md`（2026-09-23 真读核验 · capability/lg_rag 行 · 签录链完整至主线裁定行） |
| 改造对象 | `app/ops/capability/delegation.py`（新增）· `gateway.py::_prepare_call`（:258 前插验签门）· `lg_rag/multi/`（graph.py :94-102 分发 · nodes.py :1050-1091 tool_exec ctx）· `lg_rag/schemas/subtasks.py`（requested_scope）· `strategy/builder.py`（声明∩裁剪） |
| 先例 · 纯函数闸 | `app/ops/lg_rag/multi/step_contract.py`（`_env_int` :33-42 · 上限纪律 :23 · 零 LLM 零 IO :15） |
| 先例 · 闸门拒执 | `app/ops/capability/gateway.py::_blocked_result`（:219-255 被拒不落回执）· errors.py 错误码词表纪律（detail 区分 · 承 :557-559） |
| 先例 · 阶段 T 租户 | `app/ops/tenant_context.py` · nodes.py :1081-1083（ctx 注入 tenant_id） |
| 先例 · HITL 回路 | `app/ops/hitl/`（interrupt/resume · `ops_hitl_requests` 留痕） |
| 测试锚点 | B1 清单 8 组（capability/lg_rag/strategy/hitl 面） |
| 格式基准 | `docs/tasks/done/task_memory_compliance_delete.md`（signed → done 五棒全通 · 本 task 格式对齐此） |

---

## 给执行帽的必读列表

1. `AGENTS.md`（新会话启动纪律 · 分支纪律 · GATE_VERIFY）
2. 本 task（钉死契约 · 闸 · 非范围 · B1）
3. SPEC `docs/spec/host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md`（§2 D1–D6 / §3 非范围 / §4 裁定 Q1–Q3 / §5 FP-1~FP-7 / §6 验收）
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
5. 代码：`app/ops/capability/gateway.py`（:219-255 `_blocked_result` · :258-385 `_prepare_call`）· `app/ops/lg_rag/multi/graph.py`（:94-102 分发）· `app/ops/lg_rag/multi/nodes.py`（:1050-1091 tool_exec ctx）· `app/ops/lg_rag/schemas/subtasks.py` · `app/ops/strategy/builder.py`（:38-59）· `app/ops/capability/policy.py` · `app/ops/lg_rag/multi/step_contract.py`（:15-50 纯函数/env 纪律）
6. 先例：`tests/test_capability_gateway.py`（闸链断言范式）· `tests/test_lg_rag_multi.py`（图节点 fake 范式）· `tests/test_strategy_builder.py`（裁剪断言范式）
7. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（30 首输出闸扫描）

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | SPEC signed（HG-SPEC-SIGNOFF=approved 2026-09-23 00 代录）；范围 D1–D6 承 SPEC §2 不重开辩论；本帽实扫复核：验签门插入位（gateway :258）· 签发点（graph :94-102）· tool_exec ctx（nodes :1050-1091）· 命名冲突零命中 · 基线 1368 | no | — | 无 |
| R1 | 开工闸：HG-TASK-DRAFT approved（00 代录 · 维护者令留痕）· HG-AUDIT-R1 **pending**（blocks 30 未放行 → **30 拒开工**）· HG-GRAPH-MODULES=approved（模块表已建置真读核验 · 图谱新签义务随 30 落盘） | no | — | 无 |
| R2 | 竖切：D1→D5→D2→D3→D4→D6 同 task 一次提交；方案对比继承 SPEC §4 三组裁定（Q1 HMAC 弃 Ed25519 · Q2 分级弃全 HITL/全自动 · Q3 不新模块弃独立模块），不重演 | no | — | 无 |
| R3 | failure_paths **12 条** = SPEC FP-1~FP-7 翻四列 + 过程三（闸未签拒开工 · B1 闸前置拒收 · 缺断言拒收）+ Host 权威面二（模型伪造 scope/令牌 · 签发审批误判归 manifest 治理面）（R1 审查 N2 计数修正）；一次性防重放窗口=进程生命周期如实定性（FP-5 不虚假承诺跨重启防重放）；审批误判风险归 manifest 治理面如实划出 | no | — | ① 进程重启后一次性防重放窗口丢失（FP-5 · 幂等键面承接）② observe→enforce 灰度依赖观察期报告质量 |
| R4 | 验收 **19 条**全否定性断言化逐块映射 SPEC §6（人工闸 1 / D1×4 / D2×4 / D3×4 / D5×3 / D6×3）；变异检验三条（签名/一次性/审计可检）；B1 实扫 8 组处置三态齐全（回归×6 · 新增×1 · 迁移无×1） | no | — | 无 |
| R5 | 可交 20-task-audit；与 SPEC 实质差异为零（锚点行号/B1/基线数/闸行留痕均为过程化落地）；HG-AUDIT-R1 落稿时待签 | no | — | 见 R3 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：见 R3/R5

### R0 · 问题框定

SPEC 已签收（Q1 HMAC-SHA256 + Q2 只读自动·其余 HITL + Q3 不新增一级模块锁死），本 task 只做可执行化拆解：委派无授权产物（SPEC §1 实扫锁死 · 本帽复核 gateway :258 闸链与 graph :94-102 分发一致）。当前分支 master——**30 阶段必须切 `task/host-v1-delegation-token`**（钉死契约已载 · 00 委派子 Agent 时验分支）。

### R1 · 开工闸

HG-TASK-DRAFT approved（00 代录 · 维护者令原话留痕闸表）；HG-AUDIT-R1 **pending**（10 帽不签 · blocks 30 未放行 → **30 拒开工**）；HG-GRAPH-MODULES **真读** `01_modules.md` 核验：模块表已建置（bootstrap 签 2026-07-16 · 签录链完整至 2026-09-23 主线裁定行）；capability/lg_rag 行在表；Q3 裁定不新增一级模块 → 图谱义务=两行备注+人签新行随 30 落盘。

### R2 · 竖切

D1–D6 是不可拆语义单元：令牌模型不配验签门 = 授权产物无强制面；不配签发审批 = 高危面裸奔（大纲 A1「签发本身是高危操作」）；不配六类拒绝断言 = 违反「不能自证的机制等于没装」。实现序：D1 令牌模型（纯函数底座）→ D5 requested_scope（签发上界输入）→ D2 签发点 → D3 验签门 → D4 审计 → D6 断言收口。

### R3 · 失败语义

SPEC §5 七条失败面全收并翻四列，加过程三条与 Host 权威面两条（模型伪造 · 审批误判）共十二条。最锋利边界 = 一次性 vs replan/resume：裁定「重签发禁续期」（FP-1）——续期等于防重放开口子；进程重启丢 nonce registry 的残余如实定性（FP-5：防重放窗口=进程生命周期 · 重复执行由 capability 幂等键面承接 · 跨进程防重放 v2.0），不虚假承诺。

### R4 · 可测性

验收 19 条全部可执行断言：篡改必失效（缺此条则验签通过是假通过）· 六类拒绝逐类 · 重签发 nonce 作废 · 三档模式（off 零 diff 由既有 1368 用例零改动全绿证明）· 声明∩裁剪矩阵 · 变异检验三条（签名/一次性/审计各配一条「临时破坏→断言必挂」）。B1 八组实扫落盘：回归×6（默认 off + `_delegation_required` 口径双保险）· 新增×1（两个新测试文件）· 迁移无×1。

### R5 · 交付判定

可交 20-task-audit：与 SPEC 实质差异为零（锚点行号复核 / B1 实扫 / 基线 1368 真跑 / 闸行留痕均为过程化落地，无范围/验收/非范围语义偏移）；HG-AUDIT-R1 落稿时待签；残余风险两条承 R3 如实携带（进程重启防重放窗口 · 灰度观察期报告质量）。

### 自检结论

本稿：范围/非范围/验收/failure_paths 逐块映射 SPEC（§2→范围 D1–D6 · §3→非范围 · §5→failure_paths+过程三 · §6→验收 19 条）；钉死契约自 SPEC §2/§4/§5 锁死不重开辩论；B1 实扫 8 组处置三态齐全；闸表四行（HG-TASK-DRAFT 00 代录 approved · HG-AUDIT-R1 pending blocks 30 · HG-GRAPH-MODULES approved 真读核验 · PILOT n/a）；思考轮 R0–R5 回填齐全无跳轮。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-09-23 | 10-task 落稿（SPEC signed 后 · 00 亲起 · 承 harness-00-delegate-only「无初稿时起草第一步」例外）：锚点逐个复核（gateway :258 · graph :94-102 · nodes :1050-1091 · subtasks schema · builder :38-59）· 命名冲突扫零命中 · pytest 基线 1368 真跑 · B1 八组落盘 · HG-TASK-DRAFT 00 代录 approved（维护者令原话留痕）· HG-AUDIT-R1 pending 待 20-task-audit |
| 2026-09-23 | **40 核验（00 独立复核）**：全量 pytest 1420 collected（+52 新增 · 零既有删除）· 1267 passed / 11 failed / 142 skipped——**11 红全部实证为基线环境性**（本地 PG 5432 未起 · master+同 .env worktree 复跑同 8+3 全挂 · 与本 diff 无关）；ruff 改动文件 7 errors 与 master 同数（净增 0 · 新增三文件全绿）；`graph-compile.sh` 绿；alembic diff 为空；**state.py 白名单偏离确认**（Send 载荷必须是 state channel · 最小必需增量 · 钉死契约无改义） |
| 2026-09-23 | 20-task-audit R1 **PASS-WITH-NITS**（零阻塞 · 审查文 `docs/harness/reviews/task_host_v1_delegation_token_audit_R1_20260923.md` · 子 Agent 执行）；N1–N5 微修留痕：N1 先例行号修正（result_contract.py:23/:44/:61-62 + errors.py:102-103）· N2 failure_paths 计数 10→12（7+3+2 点名额外面）· N3 计时 smoke 注记（不计验收计数）· N4 SPEC §6-8/9 映射显式化注记 · N5 B1 组 5/6 双计去重注记；**00 代录 HG-AUDIT-R1=approved**（维护者令原话+日期留痕 · 本窗追认令「授权00可以签收所有过程文档」）· 30 可委派开工（分支 `task/host-v1-delegation-token`） |
