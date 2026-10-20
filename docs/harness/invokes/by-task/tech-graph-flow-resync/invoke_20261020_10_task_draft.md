# invoke：tech-graph-flow-resync · 10_task_draft · 2026-10-20

- **hat**：10-task（task 起草）
- **task**：`docs/tasks/active/task_tech_graph_flow_resync.md`（draft v0.1 · 193 行）
- **建议序**：5/5（收官：#1 PR #284 · #2 PR #285 · #3 PR #286 · #4 PR #288 **全部已合**（master `c17e63b`）→ 本 task）
- **分支**：`docs/task-tech-graph-flow-resync`（自 master `31924af` 切出 · 已 ff 至 `c17e63b`）；30 实施分支 `task/tech-graph-flow-resync` 自 master `c17e63b` 另行切
- **写入面**：仅 task 文件 + 本 invoke（两处分 · 零 `app/` 零 `tests/` 改码 · 未改 SPEC · 未代签任何闸）

## 一、签收与审查依据

| 依据 | 结论 |
|---|---|
| `docs/spec/tech-graph-flow-resync/SPEC-tech-graph-flow-resync_v0.md` | v0 · signed · HG-SPEC-SIGNOFF=approved（2026-10-19 维护者）· **裁定 D2-a 续冻**（l2 索引加显式冻结声明 + s_intent 标 dormant · 不扩 l2 重生成） |
| `docs/harness/reviews/spec_tech-graph-flow-resync_audit_R1_20261019.md` | R1 conditional_pass（阻塞 0 · 锚点 17/17 全中 · N1–N5 移交 task 吸收） |

## 二、N1–N5 吸收位置索引（task 行号 · v0.1）

| 移交项 | 吸收落点 |
|---|---|
| N1（编辑真值面钉 yaml 源 · 生成物勿手改清单） | task D1（编辑面=`10_flow_lg_rag.graph.yaml` · 禁手改 .md · 生成物链 compile→build_site）+ graph_delta_note + TC1（重跑 compile 幂等断言 · 生成物三件 `git diff --exit-code`=0） |
| N2（:106 mermaid / :259 边表 归类措辞） | task D3 引用口径（摘除面一律引 yaml 源坐标 :159-165/:495-496/:501-503/:730-744 · 不引 md 行号） |
| N3（sse_stream.py:64 `_ROLE_ALIAS` 死键范围缝隙） | task D4 表 #1 **裁定移交挂账**（非图谱备注知会 · 零 app/ 铁律）+ 非范围 ① + TC6 在册断言 |
| N4（invoke 目录补建） | task invoke_retention_profile + 本文件（目录占位 · required_invoke_hats=10,20,30,40） |
| N5（01_modules :35 「行末」定位词不准） | task D3 引用口径（写「:35 lg_rag 行」· 10-task 亲读已在册含 2026-10-19 去前置 Intent + 2026-10-20 scenario 摘除 dormant 两段 · 无需改） |

## 三、亲读复核实录（master `c17e63b` · 初稿于 `31924af` 复核 · #4 合并后全锚重核 · 行号 30 按实校正）

