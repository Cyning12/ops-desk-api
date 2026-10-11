# invoke：10-task 起草 verify-upstream-dual-address（2026-10-11）

> **hat**：10-task · **task_slug**：`verify_upstream_dual_address`  
> **worktree**：`../ops-desk-api-worktrees/t-verify-upstream-dual-address` · **分支**：`task/verify-upstream-dual-address`（base master `286d825`）  
> **性质**：只起草 task 文档 · 零实现码改动

## 1. 任务来源

- 交接档 `docs/harness/invokes/by-task/_prompts/PROMPT_00_spec-campaign-handoff_20261011.md` §2.2 第 3 项（verify 上游根治：findLatestReview 支持址B）+ §4-3（审查档口径墙机读纪律坑）。
- 规约档 `docs/harness/CONVENTION_review_gate_dual_address_v1_zh.md` 全文真读：过渡期「审查文必须落址A、可同时落址B」生效中；「上游若日后支持，本规约届时修订」= 本 task 收口依据。
- 00 派单要求：task = 上游 issue/PR 根治 + 根治后本仓解除双址复制纪律的收口条件。

## 2. 真读清单（锚点全部实证 · 零编造）

| 对象 | 结果 |
|------|------|
| 交接档 PROMPT_00 §2.2/§4 | 立项项 + 坑全集（verify 管道吞码 · 闸表 4 列纯 pending · invoke 禁 heredoc） |
| CONVENTION 双址规约 v1 | 工具口径实证表 + 误报两起（hitl_auto_resume_claim_race · B1/B2）+ 存量零挪零改契约 |
| 上游源码 Cyning12/SpecWave @ `fad4694`（本机 checkout `~/Desktop/Projects/dsh-coding-kit`） | `src/checks/review-gates.ts:92-114` findLatestReview；**:96** 扫描面写死 `docs/harness/reviews` + `reviews` 两址（址B `docs/audits/task-review/` 不在内）；**:99** 命名 RE `^(task_.+?)_audit_R(\d+)_.*\.md$`；**:116-119** findReview 布尔投影同源；**:46** spec 扫描面同构限制 |
| 本仓安装镜像 | `node_modules/spec-wave@3.0.1/lib/checks/review-gates.js:89-114`（编译产物与源码行对齐） |
| 本仓钉版三处 | `scripts/graph-compile.sh:28` GRAPH_CLI=spec-wave@3.0.1 · `package.json:6` · `.github/workflows/lint-wiki-delta.yml:35`（3.2.0 implementedBy schema 前科在案 · bump 须实证） |
| lint/verify 契约（node_modules spec-wave 3.0.1 真读） | E3 节名须字面 `## 验收标准` 无编号 · E8 wiki_delta 必填 · 闸表 GATE_ROW_RE 4 列 status 纯词 · G4 思考轮 `### R0`–`### R5` + 控制表头 `| 轮 | 结论 | early_stop |` · E6 禁绝对本机路径 · E7 slug 归一（_→-） |
| 模板 | 仓内 `docs/harness/templates/TASK_TEMPLATE.md` + 上游 `TASK_TEMPLATE_upstream_pr_v1.md`（思考轮五槽形制） |
| 先例 | `docs/tasks/done/task_specwave_verify_baseline.md`（序3 姊妹 task）· `task_testing_write_capability.md`（元信息字段形制） |

## 3. 关键裁定

1. **slug**：`verify_upstream_dual_address`（00 建议照录）· 文件名 `task_verify-upstream-dual-address.md`（连字符 · 仓惯例；E7 normalizeSlug 下 _≡- 一致）。
2. **graph_change_layer=none**：本仓改动面=钉版 bump 三处 + CONVENTION 规约档修订，不触 `docs/_tech_graph/` 模块语义；docs-only 先例取值 `none`（51 处在案）。
3. **test_strategy=recommended**：上游实现面单测在上游仓随 PR 交付；本仓零业务码，验收=收口红绿对照 + pytest 零新增红对拍。
4. **址B 命名不同构**（`YYYYMMDD_<slug>_r<n>.md` vs 址A `task_<slug>_audit_R<n>_*.md`）钉为 R2 思考轮种子：上游支持须同时扩扫描目录 + 识别第二命名口径。
5. **范围切分**：上游 issue/PR + 本仓收口条件（钉版 bump / 实证 / 规约修订）一 task 承载；上游实现方案不锁死（留 R2–R5）。

## 4. 产出与校验

- 产出：`docs/tasks/active/task_verify-upstream-dual-address.md`（draft · 三闸 pending · R0/R1 已真读预填 · R2–R5 种子待执行链回填）
- `npx spec-wave task lint --file <task>` → **LINT_EXIT=0 · LINT: PASS**
- `npx spec-wave verify --target . --task <task> > /tmp/verify_verify_upstream_dual_address.log 2>&1; echo $?` → **VERIFY_EXIT=2** · `VERIFY: BLOCKED · HG-AUDIT-R1 pending`（三闸 pending 逐条点名 · 新 draft 正确语义 · 非 lint 解析问题）
- verify 后 `git status --porcelain` 仅本 task 新增档一行 → **零再生噪音**

## 5. 遗留

- 三闸待维护者签（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES · 20 R1 审查先行）。
- R2 方案对比（甲 加第三址+第二 RE / 乙 可配置扫描面 / 丙 统一命名迁档——丙违存量零挪零改契约倾向否）待执行链裁定。
- 收口执行依赖上游发版节奏（上游维护者决策 · 非本仓可控）。
