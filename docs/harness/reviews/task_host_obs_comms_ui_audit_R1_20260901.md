# Task Audit R1：host-obs-comms-ui（C4 · task + 契约 obs-comms-v0）

> **hat_id**：20-task-audit  
> **task**：`docs/tasks/active/task_host_obs_comms_ui.md`（C4 末波 · **api 无码 · docs-only**：契约 `obs-comms-v0` + web Prompt 落盘 `_prompts/`；web Vue 实现另 task）  
> **契约**：`docs/spec/agent-infra/host_comms_obs_contract_v0.md`（契约 id `obs-comms-v0` · draft · 文档级 · 未实现不冻结行为）  
> **上游 SPEC**：`docs/spec/agent-infra/06_host_comms_boundary_spec_v0.md`（**signed** · #111）§4（意图路由）· §6（闸纪律）· §9（session 隔离）· §10（C4 行）· §11（/obs 主入口钉）  
> **先例**：`docs/harness/reviews/task_host_comms_task_writer_audit_R1_20260901.md`（C3 · 同款 W4 豁免 · 同款 00 代签流程）；C1/C2 审查文同目录  
> **跨仓对照（只读）**：`ops-desk-web/src/api/obs.ts` + `src/fixtures/obs/*.json` 四份 fixture（2026-09-01 快照 · 本帽未改 web 仓任何字节）  
> **日期**：2026-09-01 · 审查人：20-task-audit · 分支 `task/host-obs-comms-ui`（未切换 · 未 push）  
> **lint 复跑**：`dsh-coding-kit@1.10.0 task lint` → **PASS（exit 0 · W4 warn 合法豁免）**；`lint-wiki-delta --target .` → **PASS（exit 0 · scanned 103 · issues 0）** —— 均本帽独立复跑核实，非转述 10 自检

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **pass** · 零阻塞 · 不退回 10 · **无「必须退回 00 改钉」级问题**（00 定夺七项全部忠实落入 task/契约；契约字段表与 web 类型逐字段核对仅 1 处已声明偏离且理由成立） |
| **流程闸** | `HG-AUDIT-R1` = **n/a**（本波 **无 30** · api 无码 —— 与 C0 SPEC 波同款处置，合法）；`HG-TASK-DRAFT` approved（00 代签 · 维护者 Prompt 授权留痕）；`HG-GRAPH-MODULES` n/a（graph_change_layer=none） |
| **30 授权** | **本波无 30 可签** · 本帽不签发任何闸；pass 后由 **00 收口 CLOSE**（close_pr_policy=required · kpi_aggregator=CLOSE） |

---

## 审查核对（对照 SPEC 06 §4/§6/§9/§10/§11 · web obs.ts + 四 fixture 只读核实）

