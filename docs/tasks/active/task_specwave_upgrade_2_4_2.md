# Task：spec-wave 升级 2.4.2（2.1.3 → 2.4.2 · 跨 6 版过程轨升级）

> **状态**：draft  
> **类型**：基础设施 / harness 过程轨升级（minor×4 + patch×2 跨度：2.2.0/2.2.1/2.3.0/2.3.1/2.4.0/2.4.1）  
> **前置**：manifest / package 钉 `2.1.3`（`task_dsh_coding_kit_upgrade_2_1_0` + `task_specwave_cleanup_2_1_3` 均已 done）；npm 最新 **`2.4.2`**（2026-09-15 发布）  
> **分支**：`task/specwave-2-4-2`（**从 master 切**；master 已同步 origin/master）  
> **执行模式**：Open Folder = **ops-desk-api**；过程轨；不改 `app/` 业务逻辑（唯一例外：`app/ops/capability/harness_cli.py` npx 命令向量包名 1 行机械改，理由见范围 5-B）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `specwave-upgrade-2-4-2` |
| **git_branch** | `task/specwave-2-4-2`（base：`master`） |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | `node_modules/.bin/spec-wave check --target .` 已是最新零 WARN；`node_modules/.bin/spec-wave --version` = 2.4.2；`verify --task` 本 task PASS；`./scripts/graph-compile.sh` exit 0（GRAPH_CLI 默认 `spec-wave`）；`pytest tests/test_capability_harness_cli.py` PASS（mock 钉 `spec-wave@2.4.2`）；CI `lint-wiki-delta.yml` 钉 `spec-wave@2.4.2`；grep 旧字面锚定零命中（见验收） |
| **code_quality_bar** | `not_applicable` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 过程轨升级；compile 产物可能因 kit 变化改写，不改 YAML 源 |
| **wiki_delta** | `none` |
| **wiki_delta_note** | 本波不晋升 coding_wiki；FEEDBACK 走 evidence + doc-health/feedback |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **invoke_retention_profile** | `minimal` |
| **required_invoke_hats** | `30` |
| **close_pr_policy** | `required` |
| **related_pr** | TBD（30 执行后回填） |
| **review_hat** | `20` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20-R1, 30 | 2026-09-17 维护者授权 00 本窗代签；范围 F 裁定**收编**（含 N-2/N-4 边界） |
| HG-AUDIT-R1 | approved | 30 | 20-task-audit R1 PASS-WITH-NOTES（reviews/task_specwave_upgrade_2_4_2_audit_R1_20260917.md）· 2026-09-17 维护者授权 00 本窗代签 |

---

## 背景与目标

本仓 spec-wave 钉 **2.1.3**（`package.json` devDependencies exact + `.coding-kit/manifest.json`）。npm 最新 **2.4.2**（2026-09-15 发布），中间跨 **2.2.0 / 2.2.1 / 2.3.0 / 2.3.1 / 2.4.0 / 2.4.1** 共 6 个版本。上游包内 `MIGRATION.md` 最短路径：钉 `spec-wave@2.4.2` → `npx spec-wave upgrade --yes` → CI/脚本字面改 `npx spec-wave` →（推荐）`refresh-ide-blocks` / `skills install` / `sync prompts`。

### 2.2.0–2.4.2 关键增量（解包 2.4.2 与仓内 2.1.3 `node_modules/spec-wave/` 实证对比）

