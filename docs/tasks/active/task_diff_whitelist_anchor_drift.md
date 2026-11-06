# Task：diff-whitelist 锚点漂移修复（stage-w-004/stage-w-002 本地基线红 · 纯测试基建）

> **状态**：`draft`（10 落稿 · 四闸 pending · NO-GO 20/30）
> **类型**：fix / 测试基建面（diff-whitelist 锚点漂移 ×2 · **只动测试基建（whitelist/锚点）** · 红线=不碰实现/SSE/freeze）
> **上游**：issue [#337](https://github.com/Cyning12/ops-desk-api/issues/337)（backlog 正文 + 维护者 comment [`6682233401`](https://github.com/Cyning12/ops-desk-api/issues/337#issuecomment-6682233401) 令起草 · 受理依据 = 维护者 2026-11-06 13:40 多选授权（lead 代行签收与验收））
> **分支**：10/00 走 `agent/diff-whitelist-task-5e3e38c2abdd`（本 PR · 部署绑定要求末段=工单名）· 30 实分支预登记 `fix/diff-whitelist-anchor-drift`（待闸签收后另行授权）
> **10 注**：2026-11-06 · 承 issue #337 维护者 comment `6682233401` 令起草 fix task（**10 帽活** · 只产 task 档 + 10 invoke + lint PASS + PR · 禁改业务码/禁改测试码）· 设计闸决策点 = **诊断裁决**（锚点真漂移→修锚点 / whitelist 过期→刷新基线 · 二选一必须有证据——先跑两条用例拿当前实际行号与输出再裁）· 10 档已跑两条用例取证（实测证据见「现状锚点」节 · 裁决属闸不归 10）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `diff-whitelist-anchor-drift` |
| **git_branch** | `agent/diff-whitelist-task-5e3e38c2abdd`（10 起草 PR 分支 · 部署绑定末段=工单名；30 执行分支预登记 `fix/diff-whitelist-anchor-drift`） |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 红测先行 · 命令级可复验（维护者令第 2 条）：负样本 = 修复后两条本地基线红转绿——`pytest tests/test_lg_rag_write_replay_guard.py::test_tc8_diff_whitelist tests/test_strategy_scenario.py::test_diff_whitelist_scenario_stage_rewire` 修复前 2 failed（红证据留痕）→ 修复后 2 passed（绿证据留痕），pytest 命令级可复验；两条用例之修复只经测试基建（whitelist/锚点常量与判定逻辑）达成，实现零 diff |
| **code_quality_bar** | `L2_backend`（涉码面=两枚既有测试文件的锚点/whitelist 常量与判定逻辑 · 实现/SSE/freeze 零改动红线） |
| **graph_change_layer** | `none`（预期：纯测试基建增量 · 无路由/表/事件类型/一级模块面；若 30 实扫出现图谱面须先回闸再动） |
| **graph_delta** | `none` |
| **graph_delta_note** | 模块边界不变（测试文件内常量/逻辑修正 · 非 G-L0/L1/L2 业务模块改动）；不触发图谱同步义务（承 AGENTS.md：仅新增路由/表/事件类型须同步）；HG-GRAPH-MODULES 以 `none` 口径随档签认 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 workspace contracts / freeze；本波零 wiki 面 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿（本 PR · task 档 + 10 invoke）→ lead 签四闸（含 HG-DIFF-WHITELIST-DIAGNOSIS 诊断裁决）→ 30 实现（fix 分支 · 两枚闸修复 + 红转绿证据）→ 40 独立复跑 → CLOSE |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | pending | 20-R1, 30 | 初稿未经 20-task-audit 审查与维护者签收 |
| HG-AUDIT-R1 | pending | 30 | 20-task-audit R1 审查文未落盘 |
| HG-GRAPH-MODULES | pending | 30 | `none` 口径待签（纯测试基建面 · 承 ops-write-catalog-reconcile 先例；30 实扫出图谱面须回签） |
| HG-DIFF-WHITELIST-DIAGNOSIS | pending | 30 | **设计闸 · 诊断裁决**：锚点真漂移→修锚点 / whitelist 过期→刷新基线（二选一 · 必须有证据——先跑两条用例拿当前实际行号与输出再裁 · 10 档实测证据已备见「现状锚点」节 · 最终裁决随签认落闸表行） |

---

## 背景与目标

issue #337（backlog · 来源 #323 40 invoke 增强/收尾清单）：**本地全量 pytest 既有 4 failed 中 2 条为 diff-whitelist 锚点漂移（题面记 stage-w-004/stage-w-002 · 实测对应两枚用例）**——`tests/test_lg_rag_write_replay_guard.py::test_tc8_diff_whitelist` 与 `tests/test_strategy_scenario.py::test_diff_whitelist_scenario_stage_rewire`。要求：修锚点或刷新基线 whitelist；**纯测试基建，不碰实现/SSE/freeze**。

**机制（10 档实扫 · 只读）**：两枚闸同源（蓝本 `tests/test_memory_injection_consumer.py:585-609` 三级探测照抄 · 四态语义承 00 裁定 O1/O2）——钉锚 `_BASE`（git 短哈希）后 `git diff _BASE..HEAD --name-only` ∪ 暂存/工作区/untracked 得改动面，先跑 **banned 前置硬 fail**（`scripts/` `alembic/` 等禁改面 · O2：先于第四态 skip 判定），再过 `_allowed` 白名单；越界文件全为后续波次产物 → 态③可审计 skip，含本波次窗内文件 → fail 保牙（回归牙）。**漂移成因**：钉锚停在 2026-10-20 各波次切出点（`_BASE=d337486`/`a1591e9`），而 diff 窗随 master 每次合入不断增长——后续波次**合法**触碰 `scripts/`（specwave 升级）与 `alembic/`（stage-w 新迁移）即撞 banned 前置断言，态③ foreign skip 被 O2 挡在 fail 之后，闸于 master 常态转红。

**现状锚点（30 必读 · 10 已取证 2026-11-06 · 工作树 @ `d594dc3`）——两条用例实测输出与溯源**：

| 主题 | 锚点 | 实测（2026-11-06 · `.venv/bin/python -m pytest` 单跑两枚） |
|------|------|------|
| 用例① | `tests/test_lg_rag_write_replay_guard.py::test_tc8_diff_whitelist`（`_BASE="d337486"` :291 · `_WAVE_TIP="c17e63b"` :295 · banned 断言 :450） | **failed**：`AssertionError: 禁改面（scripts/ alembic/ 及其余 app/）出现改动:` 22 件——`alembic/versions/20261105_capability_notes.py` / `scripts/graph-compile.sh` / `app/db/models.py` / `app/main.py` / `app/ops/capability/{defaults,manifest,note_store,types}.py` / `app/ops/capability/manifests/{builtin,ops.write,testing}.v1.yaml` / `app/ops/hitl/{router,store}.py` / `app/ops/issues.py` / `app/ops/lg_rag/{event_store,multi/step_contract,router,thread_store}.py` / `app/ops/overview.py` / `app/ops/prompts/assets/lg_rag.supervisor{,.suffix}.system.md` / `app/ops/pulls.py` / `app/ops/tenant_context.py` |
| 用例② | `tests/test_strategy_scenario.py::test_diff_whitelist_scenario_stage_rewire`（`_BASE="a1591e9"` :428 · `_WAVE_TIP="63bad3d"` :456 · banned 断言 :554） | **failed**：`AssertionError: 禁改面（scripts/ alembic/）出现改动: ['alembic/versions/20261105_capability_notes.py', 'scripts/graph-compile.sh']` |
| banned 文件溯源（`git log _BASE..HEAD -- <path>`） | `scripts/graph-compile.sh` | 后续合法波次：`6c9d0e6`（specwave 3.3.0→3.5.0 钉位全量对齐） |
| 同上 | `alembic/versions/20261105_capability_notes.py` | 后续合法波次：`51030a4`（stage-w · PR #327 `ops.write.run_note` 新迁移） |
| 旁证（既有登记链） | stage-w 30 invoke :58 / 40 invoke :30 · fix-worker-state / fix-seen-surface / fix-planner-args / cosign 各 invoke 全量行 | 「diff-whitelist 锚点漂移 ×2」自 2026-11-05 起逐波次如实登记为既有基线红（CI 无 PG skip 面 · 本地真 PG 面红） |

**10 档诊断倾向（证据归 10 · 裁决属闸）**：两枚 banned 文件均可溯源至**钉锚之后的合法波次合入**（非本波次窗内文件 · 非锚点对象缺失——`git rev-parse` 两锚皆可解析），据此证据形态指向 **whitelist 过期（基线漂移）→ 刷新基线**一支；但「修锚点」与「刷新基线」的最终裁决必须由 HG-DIFF-WHITELIST-DIAGNOSIS 签认（30 开工前须按闸表裁决执行 · 禁自裁 FP-5）。

---

## A1 锚点语义（本档定义 · 裁决与修复的共同锚）

> 维护者令「设计闸决策点=诊断裁决（二选一必须有证据——先跑两条用例拿当前实际行号与输出再裁）」· A1 = 本次诊断裁决的判定锚，20/30/40 引用 A1 时以本节为唯一真源。

**A1 = 漂移归因锚点**。语义三要素：

1. **证据先于裁决**：裁决前必须先实跑两条用例（`pytest tests/test_lg_rag_write_replay_guard.py::test_tc8_diff_whitelist tests/test_strategy_scenario.py::test_diff_whitelist_scenario_stage_rewire`），留存当前实际失败行号与输出全文；再对 banned/violations 清单逐路径 `git log _BASE..HEAD -- <path>` 溯源至具体合入 commit。无证据不裁决。
2. **二值归因**：每枚闸的漂移必属其一——**锚点真漂移**（`_BASE`/`_WAVE_TIP` 对象缺失/被改写/钉错对象 → 修锚点：更正为正确可解析锚并复跑验证）或 **whitelist 过期**（锚可解析 · banned/violations 文件全部可溯源至钉锚后的合法波次合入 → 刷新基线：按签认形态重置基线窗/白名单，使闸在 master 干净树上回到态①/态③正确语义）。两值皆须逐文件证据支撑，禁混合口径和稀泥。
3. **闸语义不破**：无论哪支裁决，四态语义（①钉锚∧零越界 pass · ②退化基线∧零越界 pass · ③钉锚∧越界全 foreign 可审计 skip · ④锚缺失 banned 兜底后 skip）与「banned 前置先于 skip」（00 裁定 O2）、「回归牙」（波次窗内未登记面被触碰 → fail）必须原样保留或经闸签认的等价改写；**禁以删闸/整段豁免 banned 来强转绿**（FP-2）。

**红线继承 A1 语义**：凡本 task 改动——**实现零 diff**（`app/` 一行不动 · 含 registry/policy/gateway/lg_rag/SSE 面）；**SSE 事件表/freeze 零 diff**（`lg-rag-sse-v1` 不破 · 不新增/不改 SSE 事件类型与帧形态）；**改码面收敛**（只动测试基建：两枚测试文件的锚点/whitelist 常量与判定逻辑）。

---

## 10 钉死契约（承 issue #337 维护者令 · freeze 后升格 · 30 不得静默改义）

| 项 | 钉死 |
|----|----------------|
| **决策点属闸** | 诊断裁决（锚点真漂移→修锚点 / whitelist 过期→刷新基线）是 **HG-DIFF-WHITELIST-DIAGNOSIS 的决策**，30 只执行签认分支，禁自裁（FP-5）；裁决须有证据（A1 语义一 · 先跑用例拿行号输出再裁） |
| **不碰实现** | issue #337 正文红线：`app/` 实现一行不动（含 registry/policy/gateway/lg_rag/defaults/note_store/manifest loader/SSE 面）；修复只经测试基建达成（FP-4） |
| **红测先行** | 30 修复前先留红证据（两枚用例修复前 2 failed 输出全文入 invoke），修复后 2 passed 转绿证据同留；pytest 命令级可复验（`pytest tests/test_lg_rag_write_replay_guard.py::test_tc8_diff_whitelist tests/test_strategy_scenario.py::test_diff_whitelist_scenario_stage_rewire`） |
| **闸语义不破** | 四态语义 / banned 前置（O2）/ 回归牙原样保留或经签认等价改写；**禁删闸 / 禁整段豁免 banned / 禁放宽断言来强转绿**（FP-2）；若裁决形态需调整 `_allowed`/`_BANNED` 面，逐路径留证据链并 20-R1 复核 |
| **SSE/freeze 零 diff** | `lg-rag-sse-v1` 不破：不新增/不改 SSE `event_type` 与帧形态；freeze 面（`docs/coding_wiki/` contracts · `app/ops/lg_rag/` 事件表）零触达（FP-3） |
| **闸表四列契约 + 纯 pending 纪律** | 30 不得破坏人工闸四列契约；10/20 档不得代签任何 human_gate |

---

## 范围（竖切 · 四闸齐后才 30）

- [ ] **D-fix-1 · 诊断裁决执行**（30 执行 · 以 HG-DIFF-WHITELIST-DIAGNOSIS 签认为准）：按 A1 语义先取证——实跑两条用例留存当前实际行号与输出全文，banned/violations 逐路径 `git log` 溯源；然后按签认分支执行——①**修锚点**（锚点真漂移：更正 `_BASE`/`_WAVE_TIP` 为正确可解析锚 · 复跑验证两闸回正确态）或②**刷新基线**（whitelist 过期：按签认形态重置基线窗/白名单 · 使闸在 master 干净树回到态①/态③正确语义 · 越界文件证据链逐路径留痕）。
- [ ] **D-fix-2 · 红转绿证据**：修复前 2 failed / 修复后 2 passed 双证据入 30 invoke（pytest 命令级可复验 · 题面负样本口径）；全量 `pytest tests` 复核零新增红（既有 env 依赖红 2 枚如实登记 · 承各波次先例）。
- [ ] **D-fix-3 · 红线对拍**：`git diff origin/master...HEAD --name-only | grep -v '^docs/'` 对拍——`app/` `alembic/`（除测试面外）`scripts/` SSE 面零 diff；改动面 ⊆ {两枚测试文件 · task 档 · invoke 档}。

### 非范围

- ❌ 诊断裁决的自行裁定（决策点是闸的 · FP-5）
- ❌ `app/` 任何实现改动（issue #337 正文红线=不碰实现 · 含 registry/policy/gateway/gateway/lg_rag/defaults/note_store/manifest loader 一行不动 · FP-4）
- ❌ SSE 事件表 / 帧形态 / `event_store` 写入面（`lg-rag-sse-v1` freeze · FP-3）
- ❌ 两枚闸的删除/停用（禁删闸强转绿 · FP-2）；banned 前置断言整段豁免同理
- ❌ 其他测试文件改动（只动 `tests/test_lg_rag_write_replay_guard.py` / `tests/test_strategy_scenario.py` 两枚闸的锚点/whitelist 常量与判定逻辑 · 其余测试一行不动）
- ❌ `scripts/graph-compile.sh` / `alembic/versions/` 任何回退或改动（banned 文件溯源属合法波次产物 · 修复不得回滚他人合入）
- ❌ spec-wave 上游 / `task lint` 规则本体改动（机检确需扩展 → 停下报另案）
- ❌ web 仓 / iOS / 平台项

---

## failure_paths

| # | 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|----------|----------|--------|----------|
| FP-1 | 四闸任一 pending 即 30 | **拒开工** | 是（签闸后） | 是 |
| FP-2 | 以删闸 / 整段豁免 banned / 放宽或删除既有断言来强转绿（四态语义 · banned 前置 O2 · 回归牙被破坏） | **拒合并**：闸语义破——红转绿必须靠锚点/whitelist 基线的正确重置达成，不靠拆闸 | 否 | 是 |
| FP-3 | 修复经 SSE 事件表 / 帧形态 / freeze 面改动达成 | **拒合并**：`lg-rag-sse-v1` freeze 破（SSE/freeze 零 diff） | 否 | 是 |
| FP-4 | 30 实扫出现 `app/` 实现改动（含 registry/policy/gateway/lg_rag/defaults/note_store/manifest loader/SSE 面） | **拒合并**：改码面破（issue #337 正文红线=不碰实现 · 修复必须纯测试基建达成） | 否 | 是 |
| FP-5 | 30 未按 HG-DIFF-WHITELIST-DIAGNOSIS 签认分支自行裁决（或无证裁决 / 混合口径） | **拒开工/拒合并**：决策点属闸 · A1 语义一（证据先于裁决）破 | 是（签闸后） | 是 |
| FP-6 | 裁决证据链缺失（未先跑两条用例留存行号输出 · banned/violations 未逐路径 `git log` 溯源） | **退回 30**：A1 语义要求证据先于裁决 | 是 | 否 |
| FP-7 | 修复回退/改动 `scripts/graph-compile.sh` 或 `alembic/versions/20261105_capability_notes.py` 等他人合法合入 | **拒合并**：banned 文件是后续合法波次产物——修闸不修史 | 否 | 是 |
| FP-8 | 改动面越出两枚测试文件的锚点/whitelist 常量与判定逻辑（顺手改其他测试/文档面） | **退回 30**：改码面收敛破（只动测试基建的限定面） | 是 | 否 |
| FP-9 | 闸表四列契约破坏 / 人工闸代签 | **拒合并**：record 杠杆破 | 否 | 是 |

---

## 验收标准

- [ ] HG-DIFF-WHITELIST-DIAGNOSIS 签认诊断裁决（二值分支 + 证据链 + 裁决依据）落闸表行，30 按签认分支交付
- [ ] **红转绿命令级复验**：修复前 `pytest tests/test_lg_rag_write_replay_guard.py::test_tc8_diff_whitelist tests/test_strategy_scenario.py::test_diff_whitelist_scenario_stage_rewire` → 2 failed（输出全文留痕）→ 修复后同命令 → 2 passed；两证据入 30 invoke
- [ ] 证据链完整：两条用例当前实际行号与输出 + banned/violations 逐路径 `git log _BASE..HEAD` 溯源 commit 清单（A1 语义一）
- [ ] 闸语义对拍：四态语义 / banned 前置（O2）/ 回归牙在修复后原样生效（或经签认等价改写 · 20-R1 复核）；禁删闸/禁豁免 banned（FP-2）
- [ ] 红线对拍零命中：`git diff origin/master...HEAD --name-only | grep -v '^docs/'` ⊆ 两枚测试文件（+测试面外零 diff）；`app/` `scripts/`（他人合入面）`alembic/` SSE/freeze 面零 diff（FP-3/FP-4/FP-7）
- [ ] 全量 `pytest tests` 零新增红：既有 env 依赖红 2 枚（`test_embedder_failure_degrades_with_marker` / `test_hitl_cross_instance_resume`）如实登记（承各波次先例口径）
- [ ] `ruff check app tests` 触及路径零新增；`npx --yes spec-wave@3.5.0 task lint --file <本档>` PASS；`npx --yes spec-wave@3.5.0 task lint-wiki-delta --target .` PASS（`--scope all` 口径）
- [ ] 40 复跑（留 40）：独立复跑不采信 30 自报（worktree @ 30 出货 commit）——两枚用例 2 passed + 全量零新增红 + 红线对拍零命中 + 证据链独立复核

---

## 依赖

| 依赖 | 说明 |
|------|-----|
| 缺陷源 | issue [#337](https://github.com/Cyning12/ops-desk-api/issues/337)（正文：diff-whitelist 锚点漂移 ×2 · stage-w-004/stage-w-002 本地基线红 · 要求=修锚点或刷新基线 whitelist · 纯测试基建 · 立项令 = comment [`6682233401`](https://github.com/Cyning12/ops-desk-api/issues/337#issuecomment-6682233401) 四要求） |
| 上游证据链 | #323 40 invoke 增强/收尾清单（`docs/harness/invokes/by-task/stage-w-write-expand/` · 留转③建议另立清理 task = 本 task 立项来源） |
| 闸机制蓝本 | [`test_memory_injection_consumer.py`](../../tests/test_memory_injection_consumer.py):585-631（`_resolve_base` 三级探测 · 四态语义 · 00 裁定 O1/O2 蓝本） |
| 修复对象（只读基准 · 30 改动面） | [`test_lg_rag_write_replay_guard.py`](../../tests/test_lg_rag_write_replay_guard.py)（`_BASE="d337486"` :291 · `_WAVE_TIP="c17e63b"` :295 · banned :450）· [`test_strategy_scenario.py`](../../tests/test_strategy_scenario.py)（`_BASE="a1591e9"` :428 · `_WAVE_TIP="63bad3d"` :456 · banned :554） |
| 溯源参照 | `git log d337486..HEAD -- scripts/graph-compile.sh` → `6c9d0e6`（specwave 升级）· `git log a1591e9..HEAD -- alembic/versions/20261105_capability_notes.py` → `51030a4`（stage-w PR #327） |
| freeze 参照 | SSE `lg-rag-sse-v1`（事件表 · 零 diff 红线 · FP-3） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md`（测试码适用） |

---

## 给执行帽的必读列表

1. `AGENTS.md`（启动纪律 · 四闸扫描）
2. 本 task（A1 锚点语义专节 · 钉死契约 · 闸 · 非范围 · failure_paths）
3. issue #337 全文（题面 + 维护者立项令四要求）
4. [`test_lg_rag_write_replay_guard.py`](../../tests/test_lg_rag_write_replay_guard.py) :284-462 与 [`test_strategy_scenario.py`](../../tests/test_strategy_scenario.py) :420-566（两枚闸全文 · 四态语义 · banned 前置 · 回归牙）
5. [`test_memory_injection_consumer.py`](../../tests/test_memory_injection_consumer.py):585-631（蓝本 · 对照未漂移一枚闸的语义基线）
6. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（闸据消费形态）· `docs/harness/templates/TASK_TEMPLATE.md`（闸表四列契约）

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 缺陷 = diff-whitelist 锚点漂移 ×2（测试基建面 · 非码面）：钉锚停在 2026-10-20 波次切出点，diff 窗随 master 合入增长，后续合法波次触碰 scripts//alembic/ 撞 banned 前置断言（O2 挡在态③ skip 前）→ 常态红；10 档实跑两枚用例取证（用例① :450 22 件 banned · 用例② :554 2 件 banned）+ 逐路径溯源（`scripts/graph-compile.sh`→`6c9d0e6` · `alembic/versions/20261105_capability_notes.py`→`51030a4` · 均钉锚后合法波次） | no | — | 题面 stage-w-004/stage-w-002 编号与仓内用例 id 无字面对应——按实测全量 failed 清单与既有 invoke 登记链双向锁定 = 上列两枚（若维护者所指另有所指 → 20-R1 或设计闸澄清） |
| R1 | 范围 = 诊断裁决执行（按签认分支）+ 红转绿证据 + 红线对拍；非范围八条锁定（裁决自裁/实现改动/SSE/删闸/其他测试文件/回退他人合入/spec-wave 上游/web·iOS）；决策点属闸钉死 | no | — | none |
| R2 | 设计闸二值（HG-DIFF-WHITELIST-DIAGNOSIS 决策点）：**修锚点**（锚真漂移：对象缺失/改写/钉错 → 更正锚 · 证据=`git rev-parse` 失败或对象不符）/ **刷新基线**（whitelist 过期：锚可解析 ∧ banned 全溯源至钉锚后合法波次 → 重置基线窗/白名单）；10 档实测证据（两锚皆可解析 · banned 全溯源合法波次）形态上指向刷新基线一支，但**裁决属闸不归 10**（FP-5）；另需注意「刷新基线」的具体形态（重钉 `_BASE` 至新 master 窗 / 改 `_WAVE_TIP` 语义 / 调整 `_allowed` 面）是裁决的子选项，签认时须指明 | no | — | 刷新基线的子形态（重钉 vs 改窗语义 vs 调白名单面）各有再漂移风险，取舍是维护者裁决面 |
| R3 | failure_paths 锚既有语义：四闸拒开工（FP-1）/ 禁拆闸强转绿（FP-2 · 四态/banned 前置/回归牙）/ SSE·freeze 零 diff（FP-3）/ 不碰实现（FP-4）/ 裁决属闸（FP-5）/ 证据先于裁决（FP-6）/ 不修史（FP-7）/ 改码面收敛（FP-8）/ 闸表契约（FP-9） | no | — | none |
| R4 | 可测性：维护者令第 2 条——红测先行写进 test_strategy，负样本 = 修复后两条本地基线红转绿（pytest 命令级可复验）：先红 = 修复前两枚 2 failed 输出全文留痕，后绿 = 修复后同命令 2 passed；40 独立复跑不采信 30 自报 | no | — | 两闸修复后须防「恒绿失效」（闸语义被顺手拆空）→ 验收含闸语义对拍条（证据：构造一次波次窗内未登记面触碰须仍 fail 保牙） |
| R5 | 起草落稿 · A1 锚点语义专节钉死 · 四闸 pending · NO-GO 20/30 · lint PASS 出货待审 · 30 待闸签收后另行授权（维护者令 + 2026-11-06 13:40 授权 · lead 代行签收与验收） | no | — | 无 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：①stage-w-004/stage-w-002 题面编号与仓内用例 id 无字面对应（见 R0 · 按实测+登记链双向锁定）；②刷新基线子形态（重钉/改窗/调白名单面）待 HG-DIFF-WHITELIST-DIAGNOSIS 签认指明（见 R2）

### R0 · 问题框定

issue #337 由维护者立项（backlog · 来源 #323 40 invoke 收尾清单留转③）：本地全量 pytest 既有 4 failed 中 2 条为 diff-whitelist 锚点漂移。10 档实跑取证（2026-11-06 · 工作树 @ `d594dc3`）：用例① `test_tc8_diff_whitelist` 于 :450 banned 前置断言 failed（22 件 · 含 stage-w capability 族 app/ 文件 + `alembic/versions/20261105_capability_notes.py` + `scripts/graph-compile.sh`）；用例② `test_diff_whitelist_scenario_stage_rewire` 于 :554 同断言 failed（2 件）。溯源：`git log d337486..HEAD -- scripts/graph-compile.sh` = `6c9d0e6`（specwave 3.3.0→3.5.0）；`git log a1591e9..HEAD -- alembic/versions/20261105_capability_notes.py` = `51030a4`（stage-w PR #327）。两锚 `git rev-parse --verify` 皆可解析 → 非锚点对象缺失。结论：diff 窗随 master 合入增长，后续合法波次触碰禁改面前置面 → 闸于 master 常态红（态③ foreign skip 被 O2 挡后）。

### R1 · 范围/非范围

范围三件套（诊断裁决执行 / 红转绿证据 / 红线对拍）收敛为最小竖切；非范围把「会被顺手扩大」的面全部锁死：裁决自裁（FP-5）、`app/` 实现（FP-4 · issue #337 正文红线）、SSE/freeze 面（FP-3）、删闸/豁免 banned（FP-2）、其他测试文件、回退他人合法合入（FP-7）、spec-wave 上游、web/iOS。

### R2 · 方案对比（设计闸决策点 · HG-DIFF-WHITELIST-DIAGNOSIS）

- **修锚点**：判定 = 锚点真漂移（`_BASE`/`_WAVE_TIP` 对象缺失/被改写/钉错对象）。修复 = 更正为正确可解析锚 + 复跑两闸验证。证据要求：`git rev-parse` 失败或对象与题面不符。本次实测**不支持**此支（两锚皆可解析）。
- **刷新基线**：判定 = whitelist 过期（锚可解析 ∧ banned/violations 全部可溯源至钉锚后的合法波次合入）。修复形态子选项（签认时须指明）：①重钉 `_BASE` 至新 master 窗（如当前 master tip）使干净树 diff 为空 → 态① pass；②改波次窗语义使闸只评 `_BASE.._WAVE_TIP` 固定窗（闸使命完成后评固定窗而非 HEAD 漂移窗）；③按证据链扩充/调整 `_allowed` 面（逐路径留痕 · 20-R1 复核）。各子选项的再漂移风险与维护成本不同，是维护者裁决面。
- 10 档证据形态指向刷新基线一支，但按维护者令「二选一必须有证据——先跑两条用例拿当前实际行号与输出再裁」，最终裁决与形态指明属闸（FP-5）。

### R3 · 边界/失败路径

FP-1~FP-9 逐条锚既有语义：四闸拒开工 / 禁拆闸强转绿（四态·O2·回归牙）/ SSE·freeze 零 diff / 不碰实现 / 裁决属闸 / 证据先于裁决 / 不修史 / 改码面收敛 / 闸表契约。核心新增 = FP-2（禁拆闸）与 FP-6（证据先于裁决）与 FP-7（不修史）三条闸语义专属闸。

### R4 · 验收/可测性

维护者令第 2 条：红测先行写进 test_strategy，负样本 = 修复后两条本地基线红转绿（pytest 命令级可复验）。本档 test_strategy_note 按此落：修复前 2 failed（输出全文入 30 invoke 红证据）→ 修复后同命令 2 passed（绿证据）；40 独立复跑不采信 30 自报。防「恒绿失效」：验收含闸语义对拍——修复后构造一次波次窗内未登记面触碰须仍 fail 保牙（回归牙原样生效实证）。

### R5 · 签收就绪

task 档落稿（含 A1 锚点语义专节 · 四闸 pending · NO-GO 20/30）· 10 invoke 落盘 · lint PASS 后出 PR 待审 · 30 改码须待闸签收后另行授权（issue #337 维护者令 · 受理依据 = 2026-11-06 13:40 授权 · lead 代行签收与验收）。

---

### 自检结论（执行者）

> **hat 10（10 起草）** · 已落稿：task 档 + 10 invoke · 未改 `app/` / `tests/`（两枚闸取证只跑不改）· 未签任何 human_gate（四闸 pending · NO-GO 20/30）。

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `.venv/bin/python -m pytest tests/test_lg_rag_write_replay_guard.py::test_tc8_diff_whitelist tests/test_strategy_scenario.py::test_diff_whitelist_scenario_stage_rewire`（取证 · 只读） | 1（2 failed · 预期红） | 修复前基线红证据：用例① :450 banned 22 件 / 用例② :554 banned 2 件（输出全文见 10 invoke） |
| `npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_diff_whitelist_anchor_drift.md` | 0 | LINT: PASS（2026-11-06 · 10 起草自检） |
| `npx --yes spec-wave@3.5.0 task lint-wiki-delta --target .` | 0 | LINT-WIKI-DELTA: PASS（scope all · 本档 wiki_delta 预填） |

**环境注记**：本机 venv 补装 `pytest` / `pytest-asyncio` / `respx`（承 ops-write-catalog-reconcile 先例 · pyproject 已声明 · requirements.txt 无 pytest 系）；两枚闸用例为纯 git 子进程面，不依赖 PG。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-11-06 | 10 落稿：承 issue #337 维护者 comment `6682233401` 令起草 fix task（10 帽活 · 只产 task 档 + 10 invoke + lint PASS + PR · 禁改业务码）· 四要求全落：设计闸 HG-DIFF-WHITELIST-DIAGNOSIS 决策点 = 诊断裁决二值（锚点真漂移→修锚点 / whitelist 过期→刷新基线 · 证据先行——10 档已实跑两条用例取实证：用例① :450 banned 22 件 / 用例② :554 banned 2 件 + 溯源 `6c9d0e6`/`51030a4` 均钉锚后合法波次 · 裁决属闸不归 10）/ 红测先行入 test_strategy（负样本 = 修复后两条本地基线红转绿 · pytest 命令级可复验）/ 红线入 failure_paths（不碰实现 FP-4 · SSE/freeze 零 diff FP-3 · 禁拆闸强转绿 FP-2 · 裁决属闸 FP-5 · 证据先于裁决 FP-6 · 不修史 FP-7）· A1 锚点语义专节钉死 · R0–R5 全轮 · 四闸 pending · NO-GO 20/30 · 30 待闸签收后另行授权 |
