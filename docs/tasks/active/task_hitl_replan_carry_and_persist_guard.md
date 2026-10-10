# Task：hitl-replan-carry-and-persist-guard（replan 保号 approved 步骤 + _persist_hitl 建单前检查 · 消费键可命中 · 防孤儿 pending）

> **状态**：`draft`（2026-10-10 · 10 骨架先行落盘 · 三人工闸 pending）
> **类型**：**SPEC 承接后续裁定**（SPEC v1 FP-3 偏差实证后维护者裁定落地 · 源证据=T1/T2 40 invoke live 实录）
> **分支**：`task/hitl-carry-and-persist-guard`（worktree t-hitl-carry-and-persist-guard · base：`master` bdd45f9 · 含 T1/T2 merge · 禁止 master 直改）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `hitl-replan-carry-and-persist-guard` |
| **git_branch** | `task/hitl-carry-and-persist-guard` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | pytest 机制段为主：保号断言（supervisor replan 三路径——正常 LLM/fallback/空 allowlist 短路——unlocked 步骤原 sid 带回 · LLM 新步骤照常盖章 · 非 unlocked 不保号变异断言 · unlocked 为空时与 master 对拍零 diff）+ 消费命中成环断言（approved 在场 → 保号 replan → 消费门命中 → 不再二次拦截 → done{completed} 机制段可达）+ 建单前检查断言组（approved 在场零建单 / 无 approved 照建 / 过期·缺键·cap 不符·blocked_by 不符照建 / 读异常 fail-open 照建+warning · InMemory+Db 双 store）；live HTTP/SSE 全链复跑（done{completed} 可达）留 40 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1`（行备注 · 不新增一级模块） |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` lg_rag / hitl 两行在册备注（保号机制 + 建单前检查） |
| **graph_delta_note** | 模块边界不变：lg_rag 模块内 supervisor replan 增保号段 + observe 落库增建单前检查（均 nodes.py 内增量）；hitl 行备注 guard 复用消费门 TTL/归一语义说明 → G-L1 行备注同步，HG-GRAPH-MODULES 随 30 回写由 00 代录 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | SPEC 承接裁定落地 task · 机制接线增量无 wiki 条目变更 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20 R1 → 维护者签 → 30 → 40（含 live 复跑）→ PR+CI 绿 → 图谱回写 → CLOSE |
| **freeze_id** | 无（零新表/零新列 · payload jsonb 不增键 · 零新 SSE 事件类型 · 零 alembic） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 维护者签 · 00 代录 2026-10-10（授权「授权00签收所有过程文档」） · lint PASS · R1 N-1/N-2 已同批顺手补 |
| HG-AUDIT-R1 | **approved** | 30 | 维护者签 · 00 代录 2026-10-10（授权「授权00签收所有过程文档」） · 依据 R1 PASS（reviews/task_hitl_replan_carry_and_persist_guard_audit_R1_20261010.md · N-1~N-3 非阻塞） |
| HG-GRAPH-MODULES | **approved** | 30 | 维护者签「在册」（lg_rag/hitl 行备注段）· 00 代录 2026-10-10 · 30 回写义务在案 |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | 非物理分层试点 task |

---

## 背景与目标

消费回路（T1 消费门 + T2 auto resume）机制面已全链闭合，但两条 live 实证偏差使 `done{completed}` 末段不可达，维护者裁定（2026-10-10）立项修复：

1. **replan 重盖章使消费键失配**（T1 40「重要发现」· `docs/harness/invokes/by-task/hitl-approval-consumption-loop/invoke_20261010_40_verify_hitl-approval-consumption-loop.md` :31-40）：resume 后 supervisor 走 LLM 正常重规划 → `_stamp_host_plan` 重盖 sid（live 实证 :1→:2→…→:11 逐轮递增）→ 消费键 `(run_id, subtask_id, capability_id)` 永不命中 → FP-3 再拦循环（每轮 decide+resume 均 200 但 `done{completed}` 不可达）。`_carry_plan` 沿用 id 形态只在 LLM 重规划失败/非法时触发（nodes.py:1017-1054）；T2 40 live 复跑逐点吻合（run dbc0fc74 · sid :1→:2 · 全程零 `delegation_approval_consumed` 台账）。
2. **resume 重放留孤儿 pending**（T2 40 附带观察 · invoke :55-57）：LangGraph resume 时 observe 节点从头重放，`_persist_hitl`（nodes.py:1727）在 `interrupt()`（:1736）返回恢复值**之前**按旧状态为已批准 sid 重建 pending（实证 `hitl_5cefb116:1` · 不进任何 hitl.waiting 帧 · 污染 pending 列表 UX 与 auto resume 补偿扫描「同 run 无未决 pending」判定的输入纯度）。

**维护者裁定（2026-10-10 · 逐字）**：

> 1. **保号**：resume 后 approved 步骤在 replan 中**保留原 subtask_id**（不重盖章）——正常 replan 路径也要保号 approved/unlocked 步骤，使消费键 (run_id, subtask_id, capability_id) 可命中 · live done{completed} 可达
> 2. **建单前检查**：_persist_hitl 建单前查「该 (run_id, subtask_id) 是否存在新鲜（未过 TTL）approved 单据」→ 有则跳过建单（防孤儿 pending）

