# SPEC：签发审批消费回路（hitl-approval-consumption · delegation HITL 批准→放行半环接线 + 批准后自动继续可配置面）（v1）

> **层级**：L1 波次 SPEC（Host V1-A delegation-token 的收口半环 · 实证驱动立项）
> **状态**：`draft`（v1 修订稿 · 承接 v0 + R1 PASS-WITH-NITS + handoff 第一棒裁定 · HG-SPEC-SIGNOFF=**pending** · 须先 20-spec-audit R2 书面审 → 维护者人签后才可拆 task）
> **v0**：[`SPEC-hitl-approval-consumption_v0.md`](SPEC-hitl-approval-consumption_v0.md)（保留不动 · R1 审查对象）
> **本版修订来源**：① handoff 令 [`PROMPT_00_hitl-consumption-loop-handoff_20261009.md`](../../harness/invokes/by-task/_prompts/PROMPT_00_hitl-consumption-loop-handoff_20261009.md)（验收令「A1 第四段补全实录」+ 两约束：自动/手动可配置 · 无状态恢复纪律）；② 终局文档 §4（[`DESIGN_agent_contribution_endgame_v0_zh.md`](../../guides/DESIGN_agent_contribution_endgame_v0_zh.md) :82-83）；③ R1 审查 nits N3/N4（SPEC 层吸收 · N1/N2 移交 task 阶段）
> **种子（源证据 · 全部实证于 2026-10-09 D2 task_testing_write_capability 的 30/40 两棒）**：
> - [`30 invoke r2`](../../harness/invokes/by-task/testing-write-capability/invoke_20261009_30_implement_r2_testing-write-capability.md)（「重要发现」节 :52-61 · 留转 :157-159）
> - [`40 invoke`](../../harness/invokes/by-task/testing-write-capability/invoke_20261009_40_verify_testing-write-capability.md)（A1 live 实测 :29-44 · run 0eb059a5883b497997f790893842efdc · 裁定建议 :65,76）
> - **维护者裁定（2026-10-09）**：「另立task，此次完成后写入到spec文档中」+「授权00签收所有过程文档」
> **上游**：[`SPEC-host-v1-delegation-token_v0.md`](../host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md)（signed · Q2 审批口径 / D5 scope / FP-2 墙钟纪律）· 终局路线 v0（§4 为本 SPEC D5 直接上游）
> **下游**：20-spec-audit R2 → HG-SPEC-SIGNOFF（人签 · 00 代录）→ 00 出 task → 20-task-audit → HG-AUDIT-R1 → 30 → 40 → PR+CI 绿+merge → 图谱回写 → CLOSE
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `hitl-approval-consumption` |
| **invoke_slug** | `hitl-approval-consumption`（SPEC 与 task 阶段共用） |
| **test_strategy** | `required` |
| **test_strategy_note** | pytest 单测/集成为主（消费门边界否定断言 + 单子任务 resume 机制段 + env 口零 diff 断言 + 自动 resume 触发/认领/补偿扫描幂等断言 + 反回归对拍）；live HTTP/SSE 全链（三 env 组 + 新 env · 无 shim → done{completed}）留 40 复跑；不开新 freeze 面 |
| **默认分支** | task 阶段 `task/hitl-approval-consumption`（自 `master` 分出；**禁止 master/main 直改**）；本 SPEC 起草于 `spec/hitl-approval-consumption` |
| **graph_change_layer** | `G-L1` 行备注（不新增一级模块：`capability`/`lg_rag`/`hitl`/`strategy` 四行在册备注；HG-GRAPH-MODULES 随 30 回写由 00 代录） |
| **freeze_id** | 无（无新 SSE 事件类型 · 无新表 · 零 alembic 义务——unlock 回填写既有列、payload 为 jsonb 增键、补偿扫描只读+行锁）；decide 端点请求载荷增**可选键**（见 D5 · 既有调用零 diff） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | **approved** | 维护者人签 · 00 代录（授权「授权00签收所有过程文档」2026-10-09）· 2026-10-10 · 依据：20-spec-audit R2 PASS-WITH-NITS（`docs/harness/reviews/spec_hitl-approval-consumption_audit_R2_20261010.md` · 裁定 8/0/0 · R2-N1~N3 携拆 task）|

