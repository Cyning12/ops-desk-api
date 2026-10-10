# Task：hitl-approval-consumption-loop（T1 · D1 审批消费门 + D2 unlock 空形态回填 + D4 台账/测试 · 批准→放行消费成环核心）

> **状态**：`draft`  
> **类型**：**SPEC 承接**（SPEC v1 · HG-SPEC-SIGNOFF=approved 2026-10-10）  
> **依据**：`docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md`（**SPEC 文档当前在 `spec/hitl-approval-consumption` 分支 · 随首个实现 PR 一并带入 master** · 本文引用即该仓内路径）——本 task 承接 D1（审批消费门）+ D2（unlock 空形态回填）+ D4（对应台账/测试）· Q1/Q2/Q3/Q5 · FP-1~FP-7 · A1/A2/A3/A5/A6/A7/A8  
> **分支**：`task/hitl-approval-consumption-loop`（base：`master` 4d905e0 · 禁止 master 直改）  
> **拆分**：T1（本）→ T2 `task_hitl_approval_consumption_auto_resume.md`（**依赖本 task merge**）；T3 `task_hitl_approval_consumption_strategy_env.md`（无依赖可插队）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `hitl-approval-consumption-loop` |
| **git_branch** | `task/hitl-approval-consumption-loop` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | pytest 单测/集成为主：消费命中放行断言 + 边界否定变异式（pending/rejected/超 TTL/三元组不匹配/缺 capability_id 旧单据/store 读异常 · **InMemory+Db 双 store 各一组 TTL 归一断言**）+ 单子任务 resume 成环机制段（decide→resume 200→done{completed}）+ off 零触达 spy 断言 + 反回归对拍（deny 判序/Policy 闸 diff 空）；live HTTP/SSE 全链（三 env 组 · 无 shim）留 40 复跑 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1`（行备注 · 不新增一级模块） |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` lg_rag / hitl / capability 三行在册备注 |
| **graph_delta_note** | 模块边界不变：消费门落 lg_rag 编排层（nodes.py async 化）+ hitl 模块消费助手/payload jsonb 增键 + capability 包零 IO 零 diff 确认备注 → G-L1 行备注同步，HG-GRAPH-MODULES 随 30 回写由 00 代录 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | SPEC 承接 task · 机制接线增量无 wiki 条目变更 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20 R1 → 维护者签 → 30 → 40 → PR+CI 绿 → 图谱回写 → CLOSE |
| **freeze_id** | 无（零新表/零新列 · payload jsonb 增键 · 零新 SSE 事件类型 · 零 alembic） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 维护者签 · 00 代录 2026-10-10（授权「授权00签收所有过程文档」） · lint PASS |
| HG-AUDIT-R1 | **approved** | 30 | 维护者签 · 00 代录 2026-10-10（授权「授权00签收所有过程文档」） · 依据 R1 审查 FAIL→修复→增量复核 PASS（reviews/task_hitl_approval_consumption_loop_audit_R1_20261010.md · commit 45fec13 · 残留 NIT 计数口径已顺手回改） |
| HG-GRAPH-MODULES | **approved** | 30 | 维护者签「在册」（capability/lg_rag/hitl 行备注段）· 00 代录 2026-10-10 · 30 回写义务在案 |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | 非物理分层试点 task |

---

## 背景与目标

SPEC v1 §1 两实证缺口（均已在 master `4d905e0` 复核成立）：

- **缺口 1 · 批准→放行半环断**：delegation 签发审批的自动放行判定 `auto_approve_ok`（`app/ops/capability/delegation.py:488-514`）与其调用方 `_delegation_issue_block_reason`（`app/ops/lg_rag/multi/nodes.py:277-295`）**只读 Host 侧注册表真值，不读任何 HITL 审批记录**。后果：`decide(approved)` persisted=true 之后，重下发同 tool 仍再拦 → 再挂起 → 循环（30 invoke :52-61 探针实证 re-blocked）。
- **缺口 2 · 单子任务计划 resume 409**：`_persist_hitl`（nodes.py:1397-1471）算 `unlock_subtask_id` 只取 `depends_on ∩ plan_prefix_ids`（:1440-1445）；单子任务计划算出空串，批准后 `app/ops/hitl/router.py:404-411` 抛 409「已批准但拿不到待解锁的步骤」——live run `0eb059a5…` 409 detail 逐字一致实证。

**一句话目标**：把 delegation HITL 的「批准」接成**可消费的授权**——签发判定在裁定拦截前先消费匹配的 approved 单据（D1 · 三元组消费键 + TTL 读时判过期 + fail-closed）；单子任务形态的批准拿得到解锁目标、resume 走通到 `done{completed}`（D2 · unlock=被拦 sid 自身 + 形态守卫）；配套台账与逐条断言化测试（D4 本 task 面）。

---

## 现状锚点（只读 · 30 必读 · 10 已逐行实读 · base `4d905e0`）

