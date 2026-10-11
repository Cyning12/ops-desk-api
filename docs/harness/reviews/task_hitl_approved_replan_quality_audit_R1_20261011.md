# hitl-approved-replan-quality 审查（R1 · 20-task-audit）


> **双址过渡复制件**：本文由 CLOSE 棒（2026-10-11）自址B 原件 `docs/audits/task-review/20261011_hitl-approved-replan-quality_r1.md` 逐字复制落址A——依 `docs/harness/CONVENTION_review_gate_dual_address_v1_zh.md` §二 过渡期口径「新增审查文必须落址A（verify 唯一消费址）· 可同时落址B 存档」；址B 原件原址原内容不动（钉死契约 4/5）。下文与原件同文。

> **审查对象**：`docs/tasks/active/task_hitl_approved_replan_quality.md` v1（commit f71200b · 00 代笔填肉 · 骨架棒 00f0ecc 卡滞 interrupt 留痕在案 · SPEC §9 序1 立案）
> **审查帽**：20-task-audit（R1 书面审查 · 未改 task 实质内容 · 未代签任何 human_gate · 未执行 30 · 未切分支 · 未动码面）
> **日期**：2026-10-11 · **审查时仓态**：worktree `t-hitl-approved-replan-quality` · 分支 `task/hitl-approved-replan-quality`（base master `cae745e`）· 工作树干净
> **委托令**：00 委派令「帽位 20-task-audit」六审查要点 + 时效纪律（15 分钟 · 只核引用锚点 · 禁全仓通读）

## 结论

**裁定：BLOCKED · 退回 10-task 修订**——唯一阻塞为**结构闸未过**（task lint E3+E5 · 机械闸 · 回填面极小）；**内容面委托六要点全部成立**（锚点 8 处亲读逐字核真 · 漂移校正裁定成立 · D1 倾向 C 与 D 另立裁定均成立 · 契约可机断 · FP/TC 可证伪 · NIT 三条随修订照登）。

| 维度 | 结论 |
|------|------|
| task **内容**可执行 | 实质达标（六要点逐条裁定见 §二）——被结构闸挡，内容无需退改实质 |
| 结构闸 task lint（本帽亲跑 · 不采信自报） | `npx --yes spec-wave task lint --file docs/tasks/active/task_hitl_approved_replan_quality.md` → **LINT: FAIL**：E3「## 验收标准 节内无任何勾选项（- [ ] / - [x]）」· E5「缺 ### 自检结论 节」（余 W5/W6 warn-only 过渡）——`docs/harness/prompts/10-task-requirements.md:49`「产出 task 须 task lint PASS（结构闸 E1–E7）」为硬闸 ⇒ 退回 |
| **流程闸** HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES | 全 `pending`（00 代录标注 ✓ · 本帽未代签 · blocks 30） |
| **流程闸** HG-PILOT-OPSDESK-GLAYER | `n/a`（无外部试点面 · 合理） |
| draft 洁净度 | ✓ 分支仅 2 个 docs commit（骨架+填肉）· 无提前实施 · 工作树干净 |

## 一、锚点亲读核真（8 处 · 本帽逐行亲读 · 全逐字命中）

| 锚点（task 声称） | 本帽亲读实证 |
|---|---|
| `nodes.py:1759` verdict 恒 replan | ✅ 逐字：`obs["verdict"] = "replan" if approved else "settle"`（approved 集 :1752-1756 非空判定）· 配合 router.py:429-434 空 approved 护栏 ⇒ 「approved 非空恒 replan」机制链闭合 |
| `nodes.py:1873-1875` 路由 | ✅ `route_after_react` def :1872 · docstring :1873「``"replan"`` → supervisor（再来一轮 plan→execute）；否则 → aggregator」· :1875 return 逐字一致 |
| `nodes.py:1156` nonce 注释 | ✅ 逐字：「重发 / replan 走到这里一律重签发新例（旧 nonce 作废 · 禁续期）」——write 重放危害论证锚点成立 |
| `nodes.py:630` `_stamp_host_plan` | ✅ def :630 在案（locked 前缀保留语义 docstring :636 起） |
| `nodes.py:747/:997` 保号 | ✅ :747-748 docstring「replan 保号集合（hitl-replan-carry-and-persist-guard 契约一）：hitl_unlocked_ids ∩ **无任何终态**」· :997-998 重规划入口调用逐字一致 ⇒ 「只保号不解决重放本体」分工边界表述如实 |
| `hitl/router.py:328-357` | ✅ `_collect_decisions` def :328 → return :357 · 系同批挂起 approved/rejected **汇总面**（docstring :329-336 逐字）· 非 verdict 决策点 |
| `hitl/router.py:428` | ✅ `approved, rejected = await _collect_decisions(row)` 逐字 |
| `hitl/resume.py:131` | ✅ 逐字：`"status": "waiting_approval" if self.re_interrupted else "resumed"` —— done 帧非重挂起时硬编码 `resumed` ⇒ done{completed} 字面结构性不可达成立（钉案① · 非范围照登有据） |

旁证：`event_store.py:95-107`（实为 `app/ops/lg_rag/event_store.py`）判终逻辑亲读——:99 done 帧 `payload.status != 'waiting_approval'` → 终态 · :107 coalesce 缺省 `completed` · 「禁读进程内存态」红线 :103 在案 ⇒ D 块「牵连判终逻辑」属实。

