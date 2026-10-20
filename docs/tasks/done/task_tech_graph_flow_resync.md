# Task：tech-graph-flow-resync（lg_rag 图谱 flow/l2 索引重同步 · 纯 docs 面 · 零 app/ 改动 · D2-a 续冻落定）

- **状态**：draft v0.1（2026-10-20 10-task 起草 · 待 20-task-audit R1 → HG-AUDIT-R1 → 30）
- **类型**：docs（图谱文档面重同步 · **零 `app/` 零 `tests/` 改动**）
- **依据**：`docs/spec/tech-graph-flow-resync/SPEC-tech-graph-flow-resync_v0.md`（v0 · **signed · HG-SPEC-SIGNOFF=approved 2026-10-19 维护者 · 裁定 D2-a 续冻**）+ `docs/harness/reviews/spec_tech-graph-flow-resync_audit_R1_20261019.md`（R1 conditional_pass · 阻塞 0 · 锚点 17/17 · N1–N5 移交本 task 吸收）
- **建议序**：5/5（收官：#1 query-coref-rewrite 已合 PR #284 · #2 memory-injection-consumer 已合 PR #285 · #3 scenario-stage-rewire 已合 PR #286 · #4 delegation-naming-boundary 已合 PR #288（master `c17e63b` · **#1–#4 全部落定**）→ **本 task**）
- **分支**：本文件落盘于文档线 `docs/task-tech-graph-flow-resync`（自 master `31924af` 切出）；30 开工分支 `task/tech-graph-flow-resync`（30 开工前自 master `c17e63b`（#1–#4 全合）另行切出 · 勿与文档线混用）

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `tech-graph-flow-resync` |
| **git_branch** | `task/tech-graph-flow-resync`（30 开工自 master `c17e63b` 切出 · 基线按实钉锚落 invoke） |
| **implement_repo** | ops-desk-api（本仓） |
| **spec** | `docs/spec/tech-graph-flow-resync/SPEC-tech-graph-flow-resync_v0.md`（v0 signed） |
| **test_strategy** | required（图谱校验） |
| **test_strategy_note** | `./scripts/graph-compile.sh` 必过 EXIT=0（compile+check+mermaid normalize 三重机器校验）+ 重跑 compile 幂等断言（生成物零 diff=无手改）+ flow↔代码逐边对拍 checklist（落 invoke）+ 行号锚点抽查 ≥10 条 ±10 行 + dormant/冻结声明存在性 grep 断言 + 白名单 diff（`git diff --stat`）；**纯 docs 面不新增 pytest 闸**（裁定理由见非范围 task 级补充 ②） |
| **code_quality_bar** | L2_backend（沿用字段 · 本 task 无代码面） |
| **graph_change_layer** | `docs`（**图谱文档面 · 零 app/ 改动** · HG-GRAPH-MODULES=approved 在册） |
| **graph_delta** | `docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml` 源重画（nodes/edges/anchors 摘除 s_intent · 拓扑=supervisor-first 实际 · 锚点重核 · version 日期更新）→ compile 重生成 `10_flow_lg_rag.md` + `shared/graph.json` → `build_site.py` 重生成 `dist/site-data.json`；`l2/indexes/by_path_lg_rag.yaml` / `by_symbol_lg_rag.yaml` 文件头加冻结声明（version 不加新版本）+ `s_intent` 标 dormant；不新增一级模块 · 零新跨模块边 · 不增 implementedBy · 零新路由/表/SSE 事件类型 |
| **graph_delta_note** | **编辑真值面 = yaml 源**（R1 N1）：`10_flow_lg_rag.md` 是 `graph-compile.sh` 生成物（md:5 `source:` 行），手改 .md 会被下次 compile 覆盖回滚；`shared/graph.json`（graph_yaml_to_json.py 生成）与 `docs/arch-browser/dist/site-data.json`（build_site.py 衍生只读视图 · README:4 纪律）同列「生成物 · 勿手改」清单 |
| **wiki_delta** | none（纯图谱文档面 · 无 WikiTrack 读序/规范/guides 变更） |
| **wiki_delta_note** | 图谱 l1/l2 属 `docs/_tech_graph/` 原路径真值，非 coding_wiki 读序面 |
| **review_hat** | 20 |
| **required_invoke_hats** | 10,20,30,40 |
| **invoke_retention_profile** | default（`docs/harness/invokes/by-task/tech-graph-flow-resync/` · 本文件起草即建目录占位 · R1 N4 闭合） |
| **experience_capture** | required |
| **kpi_aggregator** | n/a |
| **orchestration** | 10 落稿（本文件）→ 20-task-audit R1 → HG-AUDIT-R1（维护者已授权 00 代签后续文档闸 · m00147 授权在案 · 落闸动作在 20-task-audit 之后由 00 执行，起草时 pending）→ 30（自 master `c17e63b` 切分支 · #1–#4 已全落定）→ 40 → PR+CI 绿 → CLOSE（建议序 5/5 收官） |
| **freeze_id** | 承 SPEC：图谱 freeze 契约 `lg-rag-http-v1` / `lg-rag-sse-v1` 描述不变（代码没变，是图谱追上代码）；30 实判需动 → 回 SPEC 升 freeze，禁 silent 扩 |

