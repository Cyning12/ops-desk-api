# Task 审查：hitl-approval-consumption-loop（T1 · D1 消费门 + D2 unlock 回填 + D4 · R1）

> **审查帽**：20-task-audit R1（书面审 · 不实现 · 不改 task 实质）
> **审查对象**：`docs/tasks/active/task_hitl_approval_consumption_loop.md`（draft · 2026-10-10 落稿）
> **对照基准**：SPEC v1（`docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` · HG-SPEC-SIGNOFF=approved 2026-10-10 · spec 分支只读）
> **实证 base**：worktree 分支 `task/hitl-approval-consumption`（merge-base=master `4d905e0` ✓ 与 task 声明一致）
> **审查人**：Harness 20-task-audit（子 Agent · R1 · 2026-10-10）

---

## 结论（R1 终态 · 增量复核后）

| 维度 | 结论 | 说明 |
|------|------|------|
| **内容** | **PASS**（首轮 FAIL · 退回 B-1 四项修复经增量复核成立 · 10-task commit `0c5d148`；残留 1 条非阻塞 NIT 见文末增量节） | 首轮 B-1（B1 漏 scripts/acceptance 调用点 + redline「非默认跑」失准）已修复；范围/钉死契约/验收映射/思考轮/锚点 17 组均核对成立 |
| **流程闸** | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均 pending（属实时序 · 非阻塞 · 如实登记） | 见文末签闸清单 |

> 首轮 FAIL 结论与退回清单留档于下文「阻塞项 / 非阻塞项」与「回填清单」节（历史留痕不改写）；增量复核记录见文末「R1 增量复核」节。 |

---

## 核对项

