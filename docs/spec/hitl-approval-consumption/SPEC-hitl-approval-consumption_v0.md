# SPEC：签发审批消费回路（hitl-approval-consumption · delegation HITL 批准→放行半环接线）（v0）

> **层级**：L1 波次 SPEC（Host V1-A delegation-token 的收口半环 · 实证驱动立项）
> **状态**：`draft`（HG-SPEC-SIGNOFF=**pending** · 须先 20-spec-audit 书面审 → 维护者人签后才可拆 task）
> **种子（源证据 · 全部实证于 2026-10-09 D2 task_testing_write_capability 的 30/40 两棒）**：
> - [`../../harness/invokes/by-task/testing-write-capability/invoke_20261009_30_implement_r2_testing-write-capability.md`](../../harness/invokes/by-task/testing-write-capability/invoke_20261009_30_implement_r2_testing-write-capability.md)（「重要发现」节 :52-61 · 留转 :157-159）
> - [`../../harness/invokes/by-task/testing-write-capability/invoke_20261009_40_verify_testing-write-capability.md`](../../harness/invokes/by-task/testing-write-capability/invoke_20261009_40_verify_testing-write-capability.md)（A1 live 实测 :29-44 · run 0eb059a5883b497997f790893842efdc · 裁定建议 :65,76）
> - **维护者裁定（2026-10-09）**：「另立task，此次完成后写入到spec文档中」
> **上游**：[`../host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md`](../host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md)（signed · 签发审批口径 Q2 与 D5 为本 SPEC 的直接上游；冲突以本 SPEC 为准处仅 §2 三缺口接线）
> **下游**：20-spec-audit → HG-SPEC-SIGNOFF（人签）→ 00 出 task → 20-task-audit → HG-AUDIT-R1 → 30 → 40 → PR+CI 绿+merge → 图谱回写 → CLOSE
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `hitl-approval-consumption` |
| **invoke_slug** | `hitl-approval-consumption`（SPEC 与 task 阶段共用） |
| **test_strategy** | `required` |
| **test_strategy_note** | pytest 单测/集成为主（消费门边界否定断言 + 单子任务 resume 机制段 + env 口零 diff 断言 + 反回归对拍）；live HTTP/SSE 全链（三 env 组 + 真服务 + cookie maintainer → done{completed}）留 40 复跑；不开新 freeze 面 |
| **默认分支** | task 阶段 `task/hitl-approval-consumption`（自 `master` 分出；**禁止 master/main 直改**）；本 SPEC 起草于 `spec/hitl-approval-consumption` |
| **graph_change_layer** | `G-L1` 行备注（不新增一级模块：`capability`/`lg_rag`/`hitl`/`strategy` 四行在册备注；HG-GRAPH-MODULES 随 30 回写由 00 代录） |
| **freeze_id** | 无（无新 SSE 事件类型 · 无新 HTTP 路由 · 无新表 · 零 alembic 义务——unlock 回填写既有列、payload 为 jsonb 增键） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | **pending** | 本 SPEC 须先经 20-spec-audit 书面审（结论落盘 `docs/harness/reviews/`），再维护者人签；人签前 **00 不得拆 task、30 不得改码** |

---

## 1. 背景与目标

### 三处实证缺口（逐条锚定源证据行号 · 均已在 master ca4148f 复核成立）

**缺口 1 · 审批结果不被签发判定消费（批准→放行半环断）**。
delegation 签发审批的自动放行判定 `auto_approve_ok`（`app/ops/capability/delegation.py:488-514` · 三条件在 :502-513：scope 内 / 全只读 / 非 sandbox·cli 类）与其调用方 `_delegation_issue_block_reason`（`app/ops/lg_rag/multi/nodes.py:277-295`）**只读 Host 侧注册表真值，不读任何 HITL 审批记录**。后果：`decide(approved)` persisted=true 之后，重下发同 tool 仍再拦 → 再挂起 → 循环。
证据：30 invoke :52-61（探针实证 `post-approval issue_block_reason='委派签发需人工审批（…非只读（side_effect=write））'` · `re-blocked on redispatch: ['delegation_issue_hitl_required']`）；40 invoke :44（实读 delegation.py:488-514 确认不读审批结果 · 成立）。