### 人工闸

| 闸 | 状态 | 阻塞 | 备注 |
|---|---|---|---|
| HG-SPEC-SIGNOFF | **approved**（2026-10-19 维护者 · **裁定 D2-a 续冻**：l2 索引加显式冻结声明 + s_intent 标 dormant · 不扩 l2 重生成） | 20 书面审 | SPEC v0 文末签收记录 |
| HG-AUDIT-R1 | **approved**（2026-10-20 · 00 代签 · 维护者扩展授权 m00147 在案 · R1=conditional_pass 阻塞 0 · 代签即确认 N4 收窄：SPEC §6 dormant 三处一致 → 两处一致 + __init__.py:5 docstring 挂账移交另案） | 30 改码 | 审查文落 `docs/harness/reviews/`；授权链 invoke 落 `docs/harness/invokes/by-task/tech-graph-flow-resync/` |
| HG-GRAPH-MODULES | **approved**（本 task 即图谱文档面重同步：不新增/不撤销一级模块 · 零新跨模块边 · 不增 implementedBy · 零新路由/表/SSE 事件类型 · l2 续冻裁定含维护者签收） | 30 改码 | `graph_change_layer=docs` 预期不再签；30 实判越出（动 app/ · 扩 l2 · 增行/边）→ 回炉补签 |

---

## 背景与目标

### 问题（承 SPEC §1 + R1 §一.1 实证）

supervisor-first（PR #282 = 35b8f95，2026-10-19 合入）改了图拓扑，`01_modules.md:35` lg_rag 行当天已更新（「2026-10-19 supervisor-first 去前置 Intent」），但 flow 文档与 l2 索引没跟上——l1 层内部自相矛盾（行备注说「去前置 Intent」，flow 文档还在画 intent_node）。图谱是 HG-GRAPH-MODULES 闸的真值：**自相矛盾的地图比没有地图更危险**。R1 实证 5 项差异 17 处锚点全中（一致 17 · 漂移/虚构 0）。

### 目标（承 SPEC §1 + 维护者 D2-a 裁定 + 收官棒收窄裁定）

lg_rag 图谱与 supervisor-first 代码全面对拍：**D1** flow 拓扑重画（编辑真值面钉 yaml 源 · R1 N1）；**D2** l2 索引按维护者裁定 **D2-a 续冻**落显式冻结声明 + `s_intent` 标 dormant；**D3** docs/ 现行文档面旧拓扑描述修正；**D4** 两处 app/ 面残留（sse_stream 死键 · `__init__.py` docstring）裁定**移交挂账**——本 task 零 `app/` 改动（SPEC D3 注释面的有意收窄 · 见 D4 裁定理由）。

## 范围

### D1 flow 拓扑重画（**编辑真值面 = yaml 源** · R1 N1 最重要发现）