## 二、委托六审查要点逐条裁

1. **结论先行** → 本审查文按机读口径书写：「## 结论」起首节 · 裁定词落节内 · 内容/流程闸分列。
2. **锚点亲读核真** → **成立**。8 处全逐字命中（§一）· 零漂移（base cae745e 后仅 docs 两 commit · 码面零 diff 可复锚）。
3. **锚点漂移校正裁定** → **成立**。SPEC §9 序1 原文「② `router.py:328-357` _collect_decisions approved 非空恒 replan」将恒 replan 归因于汇总面；亲读证实 `_collect_decisions` 仅聚合同批决定为 (approved, rejected) 载荷（router.py:328-357），verdict→replan 映射真决策点在 `nodes.py:1759`。task 按真值锚并留漂移校正记录——校正准确、留痕合规。
4. **D1 三案倾向 C 理由** → **成立**。契约 1 钉「write 零重发禁纯提示词约束」⇒ 纯 B（记忆注入 · LLM 遵守不可机断）单独无法满足红线；A 机断最强但图改动最大且 FP-2（计划过期需重规划）风险未实证；C = B 注入去盲（读步 · 配行为断言）+ write 步硬护栏（已终态步结构性跳过 · 可机断）为满足契约 1 的最小面。倾向开放（30 实证后定）未锁死 · R3 留护栏落点（execute 节点 vs delegation 网关）——开放标注方式正确。
5. **钉死契约可机断性（write 零重发核心红线 + 契约 5）** → **成立**。契约 1 机断形式「delegation 执行计数台账」（执行次数=1 可断言 · TC3 live 同口径呼应）；落点二选一未定属 R3 开放项，不损红线可机断性。契约 5「pytest 全量零新增红 · master 基线对拍」可机断（diff=0）；「环境性 4 红口径承先例」建议基线名单先行锁定——记 NIT-2。
6. **FP-1~FP-4 · TC1-TC5** → **成立（带 NIT-1/NIT-3）**。FP-1 行为断言兜底+退路 · FP-2 反例实证义务+契约 3 双路径同口径 · FP-3 护栏只拦已终态步（与 :750-752 保号语义自洽：approved 步旧结果被剪 ⇒ 无终态 ⇒ 不受拦）· FP-4 契约 2 字面零 diff——处置均合理。TC1「实证旧行为红 → 实现后绿」防恒绿机制成立；TC3 依赖序2 排期合理（依赖节「30 后期/40 排期约束 · 起草审查可并行」+ R5 merge 确认闸双钉）；TC2/TC4/TC5 均可证伪。

## 三、钉死契约 5 条可机断性（逐条）

| # | 契约 | 可机断性 |
|---|---|---|
| 1 | 已终态 write 步零重发（结构性 · 禁纯提示词） | ✅ delegation 执行计数台账断言（=1）· TC3 live 同口径 |
| 2 | 保号机制零回归（台账键行为零 diff · TB1-TB8 全绿） | ✅ 字面零 diff + 既测全绿双机断 |
| 3 | 手动/auto_resume 双路径同口径 | ✅ resume.py:131 出口唯一 · 双路径对拍可断 |
| 4 | reject 路径零 diff | ✅ rejected 仅记录语义（router.py:335 docstring 在案）· 对拍可断 |
| 5 | pytest 全量零新增红（基线对拍 · 环境性 4 红承先例） | ✅ diff=0 可断 · ⚠ 4 红名单须 30 首步锁先入 invoke（NIT-2） |

## 四、阻塞项与回填清单（退回 10-task）

**B-1（唯一 · 机械闸）**：task lint **E3+E5** FAIL（`10-task-requirements.md:49` 结构闸 E1–E7 硬要求 PASS）。回填清单：
- [ ] E3：`## 验收标准` TC1–TC5 五条改为 `- [ ]` 勾选项形态（措辞不动 · 纯结构）
- [ ] E5：补 `### 自检结论` 节（draft 期占位符合法 · 先例 hitl-auto-resume-claim-race R1 审定时 W3 warn 可过）
- [ ] 顺手（K7 checklist 口径）：TC4 复选框化时点明「旧测 grep 影响面」（B1 节实质已具 · 字面补齐）
- [ ] 顺手（可消 warn-only）：W5/W6 思考轮槽位/控制表补全

回填后预期 LINT PASS；内容实质本轮已裁定，20 R2 仅复核 lint + 回填 diff，无需重审内容面。

## 五、NIT 照登（非阻塞 · 随修订顺手）

- **NIT-1**：FP-1 退路措辞「不达标退 A/C」——纯 B 已被契约 1 排除，实退 A 或 C+强化硬护栏；建议 R2 裁定时改写措辞。
- **NIT-2**：契约 5「环境性 4 红口径承先例」——建议 30 首步跑 master 基线锁定 4 红名单入 invoke，防事后口径漂移。
- **NIT-3**：序2 `task/repo-logging-init` 不在本 worktree `docs/tasks/active/`（他处在途 · 与「起草审查可并行」口径一致）——40 开工前须以序2 merge 实证为闸（依赖节 + R5 已留 · 照登确认）。

## 签闸状态

HG-AUDIT-R1 维持 `pending`（阻塞未清 · 退回 10 修订优先 · 本轮不附签闸清单 · 不附 30 Prompt）。修订棒：10-task（回填清单 §四）→ 20 R2 复核。