**缺口 2 · 单子任务计划 resume 409**。
`_persist_hitl`（nodes.py:1397-1471）算 `unlock_subtask_id` 只取 `depends_on ∩ plan_prefix_ids`（:1440-1445）；单子任务计划（或被拦步骤无已执行前缀依赖）算出 `unlock_subtask_id=''`，批准后 `app/ops/hitl/router.py:403-411` 抛 409「已批准但拿不到待解锁的步骤（unlock_subtask_id 为空）」。
证据：30 invoke :53-54；40 invoke :42（live run `0eb059a5883b497997f790893842efdc` · HTTP 409 detail 与 30 实证**逐字一致** · `done{completed}` 未达成如实登记）。

**缺口 3 · 第四道门（strategy 候选 map 无 env 口）**。
`app/ops/strategy/config.py:14-23` `CAPABILITY_ALLOWLIST_BY_KEY["supervisor"]` 为**静态候选 map**（无 env 口），builder 节点 `allowed = candidates ∩ visible`（`app/ops/strategy/builder.py:177-182`）使 testing.write.echo 类新 capability 在生产路径 plans 永不可达；即使 LLM 幻觉出该 id，`_subtasks_have_valid_tool_ids`（nodes.py:147-157）也拒 → fallback rag。
证据：40 invoke :33（live 首发 SSE `node.progress` 帧实证 allowed_capability_ids=静态五枚 · 以测试等价 shim `CANDIDATE_CAPABILITY_IDS` 运行期覆盖补位 · 仓内代码零改动如实登记）。

### 一句话目标

把 delegation HITL 的「批准」接成**可消费的授权**：签发判定在裁定拦截前先消费匹配的 approved 单据（缺口 1）；单子任务形态的批准拿得到解锁目标、resume 走通到 `done{completed}`（缺口 2）；strategy 候选 map 开 env 追加口，新 capability 生产可达且默认零 diff（缺口 3）。

### 设计纪律（签收时锁死 · 反回归钉死）

1. **deny 判序不动**：`registry.py::_match_filter`（:112-140 · 形态→风险→副作用→标签收窄；`deny_high_risk` :128-129 在 `deny_write` :130-136 之前；`allow_write_tags_any` 只豁免 deny_write 一层 · 永不豁免 deny_high_risk）函数体逐字节零 diff；`test_allow_tags_does_not_waive_deny_write` 原样绿。
2. **Policy 写闸不动**：`policy.py:96-105` 闸序（高危→写→sandbox→cli→tenant）零 diff；审批消费**只作用于 delegation 签发判定**，不豁免 gateway/Policy 任何一层（写能力执行仍须 `write_not_confirmed` 口径放行）。
3. **off 模式零 diff**：`LG_RAG_DELEGATION_TOKEN_MODE=off` 时消费代码路径完全不触达（无 store 读 · 无新台账 · 行为逐字节现状）。
4. **消费安全语义（20-spec-audit 可查）**：审批消费仅对**读取时刻 `status=approved` 且未过期（TTL）且未撤销**的单据生效；消费**不写回单据状态**（decide 落库不动）；任何后续状态翻转（未来撤销端点把 approved 翻走）天然令消费失效——授权效力 = 读取时刻的活状态，非缓存快照。
5. **记动作不记内容**：消费命中/未命中/失败进台账（logger + span metadata）；只记 request_id/subtask_id/capability_id/decision_by/TTL 余量，不记参数原值。

---

## 2. 范围（D 块展开）

### D1 · 审批消费门（缺口 1 · 必做）