- **编辑面**：`docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml`（nodes / edges / anchors / version）；**禁手改** `10_flow_lg_rag.md`（compile 生成物 · 手改会被覆盖回滚 · TC1 幂等断言机断）
- **拓扑真值**（10-task 于 master `c17e63b` 亲读复核 · 30 按实校正）：
  - `app/ops/lg_rag/multi/graph.py:96-104`：`:96` `add_edge(START, "strategy_builder")` → `:97` strategy_builder→supervisor → `:98` supervisor→subtask_join → `:99` conditional `route_next_subtask`（`_DISPATCH_MAP` :53-60：rag_subtask / info_extract / tool_exec / observe）→ `:100-101` 工人回 subtask_join → `:102` observe conditional `route_after_react`（`_REACT_MAP` :63-66：replan→supervisor / settle→aggregator）→ `:103` aggregator→critic_node → `:104` conditional `route_after_critic`（`_CRITIC_MAP` :69-74：pass/end→END · retry_planner→supervisor · rebind→strategy_builder）
  - 旧文档 `START → intent_node` 拓扑须全部更正；全文件无 intent_node 挂载/导入（R1 实证）
- **摘除面**（yaml 现状 · 10-task 亲读坐标）：`s_intent` 节点 `10_flow_lg_rag.graph.yaml:159-165` · START→s_intent 边 `:495-496`（label "START → intent_node"）· s_intent 出边 `:501-503` · s_intent anchors `:730-744` 两块——全部摘除
- **dormant 说明保留**：flow 文档保留一段「IntentV1 保留未挂载（dormant）」说明，指向 `app/ops/strategy/intent.py`（:52 `async def intent_node` 在册 · 代码保留不删 · 承 `01_modules.md:18` legacy/dormant「一律不删」约定）；落点须进 yaml 源（description 或说明节点），使 compile 带入生成物
- **锚点重核**：全部行号锚点按重生成时点代码重核（±10 行精度）。R1 实测漂移清单（30 逐条核销 · **nodes.py 坐标已按 c17e63b 重核**——#4 合并致位移，括号内为 R1 时值）：sup 边锚 `graph.py#L73-80` → 实际 `:96-104`（未动）；`s_rag` 锚 `nodes.py#L266` → 实际 `rag_subtask_node` **`:1420`**（R1 时 :1391）；`s_supervisor` complete 锚 `nodes.py#L200` → 实际 **`provider.complete` `:1193`**（R1 时 :1163-1170）；Send 边锚 `nodes.py#L238` → 实际 `route_next_subtask` **`:1339`**（R1 时 :1310）；critic 回环锚 `graph.py#L51-52` → 实际 `:104` / `_CRITIC_MAP` :69-74（未动）。l2 缺口符号 c17e63b 坐标（供 D2 边界声明引用）：`_issue_plan` :566 · `_join_subtasks` :893 · `_persist_hitl` :1810 · `observe_node` :1984
- **version**：yaml `version` 日期更新为重生成日（compile 带入 md front-matter）
- **生成物链**：`./scripts/graph-compile.sh`（spec-wave@3.3.0 compile + graph_yaml_to_json.py 生成 `shared/graph.json` + check + mermaid normalize check-only）→ `python3 docs/arch-browser/scripts/build_site.py`（graph.json → `dist/site-data.json` 衍生只读视图）；两处生成物链全部重跑，diff 即拓扑修正面

### D2 l2 索引 **D2-a 续冻**落显式冻结声明（维护者已裁定 · 签收凭证 SPEC v0 文末）

