# hitl-auto-resume-claim-race 审查（R1 · 20-task-audit）

> **审查对象**：`docs/tasks/active/task_hitl_auto_resume_claim_race.md`（commit 7022e20 · auto_resume 认领竞态 · decide 同秒首跑连续 stranded_checkpoint · bugfix 性质验收偏差收口）
> **审查帽**：20-task-audit（R1 书面审查 · 未改 task 实质内容 · 未代签任何 human_gate · 未执行 30 · 未切分支 · 未 commit 码面）
> **日期**：2026-10-10 · **审查时仓态**：主仓 `ops-desk-api` · 分支 `task/hitl-auto-resume-claim-race`（base master `1117286`）· 工作树仅见未跟踪 `jar`（与本 task 无关 · 未触碰）
> **委托令**：00 委派令「Harness 20-task-audit 书面审查帽（R1 · 只审不动手）」+ 八审查维度 + invoke 末段 7 条指定审查要点
> **实证真值**：`docs/acceptance/20261010_hitl-consumption-loop_local_acceptance.md` D1+项6（分支 `acceptance/20261010-hitl-consumption-loop` @ `f57b4ae` · 本帽 git show 亲读 · 实证未 merge master）

## 结论摘要

**裁定：PASS-WITH-NITS**（内容可执行 · 零内容阻塞 · 非阻塞观察项 N-1~N-3 三条列明于末节 · 三流程闸全 pending 待维护者签）

| 维度 | 结论 |
|------|------|
| task **内容**可执行 | ✅ **PASS-WITH-NITS**——码面锚点 8 处全亲读核真（行号/机制链如实）；根因研判「落库先于挂起 ⇒ pending 可见 ⇏ interrupt 元数据可见」链条钉严且开放标注假设；钉死契约 7 条逐条可机验；TC1–TC5 均可证伪；最小面与 GATE_STOP 触发明确；思考轮 R0–R5 闭合 early_stop at R5 理由成立 |
| **流程闸** HG-TASK-DRAFT | `pending`（10 未代签 ✓ · blocks 30） |
| **流程闸** HG-AUDIT-R1 | `pending`（本审查文落盘即其前置交付 · 维护者签后方 approved · 本帽留 pending 待 00 代录） |
| **流程闸** HG-GRAPH-MODULES | `pending`（graph_change_layer=n/a 预判照实写 ✓ · 触发回写条件钉清 · blocks 30） |
| lint 复跑（不采信自报） | 本帽亲跑 `npx --yes spec-wave task lint --file docs/tasks/active/task_hitl_auto_resume_claim_race.md` → **LINT: PASS · exit 0**（余 W3 自检结论占位符 · draft 期合法 · close 前 40 回填） |
| draft 洁净度 | ✓ 工作树无提前实施（git status 仅未跟踪 `jar` · task 分支仅 7022e20 一个 task 文档 commit） |

本审查文按结论机读口径书写：「结论」起首节 · 通过词落节内 · 实质内容充足 · 无否定共现。

---

## 一、根因研判与码面锚点逐一对拍（全亲读核真 · 如实）