| 锚点 | 实证 |
|------|------|
| `app/ops/lg_rag/multi/nodes.py:277-295` | `_delegation_issue_block_reason` **sync 纯判定**：tool 空/∉scope → None（不走 HITL）；未注册 → 安全默认交人；`auto_approve_ok` False → `委派签发需人工审批（{why}）`。**不读任何 HITL 记录** |
| `app/ops/lg_rag/multi/nodes.py:644` + `graph.py:94` | `_join_subtasks` 为 **sync 节点**（`builder.add_node("subtask_join", _join_subtasks)`）；delegation 拦截段在 :708-726（`blocked_by="delegation_issue_hitl_required"` + `hitl_required=True` + `AUDIT_TOKEN_ISSUE_HITL_REQUIRED` 审计 :721-725） |
| `app/ops/lg_rag/multi/nodes.py:1397-1471` | `_persist_hitl`：:1440-1445 unlock 只取 `depends_on ∩ plan_prefix_ids`（单子任务 → 空串）；:1446-1460 申请行组装；**:1457 payload 仅 `{"observation": …}`**（D1 在此 jsonb 增记 `capability_id` · 零迁移） |
| `app/ops/lg_rag/multi/nodes.py:341-354` | `_error_terminal` **保留 `tool` 字段**（:352-353）→ `_persist_hitl` 内 `term.get("tool")` 即 capability_id 真源 |
| `app/ops/lg_rag/multi/nodes.py:550-567` | `_locked_prefix`：`hitl_unlocked_ids` 摘除不可变前缀（:562 · 「批准的唯一效果」）——resume 成环既有机制，本 task 不动 |
| `app/ops/capability/delegation.py:488-514` | `auto_approve_ok` 纯函数三条件（scope ⊆ / 全只读 / 无 sandbox·cli）· **保持纯函数零 IO 一行不改**（SPEC Q2） |
| `app/ops/capability/delegation.py:105-107` | `_env_int(ENV, default, low=1, high=86400)` 先例——TTL env 解析同形态 |
| `app/ops/hitl/store.py:83-99` | InMemory `adecide`：`decided_at = time.time()`（:98 · **float**）；只受理 pending（:93-94） |
| `app/ops/hitl/store.py:159-163,249` | Db `_DECIDE`：`decided_at = now()`（:161 · SQL 层 timestamptz）；**R1-N1 锚点精度**：消费端经 `alist/aget` 实收的是 `_row_to_dict` 输出（:249 · **ISO 8601 字符串**，非 datetime 对象）——SPEC 表述「Db store 为 datetime」指 SQL 层，归一函数输入类型按 **float \| ISO str** 钉 |
| `app/ops/hitl/router.py:287-316` | `_collect_decisions` 同批已决汇总（approved→unlock_subtask_id / rejected→subtask_id）· 本 task 不动 |
| `app/ops/hitl/router.py:404-411` | 409 守卫「已批准但拿不到待解锁的步骤」**保留一行不动**（D2 让该形态不再产生空 unlock，而非放宽 409） |
| `app/ops/hitl/persistence.py:61-77` | `get_hitl_store`/`set_hitl_store`/`reset_hitl_store`——测试隔离与 store 预置面 |
| `pyproject.toml:76` | `asyncio_mode = "auto"`——sync 直调测试改 `async def` 后自动接管，无需逐枚装饰器 |
| **R1-N2 扩面实证**（10 实测 · 超 SPEC 估面） | SPEC Q2 S1 估「波及面仅 nodes.py:711 + test_capability_testing_write.py:492」；实测 `_join_subtasks`（sync）sync 直调另有 **14 处**（含 `_delegation_issue_block_reason` 直调 1 处另计）：`tests/test_step_contract.py:259,275,294,306,323,756,769`（7 处）· `tests/test_lg_rag_delegation_wiring.py:159,170,187`（3 处）· `tests/test_capability_testing_write.py:433`（1 处 · :492 直调 `_delegation_issue_block_reason` 另计）· `tests/eval/test_capability_redlines.py:1715`（1 处 · **默认跑** · 无 marker 排除）· `scripts/acceptance/capability_step_contract_gate.py:152`（1 处 · `async def _drive` 内 sync 直调 · 被 `capability_acceptance.sh:165` 真跑）。裁定见钉死契约「async 化裁定」行 |

---