- **消费点**：`nodes.py::_delegation_issue_block_reason`（:277-295）——`auto_approve_ok` 判出需审批（`ok=False`）后、返回 HITL 原因前，先查 HITL store 有无**匹配 approved 单据**；命中 → 返回 `None`（放行签发）+ 台账 `delegation_approval_consumed`；未命中/异常 → 维持拦截（fail-closed · 现状语义）。
- **消费键（§4 Q1 裁定）**：`(run_id, subtask_id, capability_id)` 三元组精确匹配。`capability_id` 由 `_persist_hitl` 落库时在 `payload`（jsonb）增记（**零迁移** · 既有读取兼容）；**旧单据缺该键 → 不消费**（fail-closed，只授权新单据）。
- **时效（§4 Q5 裁定）**：`decided_at + TTL < now` → 不消费（读时判过期，不写 expired 状态）。env `OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS` 默认 3600，非法/越界回退默认（承 step_contract `_env_int` 纪律）。
- **单据类型守卫**：仅消费 `blocked_by=delegation_issue_hitl_required` 类单据；`prefix_touch_required`（改历史授权）语义**不动**——重跑已执行步骤仍须既有前缀审批。
- `auto_approve_ok` 保持**纯函数零 IO**（§4 Q2）：消费读写在 nodes.py 编排层（async 化消费助手），不进 capability 包。

### D2 · unlock_subtask_id 空形态回填（缺口 2 · 必做）

- `_persist_hitl`（nodes.py:1440-1445）：当 `depends_on ∩ plan_prefix_ids` 为空 **且** `blocked_by=delegation_issue_hitl_required` → `unlock_subtask_id = 被拦 sid 自身`（语义：批准授权**（重）下发该被拦步骤本身**——它不是已执行前缀，解锁语义退化为「签发放行授权」，与 D1 消费配对成环）。
- **形态守卫**：仅限 delegation_issue 类；`prefix_touch_required` 类空 unlock 维持现状（router 409 是人可解的明确报错 · 不静默放行）。
- `router.py:403-411` 409 守卫**保留不动**：D2 让该形态不再产生空 unlock，而不是放宽 409（空 unlock + approved 仍 409，防「批了但按驳回收工」假动作）。
- resume 成环路径：approved=[sid] → `hitl_unlocked_ids=[sid]` → `_locked_prefix`（nodes.py:550-567）摘除（sid 非前缀则无操作）→ replan/carry 重下发 sid → D1 消费放行 → 令牌签发 → 执行 → `done{completed}`。

### D3 · strategy 候选 map env 口（缺口 3 · 必做）

- `strategy/config.py` 增 env 追加集 `OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS`（逗号分隔 · strip · 去空去重 · **默认不设=解析结果对 master 逐字节零 diff**）。
- `get_candidate_capability_ids` 在 map 解析结果后追加 env 集（含未知 key 的空集——env 是运维显式声明，fail-closed 管的是**默认**而非显式操作；§4 Q4）。
- **下游闸全链不动**：candidates 仍经 `build_allowlist_from_candidates` ∩ visible（builder.py:180-182）；可见性（deny_write/deny_high_risk 判序）、Policy 写闸、`_subtasks_have_valid_tool_ids` 全部照旧——env 只抬**候选层**，不是放行口。
- env 生效记台账（候选 id 列表 + 基数；配置非敏感）。

### D4 · 审计与测试（必做）

- 台账新动作：`delegation_approval_consumed`（命中 · request_id/subtask_id/capability_id/decision_by/TTL 余量）· 消费读取失败 warning（fail-closed 留痕）· env 追加集生效记录。承 `capability/metrics.py`/`visibility.py` 先例，记动作不记内容。
- 测试按 §6 验收 A1–A8 逐条断言化。

---

## 3. 非范围

- ❌ **HITL 挂起机制与 decide 落库本身**：interrupt/resume 回路、`adecide` 守卫（只受理 pending · 重复 decide 409）、状态机（pending/approved/rejected）一行不动。边界澄清：`_persist_hitl` 的 **unlock 计算修正**（D2）与 **payload jsonb 增记 capability_id**（D1）属接线修补在范围内——零迁移、既有读取兼容、不改任何守卫与状态语义；此解释留 20-spec-audit 复核。
- ❌ UI 不动（前端/审批列表/ SSE 事件类型零新增）。
- ❌ deny_write/deny_high_risk 判序、Policy 写闸、gateway 闸链（§1 设计纪律 1/2）。
- ❌ 撤销端点/审批中心改造（消费语义按「读时活状态」设计，与未来撤销天然兼容；撤销端点本身另议）。
- ❌ `auto_approve_ok` 三条件语义放宽（只读自动边界不动；本波只在「判出需审批之后」接消费，不改「什么需要审批」）。
- ❌ 新表/新列（payload jsonb 增键零 alembic 义务）；跨进程消费缓存（每判定读 store 活值 · 微优化另议）。
- ❌ session 级/租户级持久授权（消费键锁 run 级；更大授权半径 v2 另议）。

