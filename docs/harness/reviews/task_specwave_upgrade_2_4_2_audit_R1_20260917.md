# task_specwave_upgrade_2_4_2 审查（R1 · 20-task-audit）

> **审查对象**：`docs/tasks/active/task_specwave_upgrade_2_4_2.md`（10-task 起草 · spec-wave 2.1.3 → 2.4.2 跨 6 版过程轨升级）
> **审查帽**：20-task-audit（书面审查 · 未改 task 实质内容 · 未代签任何 human_gate · 未执行 30）
> **日期**：2026-09-17 · **审查时仓态**：`master`（task 分支 `task/specwave-2-4-2` 待 30 开工时从 master 切）；既有脏文件 `uv.lock`（M）/ `.agents/`（??）实证与 task 非范围口径一致
> **结论**：**PASS-WITH-NOTES**（内容零阻塞 · 非阻塞注记 5 项 · 可请维护者签闸，签 HG-TASK-DRAFT 时一并裁定可选范围项 6）

---

## 结论摘要

| 维度 | 结论 |
|------|------|
| task **内容**可执行 | ✅ **PASS · 零内容阻塞**——范围/非范围闭合、验收 14 条全部可机验且实证可达、failure_paths 覆盖审查要点四风险、思考轮 R0–R5 闭合 |
| **流程闸** HG-TASK-DRAFT | `pending`（blocks 20-R1, 30）· 待维护者签，**含可选范围项 6 收编/剔除裁定** |
| **流程闸** HG-AUDIT-R1 | `pending`（blocks 30）· 本审查 PASS 后待维护者签 `approved`；禁止代签 |
| lint 复跑 | `node_modules/.bin/spec-wave task lint --file docs/tasks/active/task_specwave_upgrade_2_4_2.md` → **LINT: PASS** exit 0（2026-09-17 本帽复跑 ✓） |
| 上游实证抽查 | 2.2.0–2.4.2 增量摘要与 `/tmp/sw-pkg/package`（实证为 2.4.2 真包）**逐条一致**（详见「上游一致性抽查」） |

本审查文结论节按 spec-wave 2.3.0+/2.4.x 结论机读新口径书写（「结论」起首节 · 通过词落节内 · 实质内容充足 · 无否定共现），自身即 F-6 新闸的合规样本。

---

## 审查要点逐项核对

### 1. 范围/非范围完备性 ✅

| 核对点 | 结果 |
|--------|------|
| 钉版（范围 A-1/A-2） | ✓ `package.json:6` 实证 `"spec-wave": "2.1.3"`；`.coding-kit/manifest.json` 实证 `version=2.1.3 / from_version=2.1.0`，upgrade 后 `from_version=2.1.3` 与 MIGRATION.md「from_version=旧号」语义一致 |
| upgrade 行为 | ✓ MIGRATION.md 实证：读旧写新、写 `.coding-kit/manifest.json`、不删 `.cyning-harness/`、S2 永不覆写——与范围 A-2、非范围口径一致 |
| refresh-ide-blocks（B-3） | ✓ local 定制块零改写验收锚定 `git diff AGENTS.md CLAUDE.md` 中 `cyning-harness-local` 块，可机验 |
| sync prompts（B-4）冲突策略 | ✓ 实证复核：`FRAGMENT_30_gate_verify_v1_zh.md` / `TEMPLATE_30_gate_stop.md` / `30-execute-code.md` 仓内与 2.4.2 包资产**逐字一致**（diff -q 全 SAME）；`30-execute-code.md:42` 两版均为 `HG-GRAPH-MODULES` 行；唯一漂移 `README.md` 仓内 L42 含 `npx dsh-coding-kit`、包资产对应行为 `npx spec-wave`——「包内为准 + diff 核对 + 冲补丁即 STOP」表述清晰可裁定 |
| CI/scripts/tests 钉版字面（C-6/7/8/9） | ✓ 行号全实证（见「行号实证表」）；CI 钉的实为旧名 `dsh-coding-kit@2.1.0`（L4/L35/L39 三处），task 按实证措辞，无夸大 |
| 宿主命令向量例外（C-7） | ✓ 理由成立：MIGRATION.md 明令「安装终点始终是 spec-wave · 勿再 npm i dsh-coding-kit」；`harness_cli.py:109` 实证 `f"dsh-coding-kit@{_kit_pin()}"`；env 名不动、F-5 裁定闸单列——app 唯一触碰边界清晰 |
| 可选范围项 6 表述 | ✓ 5 文件 6 行行号全实证（见下）；收编/剔除二态与验收 N/A 注裁定人，可裁定 ✓（审查意见见专节） |
| 非范围闭合 | ✓ 9 条：历史档旧命令面豁免（done/reviews/invokes/feedback）、DAG.md 仓内独有不动、.cursor kit 资产走 FEEDBACK、占位草案点名豁免、既有脏文件留原样、不代签——循 R2 教训「显式豁免」 |

