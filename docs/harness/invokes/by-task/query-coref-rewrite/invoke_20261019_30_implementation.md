# invoke · 30 实现 query-coref-rewrite（2026-10-19）

- **任务**：docs/tasks/active/task_query_coref_rewrite.md（D1–D4 · TC1–TC12 · HG-AUDIT-R1=approved）
- **分支/提交**：task/query-coref-rewrite @ 4b36b3b（自 d8b787d 切 · 9 文件 +694/-6）
- **授权链**：invoke_20261019_gate_sign_hg_audit_r1.md（维护者「授权00签收后续文档」→ 00 代签 HG-AUDIT-R1）

## GATE_VERIFY 实录
- `npx spec-wave verify` exit=2：闸扫描表 HG-AUDIT-R1=approved / HG-GRAPH-MODULES=approved（均可 30）；VERIFY: BLOCKED 系审查文机读启发式误报（命中「退回」字样，语境为「不构成退回理由」），审查文结论实为 pass/阻塞 0/锚点 26 处 0 漂移 → 以 task 闸表真值为准开工。

## 偏离与自选（均落此实录）
1. 分支自 d8b787d（docs/spec-followups-2026-10-19 尖端）切而非 master：task 文件真值在该尖端待合并，授权链 prompt 已记录此偏离。
2. QUERY_REWRITE_TIMEOUT_S=30.0 为 30 自选（task 未钉数值；summary 档先例 60s，重写为轻量调用取 30s）。
3. TC10 口径=01_modules.md lg_rag 行备注「仅增一句」→ 未动闸台账表（先例的台账回写本次不扩）。

## 实现（D1–D4）
- D1：app/ops/lg_rag/continuity.py impl 两装配分支（session_summary on/off）之前一次算出 `resolved_query = await maybe_rewrite_query(query, history_turns)`；末位 HumanMessage 与 recall_with_vector 统一吃 resolved_query（先重写后召回钉死）。
- D2：新模块 app/ops/lg_rag/query_rewrite.py——env LG_RAG_QUERY_REWRITE_ENABLED 默认关/非法值 warning 回退关（三件套仿 session_summary_enabled）；确定式三规则判非法（strip 空 / 含 \n·\r 拒多行 / >512 字符，恰 512 接受）；失败/超时/非法输出静默降级原文 + span query_rewrite_fallback=true；每请求至多一次调用；prompt 资产 lg_rag.query_rewrite.system（v1 · 无变量）。
- D3：落盘 persist_thread_turns 与 run.start payload.query 仍记原文（装配层以下零触碰）；span 只记 query_rewrite_applied(bool)+src/dst 长度，不记改写全文。
- D4：app/llm/model_catalog.py 三处同增——TASK_TYPES + 'rewrite'；TASK_TIER_MODELS 'rewrite': None（仿 summary 档）；TASK_TIER_FALLBACKS 'rewrite': ()。

## 红测先行实录
- 先写 tests/test_lg_rag_query_rewrite.py（38 例）→ 红测确认 ImportError: cannot import name 'query_rewrite' → 再实现 → 38/38 一次全绿。

## TC1–TC12 逐项
- TC1 默认关三模式逐元素零 diff：PASS（_FakeGraph 捕获 payload 与 assemble_graph_messages 基线 _shape 逐字节对拍 × basic/router/supervisor）。
- TC2 开+金样三类（指代/省略/时间锚定各≥2 + continue 场景共 7 条）：PASS（末位 HumanMessage==改写文；planner/aggregator 经捕获 user 条证实收改写文）。
- TC3 失败降级：PASS（span query_rewrite_fallback=true 且 query_rewrite_applied=false；异常/超时两路）。
- TC4 首轮无历史短路：PASS（LLM 调用计数==0 · 零 span 键）。
- TC5 落盘与 run.start 记原文：PASS（SSE 走 HTTP 全链：run.start payload.query==原文 + persist 桩实收原文；装配层消息已改写）。
- TC6 env 非法值：PASS（caplog 警告 'invalid LG_RAG_QUERY_REWRITE_ENABLED=%r; fallback to false' + 行为同关零 diff）。
- TC7 档键在册：PASS（source ∈ {default,env_tier,strategy_pack} · 无 unknown_task 告警 · OPS_LLM_TIER_REWRITE_MODEL→env_tier · TASK_TIER_FALLBACKS['rewrite']==()）。
- TC8 先重写后召回：PASS（recall_with_vector 实收==resolved_query · 调用序断言 rewrite 先于 recall）。
- TC9 非法输出三形态：PASS（空串/多行/>512 降级原文 · 恰 512 接受）。
- TC10 graph-compile：EXIT=0（9 graphs · freeze 零 diff · 增一句后复跑仍 EXIT=0）；01_modules.md lg_rag 行备注仅增一句。
- TC11 全量绿+ruff：ruff check app tests = All checks passed；pytest 见下「环境对拍」。
- TC12 旧测 9+1 装配面文件默认关保绿：PASS（含 test_session_summary.py off 对拍主簇等，全量内全绿）。

## 全量 pytest 环境对拍（关键证据）
- 本机 .env 泄漏（OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS / OPS_CAPABILITY_ALLOW_WRITE 等）致 16 项 capability/strategy 测试失败——干净基线 d8b787d 同 .env 环境复现同样失败（stash 实证），非本 diff 引入。
- CI 等价跑法（park .env）：分支 4 failed / 1901 passed / 1 skipped；基线 d8b787d 同法 4 failed / 1861 passed / 1 skipped——失败集逐名一致（test_hitl asyncpg · test_memory_vector_p1 embedder flaky · test_multi_replica_dualproc ×2，均需本地 PG/外部服务），本 diff 零新增失败、净增 40 项全绿（38 新测 + prompt 资产参数化 +2）。

## O1/O2 吸收实录
- O1：test_session_summary.py off 态对拍主簇实为 :89-229（非审查文原引行号）——TC1 对拍手法（_shape 逐字节 + monkeypatch 装配面 + _quiet_memory delenv）按实校正后沿用。
- O2：resolve_task_model source 全词表另含 explicit/rag_grader_model/tier_default——已知会；TC7 断言按 task 钉死的三值 {default,env_tier,strategy_pack} 未扩。

## residual_risks
- 真连 LLM 重写质量未实证（task 口径=全假 LLM 机断）；上线前建议金样真连抽查。
- rewrite 档默认 None → 走 settings.ops_llm_model；需独立模型时配 OPS_LLM_TIER_REWRITE_MODEL（_known_model_ids 校验）。
- 金样 7 条为中文三类场景；英文/混合语种未覆盖（非范围）。
- 本地全绿以 CI 等价跑法为准；本机 .env 泄漏 16 项预存失败留痕（建议另开任务治理 .env 泄入 os.environ，非本 task 范围）。