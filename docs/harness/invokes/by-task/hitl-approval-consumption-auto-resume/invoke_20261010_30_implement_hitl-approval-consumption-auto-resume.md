# Invoke：30 实现 hitl-approval-consumption-auto-resume（T2 · D5 批准后自动继续可配置面）

> **帽**：Harness 30（实现） · **task**：`docs/tasks/active/task_hitl_approval_consumption_auto_resume.md`
> **分支**：`task/hitl-approval-consumption-auto-resume`（worktree · base master `3f6a630` 含 T1 merge ✓）
> **开工**：2026-10-10 · 骨架先行 · 小段增量落盘

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | blocks_30 | 30可开工？ |
|---------------|--------------|-----------|------------|
| HG-TASK-DRAFT | approved | 20-R1, 30 | ✅ |
| HG-AUDIT-R1 | approved | 30 | ✅ |
| HG-GRAPH-MODULES | approved | — | ✅ |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | — |

- R1 审查文存在且内容 PASS（N-1~N-3 非阻塞）；pre-30 invoke 00/10/20 齐全
- `npx spec-wave verify --target . --task …` → **VERIFY: PASS · EXIT=0**
- T1 前置：HEAD=`3f6a630`（T1 merge PR #216）✓
- task 表 `git_branch` 字段已是 `task/hitl-approval-consumption-auto-resume`（:16 实证 · 00 合流裁定在案 · 无需再修）
- .env：worktree 原缺，已从主仓拷贝对齐（mode 口径随主仓）

---

## 30 裁定留痕（实操-E · run 终态谓词真源）

- **真源选择**：事件表 `ops_lg_rag_run_events` 终结帧——`error` 帧，或 `done` 帧且
  `payload.status != 'waiting_approval'`（缺省按 completed）→ 终态；`done{waiting_approval}`
  是挂起等待（恰是待恢复形态）排除；无帧=非终态。与 `history.run_terminal_status`
  同口径。SQL 形态：ORM `select(seq).where(run_id, or_(error, and_(done, coalesce(payload['status'],'completed') != 'waiting_approval'))).limit(1)`
  （`event_store.run_is_terminal` · 零新表/迁移）。红线守住：未读进程内存态 · 未以 checkpoint 存在性近似。
- **TTL 单一旋钮**：补偿扫描「未过 TTL」复用 T1 消费门同一 env
  `OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS`（惰性 import nodes.`_approval_consumption_ttl_seconds`/`_decided_at_ts` · 不另开旋钮 · 无环）。
- **认领不写状态**（零新列约束）：行锁仅作「并发认领窗口」（锁随事务提交释放）；
  窗口后的幂等由 run 终态判定 + resume 状态机守卫（not_interrupted 无副作用）兜底——R2-N3 机制闭环。
- **N-2 命名**：`aclaim_approved_for_resume` docstring 已写明与 `capability/idempotency.py` `aclaim` 的语义差异（并发触发去重 vs 结果复用去重）。
- **N-3**：扫描周期维持建议默认 60s（域 [5,3600] 内未调整）。
- **响应块形态**：auto 触发时 `resume` 块 = `{required: False, auto_triggered: True, method, endpoint}`（注明已触发 · 仍可兜底手动）；manual 字面零 diff（快照对拍钉死）。

## TB1–TB8 验收自证

