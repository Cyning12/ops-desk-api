# Task 审查：fix-delegation-pattern-fullmatch（R1）

> **审查帽**：20-task-audit（书面审 · 不改 task 实质内容 · 不动 app/ · tests/ · 不代签人工闸 · 未 git 任何操作 · 未触碰 docs/arch-browser/dist/site-data.json）
> **被审对象**：`docs/tasks/active/task_fix_delegation_pattern_fullmatch.md`（状态=draft · 2026-10-26 10-task 落稿）
> **配套 invoke**：`docs/harness/invokes/by-task/fix-delegation-pattern-fullmatch/invoke_20261026_10_fix-delegation-pattern-fullmatch.md`（在册 · 与 task 闸表一致）
> **对照真值**：`docs/spec/host-v1-delegation-token/SPEC-host-v1-delegation-token_v0.md`（signed · :67 pattern 约束条目）
> **审查日期**：2026-10-26
> **审查方式**：通读 task/invoke/SPEC 全文 + 亲读代码锚点 + grep 复扫 + python3 实证 TC1–TC4 在 search/fullmatch 两态下的真假值（禁信转述）

## 结论

**fail（退回 10-task 3 项 · B1 为硬阻塞）**。task 结构完备、锚点核验几乎全绿、闸纪律与分支纪律合规；但验收 **TC3 与修法不自洽**（python3 实证：fullmatch 化后该用例仍放行、永红，红测先行→转绿流程对 TC3 不成立），另有两处事实性锚点错误（TC8 命令未钉版与 CI 不逐字一致、HG-GRAPH-MODULES 承册锚点 :79 指错行）。**HG-AUDIT-R1 维持 pending，不建议维护者本轮签闸**；10-task fixback 后须 20 复审（R2）。

## 一、逐项核对（审查要点 1–5）

### 1. 范围/非范围与 SPEC 一致性 · 验收可机断性 —— 部分 PASS（B1/B2 阻塞）

- 范围唯一改点 `app/ops/capability/delegation.py:304` `re.search`→`re.fullmatch`，亲读核实：`check_param_constraints` 确在 :289-307，pattern 分支 :303-306，模块内 `re.search` grep 唯一命中 :304，`re.compile` :283 属签发侧不受影响。与背景节转述逐字一致。
- SPEC :67 只规定「v1 约束子集 = enum / max_len / pattern（正则）三种纯代码校验 · 未知约束类型 → 拒绝签发」，**未锁定 search/fullmatch 匹配语义**——本 task 的 fail-closed 收紧与 SPEC 不冲突，R-e（参数越约束）拒绝类语义一致；非范围（enum :297 / max_len :299-302 / 签发侧 :252 / `_delegation_gate` gateway.py:277-334 / freeze 全零变更）与 SPEC §3 无重叠。PASS。
- 验收可机断性：TC1/TC2/TC4/TC5/TC6/TC7 每条有明确输入→期望、经既有 `_issue`/`_verify` 夹具纯函数机断。PASS。
- **B1（硬阻塞）TC3 不可达成**：python3 实证——
  - TC1 `\d+` + `"123abc"`：search=放行 · fullmatch=拒 ✓
  - TC2 `^[a-z]+$` + `"abc\n"`：search=放行（`$` 匹配换行前）· fullmatch=拒 ✓
  - **TC3 `^[\w./-]+$` + `"../../etc/passwd"`：search=放行 · fullmatch=放行 ✗**（该值**整串**即匹配此 pattern——放宽机理纯为「字符集过宽」，与匹配函数无关；fullmatch 一行修法**治不了** TC3）
  - TC4 `\d+`+"123" / `^[a-z]+$`+"abc"：两态均通过 ✓（防误伤成立）
  - 既有 `tests/test_capability_delegation.py:233-237` `^[0-9]+$`+"123"/"12a"：fullmatch 下保绿 ✓（零 diff 对照成立）
  - 连带失真：背景节实弹 #3 归因「字符集过宽 **+ search**」中「+ search」不成立；R1 行「实弹三条全部复现（00 于 master 核实）」隐含「三坑均可由本修法闭合」不成立；R3 行「三条对抗用例覆盖三类放宽机理（子串命中 / `$` 换行前 / 宽字符集+search）」中第三类机理与 fullmatch 无关；`test_strategy_note`「三条对抗用例先在 master 上复现红 → 改 fullmatch 转绿」对 TC3 不成立（改后仍红）。