- **编辑面**：`docs/_tech_graph/l2/indexes/by_path_lg_rag.yaml` 与 `by_symbol_lg_rag.yaml` 文件头注释区（现 :1-4 头注段 · version 行 :6 两侧）
- **冻结声明四要素**（缺一 TC5 fail）：
  1. **冻结日期**：version `"2026-08-31"` 维持原值——**不加新版本**（声明走文件头注释，不动 version 字段）
  2. **覆盖边界**：截至 2026-08-31 的 implementedBy 面；显式列明缺口——Wave B 新文件 `run_worker.py` / `sse_subscribe.py`、后期符号 `observe_node` / `_join_subtasks` / `_persist_hitl` / `_issue_plan`、hitl 模块——「引用时须知止步于此」
  3. **冻结原因**：维护者 2026-10-19 D2-a 裁定（索引维护成本高、审核引用少 · SpecWave #40「图谱先读」纪律未落地）
  4. **解冻条件**：SpecWave #40 落地索引成高频入口，或维护者另行裁定 → 走 D2-b 扩面**另案**（非本 task）
- **s_intent 标 dormant**：`by_path_lg_rag.yaml:197-199` 与 `by_symbol_lg_rag.yaml:216-218` 的 `s_intent` / `intent_node` 条目加 dormant/未挂载标注（scenario stage 已摘除 · #3 已合并 · supervisor-first 后 lg_rag 三图零挂载 · 承 `01_modules.md:18` 约定一律不删）

### D3 docs/ 现行文档面旧拓扑描述修正（docs-only）

- 现行生效文档面 grep `START → intent_node`：命中即修正为 supervisor-first 实际拓扑或标注历史版本归属
- **历史文档不动**（不可变历史记录 · 承 R1 N3 口径）：`docs/tasks/done/` 两件、旧 SPEC、reviews/、invokes/、`ROADMAP_strategy_builder_v0.md:123`、`GUIDE_intent-vs-router-coexistence_v0.md:17`——按「标注历史版本归属」口径**无需追溯改写**
- `01_modules.md:35` lg_rag 行已含「2026-10-19 supervisor-first 去前置 Intent」（10-task 亲读在册）——**无需改**；引用口径承 R1 N5：写「:35 lg_rag 行」不写「行末备注」；承 R1 N2：md 侧引用按「:106 mermaid / :259 边表」分拆，本 task 摘除面一律引 yaml 源坐标（见 D1）

### D4 挂账移交登记（R1 N3 死键 + `__init__.py` docstring · 两处 app/ 面残留）

本 task **零 `app/` 改动**（铁律 · graph_change_layer=docs）。SPEC D3 原含 `multi/__init__.py` docstring 注释-only 修正与全仓扫，维护者收官棒收窄为纯 docs 面——两处 app/ 残留裁定**移交挂账**（**不**走图谱备注知会 · 理由：知会仍属在册留存，挂账移交才把处置权交还后续 app 面 task，且与 `01_modules.md:18`「一律不删」约定同向）：

| # | 残留 | 实证 | 裁定 |
|---|---|---|---|
| 1 | `app/ops/lg_rag/sse_stream.py:63-66` `_ROLE_ALIAS = {"intent_node": "intent", ...}`（死键 :64 · R1 N3） | 死映射零行为（图已无 intent_node 帧源 · #3 scenario 摘除后亦无 scenario 消费） | **移交挂账**：后续 app 面 task 处置（删 or 保留说明），本 task 不碰 |
| 2 | `app/ops/lg_rag/multi/__init__.py:5` docstring 仍写「拓扑：START → intent_node → strategy_builder → supervisor」 | 与同包 `graph.py:82` 注释（supervisor-first 去前置 intent_node）直接冲突（SPEC 差异 5 · R1 实证逐字在册） | **移交挂账**：注释-only 修正移交后续 app 面 task；本 task 不碰（SPEC D3 的有意收窄 · 20-task-audit 核对移交项不丢） |

移交清单同步落 invoke（30/40 复核出口），TC6 机断在册性。

## 非范围（承 SPEC §3 原样 + task 级补充）

承 SPEC 非范围：❌ 改图谱分层结构（G-L0/L1/L2 物理分层不动）· ❌ 改 HG-GRAPH-MODULES 闸语义与签署流程 · ❌ 概念总图 delegation 9 项缺口（另案）· ❌ 图谱↔代码自动同步工具 · ❌ 建议序 1–4 落定前启动——**1–4 已全部落定（master `c17e63b`）· 启动条件已满足 · 30 仍须 HG-AUDIT-R1 approved**。

