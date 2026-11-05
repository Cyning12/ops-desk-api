# Invoke · 30 帽 · 实现（fix-seen-surface-idempotency）

| 字段 | 值 |
|------|-----|
| hat_id | `30`（实现棒 · 红测先行先红后绿） |
| task_slug | `fix-seen-surface-idempotency` |
| task_paths | `docs/tasks/active/task_fix_seen_surface_idempotency.md` |
| related_review_or_none | `docs/harness/reviews/task_fix_seen_surface_idempotency_audit_R1_20261106.md`（20-R1 文随本 PR 落盘） |
| git_branch | `fix/seen-surface-idempotency`（30 实分支 · 承签认档预登记） |
| created_utc_or_local | 2026-11-06 |
| notes | 维护者 issue #335 comment `6669768156` 30 授权（六交付条件）· 签认依据 = PR #345 review `5792245814` + 窗口授权 2026-11-05 22:26 指令；决策点①委派工人探针裁决并引用本评论 |

---

## §1 · 实现摘要

- **探针定位（红测先行）**：负样本真链复现——首轮巡检建单 T1(sid=A) → 图真挂起 → **checkpoint 重建（worker 重启语义 · 前置断言 `hitl_requests` 必空 = seen 面重置）** → 重规划孪生步 B（同写意图新 sid）→ join/写闸/persist 首轮。**修复前 RED 实证**：同 run 同写意图库面 **2 笔**（`hitl_…:1` / `:2` 各一票）+ 写闸拦截行 **2 条**（overlap 双拉起噪音）——承载面 = `nodes.py` 拉起链双点：join 巡检派发面（孪生步重复派发）+ `_persist_hitl` 建单面（精确 sid 去重对孪生 sid 不可见 ⇒ 重复建单）。
- **设计闸决策点①裁决**（引用 #6669768156）：**案 A ∪ 案 B 同链双点半卫**（10 档 R2 单点倾向经探针修正 · 锚点留痕）——
  1. **巡检层守卫**（`_write_blocked_call_keys` + 孪生继承）：同写意图在途写单步（blocked_by=capability_write ∧ hitl_required 的终态）被重规划孪生时，孪生步继承在途终态（`replay_of` 溯源 · 不派发不消费 · 留痕 `write_ticket_twin_inherited`）；
  2. **建单层守卫**（`_write_intent_live_key` = status 位真源）：库面 live 写单（capability_write 类 ∧ 带 write_intent · pending 全量 + approved 未过期 TTL 同消费门口径）按 (capability_id, args_summary) 索引；命中 ⇒ `arelocate_linkage`（store 增量方法 · Protocol/InMemory/Db/Null 全实现 · live 状态守卫）存量单连接域迁附当前步（subtask_id/unlock_subtask_id）并带回 `created`，**不新建**（留痕 `hitl_write_intent_attached`）；与 `already`（seen_surface 位）合成 **status ∧ seen_surface 双条件**（决策点②签认语义落地：只看 seen 位=本缺陷；只看 status 位=不同 args 合法写被误并——args_summary 决定性序列化防 FP-6）。
- **改码面唯一**：`app/ops/lg_rag/multi/nodes.py`（+151/-1 · 双点半卫 + 注释显性化裁决依据）+ `app/ops/hitl/store.py`（+75/-0 · arelocate_linkage 增量 · 无表结构/语义面变更）+ 新测 `tests/test_fix_seen_surface_idempotency.py`（3 枚）。守卫共用既有 `LG_RAG_WRITE_REPLAY_GUARD_ENABLED` 单开关（关 = master 基线零 diff）。
- **四红线零触碰**：消费门（`_approval_consumed`/`_write_execution_approval`/`_match_fresh_approved`）/ resume 单路径（`router.py`/`resume.py`）/ SSE 事件表（`event_store`/`sse_*`）/ worker freeze（`run_worker.py`）/ 委派令牌 / HITL 表结构 / auto-resume 全零 diff。

## §2 · 六交付条件对照（issue #335 comment `6669768156`）

| # | 条件 | 结论 | 证据 |
|---|------|------|------|
| 1 | 红测先行：负样本走真巡检/派发路径，先红后绿留 invoke 档 | ✅ | 负样本真链（join→写闸→persist→真挂起→checkpoint 重建→重规划）· 修复前红（2 笔票 + 双拦截行）→ 修复后绿（恰一笔 + 零新增）· 同形态 stash 复验 RED |
| 2 | 常规对拍：无重置巡检轮次零漂移 | ✅ | 对拍①同 sid 重放 attach 既有语义 · 对拍②成功孪生 replay-guard 面零漂移（2 枚绿） |
| 3 | 改码面收敛唯一落点 | ✅ | `git diff` 面 = `nodes.py` + `hitl/store.py` 唯一（+225/-1 含注释）；承载面探针定位如实留痕（task 档 30 注） |
| 4 | 四红线零 diff 对拍 | ✅ | SSE 事件表零 diff · 消费门 fail-closed 负样本组全绿（`test_write_approval_gate`/`test_hitl_approval_consumption`）· resume 单路径（`router.py`/`resume.py` 零 diff · A5 grep 承既有测试组）· worker freeze（`run_worker.py` 零 diff） |
| 5 | ruff + pytest + graph-compile 全绿（CI 4/4） | ✅ | `ruff check app tests` All checks passed（零）· 全量 2068 passed + 4 failed = master 既有基线同形（diff-whitelist ×2 / embedder env ×1 / dualproc env ×1 · stash 复验同 4 枚）零新增红 · `graph-compile.sh` EXIT=0 |
| 6 | 20-R1 审查文随 30 PR 落盘 | ✅ | `docs/harness/reviews/task_fix_seen_surface_idempotency_audit_R1_20261106.md`（lead 人审转录 · 非自签） |

## §3 · 验证

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `pytest tests/test_fix_seen_surface_idempotency.py`（负样本 · stash 修复后先红） | 1 | RED：reset 后首轮巡检库面 2 笔同写意图票 + 写闸拦截行双拉起 |
| `pytest tests/test_fix_seen_surface_idempotency.py`（修复后） | 0 | 3 passed（负样本 + 对拍 ×2 · 后绿） |
| `pytest`（8 文件关联回归组） | 0 | 122 passed 零适配 |
| `pytest tests`（全量） | 0* | 2068 passed · 4 failed = master 既有基线同形（*4 枚 stash 复验 baseline 同红 · 零新增红） |
| `ruff check app tests` | 0 | All checks passed（零） |
| `./scripts/graph-compile.sh` | 0 | EXIT=0 |
| `npx spec-wave task lint --file docs/tasks/active/task_fix_seen_surface_idempotency.md` | 0 | LINT: PASS |
| `npx spec-wave verify --target . --task docs/tasks/active/task_fix_seen_surface_idempotency.md` | 0 | VERIFY: PASS（四闸 approved · 出货前闸态） |

## §4 · 下一棒

出货 PR 待 lead 终审（六条件已逐条对照）→ 40 复跑（live 面：worker 重启后首轮巡检单拉起实证 · 承 40 invoke 惯例）→ CLOSE。

---

### 修订

| 日期 | 说明 |
|------|-----|
| 2026-11-06 | 30 实现棒 invoke 落档（探针定位 + 决策点①裁决 + 六条件对照 + 先红后绿实证） |