### 2. 验收可机验性 ✅（14 条逐条核对 · 无 B-1/B-3 类不可达成缺陷）

| # | 验收 | 可达性实证 |
|---|------|-----------|
| 1 | package.json/lock 钉 2.4.2 | ✓ 机械可查 |
| 2 | manifest version/from_version | ✓ |
| 3 | `--version` = 2.4.2 | ✓ |
| 4 | `check` 零 WARN | ✓ 现行 2.1.3 `check` 已零 WARN 基线（task 声明，本帽未复跑全量 check——非验收前置） |
| 5 | refresh dry-run + local 块零变化 | ✓ 锚定具体文件 diff |
| 6 | `grep -rn "dsh-coding-kit" docs/harness/prompts/` 零命中 + HG-GRAPH-MODULES 保留命中 | ✓ **当前仅 README.md:42 一处命中**（DAG.md 及其余 12 文件均无命中，实证）；sync 后由包资产覆盖即零命中；保留项锚定 `30-execute-code.md` 具体文件——**锚定旧位置+显式保留面，无 B-3 类缺陷** |
| 7 | CI grep 零命中 + `grep -c "spec-wave@2.4.2" lint-wiki-delta.yml` = 3 | ✓ 当前 `.github/workflows/` 内 `dsh-coding-kit` 仅 L4/L35/L39 三行（其余 workflow 实证零命中）；改后每行一处共 3 行，计数断言可达 |
| 8 | `spec-wave@{_kit_pin()}` 命中 1 处 + `dsh-coding-kit@` app/tests 零命中 | ✓ 当前 app/tests 内 `dsh-coding-kit@` 仅 `harness_cli.py:8`（docstring）、`:109`（向量）、tests L170/203/226 三处；C-7 已含 L8 docstring 随行更新，改后可达（pyc 噪音见 N-3）；env 名 `DSH_CODING_KIT_VERSION` 不含 `@` 不入 grep 面，task 已显式说明 |
| 9 | pytest PASS | ✓ |
| 10 | GRAPH_CLI 默认值命中 + compile exit 0 | ✓ 锚定 `GRAPH_CLI:-spec-wave` 具体模式 |
| 11 | verify --task PASS | ✓ 2.4.2 新结论闸下：本审查文合规 + F-6 处置路径明确 |
| 12 | assets/pins 基线留痕（偏差不挡） | ✓ 非阻塞型验收措辞明确 |
| 13 | opt-6 grep 零命中（收编时）/ N/A 注裁定人（剔除时） | ✓ 锚定 5 个具体文件——循 R2 教训；二态均可裁定（缺口见 N-2） |
| 14 | FEEDBACK 落盘 | ✓ |

### 3. failure_paths 覆盖 ✅

| 审查要点要求 | 落点 | 评价 |
|---|---|---|
| sync --force 冲本地补丁 | F-3（拒 --force · STOP 手合 · 实证基线无冲突） | ✓ 与范围 B-4、非范围第 4 条三处口径一致 |
| 上游布局再变 | F-2（manifest 写旧根）+ F-9（assets/pins 偏差）+ F-8（compile 产物 diff 接受） | ✓ 分层合理 |
| CI 钉版遗漏 | 验收 #7 grep 双锚（零命中 + 计数=3）机验兜底 | ✓ 虽无独立 F 条目，验收可捕获 |
| tests 钉版字符串漂移 | F-7（逐处对齐 · 禁改测试语义） | ✓ |
| 追加亮点 | F-5（app 触碰维护者裁定闸 · 无裁定不继续 C-7/C-8）、F-6（verify 新闸退回 20 的处置 · 不滥用 --allow-no-review）、F-10（CI 绿前不 merge） | ✓ 超要点覆盖 |

### 4. 上游一致性抽查（/tmp/sw-pkg/package 实证 · 全部属实）

