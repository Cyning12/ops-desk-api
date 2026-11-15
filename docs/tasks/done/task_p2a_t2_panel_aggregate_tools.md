---
title: P2a-T2 面板聚合工具 get_overview / graph_snapshot
---

# task_p2a_t2_panel_aggregate_tools

> **状态**：`closed`（2026-11-16 落卡 · 2026-11-16 关账 · PR #404 squash merge 94f5ba87）

- 关联：issue Cyning12/ops-desk-workspace#23（m03064 夜间授权窗口）· 设计真源 08-p2a-tools-design.md（§1.4 / §1.5 / §1.6 / §2 / §5 / §7 T2 行 / §8）

## Harness 元信息

| 键 | 值 |
|---|---|
| **task_slug** | p2a-t2-panel-aggregate-tools |
| **wiki_delta** | 无（WikiTrack 零改动） |
| graph_change_layer | G-L1 备注级（capability 行回写 · 不新增一级模块 · 不增 implementedBy） |
| review_hat | 20 |
| base | 8af02c4a（T1 CLOSE merge sha） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-AUDIT-R1 | approved | 30 | 维护者夜间授权窗口（issue Cyning12/ops-desk-workspace#23 m03064）+ 08 设计终稿 §7 T2 行；R1 审查文 docs/harness/reviews/task_p2a_t2_panel_aggregate_tools_audit_R1_20261116.md 结论 GO |
| HG-GRAPH-MODULES | approved | 30 | 同上授权；不新增一级模块 · 不增 implementedBy；01_modules.md capability 行已含 P2a-T1 备注行（docs/_tech_graph/l1/01_modules.md:34），T2 回写承 :135 先例于 CLOSE 波补 P2a-T2 备注与签收行 |
| HG-PILOT-OPSDESK-GLAYER | approved | 30 | 同上授权；本单不触物理分层试点面 |

## 背景

P2a（面板工具化）第二波。T1 已落面板列表双工具 query_issues/query_pull_requests（builtin.v1.yaml 5→7 · supervisor allowlist +2 · span tenant_id · mock 收窄）。T2 落聚合面双工具：get_overview（对齐 overview.py:169-180 口径）与 graph_snapshot（对齐 graph.py 外壳 + §1.5 视图/截断/fail-visible 语义）。

## 范围

1. app/ops/capability/lookups.py 增两枚 adapter：
   - get_overview：无参数（args_schema type:object · properties:{} · additionalProperties:false）；返回逐键对齐 overview.py 端点口径（cycle_time/review_time/issue_throughput/as_of/sync_status/sync_run/scan_snapshot/trend · trend 30 天全量零填）；scan_snapshot.parsed_summary JSON 序列化 >2000 字符截断为 {keys,truncated:true}；as_of 必带；空数据 null 逐键声明进 output_schema；description 禁「实时」字样；tenant_scoped:true（派生指标带 tenant 谓词 · sync_run/scan_snapshot 全局段 docstring 钉口径）。
   - graph_snapshot：args view enum[summary(默认)/modules/full] + module 可选；统一外壳 {view,scope:"global_repo",repo_id,created_at,summary{node_count,edge_count,module_count},module_matrix?|截断,payload?|截断,truncated:bool}；上限 summary 4000 / modules 8000 / full 12000 字符；超出按 nodes→edges 顺序截断 + truncated:true + totals；过滤优先于截断；fail-visible：module 过滤键缺失/结构漂移 → warning:"module_filter_no_match" + 未过滤摘要（不静默空集）；截断抽独立纯函数；tenant_scoped:false 但照 T1 惯例处理 ctx（None/空放行）。
2. manifests/builtin.v1.yaml +2（全字段含 output_schema · tags panel+域+readonly · args_schema 无 per-prop description · 使用引导全落 description）+ defaults.py 回退面逐字段对齐 + strategy/config.py supervisor allowlist +2。
3. 测试（08 §5）：manifest count 7→9 全字段钉死；双层范式（InMemory 恒跑含 tenant_scope_missing 负样本/graph 无 ctx 放行/截断纯函数单测 + 真 PG _DB_MARK 双租户 seed：全局口径同值/截断标志/空数据 null 声明）；fixture 含 budget.reset()/circuit.reset()；warning:"module_filter_no_match" 实证用例；catalog≤6000 断言更新。
4. 存量锚推进 7→9：test_capability_manifest.py / test_capability_panel_tools.py / test_capability_testing_write.py / test_ops_write_catalog_reconcile.py / test_stage_w_write_expand.py / test_strategy_env_extra_candidates.py。