task 级补充：

- ① **零 `app/` 改动**——含 `multi/__init__.py:5` docstring（SPEC D3 注释面有意收窄 · D4 挂账移交）与 `sse_stream.py:63-66` 死键（R1 N3 · D4 挂账移交）
- ② **零 `tests/` 改动 · 不新增 pytest 闸**（含 git 基线锚点白名单测试）——裁定理由：本 task 改动面 100% 落在 `docs/_tech_graph/` 与其生成物链，`graph-compile.sh` 内部已含 compile + check + mermaid normalize 三重机器校验（既有闸 · PR 合并前必过）；#2/#3 `_resolve_base`/`_BANNED_PREFIXES`/波次分类器四态先例服务的是 app/tests diff 白名单的**机器化**判定，纯 docs 面白名单由 TC7 `git diff --stat` 断言 + 40 复核 + CI 绿即可闭合，新增 pytest 闸对纯 docs task **零增量保护**（反增维护面）
- ③ **l2 索引重生成/扩面**（D2-b 弃 · 维护者裁定续冻 · 解冻另案）
- ④ 历史 docs 旧拓扑引用不动（不可变历史记录 · D3 口径）
- ⑤ 本起草阶段零 `app/` `tests/` 改码（仅 task 文档 + invoke 占位）

## failure_paths

| ID | 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|---|---|---|---|
| FP-1 | 手改 `10_flow_lg_rag.md` 生成物（未改 yaml 源） | 下次 compile 覆盖回滚 · TC1 幂等断言 fail（重跑 compile 后生成物 git diff 非零=手改混入） | 是（改回 yaml 源重生成） | 否 |
| FP-2 | 重生成后 flow ↔ 代码对拍不符 | 对拍 checklist 逐边/节点在代码找到对应（`graph.py:96-104` + 三 MAP 坐标）· 任一条无对应 fail | 是（修正 yaml 重生成） | 否 |
| FP-3 | 行号锚点漂移残留 | 抽查 ≥10 条 · 每条指向符号实际位置 ±10 行内 · 任一越界 fail | 是（重核锚点） | 否 |
| FP-4 | `graph-compile.sh` 失败 | EXIT≠0 · 报错必带**具体错名+路径**（spec-wave check 报错文件/字段 · graph_yaml_to_json.py · mermaid normalize）· 禁裸「失败」 | 是（按错名修 yaml） | 否 |
| FP-5 | intent 残留或 dormant 标注缺失 | 生成物 md + yaml grep `START → intent_node` 零命中（豁免历史 docs）· flow dormant 说明段存在 · l2 两索引 `s_intent` dormant 标记存在 · 缺一 fail | 是 | 否 |
| FP-6 | 冻结声明缺要素或 version 被 bump | 四要素（冻结日期/覆盖边界/冻结原因/解冻条件）grep 断言 · version 仍 `"2026-08-31"` · 缺一 fail | 是 | 否 |
| FP-7 | 生成物 diff 越面（含拓扑修正外内容） | 40 复核 `git diff` 生成物三件（md/graph.json/site-data.json）= 拓扑修正面 · 越面 fail | 是（回滚越面段） | 否 |
| FP-8 | `app/` `tests/` `scripts/` `alembic/` 出现任何改动 | TC7 `git diff --stat` 断言 fail（零改动铁律） | 是（回滚） | 否 |
| FP-9 | 挂账移交项丢失（D4 两项不在册） | TC6 task+invoke 移交清单在册断言 fail | 是（补登记） | 否 |

## 验收标准

