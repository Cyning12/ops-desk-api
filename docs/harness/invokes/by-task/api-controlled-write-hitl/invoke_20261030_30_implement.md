# invoke · 30 实现（阶段 W：api 受控写 + HITL）

| 项 | 值 |
|---|---|
| hat | 30（实现帽） |
| task_slug | api-controlled-write-hitl |
| task 文件 | `docs/tasks/active/task_api_controlled_write_hitl.md` |
| 分支 | `task/api-controlled-write-hitl-w0`（起点 = master merge 6f30889 · 干净零残留） |
| 指令来源 | 棒次参数（00 委派 · 2026-10-30）+ task 真值 |
| 前序 invoke | `invoke_20261030_10_task_draft.md` · `invoke_20261030_20_task_audit.md` |

## GATE_VERIFY（开工前 · 2026-10-30 21:13 +08:00）

| human_gate_id | status | blocks_30 | 判定 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 20-R1, 30 | ✅ |
| HG-AUDIT-R1 | approved | 30 | ✅ 可 30 |
| HG-GRAPH-MODULES | approved | 30 | ✅ 可 30 |
| HG-STAGE-W-DESIGN | approved | 30 | ✅ 可 30 |

- `npx spec-wave verify --target . --task docs/tasks/active/task_api_controlled_write_hitl.md` → `VERIFY: PASS`（exit=0）。
- 真值以 task 人工闸表为准（2026-10-30 维护者签 · 00 代录 · 四闸齐）。

## 改动文件清单

| 文件 | 性质 | 说明 |
|---|---|---|
| `app/ops/lg_rag/multi/nodes.py` | 改（唯一 app 改动 · +234/-62） | 写执行审批闸 + 匹配核心抽取 + D2 回填扩类 + payload write_intent |
| `tests/test_write_approval_gate.py` | 新增（11 测） | W0–W3 红测先行 + 红线负样本 + 单路径钉死 |
| `docs/_tech_graph/l1/01_modules.md` | 改（W5 薄增量 · 4 处） | capability / lg_rag / hitl 行备注 + HG-GRAPH-MODULES 台账 1 行 |
| 本 invoke | 新增 | 30 过程记录 |

零改动确认：`app/ops/hitl/**` · `app/ops/capability/gateway.py` · `app/ops/capability/policy.py` · SSE/事件发射面 · manifest（testing.write.echo PR #209 已就位）· alembic（零迁移零扩表）。

## 设计要点（对棒次口径的落法）

1. **闸位 = 编排层 `tool_exec_node`**（镜像委派签发 HITL 拦挂回路先例 · capability/hitl 包零 IO 纪律不破）。`side_effect ∈ WRITE_SIDE_EFFECTS` 且无新鲜 approved 单据 → blocked terminal（`blocked_by=capability_write_hitl_required` + `hitl_required` + `tenant_id` + `write_intent`）→ 复用 `_persist_hitl` → `interrupt()`（既有 `hitl.waiting` 形态 · SSE 零新事件类型）。闸在 subtask.running 帧之前（未跑一步不发 running）。
2. **两道闸正交（fail-closed 钉死）**：`OPS_CAPABILITY_ALLOW_WRITE`/`_host_policy.allow_write` 只过 Policy 写闸，**不豁免** HITL 审批闸；反之审批命中后由编排层注入 `cap_ctx["_host_policy"]={"allow_write": True}`（复用 Host 单次放行既有语义「只对这一次调用有效」）过 Policy 闸。负样本 W0②：env=1 无审批仍拦。
3. **审批消费 = 单实现三调用点**：`_match_fresh_approved` 匹配核心抽取（`_approval_consumed` / `_approved_fresh_for_subtask` / 新 `_write_execution_approval` 共用，禁第二份匹配实现）。写闸收 `capability_write_hitl_required` + `delegation_issue_hitl_required` 两类单据（委派签发审批同为「人已知情写意图」的批准 · TA3/TB5 零破坏）；委派门 `_approval_consumed` 本身仍只收委派类（既有语义不动）。
4. **W2 tenant_scope**：capability_write 类单据 `tenant_id` 缺失或与当前租户不一致 → fail-closed 不消费（跨租户写对外 404/不执行）；委派类维持三元组语义不动（M1 保留面）。新拦单 terminal 显式带 `tenant_id`（修 `_error_terminal` 不含租户的空洞，仅限新类）。
5. **W3 span 串链**：命中注入 `cap_ctx["approval_id"]` → `gateway.py:1318` 预留读 `ctx["approval_id"]` 落 span（gateway 零改动 · 预留启用）；nodes 侧台账 `capability_write_approval_consumed`（logger + span · 记动作不记内容）。
6. **W1 单路径接合**：decide/resume/auto_resume 零改动；源码钉死测试断言 `_execute_decided_resume` 在 `router.py` 唯一定义且 `auto_resume.py` 同源惰性 import 复用（禁第二条 resume 实现）。
7. **不扩 hitl 表结构**：`write_intent`（{capability_id, tenant_id, args_summary 脱敏截断, idempotency_key 模板}）落既有 `payload` jsonb 键；D2 空 unlock 回填守卫由 `== delegation_issue` 扩为 `∈ {delegation_issue, capability_write}`（resume 不 409）；`_approved_fresh_for_subtask` 去重守卫同步扩类。

## 红测 → 绿 过程

