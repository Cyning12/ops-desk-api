# specwave-verify-baseline 审查（R1 · 20-task-audit）

> **双址过渡复制件**：本文由 CLOSE 棒（2026-10-11）自址B 原件 `docs/audits/task-review/20261011_specwave-verify-baseline_r1.md` 逐字复制落址A——依 `docs/harness/CONVENTION_review_gate_dual_address_v1_zh.md` §二 过渡期口径「新增审查文必须落址A（verify 唯一消费址）· 可同时落址B 存档」；址B 原件原址原内容不动（钉死契约 4/5）。下文与原件同文。


> **审查对象**：`docs/tasks/active/task_specwave_verify_baseline.md`（commit f992fff · 仓级 verify 缺口基线收口 chore · 00 代笔落稿）
> **审查帽**：20-task-audit（R1 书面审查 · 未改 task 实质内容 · 未代签任何 human_gate · 未执行 30 · 未切分支 · 仅落本审查文+invoke 两档）
> **日期**：2026-10-11 · **审查时仓态**：worktree `t-specwave-verify-baseline` · 分支 `task/specwave-verify-baseline`（task 文档 commit f992fff · base master `cae745e`）
> **委托令**：00 委派令 帽位 20-task-audit · 六审查要点 · 时效 15 分钟 · BLOCKER 退修订 / NIT 照登
> **实证留痕**：`/tmp/verify_baseline_r1.txt`（verify 全量输出）· `/tmp/lint_r1.txt`（task lint 输出）

## 结论

结论：本帽裁定 **BLOCKER · 退 10 修订**——task 内容面（实跑真值/D1 三案/钉死契约/TC 组）经本帽逐项复核**扎实可执行**（详见 §一~§五 全正向），但 `npx spec-wave task lint` 亲跑 **EXIT=2 FAIL**（E3 缺 ## 验收标准节 · E4 缺 failure_paths 节 · E5 缺 ### 自检结论节 · E8 缺 wiki_delta 行 · 见 §六），其中 E4 failure_paths 属内容性缺失（AGENTS.md 启动纪律必读三件套之一），20 帽不代改 task，退修订补齐后再签 HG-AUDIT-R1。修订量小（节名对齐 + 补两节 + 补一行），修订棒可顺带吸收 N-1~N-3。

## 一、实跑复核（要点② · 全对账 ✓）

- 本帽亲跑 `set -o pipefail; npx spec-wave verify --target . > /tmp/verify_baseline_r1.txt 2>&1` → **TRUE_EXIT=2** ✓ 尾行 `VERIFY: BLOCKED · 仓级 reviews 缺口 93` ✓（与 task §1 声称一致 · 重定向取码 · D3 管道吞码坑钉案必要且表述准确）。
- **缺口 93 对账**：输出明细行 `^  - docs/tasks/done/` 恰 **93 行** ✓ 1:1。
- **分账 52+36+5 复核**：missing R<n> review = **36** ✓ · SUBJ = **5** ✓ · 第三类 task 合并计 52 = 实跑拆分 **39**（无结论/签收起首节或节内无通过词）+ **13**（结论节含否定结论词）= 52 ✓——合并计数口径如实。
- **抽查**：task_strategy_builder_spec 同类例 `task_tenant_readonly_predicate` 在 `docs/harness/reviews/` 零审查档 ✓（missing 声称成立）；reviews/ 现 **133 档** ✓ 与 task §1 一致。
- ⚠ 微偏：verify 头行实报 `done tasks: 154`，task §1 与修订录写「done/ 155 档」——计数差 1 · 93 缺口真值不受影响 → 记 N-1。

## 二、D1 三案与豁免机制探查（要点③）

- **倾向 C 理由成立**：A 全量补审「为绿而写」风险与历史档语义难真审的论证诚实 ✓；B 存量永不合规但成本最低 ✓；C 混合（近期真补审 + 古早豁免注记「未审」）诚实可行 ✓——三案利弊陈述如实，倾向有理。
- **豁免机制原生支持探查（本帽已落地 · task 留 30 首步的探查要求提前闭环）**：verify 3.2.0 输出头行明示「reviews 缺口（**failClosed** · 存量过渡豁免走 `docs/harness/legacy-gate-exempt.yaml` · **四字段 slug/reason/date/authorized_by**）」——**原生支持按档钉死的存量豁免清单** ✓。仓内该 yaml **尚未建立**（落地面 = 新建原生清单档，非仓内脚本承载）；task D1 末行「不支持则仓内脚本/配置承载」兜底分支实证**不会触发**。另 CLI 面有 `--allow-no-review` 等宽口径开关（全豁免某类 · 不适配「按文件名钉死」诉求），failClosed 清单机制正解 D1-B/C。→ 记 N-2（30 可直接钉四字段清单档 · 建议豁免档注记「存量基线豁免 · 未审」+ 增量零豁免口径入 invoke）。
- **D2 双址**：`docs/audits/task-review/` 现仅 1 档 vs reviews/ 133 档，「只钉规约文档 · 不挪存量」最小面倾向成立；规约文档落点档名未钉 → 记 N-3（留 30 钉名即可）。

## 三、钉死契约 5（要点④ · 禁伪造审查为核心）可机验性

