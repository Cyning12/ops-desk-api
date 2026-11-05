# Invoke · 30 帽 · 实现交付（fix-delegation-resume-approval-id）

| 字段 | 值 |
|------|-----|
| hat_id | `30`（implement · 改码棒 · 消费层双消费合一） |
| task_slug | `fix-delegation-resume-approval-id` |
| task_paths | `docs/tasks/active/task_fix_delegation_resume_approval_id.md` |
| related_review_or_none | `docs/harness/reviews/task_fix_delegation_resume_approval_id_audit_R1_20261106.md`（20-R1 · lead 人审转录） |
| git_branch | `fix/delegation-resume-approval-id`（reset 自 origin/master `c162d1d` = PR #341 squash 合入点） |
| created_utc_or_local | 2026-11-06 |
| notes | 30 授权 = issue #334 comment `6664735511`（六交付条件）+ comment `6665660681`（**锚点修正裁定 + 第七条交付条件**）；GATE_VERIFY 闸据 = task 档闸表（VERIFY: PASS 后开工） |

---

## §1 · 调查与锚点修正（第七条交付条件履行 · 如实留痕）

- **签认锚点 `:2162+:2177`（= `_approved_fresh_for_subtask`/`_persist_hitl` 建单守卫区）经红测探针端到端实证为干净面**：graph state / 工人 Send 载荷 / replan 保号行 / checkpoint（挂起 + resume 后）主·delegation 双路径全净，不含任何 approval_id 消费或残留。
- **真实缺陷（维护者裁定 `6665660681` 确认 · lead 亲核 :420-504）**：delegation 路径 resume 后同一 approval_id **双消费**——签发门 `_approval_consumed`（`delegation_approval_consumed{request_id}` 台账 · :411 面）+ 写闸 `_write_execution_approval`（`capability_write_approval_consumed{approval_id}` 台账 · :506 面）独立触达同一 approved 单据；主路径（capability_write 类）仅写闸单消费。**一单两审，语义不齐**。
- **锚点修正已如实入档**：task 档闸表设计闸行（删除线 + 裁定引注）· 背景缺陷段改写（探针证据 + 裁定引注）· D-fix-1 交付记录 · 本 invoke——**无静默改档**。

## §2 · 实现摘要

- **改码面唯一**：`app/ops/lg_rag/multi/nodes.py::_write_execution_approval`（+18/-3 · 注释显性化裁决依据与契约）。
- **语义（零行为变化）**：delegation 类命中 = **查命中不重复消费**——同一 fail-closed `_match_fresh_approved` + W2 租户守卫 + 返回行（`approval_id` 注入与三照串链不变），提前返回不再记 `capability_write_approval_consumed` 台账；delegation 类单据消费归签发门单点（`delegation_approval_consumed` 即唯一消费记录）。capability_write 类消费形态与主路径逐字节一致。
- **红测先行（先红后绿可见）**：`tests/test_fix_delegation_resume_approval_id.py` 2 枚——
  - 负样本（红线）：delegation on 全链 resume（签发拦下 → 图真挂起 → decide → 真 resume → replan 保号 → 签发门放行 → 令牌 → tool_exec 真执行），断言同一 approval_id 消费台账**恰一笔**（签发门面）+ 写闸无第二笔 + 真落笔 + 三照（台账 request_id / gateway span approval_id / 执行回执）串链。**修复前 RED**（双消费两笔并存）→ 修复后绿；
  - 对称对拍：主路径（delegation off · capability_write 闸）resume 后写闸单消费形态与修复前零漂移。
- **旧测适配**：实扫**零适配**——delegation 消费 / write 闸 / replan quality / stage-w / fix-worker-state 全组 190 枚断言对象均不锚写闸 delegation 类台账（W2④ 仅断言放行+执行）。

## §3 · 验证

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `pytest tests/test_fix_delegation_resume_approval_id.py`（先红） | 1 | RED：修复前同一 approval_id 双消费（签发门 :411 + 写闸 :506 两笔并存） |
| `pytest tests/test_fix_delegation_resume_approval_id.py`（后绿） | 0 | 2 passed |
| 关联回归 5 文件（hitl_approval_consumption / write_approval_gate / hitl_approved_replan_quality / fix_worker_state_send_run_id / hitl_resume） | 0 | 101 passed 零适配 |
| 关联回归 4 文件（stage_w_write_expand / capability_testing_write / lg_rag_delegation_wiring / capability_delegation） | 0 | 89 passed 零适配 |
| `pytest tests`（全量 · 本机） | 0 | 2065 passed · 4 failed = master `c162d1d` **既有红基线**逐项同形对照（worktree 实证）：diff-whitelist 锚点漂移 ×2 / embedder env ×1 / dualproc env ×1——**零新增红** |
| `ruff check app tests` | 1 | 13 枚 master 既有基线（UP038/UP007）· 本波新文件 3 枚已修（I001/B007×2）· 触及路径零新增 |
| `./scripts/graph-compile.sh` | 0 | EXIT=0 |
| `npx spec-wave verify --target . --task docs/tasks/active/task_fix_delegation_resume_approval_id.md` | 0 | VERIFY: PASS（出货前闸态） |
| 红线对拍 `git diff origin/master --stat` | 0 | app/ 唯一 `nodes.py`（+18/-3）· `hitl/**` / `registry.py` / `policy.py` / SSE 事件表 / web freeze 零 diff · resume 单路径（`router.py`/`resume.py`）零 diff |

## §4 · 六+一交付条件对照（issue #334 #6664735511 / #6665660681）

1. ✅ 红测先行可见红→绿：负样本 = delegation resume 后 approval_id 单消费（签发门唯一台账）+ 真落笔 + 消费闭环三照，端到端（真派发路径 + 真 resume）；
2. ✅ 旧测适配不放宽随 PR：实扫**零适配**（190 枚关联全绿 · 断言对象均不锚写闸 delegation 台账 · 如实列出）；
3. ✅ 改码面唯一收敛：唯一码文件 `nodes.py::_write_execution_approval`（+18/-3）——签认锚点经实证作废后修复面收敛消费层（维护者裁定 · 非静默偏离）；
4. ✅ 四红线零 diff 对拍：resume 单路径 / SSE 事件表零 diff / 消费门 fail-closed 永不放宽（匹配 + W2 租户守卫原样 · TA2/W2 负样本组全绿）/ 改码面收敛；
5. ✅ ruff + pytest + graph-compile 全绿（口径见 §3 · 既有基线红如实登记）；
6. ✅ PR 说明逐条对照（本表）+ 30 invoke 落档待审；
7. ✅ **锚点修正如实留痕**：task 档闸表行 + 背景缺陷段 + D-fix-1 + 本 invoke 均记录「签认锚点探针实证干净面作废 · 真实缺陷 = 双消费」。

## §5 · 下一棒

PR 出货待 lead 终审（不 merge · 不 auto-merge）→ 40 复跑销项（live delegation on 全链 resume 实测 · 单消费达成）→ CLOSE。

---

### 修订

| 日期 | 说明 |
|------|------|
| 2026-11-06 | 30 实现棒 invoke 落档：调查/锚点修正/实现/验证/七条件对照全录 |