- **B2 TC8 与 CI 不逐字一致**：task TC8 写 `npx --yes spec-wave task lint-wiki-delta --target .`，而 CI 真值 `.github/workflows/lint-wiki-delta.yml:39` 为 `npx --yes spec-wave@3.5.0 task lint-wiki-delta --target .`（**钉版 @3.5.0**）。验收文字自称「与 PR CI sample `run:` 行逐字一致」不成立。

### 2. failure_paths 覆盖 —— PASS

- 兼容性语义漂移（search→fullmatch 对未锚定 pattern）：FP-1 正面裁定（由放行变拒=修复意图 · R 轮 grep 对拍兜底 · 漂移回填禁静默）✓
- 误伤正向值：FP-6 + TC4 双钉 ✓
- 非 str 值：FP-3 + TC5（`:304` 前半分支 `not isinstance(value, str)` 语义不变，亲读属实）✓
- 另覆盖流程闸（FP-2）、grep 漏检（FP-4）、非范围越界（FP-5），可重试/用户可见列齐。K7 旧测影响面项在自检结论 :183 已列（行为变更类 task checklist 满足）。

### 3. 思考轮控制表 —— 结构 PASS · 内容受 B1 连带

- R0–R5 六轮齐、`actual_last_round`=R5 如实、全 `early_stop=false`、residual_risks 列如实（R5 载 HG-AUDIT-R1=pending）✓
- 但 R1/R3 行内容受 B1 连带失真（见 §一.1），随 fixback 一并改写。

### 4. 人工闸 —— 闸态 PASS · 承册锚点 B3

- **HG-AUDIT-R1=pending** 在表（task :37）· 本帽未代签 ✓；invoke GATE_VERIFY 摘要与 task 闸表一致 ✓。
- HG-GRAPH-MODULES=approved 的承册口径**本身站得住**：`docs/_tech_graph/l1/01_modules.md:130` delegation-naming-boundary 先例（行内备注写实 + 闸登记表新行 · 不新增一级模块 · 零新跨模块边）+ SPEC Q3 裁定（不新增一级模块 · 图谱义务=行内备注）支撑 `graph_change_layer=none` + graph_delta（:34 capability 行 delegation 段备注补写 + 闸登记表新行）的自洽性 ✓
- **B3 锚点指错行**：task :38 引「承 01_modules.md:79 · 2026-08-30 在册口径」——亲读 :79 为 2026-08-30 lg-rag-sse-stream-updates 的「00 代签 ·『开工』」登记行，**非「在册」口径行**；维护者签「图谱在册」/「在册」签法首见于 :112/:113（2026-09-30）与 :122/:128/:130。口径结论不变，锚点应改指「在册」口径行（如 :130）。

### 5. 分支纪律 —— PASS

- task :6 / :13（git_branch 行）/ :122（依赖节）三处一致写明：30 开工须自 master 新建 `task/fix-delegation-pattern-fullmatch`、禁直推 master、当前工作区 `task/specwave-3-5-0` 勿混入、PR 前 `pytest tests` 绿 + `./scripts/graph-compile.sh` 过；勿动 `docs/arch-browser/dist/site-data.json` 既有 M。与 AGENTS.md 分支纪律一致 ✓

## 二、兼容性核验（复扫对拍 · 与 00 预扫一致 · 零漂移）

| 核验项 | 结果 |
|---|---|
| `grep pattern app/ops/capability/manifests/` | 零命中 ✓ |
| `param_constraints` 全仓出现点 | 仅 delegation.py :178,195,225,239,252,262,265,268,289,291,405,425,426,454,555（十五处逐一命中）+ tests/test_capability_delegation.py + SPEC/task/invoke 文档 ✓ 零漂移 |
| delegation.py 内 `re.search` | 唯一 :304 ✓ |
| budget.py:103-105「假门」注释 | 亲读逐字成立 ✓ |
| gateway.py:277-334 `_delegation_gate` | 亲读成立（非范围定位锚）✓ |
| 既有 pattern 用例 :233-237 fullmatch 下行为 | python3 实证保绿（"123" 过 / "12a" 拒）✓ 零 diff 对照成立 |