| TB | 结论 | 实证（命令 + 结果） |
|----|------|---------------------|
| TB1（A9 auto 全链） | **PASS（机制段）** | `test_auto_decide_auto_resumes_without_manual_call`：挂起 → decide(immediate) → **不调 resume** → 后台任务同源跑完（unlocked=[T1] · verdict=replan · triggered+claimed 台账断言）；`test_db_auto_chain_terminal_done_frame`（真 PG）：sink `done{resumed}` → `run_is_terminal` False→True → 扫描不再补触发。**live 段留 40**（见留转清单 1） |
| TB2（A10 钉死组） | **PASS** | ① `test_trigger_carries_no_state_and_no_http_self_call`（AST 模块级可变态白名单 + 禁 httpx）+ `test_single_resume_path_in_router`（`await resume_hitl_run(` 调用点==1）② 幂等：终态跳过（TB1 Db 末段）+ pending 跳过（TB4 末段）③ 行锁 Db 组真 PG：`test_db_claim_skip_locked_only_one_succeeds`（持锁期间认领=None · 释放后成功）+ `test_db_claim_condition_filters`（过期/pending/rejected/ghost 四组）；InMemory 仅条件+状态机幂等（无行锁断言 · 实操-C 守住）④ `test_decide_resume_mode_unknown_400_not_422`（400 + decision 422 对照钉 + 不落 decide）⑤ `test_env_auto_resume_parse` 7 组参数化 + 非法 error 日志 |
| TB3（FP-8 防重） | **PASS** | 并发双 decide 409 原样绿（B1 `test_hitl_pending_decide.py` 20 用例内）；触发/扫描并发命中同单 → `test_inmemory_double_dispatch_state_machine_idempotent` 执行==1（状态机幂等）· Db 侧行锁仅一认领（TB2③ 持锁钉） |
| TB4（FP-9 崩溃兜底） | **PASS** | `test_db_scan_compensates_after_store_rebuild`（真 PG）：approved 落库 → 丢弃旧 store 新建 DbHitlStore（模拟重启）→ 扫描补触发（compensated+claimed 台账）→ 同 run 补 pending 后二轮扫描 dispatched==0 |
| TB5（FP-11 不循环） | **PASS** | `test_auto_re_interrupted_no_second_trigger_and_scan_skips`：auto 恢复后构造同 run 新 pending → 台账 triggered==1 · 扫描跳过 |
| TB6（A6 零 diff） | **PASS** | `test_decide_manual_resume_block_literal_unchanged`（缺省/非法 env 两组快照对拍字面一致）· `test_manual_mode_dispatches_nothing`（spy 零派发 + delegation off 面）· `test_lifespan_manual_creates_no_scan_task` / `test_lifespan_auto_starts_then_cancels_scan`（双面） |
| TB7（反回归存续） | **PASS** | `git diff master -U0 -- store.py` 删除行=0（76 行纯新增）· `_DECIDE`/`adecide` 段 diff 空 · registry/policy/nodes diff 空 · 手动 resume 对拍=既有测试原样绿 |
| TB8（工程面） | **PASS** | 全量 `pytest tests`：**1748 passed · 1 skipped · 4 failed**（capability_lookups×3+lg_rag_multi×1 = master 基线本地环境性 4 红 · T1 40 对拍钉死 · **零新增红**）；`ruff` 触及六路径零新增（stash 对拍 base 同绿）；`graph-compile.sh` EXIT=0（graph.json freeze/日期噪音已还原 · 承 T1 40 口径）；task lint PASS · lint-wiki-delta PASS |

**B1 旧测亲跑**：13 文件 `pytest test_hitl_pending_decide/test_hitl_resume/test_hitl_resume_events/test_hitl/test_lg_rag_sse_hitl/test_capability_delegation/test_lg_rag_delegation_wiring/test_capability_domain_allowlist/test_chat_ws/test_chat_router/test_admin_capability_observability/test_hitl_approval_consumption/test_hitl_auto_resume` → **243 passed**。

**新测试文件**：`tests/test_hitl_auto_resume.py` 39 枚全绿（含 Db 组 4 枚真 PG 非 skip）。

## 留转 40 清单

1. **TB1 live 段（handoff「A1 第四段补全实录」验收令）**：live HTTP/SSE auto 全链实录复跑。
   ⚠️ 已知偏差预告：T1 40 已钉「replan 重盖章 sid 致消费键失配」live 偏差（每次 resume 后
   `_stamp_host_plan` 重盖 sid → 消费键 (run_id, subtask_id, capability_id) 不命中 → FP-3 再拦循环 ·
   末段 `done{completed}` 不可达）。本 task 钉死契约边界内不改图重盖章语义（T1 面零改 ·
   非范围）→ **auto 形态 live 末段预计撞同一偏差**：机制段（decide→自动派发→同源恢复→图继续）
   已由 TB1 pytest 钉死，live 复跑请如实登记命中情况，「replan 后 approved 步骤 carry 保号 /
   消费键放宽粒度」裁决留维护者/SPEC v2（登记 · 不静默改向）。
2. **HG-GRAPH-MODULES 在册行**：已按 T1 先例形态落（00 代录措辞）→ 留 00 ratify。
3. **.env.example 未增新 env 键**（OPS_HITL_AUTO_RESUME / SCAN_INTERVAL）：承 T1 先例
   （TTL 键亦未登记）保持一致；如维护者要求补登记另议。
4. commit：`6530bd0` feat · `d35369a` test · 本 invoke 回填随收尾 docs commit；不 push 不开 PR。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-10 | 30 骨架先行落盘（GATE_VERIFY PASS · T1 merge 核验 ✓ · .env 对齐主仓） |
| 2026-10-10 | 30 实现落地：F1–F8 全件（auto_resume.py 新增 · store 行锁认领 · 恢复段抽取同源 · lifespan 补偿扫描 · 台账三件套 · 图谱两行+在册行）· TB1–TB8 逐项实跑 PASS（全量 1748 绿 · 4 红=基线环境性零新增）· commit 6530bd0/d35369a/+收尾 docs |