| # | 核对项 | 结论 | 实证 |
|---|--------|------|------|
| 1 | 范围承接：D1 消费门 + D2 unlock 回填 + D4 台账/测试（本 task 面）· Q1/Q2/Q3/Q5 · FP-1~FP-7 · A1/A2/A3/A5/A6/A7/A8 | ✅ | 与 SPEC §2/§4/§5/§6 逐块对上；A4（env 口）划 T3、A9/A10 划 T2，拆分边界与 SPEC D3/D5 一致 |
| 2 | 非范围完备性 | ✅ | D5/D3/decide 落库与状态机/deny 判序/Policy/gateway/UI/SSE/新表新列/session 级授权/跨进程缓存逐条划出，与 SPEC §3 对齐无漏 |
| 3 | 消费键三元组（Q1）+ 旧单据缺键 fail-closed | ✅ | 钉死契约「消费键」行 + 实操-C 断言化（缺键 approved 单据存在时仍拦截），闭环 |
| 4 | fail-closed 断言组（TA2 五项变异式） | ✅ | pending/rejected · 超 TTL（双 store 各一组 · Db 组必经 alist/aget 真读路径）· 三元组任一不匹配三例 · 缺 capability_id · store 读异常——SPEC A2 全覆盖且更细 |
| 5 | decided_at 归一输入 float\|str（R1-N1 锚点精度钉） | ✅ **实证成立且必要** | 实读：InMemory `adecide` :98 `decided_at = time.time()`（float）；Db `_DECIDE` :161 SQL `now()`，但消费端经 `alist/aget` 实收 `_row_to_dict` 输出 :249 `row[14].isoformat()`（**ISO 8601 str**）——SPEC「Db store 为 datetime」指 SQL 层，task 把消费端实收类型钉为 float\|str 是对 SPEC 表述落差的正确修正 |
| 6 | async 化裁定甲案（R1-N2 · 留 20 复核项） | ⚠️ 裁定本身成立 · **波及面漏一处**（见 B-1） | 实证：`_join_subtasks` 确为 sync（nodes.py:644 `def`）· graph.py:94 sync 注册 · 拦截/审计段 :708-726 在 sync 核心内（乙案「事后修补须回卷已发审计」成立）· store.py:1-10「只有异步接口」docstring 实证（丙案违 P-13 成立）· `asyncio_mode=auto`（pyproject.toml:76）实证。甲案选定理由闭环；但 B1 清单与「grep 全量」声称不符（B-1） |
| 7 | `auto_approve_ok` 零 IO · capability 包零触（Q2） | ✅ | delegation.py:488-514 实读为纯函数三条件；钉死「逐字节零 diff」+ TA4 diff 空断言，可机断 |
| 8 | unlock 回填形态守卫（Q3）+ 409 保留 | ✅ | router.py:404-411 409 守卫实读在案；FP-4「prefix_touch 空 unlock 仍 409」保留断言成双保险；SPEC Q3 S2（router 放行空 unlock=静默按驳回）弃选理由存续 |
| 9 | off/observe 零 diff（FP-7） | ✅ | `_delegation_active()`（nodes.py:252-254）mode!=off 才启用 → :710-726 整段短路论证实证成立；spy 断言兜底入 TA5 |
| 10 | 实操-E「设计真态钉死」段改写义务 | ✅ **实证逐字一致** | test_capability_testing_write.py:488-493 实读：该段断言「批准后重下发仍拦（审批逐次有效）」；D1 落地后语义翻转风险真实存在；「改写为双断言 · 禁整段删除」处置正确 |
| 11 | 台账纪律（记动作不记内容） | ✅ | `delegation_approval_consumed` + 读失败 warning；字段白名单（request_id/subtask_id/capability_id/decision_by/TTL 余量）与 SPEC 设计纪律 5 一致 |
| 12 | failure_paths 推演（12 条） | ✅ | FP-1~FP-4/FP-6/FP-7 承 SPEC + 实操 A–F 六条来自锚点实读，每条有断言/闸对应，可机断；FP-5 归 T3 说明在 R4 有据 |
| 13 | 思考轮 R0–R5 闭合 | ✅ | 控制表回填齐；early_stop=yes 理由（SPEC 裁定存续 + 新增三裁定各有实证排除岔路 + 锚点逐行实读）成立；residual_risks 如实（R2/R3 留 20 复核项本审已逐条复核） |
| 14 | 行为变更类 task「旧测 grep 影响面」checklist 项（K7） | ⚠️ 有 B1 专节但**漏一处** | B1 表在册且分两节（随改清单 + 零 diff 期望），形态合规；但随改清单不完整（B-1） |
| 15 | 人工闸表 / invoke 目录 / lint 闸 | ✅ | 三闸 pending 如实；`required_invoke_hats=10,20,30,40` 含 20 → 本审 invoke 落盘义务已履行；验收末行含 task lint + lint-wiki-delta |

## 锚点实读抽查

（20 亲读 worktree 分支 `task/hitl-approval-consumption` · merge-base=master `4d905e0` 与 task 声明一致）