**一句话目标**：① supervisor replan 全路径对 `hitl_unlocked_ids`（approved 解锁）步骤**保号**——原行原 `subtask_id` 带回，LLM 自由规划的新步骤仍正常盖章新 id，消费键可命中，live `done{completed}` 可达；② `_persist_hitl` 建单前检查——同 `(run_id, subtask_id, capability_id)` 存在新鲜 approved 单据则跳过建单（防孤儿 pending），检查读异常 **fail-open 照建 + warning**（裁定见钉死契约五）。

---

## 现状锚点（只读 · 30 必读 · 10 已逐行实读 · base `bdd45f9`）

| 锚点 | 实证 |
|------|------|
| `app/ops/lg_rag/multi/nodes.py:630-673` | `_stamp_host_plan(state, items, locked)`：locked 前缀**原行原 id 保留**（:638 `locked_rows` · :650 `full = locked_rows + plan`）；仅 LLM 项经 `_issue_plan` 盖章新 id（:642-649 · seq 自 `host_subtask_seq` 递增——**这就是 sid :1→:2→:11 递增的机械来源**）；`plan_prefix_ids`=locked ids · `recoverable_point`=len(locked)（:657-658） |
| `app/ops/lg_rag/multi/nodes.py:676-693` | `_locked_prefix`：成功终态进步前缀；**:688 `hitl_unlocked_ids` 被摘出前缀**——approved 步不再受保护、可重跑（「批准的唯一效果」）· 保号面正落在被摘出的这批步骤上 |
| `app/ops/lg_rag/multi/nodes.py:696-715` | `_unresolved_suffix(state, locked)`：未解决后缀**原行原 id 带回不重新签发**（:702-704 docstring 钉理由）——approved 步旧结果已被剪掉（:1687-1689）故天然落在未解决集内 |
| `app/ops/lg_rag/multi/nodes.py:718-734` | `_carry_plan`：前缀+未解决后缀沿用 · **不重新签发 subtask_id**（:721）——保号语义的既有载体（当前仅 fallback 路径触发） |
| `app/ops/lg_rag/multi/nodes.py:960-1054` | supervisor replan 三路径：空 allowlist 短路 :963-977（`items=[] if locked` · 仍走 `_stamp_host_plan`）；LLM 正常规划 :990-1009 → :1054 盖章；LLM 失败 fallback :1017-1051（仅此处走 `_unresolved_suffix`+`_carry_plan` 保号）。**保号须覆盖三条路径**（钉死契约二） |
| `app/ops/lg_rag/multi/nodes.py:1644-1701` | `_apply_hitl_decision`：approved ∪ 既有 → `hitl_unlocked_ids`（:1671-1676）；剪掉 approved 步旧结果（:1687-1689 `keep = plan_ids - approved`）⇒ approved 步在 replan 时**必为未解决态**（保号集合的操作定义依据） |
| `app/ops/lg_rag/multi/nodes.py:268-278` | `_approval_consumption_ttl_seconds()`：env `OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS` 默认 3600 · 域 [1,86400] 非法回退——建单前检查**复用同一 TTL**（T2 auto_resume 已复用 · auto_resume.py:92-96 先例） |
| `app/ops/lg_rag/multi/nodes.py:281-301` | `_decided_at_ts`：float（InMemory）| ISO 8601 str（Db 经 `_row_to_dict`）双型归一 · 不可归一返 None——建单前检查**复用同一归一** |
| `app/ops/lg_rag/multi/nodes.py:318-372` | `_approval_consumed`（D1 消费门）：`alist(status="approved", limit=200)` + blocked_by 守卫（:347 仅 `delegation_issue_hitl_required`）+ 三元组精确匹配（:349-357 · 旧单据缺 `capability_id` 键 fail-closed）+ 读时 TTL（:358-363）——建单前检查的**匹配语义镜像源** |
| `app/ops/lg_rag/multi/nodes.py:395-421` | `_delegation_issue_block_reason`：消费门调用点 :419（sync 判定需审批后 · 返拦截原因前消费）——**本 task 零改**（钉死契约七） |
| `app/ops/lg_rag/multi/nodes.py:1523-1611` | `_persist_hitl`：pending 去重以 `(run_id, subtask_id)` 为幂等键读 store（:1544-1555 · 去重读失败退回 state 不崩 :1554-1555——**fail-open 先例在案**）；D2 空形态 unlock=sid 回填（:1572-1578）；payload 增记 `capability_id`（:1579-1585 · 真源 `term.get("tool")` :1583）；建单 `acreate` :1601——**建单前检查挂点 = :1558 循环内 `acreate` 之前** |
| `app/ops/lg_rag/multi/nodes.py:1704-1744` | `observe_node`：落库先于挂起（:1725-1727 docstring 钉理由）→ `interrupt()` :1736——resume 重放时节点从头重跑 · `interrupt()` 直接返回 resume 值（:1739-1740）· **重放期 `_persist_hitl` 按旧状态重建孤儿 pending 的机械来源** |
| `app/ops/lg_rag/state.py:239,279` | `hitl_unlocked_ids: list[str]` state 键（已批准授权重跑步骤集） |
| `app/ops/hitl/store.py:55/161` | `InMemoryHitlStore`/`DbHitlStore` 双 store（`alist` :76/:255）——建单前检查断言须双 store 各一组（承 T1 A2 口径）；**既有方法 diff 空**（guard 只读复用 `alist`） |
| `app/ops/hitl/auto_resume.py:92-96` | `_approval_ttl_seconds` 已复用 `_approval_consumption_ttl_seconds`——TTL 单一真源先例 |
| T1 40 重要发现 | `docs/harness/invokes/by-task/hitl-approval-consumption-loop/invoke_20261010_40_verify_hitl-approval-consumption-loop.md` :31-40（sid 递增实证 · FP-3 循环 · carry 触发条件实读） |
| T2 40 live+观察 | `docs/harness/invokes/by-task/hitl-approval-consumption-auto-resume/invoke_20261010_40_verify_hitl-approval-consumption-auto-resume.md` :48（sid :1→:2 · 零消费台账 · done 不可达）· :55-57（孤儿 pending `hitl_5cefb116` · nodes.py:1725-1727 机制实读） |
| SPEC v1 | `docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` :77（Q1 消费键三元组 + 缺键 fail-closed）· :193（FP-3 原裁定「carry 沿用 id 可命中」——live 实证推翻其覆盖假设 · 本 task=裁定修正落地） |