---

## 4. 开放裁定（必答题 · 全部作答 · 留 20-spec-audit 复核）

### Q1 · 消费键粒度

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · (run_id, subtask_id, capability_id) 三元组** | payload 增记 capability_id · 读时精确匹配 | 半径最小（一次批准只授权这一 run 这一步这一 tool）；旧单据缺键 fail-closed | `_persist_hitl` 落库载荷增一键 | **推荐（裁定）** |
| S2 · 仅 (run_id, subtask_id) | 不动落库载荷 | 零写路径改动 | 同 sid 换 tool 的 replan 校验弱（虽 `_carry_plan` 不换 tool · 仍属隐式假设） | 弃选 |
| S3 · (thread_id, capability_id) 会话级 | 一批整会话放行 | 人少点几次 | 半径爆炸（同 tool 后续任意步骤全免批）· 与「run 级授权」纪律冲突 | 弃选 |

**裁定：S1。** 审批是 run 级授权产物（承 delegation-token SPEC Tier 1 语义）；capability_id 入键防「批了 A tool 放行 B tool」。

### Q2 · 消费点位置

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · nodes.py 编排层消费（async 助手）** | `_delegation_issue_block_reason` 判定链前置消费读；`auto_approve_ok` 保持纯函数 | 守住 capability 包「纯代码判定零 IO」纪律（delegation-token SPEC §2 D2/D3 同纪律）；store 异常可 fail-closed 留痕 | nodes 调用面 async 化小改 | **推荐（裁定）** |
| S2 · 改 `auto_approve_ok` 增第四条件 | 消费进 capability 包 | 调用点不变 | 破坏纯函数纪律 · sync 签名装不下 async store 读 · 单测面污染 | 弃选 |

**裁定：S1。**

### Q3 · unlock 空形态回填语义

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · 无前驱前缀时 unlock=被拦 sid 自身 + 形态守卫** | 仅 delegation_issue 类回填；router 409 保留 | resume 走通且「批准=授权重下发该步」语义显式；409 假动作防线不拆 | 解锁语义从「改历史」扩展到「签发放行」——由 D1 消费配对成环 | **推荐（裁定）** |
| S2 · router 放行空 unlock | approved 空集也恢复 | 零写路径改动 | 正是 409 存在理由的反面（静默按驳回收工 · 人看「批了但没做」） | 弃选 |

**裁定：S1。**

### Q4 · 候选 map env 口形态

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · env 追加集（逗号分隔 · 默认空）** | map 解析后追加；下游 ∩visible/Policy 不动 | 默认零 diff · 运维显式 · 不碰静态 map 默认值 | 需钉死「env 只抬候选层」文档与测试 | **推荐（裁定）** |
| S2 · env JSON 覆盖整 map | 运维可全量改写候选 | 灵活 | 易误伤默认五枚只读集 · 覆盖语义比追加难审计 | 弃选 |
| S3 · 不动 map · 复用 `CANDIDATE_CAPABILITY_IDS` 全局覆盖 | 零新代码 | 模块全局覆盖所有 key 半径过大 · 定位是测试钩子（config.py:25-26 注释明示） | 弃选 |

**裁定：S1。**

### Q5 · 批准时效语义

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · decided_at+TTL 读时判过期（默认 3600s）** | 不写状态 · 消费时计算 | 防挂起囤批（承 delegation-token FP-2 墙钟纪律）；`ops_hitl_requests` 模型注释 :481 已预留 `expired` 语义位 | 长审批链路超 TTL 需重批（可配） | **推荐（裁定）** |
| S2 · 永久有效 | 不判过期 | 实现最省 | 批准囤成永久后门 | 弃选 |
| S3 · 一次性消费写回状态 | 消费后翻转单据 | 语义最严 | 动 decide 落库语义（越非范围）· replan 重下发同 sid 会被二次拦 | 弃选（留 v2 再议） |