| task 背景声明 | 实证 |
|---|---|
| 包为 2.4.2 | ✓ `package.json` version=2.4.2 |
| MIGRATION.md 最短路径：钉版 → upgrade --yes → 字面 → refresh/skills/sync | ✓ 包内 MIGRATION.md 原文一致；「安装终点仅 spec-wave · dsh-coding-kit 已 deprecate」原文在案 |
| 2.2.0 release-pins + sha256.manifest + 新命令 pins/assets | ✓ `assets/release-pins.yaml` / `assets/sha256.manifest` 在 2.4.2 存在、**2.1.3 中不存在**（实证）；`lib/cli-pins.js` / `cli-assets.js` 存在 |
| 2.2.0 verify --json `lib/inject-collect.js` 新文件 | ✓ 2.4.2 存在；2.1.3 lib 无此文件 |
| 2.3.0 verify/gate-check 结论机读（findLatestReview 取最高 R 轮 · evalReviewConclusion） | ✓ `cli-checks.js:607` findLatestReview 实证取 `round > best.round` 最高 R；`:655` evalReviewConclusion 实证「结论/签收起首节 + 通过词 + 否定词判否」；**2.1.3 中 evalReviewConclusion 计数为 0**——「语义变化系 2.3.0 新增」属实 |
| 2.3.1 N11 无结论节直接判未通过（禁止回退全文） | ✓ 代码注释与逻辑实证（chunks.length===0 → pass:false） |
| 2.4.0 N=20 内容量闸 | ✓ `REVIEW_MIN_SUBSTANCE = 20` 实证，去通过词后非空白 <20 判未通过 |
| 2.4.2 R-2 否定词窗 `不[^。；\n]{0,12}通过` / `未…` + `not\s*pass` | ✓ `REVIEW_NEG_RE` 字面逐字实证一致（另含 `no\s*pass`、`(?<!零)内容阻塞`、退回 lookbehind 族） |
| 过渡豁免 `docs/harness/legacy-gate-exempt.yaml` 缺四字段不豁免 | ✓ `LEGACY_GATE_EXEMPT_REL` 与加载逻辑实证（本仓暂无该文件，非必须） |
| prompts 资产与 2.1.3 全同 | ✓ `diff -rq` 两版 `assets/harness/prompts` **exit 0 全同** |
| ontology.yaml / discipline-coverage.yaml / host-adapt 示例有更新 | ✓ 三者 diff 均证实有差异（`assets/ide/host-adapt/README.md` 与 `examples/mvp-hosts.yaml` 亦 differ） |
| 三 bin 同入口 | ✓ `bin` 字段 `spec-wave`/`specgate`/`dsh-coding-kit` 三入口实证 |

**2.2.1 patch 未入实证面**：task 已自述并以 early_stop residual_risks ① 留痕，可接受。

### 5. 元信息与前序口径 / 闸表 / lint ✅

| 核对点 | 结果 |
|--------|------|
| 前序两 task CLOSE | ✓ `task_dsh_coding_kit_upgrade_2_1_0.md`、`task_specwave_cleanup_2_1_3.md` 均在 `docs/tasks/done/`；依赖链接路径正确 |
| 生产字段 | ✓ `graph_change_layer=none`、`review_hat=20`、`required_invoke_hats=30`、`close_pr_policy=required` 等齐全，符 AGENTS.md 生产字段要求 |
| 闸表 | ✓ HG-TASK-DRAFT / HG-AUDIT-R1 全 `pending`，无代签；HG-TASK-DRAFT blocks=`20-R1, 30` 循 R2 教训；opt-6 裁定挂 HG-TASK-DRAFT 说明列，权责清晰 |
| lint 复跑 | ✓ LINT: PASS exit 0（本帽 2026-09-17 复跑，与任务简报「lint PASS」一致） |
| 思考轮 | ✓ R0–R5 闭合、各轮有结论回填；early_stop 理由 + 3 条 residual_risks 具体；「20 认为不足 → 退回 10 补轮」回路在案 |

### 6. 破坏性变更仓内响应评估 ✅

| 上游变化 | 仓内响应 | 评价 |
|---|---|---|
| verify 结论机读闸（2.3.0+，BLOCKED 退出码 2 单一常量） | F-6 + 必读 5 + 本审查文合规书写 | ✓ 已响应；对**其他**存量/未来 task 的外溢影响已在 residual_risks ② 留痕 |
| manifest `from_version` 语义 | 范围 A-2 + 验收 #2 钉死期望值 | ✓ |
| `.coding-kit` 布局 | 无变化（2.1.3 已在新布局），非范围保留 legacy 只读 | ✓ |
| pins check S2 机械拒写无豁免 / assets verify exit 2 | 范围 E 仅体检留痕、偏差不挡验收（F-9） | ✓ 本波不引入新闸为硬依赖，稳妥 |
| dsh-coding-kit 包 deprecate | C-7 向量切换 + F-5 裁定闸 | ✓ 唯一 app 触碰理由成立 |