## 钉死契约（30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **消费点** | `_delegation_issue_block_reason`（nodes.py:277-295）：`auto_approve_ok` 判出需审批后、返回 HITL 原因前，先查 HITL store 有无匹配 approved 单据；命中 → 返回 `None`（放行签发）+ 台账 `delegation_approval_consumed`；未命中/异常 → 维持拦截（**fail-closed**） |
| **消费键（Q1）** | `(run_id, subtask_id, capability_id)` 三元组精确匹配。`capability_id` 由 `_persist_hitl` 落库时 `payload`（jsonb）增记（取 `term.get("tool")` · nodes.py:352-353 真源 · 零迁移）；**旧单据缺该键 → 不消费**（fail-closed，不得视作匹配） |
| **时效（Q5 + R1-N3）** | `decided_at + TTL < now` → 不消费（读时判过期 · **不写回单据状态**）。env `OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS` 默认 3600，**合法域 [1, 86400]**（承 delegation.py:107 `_env_int` 先例），非法/越界回退默认。授权效力 = 读取时刻的活状态，非缓存快照 |
| **decided_at 归一（R1-N1）** | 消费端输入类型 = **float（InMemory :98）| ISO 8601 str（Db `_row_to_dict` :249）**；归一为可比时间戳后再做 TTL 比较；归一函数落消费助手内；**InMemory + Db 双 store 各一组 TTL 断言**（缺 str 分支 = 未履约） |
| **单据类型守卫** | 仅消费 `blocked_by=delegation_issue_hitl_required` 类单据；`prefix_touch_required` 语义一行不动 |
| **async 化裁定（R1-N2 扩面 · 10 裁定留 20 复核）** | **甲案（选定）**：`_delegation_issue_block_reason` → `async`（函数内先做 sync 纯判定，判出需审批后再 async 消费读）；`_join_subtasks` → `async` 节点（LangGraph `add_node` 原生兼容 async 节点函数 · graph.py:94 注册行零改动）；全部 sync 直调点随改（测试点 `async def` 化 · `asyncio_mode=auto` 自动接管；`scripts/acceptance/capability_step_contract_gate.py:152` 补 `await` · 清单见 B1 表 14 处）。**否乙案**（sync 核心 + 外层 async 包装节点事后修补：须摘除已落 blocked 终态、回卷 `blocked_meta` 计数与已发出的 `AUDIT_TOKEN_ISSUE_HITL_REQUIRED` 审计 · 双写面风险大于测试改动面）；**否丙案**（sync-over-async 桥：违反 P-13 异步一致性与 store「只有异步接口」纪律，store.py:1-10 模块 docstring 明示） |
| **`auto_approve_ok` 零 IO** | 纯函数逐字节零 diff；消费读写在 nodes.py 编排层 async 助手，**不进 capability 包**（Q2）；capability 包 import 面零变化 |
| **unlock 回填形态守卫（Q3）** | `_persist_hitl`（:1440-1445）：当 `depends_on ∩ plan_prefix_ids` 为空 **且** `blocked_by=delegation_issue_hitl_required` → `unlock_subtask_id = 被拦 sid 自身`（批准=授权（重）下发该被拦步骤 · 与 D1 消费配对成环）；`prefix_touch_required` 类空 unlock **维持现状**（router 409 保留 · 人可解的明确报错 · 不静默放行） |
| **409 守卫保留** | `router.py:404-411` 一行不动；验收含「prefix_touch 空 unlock 仍 409」保留断言 |
| **off/observe 零 diff（FP-7）** | `LG_RAG_DELEGATION_TOKEN_MODE=off` → 消费代码路径零触达（无 store 读 · 无新台账）；observe 本就不拦 → 不记假台账；仅 enforce 下改变判定 |
| **deny 判序 / Policy 写闸不动** | `registry.py::_match_filter`（:112-140 · `deny_high_risk` 在 `deny_write` 前）函数体逐字节零 diff；`policy.py:96-105` 闸序零 diff；审批消费**只作用于 delegation 签发判定**，不豁免 gateway/Policy 任何一层；`test_allow_tags_does_not_waive_deny_write` 原样绿 |
| **台账纪律** | 新增动作 `delegation_approval_consumed`（命中 · logger + span metadata）与消费读取失败 warning；只记 request_id/subtask_id/capability_id/decision_by/TTL 余量，**不记参数原值**（记动作不记内容） |
| **resume 成环路径（D2 配套 · 既有机制复用零改）** | approved=[sid] → `hitl_unlocked_ids=[sid]` → `_locked_prefix`（:550-567）摘除 → replan/carry 重下发 sid → D1 消费放行 → 令牌签发 → 执行 → `done{completed}` |

---

## 范围

- [ ] **F1 · payload 增记 capability_id**：`_persist_hitl`（nodes.py:1446-1460）申请行 `payload` jsonb 增记 `capability_id`（取 `term.get("tool")` · 缺省空串不落键或落空串由 30 定并留痕 · 消费端缺键 fail-closed 语义不变）；零迁移 · 既有读取兼容
- [ ] **F2 · 消费助手（async）**：nodes.py 编排层新增 async 消费判定（store 读 → `blocked_by` 守卫 → 三元组匹配 → decided_at 归一 → TTL 判过期 → 命中返回放行 + `delegation_approval_consumed` 台账；异常 → warning + 维持拦截）；TTL env 解析承 `_env_int` low/high 先例
- [ ] **F3 · async 化波及面随改**：`_delegation_issue_block_reason` 与 `_join_subtasks` async 化；B1 表 14 处 sync 直调点全部随改（测试点 `async def` 化 · scripts 门禁脚本补 `await`；含 `test_capability_testing_write.py:488-493`「设计真态钉死」段语义改写 · 见 B1）
- [ ] **F4 · unlock 空形态回填**：`_persist_hitl` :1440-1445 增形态守卫回填（仅 delegation_issue 类 · unlock=被拦 sid 自身）
- [ ] **F5 · 测试**：验收 TA1–TA7 逐条断言化（新增消费/回填用例 + B1 旧测全绿亲跑）
- [ ] **F6 · 图谱同步**：`docs/_tech_graph/l1/01_modules.md` lg_rag / hitl / capability 三行在册备注回写（G-L1 · HG-GRAPH-MODULES 随 30 回写由 00 代录）