---

## 1. 背景与目标

### 三处实证缺口（逐条锚定源证据行号 · 均已在 master ca4148f 复核成立）

**缺口 1 · 审批结果不被签发判定消费（批准→放行半环断）**。
delegation 签发审批的自动放行判定 `auto_approve_ok`（`app/ops/capability/delegation.py:488-514` · 三条件在 :502-513）与其调用方 `_delegation_issue_block_reason`（`app/ops/lg_rag/multi/nodes.py:277-295`）**只读 Host 侧注册表真值，不读任何 HITL 审批记录**。后果：`decide(approved)` persisted=true 之后，重下发同 tool 仍再拦 → 再挂起 → 循环。
证据：30 invoke :52-61（探针实证 re-blocked）；40 invoke :44。

**缺口 2 · 单子任务计划 resume 409**。
`_persist_hitl`（nodes.py:1397-1471）算 `unlock_subtask_id` 只取 `depends_on ∩ plan_prefix_ids`（:1440-1445）；单子任务计划算出 `unlock_subtask_id=''`，批准后 `app/ops/hitl/router.py:404-411` 抛 409「已批准但拿不到待解锁的步骤（unlock_subtask_id 为空）」。
证据：30 invoke :53-54；40 invoke :42（live run `0eb059a5…` · 409 detail 逐字一致 · `done{completed}` 未达成如实登记）。

**缺口 3 · 第四道门（strategy 候选 map 无 env 口）**。
`app/ops/strategy/config.py:14-23` `CAPABILITY_ALLOWLIST_BY_KEY["supervisor"]` 为**静态候选 map**（无 env 口），builder 节点 `allowed = candidates ∩ visible`（`app/ops/strategy/builder.py:177-182`）使 testing.write.echo 类新 capability 生产路径 plans 永不可达。
证据：40 invoke :33（live 首发 SSE 帧实证静态五枚 · 测试等价 shim 补位如实登记）。

### 第四立案（v1 新增 · 承 handoff 令与终局 §4）

**批准后自动继续缺失**：v0 链路只覆盖「手动 resume」半环；终局 §4 :82 裁定「批准后自动继续」做成**可配置**（全局默认 + 可按审批单选「立即执行/稍后手动」），机制 = 触发器（进程内后台任务 / PG 轮询工人 / PG LISTEN-NOTIFY 三选一）+ 补偿扫描（启动时+定时扫「已批准未恢复」· 无状态恢复保证幂等）+ 多副本数据库行锁认领防重。本 SPEC 按此落地为 D5，不单边改死。

### 一句话目标

把 delegation HITL 的「批准」接成**可消费的授权**：签发判定在裁定拦截前先消费匹配的 approved 单据（缺口 1）；单子任务形态的批准拿得到解锁目标、resume 走通到 `done{completed}`（缺口 2）；strategy 候选 map 开 env 追加口（缺口 3）；「批准后继续」做成可配置自动/手动并以补偿扫描兜底（第四立案 · D5）。

### 设计纪律（签收时锁死 · 反回归钉死）

1. **deny 判序不动**：`registry.py::_match_filter`（:112-140 · `deny_high_risk` 在 `deny_write` 之前；`allow_write_tags_any` 只豁免 deny_write 一层）函数体逐字节零 diff；`test_allow_tags_does_not_waive_deny_write` 原样绿。
2. **Policy 写闸不动**：`policy.py:96-105` 闸序零 diff；审批消费**只作用于 delegation 签发判定**，不豁免 gateway/Policy 任何一层。
3. **off 模式零 diff**：`LG_RAG_DELEGATION_TOKEN_MODE=off` 时消费与自动 resume 代码路径完全不触达（无 store 读 · 无新台账 · 无后台任务行为差）。
4. **消费安全语义（20-spec-audit 可查）**：审批消费仅对**读取时刻 `status=approved` 且未过期（TTL）且未撤销**的单据生效；消费**不写回单据状态**；状态翻转天然令消费失效——授权效力 = 读取时刻的活状态，非缓存快照。
5. **记动作不记内容**：消费命中/未命中/失败、自动 resume 触发/认领/补偿扫描进台账（logger + span metadata）；只记 request_id/subtask_id/capability_id/decision_by/TTL 余量/resume_mode，不记参数原值。
6. **无状态恢复纪律（v1 新增 · 承终局 §4 :83 SPEC 级锁死）**：任何时候不得引入「恢复依赖进程内存」的挂起态——resume（含自动 resume 与补偿扫描）一律从事件表/DB 重建；进程内后台任务只是**触发器**，不是状态载体；进程重启不丢任何待恢复审批（补偿扫描兜底）。破坏此条 = 红线退回。

