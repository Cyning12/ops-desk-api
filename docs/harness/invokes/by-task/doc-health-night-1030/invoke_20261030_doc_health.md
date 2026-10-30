# invoke · 夜间文档健康巡检（2026-10-30 · 10 帽 · 纯文档）

| 项 | 内容 |
|----|------|
| **时间** | 2026-10-30（夜间） |
| **性质** | 文档健康巡检 · 纯文档改动 · 零业务码（app//tests//src/ 零触碰 · freeze 契约语义零触碰） |
| **分支** | api `fix/doc-health-night-1030`（自 `master` 建）· workspace `fix/doc-health-night-1030`（自 `main` 建） |
| **巡检基准** | api 阶段 W CLOSE（PR #303 merge `09f97f4` · PR #304 merge `9fa9da9`）· 阶段 T CLOSE（PR #142 · F1–F6 freeze）· active/ 无 task；workspace 阶段 T CLOSE（PR #13）· 联调 task PR #14 在途（HG-TASK-DRAFT approved）· web HITL 页 done 待 TC9 手测；§8.1 阶段序 H→T→W→P · P 进入条件未达 |
| **巡检范围** | 两仓 `docs/`：陈旧阶段状态扫描 · 跨仓指针一致性抽验 · 图谱台账只读核对 |

## 发现全清单（改 / 不改分明）

### 已修（api 仓 · 本分支）

| # | 位置 | 陈旧表述 | 实态 | 证据锚 |
|---|------|---------|------|--------|
| A1 | `docs/tasks/active/README.md` 关账行（task_api_controlled_write_hitl） | 「分支 task/api-controlled-write-hitl-close 走 PR 待合」 | PR #304 MERGED 2026-10-30 | merge commit `9fa9da9`（`git log --merges master`） |
| A2 | 同上（task_api_legacy_reviews_backfill） | 「全程本地未 push · PR 合码待维护者裁决」 | PR #300 MERGED 2026-10-30 | merge commit `f62fe7d` |
| A3 | 同上（task_api_prompts_sync_3_5_0） | 「未 push · PR 合码待维护者裁决」 | PR #299 MERGED 2026-10-30 | merge commit `347c59a` |
| A4 | 同上（task_api_graph_anchor_profile_fix） | 「未 push · PR 合码待维护者裁决」 | PR #298 MERGED 2026-10-30 | merge commit `835cacf` |
| A5 | 同上（task_lg_rag_replay_resume_ux_opt） | 「未 push · PR 待维护者裁决」 | 已本地合入 master（维护者 2026-10-30 令 · 零 push） | merge commit `fb4a7fc`「merge: lg-rag-replay-resume-ux-opt 合入 master」 |
| A6 | `docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md` §5 进度行 / §8.4 注记其二 / 修订表 | 「web HITL 审批页另 task 进行中」 | web task 已 CLOSE 2026-10-30 | `ops-desk-web/docs/tasks/done/task_web_hitl_approval_page.md` 状态 done v1.0（分支已合 main · 实现 `a34c626` · TC9 待维护者手测回填 · 关账 `200c447`） |

修订风格沿用 PR #301 先例：~~旧文~~ **新文**（修订注记 2026-10-30）+ 修订表一行。注记正文中的同日快照句亦一并划改并加「修订注记（其三）」说明由来。

### 已修（workspace 仓 · 见 workspace 分支 `fix/doc-health-night-1030`）

| # | 位置 | 陈旧表述 | 实态 | 证据锚 |
|---|------|---------|------|--------|
| W1 | `docs/05-plan/05_post_h_stage_brief_v1_zh.md` §1 当前水位表 :21 | 「T：条件核对 + 数据前置 + task 壳已落（NO-GO 30）；W/P 未开」 | T 已 CLOSE（api PR #142 · workspace PR #13 · Fixture 轨）· W 双轨单轨验收 CLOSE（api PR #303 · web 已合 main）· 双轨联调 task 在途（PR #14）· P 未开 | api merge `09f97f4`；workspace PR #13；`docs/tasks/active/task_stage_w_e2e_join_acceptance.md` |

§1 同表 :22-23、§3「下一候选」表、§4「推荐下一刀：web 冒烟」为 2026-09-17/18 时点快照，本次以修订注记标明「已被后续阶段推进超越 · 实态以 :21 更正行与修订表为准」，不逐行改写历史快照。

### 刻意不改（列出 · 每项带理由）

