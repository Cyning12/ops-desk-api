---
title: task · fix · #434 worker-fired run 面板可见性（thread 行 upsert）
---

# task · fix · #434 worker-fired run 面板可见性（thread 行 upsert）

> **状态**：`active`（2026-11-17 落卡 · 夜间自动执行波）
> **来源**：issue Cyning12/ops-desk-api#434（第一项 · 第二项「离线交付触达面」属 APNs 下波不做）· 授权 issue Cyning12/ops-desk-workspace#23（m03064/m03283/m03694 夜间授权 · 契约真源 15-p3-contracts.md §1「thread 不存在 fire 时自建」）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | fix-434-worker-thread-upsert |
| base | 396f7fed |
| 关联 issue | Cyning12/ops-desk-api#434（仅第一项） |
| 关联 PR | （待补 · feat PR squash merge 后回填） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack；本波为 worker fire 路径小修 + 图谱登记 |
| graph_change_layer | G-L1（01_modules.md schedule 行 fix-434 备注 + HG-GRAPH-MODULES 签收行） |
| review_hat | 20（R1 审查文已落盘 · GO） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 30 | approved 2026-11-17 · 授权 issue Cyning12/ops-desk-workspace#23 m03064/m03283/m03694（夜间授权）+ issue #434 为唯一范围真源 |
| HG-AUDIT-R1 | approved | 30 | approved 2026-11-17 · 同上授权 + R1 审查文 docs/harness/reviews/task_fix_434_worker_thread_upsert_audit_R1_20261117.md（GO） |
| HG-GRAPH-MODULES | approved | 30 | approved 2026-11-17 · 同上授权（schedule 行 fix-434 备注属图谱登记义务 · 随 30 交付回填） |

## 背景

P3-T11 验收（S1/S2/S3 工程判据全过）暴露 (b) 类实例级缺口（issue #434 第一项）：Schedule worker 点火（`app/ops/schedule/worker.py::_execute_fire`）时若目标 thread 无 turns（对话从未发生过），契约 15 §1 允许「thread 不存在 fire 时自建」，但既有实现只保证归因 turn 落库路径（`thread_store.persist_thread_turns` 于 run done 时兜底建行），fire 落 run 行到 done 之间的窗口、以及 run 失败/waiting_approval/断连等不走到 persist 的终态下 thread 行不存在——面板按 thread 归聚（`runs_router.py::_load_runs_page` → `thread_store.thread_owner` 返回 None → 404 不泄露存在性 · 承 history_router FP-1）即 404/卡片不可见。本波在 worker fire 路径补 thread 行 upsert，把「自建」语义前移到点火落 run 行同事务。

## 范围

1. **修复**：`app/ops/schedule/worker.py::_execute_fire` R6 归属复核后、create_run 前补 thread 行 upsert——thread 不存在则 `db.add(OpsLgRagThread(id=schedule.thread_id, user_id=schedule.user_id))`（最小字段 · user_id=creator · created_at/updated_at 列默认 · 承 thread_store.py:35/:95 先例形态）；已存在且属 creator 不动；外来 thread 维持 R6 failed 语义零改动。OpsLgRagThread 模型（app/db/models.py:226-238）仅 id/user_id/created_at/updated_at 四列无 tenant_id 列（委派书「最小字段含 tenant_id」按模型实际裁剪 · 偏差 D1 登记）。upsert 与 fire 状态机写回同事务（失败整体回滚 · 不留半建行）。
2. **测试**（真 PG postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五键 blank 前缀）：
   - 新增用例：无 turns 的 schedule + fire → 断言 ops_lg_rag_threads 行存在（id/user_id 对得上 creator · 既有行 created_at/updated_at 不被改写——二火回归）；
   - 端到端可见性：fire 后真 GET /api/ops/lg-rag/threads/{thread_id}/runs → 200 且 runs 卡片含该 run_id（承 tests/test_lg_rag_runs_readonly_api.py 先例形态）；
   - 既有 tests/test_schedule_worker.py / test_schedule_rest.py / test_schedule_store.py / test_p3_t2b_create_schedule_capability.py / test_ops_schedule_ddl.py / test_lg_rag_runs_readonly_api.py（T2/T2b/T3/T4 面）回归零红；全量 pytest 绿（环境性红与 base 396f7fed 同路径基线逐签对照 · CI 终裁）。
3. **图谱**：`docs/_tech_graph/l1/01_modules.md` schedule 行补 fix-434 备注（fire 同事务 thread upsert）+ HG-GRAPH-MODULES 签收行（承 :41/:42 先例）。
4. **落盘**：registry entry（status=active → close 波 closed）· invokes by-task/fix-434-worker-thread-upsert/{10,30,40,50} · R1 审查文 · task 档 active→done。

## 非范围

