# CLOSE：hitl-n1-locked-branch-inject（locked 空分支 preserved_block 注入 · hitl-approved-replan-quality CLOSE N1 钉案后续项 · SPEC §9 序1）（2026-10-17）

> **task**：[../done/task_hitl_n1_locked_branch_inject.md](../done/task_hitl_n1_locked_branch_inject.md)（已归档 done/ · 状态行 CLOSED 回写）
> **类型**：功能缺口收口（hitl-approved-replan-quality CLOSE N1 钉案 · SPEC §9 序1 后续项 · 消费回路血统延续）
> **关账日期**：2026-10-17 · 批量关账分支 `close/active-batch-20261017`（批量关账 PR 待开）· 帽位：CLOSE（50 · 三闸 approved · 00 代录 · 授权 m00106）

---

## 一 · 任务信息

| 项 | 值 |
|----|----|
| task_slug | `hitl_n1_locked_branch_inject` |
| 依据 | SPEC `docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` §9 序1 · CLOSE 档 `docs/tasks/close/close_hitl_approved_replan_quality_20261011.md` §四.1（N1 钉案）+ §七.1（另立 task 建议 · 最高优先）· 交接档 `docs/harness/invokes/by-task/_prompts/PROMPT_00_spec-campaign-handoff_20261011.md` §2.2 第 1 项 |
| 背景 | hitl-approved-replan-quality（PR #233）交付 suffix v2 `$preserved_block` 注入去盲 + write 孪生结构护栏；40 live 双 run 对照发现 N1：locked 空分支（`app/ops/lg_rag/multi/nodes.py:1173-1174` else）走 `_build_supervisor_system` 基础 prompt，preserved_block 不注入——保号行对 LLM 不可见的路径覆盖缺口（契约红线不破 · 护栏兜底 · run1 实证 `write_replay_guard_skip` 命中），40 裁定不阻塞收口、另立 task |
| 目标 | locked 空分支下 preserved 非空时，保号行名单对 supervisor LLM 可见（prompt 注入 · 可机断）；preserved 空时行为对 master 零 diff；write 护栏兜底现状不破坏 |
| 分支 | `task/hitl-n1-locked-branch-inject`（base master `286d825`） |
| 帽链 | 10-task 落稿（候选 A/B/C 开放 · 倾向 A · R0–R5 early_stop at R5）→ 20 R1 **PASS**（nit N1 豁免）→ 三闸 approved（00 代录 · 授权 m00106 · 2026-10-11）→ 30/40 → PR #238 → **CLOSE（本档 · 批量关账）** |

## 二 · 交付

