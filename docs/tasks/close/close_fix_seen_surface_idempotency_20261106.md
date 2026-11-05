# CLOSE：fix-seen-surface-idempotency（reset seen 面后首轮巡检不重复拉起存量 write ticket · 幂等守卫双点半卫）

> 关账日期：2026-11-06 · 关账人：bot 全棒链执行（10 → 20 → 30 → 40 → 50 CLOSE · 同日闭环）· 维护者令 issue #335 comment `6670686601`（40 复跑销项 · 窗口至 2026-11-06 07:00）
> 体例承 [close_fix_delegation_resume_approval_id_20261106.md](close_fix_delegation_resume_approval_id_20261106.md)

## 一、任务信息

| 项 | 值 |
|---|---|
| task | [`task_fix_seen_surface_idempotency.md`](../done/task_fix_seen_surface_idempotency.md)（已归档 done/） |
| 性质 | fix / 缺陷修复（worker 重启后 seen 面重置无幂等守卫 · reset 后首轮巡检重复拉起存量 write ticket · overlap_warning 噪音 · issue #335 backlog） |
| 由来 | issue #335（来源 #323 stage-w 40 invoke 实测证据链）· 30 红测探针实证承载面 = nodes.py 拉起链双点（join 巡检派发面 + `_persist_hitl` 建单面）：修复前同 run 同写意图库面 2 笔票 + 写闸拦截行双拉起 |
| PR | [#345](https://github.com/Cyning12/ops-desk-api/pull/345)（10 起草 · squash `ec87535` · CI 4/4 绿 · lead review APPROVED `5792245814` 签认四闸 + 决策点②）· [#346](https://github.com/Cyning12/ops-desk-api/pull/346)（30 实现 · squash `6daccb1` · lead 验收合并） |
| 闸 | HG-WRITE-TICKET-IDEMPOTENCY-DESIGN（决策点②签认 = status/seen_surface 双条件位 · 决策点①经 #6669768156 委派 30 探针裁决 = 案 A∪B 双点半卫）· HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES（lead 签认 · 依据 PR #345 review `5792245814` + issue #335 `6668554143`/`6669768156`） |

## 二、交付清单

| 产物 | 说明 |
|---|---|
| `app/ops/lg_rag/multi/nodes.py` 巡检层守卫 | `_write_blocked_call_keys`：在途写单步（capability_write 拦态 ∧ hitl_required）canonical 索引；重规划孪生步命中 ⇒ 继承在途终态（`replay_of` 溯源 · 不派发不消费 · 留痕 `write_ticket_twin_inherited`） |
| `app/ops/lg_rag/multi/nodes.py` 建单层守卫 | `_write_intent_live_key`（status 位）：库面 live 写单按 (capability_id, args_summary) 索引（pending 全量 + approved 未过期 TTL 同消费门口径）；命中 ⇒ `arelocate_linkage` 迁附当前步带回不新建（留痕 `hitl_write_intent_attached`）；与 `already`（seen_surface 位）合成 status ∧ seen_surface 双条件 |
| `app/ops/hitl/store.py::arelocate_linkage` | 存量 live 单（pending/approved）连接域迁附（Protocol/InMemory/Db/Null 全实现 · live 状态守卫 · 终态不可改挂 · 只动连接域不动语义字段） |
| `tests/test_fix_seen_surface_idempotency.py` | 3 枚红测先行：负样本（reset seen 面 → 首轮巡检 → 存量票恰一笔 + overlap 零新增 · 先红后绿）· 对拍①同 sid 重放 attach 零漂移 · 对拍②成功孪生 replay-guard 面零漂移 |
| 旧测适配 | **零适配**（实扫关联 122 枚断言对象均不锚孪生写步建单形态 · 如实列出） |
| 过程文档 | task 档（四闸签认 + 决策点①裁决留痕 + 全棒自检）· 20-R1 审查文（lead 人审转录 · 非自签）· 10/20/30/40/50 invoke 全落盘 |

## 三、验收核验（全 PASS · 机制面关账）

| 验收 | 结果 |
|---|---|
| 红测负样本（维护者红线） | ✅ 先红（修复前库面 2 笔同写意图票 + 写闸拦截行双拉起）→ 后绿（恰一笔 + 拦截行零新增 + 孪生步不派发 · stash 复验同形态 RED） |
| 决策点②双条件语义 | ✅ status 位（库面 live 单索引 · 过期 approved 不 live 同消费门口径）∧ seen_surface 位（already 本轮面）落地 · FP-6 防单条件化注释显性化（不同 args ⇒ 不同 intent 键不合并） |
| 常规对拍 | ✅ 同 sid 重放 attach 既有语义零漂移 · 成功孪生 guard-skip 面零漂移（2 枚对拍绿） |
| 四红线零 diff | ✅ 消费门（`_approval_consumed`/`_write_execution_approval`/`_match_fresh_approved`）· resume 单路径（`router.py`/`resume.py`）· SSE 事件表（`event_store`/`sse_*`）· worker freeze（`run_worker.py`）全零 diff；守卫共用既有 `LG_RAG_WRITE_REPLAY_GUARD_ENABLED` 单开关（关 = 基线零 diff） |
| 工程面 | ✅ 30 自检 + 40 独立双证：全量 2068 passed · 4 failed = 既有基线同形（diff-whitelist ×2 / embedder env ×1 / dualproc env ×1 · worktree 对照）· ruff 零新增 · graph-compile EXIT=0 · verify PASS |
| 40 复跑销项 | ✅ 机制面 PASS——独立复跑（不采信 30 自报）：worktree `/tmp/verify40-seen` @ `6daccb1` 新测 3 / 关联 119 / 全量 2068 零新增红 · 红线对拍零命中 |

## 四、偏差与裁定留痕

- **决策点①裁决修正（10 档倾向经探针修正 · 锚点留痕纪律）**：10 档 R2 倾向案 A（巡检层单点）· 30 探针实证承载面双点后裁决 = **案 A ∪ 案 B 同链双点半卫**——单点半卫各有盲区（join 只看得见 plan 内终态；persist 看得见库面但拦不住已发生的重复派发噪音）· 留痕位：task 档 30 注 / D-fix-1 / 30 invoke / 本档。
- **偏差①（live 面未跑 · 口径登记）**：维护者 40 令（`6670686601`）明确范围 = 独立复跑对拍 + 关联回归 + 全量零新增红（机制面），未含 live 要求 → live 实测未执行；若后续补 live 撞 #339 planner-args 已知缺陷，按 #329/#334 同口径登记（机制面 PASS + 偏差如实 · 不静默修）。
- **偏差②（环境性）**：40 worktree 无 `.env` 环境下全量套件墙钟显著拉长（网络型用例走真实超时路径）——环境性非仓码语义，套件结果与同形基线判定不受影响。

## 五、关账动作

- 档迁：`docs/tasks/active/` → `docs/tasks/done/`（本 CLOSE 档 + done/README + active/README 同步 + 40/50 invoke）；
- issue #335：维护者执行关 issue（bot 不 close issue · 已声明）；
- 后续跟踪：无另波（#339 planner-args 已有独立 issue 跟踪 · 非本 task 产物）；
- 评审署名登记：PR #345 / #346 的 lead（Cyning12）review 均因 merge 先于署名改写，**未署名记录**（按规不 rewrite 已合并 PR · 此处登记）。

## 六、棒链留痕

| 棒 | 交付 | PR / 落点 |
|----|------|-----------|
| 10 | task 档起草（四闸 pending · NO-GO 20/30 · 实扫声明诚实） | #345 squash `ec87535` · CI 4/4 绿 · lead review APPROVED 签认四闸 + 决策点② |
| 20 | 四闸签认代录 + R1 审查文（lead 转录 · 决策点①委派 30 探针裁决） | PR #345 review `5792245814` → 30 分支闸据档 `0902e9d` |
| 30 | 双点半卫（nodes.py 拉起链 + hitl/store.py arelocate_linkage · +225/-1）+ 红测 3 枚先红后绿 | #346 squash `6daccb1` · lead 验收合并 |
| 40 | 独立复跑全绿（worktree `/tmp/verify40-seen` @ `6daccb1` · 不采信 30 自报）· 偏差①②登记 | `invoke_20261106_40_verify.md` |
| 50 | 本 CLOSE 收口 | 本档 + done/README + active/README + `invoke_20261106_50_close.md` |
