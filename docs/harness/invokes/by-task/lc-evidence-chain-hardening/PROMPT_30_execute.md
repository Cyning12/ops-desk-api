# 可复制 Prompt · 30（含 40）· lc-evidence-chain-hardening

> **给谁**：30 子 agent（**不要**交回起草 SPEC 的原窗）。  
> **Open Folder**：本 worktree 根。  
> **00**：不实现 `app/`。闸表已 approved；`harness verify` 2026-08-17 PASS。

---

## 复制区（整段粘贴）

````text
你是 ops-desk-api 的 Harness 30（含 40 自检）。cwd 必须是本 worktree，不要用主仓 ops-desk-api/。

Open Folder
  当前 Cursor 工作区根（ops-desk-api-wt-lc-evidence-hardening）
分支
  task/lc-evidence-chain-hardening（相对 origin/master；禁止直推 master）

身份
- 实现 D1–D4 + pytest mock + 40 自检。
- 禁止改 app/ops/chat/graph.py 拓扑。
- 禁止升 freeze lc-evidence-http-v1。
- 禁止把 CE rerank_score 映射成 EXACT。
- 禁止改 timeout 为 60、build_chain 单例、lru_cache/Redis、接回 Graph、句边界截断、改 Web。
- 禁止改 docs/tasks/active/task_ops_sync_sender_migration.md 或其实现。
- 不要 commit、不要 push（维护者未授权）。

必读（先读再改码）
1. docs/tasks/active/task_lc_evidence_chain_hardening.md（人工闸表 + 验收 + failure_paths）
2. docs/spec/lc-evidence-chain/SPEC-lc-evidence-chain-hardening_v1.md
3. docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md
4. docs/harness/prompts/30-execute-code.md · 40-self-check.md
5. docs/standards/CODING_BACKEND_L2_v1_zh.md
6. app/llm/providers/siliconflow.py · bailian.py · base.py（complete 聚合）
7. app/ops/lc_evidence_chain/grader.py
8. app/ops/chat/nodes.py（complete_stream usage 先例，对照不要双计）
9. app/ops/tracing.py · update_current_generation_usage
10. tests/test_lc_evidence_chain.py · tests/test_lc_evidence_http.py · tests/test_llm_providers.py

【开工前 · 首输出 GATE_VERIFY】
读 task 人工闸表填表，再 npx @cyning/harness verify --target . --task docs/tasks/active/task_lc_evidence_chain_hardening.md
任一 blocks 30 的闸 pending → 零 diff 拒开工。
用户口头「开工」≠ 闸。

实现范围
D1 complete() 聚合 stream 时上报 Langfuse usage
- 仍返回 str；不要改 BaseProvider.complete 签名。
- 两 Provider 收成一处 helper（建议 BaseProviderImpl 方法）。
- 识别 LlmChunk.meta["usage"] 的 prompt_tokens / completion_tokens；构造 LlmUsage；调 update_current_generation_usage。
- 无 usage 帧：静默跳过，不抛。上报失败静默（对齐 tracing.py）。
- 纯 meta 帧（usage / 可能的 model.fallback）不要当正文；对齐 nodes.py：usage 帧 continue。
- 上报点只此一处；不要在 grade_llm/answer_llm 再报一次（Chat complete_stream 已自行上报，勿改 graph）。
- llm 模块表出边保持「—」：对 tracing 用函数内 lazy import，不要新增一级模块、不要改依赖方向列。

D2 grader LLM 异常 → grades=[] → decide_grade refuse；HTTP 200 不是 500
- 在 _grade_chunks_llm（或 grade_chunk）捕获 LlmProviderError 与其它完成期异常。
- 失败：error 日志；返回 grades=[]；可选 grade span metadata grade_failed=true（失败静默）。
- 不要把 retrieve/answer/embed 失败吞成 refuse；那些仍应让 ainvoke 抛错 → HTTP 500。
- 不新增 HTTP 必填字段。

D3 kept 按 relevance.level 降序（同档稳定排序）
- decide_grade 过滤后 sorted(kept, key=level, reverse=True)；Python 稳定排序。
- refuse 时 kept 仍为空。

D4 G-L1
- docs/_tech_graph/l1/01_modules.md：lc_evidence_chain / llm 备注补「complete 路径上报 usage；grader 故障 refuse」。
- ./scripts/graph-compile.sh 通过。

单测（mock，不连真 LLM/真库）
- tracing 开 + mock stream 带 usage：complete() 后 update_current_generation_usage 被调用且 tokens 与末帧一致。
- tracing 关：complete() 仍返回拼接文本；不上报或不抛。
- mock grader complete 抛 LlmProviderError：ainvoke_evidence_answer 返回 gate_action=refuse、空 evidence、拒答文案。
- 同一失败路径走 HTTP POST /api/ops/lc-evidence/invoke → 200 不是 500（不要只 mock 掉 ainvoke 返回 refuse；要证明异常被链内吞成定义态）。
- answer/retrieve 失败仍 500（可保留既有 test_invoke_upstream_failure_envelope）。
- decide_grade：同时 exact+relevant 时 exact 在前；同档保持原相对序。

验证命令（必须真跑）
- ruff check 触及路径
- pytest tests/test_llm_providers.py tests/test_lc_evidence_chain.py tests/test_lc_evidence_http.py
- git diff origin/master -- app/ops/chat/graph.py 必须为空
- ./scripts/graph-compile.sh
- npx @cyning/harness verify --target . --task docs/tasks/active/task_lc_evidence_chain_hardening.md

留档
- docs/harness/invokes/by-task/lc-evidence-chain-hardening/invoke_20260817_30_40_lc-evidence-chain-hardening.md
  （含 GATE_VERIFY 表、验证命令与退出码）
- 在 task 文末追加「### 自检结论（执行者）」并勾选已用命令验证的验收项。
- 不要改 task 范围/闸表/思考轮。不要改 reviews。

完成后交还 00：列变更文件、测试结果、graph.py diff 是否为空。不要 push。
````