| 锚点 | task 声称 | 20 实读结论 |
|------|-----------|-------------|
| `nodes.py:277-295` | `_delegation_issue_block_reason` sync 纯判定 · 不读 HITL 记录 | ✅ 逐行一致（tool 空/∉scope→None；未注册→安全默认；`auto_approve_ok` False→拦截文案） |
| `nodes.py:644` + `graph.py:94` | `_join_subtasks` sync 节点 · sync 注册 | ✅ :644 `def _join_subtasks`（sync）；graph.py:94 `builder.add_node("subtask_join", _join_subtasks)` |
| `nodes.py:708-726` | delegation 拦截段（blocked_by + hitl_required + 审计 :721-725） | ✅ 逐行一致；审计在 sync 核心内（乙案「审计不可回卷」否决理由实证成立） |
| `nodes.py:1397-1471` | :1440-1445 unlock 只取 depends_on ∩ plan_prefix_ids；:1457 payload 仅 observation | ✅ 逐行一致（单子任务 → unlock 空串路径实证） |
| `nodes.py:341-354` | `_error_terminal` 保留 tool 字段（capability_id 真源） | ✅ :352-353 实证 |
| `nodes.py:550-567` | `_locked_prefix` 摘除 hitl_unlocked_ids（:560-562） | ✅ 实证；resume 成环既有机制零改口径成立 |
| `nodes.py:252-254` | `_delegation_active()` off 短路 | ✅ 实证（off 零 diff 论证前提成立） |
| `delegation.py:488-514` | `auto_approve_ok` 纯函数三条件 | ✅ 逐行一致（scope ⊆ / 全只读 / 无 sandbox·cli · 零 IO） |
| `delegation.py:105-107` | `_env_int` low=1 high=86400 先例 | ✅ 实证（TTL env 同形态先例成立） |
| `store.py:98` | InMemory decided_at=float | ✅ `time.time()` 实证 |
| `store.py:159-163,249` | Db `_DECIDE` now()；`_row_to_dict` :249 ISO str | ✅ 实证（**R1-N1 归一输入 float\|str 钉正确且必要**） |
| `store.py:1-10` | 「只有异步接口」docstring | ✅ 实证（丙案否决理由成立） |
| `router.py:404-411` | 409 守卫保留不动 | ✅ 逐行一致（detail 文案与 SPEC 缺口 2 引述一致） |
| `router.py:287-316` | `_collect_decisions` 同批汇总不动 | ✅ 实证 |
| `pyproject.toml:76` | `asyncio_mode = "auto"` | ✅ 实证（sync→async 测试随改纯机械成立） |
| `test_capability_testing_write.py:488-493` | 「设计真态钉死」段语义翻转风险 | ✅ 逐字实证（实操-E 成立） |
| `tests/test_step_contract.py:259,275,294,306,323,756,769` · `test_lg_rag_delegation_wiring.py:159,170,187` · `test_capability_testing_write.py:433,492` · `tests/eval/test_capability_redlines.py:1715` | B1 随改 14 处 | ⚠️ 14 处本身全部实证在册；**但 grep 另发现 `scripts/acceptance/capability_step_contract_gate.py:152` 未入册**（见 B-1） |

## TA1–TA7 ↔ SPEC A 映射核对

| task 验收 | SPEC | 核对结论 |
|-----------|------|----------|
| TA1 消费放行（台账 logger/span 双面断言） | A1 | ✅ 覆盖且更细（SPEC 只要求台账含动作名） |
| TA2 消费边界否定五组变异（双 store TTL · 真读路径钉 · 缺键 · 读异常） | A2 | ✅ 全覆盖；「Db 组必经 alist/aget 真读路径 · 禁构造 float 绕过」是对 R1-N1 的正确断言化 |
| TA3 单子任务形态 resume 成环（单测 + 机制段集成 · live 留 40） | A3 | ✅ 一致（fixture 复用面点名 A4④ 形态，可执行） |
| TA4 反回归钉死（registry/policy diff 空 + deny 判死测原样绿 + 消费不过 Policy 断言） | A5 | ✅ 一致；实操-D 与 TA4 双落 |
| TA5 off 零 diff（spy 零调用 + 无台账） | A6 本 task 面 | ✅ 一致（自动 resume 面归 T2，划分正确） |
| TA6 decide 落库不动（adecide/_DECIDE diff 空 + 409 保留断言） | A7 本 task 面 | ✅ 一致（decide 载荷可选键面归 T2，划分正确） |
| TA7 工程面（pytest 全绿 / ruff / graph-compile / 图谱三行） | A8 本 task 面 | ✅ 一致（strategy 行归 T3，三行划分正确） |
| （归 T3/T2） | A4 / A9 / A10 | ✅ T1 正确不承载，依赖表与 T2/T3 互指一致 |

## 阻塞项 / 非阻塞项