**裁定：S1。**

---

## 5. failure_paths

| # | 路径 | 裁定 |
|---|---|---|
| FP-1 | 消费读 store 失败（DB 抖动/异常） | **fail-closed**：视同无批准 · 维持现状拦截 + warning 台账；绝不静默放行 |
| FP-2 | 批准过期/囤积 | TTL 读时判过期不消费；env 非法值回退默认 3600；过期重走挂起→审批 |
| FP-3 | replan 换 subtask_id 致消费键不命中 | 再挂起重批（新步骤=新授权 · 安全默认）；`_carry_plan` 沿用 id 形态可命中 · 断言化 |
| FP-4 | unlock=自身被误用到其他 blocked_by | 形态守卫仅 `delegation_issue_hitl_required`；`prefix_touch_required` 空 unlock 维持 router 409（人可解的明确报错） |
| FP-5 | env 口注入高危/写 id | 下游 ∩visible + deny_high_risk（判序在前）+ Policy 写闸全链仍在；env 只抬候选层 · 断言「env 含高危 id 仍被裁」 |
| FP-6 | 同批多申请部分批准 | `_collect_decisions`（router.py:287-316）既有汇总不动；消费按单据逐条匹配；重复 decide 409 守卫原样绿 |
| FP-7 | delegation off/observe 模式语义 | off：消费路径零触达（零 diff 断言）；observe：本就不拦 · 消费无可观测差（不记假消费台账）；仅 enforce 下消费改变判定结果 |

---

## 6. 验收标准（可机验）

1. **A1 消费放行**：store 预置匹配 approved 单据（三元组命中 · decided_at 新鲜）→ 重下发同 tool 签发判定返回 `None`（不再产出 `delegation_issue_hitl_required`）· 台账含 `delegation_approval_consumed`（pytest 断言）。
2. **A2 消费边界否定断言（变异式）**：pending/rejected 单据不生效；超 TTL 不生效；run_id/subtask_id/capability_id 任一不匹配不生效；payload 缺 capability_id 的旧单据不生效；store 读异常 → 维持拦截 + warning。
3. **A3 单子任务形态 resume 成环**：`_persist_hitl` 对无前驱前缀 delegation_issue 拦截算出 `unlock_subtask_id=sid`；机制段 pytest 集成：decide(approved) → resume 200 → 图恢复 → `done{completed}`；live HTTP/SSE 全链（三 env 组 + 新 env · 无 shim）留 40 复跑。
4. **A4 env 口**：不设 → `get_candidate_capability_ids` 各 key（含未知 key）解析结果对 master 逐字节一致；设 env → candidates 含追加 id 且 ∩visible/stripped 语义不变；env 含高危/写 id 仍被下游裁（FP-5 断言）。
5. **A5 反回归钉死**：`registry.py::_match_filter` 与 `policy.py` 闸序段 git diff 为空；`test_allow_tags_does_not_waive_deny_write` 及 capability/hitl 既有测试原样绿；审批消费不过 gateway/Policy 的断言（写能力执行仍须写确认口径）。
6. **A6 off 零 diff**：`LG_RAG_DELEGATION_TOKEN_MODE=off` 下消费路径零触达（无 store 读 · 无新台账 · 既有 delegation/hitl 测试原样绿）。
7. **A7 decide 落库不动**：`store.py` `adecide`/`_DECIDE` git diff 为空；decide 端点重复 409 守卫原样绿（`test_hitl_pending_decide`）；router.py:403-411 409 守卫保留（空 unlock + approved 仍 409 的断言）。
8. **A8 工程面**：`pytest tests` 全绿；`ruff check` 触及路径零新增；`./scripts/graph-compile.sh` EXIT=0；图谱 `capability`/`lg_rag`/`hitl`/`strategy` 四行备注回写 + HG-GRAPH-MODULES 00 代录行。

---

## 7. 思考轮回填（R0–R5）