## 非范围

承 08 §8：面板端点（overview.py/graph.py）改动、adapter 白名单扩容（manifest.py:64-66 不扩）、lg_rag 图/nodes.py 改动、SSE 新帧、新依赖、新 DDL/索引、when_not_to_use 填充、mock 退役、budget/circuit 默认值、T1 已落的 span tenant_id 与 mock 收窄（不重复）。

## 失败路径

| 场景 | 行为 |
|---|---|
| tenant_scope_missing | tenant_scoped:true 两枚（query_* 既有 + get_overview）缺 ctx 租户 → LookupError("tenant_scope_missing")；graph_snapshot tenant_scoped:false 放行 |
| overview 空数据 | sync_run/scan_snapshot 无行 → 对应键 null（output_schema 逐键声明 nullable）· sync_status="idle" · trend 30 天零填 |
| parsed_summary 超 2000 | 截断为 {keys:[...],truncated:true}（序列化长度判定） |
| graph 无快照 | repo_id/created_at/summary 等 null · truncated:false · 不抛错 |
| module 过滤键缺失/结构漂移 | warning:"module_filter_no_match" + 未过滤摘要（fail-visible 不静默空集） |
| 视图超上限 | nodes→edges 顺序截断 + truncated:true + totals 如实 |
| schema_validate | 不校验 enum/min/max（既有事实 · R1 在案）；view 词表由 adapter 显式校验 |

## 验收标准

- [x] get_overview 返回形状逐键对齐 overview.py:169-180（InMemory + 真 PG 双层绿）
- [x] get_overview 空数据 null 逐键声明进 output_schema · as_of 必带 · description 无「实时」
- [x] graph_snapshot 三视图外壳/上限/截断语义全绿（含 totals 与 nodes→edges 顺序）
- [x] warning:"module_filter_no_match" 实证用例绿
- [x] tenant_scope_missing 负样本绿（get_overview）· graph 无 ctx 放行绿
- [x] manifest count 7→9 全字段钉死 · 六处存量锚推进全绿
- [x] catalog ≤6000 断言更新绿
- [x] 真 PG _DB_MARK 双层：双租户 seed 全局口径同值/截断标志/空数据 null 绿
- [x] ruff check app tests 绿 · CI 四绿
- [x] 零新 DDL/索引/依赖/路由/SSE 事件

### 自检结论

十条全过：capability 电池 150 passed 0 failed（五 env 键 blank · PG 用例 24 例零 skip）；全量套件 2148 passed · 余红 16 枚与 base 8af02c4a worktree 同子集逐名恒等（外部环境/.env 污染既有红 · CI 无 .env 为终裁 · PR #404 四绿实证）；脏树期 test_wave_gate_registry/test_tc8_diff_whitelist/test_episode_pattern_mine 红为在途面守卫语义提交后复绿；ruff · graph-compile · spec-wave lint/verify 全 PASS。偏差五项见实现备忘（when_to_use 承 T1 · V10 白名单 +nullable · 头注释纠 stale · 六锚推进 · EXTRA_MANIFESTS 污染面新发现）。

## 必读

- ../ops-desk-workspace/docs/01-scope/03-general-agent/08-p2a-tools-design.md（§1.4/§1.5/§1.6/§2/§5/§7/§8）
- app/ops/overview.py · app/ops/graph.py · app/ops/capability/lookups.py
- docs/tasks/done/task_p2a_t1_panel_list_tools.md（T1 模板与偏差先例）

## 思考轮控制

| 轮 | 结论 | early_stop |
|---|---|---|
| R0 勘察 | 见 invoke_20261116_10_draft.md 勘察定论 | false |
| R1 契约审查 | schema_validate 不校验 enum/min/max → view 词表 adapter 显式校验；when_to_use loader 必填（manifest.py:523-526）→ 填简短引导（承 T1 偏差先例） | false |
| R2 租户 | get_overview tenant_scoped:true（派生指标谓词 · 全局段 docstring 钉口径）；graph_snapshot tenant_scoped:false + scope:"global_repo" 常量 | false |
| R3 图谱 | 不新增一级模块 · 不增 implementedBy · capability 行备注 CLOSE 波回写 | false |
| R4 截断 | 独立纯函数；过滤优先于截断；fail-visible warning 不静默空集 | false |
| R5 早停 | 设计终稿即审计真源 · 验收全机断 · early_stop 成立 | true |

actual_last_round: R5