---

## 2. 范围（D 块展开）

### D1 · 审批消费门（缺口 1 · 必做）

- **消费点**：`nodes.py::_delegation_issue_block_reason`（:277-295）——`auto_approve_ok` 判出需审批后、返回 HITL 原因前，先查 HITL store 有无**匹配 approved 单据**；命中 → 返回 `None`（放行签发）+ 台账 `delegation_approval_consumed`；未命中/异常 → 维持拦截（fail-closed）。
- **消费键（Q1 裁定）**：`(run_id, subtask_id, capability_id)` 三元组精确匹配。`capability_id` 由 `_persist_hitl` 落库时 `payload`（jsonb）增记（零迁移）；**旧单据缺该键 → 不消费**（fail-closed）。
- **时效（Q5 裁定 · v1 吸收 R1-N3）**：`decided_at + TTL < now` → 不消费（读时判过期 · 不写状态）。env `OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS` 默认 3600，**合法域 [1, 86400]**（承 `delegation.py:107` `_env_int` low/high 先例），非法/越界回退默认。
- **双 store 类型归一（v1 吸收 R1-N4）**：`decided_at` 在 InMemory store 为 float 时间戳、Db store 为 datetime（store.py:98 vs :159-163）——消费端统一归一为可比时间戳后再做 TTL 比较；归一函数落消费助手内，双 store 各一组 TTL 断言（A2）。
- **单据类型守卫**：仅消费 `blocked_by=delegation_issue_hitl_required` 类单据；`prefix_touch_required` 语义不动。
- `auto_approve_ok` 保持**纯函数零 IO**（Q2）：消费读写在 nodes.py 编排层（async 助手），不进 capability 包。

### D2 · unlock_subtask_id 空形态回填（缺口 2 · 必做）

- `_persist_hitl`（nodes.py:1440-1445）：当 `depends_on ∩ plan_prefix_ids` 为空 **且** `blocked_by=delegation_issue_hitl_required` → `unlock_subtask_id = 被拦 sid 自身`（批准=授权（重）下发该被拦步骤 · 与 D1 消费配对成环）。
- **形态守卫**：仅限 delegation_issue 类；`prefix_touch_required` 类空 unlock 维持现状（router 409 保留 · 人可解的明确报错 · 不静默放行）。
- `router.py:404-411` 409 守卫**保留不动**：D2 让该形态不再产生空 unlock，而非放宽 409。
- resume 成环路径：approved=[sid] → `hitl_unlocked_ids=[sid]` → `_locked_prefix`（nodes.py:550-567）摘除 → replan/carry 重下发 sid → D1 消费放行 → 令牌签发 → 执行 → `done{completed}`。

### D3 · strategy 候选 map env 口（缺口 3 · 必做）

- `strategy/config.py` 增 env 追加集 `OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS`（逗号分隔 · strip · 去空去重 · **默认不设=解析结果对 master 逐字节零 diff**）。
- `get_candidate_capability_ids` 在 map 解析结果后追加 env 集（含未知 key · env 是运维显式声明 · fail-closed 管默认不管显式 · Q4）。
- **下游闸全链不动**：candidates 仍经 ∩visible（builder.py:177-182）；deny 判序、Policy 写闸、`_subtasks_have_valid_tool_ids` 照旧——env 只抬候选层，不是放行口。
- env 生效记台账（候选 id 列表 + 基数 · 配置非敏感）。