---

## 钉死契约（30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **一 · 保号集合** | 保号集合 P = `hitl_unlocked_ids` ∩ 未解决步骤（无终态 · approved 步旧结果已被 `_apply_hitl_decision` :1687-1689 剪掉 ⇒ 天然未解决）。保号 = **原行原 `subtask_id` 带回**（承 `_carry_plan` :718-734 语义）；locked 前缀本已原样保留（:638）一行不动；**LLM 自由规划的新步骤仍经 `_issue_plan` 正常盖章新 id**（seq 递增存续 · :642-649）——「仅 approved 解锁步骤保号 · 其余照常盖章」为维护者裁定字面钉 |
| **二 · 保号路径全覆盖** | supervisor replan **三条路径**均保号：正常 LLM 成功（:1054 stamp 前把 P 注入带回段）· LLM 失败 fallback（:1017-1051 既有 carry 面 · P ⊆ unresolved 已自然含 · 行为可归一）· 空 allowlist 短路（:963-977）。保号步骤置于 locked 前缀之后、LLM 新后缀之前；**`plan_prefix_ids` 仍仅 = locked · `recoverable_point` = len(locked) 不变**（P 可执行 · 非前缀 · 不重跑保护不扩散） |
| **三 · 空 unlocked 零 diff** | `hitl_unlocked_ids` 为空时，replan 输出（`subtasks`/`host_subtask_seq`/`plan_prefix_ids`/`recoverable_point`/`subtask_results` 修剪面）与 master 对拍**逐字节一致**——无 approved 解锁的旧形态零行为差（反回归机断断言） |
| **四 · 建单前检查匹配语义** | `_persist_hitl` 在 `acreate`（:1601）之前，对每个待建 sid 查 store approved 单据，匹配语义**镜像消费门**：blocked_by==`delegation_issue_hitl_required` 守卫（:347 同型）+ `(run_id, subtask_id, capability_id)` 三元组（capability 真源 = `term.get("tool")` :1583 同源）+ `decided_at` 归一复用 `_decided_at_ts` + 读时 TTL 复用 `_approval_consumption_ttl_seconds`（禁第二份 TTL/env 解析实现 · auto_resume.py:92-96 复用先例）。命中 → **跳过建单**（该 sid 不产新行） |
| **五 · fail-open 裁定** | 检查读异常 → **照建单 + warning 台账**（新台账键**钉死** `hitl_persist_guard_read_failed` · 记动作不记内容 · 承 delegation 台账纪律 · 30 不得改名 —— TB6⑤ 按字面断言）。**裁定理由**：漏建单 = 人干等一个不存在的审批（`_persist_hitl` docstring :1526-1529 既有红线）；fail-closed 会在 DB 抖动时抑制合法 pending 致死等，孤儿 pending 只是 UX/判定输入污染——两害相权建单为 fail-safe 方向；且 `_persist_hitl` 既有去重读失败「退回只认 state 不崩」（:1554-1555）已是同向先例。**维护者建议原话即「fail-safe 建单 + warning」，本 task 裁定采纳** |
| **六 · 旧单据交互** | approved 单据缺 `capability_id` 键（T1 前旧格式）→ guard **不匹配**（fail-open 照建）· 与消费门缺键 fail-closed（:356-357）语义同构——旧单据场景退化为既有「再挂起重批」形态，**不扩面 · 不 Backfill**；payload 不增新键（零迁移存续） |
| **七 · T1/T2 存续** | 消费门 `_approval_consumed`/`_delegation_issue_block_reason` 判定零改（guard 在 persist 侧 · 消费门在签发侧 · 两面独立）；`auto_resume.py` 触发器/行锁认领/补偿扫描零改；`store.py` 既有方法 diff 空（guard 只读复用 `alist`）；deny 判序/Policy 写闸/gateway 闸链零触；`resume.py` 恢复链零改 |
| **八 · interrupt 语义不动** | guard 跳过建单**不改** `obs["hitl_pending"]` 与 `interrupt()` 调用结构（resume 重放时 `interrupt()` 直接返回 resume 值 · :1736-1740 · 载荷不重演）；`_persist_hitl` 返回值须把「已存在 pending」照常带回（:1559-1563 既有形态存续）；guard 跳过的 sid 不产生新行也不伪造行 |