### R0

勘察定论见 invoke_20261116_10_draft.md：overview.py 端点口径可整段复用（聚合纯函数化重写 ORM 不复用端点）；graph payload 为 kimi-code 外部自由 dict（nodes/edges 为既有夹具形态）；manifest/defaults/allowlist/六处测试锚已清点。

### R1

契约审查：get_overview args 空对象钉死；graph_snapshot view 词表 adapter 显式校验（schema_validate 不校验 enum · 承 T1 R1 事实）；output_schema 空数据 null 逐键声明；description 禁「实时」。

### R2

租户裁定：get_overview tenant_scoped:true 强制 _tenant_from_ctx；sync_run/scan_snapshot 段全局无 tenant 列（W-fix-2 F13 口径 · docstring 钉死）；graph_snapshot tenant_scoped:false · ctx 照 T1 惯例（None 放行 · 有则透传不消费）。

### R3

图谱裁定：零新模块/边/implementedBy；01_modules.md capability 行备注与人签记录于 CLOSE 波回写（承 T1 :135 先例）。

### R4

截断裁定：截断为独立纯函数可单测；上限 summary 4000/modules 8000/full 12000；nodes→edges 顺序；truncated:true + totals；过滤优先于截断；module 过滤键缺失/结构漂移 fail-visible。

### R5

早停裁定：设计终稿（08）即审计真源，验收标准全部可机断，R5 early_stop 成立。

## 实现备忘

- app/ops/capability/lookups.py 追加 P2a-T2 段：get_overview/graph_snapshot 双 adapter + 纯函数群（_to_naive_utc/_median_days/_build_trend 镜像 overview.py——capability→api 无出边不跨模块 import · _clip_parsed_summary · _truncate_json_value · _truncate_graph_payload · _filter_payload_by_module）+ 常量（_PARSED_SUMMARY_LIMIT=2000 · _GRAPH_VIEW_LIMITS 4000/8000/12000 · MODULE_FILTER_NO_MATCH）。
- app/ops/capability/manifests/builtin.v1.yaml +2（九枚）· defaults.py +2 逐字段对齐 · strategy/config.py supervisor allowlist +2 · manifest.py V10 白名单 +nullable。
- 六处存量锚 7→9 + V10 参数化补 nullable 正负样本；tests/test_capability_panel_aggregate_tools.py 新建 24 例（InMemory 恒跑 + 真 PG _DB_MARK 双租户）。
- 偏差登记：① when_to_use loader 必填非空 → 填简短引导（承 T1 先例 · when_not_to_use 不填）；② V10 output_schema 白名单原仅 required/min_items/empty_is_suspicious（manifest.py:324）与设计 §1.4/§1.5「空数据 null 逐键声明进 output_schema」冲突 → 最小改动扩 nullable（同款非空 $ 路径列表校验 · result_contract 不消费纯声明面）· allowed_app_files 随扩 manifest.py；③ builtin.v1.yaml 头注释「五枚」stale（T1 遗留）顺手纠为「九枚」；④ 六处同性质 count 锚 7→9 既定后果推进（断言语义不动）；⑤ 本地 .env OPS_CAPABILITY_EXTRA_MANIFESTS 遮蔽 test_ops_write_catalog_reconcile.py::test_machine_three_layer_opening_gates（承 T1 定论 · CI 无 .env 为终裁 · blank 五键后绿）。

## 测试策略

- InMemory 恒跑（CI）：形状断言 · tenant_scope_missing 负样本 · graph 无 ctx 放行 · 截断纯函数单测 · warning 实证 · catalog ≤6000
- 真 PG _DB_MARK：双租户 seed · 全局口径同值 · 截断标志 · 空数据 null 声明
- 涉及 capability 套件先 blank 五键（OPS_HITL_PERSISTENCE= OPS_CAPABILITY_ALLOW_WRITE= OPS_CAPABILITY_ALLOW_WRITE_TAGS= OPS_CAPABILITY_PERSISTENCE= OPS_CAPABILITY_EXTRA_MANIFESTS= · 末者为 T2 新发现 .env 污染面）
- ruff check app tests

## 修订记录

- 2026-11-16 · 落卡（夜间授权窗口 · issue #23 m03064 + 08 §7 T2 行）
- 2026-11-16 · 30 实施 + 40 验收全绿（feat PR #404 squash merge 94f5ba87 · CI 四绿）· CLOSE 关账（registry status=closed 钉 wave_tip=94f5ba87 · 迁 done · 01_modules 回写）
