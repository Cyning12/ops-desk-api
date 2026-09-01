# Task Audit R1：host-comms-task-writer

> **hat_id**：20-task-audit  
> **task**：`docs/tasks/active/task_host_comms_task_writer.md`（C3 · 受控 task 写盘：`app/ops/capability/task_writer.py` 纯服务 `plan_task_write`/`apply_task_write` · allowlist 三目录 · dry-run 默认 · 人确认落盘 · 禁代签机械挡 · 无 HTTP 路由 · 不进 Gateway registry）  
> **上游 SPEC**：`docs/spec/agent-infra/06_host_comms_boundary_spec_v0.md`（**signed**）§5（产物路径 allowlist）· §6（闸纪律 · C3 前置人确认 · 禁代签）· §7（白名单仅三条）· §10（C3 行）· §15（思考轮承载）  
> **先例**：`docs/harness/reviews/task_host_comms_prompt_pack_audit_R1_20260901.md`（C2 · 同款 W4 豁免 · 同款「00 代签待 R1 落盘」流程）；`docs/harness/reviews/task_host_harness_cli_capability_audit_R1_20260901.md`（C1）  
> **日期**：2026-09-01 · 审查人：20-task-audit · 分支 `task/host-comms-task-writer`（未切换 · 未 push）  
> **10 lint**：PASS（W4 无思考轮节 · SPEC 06 §15 承载合法）· 本帽复跑 `dsh-coding-kit@1.10.0 task lint` → **PASS（exit 0 · W4 warn）** 核实

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **pass** · 零阻塞 · 不退回 10 · **无「必须退回 00 改钉」级问题**（写盘层无可绕过禁代签挡 / allowlist 的已定路径） |
| **流程闸** | `HG-AUDIT-R1` **仍 pending**（正确 · 20 不代签）· `HG-TASK-DRAFT` / `HG-GRAPH-MODULES` 已 approved（00 代签 · 维护者 Prompt 授权留痕） |
| **30 授权** | **未签发** · pending 时禁止附 30 Prompt；真值仍在 task 人工闸表；**可交 00 代签 HG-AUDIT-R1** |

---

## 审查核对（对照 SPEC 06 §5/§6/§7/§10/§15 · 现网代码只读核实）