| 审查点 | 结论 |
|--------|------|
| 契约 §2 ObsStatus 字段表 ↔ web `ObsStatus` 逐字段一致 | **一致**。web obs.ts L12–26 共 **13 个顶层字段**：`schema_version/task_slug/task_path/status/gates/may_start_30/blockers/last_invoke/reviews/verify_preview/hgm/kpi_section/next_hint` —— 契约 §2 字段表逐行命中：字段名 ✅ · 类型 ✅ · 可空性 ✅（`last_invoke.path/hat_id` string\|null · `hgm.event_count` number\|null · `hgm.last_at` string\|null 均与 web 逐字一致）· 嵌套 `ObsGate`（id/status/blocks_hats 全 string）✅。`schema_version` 契约钉字面 `"obs_status.v1"`、web 类型为 string —— 语义收窄非类型冲突，fixture 实值即为该字面 ✅ |
| 契约 §3 ObsTimeline 字段表 ↔ web `ObsTimeline` 逐字段一致 | **一致**。web 9 个顶层字段（`schema_version/task_slug/task_path/event_count/returned/limit/ingested/ingest/events`）与契约 §3 逐行命中：`limit` number\|null ✅ · `ingested` boolean ✅ · `events` 6 子字段（`event_id?/type/occurred_at/subject?/summary?/data?`）可选性与契约「必填」列逐项一致 ✅（`data?` web `Record<string, unknown>` ↔ 契约「object」为 JSON 契约文档常规表述，不歧义） |
| 唯一偏离 `ObsTimeline.ingest`：web `unknown` → 契约 `object\|null` —— 理由是否成立 | **成立**。① 方向正确：`unknown` 是 TS 顶层类型（任意值的超集），fixture 期占位宽类型在契约首版收敛为可文档化的 `object\|null`，是契约先行的标准做法；② 「web 兼容零改动」结论 **正确**：生产方产出 `object\|null` 对消费方 `unknown` 字段天然可赋值，运行时与类型层均无破坏；四份 fixture 实值 `ingest: null` 与契约相容（现网核实 timeline_empty/timeline_events 均为 null）；③ 契约 §4 已给 web 切换波的顺手收窄路径（`Record<string, unknown>\|null` · 类型层收紧 · 运行时无破坏），不预加本波义务。偏离计数「仅 1 处」经本帽独立逐字段复核属实 |
| 契约 §5 示例 JSON ↔ web fixture | **同形属实**（实为逐字段同值）：§5.1 ready ↔ `status_ready.json`、§5.2 blocked ↔ `status_blocked.json` 字段/取值/闸序逐项相同（含 `verify_preview.reason` 的「30 前仍须正式跑」提示 · `blockers: ["HG-AUDIT-R1=pending"]` 形态）。timeline 示例指向 web fixture 并注明「真源波在本契约补正式示例」——可接受（见非阻塞 3） |
| 数据源决策点 A/B：A 的部署容器无 docs/ 风险是否写明 · 「本波不选定」是否明确 | **写明且无暧昧**。契约 §6 风险行：方案 A「**部署容器无 `docs/`**：生产镜像只带 `app/`，仓内 docs 不在容器内 → 端点无数据源」，并给三条解法（镜像打包 docs/ 只读副本 · 挂载卷 · 改读 git 仓 API）；方案 B 风险（新表 + Alembic + GHA 维护 · sync 陈旧须暴露 `synced_at`）对等写明。「不选定」三处钉死：节标题「本波 **不选定**」+ L141 钉死行「真源实现 task 开工第一棒由 00 拍板并回填本节」+ task L52 00 定夺原文 —— 标题/正文/任务三层一致，回填义务落实到具体帽（00）与具体时点（真源 task 第一棒），防暧昧成立。failure_paths（task 表 + 契约 §9）均有对应行 |
| 发起沟通语义 ↔ SPEC §4/§6/§9 | **逐项一致**。契约 §7：① 显式发起（按钮/结构化 UI 入口 = §4 显式意图信号 ·「无显式点击不进 comms · 默认 product 原则不变」= §4 默认 product 钉）✅；② 分 session（C2 `pack=comms` · `session_scope="comms"` · 与 product 分 thread · 互不注入历史 = §9 逐字落地）✅；③ 人确认（C3 writer dry-run diff 预览 → 人显式确认 → `apply_task_write(confirmed=True)` · 未确认零落盘 = §6 C3 前置 + §13 failure_paths 行的服务层等价物，与 C3 已 CLOSE 实现咬合）✅；④ 禁代签（「已签收/approved/**已代签**」字样违规 · 可输出「待人签」· 闸真值 SoT 在 task 表 · UI 只读投影 = §6 闸纪律逐字落地）✅；⑤ 浏览器禁 npx（status/timeline 只经 api 端点或 fixture · `verify_preview` 仅只读预览 = §3 永久禁令 A + §7 白名单 + §8 Skills≠verify 的 UI 侧投影）✅ |
| 依赖注记：`harness.status` C1 留白 · 真源实现另 task | **属实且处置正确**。契约 §8「C1 留白（SPEC 06 §7 可选 · C1 自检显式注明不做）· 真源实现波需要时补做 · 白名单三条已含 `harness.status` 不触发 §7 白名单变更 · Policy 默认关沿用 · 数据源选 B 时可能不需要」—— 现网核实 C1 done 文件（`docs/tasks/done/task_host_harness_cli_capability.md` L93「不做 · C4 开工时补 · 自检结论显式注明」· L176 ④ · L199 修订记录）逐字属实；SPEC §7 白名单第三行 `harness.status`（可选 · 默认关）确实**已含**该条，补做不构成白名单新增，契约判断正确。「真源 status/timeline 端点另 task」在 task 非范围 L69 与契约 §1/§8 三处互钩 |
| web Prompt 红线齐全 · fixture→真源切换点可执行 | **齐全且可执行**。现网核实 `docs/harness/invokes/by-task/_prompts/PROMPT_web_00_c4_obs_comms_ui.md`：红线四条 —— 浏览器禁 npx/CLI（L28）· 禁代签（L29）· 人确认（L30 ·「UI 不提供跳过确认路径」）· 分 session（L31 · 误判回退 product）—— 覆盖 task 验收条 3 要求的三条并多禁代签一条。切换点具体可执行：`ObsDataSource` 抽象 + 单一开关 `VITE_OBS_SOURCE=fixture\|api` + fixture 保留默认/fallback（真源未上线不拨开关）+ DevTools Network 零 api 请求联调钩；端点形态以契约为准并附 `ingest` 收窄提示。过渡形态（comms 接线未完成时提示文案/禁用态 · 不得静默混进 product）防越界，与 SPEC §4 误判处理条款同向 |
| task 验收可判定性 | **六条全部可判定**：① 契约章节齐全（章节清单列明）✅ 已满足；② 逐字段核对 + 偏离写明 ✅ 已满足（本帽独立复核）；③ Prompt 落盘含三条红线 ✅ 已满足；④ 20 R1 审查文 pass —— 即本文；⑤ `app/` · `tests/` 零改动 —— 本帽 `git diff master --stat -- app tests` 复跑 **输出为空** 核实；⑥ `lint-wiki-delta` PASS —— 本帽复跑 exit 0。test_strategy=`n/a` + test_strategy_note「验收=契约章节齐全 + 20 R1 pass + web Prompt 落盘」与 docs-only 形态自洽 |
| api 无码形态与串行纪律（C 轨末波）| **一致**。orchestration「C1 ✓ → C2 ✓ → C3 ✓ → C4」与 git log 现网核实咬合（#114 C1 · #116 C2 · #118 C3 · #119 C3 归档）；SPEC §10 顺序钉「C1→C2→C3 串行 · C4 可与 C3 尾并行仅 web 侧」—— 本波 C3 已 CLOSE 后开工，api 侧交付物为契约+Prompt（非 web 实现），不触碰「仅 web 侧」并行例外，纪律无违。C4 行「/obs：fixture → 真 status + 发起沟通入口」由本契约（真 status 契约面）+ web Prompt（入口 UI 面）两件覆盖，web 实现另 task 的分工与 §10「web task（跨仓）」一致。SPEC §11 /obs 主入口建议钉已随签收生效，本波正是其落地 |
| W4 豁免合法 | **合法**。task 无思考轮节；W4 warn 原文允许「SPEC 承载 / bugfix 轨合法豁免」；SPEC 06 §15 R0–R5 回填完整（R2 方案对比 · R3 边界 · R5 移交），本 task 是 signed SPEC 的执行落地波，与 C1/C2/C3 三先例同款处理；本帽复跑 lint 核实 W4 为 warn 非 fail |
| 人工闸表与 invoke 留档 | **合规**。required_invoke_hats=`10,00` —— 两 invoke 现网核实俱在（`invoke_20260901_00_*` · `invoke_20260901_10_task_*`）；HG-TASK-DRAFT approved（00 代签 · 维护者 Prompt 授权 · blocks 栏 `22-R1` 为全仓统一遗留帽号命名，C1–C3 及历史 task 同款，C3 审查文已认定不影响闸语义）；HG-AUDIT-R1=`n/a` 与「本波无 30」自洽（同 C0 SPEC 波处置）；HG-GRAPH-MODULES=`n/a` 与 graph_change_layer=`none` 一致；闸表状态本帽未改、亦无人要求改 |
| 行为变更类 task「旧测 grep 影响面」（K7 checklist） | **N/A**。docs-only 契约波 · `app/`/`tests/` 零 diff（已核实）· 不改任何默认值/校验/fallback 语义，K7 提醒不触发 |
| freeze / 图谱 / wiki 元信息 | **合法**。freeze_id=`n/a` 与 SPEC §16「C1 起新契约由对应实现 task 定义 freeze，不在 SPEC 预冻」对齐；契约头部自标「文档级契约 · 未实现不冻结行为」—— obs-comms-v0 作为文档级契约不冻结行为，真源 task 再定 freeze，无偷渡。graph_delta=`none` + note「真源实现波再同步」合理（docs-only 不动图谱）；wiki_delta=`n/a` 有 lint-wiki-delta 机械闸兜底；`lint-wiki-delta` 同时是范围条 4 与验收条 6，双钩一致 |

其余可执行性：`close_pr_policy=required` · `kpi_aggregator=CLOSE` 与「pass 即 00 收口 CLOSE」路径匹配；必读列表四项现网全部存在（本 task · SPEC 06 §4/§6/§9/§10/§11 · web obs.ts · C1–C3 done 文件 —— 本帽逐一核实）。

---

## 阻塞

无。

---

## 非阻塞风险（不退回 10 · 00/真源波知情即可）

1. **字段计数措辞小差**：契约 §4 结论行与 task 自检称「ObsStatus **14** 字段（含嵌套）」，web obs.ts 顶层字段实为 **13** 个（含嵌套子字段全展为 24 行）；字段表**本体**逐字段一致（本帽逐项复核），仅计数措辞偏差。建议下次文档触及（真源波回填契约时）顺手改为 13 或写明口径；不构成退回。
2. **SPEC §10 C4 行依赖列「C1 status」与 C1 status 可选未做的落差**：契约 §8 已正确处置（留白注记 + 选 B 可能不需要），本契约波不受阻；但**真源 task 开工第一棒 00 拍板 A/B 时须一并拍板 `harness.status` 补做与否**（契约 §6 已钉回填义务，此处仅提请注意两处决策在同一棒）。
3. **timeline 正式示例欠奉**：契约 §5 仅 status 两示例，timeline 指向 web fixture 并自注「真源波在本契约补正式示例」—— fixture 四份现网核实与契约字段表相容，本波可接受；真源波回填时勿忘补（含 `events[].data` 非空用例）。
4. **`verify_preview` 定位靠文案自律**：示例 `reason` 含「非正式 verify · 30 前仍须正式跑」、Prompt 红线与契约 §7 均钉「只读预览」——三处一致、无机械挡需求（UI 只读投影 · 正式 verify 在 api/CLI 侧），与 SPEC §8 分工自洽；实现期保持即可。

---

## 回填清单

无（内容零阻塞 · 不改 task/契约实质 · **不改**人工闸表 status）。

---

## 签收

**内容签收 · pass**（终轮 R1）。流程闸 `HG-AUDIT-R1` = **n/a**（本波无 30 · 本帽不签发任何闸）—— 按 C 轨末波约定，pass 后交 **00 收口 CLOSE**（归档 task 至 `docs/tasks/done/` · PR 合并走 `close_pr_policy=required`）；web 侧实现由 `_prompts/PROMPT_web_00_c4_obs_comms_ui.md` 派 web 00 另起 task（跨仓 · 不阻塞本波 CLOSE）。

---

## 00 收口清单（20 后 · CLOSE 前 · 非 30 Prompt）

- [ ] 已读 R1 审查结论（pass · 零阻塞 · 非阻塞 4 条知情）
- [ ] 归档 task 至 `docs/tasks/done/` 并补 CLOSE 记录（kpi_aggregator=CLOSE）
- [ ] PR 合并（`close_pr_policy=required` · CI 绿）
- [ ] web 实现另 task 时以 `_prompts/PROMPT_web_00_c4_obs_comms_ui.md` 派 web 00
- [ ] 真源 task 立项时 00 第一棒拍板：数据源 A/B（回填契约 §6）+ `harness.status` 补做与否（非阻塞 2）