- 不做 issue #434 第二项「离线交付触达面」（APNs/通知属下波 · 已在 workspace 14 文 R21 登记）——close issue 时评论注明再处置。
- 不改 R6 外来 thread failed 语义 · 不改 runs_router/runs 只读端点（T4 已交付零改动）· 不改 thread_store（persist 兜底建行保留 · 双路径幂等）。
- 不碰 alembic/（零新迁移 · thread 表早已存在）· scripts/ · skill_registry/ · SSE/契约面 · lg_rag 本体。
- 观察项两条（HITL 三次批准 UX · resume 旧格式 checkpoint 误标）不修仅登记来源 issue。

## 失败路径

- upsert 撞并发（两 schedule 同 thread_id 并发 fire · PK 冲突）→ 该 fire 走既有 except 路径 rollback + failed + logger.exception（不重打 · 14 §11）；下一 tick/relink 不自动重火同 fire（台账终态）——判据：撞并发概率极低且语义安全（failed 可审计）。
- thread 表不可写（DB 故障）→ 同 create_run 失败路径 failed 留痕。
- 既有行属 creator 但 user_id 类型不一致（UUID vs str）→ 统一 str() 比较（承 :230 既有形态）。
- 并行 agent 撞 registry.yaml / 01_modules.md 同区冲突 → rebase origin/master 保留双方 entry 手动解，冲突块如实登记。
- 仓根 .env 经 tests/test_check_vector_waterline.py 裸 load_dotenv 渗入 worktree 收集期致全量 pytest 环境性红 → 与 base 396f7fed 同路径基线逐签对照登记，CI 终裁。
- 脏树期 wave_gate_registry 红为结构性常态（委派书钉明）。

## 验收标准

- [ ] `_execute_fire` 补 thread upsert：无 turns 的 schedule fire 后 ops_lg_rag_threads 行存在（id=schedule.thread_id · user_id=creator）；既有行（属 creator）二火后 created_at 不变（已存在不动）
- [ ] 端到端：fire 后 GET /api/ops/lg-rag/threads/{thread_id}/runs（creator 会话）→ 200 · runs 列表含 fire.run_id（不再 404）
- [ ] R6 外来 thread 回归：foreign thread fire 仍 failed · 不建行（tests/test_schedule_worker.py::test_foreign_thread_failed 绿）
- [ ] T2/T2b/T3/T4 目标六测试文件回归零红；全量 pytest 绿（环境性红逐签对照 base 396f7fed）
- [ ] `ruff check app tests` 绿
- [ ] 01_modules.md schedule 行 fix-434 备注 + HG-GRAPH-MODULES 签收行
- [ ] registry entry active · invokes 四件 · R1 审查文 · spec-wave task lint PASS

### 自检结论

验收 7 条全过（2026-11-17）：upsert 三用例真 PG 绿（建行/二火不动/端点 200 含 run_id）· R6 外来 thread 回归绿（test_foreign_thread_failed）· 目标六文件 105 passed · ruff 绿 · 图谱两件落盘（schedule 行 :40 备注 + HG-GRAPH-MODULES 签收行）· 过闸四件齐（registry active entry · invokes 10/30/40 · R1 审查文 GO · lint PASS）。全量 pytest 2442 passed / 4 failed——逐签对照：test_hitl_decide_owner_fallback::test_db_frameless_run_decide_via_real_thread_owner 与 test_hitl_pending_decide::test_db_decide_survives_store_rebuild_then_resume 在 base 396f7fed 同路径同红（环境性基线红 · 与本波无关）；test_lg_rag_write_replay_guard::test_tc8_diff_whitelist 与 test_wave_gate_registry 为脏树期结构性红（在途 worker.py 改动未入他 entry allowed · base 干净树绿 · 提交后闭窗复绿 · CI 终裁）。

## 必读列表

- issue 真源：Cyning12/ops-desk-api#434（第一项 · P3-T11 终报 /tmp/opsdesk-rfc/p3-t11-exec.md 偏差节）
- 契约真源：`../ops-desk-workspace/docs/01-scope/03-general-agent/15-p3-contracts.md` §1（thread_id 无 FK · fire 时不存在则 worker 自建）
- 代码锚：`app/ops/schedule/worker.py:229-240 _execute_fire R6 复核` · `app/ops/lg_rag/thread_store.py:35 resolve_thread_for_user 建行先例 · :82-107 persist_thread_turns 兜底建行` · `app/ops/lg_rag/runs_router.py:68-74 归属 404` · `app/db/models.py:226-238 OpsLgRagThread`
- 体例先例：`docs/tasks/done/task_p3_t3_schedule_worker.md` · registry `docs/harness/audit_gates/registry.yaml` · 图谱签收承 01_modules.md:41/:42
- 测试先例：`tests/test_schedule_worker.py`（_mk_user/_mk_schedule/worker_spy）· `tests/test_lg_rag_runs_readonly_api.py`（runs 端点 200/404 面）

## 思考轮

