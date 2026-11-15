# invoke 10 · p2a-t2-panel-aggregate-tools · 落卡

## 内容

按 08-p2a-tools-design.md §7 T2 行落卡：get_overview（§1.4）+ graph_snapshot（§1.5）两枚聚合 adapter 进默认面（builtin.v1.yaml 7→9）+ supervisor allowlist +2 + 双层测试基座。task 档 docs/tasks/active/task_p2a_t2_panel_aggregate_tools.md · R1 审查文 docs/harness/reviews/task_p2a_t2_panel_aggregate_tools_audit_R1_20261116.md（GO）· registry N3 entry（base=8af02c4a）。

## 勘察定论（R0）

1. overview.py:67-181 端点口径可整段对齐：_CYCLE_REVIEW_WINDOW_DAYS=90 · _TREND_WINDOW_DAYS=30 · _median_days/_build_trend 纯函数可复用；adapter 重写 ORM 查询不复用端点（承 T1 谓词先例）。
2. sync_run=OpsSyncRun started_at desc limit 1（summary.get("issues"/"pulls")→records_issue/records_pr · 无行 sync_status="idle" sync_run=None）· scan_snapshot=OpsScanSnapshot created_at desc limit 1——全局无 tenant 列（W-fix-2 F13 口径）。
3. graph.py 外壳 {snapshot:payload,module_matrix,repo_id,created_at}；OpsGraphSnapshot.payload JSONB non-null 自由 dict（既有夹具形态 {"nodes":[],"edges":[]}）· module_matrix nullable · 取 created_at desc limit 1；repo_id UUID→str。
4. payload 结构为 kimi-code 外部自由 dict → module 过滤以 nodes 为 dict 列表且元素含 module 键为结构前提；键缺失/结构漂移 → fail-visible warning:"module_filter_no_match" + 未过滤摘要。
5. 截断纯函数：序列化 payload/module_matrix，超上限按 nodes→edges 顺序截断 + truncated:true + totals；视图上限 summary 4000/modules 8000/full 12000；get_overview parsed_summary >2000 → {keys,truncated:true}。
6. 锚点推进清单（7→9）六处：test_capability_manifest.py(_BUILTIN_IDS tuple + count==7) · test_capability_panel_tools.py(len==7) · test_capability_testing_write.py(_BUILTIN_IDS set + snap count==7) · test_ops_write_catalog_reconcile.py(count==7) · test_stage_w_write_expand.py(count==7) · test_strategy_env_extra_candidates.py(_SUPERVISOR_IDS + tc1 stripped 列表)；test_capability_domain_allowlist.py 用 >= 断言不需改。
7. CI（无 .env）是终裁：本地 .env 四键（OPS_HITL_PERSISTENCE 等）会遮蔽红绿，全量对拍须 blank 四键（T1 交接注意①②）。