### D4 · 审计与测试（必做）

- 台账新动作：`delegation_approval_consumed` · 消费读取失败 warning · env 追加集生效记录 · `hitl_auto_resume_triggered` / `hitl_auto_resume_claimed` / `hitl_auto_resume_compensated`（D5 三件套 · 记动作不记内容）。
- 测试按 §6 验收 A1–A10 逐条断言化。

### D5 · 批准后自动继续（可配置面 · 必做 · v1 新增 · 承终局 §4 :82）

- **可配置两级（Q7 裁定）**：
  - 全局默认 env `OPS_HITL_AUTO_RESUME`：`manual`（默认 · 现状语义零 diff）/ `auto`；非法值回退 `manual`（fail-closed）。
  - 审批单级覆盖：decide 端点请求载荷增**可选键** `resume_mode` ∈ {`inherit`, `immediate`, `manual`}（缺省=`inherit` 用全局默认）；**键白名单 + 未知值 400**（fail-closed · 既有调用不带该键行为同现状零 diff）。
- **触发器（Q6 裁定）= 进程内后台任务**：decide(approved) 持久化成功后，若有效模式=auto 则派发进程内 asyncio 后台任务，走**与手动 resume 同一条恢复路径**（resume.py · 从事件表重建 · 无状态恢复纪律）。
- **多副本防重（钉死）**：api 多副本形态（task_multi_replica_verify 先例）下，自动 resume 执行前以 PG 行锁认领（`SELECT … FOR UPDATE SKIP LOCKED` 或等价）防重触发；重复触发幂等（resume 状态机守卫：非 pending/unlocked 态重入无副作用 · 断言化）。
- **补偿扫描兜底（钉死）**：启动时 + 定时扫「已批准未恢复」单据（approved 且未过 TTL 且 run 未终态），行锁认领后补触发；进程重启零丢失（触发器不载状态）。
- **手动模式保留**：`manual`（默认）下行为与现状完全一致——POST resume 端点路径不动，D2 回填后 resume 200 可达 `done{completed}`。
- **判定逻辑零改 + 不循环**：自动 resume 只是「代替人点 resume」，D1 消费门语义不变；auto 模式下若重下发仍被拦（如单据过期/键不匹配）→ 回到挂起态等人，**单次 decide 最多触发一次自动 resume**，台账留痕。

---

## 3. 非范围

- ❌ **HITL 挂起机制与 decide 落库本身**：interrupt/resume 回路、`adecide` 守卫（只受理 pending · 重复 decide 409）、状态机一行不动。边界澄清：`_persist_hitl` unlock 计算修正（D2）与 payload jsonb 增记 capability_id（D1）属接线修补在范围内——零迁移、既有读取兼容、不改守卫与状态语义；decide 载荷增**可选键**（D5）不改既有键语义（v0 字据存续 · R1 裁定 1 PASS）。
- ❌ UI 不动（前端/审批列表/SSE 事件类型零新增）。
- ❌ deny_write/deny_high_risk 判序、Policy 写闸、gateway 闸链（§1 设计纪律 1/2）。
- ❌ 撤销端点/审批中心改造（消费语义按「读时活状态」设计 · 与未来撤销天然兼容）。
- ❌ `auto_approve_ok` 三条件语义放宽（只读自动边界不动）。
- ❌ 新表/新列（jsonb 增键零 alembic）；跨进程消费缓存（每判定读 store 活值 · 微优化另议）。
- ❌ session 级/租户级持久授权（消费键锁 run 级 · 更大半径 v2 另议）。
- ❌ **MQ/外部调度器/独立轮询工人引入**（v1 新增 · 终局「不需要 MQ」决议 · Q6 双弃理由在案）。
- ❌ 自动 resume 的 LLM 结果质量兜底（auto 恢复后 replan 质量属图既有语义 · 本波只保证机制可达）。

---

## 4. 开放裁定（必答题 · 全部作答 · 留 20-spec-audit R2 复核）