---

## 范围

> 仅在 `task/hitl-carry-and-persist-guard` 分支修改以下路径（禁改实现码之外的任何范围外文件）：

| 路径 | 改动性质 |
|------|----------|
| `app/ops/lg_rag/multi/nodes.py` | **① replan 保号**：supervisor replan 三路径（:963-977/:990-1054/:1017-1051）对 `hitl_unlocked_ids` ∩ 未解决步骤保留原 `subtask_id`（原行带回 · 置于 locked 前缀之后 LLM 新后缀之前）；**② 建单前检查**：`_persist_hitl` `acreate`（:1601）之前增 approved 新鲜单据检查（匹配语义镜像 `_approval_consumed` :318-372 · TTL 复用 `_approval_consumption_ttl_seconds` · 归一复用 `_decided_at_ts` · 读异常 fail-open 照建 + `hitl_persist_guard_read_failed` warning 台账）——**仅本文件 · 不新增模块/助手函数出文件外** |
| `tests/test_hitl_approval_consumption.py` | 新增保号面 + 建单前检查面断言组（InMemory+Db 双 store 口径承 T1 A2）· 既有 34 枚 diff 空 |
| `tests/test_hitl_auto_resume.py` | 既有 39 枚 diff 空（保号/guard 改动后的回归对拍 · 不新增 · 若 guard 行为改变既有断言须在本 task failure_paths 清点面内显式裁定） |
| `tests/test_react_observe.py` / `test_hitl_resume*.py` | 仅当 guard/保号改变既有断言时按 B1 裁定修订（预期：不触碰 · 见 B1） |
| `docs/_tech_graph/l1/01_modules.md` | lg_rag / hitl 两行 G-L1 行备注（保号机制 + 建单前检查 + guard 复用消费门语义说明） |

### 非范围

- replan 质量 / LLM 提示词工程（保号只管 id 带回 · 不动 LLM 规划内容与 prompt）
- T2 auto_resume 机制面（触发器/行锁认领/补偿扫描/双写撤销——零改 · 孤儿 pending 清理后的扫描输入纯度提升是 guard 的自然副产品 · 非本 task 承诺目标）
- 消费门 TTL 语义本身（TTL 值域/env 键/读时窗口语义零改 · guard 只复用不定义）
- deny 判序 / Policy 写闸 / gateway 闸链 / 预算吞消费（T1 钉死契约存续 · 本 task 零触）
- 旧单据 Backfill / 迁移（缺 `capability_id` 旧单据不匹配不补写 · 钉死契约六）
- `resume.py` 恢复链 · `store.py` 既有方法 diff · 新表/新列/payload 新键/新 SSE 事件类型（freeze 存续）

---

## failure_paths