| 锚点（task 声称） | 本帽亲读实证 |
|---|---|
| `nodes.py:1820-1822`「落库先于挂起」注释 | ✅ 逐字在案：:1820-1821「落库**先于**挂起：挂起期间节点 return 的值不进 checkpoint，但申请必须在外面立刻能拉到」；:1822 `await _persist_hitl(...)` 调用；`interrupt()` 在 :1831 抛 GraphInterrupt。机制链（_persist_hitl 先写 pending 行 → interrupt 后挂起 → checkpoint interrupt 元数据落库在其后）与码面时序一致 |
| `nodes.py:1610-1706` `_persist_hitl` | ✅ def :1610 · return :1706 · pending 行 `store.acreate` :1696 逐行在案 |
| `resume.py:41-51` code→HTTP 映射 | ✅ :44-47 注释逐字：`stranded_checkpoint → 409（旧版本格式残留，**永远**恢复不了）` —— task 附带发现「竞态证明该 code 存在 transient 形态 · 分类语义须重审」成立且重要 |
| `resume.py:228-248` stranded 判定（报错行 :244） | ✅ `aget_state` :228 → 无 tasks 抛 `not_interrupted` :230-235 → tasks 有但 interrupts 全空抛 `stranded_checkpoint`（raise 起 :244 · code 字面 :245 · 设计意图注释 :237-243 = 拦 langgraph 0.2→1.2 升级残留防 TypeError 500）逐行一致 |
| `auto_resume.py:151-182` `_claim_and_execute` | ✅ 行锁认领 :156 · 终态判定 :170 · `_execute_decided_resume` 同源 :179 · 「任何异常只 logger.exception『HITL 自动恢复执行失败』等下轮扫描兜底」:180-182 逐行一致 |
| `auto_resume.py:128-148 / :185-222 / :225-247` | ✅ 触发派发（台账 triggered/compensated :137-138）· 扫描四条件 :207-219 · scanner 启动即扫+周期+manual 零创建 :225-247 全在案 |
| `router.py:242-254` 触发器挂点 | ✅ decide 成功分支 approved∧auto → `schedule_auto_resume` :247-253 · OA callback 不挂注释 :244-245 逐字一致 |
| `tests/test_hitl_resume.py:230-259` 409 断言 | ✅ `test_stranded_checkpoint_is_refused_not_crashed` 在案：`_FakeGraph` 注入 tasks 有 · interrupts=() → 断言 `code == "stranded_checkpoint"` :259。⚠ 窗尾微偏：测试体实延至 :260（第二断言 detail 含「旧版本」）——记 N-1 |

**根因研判裁定**：机制链如实——「落库先于挂起」使 pending 行（hitl store 表）可见时刻早于 LangGraph checkpoint（含 interrupt 元数据）提交时刻，auto 流 decide 同秒认领直读快照（tasks 有 · interrupts 空）→ 命中 stranded_checkpoint，推导链每一环均有码面锚点支撑；窗口 ≈30s 与 SSE/astream 生命周期绑定**仅假设**，task 已显式标注「待 30 实证定位 · 起草阶段不下结论」——开放标注方式正确，无越断。

## 二、指定审查要点（invoke 末段 7 条）逐条裁

1. **竞态根因研判充分性** → **通过**。链条钉严（见 §一）；~30s 成因假设显式标注；30 实证义务足够强——钉死契约 5「30 须先复现竞态窗口（TC1 注入式红测或实证日志）再定方案，并在 30 invoke 留裁定依据」+ TC1「修复前红、修复后绿」构成硬性先行闸。
2. **方案开放性** → **通过**。A/B/C/D 四方向+组合开放，非范围首条挡死方向 D 默认实施；「先复现再定方案」可执行——机验形式 = TC1 红测记录 + 30 invoke 裁定依据留痕（缺一即验收不过）。
3. **钉死契约 2 transient/永久张力** → **通过**。张力被显式管理而非掩盖：手动 resume 409 对外语义钉死（test_hitl_resume.py:230 断言存续）+ 「若 30 裁定 transient 重分类须动此断言 → 先过 20/维护者裁定」——重分类涉及对外语义，裁定门槛归 20/维护者与 Harness 分工一致，合适。B1 表已注明「竞态复现构造与 409 断言同形态 · 须区分随后可见 vs 永久不可见」。
4. **TC1 注入式复现可构造性** → **通过**。仓内先例实证双支撑：test_hitl_resume.py:240-258 `_FakeGraph`（aget_state 返回 tasks 有 · interrupts 空）即「永久不可见」形态注入范式；tests/test_hitl_auto_resume.py 基建在案（:692-693 `InMemorySaver` + `_suspend(_hitl_state(), saver, "t-loop")` 真挂起构造 · :583 store-rebuild 补偿组）。「先 stranded 后可见」transient 时序可以 stateful mock aget_state（计数器翻转返回值）确定性构造，禁赌真竞态（FP-1）可行。
5. **最小面与 GATE_STOP** → **通过**。钉死契约 4 列明 nodes.py interrupt/persist 时序/store.py/router.py decide 挂点/T1 消费门/T4 guard 面 diff 空；GATE_STOP 触发条件明确（30 实证根因必须动最小面外任一面即触发）· 回 10/维护者裁定——方向 D 被挡回系刻意设计，裁定权归属表述准确（升级裁定 · 非 30 自裁）。
6. **图谱 n/a 触发回写条件** → **通过（带 N-2）**。触发条件钉清：graph_delta_note「若 30 引入新 env 旋钮或新机制面 → hitl 行备注回写 + HG-GRAPH-MODULES 00 代录」+ 钉死契约 7 例外路径互锁；本帽实证 `docs/_tech_graph/l1/01_modules.md:39` hitl 行已含 T2 机制备注（触发器/SKIP LOCKED 认领/补偿扫描/台账键族 triggered/claimed/compensated）——候选修复面确落既有覆盖面，n/a 预判有据。⚠ 空隙：新**台账键**（钉死契约 6 仅要求 30 invoke 钉名）是否触发图谱回写未明钉——记 N-2。
7. **验收文档分支引用** → **通过**。本帽实证 `f57b4ae` 存在于 `acceptance/20261010-hitl-consumption-loop` 且未 merge master（`git merge-base --is-ancestor` 判否）；task 依据节/现状锚点表/依赖节三处均注明分支+commit+未 merge——commit 级钉死不可漂移，引用充分、不阻塞 30；是否推动验收文档先行 merge 裁定权在维护者，task 表述准确。