### Q1 · 消费键粒度

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · (run_id, subtask_id, capability_id) 三元组** | payload 增记 capability_id · 读时精确匹配 | 半径最小；旧单据缺键 fail-closed | 落库载荷增一键 | **裁定（v0 存续 · R1 裁定 1 PASS）** |
| S2 · 仅 (run_id, subtask_id) | 不动落库载荷 | 零写路径改动 | 同 sid 换 tool 校验弱 | 弃选 |
| S3 · (thread_id, capability_id) 会话级 | 一批整会话放行 | 人少点几次 | 半径爆炸 · 与 run 级授权纪律冲突 | 弃选 |

### Q2 · 消费点位置

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · nodes.py 编排层消费（async 助手）** | 判定链前置消费读；`auto_approve_ok` 保持纯函数 | 守 capability 包零 IO 纪律；store 异常 fail-closed 留痕 | nodes 调用面 async 化小改（波及面仅 nodes.py:711 + 一处 sync 测试直调 tests/test_capability_testing_write.py:492 · R1-N2 · 移交 task 点名） | **裁定（v0 存续 · R1 裁定 3 PASS）** |
| S2 · 改 `auto_approve_ok` 增第四条件 | 消费进 capability 包 | 调用点不变 | 破坏纯函数纪律 · sync 装不下 async store 读 | 弃选 |

### Q3 · unlock 空形态回填语义

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · 无前驱前缀时 unlock=被拦 sid 自身 + 形态守卫** | 仅 delegation_issue 类回填；router 409 保留 | resume 走通且语义显式；409 假动作防线不拆 | 解锁语义扩展（由 D1 消费配对成环） | **裁定（v0 存续 · R1 裁定 4 PASS）** |
| S2 · router 放行空 unlock | approved 空集也恢复 | 零写路径改动 | 静默按驳回收工 | 弃选 |

### Q4 · 候选 map env 口形态

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · env 追加集（逗号分隔 · 默认空）** | map 解析后追加；下游 ∩visible/Policy 不动 | 默认零 diff · 运维显式 | 需钉死「只抬候选层」测试 | **裁定（v0 存续 · R1 裁定 5 PASS）** |
| S2 · env JSON 覆盖整 map | 全量改写候选 | 灵活 | 易误伤默认只读集 · 难审计 | 弃选 |
| S3 · 复用 `CANDIDATE_CAPABILITY_IDS` 全局覆盖 | 零新代码 | — | 半径过大 · 定位是测试钩子（config.py:25-26 注释明示） | 弃选 |

### Q5 · 批准时效语义

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · decided_at+TTL 读时判过期（默认 3600s · 域 [1,86400] · 双 store 归一后比较）** | 不写状态 · 消费时计算 | 防囤批；models.py:481 预留语义位 | 长审批超 TTL 需重批（可配） | **裁定（v0 存续 · v1 吸收 N3/N4 · R1 裁定 2/6 PASS）** |
| S2 · 永久有效 | 不判过期 | 最省 | 永久后门 | 弃选 |
| S3 · 一次性消费写回状态 | 消费后翻转单据 | 语义最严 | 越非范围 · replan 重下发被二次拦 | 弃选（留 v2） |

### Q6 · 自动 resume 触发器选型（v1 新增 · 承终局 §4 :82 三选一）

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · 进程内后台任务 + PG 行锁认领 + 补偿扫描** | decide 后派发 asyncio 任务走 resume 同路径；启动/定时扫「已批准未恢复」兜底；`FOR UPDATE SKIP LOCKED` 防多副本重复 | 零新部署单元；无状态恢复纪律原生兼容（触发器不载状态）；补偿幂等 | 进程内任务不持久 → 由补偿扫描兜住（这正是设计） | **裁定** |
| S2 · PG 轮询工人（独立部署单元） | 新服务/进程专责轮询 | 职责清晰 | P1 阶段零新增服务纪律冲突；运维面+1 | 弃选 |
| S3 · PG LISTEN-NOTIFY 推送 | DB 通知触发 | 实时 | 连接生命周期管理复杂 · 丢通知面大 · 与终局「不需要 MQ」精神相悖 | 弃选 |