- [ ] **TC1 编辑面钉死 + compile 幂等（承 R1 N1 · FP-1/FP-4）**：拓扑修正只改 `docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml` 源；`./scripts/graph-compile.sh` EXIT=0；`python3 docs/arch-browser/scripts/build_site.py` 重跑成功；**重跑 graph-compile 后 `git diff --exit-code` 于三件生成物（`10_flow_lg_rag.md` · `shared/graph.json` · `dist/site-data.json`）=0**（幂等=无手改混入）；生成物 diff 即拓扑修正面。
- [ ] **TC2 拓扑对拍（承 SPEC FP-1 · FP-2）**：重生成 flow 拓扑 = `graph.py:96-104` + `_DISPATCH_MAP` :53-60 + `_REACT_MAP` :63-66 + `_CRITIC_MAP` :69-74；checklist 逐边/节点注代码坐标全勾，落 invoke。
- [ ] **TC3 锚点抽查（承 SPEC FP-2 · FP-3）**：≥10 条行号锚点指向符号实际位置 ±10 行内；R1 漂移清单五条（sup 边 / s_rag / s_supervisor complete / Send 边 / critic 回环）必含；抽查清单落 invoke。
- [ ] **TC4 intent dormant 三面一致（承 SPEC FP-4 · FP-5）**：flow yaml 摘除 `s_intent` 节点/边/anchors（:159-165/:495-496/:501-503/:730-744 面）+ dormant 说明段在册指向 `app/ops/strategy/intent.py`；生成物 md grep `START → intent_node` 零命中；l2 两索引 `s_intent` 条目 dormant/未挂载标记在册。
- [ ] **TC5 D2-a 冻结声明（承 SPEC FP-5 · FP-6）**：`by_path_lg_rag.yaml` / `by_symbol_lg_rag.yaml` 文件头冻结声明四要素齐（冻结日期 2026-08-31 + 覆盖边界含 Wave B 与后期符号缺口 + 冻结原因维护者裁定 + 解冻条件 #40/另行裁定另案）；`version` 字段仍为 `"2026-08-31"`（不加新版本）。
- [ ] **TC6 挂账移交在册（FP-9）**：D4 两项移交（`sse_stream.py:63-66` `_ROLE_ALIAS` 死键 · `multi/__init__.py:5` docstring）在 task 非范围 ① + D4 表 + invoke 移交清单三处在册。
- [ ] **TC7 白名单 diff（FP-7/FP-8）**：改动面 ⊆ {`docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml`、`docs/_tech_graph/l1/10_flow_lg_rag.md`（生成物）、`docs/_tech_graph/shared/graph.json`（生成物）、`docs/arch-browser/dist/site-data.json`（生成物）、`docs/_tech_graph/l2/indexes/by_path_lg_rag.yaml`、`docs/_tech_graph/l2/indexes/by_symbol_lg_rag.yaml`、（可选）docs/ 现行文档旧拓扑修正面、`docs/harness/invokes/by-task/tech-graph-flow-resync/**`、`docs/tasks/active/task_tech_graph_flow_resync.md`}；`app/` `tests/` `scripts/` `alembic/` 零改动（`git diff --stat` 断言 · 40 复核）。
- [ ] **TC8 文档落位**：invoke 目录 10/20/30/40 齐；invoke 落「**重生成时点 commit hash**」（下次漂移判定基准 · 承 SPEC §6 验收末条）；CI 绿（含 lint-wiki-delta 与 graph-compile 既有工作流）。

## 依赖

- base：master `c17e63b`（**#1–#4 全合** PR #284/#285/#286/#288）· 30 开工分支自 `c17e63b` 切出（基线按实钉锚落 invoke）；文档线 `docs/task-tech-graph-flow-resync`（自 `31924af` 切出 · 已 ff 至 `c17e63b`）
- SPEC：`docs/spec/tech-graph-flow-resync/SPEC-tech-graph-flow-resync_v0.md`（v0 signed · D2-a 裁定在文末）；审查文：`docs/harness/reviews/spec_tech-graph-flow-resync_audit_R1_20261019.md`（R1 conditional_pass · N1–N5）
- 拓扑真值（10-task 于 master `c17e63b` 亲读复核 · 30 按实校正）：`app/ops/lg_rag/multi/graph.py:53-105`（三 MAP + 建图边）；`app/ops/strategy/intent.py:52`（dormant 指向）；`multi/nodes.py` 符号坐标（:1420/:1339/:1193/:893/:566/:1810/:1984）
- dormant 约定：`docs/_tech_graph/l1/01_modules.md:18`（legacy/dormant 一律不删）· `docs/_tech_graph/README.md:19/:21`
- 生成物链：`scripts/graph-compile.sh`（spec-wave@3.3.0 钉版）· `scripts/graph_yaml_to_json.py` · `docs/arch-browser/scripts/build_site.py`
- 结构先例：`docs/tasks/done/task_scenario_stage_rewire.md`、`docs/tasks/done/task_memory_injection_consumer.md`
- 编码规范：`docs/standards/CODING_BACKEND_L2_v1_zh.md`（字段沿用 · 本 task 无代码面）