### 非范围

- ❌ **D5 批准后自动继续全量**（触发器/行锁/补偿扫描/decide 载荷 `resume_mode`）——归 T2 `task_hitl_approval_consumption_auto_resume.md`（依赖本 task merge）
- ❌ **D3 strategy 候选 map env 口**——归 T3 `task_hitl_approval_consumption_strategy_env.md`（无依赖可插队）
- ❌ HITL 挂起机制与 decide 落库本身：`store.py` `adecide`/`_DECIDE` diff 空；状态机/重复 decide 409 一行不动（`_persist_hitl` unlock 计算修正与 payload 增键属接线修补在范围内 · SPEC §3 边界澄清）
- ❌ `auto_approve_ok` 三条件语义放宽；deny_write/deny_high_risk 判序、Policy 写闸、gateway 闸链
- ❌ UI/前端/SSE 事件类型零新增；撤销端点/审批中心改造
- ❌ 新表/新列（payload jsonb 增键零 alembic）；跨进程消费缓存；session 级/租户级持久授权（消费键锁 run 级）
- ❌ live HTTP/SSE 全链实录（留 40 复跑 · 本 task 30 棒只做机制段 pytest 集成）
- ❌ SPEC 文档本身任何改动（在 spec 分支 · 随首个实现 PR 带入 master）

---

## failure_paths

| # | 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|----------|----------|--------|----------|
| — | HG-AUDIT-R1 / HG-GRAPH-MODULES pending 即 30 | **拒开工**（GATE_VERIFY 拦 · 真值在本表人工闸） | 是 | 是 |
| FP-1 | 消费读 store 失败（DB 抖动/异常） | **fail-closed**：视同无批准 · 维持拦截 + warning 台账（断言化） | 是 | 否 |
| FP-2 | 批准过期/囤积；env 非法/越界 | TTL 读时判过期不消费；env 非法/越界（[1,86400]）回退默认 3600；过期重走挂起→审批 | 是 | 否 |
| FP-3 | replan 换 subtask_id 致消费键不命中 | 再挂起重批（新步骤=新授权）；`_carry_plan` 沿用 id 形态可命中——**断言化**（沿用 id → 消费命中；换 id → 不命中再挂起） | 是 | 否 |
| FP-4 | unlock=自身被误用到其他 blocked_by | 形态守卫仅 `delegation_issue_hitl_required`；`prefix_touch_required` 空 unlock 维持 router 409（保留断言） | 是 | 是（409 detail） |
| FP-6 | 同批多申请部分批准 | `_collect_decisions`（router.py:287-316）既有汇总不动；消费逐条三元组匹配；重复 decide 409 原样绿 | 是 | 否 |
| FP-7 | delegation off / observe 模式 | off：消费零触达（无 store 读 · 无新台账 · spy 断言）；observe：本就不拦 · 不记假台账；仅 enforce 下改变判定 | 是 | 否 |
| 实操-A | **async 化漏改 sync 直调**（R1-N2 扩面 · 14 处） | `TypeError: coroutine … never awaited` / 断言拿到 coroutine 对象假绿——B1 清单逐点随改（测试 `async def` 化 / 脚本补 `await`）+ 全量 pytest 亲跑零新增红；**禁只改 import 不改调用**；**影响面 grep 范围须含 `scripts/`**（非仅 `app/`+`tests/`——`capability_step_contract_gate.py:152` 漏网实证 · R1 审查 B-1） | 是 | 否 |
| 实操-B | **decided_at 归一漏 str 分支**（R1-N1） | Db store 实收 ISO 8601 str（`_row_to_dict` :249），归一函数只处理 float → TTL 比较 TypeError 或误判过期/新鲜——双 store 各一组 TTL 断言兜底（Db 组必经 `alist/aget` 真读路径，禁构造 float 绕过） | 是 | 否 |
| 实操-C | 旧单据 payload 缺 capability_id | fail-closed 不消费（**不得视作匹配放行**）；断言化：缺键 approved 单据存在时仍拦截 | 是 | 否 |
| 实操-D | 消费放行后被误当「全链放行」 | 消费只作用于 delegation 签发判定；重下发后 gateway 验签门/Policy 写闸/可见性闸全链仍在——断言「消费命中但 Policy 拒绝场景仍被 Policy 裁」 | 是 | 否 |
| 实操-E | `test_capability_testing_write.py:488-493`「设计真态钉死」段语义翻转 | 该段断言「批准后重下发仍拦（审批逐次有效）」——D1 落地后**有匹配 approved 单据时应放行**：30 须改写该段为「无消费形态（无单据/键不匹配/过期）仍拦 + 有消费形态放行」双断言，**禁整段删除**（边界否定语义由 TA2 承接） | 是 | 否 |
| 实操-F | `npx spec-wave task lint` / `lint-wiki-delta` 红 | 30 返工修结构 | 是 | 否 |

