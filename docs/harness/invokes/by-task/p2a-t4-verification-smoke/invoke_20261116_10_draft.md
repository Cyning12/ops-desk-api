# invoke_20261116_10_draft · p2a-t4-verification-smoke（10-task 落卡）

## 输入

- lead 委派（exec-p2a-t4）：验证假设「Agent 读面板数据出结论」冒烟 + 验收落盘（issue #23 m03064 夜间授权 · 不中途问问题）。
- 设计真源：workspace 08-p2a-tools-design.md §6（验收双件制）/ §7 T4 行 / §8（禁承载）。

## 勘察定论（R0）

1. **端点现实**：设计写 /api/ops/chat/stream，仓内已 410 下线（app/ops/chat/router.py:56 迁移指针）→ 冒烟路径 = POST /api/ops/lg-rag/stream，StreamRequest{query, mode=supervisor}（app/ops/lg_rag/router.py:91-98 · :455 须登录 · 响应头带 thread/run id）。【偏差登记点①】
2. **基线**：master 尖 96ccf902 五键 blank 全量 2150 passed / 16 failed / 2 skipped（286s）；16 红承 T1/T2 定论为 .env 污染红——抽查三枚（test_lg_rag_supervisor_capability_catalog.py::test_supervisor_invalid_tool_id_fails_closed · test_strategy_builder.py::test_get_candidate_unknown_key_fail_closed · test_lg_rag_multi.py::test_decompose_invalid_json_fails_closed）加 blank LG_RAG_SUPERVISOR_PLAN_ON_FAIL=/LG_RAG_DELEGATION_TOKEN_MODE=/OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS= 后 3 passed 复绿，因果证实。
3. **测试范式**：tests/test_lg_rag_supervisor_capability_catalog.py（261 行）mock LLM 范式逐行可复用；plan-JSON 形态 {subtasks:[{id,type:"tool",input,tool}]}；合法 id 保留（:238-261）/非法 fail-closed（:115-146）既有覆盖。
4. **九枚 supervisor 面**：strategy/config.py CAPABILITY_ALLOWLIST_BY_KEY["supervisor"] = utc_now_iso, mock_get_issue_status, mock_get_deploy_info, get_issue_by_number, get_pr_by_number, query_issues, query_pull_requests, get_overview, graph_snapshot。
5. **seed 面**：dev 库 opsdesk 业务表全 0 行；OpsIssue/OpsPullRequest/OpsSyncRun/OpsScanSnapshot/OpsGraphSnapshot 非空字段已清点（models.py）；ops_repos 需先建行（FK）。ci_status 已知值 success|failure|pending（GitHub 惯例 · manifest description 在案）→ seed 用 failure，设计样例「failing」为描述性措辞【偏差登记点②·措辞对齐说明】。
6. **证据链**：Langfuse 真云已配（.env OPS_CHAT_TRACER=langfuse · jp.cloud.langfuse.com）→ (a) 可试 API 拉 tool_exec span（gateway.py _write_span_metadata payload 含 capability_id/ok/args_summary/tenant_id）；不可达则以 SSE 帧+既有 span 测试证据替代并登记。
7. **租户**：seed 与会话同 tenant ops-desk-pilot；面板端点 tenant 强制（issues.py:47-51）与 capability tenant_scoped 口径一致。

## 产出

- docs/tasks/active/task_p2a_t4_verification_smoke.md（含人工闸三行 approved · R0-R5 思考轮 · actual_last_round=R5）
- docs/harness/reviews/task_p2a_t4_verification_smoke_audit_R1_20261116.md（20-R1 · 结论 GO · 终轮签收）
- docs/harness/audit_gates/registry.yaml 追加 waves entry（status=active · base=96ccf902 · allowed_app_files=[] · banned_prefixes 含 app/ 全禁）

## 闸核验

- spec-wave task lint：PASS（W3 自检结论占位 warn-only · draft 期合法）
- invoke 留档：default 集合 {10,30,40}

## 下一步

30 实施：tests/test_capability_supervisor_smoke_assertions.py 新文件（四类断言）→ capability 电池十一件 + 全量对拍 → seed + 四样例真 LLM 冒烟 → 40 验收落盘。