### B-1（内容阻塞 · 退回 10-task）：B1 影响面漏 `scripts/acceptance/capability_step_contract_gate.py:152`

- **实证**：`grep -rn '_join_subtasks'` 全仓命中中，除 B1 已列 14 处外，另有 `scripts/acceptance/capability_step_contract_gate.py:152` `out = _join_subtasks(state)` —— sync 直调（在 `async def _drive` 内 · :140）；该脚本被 `scripts/acceptance/capability_acceptance.sh:165` 真跑（capability 本地验收九层门禁 · `docs/guides/RUNBOOK_local-acceptance_v1_zh.md` 引用）。
- **后果**：甲案 `_join_subtasks` async 化后该处拿到 coroutine → 门禁脚本报 TypeError 或假绿——与 failure_paths 实操-A 同型坑，但实操-A 的「B1 清单逐点随改」兜不住它（不在清单内）。
- **矛盾点**：R1-N2 行与 R3 均声称「`grep` 全量落 B1（14 处）」，实证不符（grep 范围恰漏 `scripts/`）。
- **修复面极小**：`_drive` 已是 async，补 `await` 一行即可；10-task 只需在 B1 表补第 15 处 + 把 R1-N2/实操-A/F3/R3/R5 的「14 处」口径改为 15 处。
- **附带同修（B-1b）**：B1 redline 行「非默认跑（eval marker）」表述失准——`pytestmark = pytest.mark.redline`（test_capability_redlines.py:55）不构成默认不跑：`pyproject.toml` 无 addopts 排除、conftest 无 deselect 钩子、CI `.github/workflows/pytest.yml:47` 跑的是 `pytest tests -q --tb=short`（无 `-m` 排除）→ **redline 文件默认就跑**。TA7「pytest tests 全绿」本就强制其随改，但「30 注记**是否**随改」的措辞会误导为可选，应改为「默认跑 · 必须随改并亲跑」。

### 非阻塞注记

- **N-1**：eval redlines 处随改后建议 30 在全量 pytest 之外显式跑一次 `pytest -m redline` 留证（默认虽跑，显式留证便于 40 复核）。
- **N-2**：graph_delta 三行（lg_rag/hitl/capability）与 G-L1 行备注口径一致，HG-GRAPH-MODULES 随 30 回写由 00 代录的流程写法与本仓先例一致。
- **N-3**：T1 对 SPEC「Db store 为 datetime」表述落差的修正（归一输入 float|str）属**对 SPEC 的精度补强而非改义**，SPEC 层无需回改（Q5 S1 括号内「双 store 归一后比较」语义存续）。

## 回填清单（退回 10-task · 修复后可走增量复核）

| # | 回填项 | 落点（task 小节） |
|---|--------|-------------------|
| 1 | B1 随改清单补第 15 处：`scripts/acceptance/capability_step_contract_gate.py:152`（`_drive` 内 sync 直调 → 补 `await`；该脚本被 `capability_acceptance.sh:165` 真跑） | 「B1 · 旧测影响面」随改清单表 |
| 2 | 「14 处」口径统一改「15 处」（R1-N2 锚点行 / 钉死契约 async 化裁定行 / F3 / failure_paths 实操-A / R3 / R5） | 现状锚点 R1-N2 行 · 钉死契约 · 范围 F3 · failure_paths · 思考轮 R3/R5 |
| 3 | B1 redline 行「非默认跑（eval marker）」改「默认跑（无 marker 排除 · CI 与本地 `pytest tests` 均收集）· 必须随改亲跑」；删「30 注记是否随改」可选措辞 | 「B1 · 旧测影响面」随改清单表 redline 行 |
| 4 | （建议）实操-A 补一句「grep 范围须含 scripts/」防再漏 | failure_paths 实操-A 行 |

> 修复均为文档口径补齐，不动任何裁定结构（甲案/归一类型钉/形态守卫均维持）。10-task 修复后 20 做增量复核即可，无需重走全轮。

