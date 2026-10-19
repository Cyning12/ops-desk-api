# 20-spec-audit R1 书面审：SPEC-tech-graph-flow-resync v0

> **hat_id**：20-spec-audit（R1 · 轻量路径：10-spec 思考轮 R0–R5 已内联 SPEC §8，单轮 R1）
> **审查对象**：`docs/spec/tech-graph-flow-resync/SPEC-tech-graph-flow-resync_v0.md`（draft · 172 行 · HG-SPEC-SIGNOFF=pending）
> **审查日期**：2026-10-19 · **审查人**：Harness 20-spec-audit（书面审 · 不改 SPEC 实质 · **不代签** HG-SPEC-SIGNOFF）
> **结论**：**conditional_pass（PASS-WITH-NITS）** · 委托方点名三重点全部核对通过 · 阻塞项 0 · 非阻塞 N1–N5 移交 00 起草 task 时吸收 · **建议维护者可签 HG-SPEC-SIGNOFF**（签收时须一并裁定 D2-a/D2-b，SPEC 已自钉）
> **实证复核范围**：SPEC 全文 172 行逐行 · 源码实读 `app/ops/lg_rag/multi/graph.py` 全 154 行 · `app/ops/lg_rag/multi/__init__.py` 全 18 行 · `app/ops/lg_rag/multi/nodes.py` 符号定位 7 处（grep def）+ 实读 :190-279/:1150-1189/:1380-1404 · `app/ops/strategy/intent.py:40-64` · `app/ops/lg_rag/sse_stream.py:55-74` · 图谱实读 `docs/_tech_graph/l1/10_flow_lg_rag.md` 全 291 行 · `10_flow_lg_rag.graph.yaml`:1-15/:485-544 + intent 全 grep · `l2/indexes/by_path_lg_rag.yaml` 头 60 行 + 覆盖率 grep · `by_symbol_lg_rag.yaml` 头 50 行 + 覆盖率 grep · `l2/README.md` 全 20 行 · `01_modules.md:35` · `scripts/graph-compile.sh` 全 71 行 · 前置依赖 4 份 SPEC 存在性 glob · `git log`（PR #282 = 35b8f95 已并 · 5 份 draft SPEC = 6d47c23）

## 一、委托方点名三重点核对

### 1. 对拍差异 5 项是否属实 · **全部属实（PASS）**

| # | SPEC 自述 | 实证 | 裁定 |
|---|---|---|---|
| 1 | flow md 仍画 `START → intent_node`（:106, :259）、s_intent 节点（:209）、intent→strategy_builder 边（:260）、intent LLM/SO 边（:286-287）；version 2026-10-14 | :106 mermaid `sup_graph -->|"START → intent_node"| s_intent` ✅；:209 Nodes 表 `s_intent · intent_node（S2 IntentV1 · acomplete_structured）` ✅；:259/:260/:286/:287 Edges 表四行逐字在册 ✅；front-matter `version: 2026-10-14` ✅。代码侧 `multi/graph.py:96` `builder.add_edge(START, "strategy_builder")`，全文件无 intent_node 挂载/导入——flow 与代码确自相矛盾 | ✅ |
| 2 | 行号锚点漂移：sup 边锚 `graph.py#L73-80`（实际 :96-104）、s_rag 锚 `nodes.py#L266`（实际 :1391）、s_supervisor complete 锚 `:L200`（实际 :1163-1170） | md :107/:109/:111/:113 锚 #L73-76，graph.yaml :499/:506/:513/:520 同源；实际图边在 graph.py:96-104 ✅。s_rag 锚 :155 `nodes.py#L266`，实际 `async def rag_subtask_node` 在 :1391（:266 现为注释块）✅。complete 锚 :158 `nodes.py#L200`，实际 `provider.complete(...)` 在 :1163-1170（:200 现为 `_parse_subtasks` 内）✅。另实测 Send 边锚 `nodes.py#L238`（md :116/:119/:122）亦漂移（:238 现为 `_pending_subtask` 体；`route_next_subtask` 实际 :1310）；critic 回环锚 `graph.py#L51-52`（md :149/:152）实际应指 :104/_CRITIC_MAP——SPEC「普遍漂移」措辞覆盖 | ✅ |
| 3 | l2 索引 version 2026-08-31 有意冻结：缺 run_worker.py/sse_subscribe.py、缺 observe_node/_join_subtasks/_persist_hitl/_issue_plan、缺 hitl 模块 | 两份 yaml `version: "2026-08-31"` ✅；`run_worker`/`sse_subscribe`/`observe_node`/`_join_subtasks`/`_persist_hitl`/`_issue_plan`/`hitl` 七词 grep 两文件均零命中 ✅；代码侧七符号全部存在（nodes.py:541/:868/:1781/:1955 等）——确为冻结非虚构 | ✅ |
| 4 | s_intent 仍挂 l2 索引指向 `intent.py:52`，代码保留但 lg_rag 图全不挂载，图谱未标 dormant | by_path :197-199 / by_symbol :216-218 均载 `intent_node → app/ops/strategy/intent.py · node_id: s_intent`；intent.py:52 `async def intent_node` 在册 ✅；lg_rag 三图 grep 无挂载（chat/graph.py:30 挂的是 chat 自己的 intent_node，别物）✅；flow md/yaml/indexes 无任何 dormant/未挂载标记（dormant 约定存在于 01_modules.md:18、README:19/:21，但未应用于 s_intent）✅ | ✅ |
| 5 | `multi/__init__.py:5` docstring 仍写旧拓扑，与同包 graph.py:82 冲突 | __init__.py:5「拓扑：START → intent_node → strategy_builder → supervisor」逐字在册 ✅；graph.py:82「supervisor-first：去前置 intent_node（IntentV1 模块保留，本图不再挂载）」在册 ✅——同包两注释直接冲突成立 | ✅ |

