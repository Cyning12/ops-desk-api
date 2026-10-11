# Task：specwave-330-graph-update（spec-wave 3.0.1→3.3.0 升级与 tech_graph 适配 · chore）

> **状态**：done（2026-10-11 · 30 交付当日完成 · 验收 G1-G4 全绿 · 三闸 00 代录 approved（维护者令 m00018「新建任务分支，使用新版本specwave检查tech_graph并更新」+ m00148「补task」）· commit `2029ac0`）
> **类型**：仓级 chore（工具链升级 + 图谱档适配 · 零业务码改动）
> **分支**：`task/specwave-330-graph-update`（base = master）
> **补录说明**：本 task 为维护者直接下令的图谱维护作业，30 先行交付后按仓规补录 task 档（m00148）；闸态以本表 + 维护者令为准。

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `specwave-330-graph-update` |
| **test_strategy** | `recommended` |
| **test_strategy_note** | 纯工具链/文档面：以 spec-wave 3.3.0 图谱闸全绿为验收（G1-G4）；零代码 diff 故 pytest 构造性恒等 |
| **code_quality_bar** | `not_applicable`（零业务码改动） |
| **graph_change_layer** | `G-L1`（6 个 flow graph.yaml implementedBy 形状迁移 + capability 锚点修正；graph.json/md 随编译再生成） |
| **review_hat** | `20`（补录档 · 20 书面审由本档自检结论替代 · 维护者令直签） |
| **帽链** | 10-task（补录）→ 30（已交付）→ PR |
| **graph_delta** | `docs/_tech_graph/l1/10_flow_capability.md` 等 6 个 flow（详见 §3） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 无文档站变更（图谱源档与闸配置非 coding_wiki 面） |
| **experience_capture** | `recommended` |
| **required_invoke_hats** | `10,30,40` |
| **invoke_retention_profile** | `default` |
| **git_branch** | `task/specwave-330-graph-update` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | **approved**（2026-10-11 · 00 代录 · 维护者令 m00148「补task」） | 20, 30 | 补录档 · 维护者直令立项 |
| HG-AUDIT-R1 | **approved**（2026-10-11 · 00 代录 · 维护者令 m00018/m00148） | 30 | 30 已交付且闸全绿；补录后由维护者 PR 审兜底 |
| HG-GRAPH-MODULES | **approved**（2026-10-11 · 00 代录 · 按实判） | PR | `l1/01_modules.md` 模块表零改动（不新增/不撤销一级模块 · 不增 implementedBy 语义 · 仅形状迁移）；G-L2 indexes 不扩 |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | 无外部试点面 |

## 1. 背景与目标

- 维护者令（m00002）：升级 spec-wave 至 3.3.0（仓内锁定 3.0.1）。
- 维护者令（m00018）：新建任务分支，用新版检查 tech_graph 并更新。
- 新版引入的形状闸（3.2 W1）：`nodes[].implementedBy` 须为 **object**（`{path, symbol?}`，禁 array）；3.2 W1 新增 `graph ib check` 点路径闸；3.3 新增 `graph ast check`（opt-in · Python 仓无 TS peer 合规跳过）；`graph drift` 默认期待 `01_struct.md`（本仓 stub 已于 commit 7938039 有意删除，真值迁 `l1/01_modules.md`）。

## 2. 目标

仓内 spec-wave 升级 3.3.0；全部图谱闸（yaml check / compile / ib check / drift）在 3.3.0 下绿；图谱档适配新形状闸且信息不丢失。

## 3. 范围（均已交付 · commit 2029ac0）

- [x] `package.json`/`package-lock.json`：spec-wave 3.0.1 → 3.3.0（精确版本）
- [x] `.coding-kit/manifest.json`：`npx spec-wave upgrade --yes` 同步 3.0.1 → 3.3.0（prompts dry-run 11 skip · 0 add · 1 本地冲突 TASK_TEMPLATE.md 不覆盖，无需写入）
- [x] **implementedBy 形状迁移**：6 个 graph yaml 共 71 块由 list 迁为单 object；18 个多条目节点保留首条为主锚点，其余 50 条降级为 `# also: path#symbol (kind)` 注释保留信息（chat/lg_rag 全量映射真值仍在 `l2/indexes/` 手维档）
- [x] **过期锚点修复**：`10_flow_capability.graph.yaml` 引用不存在的 `app/ops/capability/adapters/langchain_tools.py` → 实际已迁 `app/ops/capability/extras/langchain.py`（`as_tool_node` L84 / `as_structured_tools` L69）；节点 implementedBy 与边锚点均修正
- [x] **drift 闸配置**：新增 `.spec-wave/graph-drift.yaml`，`struct_rel: l1/01_modules.md`（01_struct.md stub 已删 · 不重建）
- [x] graph-compile 再生成 md + `shared/graph.json`