---

## B1 · 旧测影响面（10 已实扫落盘 · 20-audit 核查清单 · 30 亲跑义务）

**sync→async 随改清单（14 处 · 实操-A 对应 · 全绿亲跑义务）**：

| 文件 | 随改点 | 说明 |
|------|--------|------|
| `tests/test_step_contract.py` | :259,275,294,306,323,756,769（7 处 `_join_subtasks` sync 直调） | 改 `async def` + `await`（`asyncio_mode=auto` 自动接管）；既有断言语义零改动 |
| `tests/test_lg_rag_delegation_wiring.py` | :159,170,187（3 处） | 同上 |
| `tests/test_capability_testing_write.py` | :433（`_join_subtasks`）· :492（`_delegation_issue_block_reason`） | :488-493 段按实操-E 改写为双断言 |
| `tests/eval/test_capability_redlines.py` | :1715（1 处） | **默认跑**（pyproject 无 addopts 排除 · conftest 无 deselect 钩子 · CI `.github/workflows/pytest.yml:47` `pytest tests -q --tb=short` 无 `-m` 排除 · 本地与 CI 均收集）；**必须随改并亲跑**（建议另跑 `pytest -m redline` 留证） |
| `scripts/acceptance/capability_step_contract_gate.py` | :152（`async def _drive` 内 sync 直调 `_join_subtasks`） | 补 `await` 一行（`_drive` 已是 async · :140）；该脚本被 `scripts/acceptance/capability_acceptance.sh:165` 真跑（capability 本地验收九层门禁）——漏改则门禁 TypeError/假绿（R1 审查 B-1 退回项） |

**零 diff / 原样绿期望（30 亲跑 · 40 复跑）**：

| 文件 | 断言面 | 预期 |
|------|--------|------|
| `tests/test_capability_delegation.py` | `auto_approve_ok` 三条件/签发/验签面 | 原样绿（纯函数零 IO 不动） |
| `tests/test_hitl_pending_decide.py` | decide 20 用例（409/404/422/归属过滤） | 原样绿（decide 落库不动） |
| `tests/test_hitl_resume.py` / `test_hitl_resume_events.py` | resume 图替身/真 PG 重启链/事件落盘 | 原样绿（resume 机制零改 · 本 task 只让 unlock 不再为空） |
| `tests/test_hitl.py` / `test_lg_rag_sse_hitl.py` | HITL 路由/SSE 挂起帧面 | 原样绿 |
| `tests/test_capability_domain_allowlist.py:102-112` | `test_allow_tags_does_not_waive_deny_write`（deny 判序钉死） | 原样绿（反回归钉死） |
| `tests/test_capability_manifest.py` / `test_capability_visibility_and_receipts.py` / `test_capability_gateway.py` | manifest/可见性/gateway 写拦截面 | 零 diff（capability 包零触） |
| `tests/test_strategy_builder.py` / `test_strategy_scenario.py` / `test_lg_rag_supervisor_capability_catalog.py` | builder/目录面 | 零 diff（D3 归 T3 · 本 task 不碰） |

---

## 验收标准

- [ ] 人工闸：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 approved 后方可勾选下列码项
- [ ] **TA1（消费放行 · SPEC A1）**：store 预置匹配 approved 单据（三元组命中 · decided_at 新鲜）→ 重下发同 tool 签发判定返回 `None`（不再产出 `delegation_issue_hitl_required`）· 台账含 `delegation_approval_consumed`（pytest 断言 · logger/span 双面）
- [ ] **TA2（消费边界否定 · SPEC A2 · 变异式）**：① pending/rejected 不生效 ② 超 TTL 不生效（**InMemory + Db 双 store 各一组** · decided_at 类型归一断言 · Db 组必经 `alist/aget` 真读路径）③ 三元组任一不匹配不生效（换 run_id/换 subtask_id/换 capability_id 三例）④ payload 缺 capability_id 旧单据不生效 ⑤ store 读异常 → 维持拦截 + warning 台账
- [ ] **TA3（单子任务形态 resume 成环 · SPEC A3 · 手动模式）**：`_persist_hitl` 对无前驱前缀 delegation_issue 拦截算出 `unlock_subtask_id=sid`（单测）；机制段 pytest 集成：decide(approved) → resume 200 → 图恢复 → `done{completed}`（可复用 `test_capability_testing_write.py` A4④ fixture 形态）；live HTTP/SSE 全链留 40 复跑
- [ ] **TA4（反回归钉死 · SPEC A5）**：`registry.py::_match_filter` 与 `policy.py` 闸序段 git diff 为空；`test_allow_tags_does_not_waive_deny_write` 及 capability/hitl 既有测试原样绿；审批消费不过 gateway/Policy 断言（消费命中 + Policy 拒绝 → 仍被 Policy 裁）
- [ ] **TA5（off 零 diff · SPEC A6 本 task 面）**：`LG_RAG_DELEGATION_TOKEN_MODE=off` 下消费路径零触达（store 读 spy 断言零调用 · 无 `delegation_approval_consumed` 台账）；既有 delegation/hitl 测试原样绿
- [ ] **TA6（decide 落库不动 · SPEC A7 本 task 面）**：`store.py` `adecide`/`_DECIDE` git diff 为空；重复 decide 409 守卫原样绿（`test_hitl_pending_decide`）；`router.py:404-411` 409 守卫保留断言（prefix_touch 类空 unlock 仍 409）
- [ ] **TA7（工程面 · SPEC A8 本 task 面）**：`pytest tests` 全绿；`ruff check app tests` 触及路径零新增；`./scripts/graph-compile.sh` EXIT=0；图谱 lg_rag/hitl/capability 三行备注回写 + HG-GRAPH-MODULES 00 代录行
- [ ] B1 表 14 处 sync→async/补 `await` 随改全绿亲跑记录（命令 + 结果 · 含 `capability_acceptance.sh` 门禁亲跑）落 40 invoke
- [ ] `npx spec-wave task lint --file docs/tasks/active/task_hitl_approval_consumption_loop.md` PASS；`npx --yes spec-wave@3.0.1 task lint-wiki-delta --target .` PASS

