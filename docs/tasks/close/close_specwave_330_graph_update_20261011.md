# CLOSE：specwave-330-graph-update（spec-wave 3.0.1→3.3.0 升级与 tech_graph 适配 · chore）（2026-10-11）

> **task**：[../done/task_specwave_330_graph_update.md](../done/task_specwave_330_graph_update.md)（已归档 done/ · 状态行 CLOSED 回写）
> **类型**：仓级 chore（工具链升级 + 图谱档适配 · 零业务码改动）
> **关账日期**：2026-10-11 · 帽位：CLOSE（50 · 最小包 ②③ · 维护者令「开始」· 授权链 m00106 00 代录签收过程文档）

---

## 一 · 任务信息

| 项 | 值 |
|----|----|
| task_slug | `specwave-330-graph-update` |
| 立项性质 | **维护者直接下令的图谱维护作业 · 补录档**：维护者令（m00018 · 另一会话代际 ref · 原文照录）「新建任务分支，使用新版本specwave检查tech_graph并更新」开工 → 30 先行交付 → 维护者令（m00148 · 另一会话代际 ref · 原文照录）「补task」追补 task 档 · 闸态以 task 表 + 维护者令为准 |
| 背景 | 仓内锁定 spec-wave 3.0.1 → 升级 3.3.0；新版引入形状闸（3.2 W1：`nodes[].implementedBy` 须为 object 禁 array · `graph ib check` 点路径闸；3.3 新增 `graph ast check` opt-in · Python 仓无 TS peer 合规跳过；`graph drift` 默认期待 `01_struct.md`，本仓 stub 已于 commit `7938039` 有意删除、真值迁 `l1/01_modules.md`） |
| 目标 | 仓内 spec-wave 升级 3.3.0；全部图谱闸（yaml check / compile / ib check / drift）在 3.3.0 下绿；图谱档适配新形状闸且信息不丢失 |
| 分支 | `task/specwave-330-graph-update`（base = master） |
| 帽链 | 10-task（补录）→ 30（先行交付）→ PR #242 → CLOSE（本档） |

## 二 · 交付