### Q7 · 自动/手动配置面形态（v1 新增 · 承终局 §4 :82「全局默认 + 可按审批单覆盖」）

| 方案 | 做法 | 收益 | 代价 | 裁决 |
|---|---|---|---|---|
| **S1 · 全局 env + decide 载荷可选键 `resume_mode`** | `OPS_HITL_AUTO_RESUME`=manual/auto（默认 manual 零 diff）+ 单据级 inherit/immediate/manual | 终局裁定原样落地；默认现状零 diff；未知值 fail-closed | decide 载荷增一键（白名单校验） | **裁定** |
| S2 · 仅全局 env（无单据级） | 一刀切 | 最省 | 违反终局「可按审批单覆盖」裁定 | 弃选 |
| S3 · 仅单据级（无全局默认） | 每次 decide 必填 | 显式 | 破坏既有调用零 diff · 运维无默认面 | 弃选 |

---

## 5. failure_paths

| # | 路径 | 裁定 |
|---|---|---|
| FP-1 | 消费读 store 失败（DB 抖动/异常） | **fail-closed**：视同无批准 · 维持拦截 + warning 台账 |
| FP-2 | 批准过期/囤积 | TTL 读时判过期不消费；env 非法/越界（[1,86400]）回退默认 3600；过期重走挂起→审批 |
| FP-3 | replan 换 subtask_id 致消费键不命中 | 再挂起重批（新步骤=新授权）；`_carry_plan` 沿用 id 形态可命中 · 断言化 |
| FP-4 | unlock=自身被误用到其他 blocked_by | 形态守卫仅 `delegation_issue_hitl_required`；`prefix_touch_required` 空 unlock 维持 router 409 |
| FP-5 | env 口注入高危/写 id | 下游 ∩visible + deny_high_risk（判序在前）+ Policy 写闸全链仍在；断言「env 含高危 id 仍被裁」 |
| FP-6 | 同批多申请部分批准 | `_collect_decisions`（router.py:287-316）既有汇总不动；逐条匹配；重复 decide 409 原样绿 |
| FP-7 | delegation off/observe 模式语义 | off：消费与自动 resume 零触达；observe：本就不拦 · 不记假台账；仅 enforce 下改变判定 |
| FP-8（v1） | 自动 resume 重复触发（decide 重入/多副本并发） | PG 行锁认领防重 + resume 状态机守卫幂等（非 pending/unlocked 重入无副作用）· 并发双触发仅一执行断言 |
| FP-9（v1） | 触发进程崩溃/重启致自动 resume 丢失 | 补偿扫描（启动时+定时）兜底认领补触发；触发器不载状态（无状态恢复纪律）· 断言「重启后已批准未恢复单据被补触发」 |
| FP-10（v1） | `resume_mode` 覆盖键滥用/未知值 | 键白名单 + 未知值 400；载荷缺键=inherit；非法全局 env 回退 manual；覆盖记录入台账（decision_by + resume_mode） |
| FP-11（v1） | 自动 resume 后仍被拦（单据过期/键不匹配） | 单次 decide 最多触发一次；回到挂起态等人 · 不循环自动触发；台账留痕 |

---

## 6. 验收标准（可机验）

