# Task Audit R1：hitl-ops-runbook · 退回 10-task

> **hat_id**：20-task-audit  
> **task**：`docs/tasks/active/task_hitl_ops_runbook.md`（slug: hitl_ops_runbook）  
> **日期**：2026-10-17 · 审查人：20-task-audit（00 委派 · 五档批量 R1 之一）  
> **分支**：master（本帽零 git 操作 · 未切分支 · 未 commit · 未改 task 正文/人工闸表/任何仓内文件）  
> **task lint**：本帽亲跑 `npx --yes spec-wave task lint --file docs/tasks/active/task_hitl_ops_runbook.md` → **LINT: PASS**（仅 W3 自检结论占位 · draft 期合法；lint 不查思考轮占位回填）  
> **required_invoke_hats**：`10 → 20 → 人签 HG-AUDIT-R1 → 40`（含 20）· 本轮已落 20 invoke：`docs/harness/invokes/by-task/hitl-ops-runbook/invoke_20261017_20_task_audit_r1.md`

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **退回 10-task** · 1 项内容阻塞（B-1 思考轮控制表 R0–R5 全占位未闭合） |
| **流程闸** | HG-AUDIT-R1 **approved**（2026-10-17 维护者授权 00 代录 · 授权言「授权00签收后续文档，开始下面的任务」(m00238) · 20 R1 书面审经授权豁免 · 本帽照登事实 · 无权推翻亦无权再签）；HG-GRAPH-MODULES n/a · HG-PILOT-OPSDESK-GLAYER n/a（均与 graph_change_layer=none 一致） |
| **30/40 授权** | 本 task orchestration 无 30 棒（10 → 20 → 人签 → 40 执行+复走）；**内容阻塞未清零前 40 必须拒开工** · 本文不附 40 Prompt |

**总评**：范围四项（runbook 五必备节 / 阶段 5 复走 / FP-1 钉案 / F1F2 交接锚点）证据扎实、锚点全部亲读命中、TC-1..9 可机断、failure_paths 完整——**均不构成退回理由**。唯思考轮控制表 R0–R5 六行与正文六节全为「（执行者回填）」占位，设计思考未记录，20 无从审 → B-1 退回 10-task 回填。

## 审查核对

| # | 审查点 | 结论 |
|---|--------|------|
| 1 | 码面锚点（亲读） | **通过**。hitl 端点族 `app/ops/hitl/router.py` :76 runtime / :161 pending / :185 decide / :530 resume ✓；`persistence.py:22` ENV_PERSISTENCE · :40 mode=db→DbHitlStore · :54-57 NullHitlStore+「不可上生产」告警 ✓；`app/ops/lg_rag/router.py:384-420` replay 409 + Retry-After:2 + 沉降零 diff ✓；判定谓词 `run_stream_closed` 在 `app/ops/lg_rag/event_store.py:132`（router 锚点指向 :384-420 段，谓词本体在 event_store · 见 N-4）✓；`docker-compose.yml:68` OPS_HITL_PERSISTENCE 透传 ✓ |
| 2 | 依赖档存在性 | **通过**。SPEC-chat-history-hitl-ux_v0.md · 20261009/20261010 两份验收 · task_compose_hitl_persistence_env · task_lg_rag_sse_run_worker · close_hitl_resume_replay_contract_20261017 · close_lg_rag_sse_run_worker_co_disconnect_20261017 · RUNBOOK_delegation_token_observe_local_v1_zh 全在 ✓ |
| 3 | 验收标准可机断 | **通过**。TC-1 grep 节名 ≥5 · TC-2/3 curl grep 双命中 · TC-4 jq 三断言（含 has("model")|not 与 FP-1 钉案互锁）· TC-5 证据落盘位 · TC-6/7 grep 三要素 · TC-8 lint PASS · TC-9 零 app/ diff |
| 4 | failure_paths | **通过**。FP-1..7 覆盖 lint E6/旧镜像/5432 抢占/409 退避/resume 并发守卫/持久化缺省/复走缺口停派，承两份验收坑位如实 |
| 5 | 非范围 | **通过**。零 app/ 改 · 前端仅锚点 · compose 只引用 · HMAC 对接面与 auto 运维化另立 —— 划界合理 |
| 6 | K7 旧测 grep 影响面 | **n/a**（纯文档 + 复走 · 零行为变更） |
| 7 | 思考轮审查 | **阻塞**（B-1，见下） |

