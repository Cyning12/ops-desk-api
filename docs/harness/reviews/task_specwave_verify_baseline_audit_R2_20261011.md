# specwave-verify-baseline 审查（R2 · 20-task-audit 增量复核）

> **双址过渡复制件**：本文由 CLOSE 棒（2026-10-11）自址B 原件 `docs/audits/task-review/20261011_specwave-verify-baseline_r2.md` 逐字复制落址A——依 `docs/harness/CONVENTION_review_gate_dual_address_v1_zh.md` §二 过渡期口径「新增审查文必须落址A（verify 唯一消费址）· 可同时落址B 存档」；址B 原件原址原内容不动（钉死契约 4/5）。下文与原件同文。


> **审查对象**：`docs/tasks/active/task_specwave_verify_baseline.md`（修订 commit fe51492 · R1 B-1 修订后增量复核）
> **审查帽**：20-task-audit（R2 · 仅复核 lint+diff · 内容面不重审 · 未改 task 实质内容 · 未代签任何 human_gate · 未执行 30 · 未切分支 · 仅落本审查文+invoke 两档）
> **日期**：2026-10-11 · **审查时仓态**：worktree `t-specwave-verify-baseline` · 分支 `task/specwave-verify-baseline`（f992fff 落稿 → ee66dce/ac661b3 R1 档 → fe51492 B-1 修订 → 5444c85 R2 骨架）
> **委托令**：00 R2 委派令「仅复核 lint+diff · 内容面不重审」· R1 裁定 BLOCKER（B-1 · lint FAIL E3/E4/E5/E8）之修订闭环核验
> **实证留痕**：`/tmp/lint_r2.txt`（task lint 复跑）· `/tmp/lwd.txt`（lint-wiki-delta 预检）· diff 窗 `f992fff..fe51492`

## 结论

结论：本帽裁定 **PASS-WITH-NITS**——R1 B-1 四缺（E3 节名/E4 失败路径/E5 自检结论/E8 wiki_delta）经逐行 diff 核对**全部落地**且 diff 零越界（背景实证/D1 三案/钉死契约 5/TC1-TC5/非范围原样存续），task lint 本帽亲跑复证 **EXIT=0 PASS**（仅 W4 思考轮节 warn · chore 轨合法豁免），N-1 计数修正（155→154）同步吸收；残留观察项 N-4 一条照登末节（修订记录表未补 B-1 行 · 低成本顺手项）。R1 内容面裁定（实跑对账/D1 倾向 C/豁免原生机制/钉死契约可机验/TC 组可证伪）维持有效。**HG-AUDIT-R1 前置交付已齐，可签闸**；三闸仍 pending 待维护者签。

| 维度 | 结论 |
|------|------|
| B-1 修订落地（lint+diff 增量复核） | ✅ **PASS**——四缺逐行核齐（§一）· diff 窗零越界（§二）· lint EXIT=0 亲跑复证（§三） |
| R1 内容面裁定 | 维持（本帽授权范围仅 lint+diff · 内容面不重审 · R1 §一~§五 结论继续有效） |
| 残留 NIT | N-4 一条（修订记录表未补行 · 照登 · 见末节） |
| 三闸 | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 pending（本帽未代签 ✓ · 签闸权属维护者） |

---

## 一、B-1 四缺修订逐行核对（diff 窗 f992fff..fe51492 · 44+/9- · 仅触 task 档）

| R1 缺口 | 修订实证 | 裁定 |
|---|---|---|
| **E3** 缺 `## 验收标准` 节 | `## 5. 验收标准（TC 组 · 可机验）` → `## 验收标准（TC 组 · 可机验）` 节名去编号 ✓ · TC1-TC5 勾选化（`- [ ]`）✓ · 契约模板固定首两行（pytest 全量零新增红 + lint-wiki-delta 预检）补齐 ✓ | ✅ 落地 |
| **E4** 缺失败路径节 | `## 失败路径` 四行表补 ✓——豁免清单字段错（verify failClosed 红 · 与 R1 §二原生机制实证互锁）· 补录注记缺（TC4+契约 2 双层拦）· 增量新档不合规（TC3 预期行为）· 豁免清单滥用扩列（四字段+PR 人审拦）——四路径与本 task 面契合、均标可重试性与用户可见口径 | ✅ 落地 |
| **E5** 缺自检结论节 | `### 自检结论（执行者）` 占位节补 ✓（「（30/40 回填）」· draft 期合法 · 与先例口径一致） | ✅ 落地 |
| **E8** 缺 wiki_delta 行 | 元信息表补 `wiki_delta: n/a` + `wiki_delta_note`（无文档站变更 · 仓内规约档非 wiki）✓ · 顺带对齐整张元信息契约（test_strategy=required / code_quality_bar=not_applicable 纯文档面 / graph_delta=none / experience_capture=required / required_invoke_hats=10,20,30,40 / invoke_retention_profile=default / git_branch）——超出 E8 最低要求但属契约对齐，取值均与 chore 性质相符 | ✅ 落地 |