| 审查点 | 结论 |
|--------|------|
| allowlist 与 SPEC §5/§10 C3 行逐字一致 | **一致 · 不退回 00**。00 定夺 allowlist 行 = `docs/tasks/active/` · `docs/tasks/draft/`（不存在可创建）· `docs/harness/invokes/by-task/<slug>/` —— §5「**仅** `docs/tasks/`（active/draft）+ invoke 草稿（`docs/harness/invokes/by-task/`）」的逐字落地，`<slug>` 子路径为收窄不冲突；§10 C3 行「allowlist 仅 `docs/tasks/active|draft` + invoke 草稿」同。禁写面三层钉死：00 定夺「其佘一律拒绝（`app/` 永久 · `tests/` · 图谱 yaml · SPEC 正文 · 任意逃逸）」+ 非范围「改 SPEC 正文 / 图谱 yaml / `app/` 业务码 的写盘能力（永久禁写）」+ 验收条 1「`app/`/`tests/`/SPEC/图谱/逃逸路径（`../` · 绝对路径）全部拒绝（参数化断言）」——与 §5 禁写行（`app/` 永久 · `tests/` · 图谱 yaml · SPEC 正文）逐项对齐。现网核实：`docs/tasks/draft/` 确实不存在（`docs/tasks/` 仅 `_views/active/deferred/done/` + `PRIORITY_DEFERRED.md`），「不存在可创建」陈述属实 |
| 禁代签机械挡与 SPEC §6 一致且可判定 | **一致 · 可判定**。00 定夺钉「content 含人工闸节且把 `HG-*` status 写为 `approved`（非模板占位）→ 拒绝写入（`invalid_content`）」——与 §6 禁代签行「输出现『已签收 / approved / 已代签』字样 → 违规」+ §3 永久禁令 B（模型永不签发 human_gate）同向；闸真值在 task 表（§6「SoT 在 task 表 · 非 invoke 字面」）使挡聚焦人工闸节、不误伤 invoke 过程留痕。验收条 4「content 人工闸节含 `HG-...` `approved` → `invalid_content` 拒绝（断言）」机械可判。结构自检（缺人工闸节 → 拒绝）封死「写无闸节 task 携带 approved 字样」的侧路。「非模板占位」判定规则 task 未展开 → 见非阻塞 1（宁严勿宽方向已够 30 落地，不构成阻塞） |
| dry-run 默认 / confirmed 语义 / 原子写 / overwrite 可验收性 | **可验收**。验收条 2（`confirmed=False` → WritePlan + diff 预览且目标文件不存在）· 条 3（`confirmed=True` → 落盘且内容一致）· 条 7（已存在未显式 overwrite → 拒绝 · diff 含差异）· 条 8/9（原子写不留半截 · mkdir parents 仅 allowlist 内）全部 tmp_path 沙箱可断言，与 test_strategy_note 一致。§6 C3 前置「落盘前必须人确认（dry-run diff + 显式 yes）」在服务层的等价物即 `confirmed: bool = False` 默认 + 显式 True；「人确认」的 UI/接线绑定属 C4/Host（00 定夺钉「无 HTTP 路由 · 接线留 C4/Host」），本波不越界、与 §10 C3 行「dry-run 默认 · 人确认落盘」语义一致 |
| 落点 capability 包纯服务不进 registry —— 是否规避 §7 白名单 / 语义偷渡 | **无规避 · 无偷渡**。§10 C3 行本身授权「受控写盘」实现波，C3 与 §7（Gateway Capability 白名单 · 仅 `harness.*` 三条 · 新增须 SPEC 修订）是两个平面：不进 registry/manifest 即非 Gateway Capability，§7 白名单零变更属实。验收条 8「grep/AST 断言 `task_writer` 未被 register · SPEC §7 白名单零变更」机械钩住；非范围钉「Gateway 注册新 capability（SPEC §7 白名单仅三条 · 新增须 SPEC 修订）」封死后续偷渡路径。现网核实：`01_modules.md` L26 `capability` 行 path glob = `app/ops/capability/**` 覆盖落点；包内 `gateway.py/registry.py/manifest.py/policy.py/harness_cli.py` 等俱在，C1 参照 `harness_cli.py` 存在——落既有包既有 glob，**不新增一级模块**成立。「若 20 认为须新增一级模块 → 退回 00」条款：本帽判定**不需要**（纯服务 · 既有 glob · HG-GRAPH-MODULES 已 approved「落 capability 行」），条款被尊重、未触发 |
| 10 补充两钩（原子写断言 · draft/ mkdir parents 仅 allowlist 内）是否越权 | **不越权**。两钩均为已钉行为的可检验化：原子写 ← failure_paths 行 6「写盘 IO 失败 · 不留半截文件（先写临时文件再 rename）」；mkdir parents ← 00 定夺 allowlist 行「`docs/tasks/draft/`（不存在可创建）」；「非 allowlist 目录一律不创建」为 allowlist 语义的安全性质补强（防 mkdir 副作用越界）。范围/非范围/00 定夺实质零改动（10 自检如实声明），符合 10-task 帽权限 |
| failure_paths 完备性 | **基本完备**（六行）：路径越 allowlist → `path_not_allowed` ✓（§5）；未人确认 → dry-run 不落盘 ✓（§6 C3 前置 + §13「C3 写盘未经人确认 → 不落盘」对齐）；禁代签内容 → `invalid_content` ✓（§6/§3 禁令 B）；结构自检失败 → `invalid_structure` 指出缺节 ✓；目标已存在未 overwrite → `exists` ✓；写盘 IO 失败 → 上抛不留半截 ✓。覆盖 SPEC §13 中 C3 相关行并补齐实现侧。唯一缺口：文件名/slug 非法 · kind/目录错配拒绝（验收条 6 有钩）无独立 failure_paths 行 → 非阻塞 4，与 `path_not_allowed`/`invalid_content` 同形态可归并 |
| 写盘层绕过路径专项（重点风险波） | **无「必须退回 00 改钉」级问题**。逐项排查：① allowlist 逃逸（`../` · 绝对路径）由验收条 1 参数化断言钩住；② 禁代签挡对**所有** content 生效（含 `overwrite=True` 重写已有 task 的场景——挡在内容层不在路径层，重写注入 approved 同样被拒）；③ 「无人工闸节的 task 携带 approved」被结构自检（缺节 → 拒绝）封死；④ 非范围钉死「删文件 / 移动文件 · 写 docs/tasks/done/」，写盘器不能借归档越权；⑤ 无 HTTP 路由 + 不进 Gateway → 模型无可直达写盘的注册通道，调用方仅限仓内代码。两处实现期加固建议见非阻塞 2/3（apply 复核 plan · realpath 判定），均不构成本轮阻塞 |
| graph_delta / wiki_delta / W4 豁免 | **全部合法**。graph_delta = `01_modules.md` capability 行备注 · graph_change_layer=`G-L1` · 「若增 `implementedBy` → 同步 G-L2 indexes」为条件钩不预加义务——与 C1 先例同款（L74 HG-GRAPH-MODULES 留痕「capability 行备注 · 不新增一级模块」可对照）；HG-GRAPH-MODULES=approved（00 代签）成立。wiki_delta=`n/a` 合理（行为真值在 SPEC 06 §5/§6 + 本 task · 不晋升 coding_wiki · 验收条 12 `lint-wiki-delta` 钩在）。W4：本帽复跑 `task lint` → PASS · W4 warn「无思考轮节（SPEC 承载合法豁免）」；SPEC 06 §15 R0–R5 回填完整（R3 已覆盖「写盘 allowlist 收窄 · 代签为永久禁令」——本 task 验收条即 SPEC 思考轮的执行层落地）；与 C1/C2 先例同款处理 |
| 人工闸表与 invoke 留档 | **合规**。required_invoke_hats=`10,00,30`；00/10 invoke 已落盘 `docs/harness/invokes/by-task/host-comms-task-writer/`（两文件 glob 核实 ✓）；HG-TASK-DRAFT approved（00 代签 · 维护者 Prompt 授权 · 2026-09-01 · blocks 栏 `22-R1` 为全仓统一遗留帽号命名，C1/C2 及历史 task 同款，不影响闸语义）· HG-GRAPH-MODULES approved · HG-AUDIT-R1=pending 待本审查落盘后 00 代签——符合 §6「00 代签 ≠ 模型自签」区分；§3 永久禁令 B 未被触碰（本帽亦不签发） |
| 行为变更类 task「旧测 grep 影响面」（K7 checklist） | **已钩 · 本 task 纯新增**。唯一新文件 `task_writer.py` + 新测试，不改既有默认值/校验/fallback 语义；验收条 8「不进 registry/manifest · §7 白名单零变更」+ 非范围「改 `app/` 业务码（永久禁写）」已覆盖影响面；验收条 11 ruff/pytest/graph-compile 全绿为兜底 |
| 前置依赖与波次纪律 | **属实**。C1 `task_host_harness_cli_capability`（#114）· C2 `task_host_comms_prompt_pack`（#116）均在 `docs/tasks/done/`（现网核实 ✓）；orchestration「C0 ✓ → C1 ✓ → C2 ✓ → C3 串行 · C4 仅 web 侧可并行」与 §10 顺序钉逐字一致；必读列表引用（SPEC 06 · `harness_cli.py` · `packs.py` · L2 规范 · `01_modules.md`）现网全部存在（10 自检六项核对本帽复核属实） |