| 失败路径 | 现象与后果 | 规避/裁定 |
|----------|-----------|-----------|
| **FP-1 · 保号误用于非 approved 步骤** | 保号集合若误取「所有未完成步骤」或「locked 前缀外的未解决后缀」而非 `hitl_unlocked_ids` ∩ 未解决 → 未授权步骤免重批沿用原 id → 消费键可被**无批准**的 LLM 计划行伪造命中风险（旧单据 cap/run 相同场景）· 授权面静默扩大 | 钉死契约一：P 严格 = `hitl_unlocked_ids` ∩ 未解决；变异断言：非 unlocked 未解决步骤在 replan 后**必须换新 id**（保号面反例断言 · 30 必落） |
| **FP-2 · 保号打断 locked 前缀语义** | 保号行若被拼进 locked 前缀（或 `plan_prefix_ids`/`recoverable_point` 随之偏移）→ 重跑保护扩散 · `_unresolved_suffix` 计算错位 · T1/T2 既有断言（locked 语义 · carry 形态）批量失效 | 钉死契约二：P 置于 locked 之后 LLM 新后缀之前 · `plan_prefix_ids` 仍仅 = locked · `recoverable_point` 不变；既有断言回归对拍进验收 |
| **FP-3 · 旧单据（无 capability_id 键）与建单检查交互** | T1 落地前创建的 approved 单据 payload 缺 `capability_id` → guard 若宽松匹配（缺键视为通配）→ 误跳过合法建单 → 该轮 HITL 永不出现 → 人干等 | 钉死契约六：缺键单据**不匹配**（fail-open 照建）· 与消费门缺键 fail-closed 同构；断言组含「缺键旧 approved 在场 → 照建单」 |
| **FP-4 · 检查读异常静默吞错** | guard 的 `alist` 读失败若 fail-closed 不建单 → DB 抖动期合法 pending 被抑制 → 死等且无任何信号 | 钉死契约五：fail-open 照建 + `hitl_persist_guard_read_failed` warning 台账（记动作不记内容）；断言：mock store `alist` 抛错 → 单据照建 + 台账出现 |
| **FP-5 · 保号与空 allowlist 短路交互** | 空 allowlist 短路（:963-977）`items=[]` · locked 即全计划 → 真风险双端：① 保号段误向空计划注入 P → 计划膨胀；② 空 allowlist + unlocked 时 approved 步从计划丢失（实读 :688+:975 · P 元素均 approved 故「未授权行」非真风险 · R1 N-1） | 保号仅作用于 replan 输出拼装段；空 unlocked 时与 master 对拍零 diff（钉死契约三）为总闸；空 allowlist+unlocked 组合场景进断言组 |
| **FP-6 · 消费命中后 resume 重放双保险失效假设** | 保号命中消费后，T2 auto resume 依「同 run 无未决 pending」推进 · 若 guard 与消费门语义漂移（TTL/归一实现分叉）→ guard 建单而消费门命中（或反向）→ 孤儿 pending 复发或重复拦截 | 钉死契约四：guard 复用 `_approval_consumption_ttl_seconds`/`_decided_at_ts` 同一实现（禁第二份解析）；匹配三元组与 blocked_by 守卫镜像 :347-357；R3 交叉验证逐项对照两函数语义 |
| **FP-7 · 与 T1 34 枚 / T2 39 枚既有断言冲突面** | 保号改变 replan 后 `subtasks` id 序列 → 依赖「replan 后 id 递增」假设的既有断言（若有）批量失败；guard 改变 `_persist_hitl` 建单计数 → 依赖「resume 重放重建 pending」假设的断言失败 | 30 开工第一步：pytest 基线对拍（T1/T2 全绿基线）→ 实现后逐枚清点失败断言 · 凡既有断言失败须落 B1 裁定表（保留/修订/理由）· 预期冲突面集中在「重放重建 pending」形态断言（guard 跳过建单使其需按 approved-在场语义修订）；**预期零冲突面**：消费门判定/TTL/auto_resume 触发面（本 task 零改） |
| **FP-8 · 保号步骤终态残留** | approved 步旧结果被 :1687-1689 剪掉是「未解决」的前提 · 若未来改动使 approved 步保留终态 → 保号行带终态回计划 → 跳过执行 · 消费命中后不重跑 → 授权语义架空 | 保号实现处加防御：P 计算时显式排除有终态 sid（∩ 未解决为字面实现而非隐含假设）；断言：approved 步有终态时保号集合为空（防御断言） |

---

## B1 · 旧测影响面

| 既有测试面 | 预期影响 | 裁定 |
|-----------|----------|------|
| `tests/test_hitl_approval_consumption.py`（34 枚 · 消费门/TTL/归一/双 store） | **预期零 diff**：消费门判定函数零改（钉死契约七）；guard 在 persist 侧不影响签发侧消费判定 | 30 基线对拍 → 全绿存续为验收门槛；任何失败落本表显式裁定 |
| `tests/test_hitl_auto_resume.py`（39 枚 · 触发器/行锁/补偿扫描/双写撤销） | **预期零 diff**：auto_resume 零改；孤儿 pending 减少只影响真实运行态，既有断言均为构造态 | 同上基线对拍；若「补偿扫描依赖 pending 构造」断言因 guard 语义需修订 → 落 FP-7 裁定流程 |
| `tests/test_react_observe.py` / `test_hitl_resume*.py` / `test_hitl_pending_decide.py`（observe/挂起/恢复/decide 面） | **关注面**：凡断言「resume 重放后 `_persist_hitl` 重建 pending 行」者，guard 在 approved 在场时跳过建单 → 该形态断言需按新语义修订（预期少数 · 逐枚清点） | 30 实现后逐枚失败清点 → 修订断言须保留「无 approved 在场时照建」反向断言 · 修订理由落 invoke |
| `tests/test_step_contract.py` / `test_lg_rag_delegation_wiring.py` / `test_hitl.py`（计划契约/接线面） | **关注面**：凡断言「replan 后 subtask_id 全部递增/全新」者，保号使 unlocked 步骤保留原 id → 该形态断言需按「仅 unlocked 保号」语义修订 | 同上逐枚清点；空 unlocked 零 diff（钉死契约三）覆盖无 approved 场景的全部旧断言 · 预期绝大多数零 diff |

---

## 验收标准

> 全部可机断；pytest 机制段由 30 达成 · live 级复跑由 40 达成。T1/T2 既有断言全绿存续为总门槛。