附带核对（委派令声明项）：
- **人工闸改 4 列契约** ✓——独立 `### 人工闸` 节 · human_gate_id/status/blocks_hats/说明 四列齐 · 三闸 status 全 pending 照实 ✓（HG-AUDIT-R1 未因 R1/R2 落盘自签 · 纪律合规）· HG-PILOT-OPSDESK-GLAYER n/a 照登 ✓。
- **N-1 吸收** ✓——`93 = done/ 154 档`（155→154 修正 · 标注「R1 N-1 修正」溯源清晰）· 与 verify 头行 `done tasks: 154` 实证一致。

## 二、diff 越界扫描（窗内全部改动点清单化核对）

diff 窗仅 1 档 `docs/tasks/active/task_specwave_verify_baseline.md`（44+/9-）。改动点全部落在委派令声明范围：元信息表扩契约行、人工闸节独立化、N-1 计数修正、失败路径节新增、验收标准节名去编号+勾选化+模板两行、自检结论占位节。**零越界**——§1 背景实证（EXIT=2/93 分账/双址/影响）、§3 D1-D3、§4 钉死契约 5、TC1-TC5 内容行、§6 非范围、修订记录表原样存续，无任何实质内容删改；既有合规档与 done/ 档零触碰（diff 窗仅此一档）✓。

## 三、lint 亲跑复证（不采信自报）

- 本帽亲跑 `npx --yes spec-wave task lint --file docs/tasks/active/task_specwave_verify_baseline.md` → **EXIT=0 · LINT: PASS**（2026-10-11 复证 · 与修订棒自报一致）· 余 W4「无思考轮节」warn——chore 轨合法豁免 ✓（与 R1 同口径）。
- 顺带实证：修订新增验收行引用的 `npx --yes spec-wave task lint-wiki-delta --target .` 命令真实存在且亲跑 **EXIT=0 · LINT-WIKI-DELTA: PASS**（scanned 155 · issues 0）——验收行可机验性无空头引用 ✓。

## 四、R1 内容面裁定维持声明

委派令限定 R2 仅复核 lint+diff；R1 内容面结论（实跑复核 93=36+5+39+13 全对账 · D1 倾向 C 成立 · 豁免机制原生支持实证 `docs/harness/legacy-gate-exempt.yaml` failClosed 四字段 · 钉死契约 5 全可机验 · TC1-TC5 可证伪 · 非范围查漏无新增）经 diff 窗确认相关节内容零变动，**继续有效**，不再重审。R1 N-2（30 免探豁免机制 · 直接钉四字段清单档）、N-3（D2 规约档名留 30 钉）对 30 的指引效力不变。

## 非阻塞观察项（N-4 · 照登）

- **N-4**：修订记录表未补 B-1 修订行（仍仅 10 落稿一行）——commit message fe51492 已留痕，建议 30 开工前或 CLOSE 前顺手补一行「2026-10-11 · B-1 修订（E3/E4/E5/E8 补齐 · lint EXIT=0 · N-1 吸收）」；另「## 6. 非范围」节编号与去编号后的「## 验收标准」编号风格不一（lint 已 PASS · 纯美观项）。两项均低成本 · 不闸 30。

## 维护者签闸（R2 后 · 30 前）

- [ ] 已读 R2 审查结论（PASS-WITH-NITS · N-4 照登）与 R1 内容面裁定（维持有效 · N-2/N-3 指引 30）
- [ ] 在 task 人工闸表将 HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 改 approved（维护者 · 日期）
- [ ] 裁定是否顺手补修订记录行（N-4 · 不阻塞）
- [ ] 再下发 Harness 30 Prompt（30 Agent 以 task 表为准 · pending 必须拒开工）

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 20 R2 增量复核（仅 lint+diff）：B-1 四缺逐行核对全落地 · diff 窗 f992fff..fe51492 零越界 · task lint 亲跑 EXIT=0 PASS（仅 W4 合法 warn）· lint-wiki-delta 命令实证存在且 PASS · N-1 已吸收 · 裁定 **PASS-WITH-NITS**（N-4 修订记录行未补 · 照登）· R1 内容面裁定维持 · 三闸 pending 未代签 |