其余可执行性：验收含 ruff/pytest/graph-compile/lint-wiki-delta 全绿钩；`close_pr_policy=required`、`kpi_aggregator=CLOSE`；freeze_id=`n/a` 与 SPEC §16「C1 起新契约由对应实现 task 定义 freeze，不在 SPEC 预冻」对齐（WritePlan/错误码契约由 30 自检记录即可）。

---

## 阻塞

无。

---

## 非阻塞风险（不退回 10 · 30 知情即可）

1. **「非模板占位」判定规则未展开**：00 定夺禁代签挡含「（非模板占位）」限定但未定义占位形态，验收条 4 按「人工闸节含 `HG-*` `approved` → 拒绝」直断言。建议 30 按**宁严勿宽**实现：人工闸节内任何 `HG-*` 行 status=`approved` 一律拒绝（00 代签走人工授权流程直接改 task 表、**不经** comms 写盘，故严挡不误伤合法流程）；若确需占位例外，须在 30 自检记录钉死判定规则与用例。
2. **`apply_task_write` 对 plan 的信任边界未钉**：若 `WritePlan` 可被调用方手工构造，理论上可绕过 `plan_task_write` 的 allowlist/禁代签校验直调 apply。建议 30 二选一并在自检记录写明：apply 内复跑校验（allowlist + 禁代签 + overwrite + 结构自检），或使 `WritePlan` 不可外部伪造（仅 `plan_task_write` 内部构造 · 携带校验完成标记）。本波无 HTTP 路由 · 不进 Gateway，调用方仅限仓内代码，故非阻塞。
3. **symlink/realpath 逃逸未明示**：验收条 1 钩住 `../` 与绝对路径字面；建议 30 以 `resolve()` 后的 real path 前缀判定 allowlist（防 `docs/tasks/active/` 内符号链接指向 `app/` 等逃逸），tmp_path 测试可补软链用例。
4. **文件名/kind 错配拒绝无独立 failure_paths 行**：验收条 6 已钩行为（拒绝）；failure_paths 未单列，30 可按 `path_not_allowed`/`invalid_content` 同形态校验错误处理，或在 30 自检记录补注错误码归类，不退回。
5. **`docs/tasks/draft/` 为本仓新增任务态目录**：现网 `docs/tasks/` 仅 `_views/active/deferred/done/`，`draft/` 系 SPEC §5 钉死目录但本仓流程尚未使用；mkdir parents 创建不影响既有流程，30 注意仅在 kind 与目录匹配时创建（验收条 6/9 已钩）。

---

## 回填清单

无（内容零阻塞 · 不改 task 实质 · **不改**人工闸表 status）。

---

## 签收

**内容签收 · pass**（终轮 R1）。流程闸 `HG-AUDIT-R1` 仍 **pending**（本帽不签发）——**可交 00 代签 HG-AUDIT-R1**；pending 期间禁止下发 30 Prompt。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（00 代签 · 维护者 Prompt 授权 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
