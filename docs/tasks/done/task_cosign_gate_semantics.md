# Task：human-gate 同签语义裁决（同一维护者对同一工单的签认在跟进消息送达时的认定规则）

> **状态**：`done`（2026-11-06 · 全棒链同日闭环：10 起草（PR #351 squash `82bf056`）→ 四闸签认 + 设计闸裁决（案①幂等为主干 · 落点=gate 记录层）→ 30 交付（PR #352 squash `3cc3e71` · 六条件全过）→ 40 复跑机制面 PASS → 50 CLOSE）
> **类型**：fix / 流程设计（human-gate 同签认定规则缺位 · 设计裁决 + 落文 + 机断回归）
> **上游**：issue [#333](https://github.com/Cyning12/ops-desk-api/issues/333)（backlog 正文 + 维护者 comment [`6676316476`](https://github.com/Cyning12/ops-desk-api/issues/333#issuecomment-6676316476) 令起草 · 受理依据 = 维护者 2026-11-06 08:48 授权（lead 代行签收与验收））
> **分支**：10/00 走 `agent/cosign-semantics-task-022a61b26cba`（PR #351 squash `82bf056` · 部署绑定要求末段=工单名）· 30 走 `fix/cosign-gate-semantics`（PR #352 squash `3cc3e71` · comment `6676780590` 授权）· 关账走 `close/cosign-gate-semantics`
> **10 注**：2026-11-06 · 承 issue #333 维护者 comment `6676316476` 令起草设计 task（**10 帽活** · 只产 task 档 + 10 invoke + lint PASS + PR · 禁改业务码）· 设计闸决策点 = 同签语义的裁决口径（幂等/覆盖/拒重复 三案对比 + 审计链影响面 · 维护者令第 1 条）
> **30 注**：2026-11-06 · 维护者 comment `6676780590` 30 授权（签认依据 = PR #351 review `5795679444` lead 签 + 授权链）· **六交付条件**：①机断判据为主（条文 grep 锚 + 结构断言）· 涉码面红测先行（负样本 = 同锚重复送达不误读为新签 · 真实送达→认定→记录路径）；②旧测适配不放宽随 PR；③改码面收敛（裁决落文为主 · 实扫溢出口径回闸）；④红线零 diff 对拍（SSE 事件表 / freeze / 闸表契约四列机读不破坏——GATE_VERIFY 仍是唯一闸据）；⑤ruff + pytest + graph-compile 全绿；⑥PR 逐条对照验收 · 20-R1 审查文随 30 PR 落盘
> **40 注**：2026-11-06 · 维护者 comment `6678465675` 40 复跑销项令——**机制面 PASS**：干净 worktree `/tmp/verify40-cosign` @ `3cc3e71` 独立复跑（不采信 30 自报）：新测 8 枚 passed · 关联 prompt-packs 55 passed 零适配 · 全量 2083 passed · 4 failed = **既有红基线同形**（diff-whitelist ×2 / embedder env ×1 / dualproc env ×1 · base `f78a721` 同 4 枚逐字复证实锤零新增红）· ruff All checks passed · graph-compile EXIT=0 · task lint / lint-wiki-delta / verify 四闸 approved 全 PASS · spec 锚 grep 15 关键词全命中 · 红线对拍 8 文件全落承载面（app//alembic/SSE 面零 diff）。偏差登记：①**GitHub Actions 自 04:20Z 零投递**（账户分钟额度疑似耗尽 · 维护者告知在查）→ 机检证据以本地 CI 同款（ruff/pytest/graph-compile/lint/verify）为准，本档与 40 invoke 已注明；②worktree 无 `.env` 环境（承先例环境性登记）。issue #333 关 issue 由维护者执行。

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `cosign-gate-semantics` |
| **git_branch** | `agent/cosign-semantics-task-022a61b26cba`（10 起草 PR 分支 · 部署绑定要求末段=工单名；30 实分支预登记 `fix/cosign-gate-semantics`） |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 机断判据为主、红测先行条件触发：①**纯设计案**（裁决落文为 FRAGMENT/prompt 资产 + 记录格式约定）= 可机断验收——结构断言（裁决条文存在性 + 唯一真源锚 + 三案处置关键词）+ 引用依据格式断言（闸表行/invoke 代录行须含依据指针的既有契约 grep 钉）；②**若 30 实扫判定涉码**（机检扩展/pytest 锚定测试）→ 红测先行：负样本 = 「同一维护者对同一工单的同一签认二次送达」按裁决口径处置的端到端场景（先红 = 现状无规则/误读为新签 · 后绿 = 裁决落地后按口径处置），经真实送达→认定→记录路径驱动，禁直造记录直调；live 面留 40 |
| **code_quality_bar** | `L2_backend`（涉码面适用；纯落文面 = docs 结构闸） |
| **graph_change_layer** | `none`（预期：docs/harness 过程资产面增量 · 无路由/表/事件类型/一级模块面；若 30 实扫出现图谱面须先回闸再动） |
| **graph_delta** | `n/a` |
| **graph_delta_note** | 模块边界不变（Harness 过程资产面内增量 · 非 G-L0/L1/L2 业务模块）；不触发图谱同步义务（承 AGENTS.md：仅新增路由/表/事件类型须同步）；HG-GRAPH-MODULES 以 `none` 口径随档签认 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 workspace contracts / freeze；本波零 wiki 面 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿（PR #351 `82bf056` · task 档 + 10 invoke）→ **四闸签认**（2026-11-06 · lead · 00 代录 · 依据 = PR #351 review `5795679444` + issue #333 comment `6676316476`/`6676780590` + 2026-11-06 08:48 授权 + 用户 12:17『验收333』指示）→ **20-R1 审查文随 30 PR 落盘**（`docs/harness/reviews/task_cosign_gate_semantics_audit_R1_20261106.md` · lead 人审原文转录 · source = PR #351 review `5795679444` · 承 seen-surface 先例）→ **30（comment `6676780590` 授权 · 六条件）**（PR #352 `3cc3e71` · GATE_VERIFY 闸据=本档闸表）→ **40 复跑机制面 PASS**（comment `6678465675` 令 · worktree `/tmp/verify40-cosign` @ `3cc3e71` 独立复跑）→ **50 CLOSE**（本档 + CLOSE 档 + 双 README + 40/50 invoke） |
| **freeze_id** | `lg-rag-sse-v1`（**零 diff 红线**：SSE 事件表/帧形态）· 既有 Harness 过程 freeze 文件本体**不动** |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved** | 20-R1, 30 | 2026-11-06 lead 签认 · 00 代录 · 依据 = PR #351 review [`5795679444`](https://github.com/Cyning12/ops-desk-api/pull/351#pullrequestreview-5795679444)（APPROVED）+ issue #333 comment [`6676780590`](https://github.com/Cyning12/ops-desk-api/issues/333#issuecomment-6676780590）· 授权链 = 2026-11-06 08:48 维护者授权 + 12:17『验收333』指示 |
| HG-AUDIT-R1 | **approved** | **30** | 同上 · lead PR #351 review 审查通过即 20-R1 书面审记录（审查文随 30 PR 落盘 `docs/harness/reviews/task_cosign_gate_semantics_audit_R1_20261106.md` · 承 seen-surface 先例） |
| HG-GRAPH-MODULES | **approved** | **30** | 同上 · `none` 口径签认确认（无图谱面 · 承先例；30 实扫出图谱面须回签） |
| **HG-COSIGN-SEMANTICS-DESIGN** | **approved** | **30** | **设计闸 · lead 签认 2026-11-06 · 依据同上**（issue #333 维护者令设）· **裁决 = 案①幂等为主干**：幂等锚 =（维护者, 工单, 闸集, 签认依据 comment id, 授权窗口）· 同锚重送达 = 同效力不重复记录（可记 replay 附注）；**覆盖不设默认**——审计链 append-only 是判例体系根基，仅「同锚 + 维护者显式声明替换意图」允许追加新行（旧行保留引注）；**拒重复不设**——补发/重送达是合法通路（F1/S3b 判例），拒即死点；**落点 = gate 记录层**（Harness 过程资产 · 机断可 grep），消费门内属仓外运行时面随 residual_risk 登记 |

---

## 背景与目标

issue #333（backlog）：**human-gate co-sign branch 缺机器人同签语义——绕过 record 杠杆仍在**（来源：#323 40 invoke 增强/收尾清单）。维护者定性：流程设计缺口感缺陷，建议 fix task 流程；设计闸决策点 = 同签语义裁决口径。

**题面（维护者 comment `6676316476`）**：同一维护者对同一工单的签认，在**跟进消息送达时**的认定规则——即一条已生效的人工闸签认（维护者签 / 00 代录 / lead 代录），因平台重试、多线程重复表态、窗口授权自然续达、同一 review 重复投递等原因**再次送达**时，系统应如何认定：当作无操作、当作新签、还是当作无效送达。

**现状锚点（只读 · 30 必读 · 10 已扫）——本仓 Harness 面的人工闸签发与消费链**：

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| 闸表真值 | task 档 `### 人工闸` 四列契约（`human_gate_id/status/blocks_hats/说明`） | human_gate 的唯一权威凭据（record 杠杆本体）；`npx spec-wave verify --target . --task <task>` 机读闸态 · 30 开工 GATE_VERIFY 的唯一闸据 |
| 签认形态 | 维护者直签（如 issue #339 comment `6674979717` 30 授权）· 00 代录（如 w-join-gap `0c147a6` 三闸同签）· lead 预授权代录（如 stage-w `6652283580`） | 代录纪律：每处须引依据（评论 id / PR review id / 审查文），全程留痕 |
| 审计链 | 闸表行 → invoke 记录（`docs/harness/invokes/by-task/<slug>/`）→ 20 审查文（`docs/harness/reviews/`）→ CLOSE 档（`docs/tasks/close/`） | 只追加留痕先例已成惯例；窗口授权带时效锚（如「窗口授权至 2026-11-06 07:00」） |
| 同签先例 | task_api_w_join_gap_fix（`docs/tasks/done/task_api_w_join_gap_fix.md` 修订表 · 「维护者三闸同签（HG-AUDIT-R1 / HG-GRAPH-MODULES / HG-W-FIX-DESIGN · 00 代录）」） | 同一签署人一次送达多闸 = 有意同签；本 task 题面 = **同一签认多次送达**（重复/跟进送达），先例未覆盖 |
| 缺口 | 全仓无「签认重复送达」认定规则 | 误读空间：重复送达被当新签 = 无需新的人类意图即刷新/扩张权威记录（**record 杠杆绕过面**）；或被当冲突签 = 流程死点 |

**结论（10 档）**：缺陷 = 同签认定规则缺位，属流程语义面而非码面缺陷；**裁决口径（幂等/覆盖/拒重复 + 审计链影响面）留设计闸 HG-COSIGN-SEMANTICS-DESIGN**，10 档不越权定口径。本 task = 裁决落地竖切：签认口径落文（Harness 过程资产）+ 机断回归 + 红线对拍。

---

## 10 钉死契约（承 issue #333 维护者令 · freeze 后升格 · 30 不得静默改义）

| 项 | 钉死 |
|----|----------------|
| **决策点属闸** | 同签语义裁决口径（幂等/覆盖/拒重复 + 审计链影响面 + 落点子题）是 **HG-COSIGN-SEMANTICS-DESIGN 的决策**，30 只执行签认口径，禁自裁（FP-5） |
| **SSE 事件表零 diff** | `lg-rag-sse-v1` 不破：不新增/不改 SSE `event_type` 与帧形态；`event_store` 写入面零 diff |
| **freeze 不动** | 既有 Harness 过程 freeze 文件本体零改动（含 task 档 `freeze_id` 所列）；如需新增 freeze 条目 → 维护者另签，不在本 task 内自作主张 |
| **改码面收敛** | 预期唯一改码面 = docs/harness 过程资产（prompts/FRAGMENTS/templates）+ 机断回归测试（若涉码）；`app/` 业务码 / 闸链 / HITL 面 / spec-wave 上游 / task lint 规则本体 一行不动（机检确需扩展 → 停下报，另案） |
| **闸表四列契约 + 纯 pending 纪律** | 30 不得破坏人工闸四列契约；10/20 档不得代签任何 human_gate |
| **审计链只增不改** | 任何签认处置（含「覆盖」案落地形态）不得原地抹除既有签认依据——历史链只可追加（append-only），防断链（FP-7） |

---

## 范围（竖切 · 四闸齐后才 30）

- [ ] **D-cosign-1 · 裁决口径落文**（30 执行 · 以 HG-COSIGN-SEMANTICS-DESIGN 签认为准）：同签认定规则落文为 Harness 过程资产唯一真源（FRAGMENT 新档或 00-orchestrator 增补条 · 落点以签认为准），条文须机读锚定：含三案处置规则（幂等/覆盖/拒重复的选定口径与组合形态）、适用键（签署人 × 工单 × 闸 × 依据等效性判定）、跟进消息送达的认定入口、审计链留痕格式（闸表行/invoke 行引用依据格式沿用既有契约）。
- [ ] **D-cosign-2 · 机断回归**（30 执行 · 先红后绿条件触发）：①纯设计案 = 结构断言（裁决条文唯一真源存在性 + 三案关键词 + 引用依据格式 grep 钉 + 闸表四列契约钉）；②30 实扫判定涉码（机检扩展/行为锚定测试）→ 红测先行：负样本 = 「同一维护者对同一工单同一签认二次送达」场景化用例按裁决口径断言（先红 = 现状无规则或误读为新签；后绿 = 按口径处置），经真实送达→认定→记录路径驱动，禁直造记录直调。
- [ ] **D-cosign-3 · 条件旧测适配**：docs/harness 相关测试 grep 影响面实扫，如实登记（零适配亦如实列出）；适配不得放宽既有断言。

### 非范围

- ❌ 同签语义口径的自行裁定（决策点是闸的 · FP-5）
- ❌ `app/` 业务码 / 闸链 / HITL 表 / 消费门 / 状态机 任何改动
- ❌ SSE 事件表 / 帧形态 / `event_store` 写入面（`lg-rag-sse-v1` freeze）
- ❌ 既有 Harness 过程 freeze 文件本体改动
- ❌ spec-wave 上游 / `task lint` 规则本体改动（机检确需扩展 → 停下报另案）
- ❌ 闸表四列契约改动 / 人工闸代签纪律松动
- ❌ web 仓 / iOS / 平台项

---

## failure_paths

| # | 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|----------|----------|--------|----------|
| FP-1 | 四闸任一 pending 即 30 | **拒开工** | 是（签闸后） | 是 |
| FP-2 | **SSE 事件表出现 diff**（`lg-rag-sse-v1` 破） | 审查拒收 · 退回（红线） | 是 | 否 |
| FP-3 | **freeze 文件本体被改动** | 红线对拍 diff 非空 · 审查拒收退回（红线） | 是 | 否 |
| FP-4 | **改码面外溢**（`app/` 业务码 / 闸链 / HITL 面 / spec-wave 上游 / task lint 规则本体被碰） | 红线对拍 diff 非空 · 审查拒收 | 是 | 否 |
| FP-5 | **30 未经闸签收自行裁决口径**（幂等/覆盖/拒重复越过 HG-COSIGN-SEMANTICS-DESIGN 自选定案，或落文与签认口径不一致） | 审查拒收 · 退回（决策点是闸的） | 是 | 否 |
| FP-6 | **幂等案滑成覆盖**（「重复送达无操作」被实现成刷新依据/时间戳——record 杠杆绕过面未堵反开） | 负样本红（重复送达产生新效力/新记录）· 审查拒收 | 是 | 否 |
| FP-7 | **覆盖案原地改写断审计链**（新签抹除旧签依据，事后无法回溯「当初凭什么签」；违反只增不改钉死契约） | 结构断言/审查拒收 · 退回 | 是 | 否 |
| FP-8 | **拒重复案无消歧通道**（合法重投/维护者改主意被一律拒死，流程无出口） | 场景化用例红 · 审查拒收（消歧通道形态随口径一并签认） | 是 | 是（工单卡死待人工） |
| FP-9 | 落文破坏闸表四列契约 / 10·20 档代签 human_gate | `task lint` / verify 红 · 审查拒收 | 是 | 否 |
| FP-10 | 验收写成人工判断而非可机断判据（条文不可 grep 锚定 / 无先红后绿证据） | 审查拒收 · 退回 | 是 | 否 |
| FP-11 | 口径落文与实际处置面漂移（条文写 A、实现走 B；如条文锚在记录层、判重却散在消费门） | 负样本/结构断言红 · 审查拒收（落点随口径一并签认的意义） | 是 | 否 |

---

## 验收标准

- [ ] 人工闸：HG-TASK-DRAFT · HG-AUDIT-R1 · HG-GRAPH-MODULES · **HG-COSIGN-SEMANTICS-DESIGN** 均 approved 后方可勾选下列项
- [ ] 裁决口径按签认落文：唯一真源节存在且机读锚定（grep 可钉），条文含选定口径（幂等/覆盖/拒重复或其组合形态）+ 适用键 + 送达认定入口 + 审计链留痕格式
- [ ] 机断回归：纯设计案 = 结构断言全绿（条文存在性 + 三案关键词 + 引用依据格式 + 闸表四列契约）；涉码案 = 负样本先红（重复送达误读为新签/无规则）后绿（按口径处置）证据链可见，经真实送达→认定→记录路径驱动（禁直造记录直调）
- [ ] 红线对拍零 diff：SSE 事件表（`lg-rag-sse-v1`）· freeze 文件本体 · `app/` 业务码 · 闸链 / HITL 面 · spec-wave 上游
- [ ] 审计链完整性：本 task 自身闸表行 / invoke / 审查文 / CLOSE 档引用依据格式符合既有契约；若签认含「覆盖」形态，旧依据保留可回溯（append-only）
- [ ] 工程面：`ruff check app tests` 触及路径零新增；`pytest tests` 零新增红（既有红基线如实登记 · 承先例显式口径）；`./scripts/graph-compile.sh` EXIT=0；`npx spec-wave task lint --file <本档>` PASS（零 warn）；`npx spec-wave task lint-wiki-delta --target .` PASS
- [ ] 旧测 grep 影响面适配（如有）不放宽；docs/harness 相关测试族关联回归全绿
- [ ] 40 复跑（留 40）：独立复跑不采信 30 自报（worktree @ 30 出货 commit）——机断判据全绿 + 红线对拍零命中 + 场景化用例按裁决口径全过

---

## 依赖

| 依赖 | 说明 |
|------|-----|
| 缺陷源 | issue [#333](https://github.com/Cyning12/ops-desk-api/issues/333)（正文：co-sign branch 缺机器人同签语义 · 绕过 record 杠杆仍在 · 设计闸决策点=同签落点（消费门内 vs gate 记录层）；立项令 = comment [`6676316476`](https://github.com/Cyning12/ops-desk-api/issues/333#issuecomment-6676316476) 五要求） |
| 上游证据链 | #323 40 invoke 增强/收尾清单（`docs/harness/invokes/by-task/stage-w-write-expand/`） |
| 同签先例 | [`task_api_w_join_gap_fix.md`](../done/task_api_w_join_gap_fix.md)（三闸同签 00 代录 `0c147a6` · 同签署人一次送达多闸）· [`task_stage_w_write_expand.md`](../done/task_stage_w_write_expand.md)（lead 预授权代录三闸 `6652283580` · 代录依据引用契约）· [`task_fix_planner_args_schema.md`](../done/task_fix_planner_args_schema.md)（同日 10 帽活先例 · 设计闸三案形态 + 受理依据口径） |
| 过程资产面 | `docs/harness/prompts/00-orchestrator.md`（00 闸扫描/代签纪律）· `docs/harness/prompts/10-task-requirements.md`（task 生产字段/闸表义务）· `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（GATE_VERIFY · record 杠杆消费点）· `docs/harness/templates/TASK_TEMPLATE.md`（闸表四列契约） |
| freeze 参照 | SSE `lg-rag-sse-v1`（事件表 · 零 diff 红线） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md`（涉码面适用） |

---

## 给执行帽的必读列表

1. `AGENTS.md`（启动纪律 · 四闸扫描）
2. 本 task（钉死契约 · 闸 · 非范围 · failure_paths）
3. issue #333 全文（题面 + 维护者立项令五要求）
4. `docs/harness/prompts/00-orchestrator.md`（代签/代录纪律 :60）· `docs/harness/templates/TASK_TEMPLATE.md`（闸表四列契约 :39-46）· `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（闸据消费形态）
5. 先例档：[`task_api_w_join_gap_fix.md`](../done/task_api_w_join_gap_fix.md) · [`task_stage_w_write_expand.md`](../done/task_stage_w_write_expand.md)（同签/代录/审计链留痕格式）
6. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 缺陷 = 同签认定规则缺位（流程语义面 · 非码面）：同一维护者对同一工单的签认在跟进消息送达时无认定规则——既可能误读为新签（record 杠杆绕过面：无新人类意图即刷新/扩张权威记录），也可能误读为冲突（流程死点） | no | — | 「co-sign branch（0c88ac32）」所指分支不在本仓 git 对象内（10 实扫：`git cat-file -t 0c88ac32` 不存在）——按题面语义（同签认定规则）落档，承载面以本仓 Harness 过程资产为限；若 30 实扫显示裁决须落到仓外运行时 → 停下报转案（FP-4/FP-5 边界） |
| R1 | 范围 = 裁决口径落文 + 机断回归 + 条件旧测适配；非范围八条锁定（口径自裁/SSE/freeze/改码面外溢/spec-wave 上游/闸表契约/web·iOS）；决策点属闸钉死 | no | — | none |
| R2 | 设计闸三案对比（HG-COSIGN-SEMANTICS-DESIGN 决策点）：**案①幂等**（同签署人×工单×闸且依据等效 → 二次送达无操作 · 审计链最干净单记录单效力 · 风险=旧签语境过期静默沿用 → 须绑 scope/窗口时效锚 · 先例已有「窗口授权至」形态）/ **案②覆盖**（新签替换旧签 · 须 append-only 留痕防断链（FP-7）· 绕过面最大（重复投递即可刷新杠杆）→ 须「人类显式意图」判据区分真覆盖 vs 送达噪声）/ **案③拒重复**（一律拒收按异常面 · 单记录 · 误伤合法重投与改主意 → 须消歧通道（FP-8））；落点子题（#333 正文：消费门内 vs gate 记录层）随口径一并裁决——记录层判重=单点真源消费面零改；消费门判重=判定分散易漂移（FP-11） | no | — | 三案各有未决前提（时效锚/意图判据/消歧通道），取舍与组合形态是维护者裁决面，10 档不预断 |
| R3 | failure_paths 锚既有语义：四闸拒开工（FP-1）/ 三红线（SSE FP-2 · freeze FP-3 · 改码面 FP-4）/ 越权自裁（FP-5）/ 三案各自滑点（幂等滑覆盖 FP-6 · 覆盖断链 FP-7 · 拒重复死点 FP-8）/ 闸表契约（FP-9）/ 验收不可机断（FP-10）/ 落文与处置面漂移（FP-11） | no | — | none |
| R4 | 可测性：机断判据为主（条文 grep 锚 + 结构断言 · 维护者令第 3 条「纯设计案则写可机断验收判据」）；涉码则红测先行——负样本经真实送达→认定→记录路径驱动（禁直造记录直调 · 同链单测盲区教训）；live/独立复跑留 40 | no | — | 仓外运行时（0c88ac32 承载面）不可本仓机断 → 40 独立复跑面以本仓资产为限如实登记 |
| R5 | 起草落稿 · 四闸 pending · NO-GO 20/30 · lint PASS 出货待审 · 30 待闸签收后另行授权（维护者令 + 2026-11-06 08:48 授权 · lead 代行签收与验收） | no | — | 无 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：①0c88ac32 承载面在仓外运行时（见 R0）；②三案组合形态待设计闸裁决（见 R2）

### R0 · 问题框定

issue #333 由维护者立项（backlog）：human-gate co-sign branch（0c88ac32）缺机器人同签语义——绕过 record 杠杆仍在。10 档实扫确认：0c88ac32 非本仓 git 对象；本仓可承载面 = Harness 过程资产（闸表/代录/审计链/invoke）。题面 = 同一维护者对同一工单的签认在跟进消息送达时的认定规则，维护者令明确设计闸决策点 = 裁决口径（幂等/覆盖/拒重复 + 审计链影响面）。

### R1 · 范围/非范围

范围三件套（裁决落文 / 机断回归 / 条件旧测适配）收敛为最小竖切；非范围把「会被顺手扩大」的面全部锁死：口径自裁（FP-5）、SSE 事件表（FP-2）、freeze 本体（FP-3）、app/业务码与闸链（FP-4）、spec-wave 上游、闸表四列契约与代签纪律（FP-9）、web/iOS。

### R2 · 方案对比（设计闸决策点 · HG-COSIGN-SEMANTICS-DESIGN）

- **案① 幂等**：同一签认（签署人 × 工单 × 闸 × 依据等效）二次送达 = 无操作；效力与记录不变，invoke 可留「重复送达·幂等确认」观察痕。审计链影响：单记录单效力、链最干净。风险：首签语境过期（scope 变更/窗口过期）时静默沿用旧签 → 须绑定 scope 快照/窗口时效锚（本仓「窗口授权至 2026-11-06 07:00」先例形态）。绕过面：最小（重复送达不产生新效力）。
- **案② 覆盖**：新签替换旧签（依据/时间戳刷新）。审计链影响：原地改写即断链——必须 append-only（supersede 链，旧依据保留可回溯 · 钉死契约六）。绕过面最大：重复投递即可刷新 record 杠杆 → 必须配「人类显式意图」判据（新评论语义/窗口授权句）区分真覆盖与送达噪声，否则绕过面未堵。
- **案③ 拒重复**：二次送达一律拒收，按异常面停下报人工。审计链影响：单记录，但合法重投（平台重试）与维护者改主意被误伤 → 须消歧通道（明确「重申/改签」出口形态），否则流程死点（FP-8）。

落点子题（#333 正文「同签落点：消费门内 vs gate 记录层」）：记录层判重 = 单点真源、消费面（GATE_VERIFY/verify）零改、审计留痕集中；消费门判重 = 判定分散、各消费点易漂移（FP-11）。落点随口径一并签认。

**【裁决回填 · 2026-11-06 · lead 签认 · 依据 = PR #351 review `5795679444` + issue #333 comment `6676780590`】= 案①幂等为主干**：幂等锚 =（维护者, 工单, 闸集, 签认依据 comment id, 授权窗口）；同锚重送达 = 同效力不重复记录（可记 replay 附注）。**覆盖不设默认**：审计链 append-only 是判例体系根基，仅「同锚 + 维护者显式声明替换意图」允许追加新行（旧行保留引注）。**拒重复不设**：补发/重送达是合法通路（F1/S3b 判例），拒即死点。**落点 = gate 记录层**（Harness 过程资产 · 机断可 grep），消费门内属仓外运行时面随 residual_risk 登记。

### R3 · 边界/失败路径

FP-1~FP-11 逐条锚既有语义：四闸拒开工 / SSE 零 diff / freeze 不动 / 改码面收敛 / 决策点属闸 / 三案滑点（幂等滑覆盖·覆盖断链·拒重复死点）/ 闸表契约 / 验收不可机断 / 落文与处置面漂移。

### R4 · 验收/可测性

维护者令第 3 条区分两形态：涉码 → 红测先行写进 test_strategy（负样本 = 重复送达误读为新签 → 按口径处置，经真实送达→认定→记录路径驱动，禁直造记录直调）；纯设计案 → 可机断验收判据（条文 grep 锚定 + 结构断言 + 引用依据格式钉 + 闸表四列契约钉）。本档 test_strategy_note 双形态皆备，30 实扫后按签认形态执行。仓外运行时面不可本仓机断 → 40 独立复跑面如实登记。

### R5 · 签收就绪

task 档落稿 · 10 invoke 落盘 · 四闸 pending · NO-GO 20/30 · lint PASS 后出 PR 待审 · 30 改码须待闸签收后另行授权（issue #333 维护者令 · 受理依据 = 2026-11-06 08:48 授权 · lead 代行签收与验收）。

---

### 自检结论（执行者）

> **hat 10（10 起草）** · 已落稿：task 档 + 10 invoke · 未改 `app/` / `tests/` · 未签任何 human_gate（四闸 pending · NO-GO 20/30）。

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_cosign_gate_semantics.md` | 0 | LINT: PASS（2026-11-06 · 10 起草自检） |
| `npx --yes spec-wave@3.5.0 task lint-wiki-delta --target .` | 0 | LINT-WIKI-DELTA: PASS（scope all · scanned 211 · missing 0 · issues 0 · 本档 wiki_delta 预填） |

> **hat 30（30 实现）** · 已交付：裁决落文 = `docs/harness/prompts/FRAGMENT_00_gate_cosign_semantics_v1_zh.md`（案①幂等为主干 · 幂等锚五元组 · 同锚重送达同效力不重复记录 + replay 附注 / 覆盖不设默认 append-only / 拒重复不设 / 落点=gate 记录层）+ `00-orchestrator.md` 引用行（不改默认表语义）+ 机断 8 断言先红后绿 + 旧测实扫零适配 · 未触碰任何 human_gate（四闸 approved 承签认档）。

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `pytest tests/test_cosign_gate_semantics.py`（先红 · commit `d2d9eaf`） | 1 | RED 实证：7 failed 1 passed——裁决落文缺失（同锚重送达认定规则在 gate 记录层无可 grep 真源）· 闸表四列契约锚 baseline 恒绿 |
| `pytest tests/test_cosign_gate_semantics.py`（后绿 · commit `c25336c`） | 0 | 8 passed（裁决条文 / 幂等锚五元组 / 同锚重送达 / 覆盖 append-only / 拒重复不设 / 落点 / orchestrator 可达 / 闸表契约） |
| `pytest tests/test_cosign_gate_semantics.py tests/test_prompt_packs.py` | 0 | 63 passed（prompt-packs 55 零适配——仅锚 delegate_only/reanchor 两档，新 FRAGMENT 不扰动） |
| `pytest tests`（全量） | 0 | 2083 passed · 4 failed = 既有红基线同形（diff-whitelist ×2 / embedder env ×1 / dualproc env ×1 · 承先例登记）· **零新增红** |
| `ruff check app tests` | 0 | All checks passed!（F541 一枚即修即 amend） |
| `./scripts/graph-compile.sh` | 0 | EXIT=0 |
| `npx spec-wave task lint` / `lint-wiki-delta` / `verify --target . --task <本档>` | 0 | 全 PASS——VERIFY 四闸 approved ✅ 可 30（R1 审查文 + 20 invoke 落盘后复检） |
| 红线对拍 `git diff origin/master --stat` | 0 | 7 文件全落签认承载面（docs/harness prompts+reviews+invokes · docs/tasks · tests 新档）· `app/` / `alembic/` 零 diff · SSE 事件面（subtask_message/progress_stream/answer_stream/chat router/event_store）零命中 |

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-11-06 | 10 落稿：承 issue #333 维护者 comment `6676316476` 令起草设计 task（10 帽活 · 只产 task 档 + 10 invoke + lint PASS + PR · 禁改业务码）· 设计闸 HG-COSIGN-SEMANTICS-DESIGN 决策点 = 同签语义裁决口径（幂等/覆盖/拒重复 三案对比 + 审计链影响面 · 落点子题随口径一并裁决）· 三红线入 failure_paths（SSE 事件表零 diff FP-2 / freeze 不动 FP-3 / 改码面收敛 FP-4）+ 决策点属闸 FP-5 · 机断验收判据 + 红测先行条件触发入 test_strategy · R0–R5 全轮 · 四闸 pending · NO-GO 20/30 · 30 待闸签收后另行授权 |
| 2026-11-06 | **四闸 approved 代录 + 30 授权入档**（签认依据 = PR #351 review `5795679444` lead 签 APPROVED + issue #333 comment `6676780590` + 授权链 2026-11-06 08:48 维护者授权 + 12:17『验收333』指示）：设计闸裁决 = **案①幂等为主干**（幂等锚五元组 · 同锚重送达同效力不重复记录 · replay 附注）+ 覆盖不设默认（append-only · 同锚+显式替换意图追加新行 · 旧行保留引注）+ 拒重复不设（补发合法通路）+ **落点 = gate 记录层**（消费门内=仓外运行时面随 residual_risk 登记）· R2 裁决回填 · 30 六交付条件入档（机断判据为主 / 旧测适配不放宽 / 改码面收敛 / 红线零 diff 对拍 / ruff+pytest+graph-compile 全绿 / PR 逐条对照 · 20-R1 审查文随 30 PR 落盘）· 状态 draft→active |
| 2026-11-06 | **30 交付**：裁决落文 = `FRAGMENT_00_gate_cosign_semantics_v1_zh.md` + `00-orchestrator.md` 引用行（不改默认表语义）· 机断 8 断言先红（`d2d9eaf` · 7 failed）后绿（`c25336c` · 8 passed）· 旧测实扫零适配（prompt-packs 55 passed）· 全量 2083 passed 零新增红（4 枚既有基线同形）· ruff All checks passed · graph-compile EXIT=0 · task lint / lint-wiki-delta / verify 四闸 approved PASS · 红线对拍 7 文件全落承载面（app//alembic/SSE 面零 diff）· 20-R1 审查文 + 20 invoke 随本 PR 落盘 · 30 invoke 落档 |
| 2026-11-06 | **40 复跑销项（机制面 PASS）+ 50 CLOSE**：独立复跑（worktree `/tmp/verify40-cosign` @ `3cc3e71` 不采信 30 自报）——新测 8 / 关联 55 / 全量 2083 passed · 4 failed = 基线 `f78a721` 同 4 枚逐字复证零新增红 · ruff/graph-compile/lint/wiki-delta/verify 全绿 · spec 锚 grep 15/15 命中 · 红线对拍零命中 · 偏差①GitHub Actions 04:20Z 零投递（机检以本地 CI 同款为准）②worktree 无 .env（环境性）· 状态 active→done · 档迁 done/ · CLOSE 档 + 双 README + 40/50 invoke 随关账 PR |