| 环节 | 实证 |
|------|------|
| PR | [#238](https://github.com/Cyning12/ops-desk-api/pull/238) · **MERGED 2026-10-11T05:56:12Z · squash commit `8dd15ee`** · head `task/hitl-n1-locked-branch-inject` · 标题 `fix(hitl-n1-locked-branch-inject): N1 收口 locked 空分支注入 preserved_block` |
| 码面 | 照登：无实证——task 档自检结论槽仅记「（30/40 回填）」未回填方向 A/B/C 定案与 diff 明细；PR 标题实证「locked 空分支注入 preserved_block」已落地，具体实现路径（A 分支条件复用 suffix / B 基础模板加槽 / C 维持现状）以 PR #238 diff 为准 |
| 图谱 | 元信息预判 `graph_change_layer=G-L1`（`docs/_tech_graph/l1/01_modules.md` lg_rag/multi 行备注回写义务钉死 · 30 按实判）；实际回写结果照登：无实证（task 档未录） |
| 审查文 | 20 R1 **PASS**（nit N1 行号双口径留痕豁免）· 址A 原件 `docs/harness/reviews/task_hitl_n1_locked_branch_inject_audit_R1_20261011.md` · 址B 复制件 `docs/audits/task-review/20261011_hitl-n1-locked-branch-inject_r1.md`（主会话已落盘 · 址A 原件不动） |
| **CLOSE 增量** | task 档归档 done/（状态行 CLOSED + 修订记录 CLOSED 行）· 本档落盘 · 批量关账分支 `close/active-batch-20261017` |

## 三 · 核验结论

| 验收项 | 结果 | 实证 |
|--------|------|------|
| TC1 红测先行（locked 空+preserved 非空 prompt 断言 RED→GREEN） | 照登：无实证 | task 档自检结论未回填；RED→GREEN 时序须查 PR #238 git 历史 |
| TC2 注入行为与零 diff 双断言 | 照登：无实证 | 同上 |
| TC3 write 护栏兜底不破坏 | 照登：无实证 | 同上 |
| TC4 反回归全量对拍（pytest / ruff / graph-compile） | 照登：无实证 | 同上 |
| TC5 live 行为对照（40 帽 · N2 观测口径限制存续） | 照登：无实证 | 同上 |
| 合并闸 | ✅ | PR #238 MERGED（squash `8dd15ee` · 2026-10-11T05:56:12Z）· CI 状态照登：无实证（未在档内记录） |

诚实声明：本 CLOSE 仅按档内证据关账——task 档三闸/20 R1/PR 合并在案，30/40 执行明细（方向定案、测试数字、live 对照）task 档未回填，本档不代编；如需追证以 PR #238 diff 与 `docs/harness/invokes/by-task/hitl-n1-locked-branch-inject/` 留档为准。

## 四 · 偏差与 nit（如实照登）

1. **20 R1 nit N1（行号双口径留痕）**：豁免在案——审查文址A 原件 `docs/harness/reviews/task_hitl_n1_locked_branch_inject_audit_R1_20261011.md` 录 N1 豁免裁定，闸表 HG-AUDIT-R1 说明栏在案；非阻塞，不影响收口。
2. **自检结论空槽**：task 档「自检结论（执行者）」节仅记「（30/40 回填）」占位未填——关账时 30/40 明细无档内真值，本 CLOSE §三 相应各行照登「无实证」，不补编数字。
3. **graph_delta 条件注**：元信息 `graph_delta_note` 钉「若 30 实证后确认零图谱表述面变化，改填 none 并注理由」——最终填态照登：无实证（task 档维持 G-L1 预判未回写终态）。
4. **N2 观测口径限制存续**：prompt 内容级直证不可观测（CLOSE §七.2 另项 · 非本 task 面），TC5 live 对照以行为对照+台账链间接实证为限——承 task 档 R4 残余风险照登。

## 五 · 签录（闸态表与审查文链）

| 闸 / 环节 | 状态 | 文档 / 实证 |
|-----------|------|------------|
| HG-TASK-DRAFT | **approved** | 2026-10-11 00 代录（授权 m00106）· 初稿人扫 |
| HG-AUDIT-R1 | **approved** | 2026-10-11 00 代录（授权 m00106）· R1 PASS（nit N1 豁免）· 址A `docs/harness/reviews/task_hitl_n1_locked_branch_inject_audit_R1_20261011.md` |
| HG-GRAPH-MODULES | **approved** | 2026-10-11 00 代录（授权 m00106）· G-L1 预判 · 30 回写义务钉死（实证免动须交免动说明） |
| 20 R1 审查 | **PASS** | 址A 原件（同上）· 址B 复制件 `docs/audits/task-review/20261011_hitl-n1-locked-branch-inject_r1.md`（已落盘 · 址A 原件不动） |
| 合并 | **MERGED** | PR [#238](https://github.com/Cyning12/ops-desk-api/pull/238) · squash `8dd15ee` · 2026-10-11T05:56:12Z |

## 六 · 维护者验收 checklist（00 代录 · 授权 m00106 · 需人重新验收项）

- [ ] **注入行为抽验**：locked 空 + preserved 非空场景（hitl_unlocked_ids 非空 · 被批准步无终态）下 supervisor system prompt 含保号行名单（`_format_preserved_block` 输出或其等价段）。
- [ ] **零 diff 抽验**：preserved 空（含 locked 空首次规划主路径）时 system_content 对修复前逐字节零 diff；write 护栏台账键（`write_replay_guard_skip`/`replay_of`）存续。
- [ ] **方向定案追认**：PR #238 diff 核对方向 A/B/C 定案与 task 档候选面一致（档内无记录 · 以 diff 为准追认）。
- [ ] **图谱回写抽验**：`docs/_tech_graph/l1/01_modules.md` lg_rag/multi 行备注是否按实回写（或免动说明在案）。

## 七 · 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-17 | CLOSE 落稿（批量关账分支 `close/active-batch-20261017`）：结构沿 CLOSE 模板（close_hitl_resume_async_20261015）· 规模按任务收敛 · 档内证据全录（三闸 approved · 20 R1 PASS nit N1 豁免 · PR #238 MERGED）· 30/40 明细 task 档未回填处一律照登「无实证」不代编 · 址B 复制件引用在案 · 分支 `task/hitl-n1-locked-branch-inject` 移交 00 统一清理 |