- [ ] 人工闸：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 approved 后方可勾选下列码项
- [ ] **TB1（保号断言组 · pytest）**：supervisor replan 场景构造（mock LLM）：`hitl_unlocked_ids` 含 approved sid（未解决）→ replan 后 `subtasks` 中该 sid **原 id 原行带回**；同轮 LLM 新步骤照常 `_issue_plan` 盖章新 id（seq 递增存续）；保号行位于 locked 前缀之后 LLM 新后缀之前；`plan_prefix_ids`==locked ids · `recoverable_point`==len(locked) 不变
- [ ] **TB2（保号三路径覆盖 · pytest）**：正常 LLM 成功 / LLM 失败 fallback（`_carry_plan` 面）/ 空 allowlist 短路（nodes.py:963-977）三路径各一断言——unlocked sid 均保号
- [ ] **TB3（保号反例变异断言 · pytest · FP-1/FP-8）**：非 unlocked 的未解决步骤 replan 后**必须换新 id**；approved 步有终态时保号集合为空（防御断言）
- [ ] **TB4（空 unlocked 零 diff · pytest · 钉死契约三）**：`hitl_unlocked_ids` 为空时 replan 输出（`subtasks`/`host_subtask_seq`/`plan_prefix_ids`/`recoverable_point`/`subtask_results` 修剪面）与 master 对拍**逐字节一致**
- [ ] **TB5（消费命中成环 · pytest 机制段 · 维护者裁定一验收令）**：approved 单据在场（新鲜 · cap/run 匹配）→ resume → replan 保号 → `_approval_consumed` 命中（`delegation_approval_consumed` 台账断言）→ **不再二次拦截** → `done{completed}` 机制段可达
- [ ] **TB6（建单前检查断言组 · pytest · InMemory+Db 双 store · 维护者裁定二验收令）**：① 新鲜 approved（同 `(run_id, subtask_id, capability_id)` + blocked_by 守卫）在场 → `_persist_hitl` **零建单**（store 行数不变断言）；② 无 approved → 照建；③ approved 过 TTL → 照建；④ approved cap 不符 / blocked_by 不符 / 缺 `capability_id` 键（旧单据 · FP-3）→ 照建；⑤ 检查读异常（mock `alist` 抛错 · FP-4）→ **照建** + `hitl_persist_guard_read_failed` warning 台账断言
- [ ] **TB7（T1/T2 回归存续 · pytest）**：`tests/test_hitl_approval_consumption.py` 34 枚 + `tests/test_hitl_auto_resume.py` 39 枚全绿；B1 关注面（replan id 递增假设断言 · resume 重放重建 pending 假设断言）逐枚清点 · 凡修订断言落裁定记录于 30 invoke
- [ ] **TB8（live 复跑 · 40）**：双服务 live：create → hitl.waiting → decide(approved) →（resume/auto resume）→ replan 保号 → `delegation_approval_consumed` 台账 → `done{completed}` **可达**；resume 重放后 approved sid **零孤儿 pending** 重建；SSE 帧形态与 T1/T2 基线一致
- [ ] B1 旧测清单全绿亲跑记录（命令 + 结果）落 40 invoke
- [ ] `npx spec-wave task lint --file docs/tasks/active/task_hitl_replan_carry_and_persist_guard.md` PASS；`npx --yes spec-wave task lint-wiki-delta --target .` PASS（30/40 复跑于 active 期 · CLOSE 归档后改判 done/ 路径复跑）

---

## 依赖

| 依赖 | 说明 |
|------|------|
| T1 `hitl-approval-consumption-loop`（已 merge · base bdd45f9 含） | 消费门 `_approval_consumed`/`_delegation_issue_block_reason`/`_approval_consumption_ttl_seconds`/`_decided_at_ts` 为保号命中目标与 guard 语义镜像源；SPEC v1 FP-3 裁定为背景 |
| T2 `hitl-approval-consumption-auto-resume`（已 merge · base bdd45f9 含） | auto resume 触发器/补偿扫描为 live done 可达的下游消费方；`auto_resume.py:92-96` 复用消费 TTL 先例为 guard 复用范式依据 |
| `hitl_unlocked_ids` state 键（state.py:239,279） | 保号集合真源 · 由 `_apply_hitl_decision` :1671-1676 维护 · 本 task 只读 |
| 维护者两裁定（2026-10-10 · 背景节逐字引用） | 保号 + 建单前检查为本 task 全部动机的授权来源 · 钉死契约五 fail-open 裁定为维护者建议的采纳记录 |

---

## 给执行帽的必读列表