| 版本 | 增量 |
|------|------|
| 2.2.0 | **release-pins 闭环**：`assets/release-pins.yaml`（版本/身份钉单一声明源）+ 新命令 `pins check` / `pins fix`（默认 dry-run · **S2 机械拒写无豁免**）；**assets 完整性**：`assets/sha256.manifest` + 新命令 `assets verify`（偏差 exit 2）/ `assets manifest rebuild`；**verify --json 可观测**（W3 C2）：`traceId` / `source` / `injectedFiles` 字段（契约只增不改 · `lib/inject-collect.js` 新文件）；BLOCKED 退出码 2 单一常量 |
| 2.2.1 | patch（细节以包内资产为准，未入本 task 实证面） |
| 2.3.0 | **verify/gate-check 语义变化（W4）**：审查文判定由「存在性」升级为「**结论机读**」——`findLatestReview` 取**最高 R 轮**为真值（R2 通过覆盖 R1 退回）；`evalReviewConclusion` 要求审查文含以「结论/签收」起首的 `##/###` 节、节内通过词（PASS/ACCEPT/签收/通过/零阻塞）且无否定命中；不可机读通过 → `VERIFY: BLOCKED`（`--allow-no-review` 留痕豁免；done 目录降级 warn）；新增过渡豁免数据 `docs/harness/legacy-gate-exempt.yaml`（缺四字段不豁免） |
| 2.3.1 | N11：审查文**无结论/签收节 → 直接判未通过**（禁止回退全文 · 封堵「只写通过二字」绕过面） |
| 2.4.0 | W2 S1：结论节**内容量闸 N=20**（去通过词后残余非空白字符 < 20 → 判未通过 · failClosed） |
| 2.4.1 | 否定词窗初版（`不/未` 与 `通过` 间 ≤3 任意字符） |
| 2.4.2 | patch（2026-09-15 · 2.4.1 验收三条修复）：**R-1** host validate 缺省基修复；**R-2** 否定词表 + 同句共现（窗口放宽为 `不[^。；\n]{0,12}通过` / `未[^。；\n]{0,12}通过`，封堵插 4 字超窗形态 · 排除跨句误中）+ `not\s*pass`；**R-3** pin-16 无引号属性修复；tag/npm 同 commit 发版 |
| 资产面 | `assets/harness/prompts/*` 与 2.1.3 **全同**（仓内仅 `docs/harness/prompts/README.md` 为旧版漂移，含 `npx dsh-coding-kit` 字面 L42）；`ontology.yaml` / `discipline-coverage.yaml` / `host-adapt` 示例有更新；包内新增 `MIGRATION.md` / `GLOSSARY.md` |
| bin 面 | `spec-wave` / `specgate` / `dsh-coding-kit` 三 bin 同入口（2.1.3 已如此）；**安装终点仅 `spec-wave`**，registry 上 `dsh-coding-kit` 包已 deprecate 且**无 2.4.2 版本** |

目标：package/manifest/CI/scripts/tests/宿主命令向量全面钉齐 **spec-wave@2.4.2**，消费 verify 结论机读新语义（20-task-audit 结论节口径随之上调），清零过程轨旧字面。

## 范围

### A. 依赖与 manifest

1. `package.json` devDependencies `"spec-wave": "2.1.3"` → `"2.4.2"`（**exact**）；`npm install` 重装，`package-lock.json` resolved 对齐 2.4.2
2. `npx spec-wave upgrade --yes`：`.coding-kit/manifest.json` `version` 2.1.3 → 2.4.2、`from_version` = 2.1.3；**不删** `.cyning-harness/`（legacy 只读）

### B. IDE 块与 prompts

3. `refresh-ide-blocks`（默认 dry-run）→ 审报告 → 需要时 `--yes`；**`cyning-harness-local` 定制块零改写**（AGENTS.md / CLAUDE.md 块外定制：pre-30 invoke 拒改码 / HG-PILOT-OPSDESK-GLAYER / G-L0 / graph_modules_path）；备份落 `.coding-kit/backups/refresh-ide-blocks/`（已 gitignore）
4. `sync prompts --yes`：冲突策略**默认以包内资产为准**（上一波已 force 过口径），但**须 diff 核对仓内定制行**——实证基线：`FRAGMENT_30_gate_verify_v1_zh.md` / `TEMPLATE_30_gate_stop.md` / `30-execute-code.md` 仓内与包内逐字一致（`HG-GRAPH-MODULES` 行在 `30-execute-code.md:42` 两版相同）；唯一已知漂移 = `docs/harness/prompts/README.md`（仓内旧版，L42 含 `npx dsh-coding-kit`，将被包资产刷新为 `npx spec-wave`）；若 diff 发现其他仓内本地补丁（尤其 `HG-GRAPH-MODULES` 相关）被冲 → **STOP**，手合保留后 FEEDBACK
5. `skills install`（`.dsh/skills` · 不入库 · 推荐步）

### C. CI / scripts / tests / 宿主命令向量钉版字面