| 锚点 | 实录 |
|---|---|
| `app/ops/lg_rag/multi/graph.py` | :96-104 建图边（:96 `add_edge(START, "strategy_builder")` · :97 →supervisor · :98 →subtask_join · :99 conditional route_next_subtask · :100-101 工人回环 · :102 observe conditional · :103 aggregator→critic_node · :104 conditional route_after_critic）· `_DISPATCH_MAP` :53-60 · `_REACT_MAP` :63-66 · `_CRITIC_MAP` :69-74 · 全文件无 intent_node 挂载（c17e63b 未动） |
| `app/ops/lg_rag/multi/nodes.py`（#4 合并致位移 · c17e63b 重核） | `rag_subtask_node` :1420（R1 时 :1391）· `route_next_subtask` :1339（R1 时 :1310）· `provider.complete` :1193（R1 时 :1163-1170）· l2 缺口符号：`_issue_plan` :566 · `_join_subtasks` :893 · `_persist_hitl` :1810 · `observe_node` :1984 |
| `docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml` | 摘除面：s_intent 节点 :159-165 · START→s_intent 边 :495-496 · s_intent 出边 :501-503 · s_intent anchors :730-744 两块 · version `"2026-10-14"` 待更新 |
| `docs/_tech_graph/l2/indexes/` | 两文件头注 :1-4 + version :6 `"2026-08-31"`（维持 · 声明走头注）· s_intent 条目 by_path :197-199 / by_symbol :216-218（dormant 标注落点） |
| `app/ops/strategy/intent.py` | :52 `async def intent_node` 在册 · 代码保留不删（dormant 说明指向点） |
| `app/ops/lg_rag/sse_stream.py` | :63-66 `_ROLE_ALIAS`（:64 `"intent_node": "intent"` 死键 · D4 #1 挂账） |
| `app/ops/lg_rag/multi/__init__.py` | :5 docstring 旧拓扑逐字在册 · 与同包 graph.py:82 注释冲突（D4 #2 挂账） |
| `docs/_tech_graph/l1/01_modules.md` | :18 legacy/dormant「一律不删」约定 · :35 lg_rag 行已含 2026-10-19 去前置 Intent + 2026-10-20 scenario 摘除（模块 dormant 保留）+ #4 正名（`issuance_policy_allows` / `LG_RAG_WRITE_REPLAY_GUARD_ENABLED` 在册）· HG-GRAPH-MODULES approved 在册 |
| 生成物链 | `scripts/graph-compile.sh`（spec-wave@3.3.0 钉版 · compile+check+mermaid normalize）→ `shared/graph.json`（graph_yaml_to_json.py）→ `docs/arch-browser/scripts/build_site.py` → `dist/site-data.json`（实测含旧拓扑串 1 处 · 重生成覆盖） |

## 四、裁定记录（10-task 收口）

1. **N3 死键 + `__init__.py` docstring → 移交挂账**（非图谱备注知会）：本 task 零 `app/` 改动铁律（graph_change_layer=docs）· SPEC D3 注释面有意收窄 · 处置权交还后续 app 面 task · D4 表 + 非范围 ① + 本 invoke §五 三处在册
2. **白名单 pytest 闸 → 不设**：改动面 100% docs/_tech_graph/ 与生成物链 · graph-compile.sh 三重机器校验即既有闸 · #2/#3 `_resolve_base` 四态先例服务 app/tests diff 机断 · 纯 docs 面由 TC7 `git diff --stat` + 40 复核 + CI 绿闭合 · 新增 pytest 零增量保护
3. **l2 冻结声明四要素**：冻结日期（version 维持 `"2026-08-31"` 不加新版本）+ 覆盖边界（Wave B/后期符号缺口列明）+ 冻结原因（维护者 2026-10-19 D2-a 裁定）+ 解冻条件（#40 落地或另行裁定 · D2-b 另案）

## 五、移交挂账清单（30/40 复核出口 · 后续 app 面 task 处置）

| # | 项 | 坐标 | 性质 |
|---|---|---|---|
| 1 | `_ROLE_ALIAS` 死键 `"intent_node": "intent"` | `app/ops/lg_rag/sse_stream.py:63-66`（:64） | 死映射零行为 · R1 N3 · 删/留说明由后续 app 面 task 裁定 |
| 2 | docstring 旧拓扑「START → intent_node → …」 | `app/ops/lg_rag/multi/__init__.py:5` | 注释-only · 与 graph.py:82 冲突 · SPEC 差异 5 · 注释修正移交后续 task |

## 六、产出与闸态

- 产出：`docs/tasks/active/task_tech_graph_flow_resync.md`（193 行 · `npx dsh-coding-kit task lint` 结果落本文件修订——见 task 修订记录）+ 本 invoke
- 闸态：HG-SPEC-SIGNOFF=**approved**（2026-10-19 · D2-a 裁定）· HG-AUDIT-R1=**pending**（blocks 30 · 维护者已授权 00 代签后续文档闸 · m00147 授权在案 · 落闸动作在 20-task-audit 之后由 00 执行）· HG-GRAPH-MODULES=**approved**（graph_change_layer=docs 预期不再签 · 越出回炉补签）
- 下一步：20-task-audit R1 书面审 → HG-AUDIT-R1 落签（00 代签 · m00147 授权在案）→ 30 开工分支 `task/tech-graph-flow-resync`（自 master `c17e63b` 切出 · 基线钉锚落 invoke）
