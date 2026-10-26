# Task 审查：fix-delegation-pattern-fullmatch（R2 · R1=fail 三项 fixback 复审）

> **审查帽**：20-task-audit（书面审 · 不改 task 实质内容 · 不动 app/ · tests/ · 不代签人工闸 · 未 git 任何操作 · 未触碰 docs/arch-browser/dist/site-data.json）
> **被审对象**：`docs/tasks/active/task_fix_delegation_pattern_fullmatch.md`（状态=draft · 2026-10-26 10-task fixback · 修订记录第二条在案）
> **前审**：`docs/harness/reviews/task_fix_delegation_pattern_fullmatch_audit_R1_20261026.md`（fail · B1/B2/B3）
> **配套 invoke**：`docs/harness/invokes/by-task/fix-delegation-pattern-fullmatch/invoke_20261026_10_fix-delegation-pattern-fullmatch.md`（R1 已验在册一致 · fixback 未涉）
> **对照真值**：`docs/spec/host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md`（signed · :67 pattern 约束条目）+ `.github/workflows/lint-wiki-delta.yml:39` + `docs/_tech_graph/l1/01_modules.md`
> **审查日期**：2026-10-26
> **审查方式**：通读 fixback 后 task 全文（198 行）+ python3 两态实证 TC3 新值 + 亲读 CI yml :39 与 01_modules.md :34/:112/:113/:130 + git status 复核边界

## 结论

**pass**。本轮复核结论：R1 三项整改项（B1 硬阻塞 / B2 / B3）全部 fixback 到位且经本帽逐项实证通过；fixback 为纯文档增量，未见连带新失真；R1 已验绿的锚点/兼容性/闸态/分支纪律维持有效。TC3 换两态判别值后「红测先行→转绿」流程对三条对抗用例全部成立。**建议维护者签 HG-AUDIT-R1**（签前 30 仍拒改码 · 见文末签闸清单）。

## 一、R1 退回项逐项复审

### B1（硬阻塞）TC3 与修法自洽性 —— PASS（python3 实证）

10-task 采 R1-N1 建议 (a)：TC3 改用两态判别值 `"../../etc/passwd\n"`（task :113），宽字符集路径穿越登记 `out_of_scope` 另 task（task :188）。本帽 python3 复证：

| 用例 | pattern | value | search（master 现状） | fullmatch（修法后） |
|---|---|---|---|---|
| TC3 新值 | `^[\w./-]+$` | `"../../etc/passwd\n"` | 放行（`$` 匹配换行前） | **拒** ✓ 两态判别成立 |
| TC3 原值 | `^[\w./-]+$` | `"../../etc/passwd"` | 放行 | 放行（整串本即匹配 · B1 实证复现）✓ 归因成立 |
| TC1 | `\d+` | `"123abc"` | 放行 | 拒 ✓ |
| TC2 | `^[a-z]+$` | `"abc\n"` | 放行 | 拒 ✓ |
| TC4 | `\d+`+"123" / `^[a-z]+$`+"abc" | — | 通过 | 通过 ✓ 防误伤 |

连带失真四处均已改写且与实证一致：实弹 #3 归因去「+ search」改「纯字符集过宽 · 与匹配函数无关」（task :61）；`test_strategy_note` 注明 TC3 两态判别值与原值 out_of_scope（task :17）；R1/R3 行与 R3 节同步改写（task :146/:148/:160/:168）；「三条对抗用例先在 master 上复现红→改 fullmatch 转绿」对新 TC3 值重新成立（三条均 search 放行 / fullmatch 拒，上表实证）。`out_of_scope` 登记（task :186-189）自洽：宽字符集问题定性准确、后续方向（签发侧校验面）恰落本 task 非范围 `delegation.py:252`，印证另立 task 正确。

### B2 TC8 钉版 —— PASS

task :118 现为 `npx --yes spec-wave@3.5.0 task lint-wiki-delta --target .`，与 CI 真值 `.github/workflows/lint-wiki-delta.yml:39` `run:` 行命令部**逐字一致**（亲读比对）✓

### B3 HG-GRAPH-MODULES 承册锚点 —— PASS