- **红**（实现前）：`test_w0_write_blocked_without_approval` 失败 —— 旧行为 `policy_blocked: write_not_confirmed` error terminal（无 HITL 挂起 · adapter 被 Policy 拦但无审批单），确认闸缺位。
- **绿**：实现后 `pytest tests/test_write_approval_gate.py` **11/11 通过**（0.19s）。
- **全量对拍**：干净树（git stash）基线 27 failed ≡ 带改动 27 failed（`IDENTICAL_FAILURE_SETS`）；12 个受影响文件子集对拍亦恒等（21≡21）。27 个预存失败根因 = 仓根 `.env`（`OPS_CAPABILITY_ALLOW_WRITE` :85 / `LG_RAG_SUPERVISOR_PLAN_ON_FAIL` :86 等被 conftest 载入 os.environ）+ DB 依赖项（`test_multi_replica_dualproc`）——环境性，与本次改动无关（CI 无该 .env）。**本次改动零新增失败、零既有绿测转红。**
- decide 400/404/409/422 回归：`test_hitl_pending_decide.py` 等全部在两边失败集之外（绿）。

## M1 影响面表（`side_effect=write/irreversible` 调用与断言面逐条）

| 面 | 触及方式 | 处理 | 依据 |
|---|---|---|---|
| `tests/test_capability_testing_write.py`（16 处 · A4④ enforce 集成链 / A6 字段钉死 / A8 loader 文案 / A5 罐头零 IO） | 不经 tool_exec 或止于 join 拦截断言 | **保留**（全绿 · 零改动） | A4④ 不调 tool_exec；A6 直调 invoke 无 allow_write → policy_blocked 不变 |
| `tests/test_hitl_approval_consumption.py` TA3(:483)/TB5(:935)（全仓仅有两例经 tool_exec 真执行写能力） | 先造 `delegation_issue` 类 approved 单据 + env | **保留**（全绿 · 新闸接受 delegation_issue 类审批 → 消费命中放行） | 三元组匹配语义不动 |
| 同文件 TA4(:495-525)（有令牌无 Host 写放行 → write_not_confirmed） | 直调 `capability_ainvoke` 不过 tool_exec | **保留**（不受影响） | gateway Policy 闸零改动 |
| `tests/test_lg_rag_delegation_wiring.py`（WRITE_CAP 1 处） | WRITE_CAP 仅 `_join_subtasks` 拦截断言；tool_exec 执行全用 READ_CAP | **保留**（全绿） | — |
| `tests/test_strategy_env_extra_candidates.py`（6 处）· `test_capability_visibility_and_receipts.py`（4）· `test_capability_http_adapter.py`（5）· `test_admin_capability_observability.py`（2）· `test_capability_manifest_http.py`（2）· `test_capability_domain_allowlist.py`（2）· `test_capability_reversibility.py`（1 · irreversible） | 全为 gateway/Policy/manifest 层直调断言 | **保留**（失败集与基线恒等 · 其中预存失败系本地 `.env` 环境性，非本次引入） | 层内零改动 |
| app 侧判序面（`policy.py` 写闸 :102-103 · `registry.py` deny_write :120-121 · `types.py` WRITE_SIDE_EFFECTS · `baseline.py`） | 读侧引用 | **保留**（零改动） | 唯一挂钩点纪律不动 |
| 新增 `tests/test_write_approval_gate.py` | 新断言面 | **负样本化钉死**：W0② env-only 无审批仍拦 · W2 跨租户/缺租户不消费 ×3 · W1 rejected 零执行 · 单路径源码钉死 | 红线「无审批直接写 = fail-closed」 |

**行为变化声明（M1 实测「温和」确认）**：lg_rag 编排面 `tool_exec` 对 write 类 capability 的行为由「无 Host 写放行 → `policy_blocked` error terminal」变为「无新鲜 approved 审批 → HITL 挂起拦单」。实扫全仓仅 TA3/TB5 两例经 tool_exec 执行写能力且均有 approved 单据 → 零破坏（全量失败集对拍恒等佐证）。

## 图谱增量（W5 · G-L1 薄备注）

`docs/_tech_graph/l1/01_modules.md` 4 处：`lg_rag` 行（闸 + `_match_fresh_approved` 抽取 + D2 扩类 + write_intent）· `capability` 行（两道闸正交 + Host 单次放行注入 + span approval_id 预留启用 · gateway 零改动）· `hitl` 行（decide/resume 零 diff + 单路径钉死 + tenant_id 全链带）· HG-GRAPH-MODULES 台账 1 行（承 :130 先例）。**不新增一级模块 · 零新跨模块边 · 不增 implementedBy · 零新路由/表/SSE 事件类型/迁移。** `./scripts/graph-compile.sh` 绿。

## 质量门

| 门 | 结果 |
|---|---|
| `ruff check app tests` | ✅ All checks passed |
| `pytest tests` | ✅ 零回归（基线对拍恒等 · 新测 11/11 绿；27 预存环境性失败见上） |
| import-linter（`.importlinter`） | ✅ 12 kept, 0 broken |
| `./scripts/graph-compile.sh` | ✅ OK |
| SSE 事件表零 diff | ✅ app diff 仅 `nodes.py`（事件发射面零改动）+ 挂起载荷形态测试钉死 |
| spec-wave verify / task lint | ✅ VERIFY: PASS |

## 未决风险

1. **本地 `.env` 27 个预存失败本机不可全绿**：根因为开发者机器 `.env` 注入 `OPS_CAPABILITY_ALLOW_WRITE` 等；本交付以「干净树基线 ≡ 带改动」双重对拍（全量 + 12 文件子集）证明零回归，CI（无该 .env）预期全绿，建议维护者以 CI 为准。
2. **非编排直调面不过审批闸**：直接 `gateway.invoke/ainvoke` 写能力仍只受 Policy 写闸约束（既有设计边界 · 审批闸在编排层，镜像委派消费门分层纪律）；如需覆盖属阶段 P 平台项（task 非范围）。
3. **`write_intent.args_summary` 为脱敏摘要**（secret/token 等键打 `***` · 超长 sha256 截断），审计取完整参数走 span/receipt 既有通道。
