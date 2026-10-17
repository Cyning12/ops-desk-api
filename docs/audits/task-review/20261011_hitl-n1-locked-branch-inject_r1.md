# 审查文：task_hitl_n1_locked_branch_inject · 20-task-audit R1（2026-10-11）

> **hat_id**：20-task-audit（R1 · 书面审查 · 不实现代码 · 不代签 human_gate）
> **审查对象**：`docs/tasks/active/task_hitl_n1_locked_branch_inject.md`（commit d35f4de · 10 落稿 · 三闸 pending）
> **对照真值**：SPEC `docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` §9 序1（HG-SPEC-SIGNOFF approved 2026-10-10）· CLOSE `docs/tasks/close/close_hitl_approved_replan_quality_20261011.md`（§四.1 N1 钉案 · §七.1 另立 task 最高优先 · §三 TC3 run1 形态 · §九 checklist 第 3 项）· 交接档 `docs/harness/invokes/by-task/_prompts/PROMPT_00_spec-campaign-handoff_20261011.md` §2.2 第 1 项 · 代码锚点亲读（`app/ops/lg_rag/multi/nodes.py` · base master `286d825`）
> **分支/基线亲验**：当前分支 `task/hitl-n1-locked-branch-inject` HEAD `d35f4de` · merge-base=master `286d825` · `git diff master...HEAD -- app/` 为空（task L6 申报一致 · 锚点行号对现行 master 成立）

## 结论摘要

| 面 | 结论 | 说明 |
|---|---|---|
| **内容** | **PASS**（零内容阻塞 · 非阻塞 nit N1 一条） | 锚点 8 组逐行亲读核真全中 · SPEC §9 序1 / CLOSE 两源 / 交接档三处引证逐字一致 · TC1–TC5 可机断 · K7 旧测影响面实证完备 · 思考轮 R0–R5 闭合 |
| **流程闸** | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸均 **pending 照实** · 本帽不代签 · **30 拒开工**直至维护者签 HG-AUDIT-R1=approved | 闸表 4 列 · status 纯 pending ✓ |
| **机械闸** | `npx --yes spec-wave task lint --file docs/tasks/active/task_hitl_n1_locked_branch_inject.md` → **LINT: PASS · EXIT=0**（亲跑） | — |

**总结论：PASS**。内容面零阻塞，可提请维护者签闸；本帽不签发任何闸、不附 30 Prompt（HG-AUDIT-R1 仍 pending）。

## 内容核对（逐条 · 亲读/亲跑实证）

