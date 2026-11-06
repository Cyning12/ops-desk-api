# Invoke · 40 帽 · 复跑销项（fix-planner-args-schema）

| 项 | 内容 |
|----|------|
| **帽** | 40-verify · **日期** 2026-11-06 |
| **task** | `docs/tasks/done/task_fix_planner_args_schema.md`（本棒归档） |
| **分支** | `agent/planner-args-fix-task-0796db4a2434`（reset 自 origin/master `36ef90d` = PR #349 squash 合入点 · 40 全程零仓内码改动 · 独立复跑在 `/tmp/verify40-planner` worktree @ `36ef90d` · 事后已拆） |
| **核验对象** | PR #349 全量 diff（`git diff 6533d44..36ef90d` · 11 文件）+ master 活链实测（delegation off） |
| **依据** | issue #339 维护者 comment `6675685940`（40 复跑销项令 · 依据 2026-11-06 08:48 授权 · 全绿关账 / 仍红停下报 · 不许偏差绕过） |
| **结论** | **机制面 PASS + live 真落笔达成（主结论）**：独立复跑全绿（新测 7 / 关联回归 416 / 全量 2075 零新增红 · verify 四闸 PASS · 红线对拍零命中）+ live 免 shim 全链**八段真落笔不再撞 `args_schema_invalid`**（`ops_capability_notes` 真落笔落行 · issue #329/#334/#335 偏差②×3 复现登记实质销项）——偏差①（replan 空规划 · V4-Pro 模型层噪点）如实登记，不阻塞 |

---

## 1. 闸态 verify（worktree @ `36ef90d` 实跑）✅

`npx spec-wave@3.5.0 verify --target . --task docs/tasks/active/task_fix_planner_args_schema.md` → **VERIFY: PASS** · 四闸 approved（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES none 口径 / HG-PLANNER-ARGS-DESIGN 案②）。

## 2. 红线对拍（`git diff --name-only 6533d44..36ef90d`）✅

- delta 恰 11 文件：码面 `nodes.py::_format_capability_catalog`（目录块注入 args_schema 单函数）+ prompt 资产 md ×2（v2→v3）+ 新测 `test_fix_planner_args_schema.py`（+544）；文档面 task 档 + 20-R1 审查文 + 10/20/30 invoke；旧测唯三版本常量适配（`test_prompt_assets` / `test_prompt_assembly` / `test_prompt_packs` · 收紧式非放宽）——全落 30 签认承载面；
- **红线零命中**：`capability/gateway.py` / `schema_validate.py` / `event_store` / `sse_*` / `hitl/**` / `resume.py` / `router.py` 零 diff（substring 误报已甄别：命中的 `test_prompt_assembly`/`assets` 文件名含 "sse" 子串 · 非 SSE 面）· gateway fail-closed 未放宽（30 fail-closed 承接组实证承继）。

## 3. 测试独立复跑（不采信 30 自报 · `/tmp/verify40-planner` @ `36ef90d`）✅

- **新测 7 枚**：`pytest tests/test_fix_planner_args_schema.py` → **7 passed**（负样本红→绿端到端 ×1 · fail-closed 承接 ×1 · legacy 对拍 ×1 · 目录块单测 ×3 · 提示词真装配断言 ×1）；
- **关联回归 20 文件**：`pytest test_fix_planner_args_schema test_prompt_assets test_prompt_assembly test_prompt_packs test_capability_gateway test_capability_harness_cli test_capability_lookups test_capability_idempotency test_capability_http_adapter test_capability_manifest_http test_capability_reversibility test_capability_persistence_db test_stage_w_write_expand test_write_approval_gate test_hitl_approval_consumption test_lg_rag_supervisor_capability_catalog test_supervisor_budget test_supervisor_parallel_join test_supervisor_replan_error_feedback test_hitl_approved_replan_quality` → **416 passed · 1 skipped**（零适配）；
- **全量**：`pytest tests` → **2075 passed · 4 failed**——4 failed 与 #349 前各基线逐枚同形（diff-whitelist ×2 / embedder env ×1 / dualproc env ×1）· **零新增红**；
- 复跑环境注记：worktree 无独立 venv，复用主 checkout `.venv`（deps 同集）；本地真 PG `opsdesk_test`（docker db 容器在册）。

## 4. live 免 shim 全链实测（八段 · delegation OFF · 修复被修面）

**环境**：本机 uvicorn :8014 @ `/tmp/verify40-planner`（`36ef90d`）+ PG `opsdesk_test`（密码 ops/ops_password）；env 前置：`DATABASE_URL→opsdesk_test` + `OPS_HITL_PERSISTENCE=db` + `OPS_CAPABILITY_PERSISTENCE=db` + `OPS_CAPABILITY_EXTRA_MANIFESTS=<abs>/ops.write.v1.yaml` + `OPS_CAPABILITY_ALLOW_WRITE_TAGS=run_note` + `OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS=ops.write.run_note` + **`LG_RAG_DELEGATION_TOKEN_MODE=off`** + `LG_RAG_HTTP_CHECKPOINTER=postgres` + supervisor 模型 `deepseek-ai/DeepSeek-V4-Pro`（`LG_RAG_ROUTER_MODEL` · 承 #334 偏差①先例选型）；invite cookie 会话（`pl40-tester`/maintainer）；数据前缀 `pl40`（事后已清理 · 零残留实证）。