## 三、钉死契约有效性（7 钉逐条 · 可机验性裁定）

| # | 契约 | 可机验性 |
|---|---|---|
| 1 | 无状态恢复纪律存续（禁 HTTP 自调 · 禁第二条恢复实现 · 就绪校验只读） | ✅ 可机验——T2 已留 `test_single_resume_path_in_router` / `test_trigger_carries_no_state_and_no_http_self_call` 机断先例（本帽 pytest collect 实证在集）· grep 调用点==1 钉 |
| 2 | 手动 resume 409 语义零 diff · 真·永久 stranded 判定能力不丢 | ✅ 可机验（test_hitl_resume.py:230 断言原样绿）· 重分类门槛「先过 20/维护者裁定」清晰 |
| 3 | manual/off 零 diff | ✅ 可机验（env 缺省/非法回退 manual 有 T2 测试面 · B1 全绿机断逐字节不变） |
| 4 | 最小面（hitl/auto_resume.py ± resume.py 注释/分类 ± 测试） | ✅ 可机验（git diff 路径集限定）· GATE_STOP 触发条件明确 |
| 5 | 方案开放 · 30 须先复现再定方案 | ✅ 可执行——TC1 红测硬闸 + invoke 裁定依据留痕双机验；「先复现」时序由「修复前红」口径强制 |
| 6 | 台账纪律（记动作不记内容 · 新键 invoke 钉名） | ✅ 可机验（grep 台账字面 · invoke 钉名可核） |
| 7 | 零新表/零迁移/零新 SSE 事件/零新 env | ✅ 全可机验（alembic head 不动 · SSE 事件 grep · env grep）· 例外路径（新 env → 图谱回写 + 契约 4 重审）钉清 |

transient/永久裁定门槛（钉 2）与「30 须先复现再定方案」（钉 5）双双清晰可执行，无含糊词。

## 四、TC1–TC5 可证伪性

- **TC1**：注入式构造可行（§二.4 先例双支撑）；「修复前该窗口形态触发 stranded_checkpoint、修复后不再抛出且最终恢复成功」可证伪；「对照形态或修复后单测直接钉绿 · 30 裁定并留痕」留有合理退路但强制留痕，可接受。
- **TC2**：caplog/台账断言无「HITL 自动恢复执行失败」+ 无 `ResumeError: stranded_checkpoint` + 首跑即恢复成功（无补偿重试轮）——全机断可证伪。
- **TC3**：live 口径明确——六 env 组 + auto + `SCAN_INTERVAL=5` 与验收文档操作便签段同构（命令级可复跑）；「decide 同秒 → 首个 claimed 即恢复成功 · 台账链无 stranded_checkpoint 重试轮」可证伪。
- **TC4**：反回归面完整三面——真·永久 stranded 409 存续（对外语义）· manual 零 diff（默认路径）· 39 枚原样绿+B1 全文件亲跑（既有机制）。本帽 `pytest --collect-only` 实证 `tests/test_hitl_auto_resume.py` = **39 枚**，与 task/B1 声称一致。
- **TC5**：工程面齐——pytest 基线 4 failed（capability_lookups×3+lg_rag_multi×1 环境性钉案照登 · 零新增红口径）+ ruff + graph-compile EXIT=0 + task lint PASS + 三闸 approved 后才 30，全部可机断。