| 轮 | 结论 | early_stop |
|----|------|-----------|
| R0 | 范围对账（委派书 vs issue #434 第一项 vs 契约 15 §1）done | false |
| R1 | 失败路径推演（并发 PK 冲突 · DB 故障 · 类型一致 · 环境性红）done | false |
| R2 | 非范围边界（第二项留 APNs 波 · R6 语义零改 · T4 端点零触）done | false |
| R3 | 关键决策记录（upsert 落点=worker._execute_fire 同事务 · 最小字段按模型裁剪 · persist 兜底保留）done | false |
| R4 | 体例对账（T3 模板 · registry/invokes/审查文/图谱登记）done | false |
| R5 | 收尾复核（验收 checklist 全锚定）done | false |

actual_last_round: R5

### R0 · 范围对账

委派书四条与 issue #434 第一项逐条对齐：修 worker fire 路径 thread upsert（范围 1）· 真 PG 验证含 runs 卡片端点 200（范围 2）· issue 处置裁量（评论注明第二项留 APNs 波后关闭 · 或标题后缀——收口时按 issue 现状执行）· 图谱签收（范围 3）。契约 15 §1「thread 不存在 fire 时自建」为修复正当性真源。

### R1 · 失败路径推演

见「失败路径」节。推演增补：upsert 插在 R6 复核之后——外来 thread 在 R6 已 failed 返回，不会走到建行；thread 不存在且 user 悬空时 R11 先 failed，建行不执行（顺序：R11 user → R6 thread → upsert → create_run）。

### R2 · 非范围边界

issue 第二项（离线交付触达面）属 APNs 下波（契约草案 15 §6 · 14 文 R21 已登记）；R6/R11 语义、runs 端点、thread_store 均零触；allowed_app_files 仅 worker.py 一件机判守；alembic//scripts/ banned。

### R3 · 关键决策记录

- **upsert 落点=worker._execute_fire 同事务**：选 fire 路径而非「归因 turn 落库路径」（委派书允许二选一）——persist_thread_turns 只在正常 done 且 user_id 非空时调用（sse_stream.py:504-506），waiting_approval/error/disconnected 终态不走 persist，只改 persist 补不齐窗口；fire 同事务建行覆盖全终态且与 run 行同生共死（失败整体回滚不留半建行）。
- **最小字段按模型实际裁剪**：OpsLgRagThread 无 tenant_id 列（models.py:226-238 · thread SoT 归属谓词=user_id · tenant 隔离经 runs/turns 各自 tenant 列与归属谓词链承担），委派书「thread_id/tenant_id/user_id/created_at」裁为 id+user_id（created_at/updated_at 列默认）——偏差 D1 登记。
- **persist 兜底保留**：thread_store.persist_thread_turns:93-95 建行逻辑不动（双路径幂等 · SSE/invoke 面 thread 懒建行语义不破）。
- **已存在不动判据**：测试二火（同 thread 第二次 fire）断言 created_at 不变 · user_id 不变（ORM add 仅在 row is None 分支 · 既有行走 updated_at onupdate 也不触——upsert 分支不 add 不改）。

### R4 · 体例对账

照 T3/T7：task 档结构/人工闸表/registry entry（base=396f7fed · allowed_app_files=[app/ops/schedule/worker.py] · banned_prefixes=[alembic/, scripts/]）/invokes by-task 四件 {10,30,40,50}/R1 审查文 GO 机读词/spec-wave@3.5.0 task lint PASS 为闸；图谱签收承 :41/:42 先例。仓规条款一遵守（走 20-R1 审查文非 --allow-no-review）。

### R5 · 收尾复核

验收 7 条逐条锚：upsert 断言+二火回归（新用例）· 端点 200（新用例）· R6 回归（既有用例）· 六文件回归+全量 · ruff · 图谱两件 · 过闸四件。回退=revert 单文件（worker.py upsert 块）零迁移。

## 实现备忘

### 偏差登记

- **D1（最小字段裁剪）**：委派书列「thread_id/tenant_id/user_id=creator/created_at」，OpsLgRagThread 模型（app/db/models.py:226-238）无 tenant_id 列（thread SoT 归属谓词=user_id）→ 实落 id+user_id 两显式字段（created_at/updated_at 走列默认）。如实登记。

### 限制登记

（40 收口时按需回填）

## 测试策略

pytest tests（CI 终裁 · 真 PG postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五键 blank 前缀 OPS_HITL_PERSISTENCE= OPS_CAPABILITY_ALLOW_WRITE= OPS_CAPABILITY_ALLOW_WRITE_TAGS= OPS_CAPABILITY_PERSISTENCE= OPS_CAPABILITY_EXTRA_MANIFESTS=）；目标六件 test_schedule_worker/test_schedule_rest/test_schedule_store/test_p3_t2b_create_schedule_capability/test_ops_schedule_ddl/test_lg_rag_runs_readonly_api 全绿；全量回归环境性红与 base 396f7fed 同路径基线逐签对照；ruff check app tests 绿；allowed_app_files=[app/ops/schedule/worker.py] 机判。

## 修订记录

| 日期 | 修订 |
|------|------|
| 2026-11-17 | 落卡（夜间自动执行波 · 授权 issue Cyning12/ops-desk-workspace#23 m03064/m03283/m03694 · 来源 issue Cyning12/ops-desk-api#434 第一项） |