1. **A1 消费放行**：store 预置匹配 approved 单据（三元组命中 · decided_at 新鲜）→ 重下发同 tool 签发判定返回 `None`（不再产出 `delegation_issue_hitl_required`）· 台账含 `delegation_approval_consumed`（pytest 断言）。
2. **A2 消费边界否定断言（变异式）**：pending/rejected 不生效；超 TTL 不生效（**InMemory + Db 双 store 各一组** · decided_at 类型归一断言 · v1 吸收 N4）；三元组任一不匹配不生效；payload 缺 capability_id 旧单据不生效；store 读异常 → 维持拦截 + warning。
3. **A3 单子任务形态 resume 成环（手动模式）**：`_persist_hitl` 对无前驱前缀 delegation_issue 拦截算出 `unlock_subtask_id=sid`；机制段 pytest 集成：decide(approved) → resume 200 → 图恢复 → `done{completed}`；live HTTP/SSE 全链（三 env 组 + 新 env · 无 shim）留 40 复跑。
4. **A4 env 口**：不设 → `get_candidate_capability_ids` 各 key（含未知 key）解析结果对 master 逐字节一致；设 env → candidates 含追加 id 且 ∩visible/stripped 语义不变；env 含高危/写 id 仍被下游裁（FP-5 断言）。
5. **A5 反回归钉死**：`registry.py::_match_filter` 与 `policy.py` 闸序段 git diff 为空；`test_allow_tags_does_not_waive_deny_write` 及 capability/hitl 既有测试原样绿；审批消费不过 gateway/Policy 断言（写能力执行仍须写确认口径）。
6. **A6 off 零 diff**：`LG_RAG_DELEGATION_TOKEN_MODE=off` 下消费/自动 resume 路径零触达（无 store 读 · 无新台账 · 无后台任务行为差 · 既有 delegation/hitl 测试原样绿）。
7. **A7 decide 落库不动**：`store.py` `adecide`/`_DECIDE` git diff 为空；重复 decide 409 守卫原样绿（`test_hitl_pending_decide`）；router.py:404-411 409 守卫保留断言。（v1 注：decide 端点载荷增可选键属 D5 范围内 · 既有键语义 diff 为空）
8. **A8 工程面**：`pytest tests` 全绿；`ruff check` 触及路径零新增；`./scripts/graph-compile.sh` EXIT=0；图谱 `capability`/`lg_rag`/`hitl`/`strategy` 四行备注回写 + HG-GRAPH-MODULES 00 代录行。
9. **A9 自动 resume 全链（v1 新增 · handoff 验收令「A1 第四段补全实录」）**：`OPS_HITL_AUTO_RESUME=auto`（或单据级 `resume_mode=immediate`）下，plans 含写 tool 的 run → hitl.waiting → pending 可见 → decide(approved) → **无需手动 resume** → 自动恢复 → 终态 `done{completed}` 全真可达；pytest 集成断言（触发+消费+终态）+ live HTTP/SSE 实录留 40（本波必须达成 · D2 留的正是这段）。
10. **A10 无状态恢复钉死组（v1 新增）**：恢复路径（手动/自动/补偿扫描）只读事件表+DB（grep/审查断言无进程内存挂起态载体）；补偿扫描幂等断言（重复扫描不重入非 pending 态）；行锁认领断言（并发双触发仅一执行）；`resume_mode` 未知值 400 与非法 env 回退 manual 断言。

---

## 7. 思考轮回填（R0–R5 · v1 增量）

- **R0（读人聊/目标）**：v0 轮次存续（维护者裁定 + 30/40 invoke 全文 + 全锚点复核 ca4148f）；v1 增量 = handoff PROMPT 全文 + 终局文档 §4 :81-83 实读 + R1 审查文六裁定与 N1–N4。
- **R1（范围/非范围）**：v0 存续；v1 增 D5（decide 载荷可选键/触发器/补偿扫描/行锁）与第四立案；非范围增 MQ/外部调度器与 LLM 结果质量兜底两条。
- **R2（方案对比）**：v0 Q1–Q5 存续（全部 ≥2 案 · R1 复核 PASS）；v1 增 Q6（触发器三选一 · 进程内后台任务裁定 · 双弃有机制性理由）与 Q7（配置面三案 · 全局+单据双级裁定）。
- **R3（边界/失败路径）**：v0 FP-1~FP-7 存续；v1 增 FP-8~FP-11（重复触发幂等/崩溃兜底/覆盖键滥用/auto 后仍拦不循环）。
- **R4（验收/可测性）**：v0 A1–A8 存续性逐条确认（A2 增双 store TTL · A7 注 decide 载荷键边界）；v1 增 A9（auto 全链 done{completed} · handoff 验收令）与 A10（无状态恢复钉死组）；test_strategy=required 存续。
- **R5（签收就绪）**：开放裁定 Q1–Q7 无遗留；交 20-spec-audit R2 书面审 → 维护者签 HG-SPEC-SIGNOFF（00 依授权代录留痕）→ 00 拆 task。
- **过程留痕**：v1 骨架由子 Agent 落盘（90 行占位）· 全文由 00 代笔填充（两棒子 Agent 长文档生成卡滞 · interrupt 两次留痕 · 本 SPEC 为过程文档非实现码 · 维护者「授权00签收所有过程文档」+「今晚完成你可以自主判断完成的部分」令覆盖 · 详情见修订 invoke）。