| # | 位置 | 发现 | 不改理由 |
|---|------|------|---------|
| D1 | workspace `docs/tasks/active/task_stage_w_e2e_join_acceptance.md` :58/:65/:78 | 引用 `app/ops/hitl/nodes.py:499-504` —— 该文件**不存在**，实为 `app/ops/lg_rag/multi/nodes.py:499-504`（行号正落 W2 租户守卫 `if not row_tenant or row_tenant != current_tenant_or_default(): return None`） | 20-R2 审查文（`task_stage_w_e2e_join_acceptance_audit_R2_20261030.md`）已立 M3 并建议「M3 修后并签两闸」——修订权属 task 自身 10 棒 / HG-AUDIT-R1 签署流程，巡检不代改在途 task 实质内容。**本巡检唯一断链指针** |
| D2 | workspace `docs/tasks/active/README.md` :5（仅存在于在途分支 `task/stage-w-e2e-join`） | 「2026-10-30 起草（三闸 pending）」→ HG-TASK-DRAFT 已 approved（`e92fef7` · 00 代录）· 20-R1（`a6b35d3`）/R2（`f10e65c`）已落 · HG-AUDIT-R1/HG-E2E-ENV 仍 pending | 该行只存在于 PR #14 在途分支（main 上无此行）；自 main 建的巡检分支无法改动它，且该行由 task 自身签署流程同步更新。报告列出，由 task 流程消化 |
| D3 | api `docs/discussions/2026-09-17_..._v0.md` :178（§8.1 阶段定义行）· :220 等修订表历史行 · 两仓 invokes/reviews/done tasks/`tmp` 派工 prompt | 含「T/W/P 未开」「待合入」等当时快照 | 历史实证记录（带日期、书写时为真）按巡检纪律不改，改写会 falsify 历史 |
| D4 | workspace `05_post_h_stage_brief_v1_zh.md` §3 阶段序代码块（H→T→W→P） | — | 计划序本身仍有效，与实态不矛盾 |
| D5 | api `docs/tasks/active/README.md` 关账行正文内「全程本地 · 未 push」等关账时点描述（A2–A5 行内括注） | 描述的是关账当日工作模式 | 时点描述书写时为真；行尾合入状态已更正，当前态无歧义 |

### 指针一致性（跨仓抽验 14 项 · 13 通 · 1 断）

- api `AGENTS.md` 必读 → workspace 四文档（01-scope/00 · 02-backend-analysis/00 · 01-sse-chat-design · 05-plan/00-migration-roadmap）全部存在 ✓
- workspace 05 brief §5 速查表全部可解析 ✓（`invoke_20260917_00_CLOSE_*.md` 为 glob，实配 `invoke_20260917_00_CLOSE_capability-contract-hardening.md`）
- workspace 联调 task 依赖表 7 项全部存在 ✓（含 `../ops-desk-web/src/api/hitl.ts`、`docs/contracts/api-v1-tenant-readonly-context-draft.md`、`../ops-desk-api/docs/tasks/done/task_api_controlled_write_hitl.md`）
- 唯一断链 = D1（`app/ops/hitl/nodes.py`），已列刻意不改
- 同 task 文件其余 api 引用核验无误：`hitl/router.py:213-216` owner-only 闸 ✓ · `hitl/store.py:171,184` 无 tenant 谓词 ✓ · `tests/test_write_approval_gate.py:431` 起 W2 测 ✓ · `hitl/router.py:425` `_execute_decided_resume` 唯一定义 · `auto_resume.py:225` 惰性 import 同源 ✓

### 图谱台账核对（api `docs/_tech_graph/l1/01_modules.md` · 只读 · PASS 零不符）

- capability 行「span `approval_id` 预留启用 `gateway.py:1318`」✓（`:1318` `"approval_id": (ctx or {}).get("approval_id") if ctx else None`）
- lg_rag 行「`capability_write_hitl_required` fail-closed + `_match_fresh_approved` 抽取 + write_intent」✓（`app/ops/lg_rag/multi/nodes.py:314` `_BLOCKED_BY_CAPABILITY_WRITE` · `:364` def `_match_fresh_approved` · 调用点 `:442`/`:489`/`:2132`）
- hitl 行「`_execute_decided_resume` 唯一定义 router.py · auto_resume 同源惰性 import」✓（`hitl/router.py:425` · `auto_resume.py:225`）
- 闸登记表 HG-GRAPH-MODULES approved 行在册 ✓；无新一级模块声明与 `app/ops/` 目录实态一致（`hitl/` 无 nodes.py · `lg_rag/multi/nodes.py` 在）✓

## Verify

- 纯文档 diff：`git diff --stat` 仅 `docs/tasks/active/README.md` + `docs/discussions/2026-09-17_..._v0.md` + 本 invoke（api）；`docs/05-plan/05_post_h_stage_brief_v1_zh.md`（workspace）
- 无 active task → 免 GATE_VERIFY；维护者巡检派工即为授权锚
- `./scripts/graph-compile.sh`：本次零图谱改动，未触碰 `_tech_graph/`；台账核对为只读
- 两仓 PR 各一，**不合并**，合并权属维护者