| # | 核对项 | 结果 | 证据 |
|---|--------|------|------|
| C1 | 锚点 `nodes.py:1141` `locked = _locked_prefix(state)` | ✅ | 逐字一致（Q8 注释 :1140 在案） |
| C2 | 锚点 `nodes.py:1143` preserved 无条件算出 | ✅ | `preserved = _unlocked_preserved_rows(state, locked)` · 在 `if locked:`（:1161）之前 · locked 空仍计算 ✓ |
| C3 | 锚点 `nodes.py:1161-1172` locked 非空分支注入 preserved_block | ✅ | :1167-1172 `_build_supervisor_suffix_system(catalog_block, _format_prefix_block(locked, _terminals), ..., preserved_block=_format_preserved_block(preserved))` ✓ |
| C4 | 锚点 `nodes.py:1173-1174` else 分支不注入（N1 缺口本体） | ✅ | :1173 `else:` · :1174 `system_content = _build_supervisor_system(catalog_block)` —— preserved 已算出但丢弃 ✓（close 档原引 :1172-1173 · 漂移 1 行 · 见 N1） |
| C5 | 锚点 `nodes.py:755-778` `_unlocked_preserved_rows` | ✅ | unlocked ∩ 无终态 ∩ 不在 locked（:765-778）——locked 空不蕴涵 preserved 空 ✓ docstring「approved 步的旧结果已被剪掉 ⇒ 天然无终态」:759 与 task 机理链一致 |
| C6 | 锚点 `nodes.py:806-825` `_format_preserved_block` + :803「（无）」 | ✅ | 空集合返空串 :813-814 ✓ · 钉死措辞「切勿为同一目的再规划新步骤或孪生步骤」:816-817 ✓ · `_format_prefix_block` 空集返「（无）」:803 ✓（A 案 prefix 退化前提成立） |
| C7 | 锚点 `nodes.py:985-1002` write 护栏台账 | ✅ | `write_replay_guard_skip=True` :985 · `replay_of` :986 · logger 台账 :989-999 · span :1000-1006 ✓ 非范围「护栏本体不触碰」落点准确 |
| C8 | SPEC §9 序1 一致性 | ✅ | SPEC :258-262 现象①「LLM 不知晓保号行」+ 建议方向「LLM 可见保号行 · 立案时另起 task」——本 task = 现象① locked 空分支路径覆盖缺口收口立案；现象②（approved 恒 replan · `router.py:328-357`）task 非范围第四条显式排除（另立钉案）· 范围切割与 SPEC 一致 |
| C9 | CLOSE 两源原文一致性 | ✅ | §四.1（close :66）「建议另立 task 裁定（基础 prompt 路径是否同注保号行）」· §七.1（close :91）「另立 task · 最高优先」· §三 run1（close :54）单写步 approved+locked 空+护栏命中形态——task L45-46/L59 引述逐字相符 |
| C10 | 交接档 §2.2 第 1 项 | ✅ | handoff :44「序1 N1 注入缺口 · nodes.py:1172 locked 空分支 preserved_block 不注入 · 40 N1 建议另立 task · SPEC §9 序1 后续项」与 task L5 依据一致 |
| C11 | 范围 F1–F4 / 非范围五条边界 | ✅ | 非范围锁死：护栏本体（:985-1002）· locked 非空 suffix 路径（已验收 TC2/TC3 在案）· N2 观测增强（CLOSE §七.2 另项）· 恒 replan/done 语义/保号机制本体 · LLM 质量泛化/序2/序3 已 CLOSE 项——锋利且与上游裁定一致，无偷扩 |
| C12 | 验收 TC1–TC5 可机断性 | ✅ | TC1 红测先行 RED→GREEN 时序 git 可查（RED 签名=N1 缺口同形：prompt 不含保号行）· TC2 三断言机断（a 注入含名单 / b preserved 空+locked 空主路径对 master 逐字节零 diff / c 既有断言零新增红）· TC3 双钉（台账键断言存续 + `_join_subtasks` guard 段 git diff 空）· TC4 全量对拍+ruff+graph-compile · TC5 live 行为对照如实照登（观测性 · N2 口径限制自明 · 承前 task TC3 先例，非硬闸） |
| C13 | K7 行为变更类「旧测 grep 影响面」 | ✅ | 本 task 改 prompt 组装分支逻辑=行为变更；TC2(c)+必读 #4 点名 `tests/test_hitl_approved_replan_quality.py` + `tests/test_prompt_assets.py`；本帽 grep tests/ 实证：`preserved_block`/`_format_preserved_block`/`_build_supervisor_system` 触及面恰为这两文件（test_prompt_assets.py:22/40/48 · test_hitl_approved_replan_quality.py:41/327/338-340 · `_build_supervisor_system` 在 tests/ 零引用）——枚举完备无漏面，TC4 全量对拍兜底 |
| C14 | 失败路径表 | ✅ | 4 列 5 行：FP-1 prompt 非结构保证→护栏兜底中性化（写零重发结构性 · 读步浪费照实）· FP-2 prompt 膨胀（限量裁定留 30）· FP-3 误伤首次规划主路径→TC2-b 逐字节零 diff 钉死 · FP-4 prompt_assets 契约（CI 拦）· FP-5 流程闸拒开工——覆盖锋利边界 |
| C15 | 思考轮控制表 R0–R5 | ✅ | 五列（轮/结论/early_stop/reason/residual_risks）齐备 · R0 框定→R4 可测性逐轮闭合 · early_stop at R5 理由成立（缺口机理单一 · 锚点全亲读 · 方案 A/B/C 开放性显式留 30 实证 · 再轮无新增信息）· residual_risks 如实（B 案 prompt_assets 面未实估 · 超大 preserved 限量未定 · TC5 观测口径限） |
| C16 | 闸表契约 | ✅ | 4 列（human_gate_id/status/blocks_hats/说明）· status 纯 pending ×3 · blocks_hats 与说明分列（lint 契约对齐 handoff §4.1 坑位）· 无代签 |
| C17 | 元信息/lint 形态 | ✅ | required_invoke_hats=`10,20,30,40` · review_hat=`20` · graph_change_layer=`G-L1`（图谱行为表述面 · 30 按实判 · graph_delta_note 含「实证零变化改填 none」回炉条款）· `### 自检结论（执行者）` 节在（30/40 回填占位）· lint 亲跑 PASS |
| C18 | 候选方案开放性 | ✅ | A/B/C 三案不锁死（10 倾向 A 明示理由：最小 diff · 复用已验收 suffix 注入面 · 零模板资产变动）· C 案「维持现状」须 20/维护者明确裁定不默许——裁定权留 30 实证+维护者，起草不越权 |

**核对计数**：内容 18 项 · 通过 18 · 不通过 0（C4/C9 附非阻塞 nit N1）。

## 非阻塞 nit

| # | 级别 | 内容 | 建议 |
|---|------|------|------|
| N1 | nit（文献精度 · 非阻塞） | task L45 背景节引 CLOSE §四.1 原文含旧行号 `nodes.py:1172-1173`（close 档成文时分支行号），与实证锚点表现行 master 行号 `:1173-1174` 并存（漂移 1 行 · 本帽亲读现行 :1173-1174 确为 else 分支本体）。双口径并存不影响执行（必读 #1 已钉「行号漂移按实校正」） | 维护者签闸前可顺手在 L45 注「（close 原行行号 · 现 master :1173-1174）」，或留痕豁免；task 实质内容无需改动 |

## 回填清单

无（零内容阻塞 · 不退回 10-task）。

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（PASS · 零阻塞 · nit N1 一条微修/豁免留痕）
- [ ] 在 task 人工闸表将 HG-TASK-DRAFT 改为 approved（维护者 · 日期）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。HG-GRAPH-MODULES 随 30 图谱备注按实回写后由 00 代录。

## 本帽留痕

- 亲读：task 全文 175 行 · SPEC §9（:254-274）· CLOSE 全文 135 行 · handoff §2.2 · nodes.py :745-790/:795-830/:975-1010/:1130-1190
- 亲跑：`spec-wave task lint` PASS EXIT=0 · `git merge-base/log/diff` 基线核验 · grep tests/ 旧测影响面枚举实证（C13）
- 20 invoke：`docs/harness/invokes/by-task/hitl_n1_locked_branch_inject/invoke_20261011_20_task_audit_R1.md`（required_invoke_hats 含 20 · 随本审查文同 commit 落盘）

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 20-task-audit R1 落盘：锚点 8 组亲读核真 + 三源引证逐字核对 + K7 旧测面 grep 实证 + lint 亲跑 PASS + 基线/分支亲验 → **PASS**（零阻塞 · nit N1）· 三闸维持 pending 待人签 · 不附 30 Prompt |