## 给执行帽的必读列表

1. 本 task 全文（含人工闸表 · **HG-AUDIT-R1=pending 未签不得 30**）
2. `docs/spec/tech-graph-flow-resync/SPEC-tech-graph-flow-resync_v0.md`（v0 · D1/D2-a/D3 + FP-1~FP-7 + freeze 面）
3. `docs/harness/reviews/spec_tech-graph-flow-resync_audit_R1_20261019.md`（N1–N5 本 task 已吸收落位：N1→D1/TC1 · N2/N5→D3 引用口径 · N3→D4 挂账 · N4→invoke 目录）
4. `app/ops/lg_rag/multi/graph.py:53-105` 全文亲读（30 实施前再核行号与三 MAP）
5. `docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml` 全文 + `scripts/graph-compile.sh`（编辑真值面与生成物链）
6. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（30 开工 GATE_VERIFY）

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|---|---|---|---|
| R0 依据读取 | SPEC v0 signed（D2-a 裁定在案）· R1 阻塞 0 锚点 17/17 · N1–N5 移交 | 否 | — | 无（#1–#4 已全落定 `c17e63b`） |
| R1 锚点亲读 | master `c17e63b` 全锚复核：graph.py:96-104/三 MAP · yaml 摘除面 :159-165/:495-496/:501-503/:730-744 · l2 头注 :1-6 与 s_intent :197-199/:216-218 · sse_stream :63-66 · `__init__.py`:5 · nodes.py 位移核销（#4 致 :1391→:1420/:1310→:1339/:1163-1170→:1193）· 01_modules :35 已在册 | 否 | — | 行号仍可能随后续合并漂移（30 按实校正 · 对拍 checklist 兜底） |
| R2 格局沿用 | 闸表三行 / TC 全机断 / FP 表 / R 轮控制表沿用 #3 #4 定稿格局（scenario-stage-rewire · delegation-naming-boundary） | 否 | — | 无 |
| R3 反例与边界 | FP-1~FP-9 完备（手改覆盖/对拍/锚点/compile 错名/intent 三面/声明四要素/生成物越面/禁区零改动/挂账丢失）· 生成物幂等断言（TC1 重跑 diff=0）为纯 docs 面专属机断 | 否 | — | 无 |
| R4 开放点收口 | N3/__init__ 裁定移交挂账（零 app/ 铁律）· l2 续冻声明四要素定型 · 白名单测试裁定不设（docs 面零增量保护）· D2-b 列非范围 | 是 | 开放点全收口 · TC1–TC8 全可机断 | 无 |
| R5 定稿自检 | 闸表齐 · N1–N5 落位 · D2-a 四要素入验收 · 零 app/ 零代签 · lint PASS 后提交 | 是 | 收官棒草稿可交 20-task-audit | HG-AUDIT-R1=pending（blocks 30 · 00 代签授权在案 m00147） |

### R0 轮：依据读取

SPEC v0（signed · HG-SPEC-SIGNOFF=approved · **D2-a 续冻裁定**：l2 加显式冻结声明 + s_intent 标 dormant · 不扩 l2 重生成）+ R1 conditional_pass（阻塞 0 · 锚点 17/17 · N1–N5 移交）。结论：可起草，且 D2 分支已定（a），验收按 FP-5 冻结声明面写，FP-6 扩面面不适用（转非范围 ③）。

### R1 轮：锚点亲读复核（master `c17e63b` · 初稿于 `31924af` 复核 · #4 合并后全锚重核）