## 阻塞项（内容 · 退回 10-task）

### B-1 · 思考轮控制表 R0–R5 全占位未闭合

- **现状**：task「思考轮控制表」R0–R5 六行结论全为「（执行者回填）」、early_stop 全 no、reason/residual 全占位；`actual_last_round` 为「（执行者回填）」；正文 R0–R5 六节亦全占位。
- **先例核查（本帽亲跑）**：全仓 `grep -l '（执行者回填）' docs/tasks/done/*.md docs/tasks/active/*.md` **仅命中本档**；task 自引先例 `task_compose_hitl_persistence_env`（R3 early_stop 实填理由闭合）与 `task_lg_rag_sse_run_worker`（R0–R5 全实填）思考轮均实填闭合——占位非本仓认可形态。
- **性质**：思考轮是 **10-task 起草面**设计思考的记录。本 task 存在真实设计决策须留痕：runbook 五必备节的取舍、HMAC 对接面排除理由、auto resume 仅作附录的裁定、F2 复走边界（为何不顺手修 · FP-7 停派）、坑位节收录范围。这些不由执行帽 40 倒填——40 回填的是自检结论，不是设计轮。占位 = 设计思考未发生或未记录，R 轮审无从闭合。
- **处置**：退回 10-task 实填 R0–R5（控制表结论 + early_stop 理由/风险 + actual_last_round + 正文六节）。本 task 含复走实证面与多坑位设计决策，chore 轨 W4「无思考轮节」豁免**不适用**——既已开节，须实填闭合。

## 非阻塞（10 回填 B-1 时可顺手 · 单独不退回）

- **N-1**：人工闸表缺 **HG-TASK-DRAFT** 行（同批四档兄弟 task 均有该行；建议补齐使闸面口径一致）。
- **N-2**：`test_strategy` 值「人工 checklist 型」为自由文本（lint 未拦；兄弟档用 `required`/`n/a` 枚举）；`test_strategy_note` 已补可机断口径，照登不闸。
- **N-3**：修订记录「人工闸全 pending 待维护者签」系起草时史实，与现行 approved 代录并存——历史记录不回填，照登。
- **N-4**：范围 F1② 写「判定谓词 run_stream_closed（app/ops/lg_rag/router.py:384-420）」；谓词本体实在 `event_store.py:132`（router 段调用 `refuse_in_flight` 路径）。事实正确、文件归属可更准，建议回填时补谓词本体锚点。

## 回填清单（给 10-task · 只改 task）

- [ ] **思考轮控制表**：R0–R5 实填（每轮结论一句 + early_stop 判定与理由 + residual_risks）+ `actual_last_round`
- [ ] **R0–R5 正文六节**：问题重述 / 方案发散 / 方案收敛 / 风险审查 / 验收对齐 / 终审 实填（设计决策留痕：HMAC 排除 · auto 附录化 · FP-7 停派 · 坑位收录边界）
- [ ] （建议 · N-1）人工闸表补 HG-TASK-DRAFT 行
- [ ] （建议 · N-4）F1② 补 `event_store.py:132` 谓词本体锚点
- [ ] 不改验收 / failure_paths / 范围实质内容迁就思考轮
- [ ] 回填后重跑 `npx --yes spec-wave task lint --file docs/tasks/active/task_hitl_ops_runbook.md` → 送 20-task-audit R+1
- [ ] **禁止**在 R+1 通过前下发 40

## 维护者知悉（20 后 · 40 前）

- [ ] 已读 R1 审查结论（本轮退回 10-task · B-1 内容未过 · 待 R+1）
- [ ] HG-AUDIT-R1 现 approved 系 2026-10-17 维护者授权 00 代录（m00238 · R1 书面审豁免）——本帽照登事实、无权推翻；惟**内容阻塞未清零前 40 必须拒开工**（内容面以审查结论为准）
- [ ] 10 回填 + R+1 零内容阻塞后，再下发 40（执行 + 验收复走）

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-17 | 20 R1 书面审：码面锚点全亲读命中（端点族/persistence/replay 409/run_stream_closed/compose:68）· 依赖档全在 · TC-1..9 可机断 · lint 亲跑 PASS · **B-1 思考轮 R0–R5 全占位（全仓 grep 零先例）→ 退回 10-task** · N-1..N-4 照登 · HG-AUDIT-R1 approved 系 00 代录事实照登（未代签）· 不附 40 Prompt |