- **R0（读人聊/目标）**：维护者裁定原话「另立task，此次完成后写入到spec文档中」（2026-10-09）；30/40 两棒 invoke 全文已读，三缺口证据行号逐一复核于 master ca4148f 源码（delegation.py:488-514 · nodes.py:277-295,1440-1445 · router.py:403-411 · strategy/config.py:14-23 · builder.py:177-182 · registry.py:112-140 · policy.py:96-105 · store.py 全文 · models.py:449-487）。
- **R1（范围/非范围）**：范围锁三缺口接线（D1 消费门 / D2 unlock 回填 / D3 env 口 / D4 审计测试）；非范围锁挂起与 decide 落库机制、UI、deny 判序与写闸、撤销端点、会话级授权——边界澄清（_persist_hitl 载荷增键属范围）已显式立字据留审。
- **R2（方案对比）**：五个开放裁定全部 ≥2 案对比作答——Q1 三元组消费键（S2 弱校验 / S3 会话级双弃）· Q2 编排层消费（改纯函数弃）· Q3 unlock=自身+形态守卫（放宽 409 弃）· Q4 env 追加集（JSON 覆盖 / 全局钩子双弃）· Q5 TTL 读时过期（永久有效 / 一次性写回双弃）。
- **R3（边界/失败路径）**：FP-1~FP-7 全部正面裁定；最锋利边界 = 消费安全语义（读时活状态 + fail-closed + TTL + 单据类型守卫四重）与 unlock 语义扩展的形态守卫；off/observe/enforce 三档语义逐一钉死。
- **R4（验收/可测性）**：验收 8 条全部可机断（A2 为变异式否定断言组 · A5/A7 用 git diff 为空+既有测试原样绿双钉反回归 · A3 机制段 pytest + live 段留 40 分工承 testing-write-capability 先例）；test_strategy=required。
- **R5（签收就绪）**：开放裁定 Q1–Q5 无遗留；图谱义务已定（四行备注 · 无新一级模块 · 零 alembic）；本 SPEC 不自称可签收——**先 20-spec-audit 书面审，再维护者签 HG-SPEC-SIGNOFF，人签后 00 方可拆 task**。

### 思考轮控制

| 轮 | 状态 | 说明 |
|---|---|---|
| R0 | done | 维护者裁定 + 30/40 invoke 全文 + 全部代码锚点复核 |
| R1 | done | 范围 D1–D4 / 非范围锁死（含 _persist_hitl 边界澄清） |
| R2 | done | Q1–Q5 ≥2 案对比 + 裁定 |
| R3 | done | FP-1~FP-7 裁定 |
| R4 | done | 验收 A1–A8 + test_strategy=required |
| R5 | done | 交 20-spec-audit → HG-SPEC-SIGNOFF（人签）→ 00 拆 task |
| early_stop | no | — |

---

## 8. 关联

- 上游 SPEC：[`../host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md`](../host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md)（signed · Q2 审批口径 / D5 scope / FP-2 墙钟纪律）
- 源证据：[`30 invoke r2`](../../harness/invokes/by-task/testing-write-capability/invoke_20261009_30_implement_r2_testing-write-capability.md) · [`40 invoke`](../../harness/invokes/by-task/testing-write-capability/invoke_20261009_40_verify_testing-write-capability.md)
- 代码锚点：`app/ops/capability/delegation.py:488-514` · `app/ops/lg_rag/multi/nodes.py:277-295,1397-1471` · `app/ops/hitl/router.py:287-316,403-411` · `app/ops/hitl/store.py` · `app/ops/strategy/config.py:14-45` · `app/ops/strategy/builder.py:177-182` · `app/ops/capability/registry.py:112-140` · `app/ops/capability/policy.py:96-105` · `app/db/models.py:449-487`
- 图谱：`docs/_tech_graph/l1/01_modules.md`（capability/lg_rag/hitl/strategy 行 · 回写义务见 Harness 元信息）

## 修订记录

| 日期 | 版本 | 内容 |
|---|---|---|
| 2026-10-09 | v0 | 10-spec 初稿：三实证缺口锚定 30/40 invoke 行号展开 D1–D4；开放裁定 Q1–Q5 全部作答；FP-1~FP-7 裁定；验收 A1–A8；R0–R5 回填；HG-SPEC-SIGNOFF=pending（待 20-spec-audit → 人签） |
