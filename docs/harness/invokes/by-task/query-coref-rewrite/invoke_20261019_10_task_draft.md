# Invoke：query-coref-rewrite · 10 任务起草（2026-10-19）

- **hat**：10-task · **task**：docs/tasks/active/task_query_coref_rewrite.md（draft · HG-AUDIT-R1=**pending**）
- **建议序**：1/5（query-coref-rewrite → memory-injection-consumer → scenario-stage-rewire → delegation-naming-boundary → tech-graph-flow-resync）
- **分支**：当前 `docs/spec-followups-2026-10-19`（文档线 · 已核 `git branch --show-current`）；`task/query-coref-rewrite` **未切**，30 开工前按 task 文件自 master 切出
- **写入面**：仅 task 文件 + 本 invoke（两处分）；零 `app/` / `tests/` 改码 · 零 git 分支操作

## 一、签收与审查依据

| 依据 | 实录 |
|------|------|
| SPEC 签收 | `docs/spec/query-coref-rewrite/SPEC-query-coref-rewrite_v0.md` 状态行：`signed`（**HG-SPEC-SIGNOFF=approved · 2026-10-19 维护者会话签收** · 20-spec-audit R1 pass）· §9 修订记录 2026-10-19 行同载 |
| 审查文结论 | `docs/harness/reviews/spec_query-coref-rewrite_audit_R1_20261019.md`：**pass（通过）** · 14 处代码锚点 read/grep 实测全一致（0 漂移）· 阻塞项 0 · 附 3 条非阻塞观察（N1 rewrite 档 / N2 召回顺序 / N3 非问句判定）移交 10-task |
| 下游链 | HG-SPEC-SIGNOFF=approved → 00 出 task（本棒）→ 20-task-audit → HG-AUDIT-R1 → 30（SPEC 头「下游」行） |

## 二、N1–N3 吸收位置索引（task 文件行号）

| 观察 | 审查文原文坐标 | task 吸收位置 |
|------|---------------|---------------|
| **N1** `resolve_task_model('rewrite')` 档键缺失走 unknown_task 告警 | 审查文 §4.1（`model_catalog.py:123-132` 实测仅 answer/grader/extract/structured/summary · :156-158 unknown_task 分支） | task :57（范围引言）· **:88-93（D4 节全文：TASK_TYPES :119 / TASK_TIER_MODELS :123-132 增 `"rewrite": None` 仿 summary 档先例 / TASK_TIER_FALLBACKS :215-223 增空 tuple）** · :127（FP-8）· :144（TC7）· :200（R1 轮）· :206（R2 轮） |
| **N2** 重写与记忆向量召回（`continuity.py:454-457` `recall_with_vector` 吃 query）先后顺序 SPEC 未钉死 | 审查文 §4.2 | task :59（D1 节标题）· **:64（N2 顺序钉死段：先重写后召回 · resolved_query 统一供末位消息与召回 · 含裁定理由）** · :109（非范围：禁颠倒）· :128（FP-9）· :145（TC8 调用序+入参断言）· :186（R1 residual 挂账→R2 裁定）· :204（R2 轮裁定理由） |
| **N3** 「明显非问句」启发式需确定式判定规则 | 审查文 §4.3 | task :68（D2 节标题）· **:73-77（N3 确定式三规则：strip 空串 / 含换行拒多行不截首行 / >512 字符；不以问号结尾作判据；30 不得另加启发式）** · :129（FP-10）· :146（TC9 三形态注入 + 恰 512 边界闭区间口径）· :205（R2 轮裁定理由） |

## 三、亲读复核实录（起草前真读，不全信审查文转述）

| 锚点 | 实录 |
|------|------|
| `app/llm/model_catalog.py:110-186` | 亲读：:119 `TASK_TYPES=("answer","grader","extract","structured","summary")` 确无 rewrite；:123-132 `TASK_TIER_MODELS` 五键，summary 档 :128-131 注释先例（默认 None 不落档 · 灰度期 env 调档零改码）；:156-158 unknown task → warning + `(None,"unknown_task")`；:183-186 档默认 None → `(None,"default")`；env 覆盖口 `OPS_LLM_TIER_<TASK>_MODEL` :160-165 |
| `model_catalog.py:215-243` | `TASK_TIER_FALLBACKS` 五档（summary=() 先例 :222）；`resolve_fallback_chain` :239 以 `TASK_TYPES` 判未知档 → D4 须三处同增（TASK_TYPES/TASK_TIER_MODELS/TASK_TIER_FALLBACKS），缺一则 fallback 链解析仍告警 |
| `app/ops/lg_rag/continuity.py:380-514` | 亲读 impl 结构：:428-441 摘要/普通两分支 → 均归 `_assemble_messages_from_compressed(query, ...)`（:398 · 末位追加 :97）；:443-481 记忆事实注入（:454-457 `recall_with_vector(tenant, user, query, ...)` 吃 `query` 变量）；:483-514 情景召回。N2 钉死：重写须在 :428 两分支之前一次算出，召回与末位消息统一吃 resolved_query |
| `continuity.py:147-162` | `session_summary_enabled` 开关先例亲读：strip/lower · 非法值 warning+回退 false · off 态逐字节一致对拍钉死——D2 env 解析仿此 |
| `app/llm/budget.py:202/:269` | grep 实证：任务级计数按 `TASK_TYPES` 键记账（task_tokens 限额默认 0=不限）——D4 增键后预算计数自动覆盖，行为零 diff 由 30 实证 |
| HG-GRAPH-MODULES 真值 | `docs/_tech_graph/l1/01_modules.md:63-128` 闸登记表在册 approved（lg_rag 行 :65 起）；graph_change_layer=none 预期不再签，沿用在册状态 |
| tests 装配面枚举（TC12） | grep `assemble_graph_messages|recall_with_vector|_assemble_messages_from_compressed` 命中：test_lg_rag_session_continuity.py · test_session_summary.py · test_memory_injection.py · test_memory_vector_p1.py · test_memory_episode_recall.py · test_input_isolation_wiring.py · tests/eval/test_input_isolation.py · test_memory_extract_p1.py · test_memory_service_db.py——默认关保证全保绿，已入 TC12 枚举 |

## 四、产出与闸态

- task 草稿：`docs/tasks/active/task_query_coref_rewrite.md`（D1–D4 · 非范围九条（SPEC 六条原样 + task 级三条）· FP-1~FP-11 · TC1–TC12 · R0–R5 思考轮 actual_last_round=R5 · 自检结论五行）
- 人工闸表：HG-SPEC-SIGNOFF=approved（2026-10-19 维护者）· **HG-AUDIT-R1=pending（仅维护者可签 · 00/AI 不可代签 · 签前 30 拒改码）** · HG-GRAPH-MODULES=approved（在册 · none 预期不再签）
- test_strategy=required · graph_change_layer=none · review_hat=20 · invoke_retention_profile=default（10,20,30,40）
- 默认分支 `task/query-coref-rewrite` 未切（30 开工前自 master 切出）；git 零操作（仅只读 branch --show-current）
- 下一棒：20-task-audit R1 → 维护者签 HG-AUDIT-R1 → 30（红测先行）