6. **CI** `.github/workflows/lint-wiki-delta.yml`：L4 注释 + L35 `run: npx --yes dsh-coding-kit@2.1.0 task lint-wiki-delta --target .` + L39 注释 strict 行 → 三处 `dsh-coding-kit@2.1.0` → `spec-wave@2.4.2`（其余 workflow 实证无 kit 钉版：pytest.yml 零命中 · tech-graph.yml 仅 L21 缓存注释提及 npx 通用语）
7. **宿主命令向量（app 代码唯一例外 · 必改）** `app/ops/capability/harness_cli.py`：L109 `base = ["npx", "--yes", f"dsh-coding-kit@{_kit_pin()}"]` → `f"spec-wave@{_kit_pin()}"`（L8 docstring 与 L248 capability description 字面随行机械更新；**env 名 `DSH_CODING_KIT_VERSION` 不改**、读取/校验逻辑零触碰）。**理由**：registry 上 `dsh-coding-kit` 包已 deprecate 且无 2.4.2 版本，向量不改则 env 钉 2.4.2 时 `npx` 解析失败、Host capability 直接不可用；MIGRATION.md 明令安装终点仅 `spec-wave`。维护者若禁止此行改动 → 见 failure_paths F-5
8. **测试钉版** `tests/test_capability_harness_cli.py`：`monkeypatch.setenv(DSH_KIT_VERSION_ENV, "2.1.0")` 全部 → `"2.4.2"`（实证 15 处：L156/185/212/249/281/292/303/317/331/353/370/382/416 等，以 grep 为准）；argv 断言 `"dsh-coding-kit@2.1.0"` ×3（L170/203/226）→ `"spec-wave@2.4.2"`；`"2.1.0; rm -rf /"` 非法值用例（L249）版本段同步为 `2.4.2; rm -rf /` 保持注入形态语义
9. **scripts** `scripts/graph-compile.sh`：L23 `GRAPH_CLI="${GRAPH_CLI:-dsh-coding-kit}"` → `spec-wave`（L8/L15/L16 注释内旧包名字面随行机械更新；`GRAPH_CLI` env 回退口语义保留）；`scripts/graph_mermaid_normalize.py` L6/L22 为历史叙述注释，**不动**

### D. 验收机械闸

10. `check` / `verify --task` / `graph-compile.sh` / `pytest` 全绿；FEEDBACK 落盘 `docs/spec/doc-health/feedback/`（含 sync/refresh 冲突处置与 prompts 资产回灌观察）

### E. （推荐）新命令体检

11. `node_modules/.bin/spec-wave assets verify --target .` 与 `pins check --target .` 各跑一次留痕（上游新闸在本仓的基线行为；**偏差不挡本波验收**，异常入 FEEDBACK）

### F. （已裁定**收编** · 维护者 2026-09-17 · 授权 00 代签时拍板）上一波 deferred 旧字面 5 处

12. **收编执行**：以下 5 处活文档 `npx dsh-coding-kit` → `npx spec-wave`（行号为 grep 实证基线，允许漂移，以执行时 grep 为准）：`docs/coding_wiki/README.md:36` · `docs/coding_wiki/topics/wikilinks_export.md:14` · `docs/spec/inform-graph-backfill/README.md:102` · `docs/spec/doc-health/process/agent_close_discipline.md:22-23` · `docs/_tech_graph/shared/99_mermaid_protocol.md:8`（该处同行 `GRAPH_CLI=dsh-coding-kit` 字面一并改 `spec-wave`）。**N-4 边界**（审查 R1）：5 文件中残留的 `dsh-coding-kit` 裸名历史叙述/上游指针**不动**（含 `agent_close_discipline.md:4` 契约真值指针，改动会断指针）；仅改命令字面

## 非范围

- 不改 `app/` 业务逻辑（**唯一例外**：范围 C-7 `harness_cli.py` npx 向量包名 1 行 + 2 处描述字面；env 名与校验逻辑不动）
- 不处理既有脏文件：`uv.lock`（M）、`.agents/`（??）——开工前已在，留原样
- 不 `npm publish`；不擅自 `gh pr merge`；不代签任何人工闸
- 不以 `--force` 覆盖含 `HG-GRAPH-MODULES` 等仓内定制行的 prompts 本地补丁（范围 B-4 已实证当前无冲突，冲突即 STOP）
- 不强制 `host apply --profile expanded` / `host update`（维护者手跑项，同上一波口径）
- 不删除 `.cyning-harness/`（legacy 只读）
- 不清零历史档旧命令面：`docs/tasks/done/`、`docs/harness/reviews|invokes|evidence/`、`docs/spec/doc-health/feedback/` 等历史/过程文档中的 `npx dsh-coding-kit` 属史实记录，**不改写**
- 不动 `docs/harness/prompts/DAG.md`（仓内独有，非包资产）；`.cursor/commands/kit-*`、`.cursor/skills/*` 内旧字面属 kit 上游资产，走 FEEDBACK 轨不手改
- `docs/discussions/2026-08-31_host_comms_agent_kit_nesting_plan_draft.md:24`（`npx dsh-coding-kit@pin` 占位草案）与 `docs/spec/agent-infra/06_host_comms_boundary_spec_v0.md:90`（`@<pin>` 占位）、`docs/spec/harness-to-dsh-kit-graph-migrate/`（历史迁移 SPEC）不改
- `scripts/graph_mermaid_normalize.py` 历史注释不改（范围 C-9 已述）

## 验收标准