拓扑真值 `graph.py:96-104`（START→strategy_builder→supervisor→subtask_join→conditional/observe→aggregator→critic_node）+ `_DISPATCH_MAP` :53-60 / `_REACT_MAP` :63-66 / `_CRITIC_MAP` :69-74 逐行在册；yaml 摘除面四处坐标在册（:159-165 s_intent 节点 · :495-496 START→s_intent 边 · :501-503 出边 · :730-744 anchors 两块）；l2 两索引头注 :1-4 + version :6（`"2026-08-31"`）与 `s_intent` 条目（by_path :197-199 · by_symbol :216-218）在册；`sse_stream.py:63-66` `_ROLE_ALIAS`（:64 死键）与 `multi/__init__.py:5` docstring 逐字在册；`01_modules.md:35` lg_rag 行已含 2026-10-19 去前置 Intent、scenario 摘除（2026-10-20 · 模块 dormant 保留）与 #4 正名（`issuance_policy_allows` / `LG_RAG_WRITE_REPLAY_GUARD_ENABLED` 在册）——D3 无需改图谱行。#4 合并致 nodes.py 位移：`rag_subtask_node` :1420 · `route_next_subtask` :1339 · `provider.complete` :1193（c17e63b 重核 · graph.py/yaml/l2/sse_stream/__init__ 坐标未动）。

### R2 轮：格局沿用

闸表三行 / TC 全可机断 / FP 表 / R 轮控制表 / 必读列表，沿用 #3 #4 定稿格局；N1–N5 吸收索引写入 invoke（承 scenario-stage-rewire invoke_10 先例）。

### R3 轮：反例与边界

FP-1（手改生成物被覆盖）以 TC1 **重跑 compile 幂等断言**机断——纯 docs 面专属牙，替代 #2/#3 的 pytest 白名单闸；FP-4 强制 compile 失败带具体错名+路径（00 指令）；FP-8 禁区零改动 `git diff --stat` 断言。

### R4 轮：开放点收口

① R1 N3 死键 + `__init__.py` docstring：裁定**移交挂账**（非图谱备注知会）——零 app/ 铁律下处置权交还后续 app 面 task，D4 表 + 非范围 ① + invoke 移交清单三处在册；② l2 冻结声明定四要素（日期/边界/原因/解冻条件）· version 不加新版本；③ 白名单 pytest 闸裁定**不设**（docs 面零增量保护 · graph-compile 三重校验即既有闸 · TC7 diff 断言+40 复核闭合）；④ D2-b 扩面列非范围 ③ 解冻另案。

### 自检结论（R5 轮 · 定稿自检）

- 闸表三行齐（SPEC-SIGNOFF approved 含 D2-a 裁定 / AUDIT-R1 pending blocks 30 · 00 代签授权 m00147 在案 / GRAPH-MODULES approved · graph_change_layer=docs 口径写明）✔
- N1→D1 编辑真值面钉 yaml + TC1 幂等断言 ✔ N2/N5→D3 引用口径 ✔ N3→D4 挂账+TC6 ✔ N4→invoke 目录占位 ✔
- D2-a 四要素落 D2 + TC5（version 不加新版本 · 解冻另案）✔ l2 重生成列非范围 ③ ✔
- 验收 TC1–TC8 全可机断 · FP-1~FP-9 覆盖 ✔ 生成物 diff=拓扑修正面（TC1/TC7）✔
- 本起草阶段零 `app/` `tests/` 改码、未改 SPEC、未代签任何闸 ✔

## 修订记录

| 版本 | 日期 | 变更 |
|---|---|---|
| v0.1 | 2026-10-20 | 10-task 起草（master `c17e63b` 亲读复核锚点 · #1–#4 全落定 · D2-a 续冻四要素落验收 · N1 编辑真值面钉 yaml + 幂等断言 · N3/__init__ 裁定移交挂账 · 白名单 pytest 闸裁定不设 · 建议序 5/5 收官 · 待 HG-AUDIT-R1 落签后 30） |