| 段 | 结果 | 证据摘录（服务端日志 / 库面 · run `7ecfe9d96cef4ca1a7e1bcd81893fde2`） |
|----|------|----------|
| ① catalog 可见性 | ✅ | `visible_ids` 6 枚含 `ops.write.run_note`（`GET /capability/mine` 实证） |
| ② plans 含写 tool → 挂起 | ✅ | `capability_write_hitl_required {subtask_id: …:1, tool: ops.write.run_note}` → `hitl.waiting` + `done{status:waiting_approval}`；**`write_intent.args_summary` = 结构化对象形态** `{"run_id": "pl40", "note": "…", "request_id": "pl40-note-test-001"}`（pre-fix 为 string-args 拦截形态） |
| ③ pending 可见 | ✅ | `GET /hitl/pending` 列出 `hitl_deb00fa4a8104840be45`（owner 过滤生效） |
| ④ decide(approved) | ✅ | HTTP 200 · `decision_by=pl40-tester`；**重复 decide → 409**「申请已是 approved，不接受重复决定」live 实证 |
| ⑤ resume 受理 | ✅ | `resume={status:accepted}` 异步单飞 · approved=['…:1']；**重复 resume → 409**「该申请的恢复正在执行中，待沉降后再试」（写窗）live 实证 |
| ⑥ replan | ⚠️ 偏差① | `hitl.resumed` 帧达成；但 supervisor replan 返回空 `{"subtasks": []}`（11:15:02）→ 既有 fail-closed 灾备降级单 rag（主 .env `LG_RAG_SUPERVISOR_PLAN_ON_FAIL=single_rag`）收终态——见 §5 偏差①登记 |
| ⑦ **消费命中（免 shim 修复核心 live 实证）** | ✅ | `capability_write_approval_consumed {approval_id: hitl_deb00fa4a8104840be45, capability_id: ops.write.run_note, decision_by: pl40-tester, subtask_id: …:1, ttl_remaining_seconds: 3566}`（11:15:02.888 · **全链唯一消费台账**）→ 执行放行（无 fail-closed 再拦） |
| ⑧ **真落笔（issue #339 销项核心 live 实证 · 主结论证据）** | ✅ | `ops_capability_notes` 落行（11:15:02.893 · 消费后 5ms）：`note="真落笔验证，args_schema 销项测试便签"` · `approval_id=hitl_deb00fa4a…`（审批串链）· `subtask_id=…:1`（派发串链）· `idempotency_key=pl40-note-test-001`（幂等串链）· `tenant_id=ops-desk-pilot`——**不再撞 `args_schema_invalid`**（pre-fix 永久拦截面 · issue #329 run `5bc63c8b…`/`f193a5b9…` 与 #334 偏差② 同源形态销项）；补充帧证据：`subtask.progress` 中 planner `input` 为自然语言意图摘要（非 pre-fix JSON 串）· args 结构化透传 |
| 收口 | ✅ | `done{status:resumed, latency_ms:…}`（seq 19）+ `HITL 恢复完成 request=hitl_deb00fa4a… approved=['…:1'] replay=…:19`（11:18:23） |

## 5. 偏差登记

**偏差①（环境噪点 · 模型层 · 同源 #334 偏差①）**：resume 后 supervisor replan（V4-Pro）返回空 `{"subtasks": []}`（一轮采样）→ 既有 fail-closed 灾备降级单 rag 收终态。处置口径承 #334 偏差①（模型层环境性 · fail-closed 行为本身正确 · 非仓码语义）；**不阻塞销项**——真落笔（⑧）在降级前已达成，降级仅影响回答收尾形态（单 rag 空证据回答）。若维护者要求 replan 非空采样，可复走 #334 显式引导两步任务口径另行补跑（本 40 令未含该要求）。

**偏差②（口径登记）**：live 全程 delegation **off**（专验本修复被修面「planner args → gateway schema → 真落笔」链；#334 delegation on 面已由该单 40 实证承继，本修复对两形态同构——args 形态修复在 planner/gateway 链，与 delegation 闸正交）。

## 6. 终态工程面

| 项 | 结果 |
|---|---|
| 40 全程仓内码改动 | **零**（仅本 invoke + 关账文档入 PR） |
| 测试数据清理 | notes 1 / run_events 19 / hitl 1 / invite 1 / sessions 1 / checkpoints+blobs+writes 107 行 / user 1 全 DELETE（`leftover: 0` 逐项实证）· uvicorn :8014 已停 · worktree `/tmp/verify40-planner` 已拆 |

## FAIL 判定扫描

30 无造假：红线零 diff 对拍成立 / 新测独立复跑全绿 / 全量零新增红 / verify PASS / **live 真落笔四串链（approval/subtask/幂等键/tenant）实证销项**。偏差①如实登记，不阻塞（主结论达成面 = ⑧真落笔 + 全量零新增红 + 红线零破）。

## 销项声明

- **issue #339 缺陷本体销项**：live 八段真落笔不再撞 `args_schema_invalid`（pre-fix 两轮一致永久拦截面）；
- **同源偏差链销项**：issue #329 40 偏差② / issue #334 40 偏差② / issue #335 偏差②（planner string-args ×3 复现登记）**实质销项**——本修复即三单登记的预期另波（#339）；
- issue #339 关 issue 由维护者执行（承关账链惯例）。

## 环境注记

- live 证据文件（ephemeral · 摘录已嵌上文）：/tmp/planner40_sse1.log · /tmp/planner40_server.log · /tmp/planner40_cookies.txt（不入仓 · 事后可弃）；
- 本机代理 env 已按先例剔除（httpx bracketed IPv6 no_proxy 坑 · 承 fix-no-proxy 先例）；主 checkout `.env` 仅 live 用（LLM 凭据 · 40 档不提交）；
- langfuse/otel exporter 403（dev 环境键过期面）为既有环境噪点，与本修复无关，照登。