## 三、阻塞 / 非阻塞分列

**内容阻塞（退回 10-task）**：

| ID | 阻塞 | 退回 task 小节 |
|----|------|----------------|
| B1 | TC3 验收不可达成：`^[w./-]+$` + "../../etc/passwd" 在 fullmatch 下仍放行（整串本即匹配 · 放宽机理=字符集过宽 · 与 search/fullmatch 无关），红测先行→转绿流程对 TC3 不成立；连带实弹 #3 归因、R1/R3 行、test_strategy_note 失真 | 「验收标准」TC3 ·「背景与目标→问题」实弹 #3 ·「思考轮控制」R1/R3 行 · 元信息 `test_strategy_note` |
| B2 | TC8 命令未钉版，与 CI `lint-wiki-delta.yml:39`（`spec-wave@3.5.0`）不逐字一致 | 「验收标准」TC8 |
| B3 | HG-GRAPH-MODULES 承册锚点 :79 指错行（:79 非「在册」口径行；应指 :112/:113 或 :130） | 「人工闸」表 HG-GRAPH-MODULES 行 |

**非阻塞观察**：

- N1 · B1 处置方向建议（供 10-task 定夺，本帽不代决）：(a) TC3 改用能区分两态的值——如 `"../../etc/passwd\n"`（`$` 换行前机理）或 `"../../etc/passwd;id"`（子串命中机理），保持「钉死 pattern 整串语义」目的；宽字符集路径穿越属约束作者纪律/签发侧校验面问题，登记 `out_of_scope` 另立 task（如签发侧 `validate_param_constraints` 拒高风险字符集 pattern——注意 :252 属本 task 非范围，恰印证应另立）；或 (b) 删 TC3 并将实弹 #3 定性改写为「字符集过宽为独立问题 · 本 task 不治」。两案均须同步改写 R1/R3 与 test_strategy_note。
- N2 · FP-1/FP-4 的「30 复扫对拍 → 漂移回填 → 20 复审」回路与本 R1 实证基线一致，30 可直接以本审查文 §二 表为对拍基线。

## 四、回填清单（10-task fixback · 禁附 30 Prompt）

1. B1：改写 TC3（换可判别值或删除）+ 实弹 #3 归因去「+ search」+ R1/R3 行改写 + `test_strategy_note`「三条对抗用例」表述对齐（若保留三案则 TC3 须为真可转绿用例；宽字符集问题登记 `out_of_scope`）。
2. B2：TC8 改 `npx --yes spec-wave@3.5.0 task lint-wiki-delta --target .`（与 `.github/workflows/lint-wiki-delta.yml:39` 逐字一致）。
3. B3：人工闸表 HG-GRAPH-MODULES 行锚点 :79 → 在册口径行（建议 :130 delegation-naming-boundary · 与 graph_delta 先例同源）。
4. fixback 后重走 20-task-audit R2 复审（本帽），通过后方进入维护者签闸。

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（fail · B1/B2/B3）
- [ ] 10-task fixback 完成 + 20-task-audit R2 复审通过
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

## 五、审查边界声明

本帽仅书面审查：未改 task 实质内容、未改 `app/` 与 `tests/` 任何代码、未代签 HG-AUDIT-R1（维持 pending）、未 git commit / 切分支、未触碰 `docs/arch-browser/dist/site-data.json`（工作区既有 M · 别人分支）。唯一写入面 = 本审查文。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-26 | 20-task-audit R1：结论 **fail（退回 10-task 3 项）**——B1 TC3 与 fullmatch 修法不自洽（python3 实证整串匹配仍放行 · 硬阻塞）· B2 TC8 未钉版与 CI 不逐字一致 · B3 HG-GRAPH-MODULES 承册锚点 :79 指错行；锚点/兼容性/闸态/分支纪律逐项亲验全绿（§一/§二）；HG-AUDIT-R1 维持 pending 不建议本轮签 |