- [ ] `package.json` `"spec-wave": "2.4.2"`（exact）；`package-lock.json` 中 spec-wave `version`/`resolved` = 2.4.2
- [ ] `.coding-kit/manifest.json` `version` = 2.4.2 · `from_version` = 2.1.3
- [ ] `node_modules/.bin/spec-wave --version` 输出 2.4.2
- [ ] `node_modules/.bin/spec-wave check --target .` exit 0 ·「已是最新」· **零 WARN**
- [ ] `refresh-ide-blocks` dry-run 报告已审；`git diff AGENTS.md CLAUDE.md` 中 `cyning-harness-local` 块内容零变化
- [ ] `sync prompts` 后：`grep -rn "dsh-coding-kit" docs/harness/prompts/` 零命中；`grep -n "HG-GRAPH-MODULES" docs/harness/prompts/30-execute-code.md` 有命中（定制行保留）
- [ ] CI：`grep -n "dsh-coding-kit" .github/workflows/` 零命中；`grep -c "spec-wave@2.4.2" .github/workflows/lint-wiki-delta.yml` = 3
- [ ] `grep -n 'spec-wave@{_kit_pin()}' app/ops/capability/harness_cli.py` 命中 1 处；`grep -n "dsh-coding-kit@" app/ tests/` 零命中（env 名 `DSH_CODING_KIT_VERSION` 保留不在此 grep 面）
- [ ] `pytest tests/test_capability_harness_cli.py` PASS
- [ ] `grep -n 'GRAPH_CLI:-spec-wave' scripts/graph-compile.sh` 命中；`./scripts/graph-compile.sh` exit 0
- [ ] `node_modules/.bin/spec-wave verify --target . --task docs/tasks/active/task_specwave_upgrade_2_4_2.md` PASS
- [ ] `assets verify` / `pins check` 基线结果已留痕（FEEDBACK 或 invoke；偏差不挡）
- [ ] （范围 F 已裁定收编）5 处旧字面替换完成：`grep -rn "npx dsh-coding-kit" docs/coding_wiki/README.md docs/coding_wiki/topics/wikilinks_export.md docs/spec/inform-graph-backfill/README.md docs/spec/doc-health/process/agent_close_discipline.md docs/_tech_graph/shared/99_mermaid_protocol.md` 零命中；**N-2 补锚**：`grep -rn "GRAPH_CLI=dsh-coding-kit" docs/_tech_graph/shared/99_mermaid_protocol.md` 零命中；**N-3**：app/tests 侧 grep 一律加 `--include='*.py'` 避 `__pycache__` 二进制噪音；裸名残留（N-4 清单）属预期不要求零命中
- [ ] FEEDBACK 落盘 `docs/spec/doc-health/feedback/`

## failure_paths

| ID | 触发 | 行为 |
|----|------|------|
| F-1 | `npm install` 失败 / lockfile 解析异常 | STOP；不重试超过一次；记录 registry 状态入 FEEDBACK |
| F-2 | `upgrade` 未写 `.coding-kit/manifest.json` 或写旧根 | STOP · FEEDBACK kit |
| F-3 | `sync prompts` 冲掉 `HG-GRAPH-MODULES` 等本地补丁行 | 拒 `--force`；STOP 手合保留后 FEEDBACK（实证基线当前无冲突，见范围 B-4） |
| F-4 | `refresh-ide-blocks` 改写 `cyning-harness-local` 块 | git checkout 回滚该文件 · FEEDBACK kit（上一波实证「跳过 local 块」行为，预期零改写） |
| F-5 | 维护者禁止改 `app/ops/capability/harness_cli.py` 向量（范围 C-7） | **STOP 问维护者**；二选一裁定：①维持禁改 → Host capability 留在 `dsh-coding-kit@≤2.1.x` 旧终点，env 钉版与宿主能力脱钩，风险书面留痕入非范围；②解除禁改 → 按范围执行。无裁定不继续 C-7/C-8 |
| F-6 | verify 2.4.2 新结论机读闸 BLOCKED（审查文无「结论/签收」节 / 内容量 <20 / 否定词命中） | 非本 task 缺陷；退回 20-task-audit 按 2.3.0+/2.4.x 新口径补结论节（通过词落节内 · 实质内容 ≥20 字符 · 避否定共现），复审后再跑；`--allow-no-review` 仅作留痕豁免不滥用 |
| F-7 | `pytest` 断言漂移（argv/环境变量字面未同步） | 按范围 C-8 逐处对齐；禁改测试语义 |
| F-8 | graph-compile 产物仅戳/格式 diff | 接受并入库（若有） |
| F-9 | `assets verify` / `pins check` 报偏差 | 不挡本波；结果留痕 FEEDBACK（范围 E-11） |
| F-10 | CI 绿前 PR 被催合 | close_pr_policy=required；PR 合并须 CI 绿 + `graph-compile.sh` 通过，不擅自 merge |