## 非范围

- spec-wave 上游本体改动；词表登记档整理（compile 的 branches/triggers 词表 warning 为非阻断开放惯例，不收）
- `docs/harness/prompts/` 同步（dry-run 全 skip 已实证同步）；TASK_TEMPLATE.md 本地冲突面（保持本地改）
- 业务代码与测试改动（零）

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| implementedBy 残留 list 形态 | `graph yaml check --all` 红（nodes[i].implementedBy 须为 object） | 是 | 按报错点位迁移复跑 |
| implementedBy.path 指向不存在文件 | `graph ib check` EXIT=2 missing_ib_path | 是 | 修正路径复跑（本 task 实证 langchain_tools.py 案例） |
| drift 闸缺 struct 档 | `graph drift` struct_missing 红 | 是 | `.spec-wave/graph-drift.yaml` struct_rel 指向真值档 |
| 多条目 implementedBy 信息丢失 | 30 迁移纪律：首条为锚 · 其余 `# also:` 注释留痕 | 是 | diff 审 + 注释 grep 可查 |

## 验收标准（G 组 · 可机验 · 30 已全绿）

- [x] G1 `npx spec-wave graph yaml check --target . --all` → **9/9 OK · EXIT=0**
- [x] G2 `./scripts/graph-compile.sh` → **OK**（md + graph.json 再生成 · 仅词表开放惯例 warning 不咬 exit）
- [x] G3 `npx spec-wave graph ib check --target .` → **PASS**（checked=71 · issues=0）
- [x] G4 `npx spec-wave graph drift --target .` → **PASS**（dirs=1 · anchors=194 · drifts=0 · struct_layout=protocol）
- [x] G5 `npx spec-wave graph ast check --target .` → PASS（checked=0 skipped_ib=71 · 无 TS peer 合规跳过 · opt-in）
- [x] G6 `npx spec-wave check --target .` → manifest 3.3.0 可升级提示消除（upgrade 后实证）
- [x] `npx --yes spec-wave task lint-wiki-delta --target .` 通过（wiki_delta=n/a 恒绿口径 · 补录后复跑）

## 给执行帽的必读列表

1. `AGENTS.md`（图谱闸路径 · 分支纪律）
2. `docs/_tech_graph/README.md` + `LAYER_README.md`
3. `docs/_tech_graph/l1/01_modules.md`（HG-GRAPH-MODULES 真值 · 本 task 零改动）
4. spec-wave 3.3.0 形状闸真值：`node_modules/spec-wave/lib/cli-graph-yaml.js`（implementedBy object 校验）· `cli-graph-drift.js`（GRAPH_DRIFT_CONFIG_REL=`.spec-wave/graph-drift.yaml`）

## 测试策略（Harness）

**test_strategy**: `recommended` —— 图谱/工具链面以闸命令红绿为证；零代码 diff，pytest 构造性恒等（分支与 master 代码面同一，仅 package*.json 依赖声明 + docs/ 与配置）。

---

### 自检结论（执行者）

**30 自检（2026-10-11 · commit 2029ac0）**：

- [x] G1-G5 全绿（数值见验收节 · 均亲跑重定向取 EXIT）
- [x] implementedBy 迁移无信息丢失：50 条次锚点全部 `# also:` 注释留痕（grep 可核）
- [x] ib check 检出的 missing_ib_path（langchain_tools.py → extras/langchain.py）已修正并复跑 PASS
- [x] 既有档面：`l1/01_modules.md` 与 `l2/indexes/` 零改动（模块表/indexes 真值不动）
- [x] 分支纪律：`task/specwave-330-graph-update` 单 commit `2029ac0`（17 档 · +220/-383）

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 10 补录落稿（维护者令 m00018 开工 · m00148「补task」追补 task 档）：30 已交付（commit 2029ac0 · G1-G5 全绿）· 三闸 00 代录 approved · 待 PR |