---

## R1 增量复核（B-1 修复 · 10-task commit `0c5d148` · 2026-10-10）

按退回清单四项逐点核对（仅核修复点 · 未重走全轮 · 裁定结构确认零改：commit diff stat 仅 task 文件 13+/11-）：

| # | 退回项 | 复核结论 | 实证 |
|---|--------|----------|------|
| 1 | B1 随改清单补 scripts/acceptance 调用点 | ✅ | B1 表新增 `scripts/acceptance/capability_step_contract_gate.py` 行（:152 · 补 `await` 一行 · `_drive` 已是 async :140 · 被 `capability_acceptance.sh:165` 真跑 · 漏改后果写明）；R1-N2 锚点行同步补列 |
| 2 | 计数口径全文统一 | ⚠️ **方向修对 · 数值差 1（残留 NIT · 非阻塞）** | R1-N2/R2 已作「直调点 14 处」（**正确**：20 逐枚复枚 join=13（test_step_contract×7 + wiring×3 + testing_write:433×1 + redlines×1 + scripts×1）+ block_reason :492×1 = **14**）；但 B1 标题/F3/实操-A/R5/验收末行作「**15 处**」，与 B1 表实列 14 点不符，且 R2 段内「14 处直调点 / 15 处随改」自相矛盾。溯源：原稿声称 13 实列 12（原稿自身差 1），本 20 首轮退回清单以「声称 14+1=15」为口径未逐枚枚举——**本 NIT 由 20 引起，在此自引并更正：真值=14 处（B1 表枚举为真值）**。非阻塞（清单本体完整正确 · 30 按表施工不受影响）；建议 10-task 顺手把 5 处「15 处」回改「14 处」（可与维护者签闸同批 · 不单独退回） |
| 3 | redline「非默认跑」措辞修正 | ✅ | B1 redline 行改「默认跑（pyproject 无 addopts 排除 · conftest 无 deselect · CI pytest.yml:47 无 `-m` 排除）· 必须随改亲跑」+ 建议另跑 `pytest -m redline` 留证；R3 residual 同步钉死；R1-N2 行标注同步 |
| 4 | 实操-A 补「grep 范围须含 scripts/」 | ✅ | 实操-A 行补提醒（含漏网实证引注 · R1 审查 B-1 溯源）；R3 波及面实证行 grep 命令同步补 `scripts` |
| 5 | （附带）修订记录 + lint 自报 | ✅ | 修订表新增 10-task 修订行（「仅文档口径补齐 · 裁定结构不动」如实）；20 复跑 lint/verify 见下 |

**增量复跑（20 亲跑）**：`npx spec-wave task lint --file docs/tasks/active/task_hitl_approval_consumption_loop.md` → **PASS（EXIT=0）**；`npx spec-wave verify --target . --task docs/tasks/active/task_hitl_approval_consumption_loop.md` → **EXIT=2**（三闸 pending 属实时序 · 预期内）。

**增量裁定**：B-1 阻塞解除 → **内容 PASS**（残留 NIT 一条非阻塞：计数口径 15→14 回改建议移交 10-task 顺手修 · 不挡签收）。

---

- [ ] 已读 R1 审查结论
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-10 | R1 骨架落盘（骨架先行 · 逐节增量）→ 全文填充：**内容 FAIL（B-1 阻塞 · 退回 10-task 补 B1 漏点 + redline 措辞）· 流程闸 pending 属实时序** · 锚点 17 组实读 · TA1–TA7↔SPEC A 映射全对上 |
| 2026-10-10 | R1 增量复核（10-task 修复 commit `0c5d148`）：四项退回点 3✅+1⚠️（计数口径残留 NIT · 真值 14 处 · 20 自引并更正）→ **内容转 PASS** · lint 复跑 PASS · verify EXIT=2 预期内 · 「结论」节机读口径修正（节名改以「结论」起首） |