| 必读 | 理由 |
|------|------|
| `app/ops/lg_rag/multi/nodes.py` :630-734（`_stamp_host_plan`/`_locked_prefix`/`_unresolved_suffix`/`_carry_plan`） | 保号机制的落点与既有「原行带回」载体 |
| `app/ops/lg_rag/multi/nodes.py` :960-1054（supervisor replan 三路径） | 保号全覆盖的实现面 |
| `app/ops/lg_rag/multi/nodes.py` :268-372（TTL/归一/消费门） | guard 匹配语义镜像源 · 复用禁分叉 |
| `app/ops/lg_rag/multi/nodes.py` :1523-1611（`_persist_hitl`）+ :1644-1744（`_apply_hitl_decision`/`observe_node`） | 建单前检查挂点 :1601 前 · resume 重放孤儿 pending 机械来源 |
| `docs/harness/invokes/by-task/hitl-approval-consumption-loop/invoke_20261010_40_verify_hitl-approval-consumption-loop.md` :31-40 | T1 重要发现：sid 递增实证 · FP-3 循环 · carry 触发条件 |
| `docs/harness/invokes/by-task/hitl-approval-consumption-auto-resume/invoke_20261010_40_verify_hitl-approval-consumption-auto-resume.md` :48,55-57 | T2 live 复跑逐点吻合 + 孤儿 pending 附带观察 |
| `docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` :77,:193 | Q1 消费键三元组 + 缺键 fail-closed · FP-3 原裁定（本 task 修正其覆盖假设） |
| `tests/test_hitl_approval_consumption.py` + `tests/test_hitl_auto_resume.py` | T1 34 枚/T2 39 枚基线 · B1 对拍对象 |
| 本 task 钉死契约节 + failure_paths 节 | 30 不得静默改义 · FP-1/FP-3/FP-4/FP-5 断言必须落地 |

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 问题=两 live 实证偏差：replan 重盖章 sid 递增致消费键失配（`_stamp_host_plan` :642-649）· resume 重放 `_persist_hitl` 先于 `interrupt()` 返回重建孤儿 pending（:1727/:1736）；维护者两裁定逐字在案 · 需求边界无歧义 | no | — | none |
| R1 | 范围=nodes.py 单文件两段增量（保号段+建单检查段）+ 断言组 + G-L1 两行备注；replan 质量/auto_resume/TTL 语义/deny 判序/旧单据迁移/freeze 面六条非范围钉死 | no | — | 无 |
| R2 | 三裁定：**保号=复用 `_carry_plan` 原行带回语义**（否「回填 locked 前缀」· 否「LLM 提示词保号」）· **fail-open 照建单+warning 台账**（维护者建议采纳 · 漏建单死等重于孤儿 pending · :1554-1555 先例同向）· **旧单据缺键不匹配不扩面**（与消费门缺键 fail-closed 同构） | no | — | 保号拼装位置（locked 后 LLM 新后缀前）的精确实现形态 30 定 · 契约二已钉语义边界 |
| R3 | 交叉验证：guard 匹配语义逐项镜像 `_approval_consumed` :318-372（blocked_by 守卫/三元组/缺键不匹配/归一/TTL 同一函数调用 · 禁第二份实现）· capability 真源 `term.get("tool")` :1583 同源 · auto_resume.py:92-96 复用先例 | no | — | 无 |
| R4 | failure_paths 推演 8 条（FP-1~FP-8 · 含保号误用/前缀语义漂移/旧单据交互/读异常静默/空 allowlist 交互/语义漂移/T1·T2 断言冲突面/终态残留）· FP-1/3/4/5 各有断言落点 | no | — | 无 |
| R5 | 验收口径机断化收敛（TB1~TB8 · 台账断言/store 行数/逐字节对拍/全绿存续/live 帧形态均可机断 · 30/40 分工明确） | yes | 三裁定各有实证排除岔路 · 锚点逐行实读闭环 · T1/T2 依赖边界清晰 | 见 R2 |

**actual_last_round**：R5 · **early_stop**：yes · **residual_risks**：见 R2

### R0 · 问题框定

两个 live 实证偏差同源不同面：**面一**，`_stamp_host_plan` :642-649 对 LLM 规划项一律 `_issue_plan` 盖章新 id（seq 递增），approved 步不在 locked 前缀（:688 摘出）故每次 replan 换号 → 消费键三元组 subtask_id 维度永不命中 → FP-3 再拦循环（T1 40 :31-40 live 实证 sid :1→:11）。**面二**，LangGraph resume 时 observe 节点从头重放，落库（`_persist_hitl` :1727）先于 `interrupt()`（:1736）返回恢复值 → 按重放期旧状态为已批准 sid 重建 pending（T2 40 :55-57 实证 hitl_5cefb116）。两面均不涉消费门/auto_resume 判定本身（T1/T2 机制面已闭合）。

### R1 · 范围钉死

改动仅 `nodes.py` 一处文件内两段增量：① supervisor replan 保号段（三路径全覆盖）；② `_persist_hitl` `acreate` 前建单检查段。测试面新增断言组集中于 `test_hitl_approval_consumption.py`。图谱仅 G-L1 行备注。非范围六条逐条与范围无交集（replan 质量/auto_resume/TTL 语义/deny 判序/旧单据迁移/freeze 面全部明确排除）。

### R2 · 方案裁定

- **保号机制选型**：复用 `_carry_plan`「原行带回不重新签发」语义（:721 既有载体），保号集合 P=`hitl_unlocked_ids`∩未解决，拼装位置 locked 之后 LLM 新后缀之前——不选「approved 步回填 locked 前缀」（会扩散重跑保护 · 破 `plan_prefix_ids` 语义 · FP-2），不选「LLM 提示词要求沿用 id」（不可机断 · 属非范围）。
- **fail-open/fail-closed 裁定**：**fail-open 照建单 + warning 台账**（钉死契约五 · 维护者建议采纳）。理由：漏建单=人干等不存在的审批（:1526-1529 既有红线）重于孤儿 pending=UX/判定输入污染；`_persist_hitl` :1554-1555 去重读失败「退回 state 不崩」为同向先例。
- **旧单据缺键**：不匹配不扩面（钉死契约六 · 与消费门缺键 fail-closed 同构 · 退化为既有再挂起形态）。