上游事实链亦核：PR #282 = commit 35b8f95（图边去 intent）已并入；`01_modules.md:35` 含「2026-10-19 supervisor-first 去前置 Intent」；5 份 draft SPEC = commit 6d47c23。**5/5 差异全部属实，无虚构锚点。**

### 2. 前置依赖 1–4 是否钉死 · **PASS**

- 建议序 1–4（query-coref-rewrite / memory-injection-consumer / scenario-stage-rewire / delegation-naming-boundary）四份 SPEC 均在册（`docs/spec/<slug>/SPEC-<slug>_v0.md`，同批 6d47c23 提交，均 draft）。
- SPEC 四面互锁：文首「建议序 5/5（最后做）」+ §2 范围「前置依赖落定后再启动——它们都会再动拓扑相关代码」+ §3 非范围末条「❌ 在前四项修复落定前启动本 task（建议序钉死 5/5 最后）」+ §8 R3（residual：1–4 延期则本项顺延，接受）+ §7 风险表「重生成后不久又漂移 → 建议序钉最后做」。
- 机制论证成立（§4 弃案 A：现在全量追必然再漂移一次）——时机判断是本 SPEC 核心，理由机制性非敷衍。

### 3. D2-a/D2-b 是否留签收裁定 · **PASS（本帽不预裁、不代签）**

- 四面互锁：人工闸表「l2 索引扩/冻裁定在签收时一并做（见 D2）」+ §1 一句话目标「由维护者签收时裁定（本 SPEC 预写两分支）」+ §8 R5「签收时必须一并裁定 D2 分支」+ §6 验收「l2 分支裁定有维护者签收记录；按分支完成 FP-5 或 FP-6」。
- 两分支各自有可机断 FP（FP-5 冻结声明存在性 / FP-6 点名文件与符号入索引），裁定任一分支后 task 验收不含糊。
- 分支适用判断（索引维护成本 vs SpecWave #40 图谱先读纪律）留给维护者，SPEC 未预设倾向——合规。

## 二、结构核对表（范围 / 非范围 / 验收 / failure_paths / 思考轮）

| 项 | 裁定 | 摘要 |
|---|---|---|
| 现状锚点真实性 | ✅ | 5 项差异 17 处锚点逐一实测全中（见 §一.1）；抽查结果：**一致 17 条 · 漂移/虚构 0 条** |
| 范围 D1/D2/D3 内聚 | ✅ | D1 flow 重生成（必做）+ D2 l2 二选一（签收裁定）+ D3 docstring 注释-only，三块同属「图谱追上代码」一主题；唯一代码面 `__init__.py` docstring 与非范围「除 docstring 外零 app/ 改动」互锁 |
| 非范围与范围互斥 | ✅ | §3 六条与 D1–D3 无重叠；「不动分层结构 / 不动闸语义 / 不做自动同步工具」与风险表「l2 扩面失控」缓解（D2-b 只补点名清单）方向一致 |
| 验收可机断 | ✅ | 六条全部可机器判定：拓扑对拍 checklist、锚点 ±10 行抽查 ≥10 条、dormant 三处一致性、冻结声明/索引条目存在性、graph-compile.sh、invoke 记 commit hash |
| failure_paths 充分 | ✅ | FP-1~FP-7 覆盖对拍 / 锚点抽查 / 既有校验零回归 / intent dormant 三面 / D2 两分支各一条 / docstring 一致性 + grep 无残留；D2 两分支 FP 成对（FP-5/FP-6） |
| R0–R5 思考轮闭合 | ✅ | §8 表 + 各轮小节齐全；`actual_last_round=R5`；R5 reason=「人签未发生」、residual=`HG-SPEC-SIGNOFF=pending`——诚实标记 draft；R2 方案对比 A/B/C 两弃一采，弃案理由机制性 |
| 人工闸纪律 | ✅ | HG-SPEC-SIGNOFF=pending 在表；SPEC R5 自声明「不授权改 app/（含 docstring——需 task + 闸）」；本帽不代签 |
| freeze 契约 | ✅ | freeze_id 行「lg-rag-http-v1 / lg-rag-sse-v1 描述不变（代码没变，是图谱追上代码）」成立——代码侧本轮零行为变更 |