---

## 依赖

| 依赖 | 说明 |
|------|------|
| SPEC（依据 · signed） | `docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md`（**当前在 `spec/hitl-approval-consumption` 分支 · 随首个实现 PR 一并带入 master** · D1/D2/D4 + Q1/Q2/Q3/Q5 + FP-1~FP-7 + A1/A2/A3/A5/A6/A7） |
| 上游 SPEC | `docs/spec/host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md`（signed · Q2 审批口径 / FP-2 墙钟纪律） |
| 源证据 | `docs/harness/invokes/by-task/testing-write-capability/invoke_20261009_30_implement_r2_testing-write-capability.md`（:52-61 探针实证）· `invoke_20261009_40_verify_testing-write-capability.md`（:42-44 live 409 实证） |
| 触发链/改动面锚点 | `nodes.py:277-295,341-354,550-567,644,708-726,1397-1471` · `graph.py:94` · `delegation.py:105-107,488-514` · `hitl/store.py:83-99,159-163,249` · `hitl/router.py:287-316,404-411` · `hitl/persistence.py:61-77` |
| 反回归真值 | `registry.py:112-140` · `policy.py:96-105` · `tests/test_capability_domain_allowlist.py:102-112` |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md`（P-13 异步一致性 · P-15 LangGraph 节点约束 · P-16 capability 契约纪律） |
| 上游任务范式 | `docs/tasks/done/task_testing_write_capability.md`（task 结构/钉死契约/B1/验收形态范式 · 40 核验偏差登记=本 task 立项源） |
| 下游 | T2 `task_hitl_approval_consumption_auto_resume.md`（**依赖本 task merge 进 master** · 消费门是 auto resume 全链 A9 前提）；T3 无依赖 |

---

## 给执行帽的必读列表

1. `AGENTS.md`（新会话启动纪律 + GATE_VERIFY）· 2. 本 task（钉死契约 + B1 + 验收标准）· 3. SPEC v1（`docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` · 若分支尚未带入 master 则于 `spec/hitl-approval-consumption` 分支只读）§1 设计纪律 + §2 D1/D2/D4 + §4 Q1/Q2/Q3/Q5 + §5 FP-1~FP-7 · 4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`（P-13/P-15/P-16）· 5. `nodes.py:277-295,550-567,644,708-726,1397-1471` + `graph.py:94`（改动面）· 6. `hitl/store.py` 全文 + `hitl/persistence.py:61-77`（store 语义与测试隔离面 · 只读不改）· 7. `hitl/router.py:287-316,377-430`（resume 链真值 · 只读）· 8. `tests/test_capability_testing_write.py` 全文（fixture 复用 + :488-493 段改写义务）· 9. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 问题=SPEC v1 既定 D1/D2/D4 承接（HG-SPEC-SIGNOFF=approved）；需求边界无歧义 | no | — | none |
| R1 | 范围=消费门+unlock 回填+台账/测试；D5 划 T2 · D3 划 T3 · decide 落库/deny 判序/Policy 闸全非范围 | no | — | 无 |
| R2 | SPEC Q1/Q2/Q3/Q5 裁定存续不重开；新增裁定=**async 化甲案**（R1-N2 扩面实证后甲乙丙三案裁决 · 乙=事后状态修补双写面 · 丙=sync-over-async 违 P-13）+ **decided_at 归一输入=float\|ISO str**（R1-N1 锚点精度钉） | no | — | async 化甲案与归一类型钉均留 20-task-audit R1 复核 |
| R3 | 交叉验证：`_join_subtasks` sync 实证 14 处额外直调（超 SPEC 估面 · 含 `scripts/` 门禁脚本 1 处 · B1 落清单）· `_error_terminal` tool 字段真源确认 · `_row_to_dict` ISO str 实证 · off/observe 零 diff 论证（`_delegation_active()` 短路在前） | no | — | eval redlines 文件默认跑（无 marker 排除）· 随改义务已钉死 |
| R4 | failure_paths 推演 12 条（FP-1~FP-4/FP-6/FP-7 + 实操 A–F · 含语义翻转段改写义务与归一漏分支坑） | no | — | 无 |
| R5 | 验收口径机断化收敛（TA1–TA7 逐条映射 SPEC A 编号 · 均可对命令输出/断言机断）；无方案分叉残留 | yes | SPEC 裁定全部存续 · 新增两裁定各有实证排除岔路 · 锚点逐行实读闭环 | 见 R2/R3 |