| 环节 | 实证 |
|------|------|
| PR | [#242](https://github.com/Cyning12/ops-desk-api/pull/242) · **MERGED 2026-10-11T07:24:44Z · squash commit `92a8526`**（交付 commit `2029ac0`+`71341cc` · 17 档 +220/-383 · CI 绿） |
| 升级面 | `package.json`/`package-lock.json`：spec-wave 3.0.1 → 3.3.0（精确版本）· `.coding-kit/manifest.json`：`npx spec-wave upgrade --yes` 同步（prompts dry-run 11 skip · 0 add · 1 本地冲突 TASK_TEMPLATE.md 不覆盖） |
| 图谱适配 | **implementedBy 形状迁移**：6 个 flow graph.yaml 共 71 块由 list 迁为单 object；18 个多条目节点保留首条为主锚点，其余 50 条降级为 `# also: path#symbol (kind)` 注释保留信息（chat/lg_rag 全量映射真值仍在 `l2/indexes/` 手维档）· **过期锚点修复**：`10_flow_capability.graph.yaml` 引用不存在的 `app/ops/capability/adapters/langchain_tools.py` → 实际已迁 `app/ops/capability/extras/langchain.py`（`as_tool_node` L84 / `as_structured_tools` L69）· 节点 implementedBy 与边锚点均修正 |
| drift 闸配置 | 新增 `.spec-wave/graph-drift.yaml`，`struct_rel: l1/01_modules.md`（01_struct.md stub 已删 · 不重建） |
| 再生成 | graph-compile 再生成 md + `shared/graph.json` |
| invokes | `docs/harness/invokes/by-task/specwave_330_graph_update/`（10_task_draft 一件 · 补录档）· 本 CLOSE 补 50 于 `by-task/close_b2_and_specwave330/` |
| **CLOSE 增量** | task 档归档 done/（状态行 CLOSED + 修订记录 CLOSED 行）· active README 登记表补登 · **`docs/harness/legacy-gate-exempt.yaml` 扩列一枚**（slug `specwave-330-graph-update` · 归档后 verify 缺口处置 · 四字段齐 · 本 PR 即人审面）· 本档 + 50 invoke 落盘 |

## 三 · 核验结论（验收终态摘要 · G 组全绿实证）

30 交付验收（task 档验收节 + 自检结论 · 交付 commit `2029ac0` · 均亲跑重定向取 EXIT）：

| 验收项 | 命令 | 结果 |
|--------|------|------|
| G1 | `npx spec-wave graph yaml check --target . --all` | ✅ **9/9 OK · EXIT=0** |
| G2 | `./scripts/graph-compile.sh` | ✅ **OK**（md + graph.json 再生成 · 仅词表开放惯例 warning 不咬 exit） |
| G3 | `npx spec-wave graph ib check --target .` | ✅ **PASS**（checked=71 · issues=0） |
| G4 | `npx spec-wave graph drift --target .` | ✅ **PASS**（dirs=1 · anchors=194 · drifts=0 · struct_layout=protocol） |
| G5 | `npx spec-wave graph ast check --target .` | ✅ PASS（checked=0 skipped_ib=71 · 无 TS peer 合规跳过 · opt-in） |
| G6 | `npx spec-wave check --target .` | ✅ manifest 3.3.0 可升级提示消除（upgrade 后实证） |
| lint-wiki-delta | `npx --yes spec-wave task lint-wiki-delta --target .` | ✅ 通过（wiki_delta=n/a 恒绿口径 · 补录后复跑） |

30 自检钉死（task 档自检结论节照录）：G1-G5 全绿（数值均亲跑重定向取 EXIT）· implementedBy 迁移无信息丢失（50 条次锚点全部 `# also:` 注释留痕 · grep 可核）· ib check 检出的 missing_ib_path（langchain_tools.py → extras/langchain.py）已修正并复跑 PASS · `l1/01_modules.md` 与 `l2/indexes/` 零改动（模块表/indexes 真值不动）· 分支纪律：单 commit `2029ac0`（17 档 · +220/-383）。

**CLOSE 质量钉复跑（本帽 · 归档后仓态 · 重定向取真码）**：

- 改动前基线：`npx --yes spec-wave verify --target . > /tmp/verify_close_baseline.log 2>&1; echo EXIT=$?` → **EXIT=0 · VERIFY: PASS**（spec-wave 3.3.0 · 93 存量豁免命中留痕）。
- 归档后首跑：`npx --yes spec-wave verify --target . > /tmp/verify_close.log 2>&1; echo EXIT=$?` → **EXIT=2 · VERIFY: BLOCKED**（仓级 reviews 缺口 1：`docs/tasks/done/task_specwave_330_graph_update.md · missing R<n> review`）——**归档 done/ 后本 task 进入 verify 的 done 任务 reviews 扫描面，而本 task 无 R1 审查文（补录档口径）故缺口浮现**（active/ 期不入该扫描面 · 基线 EXIT=0 不矛盾）。
- 处置：**按豁免清单扩列纪律（`legacy-gate-exempt.yaml` 头注「扩列须四字段齐 + PR 人审」· 承 `task_specwave_verify_baseline` 失败路径表第 4 行）新增一枚豁免条目**（slug `specwave-330-graph-update` · reason 如实注记「维护者直令兜底 · 无 R1 审查文」· authorized_by `00（2026-10-11 维护者授权 m00267/m00106）` · 本 CLOSE PR 即人审面）——禁伪造审查（不补假 R1 档）· 豁免≠审查通过的诚实口径照承。
- 扩列后复跑：同一命令 → **EXIT=0 · VERIFY: PASS**（94 枚豁免命中留痕含本枚 · 0 invalid）。
- `npx --yes spec-wave task lint --file docs/tasks/done/task_specwave_330_graph_update.md` → **EXIT=0 · LINT: PASS**。

## 四 · 偏差与 nit（如实照登）

1. **无 R1 审查文 · 维护者直令兜底（如实照录）**：本 task 为维护者直接下令的图谱维护作业，30 先行交付、task 档补录（m00148）；双址（址A `docs/harness/reviews/` · 址B `docs/audits/task-review/`）均无 `specwave_330_graph_update` R1 审查文。task 档人工闸表 HG-AUDIT-R1 记「approved（2026-10-11 · 00 代录 · 维护者令 m00018/m00148）· 30 已交付且闸全绿；补录后由维护者 PR 审兜底」。本 CLOSE 照录此口径：**审查以维护者直令 + PR 审兜底为真值，无独立 R1 审查文**，故无址B 复制件落盘义务。**连带处置**：归档 done/ 后 verify 对本 task 报 `missing R<n> review`（done 任务入 reviews 扫描面）——已按扩列纪律在 `docs/harness/legacy-gate-exempt.yaml` 新增四字段豁免条目（reason 如实注记本口径 · 本 CLOSE PR 即人审面 · 禁伪造审查故不补假 R1 档），扩列后 verify EXIT=0 PASS（见 §三）。
2. **补录档帽链非标准**：帽链为 10-task（补录）→ 30（先行交付）→ PR（无独立 20 审查环节 · `review_hat=20` 注「补录档 · 20 书面审由本档自检结论替代 · 维护者令直签」）——补录档既有先例口径，照录。
3. **G-L1 图谱层改动 · HG-GRAPH-MODULES approved 按实判**：6 个 flow graph.yaml 形状迁移 + capability 锚点修正属 G-L1（md/json 随编译再生成）；`l1/01_modules.md` 模块表零改动（不新增/不撤销一级模块 · 不增 implementedBy 语义 · 仅形状迁移）· G-L2 indexes 不扩 —— 闸态表照录。
4. **词表 warning 非阻断不收**：compile 的 branches/triggers 词表 warning 为非阻断开放惯例（task 档非范围明示不收）· G2 OK 口径照录。
5. **迁移纪律留痕**：多条目 implementedBy 信息以「首条为锚 · 其余 `# also:` 注释留痕」降级保留（grep 可核 · 全量映射真值仍在 `l2/indexes/` 手维档）——信息不丢失实证已自检勾选。

### ⚠️ 遗留观察点（照录事实 · 禁擅改 · 待维护者确认）

**CI 钉版不一致**：本 task 已将 `package.json`/`package-lock.json` 钉 spec-wave **3.3.0** 且 `.coding-kit/manifest.json` 同步 3.3.0，但以下两处仍钉 **3.0.1**（本 CLOSE 照录事实，是否刻意待维护者确认，禁擅改）：

- `scripts/graph-compile.sh:28`：`GRAPH_CLI=${GRAPH_CLI:-spec-wave@3.0.1}`
- `.github/workflows/lint-wiki-delta.yml:35`：`npx --yes spec-wave@3.0.1`

影响面照录：本地/CI 的 graph-compile 与 lint-wiki-delta 闸实际跑在 3.0.1 上，与仓内 3.3.0 声明不一致；3.2 W1 形状闸（implementedBy object）与 3.3 ast check 在 3.0.1 下不存在，故两处钉 3.0.1 时不会拦形状闸缺口，亦不会产生升级提示 —— 若刻意保留需维护者明示理由，若遗漏建议后续统一升 3.3.0。

**verify-upstream 收口挂上游发版**：上游 issue #35 / PR #36 已提；`task_verify-upstream-dual-address` 仍 active（未收口 · 不在本 CLOSE 范围）。

## 五 · 签录（闸态表与审查文链）

| 闸 / 环节 | 状态 | 文档 / 实证 |
|-----------|------|------------|
| HG-TASK-DRAFT | **approved**（2026-10-11 · 00 代录） | 维护者令 m00148「补task」（另一会话代际 ref · 原文照录）· 补录档 · 维护者直令立项 |
| HG-AUDIT-R1 | **approved**（2026-10-11 · 00 代录） | 维护者令 m00018/m00148（另一会话代际 ref · 原文照录）· 30 已交付且闸全绿；补录后由维护者 PR 审兜底 · **无 R1 审查文（双址均无 · 照录）** |
| HG-GRAPH-MODULES | **approved**（2026-10-11 · 00 代录 · 按实判） | `l1/01_modules.md` 模块表零改动（仅形状迁移）· G-L2 indexes 不扩 |
| HG-PILOT-OPSDESK-GLAYER | n/a | 无外部试点面 |
| 20 R1 审查 | **无独立审查文 · 维护者直令兜底** | 补录档口径：20 书面审由 task 档自检结论替代 · 维护者令直签 + PR 审兜底 · verify 面以豁免清单扩列条目承接（四字段齐 · 本 PR 人审） |
| invokes | — | `by-task/specwave_330_graph_update/`（10_task_draft）· 50_close 落 `by-task/close_b2_and_specwave330/` |
| 合并 | **MERGED** | PR [#242](https://github.com/Cyning12/ops-desk-api/pull/242) · squash `92a8526f7f1fc052f8c932dd685cd3042a219781` · 2026-10-11T07:24:44Z · CI 绿 |

## 六 · 资源清理

- **本 CLOSE 不删任何东西**：分支 `task/specwave-330-graph-update`（本地/远端）与 `docs/close-b2-and-specwave330` **移交 00/维护者统一清理**——CLOSE PR 未合并前 close 分支在役；**CLOSE PR 合并后**：删除 task 分支（已 squash 合入 master `92a8526` · 删除安全 · 远端一并清）。
- 先例对照：各 CLOSE 均将 worktree/分支清理移交 00（active README 登记表在案）· 本件同口径。

## 七 · 维护者验收 checklist 与后续建议

### 维护者验收 checklist（00 代录 · 授权 m00106 · 需人重新验收项）

- [ ] **图谱闸全绿抽验**：master 上复跑 G1-G6（`npx spec-wave graph yaml check --target . --all` / `./scripts/graph-compile.sh` / `graph ib check` / `graph drift` / `graph ast check` / `check`）确认 9/9 OK · checked=71 issues=0 · anchors=194 drifts=0 · 升级提示消除 —— 复跑口径即验收标准节六条命令（仓内现钉 3.3.0 · 注意 `scripts/graph-compile.sh` 默认 GRAPH_CLI 仍 3.0.1，抽验时以 `GRAPH_CLI=spec-wave@3.3.0` 或 npx 直跑 3.3.0 为准）。
- [ ] **信息不丢失抽验**：6 个 flow graph.yaml 中 18 个多条目节点的 50 条次锚点以 `# also: path#symbol (kind)` 注释留痕（grep `# also:` 可核 · 全量映射真值仍在 `l2/indexes/`）。
- [ ] **过期锚点修复抽验**：`10_flow_capability.graph.yaml` 的 langchain 锚点指向 `app/ops/capability/extras/langchain.py`（`as_tool_node` / `as_structured_tools`）· `graph ib check` issues=0。
- [ ] **CI 钉版不一致观察点裁决**：`scripts/graph-compile.sh:28` 与 `.github/workflows/lint-wiki-delta.yml:35` 仍钉 3.0.1 是刻意或遗漏 —— 维护者确认后另案收口（本 CLOSE 照录未擅改）。
- [ ] **豁免清单扩列人审**：`docs/harness/legacy-gate-exempt.yaml` 新增 `specwave-330-graph-update` 一枚（归档后 verify `missing R<n> review` 缺口处置 · reason 如实注记「无 R1 审查文 · 维护者直令兜底」）—— 按扩列纪律须 PR 人审确认；若维护者裁定应补正式 R1 审查文，则撤本豁免条目、走 20 补审流程。

### 后续建议

1. **CI 钉版统一（待维护者裁决后另案）**：若确认为遗漏，另立小 task 将 `scripts/graph-compile.sh` 默认 GRAPH_CLI 与 `lint-wiki-delta.yml` npx 钉版统一升 3.3.0，与 `package.json` 对齐。
2. **verify-upstream 收口跟进**：上游 issue #35 / PR #36 发版后由 `task_verify-upstream-dual-address`（仍 active）收口双址切换。
3. **ast check 启用评估（可选）**：3.3 新增 `graph ast check` 当前因无 TS peer 合规跳过（checked=0 · opt-in）—— 若后续仓内引入 TS 面，评估启用以覆盖符号级锚点校验。

## 八 · 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-11 | CLOSE 落稿（50 close 棒 · worktree `t-close-b2-330` · 分支 `docs/close-b2-and-specwave330` · base master `92a8526`）：九节沿仓内先例（tool-catalog-page / hitl-approved-replan-quality CLOSE 文档）· 验收终态承 task 档 G 组全绿实证（30 亲跑重定向取 EXIT）· **无 R1 审查文 · 维护者直令兜底如实照录**（无址B 复制件义务）· 质量钉复跑（verify 改动前基线 EXIT=0 PASS → 归档后 EXIT=0 PASS · task lint done/ 档 PASS · spec-wave 3.3.0 · 重定向取真码）· CI 钉版不一致观察点入档（照录事实 · 待维护者确认刻意或遗漏 · 禁擅改）· verify-upstream 收口挂上游发版照登 · 维护者 checklist 00 代录（授权 m00106）· **归档后 verify 首跑 EXIT=2（missing R<n> review）→ 按扩列纪律新增豁免条目（四字段齐 · 本 PR 即人审面 · 禁伪造审查）→ 复跑 EXIT=0 PASS**（94 豁免命中含本枚） |

## 九 · 附录

### 关键路径

| 类别 | 路径 |
|------|------|
| task（已归档） | `docs/tasks/done/task_specwave_330_graph_update.md`（状态行 CLOSED） |
| 升级声明 | `package.json` · `package-lock.json` · `.coding-kit/manifest.json`（spec-wave 3.3.0） |
| 图谱适配 | `docs/_tech_graph/l1/` 6 个 flow `graph.yaml`（implementedBy 形状迁移 + capability 锚点修正）· `.spec-wave/graph-drift.yaml`（新增 · `struct_rel: l1/01_modules.md`）· `docs/_tech_graph/shared/graph.json` 与 md 再生成 |
| 钉版观察点 | `scripts/graph-compile.sh:28`（GRAPH_CLI 默认 3.0.1）· `.github/workflows/lint-wiki-delta.yml:35`（npx 钉 3.0.1） |
| 豁免清单 | `docs/harness/legacy-gate-exempt.yaml`（本 CLOSE 扩列 `specwave-330-graph-update` 一枚 · 四字段齐 · PR 人审面） |
| invokes | `docs/harness/invokes/by-task/specwave_330_graph_update/`（10_task_draft）· `by-task/close_b2_and_specwave330/`（50_close） |

### CLOSE 复跑命令留痕

```bash
npx --yes spec-wave verify --target . > /tmp/verify_close_baseline.log 2>&1; echo "EXIT=$?"   # 改动前基线 EXIT=0 · VERIFY: PASS
npx --yes spec-wave verify --target . > /tmp/verify_close.log 2>&1; echo "EXIT=$?"           # 归档后首跑 EXIT=2（missing R<n> review）→ 豁免清单扩列后复跑 EXIT=0 · VERIFY: PASS
npx --yes spec-wave task lint --file docs/tasks/done/task_specwave_330_graph_update.md       # EXIT=0 · LINT: PASS
```