### R3 · 交叉验证

guard 匹配语义逐项镜像 `_approval_consumed` :318-372：blocked_by 守卫（:347）· 三元组精确匹配（:349-357）· 缺键不匹配（:356-357）· `decided_at` 归一（`_decided_at_ts` 同一函数调用）· TTL（`_approval_consumption_ttl_seconds` 同一函数调用 · auto_resume.py:92-96 复用先例）。两函数语义分叉即 FP-6，故禁第二份 TTL/env/归一实现。capability 真源 `term.get("tool")`（:1583）与消费门 capability 维度同源。

### R4 · 失败路径推演

FP-1~FP-8 见 failure_paths 节。要点：FP-1（保号误用于非 approved）由保号反例变异断言 TB3 锁死；FP-3（旧单据缺键）由 TB6④ 锁死；FP-4（读异常静默）由 TB6⑤ 锁死；FP-5（空 allowlist 交互）由 TB2 第三路径 + TB4 总闸覆盖；FP-7（T1/T2 断言冲突面）由 TB7 基线对拍 + B1 逐枚清点消化。

### R5 · 验收口径收敛

TB1~TB4 保号面 + TB6 建单检查面为 pytest 机制段（30 达成）；TB5 消费命中成环为机制段端到端；TB7 回归存续为总门槛；TB8 live 复跑（done 可达 + 零孤儿 pending）留 40。全部可机断 · 无人工目测项。

---

## 测试策略（Harness）

`test_strategy=required`。pytest 机制段为主 · live HTTP/SSE 复跑留 40：

- **新增断言组**（`tests/test_hitl_approval_consumption.py`）：TB1 保号断言组 · TB2 三路径覆盖 · TB3 反例变异断言 · TB4 空 unlocked 零 diff 对拍 · TB5 消费命中成环 · TB6 建单前检查五断言（InMemory+Db 双 store 口径承 T1 A2）
- **回归存续**（TB7）：T1 34 枚 + T2 39 枚全绿 · B1 关注面（replan id 递增假设断言 · resume 重放重建 pending 假设断言）逐枚清点 · 凡修订落裁定记录
- **live 级**（TB8 · 40）：双服务复跑 done{completed} 可达 + 零孤儿 pending + SSE 帧形态基线一致
- **台账纪律**：新增 `hitl_persist_guard_read_failed` warning 台账（记动作不记内容 · 承 delegation 台账纪律）

---

### 自检结论（执行者）

**30 实现**：nodes.py 两段增量（_unlocked_preserved_rows 保号段 + _persist_hitl 建单检查段）· 14 枚 TB 断言 · 图谱 G-L1 备注 · 全量 4failed/1762passed（4 红=master 基线环境性）· ruff 零新增 · graph-compile EXIT=0 · B1 107 枚全绿（详见 invoke_20261010_30_implement.md）。

**40 核验**（独立复跑 · 详见 invoke_20261010_40_verify.md）：七项全过。diff 面对拍恰 10 文件面外零（真 base=merge-base bdd45f9 · .env.example -34 行系 base 漂移伪象）；14 枚抽跑全绿 · TB3/TB6 断言强度亲读非假绿；全量 4 红与基线同名同数零新增 · ruff 零新增 · graph-compile EXIT=0 · B1 107 枚亲跑吻合。**live 三 run 正面终验**：保号消费命中原 sid（568d288a 四轮 :1/:2/:3 各自 delegation_approval_consumed · a0850a8e consumed{:1}+token+echo 真执行）= T1 :1→:11 偏差收口；hitl_persist_guard_skip 每次重放在案 = T2 孤儿单偏差收口；终态 run 零 pending。两条如实钉案：①TB8 字面 done{completed} 在手动 resume 流结构性不可达（resume.py:131 既有设计 · 终帧字面永为 resumed · event_store.py:99-107 语义=终态达成）；②approved 路径自然完成双重结构性不可达（LLM 不知晓保号行每轮新铸 echo 步+observe 剪结果盲循环 · router.py:328-357 聚合 approved 非空恒 replan · 均面外既有语义）。另钉：30 自报「verify EXIT=0」不准（实测 EXIT=2 仓级基线 BLOCKED · 主仓同 · 非本 task 归因）。**裁定：可进 PR 队列（附钉案）**。

---

### KPI（00）

（CLOSE 关账回填）

---

### 经验总结

（CLOSE 关账回填）

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-10 | 10 起草落盘：Harness 元信息/人工闸三 pending/背景（维护者裁定逐字）/现状锚点（nodes.py 行号实证）/钉死契约八项/范围+非范围/failure_paths FP-1~FP-8/B1 旧测影响面/验收 TB1~TB8/依赖/必读/R0–R5/测试策略 · 骨架先行增量落盘完成 |