**actual_last_round**：R5 · **early_stop**：yes · **residual_risks**：见 R2/R3

### R0 · 问题框定

SPEC v1 已签收（HG-SPEC-SIGNOFF=approved 2026-10-10），D1/D2/D4 的范围、消费键（Q1）、消费点位置（Q2）、unlock 回填语义（Q3）、时效（Q5）均为已裁定项，本 task 直接承接，不重开需求分析。实读：SPEC v1 全文 + 上游 SPEC host-v1（Q2 审批口径）+ 30/40 源证据 invoke + 全部代码锚点（master `4d905e0` 逐行复核成立）。

### R1 · 范围钉死

改动面六件（F1–F6）：payload 增键 · async 消费助手 · async 化波及面随改 · unlock 回填 · 测试 · 图谱备注。明确划出：D5 自动 resume（T2 · 依赖本 task 成环后才谈得上「自动继续可达 done」）、D3 strategy env 口（T3 · 无耦合）、decide 落库与状态机、deny/Policy/gateway 闸链、UI/SSE。拆分理由：T1 是消费成环**最小可验收闭环**（A1/A2/A3 独立可机断）；T2 的 A9 全链以 T1 消费门+unlock 回填为前提（无消费则 auto resume 恢复后仍再拦 · 无 D2 则 resume 409）——串行合并是机制依赖不是偏好。

### R2 · 方案裁定

**SPEC 裁定存续（不重开）**：Q1 三元组消费键（S2 弱校验/S3 半径爆炸已弃）· Q2 编排层消费（S2 进 capability 包破纯函数纪律已弃）· Q3 unlock=sid+形态守卫（S2 router 放行空 unlock=静默按驳回收工已弃）· Q5 读时 TTL（S2 永久后门/S3 写回状态越非范围已弃）。

**新增裁定一 · async 化路径（R1-N2 扩面 · 甲乙丙三案）**。实证矛盾：SPEC Q2 S1 估「波及面仅 nodes.py:711 + test 一处」，但 `_delegation_issue_block_reason` 唯一生产调用方 `_join_subtasks`（nodes.py:644）是 **sync 节点**，其 sync 直调点另有 13 处（B1 清单 · 含 `scripts/acceptance` 门禁脚本 1 处）· 加 `_delegation_issue_block_reason` 1 处共 14 处。三案：**甲**（`_delegation_issue_block_reason` + `_join_subtasks` 皆 async 化 · 14 处随改）**选定**——LangGraph `add_node` 原生兼容 async 节点（graph.py:94 注册零改动），消费读在拦截/审计落痕**之前**完成（单一写面），`asyncio_mode=auto` 使测试随改纯机械；**乙**（sync 核心不动 + 外层 async 包装节点事后修补）**否**——须摘除已落 `done/extras` 的 blocked 终态、回卷 `blocked_meta` 计数，且 `AUDIT_TOKEN_ISSUE_HITL_REQUIRED` 审计已在 sync 核心内发出无法回卷，双写面风险大于 14 处机械改动；**丙**（sync 判定内 sync-over-async 桥读 store）**否**——违反 P-13 与 store.py:1-10「只有异步接口 · 同步路径一律显式失败」纪律。

**新增裁定二 · decided_at 归一输入类型钉（R1-N1 锚点精度）**。SPEC 表述「Db store 为 datetime（store.py:159-163）」指 SQL 层；消费端经 `alist/aget` 实收 `_row_to_dict` 输出（:249）为 **ISO 8601 字符串**。归一函数输入类型钉 **float | str**，Db 组 TTL 断言必须经真读路径（禁构造 float 绕过 str 分支）。

**新增裁定三 · capability_id 真源**。取 `_persist_hitl` 内 `term.get("tool")`（`_error_terminal` :352-353 保留 tool 字段 · 与 `_delegation_issue_block_reason` 判定所读 `row["tool"]` 同源）——不引入第二真源。

### R3 · 交叉验证