## 五、最小面边界与方向 D 挡回

最小面收敛 `app/ops/hitl/auto_resume.py` 认领-执行路径（± resume.py 内部注释/分类 · ± 测试），边界枚举闭合（nodes.py/store.py/router.py/T1/T4 逐一列名 diff 空）；方向 A/B/C 均落在面内（A 认领后就绪校验 · C 执行体退避 · B 触发侧 delay——B 若动 router.py decide 挂点则触发 GATE_STOP，task 已用钉 4 兜住）；方向 D（动 LangGraph interrupt 元数据落库时序）挡回 10/维护者合理——超最小面+涉框架语义，升级裁定符合 Harness 分层。

## 六、图谱 n/a 预判触发回写条件

见 §二.6：n/a 预判有 hitl 行备注实证支撑；触发回写条件（新 env/新机制面 → hitl 行备注回写 + HG-GRAPH-MODULES 00 代录）钉清；HG-GRAPH-MODULES 闸 pending 与 n/a 预判口径一致（照实判定 · 若实证升级则回写后签）。

## 七、验收文档分支引用口径

见 §二.7：`f57b4ae` 未 merge master 照登合理 · commit 级引用不阻塞 · merge 裁定权维护者。

## 八、lint 复跑（不采信自报）

本帽亲跑：`npx --yes spec-wave task lint --file docs/tasks/active/task_hitl_auto_resume_claim_race.md` → **LINT: PASS · exit 0**（2026-10-10 本帽复跑 ✓ · 与 10 invoke 自报一致 · 余 W3 自检结论占位符 draft 期合法）。

## 思考轮审查（R0–R5）

控制表表头（轮/结论/early_stop/reason/residual_risks）齐 · `actual_last_round` 行在 · `### R0`–`### R5` 槽位齐 · 每轮 residual_risks 如实回填（窗口成因未实证 → 留 30 · 图谱判定为预判 → 触发条件兜底）· early_stop at R5 理由成立（范围/非范围/验收/failure_paths/锚点齐备 · 方案开放性刻意留 30 · 再轮无新增信息）。R1 证据收集与本帽亲读结论逐环一致；R3 反例（真·永久 stranded 不可误伤 · transient/永久区分 · B1 冲突面）均落入钉死契约与 failure_paths，无漏环。行为变更类 task 旧测影响面（B1 表 7 文件）在案 ✓。

## 非阻塞观察项（N-1~N-3）

- **N-1**：`tests/test_hitl_resume.py:230-259` 锚点窗尾微偏——测试体实延至 :260（第二断言 `assert "旧版本" in exc.value.detail or "interrupt" in exc.value.detail` 在 :260）；主断言 :259 在窗内，语义无损。
- **N-2**：图谱回写触发条件未显式含「新台账键」——钉死契约 6 仅要求 30 invoke 钉名；hitl 行备注（l1/01_modules.md:39）已列台账键族，若 30 新增重试/就绪台账键，建议同步评估行备注是否补键名（低成本 · 不阻塞开工）。
- **N-3**：TC1「修复前红」依赖 30 执行序（先注入红测后实现）——钉死契约 5 已强制 invoke 留裁定依据，建议 30 invoke 模板显式记「红测先于实现」时序证据，免收口争议。

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（PASS-WITH-NITS · N-1~N-3）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] 裁定验收文档 `f57b4ae` 是否先行 merge master（不阻塞 · 裁定权维护者）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-10 | 20 R1 书面审：码面锚点 8 处全亲读核真 · 7 指定要点逐条通过（要点 6 带 N-2）· 钉死契约 7 条可机验 · TC1–TC5 可证伪 · lint 亲跑 PASS exit 0 · 思考轮闭合 · 裁定 **PASS-WITH-NITS**（N-1~N-3）· 三流程闸 pending 未代签 |