## 依赖

- 前置 task：[`task_dsh_coding_kit_upgrade_2_1_0.md`](../done/task_dsh_coding_kit_upgrade_2_1_0.md)（done）· [`task_specwave_cleanup_2_1_3.md`](../done/task_specwave_cleanup_2_1_3.md)（done · 可选范围项 6 即其 deferred 清单）
- 上游迁移真值：spec-wave@2.4.2 包内 `MIGRATION.md`（最短路径 + 推荐步）· 包内 `GLOSSARY.md`
- 钉版实证面：`package.json:6` · `.coding-kit/manifest.json` · `.github/workflows/lint-wiki-delta.yml:4,35,39` · `tests/test_capability_harness_cli.py`（15+3 处）· `app/ops/capability/harness_cli.py:109` · `scripts/graph-compile.sh:23`

## 给执行帽（30）必读

1. 本 task 人工闸表（HG-TASK-DRAFT / HG-AUDIT-R1 **approved 前拒开工**；禁止代签）
2. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（GATE_VERIFY 首输出）
3. spec-wave@2.4.2 包内 `MIGRATION.md`（升级顺序：钉版 → upgrade → 字面 → refresh/skills/sync）
4. 范围 C-7 是**本波唯一 app 代码触碰**（1 行向量 + 2 处描述字面）；F-5 无裁定不动
5. **verify 新语义预警**（2.3.0+/2.4.x）：审查文须含「结论/签收」起首节 + 通过词 + 实质内容 ≥20 字符 + 无否定共现，否则 `verify --task` BLOCKED（F-6）
6. 开工先确认 base = master 并从 master 切 `task/specwave-2-4-2`；`uv.lock`（M）/ `.agents/`（??）为既有脏文件，不动

## 思考轮控制

| 轮 | 焦点 | 结论 |
|----|------|------|
| R0 | 事实收集：npm 最新 2.4.2（2026-09-15）· 跨 6 版；解包 2.4.2 vs 仓内 2.1.3 diff 实证（新命令 pins/assets · verify 结论机读闸 · prompts 资产零变化） | 背景增量表落定 |
| R1 | 钉版面全仓盘点：package/lock/manifest/CI/tests/scripts/app 向量逐处 grep 实证行号；CI 钉的实为旧名 `dsh-coding-kit@2.1.0`（非 2.1.3），范围措辞按实证修正 | 范围 C 行号清单落定 |
| R2 | `harness_cli.py` app 代码触碰取舍：registry 无 `dsh-coding-kit@2.4.2` → 向量不改则宿主能力必坏；MIGRATION 终点仅 spec-wave | 定为必改 1 行 + F-5 裁定闸 |
| R3 | prompts 冲突面：仓内 3 个关键文件与包资产逐字一致（`HG-GRAPH-MODULES` 行含在内），唯一漂移 README.md 由包刷新即收益 | 冲突策略=包内为准 + diff 核对验收 |
| R4 | 可选范围项 6（上一波 deferred 5 处旧字面）收编取舍：活文档、面小、命令可验证；但属上一波明示「留待后续波」 | 列为可选范围项，维护者签闸裁定 |
| R5 | 验收机验锚定设计：旧字面 grep 零命中（锚定具体文件/模式）+ 新版本断言（version/manifest/pytest）双锚；历史档 grep 命中属预期不入验收 | 验收标准落定 |

- **early_stop**：R5 后停 · reason：过程轨升级，面已全实证（行号级）、命令可验证、无业务逻辑风险（app 触碰 1 行已单独立闸 F-5） · residual_risks：① 2.2.1 patch 细节未入实证面（以包内资产为准，风险极低）；② verify 新结论闸可能影响后续**其他** task 的 20-task-audit 写法（本 task 已在 F-6/必读 5 留痕）；③ 可选范围项 6 若剔除则旧字面继续存留（已与上一波口径一致，可控）
- 20-task-audit 认为不足 → 退回 10-task 补轮再审 R+1

### 自检结论

| 命令 | 退出码 |
|------|--------|
| _（draft 期占位 · 10-task 起草后回填 task lint 结果）_ | — |

### KPI

Task_KPI%: TBD（30 执行后回填） · 目标：钉 2.4.2 · manifest 升级 · CI/scripts/tests/宿主向量字面清零 · prompts 冲突零或手合保留 · check 零 WARN · verify PASS