task :38 锚点已由 :79 改指 :130（delegation-naming-boundary「在册」先例）并补注「图谱在册/在册」签法首见 :112/:113 · 2026-09-30。亲读核实：01_modules.md :112（chat-history-api）与 :113（hitl-browser-decide）均为维护者签「图谱在册」2026-09-30 行 ✓；:130 为维护者签「在册」2026-10-20 delegation-naming-boundary 回写行（capability 行 delegation 段行内备注 + 不新增一级模块）✓。承册口径与先例同源，`graph_change_layer=none` + graph_delta（01_modules.md:34 capability 行 delegation 段备注 + 闸登记表新行 · :34 亲读确为 capability 行）自洽性维持 R1 裁定 ✓

## 二、fixback 连带新失真排查 —— 未发现

- 范围/非范围/验收编号一致性：范围节「验收 TC1–TC5」、FP-3→TC5、FP-6→TC4 交叉引用完好；TC6–TC8 定义未漂移。
- 思考轮控制表：R0–R5 六轮齐、`actual_last_round`=R5 如实、R5 residual 仍载 HG-AUDIT-R1=pending ✓；R1/R3 行改写后与 §一 B1 实证逐字对拍无冲突。
- 状态行（task :3）与修订记录第二条（task :198）如实记录三项 fixback，与实证结果一致，无夸大。
- 闸态：HG-AUDIT-R1 仍 **pending**（task :37）· 本帽未代签 ✓；HG-TASK-DRAFT / HG-GRAPH-MODULES 行未被 fixback 扰动。
- R1 已验绿项未被触碰：锚点清单（task :123-130）、兼容性枚举（delegation.py 十五处）、分支纪律三处（task :6/:13/:122）、非范围五条均原样。

## 三、审查要点 1–5 复核结论（R2 总览）

1. 范围/非范围与 SPEC :67 一致性 · 验收可机断性 —— **PASS**（TC1–TC8 每条输入→期望可机断；TC3 两态判别实证成立）
2. failure_paths 覆盖（兼容语义漂移 FP-1 · 正向误伤 FP-6+TC4 · 非 str FP-3+TC5 · grep 漂移 FP-4）—— **PASS**（维持 R1 裁定）
3. 思考轮控制表 R0–R5 闭合 · actual_last_round 如实 —— **PASS**
4. 人工闸：HG-AUDIT-R1=pending ✓ · HG-GRAPH-MODULES 承册口径与锚点（:130 · 首见 :112/:113）站得住 · graph_change_layer=none 与 graph_delta 自洽 —— **PASS**
5. 分支纪律（自 master 新建 task/fix-delegation-pattern-fullmatch · 禁直推 master · PR 前 pytest tests + ./scripts/graph-compile.sh · 勿动 site-data.json）—— **PASS**（维持 R1 裁定）

## 四、非阻塞观察（不阻塞签闸）

- N1 · TC3 新值的两态判别依赖 Python `$` 匹配换行前语义（search 放行之因），30 落地时建议测试断言直接断言 `verdict.ok is False` + `reject_class`/`violated_field`（承既有夹具形态），勿依赖报错文案——与 R1-N2 一致，30 可以 R1 审查文 §二 表为 grep 对拍基线。
- N2 · `out_of_scope` 登记的宽字符集签发侧加固（task :188）建议 00 后续立项时引用本审查文 §一 B1 实证表，避免复核成本。

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查（fail · B1/B2/B3）与本文 R2 复审（pass · 三项 fixback 实证成立）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt（红测先行 · 自 master 切 `task/fix-delegation-pattern-fullmatch`）

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

## 五、审查边界声明

本帽仅书面审查：未改 task 实质内容、未改 `app/` 与 `tests/` 任何代码、未代签 HG-AUDIT-R1（维持 pending · 本文结论 pass 仅为建议）、未 git commit / 切分支、未触碰 `docs/arch-browser/dist/site-data.json`（工作区既有 M · 别人分支）。唯一写入面 = 本审查文。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-26 | 20-task-audit R2：结论 **pass**——R1 退回 B1/B2/B3 全部 fixback 到位并逐项实证（TC3 两态判别 python3 复证 · TC8 与 CI :39 逐字一致 · 承册锚点 :130/:112/:113 亲读成立）；fixback 纯文档增量无连带新失真；建议维护者签 HG-AUDIT-R1 |