---

## 非阻塞注记（5 项 · 不挡签闸；N-1/N-2/N-5 建议 10-task 顺手回填或签闸时确认）

- **N-1 · 测试计数微差**：范围 C-8 称 env 钉版「实证 15 处」，实际 grep 为 **13 行**（L156/185/212/281/292/303/317/331/353/370/382/416 共 12 处精确形 + L249 注入形 `"2.1.0; rm -rf /"`）；task 所列行号清单与实证完全一致且有「以 grep 为准」对冲，仅总数 15 有误。建议顺手改「13 处」。
- **N-2 · opt-6 验收缺口（建议补一条锚定 grep）**：范围 F-12 要求 `99_mermaid_protocol.md:8` 同行 `GRAPH_CLI=dsh-coding-kit` 一并改，但验收 #13 的 grep 只查 `npx dsh-coding-kit`，**漏改 GRAPH_CLI 字面不会被验收捕获**。建议验收加一条：`grep -n "GRAPH_CLI=dsh-coding-kit" docs/_tech_graph/shared/99_mermaid_protocol.md` 零命中。（注：**不建议**把验收加宽为裸名 `dsh-coding-kit`——实证该 5 文件另有 5 处裸名历史叙述/上游指针命中，见 N-4，加宽将导致 B-1 类不可达成。）
- **N-3 · pyc 二进制噪音**：验收 #8 的 `grep -n "dsh-coding-kit@" app/ tests/` 当前会命中 `__pycache__/*.pyc`（Binary file matches）。改码 + pytest 重编译后实践中可达，但建议加 `--include='*.py'` 更稳。
- **N-4 · opt-6 收编后的残留裸名（签闸裁定时请明示不动）**：实证 5 文件除 6 处命令字面外，另有 5 处裸名 `dsh-coding-kit` 为历史叙述/上游指针：`coding_wiki/README.md:37`（兼容注记）、`inform-graph-backfill/README.md:15`（迁移 SPEC 引用）、`agent_close_discipline.md:4`（**契约真值上游路径指针**，改动会断指针）、`99_mermaid_protocol.md:13` / `:136`（2026-08-25 历史叙述）。建议维护者裁定「收编」时明示此 5 行维持不动（史实/指针），与 task 非范围「历史档不改写」精神一致。
- **N-5 · 自检结论表占位**：task §自检结论仍为 draft 占位行，而 lint 已 PASS（本帽复跑确认）。建议 10-task 回填 `task lint` 行后再送签，或签闸时维护者知悉。

---

## 可选范围项 6 审查意见（维护者裁定参考）

**建议：收编。** 理由：

1. **面小且全实证**：5 文件 6 行命令字面，行号级基线已在 task 与本文双侧实证；验收锚定具体文件，无 B-1/B-3 类风险。
2. **本波顺手成本最低**：2.4.2 升级后这 5 处 `npx dsh-coding-kit` 指向已 deprecate 包，属「活文档命令面」与上一波非范围「历史档不改写」性质不同——上一波 deferred 的裁定前提（留待后续波）由本波自然兑现。
3. **与 C-6/CI 字面变更同质**：同一次 grep 清零心智，避免后续波次再开 task 的流程成本。
4. 收编时请连同采纳 N-2（补 GRAPH_CLI 锚定验收）与 N-4（明示 5 处裸名历史行不动）。

若维护者裁定**剔除**：口径与上一波一致、风险可控（task early_stop residual_risks ③ 已留痕），亦成立。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（PASS-WITH-NOTES · 非阻塞注记 5 项）
- [ ] 裁定**可选范围项 6**：收编（建议连同 N-2/N-4）或剔除（验收 #13 标 N/A 注裁定人）
- [ ] （建议）10-task 顺手回填 N-1（15→13）、N-2（验收加 GRAPH_CLI 锚定 grep）、N-3（--include='*.py'）、N-5（自检表 lint 行）；不回填亦不挡签闸
- [ ] 在 task 人工闸表将 HG-TASK-DRAFT、HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