## 三、非阻塞 nits（移交 00 起草 task 吸收；**不**退回 10-spec · 不改 SPEC 实质）

| ID | 位置 | 内容 |
|---|---|---|
| N1 | D1 / test_strategy_note | **编辑真值面未显式钉为 yaml 源**：`10_flow_lg_rag.md` 是 `graph-compile.sh` 从 `10_flow_lg_rag.graph.yaml` 的生成物（md:5 `source:` 行；锚点真值在 yaml :497-520 等 `anchors:` 段）。30 若只手改 .md，下次 compile 即覆盖回滚。「重生成」一词隐含此意但未钉死——建议 task 验收显式写「改 `10_flow_lg_rag.graph.yaml` 源（节点/边/anchors）→ `./scripts/graph-compile.sh` 重生成 .md + shared/graph.json」，并将生成物 `shared/graph.json:2634`、`docs/arch-browser/dist/site-data.json:4363`（均含旧拓扑串）列入「compile 覆盖、勿手改」清单 |
| N2 | 文首现状锚点 1 | 措辞精度：「mermaid `START → intent_node`（:106, :259）」——:259 实为 Structured Data Edges 表行（非 mermaid 块）；mermaid 块内仅 :106。锚点真实、归类用词不准，task 引用时按「:106 mermaid / :259 边表」分拆 |
| N3 | D3 全仓扫 vs §3 非范围 | **扫描范围缝隙**：D3「grep 其他仍写 START → intent_node 的注释/文档一并修正或标注」，但实测命中含**代码面** `app/ops/lg_rag/sse_stream.py:64` `_ROLE_ALIAS = {"intent_node": "intent", ...}`（死映射，非注释/docstring）——§3 非范围禁止动除 `__init__.py` docstring 外的 app/ 代码，扫到它时 SPEC 内无处安放。建议 task 显式裁定：豁免为「dormant 死键 · 零行为 · 不删」（与 01_modules.md:18「一律不删」约定同向）或扩注释面。另历史文档命中（docs/tasks/done/ 两件、旧 SPEC、ROADMAP_strategy_builder_v0.md:123、GUIDE_intent-vs-router-coexistence_v0.md:17）按 D3「标注历史版本归属」处理即可，无需追溯改写 |
| N4 | invoke_slug | SPEC 声明 `invoke_slug=tech-graph-flow-resync`，但 `docs/harness/invokes/by-task/tech-graph-flow-resync/` 当前不存在（SPEC 阶段思考轮已内联 §8，轻量路径可接受）。按仓纪律 pre-30 invoke 缺失拒改码——移交 00 起草 task 时同步补 invoke（含对拍 checklist 与重生成时点 commit hash 落位，验收末条已要求） |
| N5 | 文首现状锚点（上游行） | 定位词精度：「01_modules.md:35 行末备注」——实测「2026-10-19 supervisor-first 去前置 Intent」位于 :35 行**中段**（该行极长，行末实为 supervisor-first-fail-closed 的 `error.stage=supervisor_plan` 段）。锚点真实，「行末」定位词不准；且该行自述「见行末备注」自指亦跳不到拓扑句。不影响结论，task 引用时写「:35 lg_rag 行」即可 |

## 四、HG-SPEC-SIGNOFF 建议

**建议维护者可签 HG-SPEC-SIGNOFF**（conditional_pass：nits 不阻塞人签，移交 task 阶段吸收）。签收动作按 SPEC 自钉须**一并裁定 D2-a（继续冻 + 冻结声明 + s_intent dormant 标记）或 D2-b（扩 Wave B 文件与点名符号）**，裁定记录落签收凭证。本帽**不代签**；人签前维持：不出 task / 不改码 / 30 拒开工；且建议序约束不变——本 task 在 1–4 落定前不启动 30。

## 五、下一棒

人签（含 D2 裁定）→ 待建议序 1–4 落定 → **00 起草 task**（slug=`tech-graph-flow-resync`，分支 `task/tech-graph-flow-resync`）：
1. 吸收 N1–N5 进 task 验收/failure_paths（尤其 N1 yaml 源钉法、N3 sse_stream 死键裁定）；
2. 补 `docs/harness/invokes/by-task/tech-graph-flow-resync/` invoke（对拍 checklist + commit hash 基准位）；
3. task 草稿 → 20-task-audit → HG-AUDIT-R1 人签 → 30。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-10-19 | R1：委托方三重点（5 项差异属实性 / 前置依赖钉死 / D2 签收裁定）全部 PASS；锚点抽查一致 17 条 · 漂移 0 条；conditional_pass · N1–N5 移交 task；建议可签 HG-SPEC-SIGNOFF（不代签 · 签收时裁定 D2） |
