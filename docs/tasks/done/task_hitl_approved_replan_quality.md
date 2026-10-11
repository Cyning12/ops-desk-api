# Task：hitl-approved-replan-quality（approved 恒 replan + LLM 盲循环 · approved 步骤「自然完成」双重结构性不可达）

> **状态**：done（CLOSED 2026-10-11 · 40 核验 PASS-WITH-NITS：TC3 live 双 run 对照（run1 护栏 `write_replay_guard_skip`/`replay_of` 命中孪生中性化 · run2 suffix v2 注入激活零孪生 · write 执行均=1 · consumed 命中原 sid）· TC4 全量 1769 过/7 红与 master 基线逐枚同名同因零新增 · TC5 台账链 grep 可断 · N1 locked 空注入缺口照登留另立 task · 三闸 approved（维护者授权 m01606/m00255 · 00 代录）· PR [#233](https://github.com/Cyning12/ops-desk-api/pull/233) MERGED（squash `be1469d` · 2026-10-11 · CI 绿）· CLOSE 归档 done/ · 细节见 CLOSE 文档 [`../close/close_hitl_approved_replan_quality_20261011.md`](../close/close_hitl_approved_replan_quality_20261011.md)）
> **类型**：质量收口（消费回路血统延续 · 功能缺口 · 实证驱动 · T4 CLOSE 钉案② + SPEC §9 序1 立案）
> **依据**：SPEC `docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` §9 序1（2026-10-11 维护者令登记 · 维护者令立项）· T4 CLOSE 钉案② `docs/tasks/close/close_hitl_replan_carry_and_persist_guard_20261010.md` §四.2 · 语义边界登记 `docs/acceptance/20261010_hitl-consumption-loop_local_acceptance.md`
> **分支**：`task/hitl-approved-replan-quality`（worktree 专用 · base master `cae745e` · 已经 PR #233 squash 合入 master `be1469d` · CLOSE 后 worktree `t-hitl-approved-replan-quality` 与 task/close 分支留 00/维护者清理——本 CLOSE 在该 worktree 内作业无法自清）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `hitl-approved-replan-quality` |
| **git_branch** | `task/hitl-approved-replan-quality` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 红测先行（复现孪生/重放）→ 实现 → 全量对拍；含 live 实证：approved 后无孪生 · write 步执行次数=1 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` 预期（multi 图 resume 行为语义变 · 按实判） |
| **graph_delta** | 预期改 `app/ops/lg_rag/multi/nodes.py` resume/verdict 面（按实判） |
| **graph_delta_note** | modules.md lg_rag/multi 行若涉 resume 行为表述须回写（30 判） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 无文档站变更 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `required` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → 20 R1 → 维护者签 → 30（先实证复现再定方案）→ 40（含 live 实证）→ PR+CI 绿 → CLOSE |
| **freeze_id** | 无（预期零新表/零迁移/零新 SSE 事件/零新 payload 键） |

### 人工闸

| 闸 | 状态 | 说明 |
|---|---|---|
| HG-TASK-DRAFT | **approved**（2026-10-11 · 00 代录 · 授权 m01606/m00255） | R2 PASS（docs/audits/task-review/20261011_hitl-approved-replan-quality_r2.md · e9b2c9a） |
| HG-AUDIT-R1 | **approved**（同上代录） | R1 BLOCKED→B-1 修订 54a3897→R2 PASS 闭合 |
| HG-GRAPH-MODULES | **approved**（同上代录） | 在册·无图谱结构变更（nodes.py 执行逻辑内改 · 模块清单零增删） |
| HG-PILOT-OPSDESK-GLAYER | n/a | 无外部试点面 |

## 背景与目标

### 实证锚点（逐字关键行 · 三源在案 · base cae745e 亲读复核）

1. **approved 恒 replan**：`app/ops/lg_rag/multi/nodes.py:1759` `obs["verdict"] = "replan" if approved else "settle"` → :1875 路由回 supervisor 再来一轮完整 plan→execute。**锚点漂移校正**：SPEC §9 序1 旧引 `router.py:328-357` 系 `app/ops/hitl/router.py` 的 `_collect_decisions`（resume 汇总面）——真决策点在 multi/nodes.py :1759，本文按真值锚。
2. **盲循环/孪生步**：新一轮 plan 由 LLM 自由重规划，无「已完成步骤+终态结果」结构化记忆注入 → 重放已执行步骤。live 实证（维护者复跑 + T1 40 run 7b317804 系）：resume 后 `re_interrupted:true` + subtasks `:1`/`:2` 同语义双胞胎。
3. **write 副作用重放风险**：`nodes.py:1156` 钉「重发/replan 走到这里一律重签发新例（旧 nonce 作废 · 禁续期）」——write capability 被盲重放会**真再执行一次**，delegation idempotency 不兜底。读步重放浪费 LLM 轮，写步重放是正确性风险。
4. 保号机制（hitl-replan-carry-and-persist-guard · nodes.py :747/:997）只保 sid 编号与消费键命中，**不解决重放本体**（分工边界在案）。

### 10 初步研判（开放 · 待 30 实证 · 不锁死）

双重结构性不可达机制链：① replan 重规划轮 LLM 不知晓既有步骤终态（盲）→ 重复规划同语义步（孪生）；② approved 非空恒 replan（:1759）使该盲循环在**每次**批准后必经。保号行（hitl_unlocked_ids）对 LLM 规划层不可见。

### 候选修复方向（开放给 30 实证后定 · 起草不锁死）

- **A 结构化定点重跑**：resume 后不进完整 replan——以既有计划+状态构造「仅 unlocked 步重执行」路径，跳过 supervisor 重规划。可机断性最强，图改动最大。
- **B replan 保留 + 记忆注入**：verdict 仍为 replan，plan 上下文注入结构化「已完成步骤+终态结果」清单。改动最小，但 LLM 遵守不可机断，须配行为断言。
- **C 混合（10 倾向）**：默认 B 注入去盲 + write 步硬护栏（已终态 write 步结构性跳过不经 LLM 裁量）——读步去盲靠注入，写步安全靠结构。
- **D resume.py:131/41-51 done{completed} 语义重审**：倾向**另立 task**（§非范围照登 · 终态字面改动牵连 event_store.py:99-107 判终逻辑，超本 task 最小面），留 20 审裁定。

**目标**：HITL 批准 resume 后——已批准步定点重跑到位 · 已完成步不被盲重放（孪生步=0 可机断）· write 副作用零重发（结构性 · 非提示词约束）· TA/TB 既测全绿。

## 现状锚点

| 锚点 | 实证 |
|---|---|
| nodes.py:1759 | `obs["verdict"] = "replan" if approved else "settle"` 逐字 |
| nodes.py:1873-1875 | `"replan"` → supervisor 再来一轮；否则 aggregator |
| nodes.py:1156 | replan 一律重签发 nonce（旧作废）逐字注释 |
| nodes.py:630 | `_stamp_host_plan` def（每轮重盖章 sid · T1 40 实证 :1→:11 漂移 · 保号后已收口消费键） |
| nodes.py:747/:997 | 保号集合 P=hitl_unlocked_ids∩无终态（契约一） |
| app/ops/hitl/router.py:328-357/:428 | `_collect_decisions` 汇总同批 approved → resume 载荷 |
| app/ops/hitl/resume.py:131 | done 帧硬编码 `resumed`（钉案① · 本 task 非范围） |

## 钉死契约

1. **已终态 write capability 步零重发**——结构性保证（执行面跳过/网关拒放），禁纯提示词约束；机断：delegation 执行计数台账。
2. **保号机制零回归**：hitl_unlocked_ids/保号集合/delegation_approval_consumed/hitl_persist_guard_skip 台账键行为零 diff（TB1-TB8 全绿）。
3. **手动 resume 与 auto_resume 双路径同口径**（resume.py:131 出口一致）。
4. **reject 路径零 diff**（rejected 集合仅记录语义不动）。
5. **pytest 全量零新增红**（master 基线对拍 · 环境性 4 红口径承先例 · worktree 无 .env 须注明执行环境）。

## 范围

- **F1**：D1 裁定落地（30 实证复现后定 A/B/C）——resume 后重放面收口。
- **F2**：孪生步机断断言（步骤集合/计数）入测试面。
- **F3**：write 步零重发护栏 + 台账断言。
- **F4**：invoke/图谱回写/经验捕获。

### 非范围

- **done{completed} 字面语义**（resume.py:131 硬编码 resumed 结构性不可达 · event_store.py:99-107 判终）——独立后续 task 候选（D 块已留裁定口）。
- 仓级 verify 缺口（序3 在途）· logging 初始化（序2 在途）· LLM 规划质量泛化优化。

## failure_paths

| FP | 路径 | 处置 |
|---|---|---|
| FP-1 | 注入记忆后 LLM 仍重放（B 案软肋） | TC 行为断言兜底（孪生=0 硬断）；不达标退 A/C |
| FP-2 | 定点重跑跳过必要重规划（计划已过期场景） | 30 实证找反例；契约 3 双路径同口径防分叉 |
| FP-3 | write 护栏误伤「就该重跑」的批准步 | unlocked 步不受护栏拦（护栏只拦**已终态**步） |
| FP-4 | 台账键改动破坏验收机读 | 契约 2 字面零 diff + TC 对拍 |

## B1 · 旧测影响面

TB1-TB8（保号 14 枚）· TA 组（T1 29+34 枚）· hitl resume/decide 既测——全量对拍零新增红；若 D1=A 图路径变动涉 resume 流程测试，逐枚核 diff 归因。

## 验收标准

- [x] TC1 红测先行：构造 resume 场景（approved 非空+部分步已终态）实证旧行为（孪生/重放）→ 实现后转绿（防恒绿假象）。（9b56343 RED → ebe2a01 转绿 · 时序在 git 历史）
- [x] TC2 单测：D1 裁定形态对应断言（定点路径步集 / 注入载荷含已完成清单 / write 步跳过）。（TC2 六枚：FP-3 反面/异 args/error 不拦/同批双胞胎/off 零介入/canonical 确定性 · ebe2a01）
- [x] TC3 live（依赖序2 merge 后台账可见）：六 env 组 → 挂起→decide→resume → 断言：无孪生 subtask · write 步执行次数=1 · delegation_approval_consumed 命中原 sid。（40 双 run 实证：run1 6d467359 护栏 guard-skip 命中孪生 :2 replay_of :1 · run2 3f2c58bf 注入路径激活零孪生 · write 执行均=1 · consumed 命中原 sid · pending 零孤儿 · invoke_20261011_40_verify.md §3）
- [x] TC4 反回归：全量 pytest + TB1-TB8 + capability_acceptance 门禁 · **旧测 grep 影响面以 §B1 节为准**（K7 口径 · 涉改文件逐枚核 diff 归因）。（40 终验：1769 过/7 红与 master 基线逐枚同名同因 · ruff 55=55 涉改文件 6=6 · TB+新测+prompt_assets 93 绿 · 门禁失败2跳过1 与 master cae745e 同形 · §2）
- [x] TC5 台账链：live 全程台账键 grep 可断。（token_issue_hitl_required→hitl_persist_guard_skip→delegation_approval_consumed→token_issued→token_verified→（run1）write_replay_guard_skip/replay_of→HITL 恢复完成 · §3 TC5）

## 依赖

序2 `task/repo-logging-init` 先行 merge（live 台账观测前提 · 30 后期/40 排期约束 · 起草审查可并行）。六 env 组口径承验收文档 :20。

## 给执行帽的必读列表

1. SPEC §9 序1 + 本 task 全部锚点行（逐一亲读复核 · 禁信转述）。
2. T4 CLOSE `docs/tasks/close/close_hitl_replan_carry_and_persist_guard_20261010.md` §四.2 钉案②。
3. 验收文档 `docs/acceptance/20261010_hitl-consumption-loop_local_acceptance.md` 语义边界段 + 操作便签（坑位 1 logging 将由序2 收口 · 复跑前确认序2 已 merge）。
4. nodes.py 保号契约段（:747/:997）+ router.py _collect_decisions。

## 思考轮控制

| 轮 | 结论 | early_stop |
|---|---|---|
| R0 | 锚点复核（30 首步 · 行号漂移按实校正） | 否 |
| R1 | 盲循环复现方案（红测构造） | 否 |
| R2 | D1 裁定（复现实证后） | 否 |
| R3 | write 护栏落点（execute 节点 vs delegation 网关） | 否 |
| R4 | TC 组完备性回扫 | 否 |
| R5 | 40 live 排期（序2 merge 确认） | 否 |

## KPI（00）

（00 职责段 · CLOSE 时回填：轮次/棒次/卡滞干预/偏差）

## 经验总结

1. **「注入去盲 + 结构护栏」双层是 LLM 行为类红线的最小可信面**：契约 1 钉「write 零重发禁纯提示词约束」——纯 B（记忆注入）LLM 遵守不可机断，C 混合案以 suffix v2 `$preserved_block` 注入承担读步去盲（行为断言+live 对照佐证）、以 `_join_subtasks` 分发层 guard-skip（先于签发 · 不派发不消费 · `replay_of` 台账）承担写步结构红线；两层各配机断面，互不寄生。
2. **live 双 run 对照是 prompt 注入类改动的行为实证范式**：locked 空（run1 · 注入未激活 · LLM 仍产孪生 → 护栏命中中性化）vs locked 非空（run2 · suffix v2 激活 · 零孪生）构成 off/on 活体对照——比单 run「未见孪生」可信度高一个量级，且顺带 FP-3 反面（approved 步自身正常消费重跑）同框取证。
3. **注入路径覆盖缺口要在 40 显性照登而非隐含**：N1（locked 空走基础 prompt · preserved_block 不注入 · nodes.py :1172-1173 else 分支）系 live 复跑新发现——契约红线不破（护栏兜底）但去盲面有路径缺口，照登+另立 task 裁定，不硬编「全路径覆盖」。
4. **验收环境坑位会复发，须按先例处置并照登**：NO_PROXY 含 `[::1]` 致 httpx InvalidURL（验收文档坑位 1 复发 · 剥 no_proxy 后通）；worktree compose 5432/6333 被主仓容器占用 → 复用主仓 healthy 容器零残留——两项均非本 diff 引入，口径先行登记防误判。
5. **审查文落址A 是归档硬步骤**（序2 教训 → 序3 双址规约 §二）：verify 仅扫 `docs/harness/reviews/`，审查文只落址B（`docs/audits/task-review/`）则 done 档 verify 必红 missing review——本 CLOSE 循规约复制 R1/R2 落址A（档头注来源 · 址B 原件不动）。

**40 自检结论（2026-10-11 · 复核 HEAD 403a0e9）**：**PASS-WITH-NITS**。①diff/契约五条独立核全过（hitl/ 目录零 diff · write 零重发结构性机断 · TB 93 绿）；②TC4 终验：全量 1769 过/7 红与 master 基线逐枚同名同因（环境性）· ruff 55=55 涉改文件 6=6 · capability_acceptance 门禁失败2跳过1 与 master cae745e 完全同形（基线环境性零新增）；③TC3 live 双 run 对照实证：run1 单写步 locked 空→LLM 仍产孪生 :2→**write_replay_guard_skip/replay_of 台账 live 命中**（零重发零孤儿单 · FP-3 对照 approved 步正常消费重跑）；run2 rag+write locked 非空→suffix v2 注入路径激活→**LLM 零孪生** · :1 rag 零重跑 · :2 重跑 exactly once；④TC5 台账链 grep 可断。偏差：N1 locked 空路径 preserved_block 不注入（nodes.py :1172 else 分支 · 护栏兜底红线不破 · 建议另立 task）；N2 prompt 内容级直证不可观测（TC1-b 单测钉死+live 行为对照间接实证）；N3 worktree compose 端口占用复用主仓容器。TC3/TC4/TC5 勾选。详见 invoke_20261011_40_verify.md。

### 自检结论（执行者）

**30（2026-10-11 · ebe2a01）**：D1=C 混合案落地——replan 注入去盲（$preserved_block 保号行 + locked 终态摘要 · 模板 v1→v2）+ write 孪生分发层 guard-skip 护栏（先于签发检查 · 不派发不消费 · replay_of 台账 · off 零触达）。钉死契约五条全过：①write 零重发结构性机断（TC1-a/TC2 组）②TB1-TB8 48 枚全绿台账键零字面改动③resume.py:131 未触④reject 零 diff⑤全量 1769 过/7 红与基线逐枚一致（环境性 · .env delegation ON+postgres checkpointer · stash 对拍在案）· ruff 55 持平 master。TC1/TC2 勾选；TC3/TC5 live 待序2 merge 后 40 帽；40 本棒不做。详见 invoke_20261011_30_implementation.md。

---

## 修订

| 日期 | 版本 | 说明 |
|---|---|---|
| 2026-10-11 | v0-skeleton | 10 骨架先行落稿（全节标题+占位 · 增量填充中） |
| 2026-10-11 | v1 | 10 填肉定稿（骨架棒卡滞 interrupt 留痕 · **00 代笔填肉** · 授权 m01606）：锚点亲读复核+漂移校正（真决策点 nodes.py:1759 非旧引 router.py）· D1 三案倾向 C · write 零重发核心红线 · done{completed} 钉案非范围照登（D 块留另立裁定口）· 依赖序2 |
| 2026-10-11 | v1.1 | 30 自检结论回填 + TC1/TC2 勾选（feat ebe2a01 · 契约五条全过 · TC3/TC5 留 40） |
| 2026-10-11 | v1.2 | 40 核验回填：PASS-WITH-NITS · TC3/TC4/TC5 勾选 · live 双 run 实证（护栏命中+注入对照）· N1 locked 空注入缺口留另立 task |
| 2026-10-11 | v1.3 | **CLOSED**（close/hitl-approved-replan-quality）：PR [#233](https://github.com/Cyning12/ops-desk-api/pull/233) MERGED（squash `be1469d` · CI 绿）· 归档 done/（头部状态/分支行/经验总结回填）· CLOSE 文档 `docs/tasks/close/close_hitl_approved_replan_quality_20261011.md` + 50 invoke 落盘 · 审查文 R1/R2 按双址规约 §二 过渡期口径复制落址A（`docs/harness/reviews/task_hitl_approved_replan_quality_audit_R{1,2}_20261011.md` · 址B 原件不动）· README 双侧补登 · 质量钉：verify EXIT=0 PASS + task lint PASS（CLOSE 复跑）· worktree/分支移交 00 清理 |