- **波及面实证**：`grep -rn '_join_subtasks' app tests scripts` + `grep -rn '_delegation_issue_block_reason' app tests scripts` 全量落 B1（14 处 · 含 eval 默认跑 1 处注记 · **grep 范围须含 `scripts/`**——`capability_step_contract_gate.py:152` 系 R1 审查补网）。
- **归一精度实证**：实读 `store.py:83-99`（InMemory float :98）vs `:159-163,249`（Db SQL now() → `_row_to_dict` ISO str）——SPEC 表述与消费端实收类型的落差落钉死契约。
- **unlock 回填不波及其他形态**：`prefix_touch_required` 由步骤契约闸（:693-707）产出，其空 unlock 仍走 router 409——形态守卫条件 `blocked_by==delegation_issue_hitl_required` 在 `_persist_hitl` 单点判定，无第二路径。
- **off 零 diff 论证**：`_delegation_active()`（nodes.py:252-254）mode!=off 才启用 → off 时 :710-726 整段短路，消费助手位于该段内 → 天然零触达；spy 断言兜底。observe：`auto_approve_ok` 判出需审批才进消费读 · observe 语义不拦（既有行为）→ 不记假台账。
- **resume 成环机制复用**：`_locked_prefix` 摘除 `hitl_unlocked_ids`（:560-562 注释「批准的唯一效果」）为既有机制 · D2 只是让 unlock 值不再为空 · resume.py/router.py 恢复链一行不改。

### R4 · failure_paths 推演

SPEC FP-1~FP-7 逐条落机制（FP-5 属 T3 env 口面 · 本 task 不承载；FP-8~FP-11 归 T2）：读失败 fail-closed（FP-1）· TTL/非法 env 回退（FP-2）· replan 换 id 再挂起与沿用 id 命中双断言（FP-3）· 形态守卫（FP-4）· 同批部分批准逐条匹配（FP-6）· off/observe（FP-7）。实操坑六条来自锚点实读：async 漏改（A · coroutine 假绿）、归一漏 str（B · TypeError/误判）、旧单据缺键误匹配（C · fail-closed 钉）、消费≠全链放行（D · Policy 仍裁断言）、既有测试语义翻转段改写义务（E · 禁整段删除）、lint 红（F）。每条均有断言或闸对应，可机断。

### R5 · 验收口径机断化收敛

TA1–TA7 逐条映射 SPEC A 编号并落到可对命令输出/断言机断的形态（台账断言 · 双 store TTL · diff 空 · spy 零调用 · 409 保留 · EXIT=0）；B1 14 处随改与旧测清单全绿亲跑义务落 40 invoke。无残留方案分叉（SPEC 裁定存续 + 新增三裁定各有实证排除岔路）→ early_stop。

---

### 自检结论（执行者）

| 验收 | 结论 | 证据 |
|---|---|---|
| TA1 消费放行 | ✅ | tests/test_hitl_approval_consumption.py（台账 logger+span 双面） |
| TA2 变异否定组 | ✅ | 八组 25+ 枚（pending/rejected · 三元组/缺键/类型守卫 · TTL 双 store 真读 · 读异常 · env 解析 · 归一） |
| TA3 unlock 回填+成环 | ✅（机制段）/ ⚠️（live 末段见下） | unlock=sid+payload 键单测 · resume 成环机制段（decide→replan→消费放行→签发→执行→done 收口）；live 挂起→pending→decide→**resume 200** 实证（40 invoke） |
| TA4 反回归 | ✅ | registry/policy/delegation diff 空 + TA4-D 断言（消费不过 gateway/Policy） |
| TA5 off 零 diff | ✅ | spy 零调用 + 零台账 |
| TA6 decide 落库不动 | ✅ | store/router diff 空 + prefix_touch 空 unlock 409 保留断言（HTTP 真端点） |
| TA7 工程面 | ✅ | 全量 1713 passed 0 failed · ruff 触及面零新增 · graph-compile EXIT=0 · 门禁失败 0 |

⚠️ live 末段偏差：replan 重盖章 sid 致消费键失配（FP-3 循环）· 非本 task 回归 · 上抛 T2/SPEC v2（40 invoke「重要发现」）。30/40 invoke：by-task/hitl-approval-consumption-loop/。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-10 | 10-task 落稿（骨架先行增量落盘 · SPEC v1 signed 承接 · R0–R5 · HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 pending → 30 拒开工） |
| 2026-10-10 | 00 代录三闸 approved（R1 增量复核 PASS · commit 45fec13）+ 计数口径顺手回改「15 处」→「14 处」（真值=B1 表枚举 join 13 + block_reason 1 · R2 审查自引更正） |
| 2026-10-10 | 10-task 修订（20-task-audit R1 退回 B-1 修复 · **仅文档口径补齐 · 裁定结构不动**）：① B1 随改清单补第 15 处 `scripts/acceptance/capability_step_contract_gate.py:152`（`async def _drive` 内 sync 直调 `_join_subtasks` · 补 `await` · 被 `capability_acceptance.sh:165` 真跑 · 本地验收九层门禁）② 「14 处」→「15 处」全文统一（R1-N2 锚点/R2/R3 内「13 处」同步→「14 处」）③ B1 redline 行「非默认跑（eval marker）」改「默认跑（pyproject 无 addopts 排除 · conftest 无 deselect · CI pytest.yml:47 无 `-m` 排除）· 必须随改亲跑」（删「30 注记是否随改」可选措辞 · R3 residual 同步）④ 实操-A 补「grep 范围须含 `scripts/`」提醒 |