### 思考轮控制

| 轮 | 状态 | 说明 |
|---|---|---|
| R0 | done | v0 存续 + handoff/终局 §4/R1 审查文实读 |
| R1 | done | D5 范围 + 非范围两条新增锁定 |
| R2 | done | Q6/Q7 ≥2 案对比 + 裁定 |
| R3 | done | FP-8~FP-11 裁定 |
| R4 | done | A9/A10 新增 + A1–A8 存续确认 |
| R5 | done | 交 20-spec-audit R2 → HG-SPEC-SIGNOFF（00 代录）→ 拆 task |
| early_stop | no | — |

---

## 8. 关联

- 上游 SPEC：[`SPEC-host-v1-delegation-token_v0.md`](../host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md)（signed · Q2 审批口径 / D5 scope / FP-2 墙钟纪律）
- 上游路线：[`DESIGN_agent_contribution_endgame_v0_zh.md`](../../guides/DESIGN_agent_contribution_endgame_v0_zh.md)（§4 :82-83 自动/手动可配置 + 无状态恢复纪律 · P0–P3 路线 · 16 点查漏补缺）
- handoff：[`PROMPT_00_hitl-consumption-loop-handoff_20261009.md`](../../harness/invokes/by-task/_prompts/PROMPT_00_hitl-consumption-loop-handoff_20261009.md)（第一棒链路与验收令）
- 源证据：[`30 invoke r2`](../../harness/invokes/by-task/testing-write-capability/invoke_20261009_30_implement_r2_testing-write-capability.md) · [`40 invoke`](../../harness/invokes/by-task/testing-write-capability/invoke_20261009_40_verify_testing-write-capability.md)
- v0 审查：[`spec_hitl-approval-consumption_audit_R1_20261009.md`](../../harness/reviews/spec_hitl-approval-consumption_audit_R1_20261009.md)（PASS-WITH-NITS · N1–N4 处置见 §2/§6 与修订记录）
- 代码锚点：`delegation.py:488-514,107` · `nodes.py:277-295,550-567,711,1397-1471` · `router.py:287-316,404-411` · `store.py:89-94,98,130-138,159-163` · `strategy/config.py:14-45` · `builder.py:177-182` · `registry.py:112-140` · `policy.py:96-105` · `models.py:449-487`
- 图谱：`docs/_tech_graph/l1/01_modules.md`（capability/lg_rag/hitl/strategy 行 · 回写义务见 Harness 元信息）

## 修订记录

| 日期 | 版本 | 内容 |
|---|---|---|
| 2026-10-09 | v0 | 10-spec 初稿：三实证缺口锚定 30/40 invoke 行号展开 D1–D4；Q1–Q5；FP-1~FP-7；A1–A8；R0–R5；HG-SPEC-SIGNOFF=pending（20-spec-audit R1 PASS-WITH-NITS · 留转六条全 PASS · N1–N4） |
| 2026-10-10 | v1 | handoff 令退回修订：补终局 §4 两裁定——D5 批准后自动继续可配置面（触发器=进程内后台任务+PG 行锁认领+补偿扫描 · 全局 env `OPS_HITL_AUTO_RESUME` 默认 manual + decide 载荷可选键 `resume_mode` 白名单 fail-closed）+ 无状态恢复纪律锁死（设计纪律 6）；Q6/Q7；FP-8~FP-11；A9（auto 全链 done{completed} · handoff 验收令）/A10（无状态恢复钉死组）；吸收 R1-N3（TTL 域 [1,86400]）/N4（decided_at 双 store 归一 · A2 双断言）；N1/N2 移交 task 阶段；骨架子 Agent 落盘 + 全文 00 代笔（卡滞留痕见修订 invoke） |