| # | 契约 | 可机验性裁定 |
|---|---|---|
| 1 | 零业务码改动 | ✅ git diff 路径集限定可机断 |
| 2 | 禁伪造审查（补录注「存量补录 · 非同期审查」· 豁免注「未审」） | ✅ 核心红线——注记措辞可 grep 机查 + TC4 维护者抽 5 档人读兜底，双层闭合 |
| 3 | 增量门禁不破（反向实证） | ✅ TC3 机断（failClosed 行在案 → 新增不合规档必红） |
| 4 | 既有 133+ 合规档零 diff | ✅ git diff 路径限定可机断 |
| 5 | done/ 档本体零改 | ✅ git diff 路径限定可机断（豁免走新建 yaml · 不动 done 档 ✓ 与原生机制契合） |

## 四、TC1–TC5（要点⑤ · TC3 反向实证形态）

- **TC1** 基线全表 1:1 对账——本帽已实证可行（93 明细行逐档可对）✓。
- **TC2** `set -o pipefail; npx spec-wave verify` EXIT=0 · 尾行 PASS——口径与 D3 互锁 ✓。
- **TC3** 反向实证：临时加一不合规档 → 红且指向该档 → 撤档复绿——failClosed 机制在案（§二），形态标准可构造、可加撤复绿闭环 ✓。
- **TC4** 诚实性抽查（维护者抽 5 档可读）——人读兜底与契约 2 互锁 ✓。
- **TC5** pytest 零新增红（master 基线对拍）+ 既有档 git diff 零——chore 面反回归完整 ✓。

## 五、非范围查漏（要点⑥）

三项非范围划定合理（不改上游 verify 规则 · 不重审古早档内容 · 双址物理归一留裁定）。本帽补查无漏：active draft 的 warn-不闸行为不受本 task 影响（头行实证 ✓）；新建 legacy-gate-exempt.yaml 非 task/review 档、不在 reviews 扫描面，无递归门禁风险；93 处置后 verify 输出口径变化已由 TC2 覆盖。

## 六、lint 复跑（不采信自报 → B-1）

本帽亲跑 `npx --yes spec-wave task lint --file docs/tasks/active/task_specwave_verify_baseline.md` → **EXIT=2 · LINT: FAIL**：
- **[E3] 缺 ## 验收标准 节**——task 实有「## 5. 验收标准（TC 组 · 可机验）」，节名带编号前缀致 lint 不识（形式瑕疵 · 去编号即解）。
- **[E4] 缺失败路径节**（## 失败路径 或 failure_paths）——**内容性缺失**（AGENTS.md 启动纪律将 failure_paths 列 task 必读三件套）。
- **[E5] 缺 ### 自检结论 节**——draft 期占位符即合法（先例口径 · close 前 40 回填）。
- **[E8] 缺 wiki_delta 行**——Harness 元信息表须含 `wiki_delta: path|none|n/a`（本 task 纯文档面 · 填 n/a 即解）。
- 附 warn：W2 缺 ### 人工闸 节（轻量 task 可忽略）· W4 无思考轮节（chore/bugfix 轨合法豁免）。

## BLOCKER 项（退修订）

- **B-1**：task lint EXIT=2 FAIL（E3/E4/E5/E8 四 error · §六）——退 10/维护者修订：节名对齐 `## 验收标准` · 补 failure_paths 节 · 补 ### 自检结论 占位节 · Harness 元信息表补 wiki_delta 行；修订后 lint EXIT=0 再签 HG-AUDIT-R1。修订棒可顺带吸收 N-1~N-3（均低成本）。

## 非阻塞观察项（N-1~N-3 · 照登不闸）

- **N-1**：done/ 档数 task 写 155 · verify 实报 `done tasks: 154`——计数微偏 1，93 缺口真值与分账对账均不受影响，修订时顺手对齐即可。
- **N-2**：豁免机制原生支持已由本帽实证闭环（`docs/harness/legacy-gate-exempt.yaml` · failClosed · 四字段 slug/reason/date/authorized_by · 仓内未建）——30 无需再做「是否支持」探查，可直接钉四字段清单档；建议 30 invoke 钉「豁免档注记存量基线豁免 · 未审 + 增量档零豁免」口径。
- **N-3**：D2 规约文档落点档名未钉——「只钉规约不挪档」倾向成立，建议 30 钉规约档名落点（如 standards 或 harness 规约面），免收口争议。

## 维护者签闸（修订后 · 30 前）

- [ ] 已读 R1 审查结论（BLOCKER · B-1 退修订 · N-1~N-3 照登）
- [ ] 10 修订落地：lint EXIT=0（E3/E4/E5/E8 清零）
- [ ] 在 task 人工闸表将 HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 改 approved（维护者 · 日期）
- [ ] 再下发 Harness 30 Prompt（30 Agent 以 task 表为准 · pending 必须拒开工）

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 20 R1 书面审：实跑复核全对账（EXIT=2 · 93=36+5+39+13 · 抽查 tenant_readonly_predicate ✓ · reviews/ 133 ✓）· 豁免机制原生支持实证闭环（legacy-gate-exempt.yaml · failClosed · 四字段）· D1 倾向 C 成立 · 钉死契约 5 全可机验 · TC1-TC5 可证伪 · lint 亲跑 EXIT=2 FAIL → 裁定 **BLOCKER 退修订**（B-1）· N-1~N-3 照登 · 三闸 pending 未代签 |
