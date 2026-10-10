# 30 invoke · hitl-approval-consumption-loop（T1 · D1 消费门 + D2 unlock 回填 + D4 台账/测试）

> **帽**：30-implement · **task**：docs/tasks/active/task_hitl_approval_consumption_loop.md
> **分支**：task/hitl-approval-consumption-loop（worktree t1-approval-consumption-loop · base master 7853334 含 T3）
> **日期**：2026-10-10 · **结论**：**完成（TA1–TA7 全绿 · 见下）**
> **依据**：SPEC v1（spec/hitl-approval-consumption 分支只读 · HG-SPEC-SIGNOFF=approved）· R1 增量复核 PASS（reviews/task_hitl_approval_consumption_loop_audit_R1_20261010.md · 45fec13）

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved（维护者签 · 00 代录 2026-10-10） | approved（开工令） | Y | Y | ✅ |
| HG-AUDIT-R1 | approved（R1 FAIL→修复→增量复核 PASS · 45fec13） | approved | Y | Y | ✅ |
| HG-GRAPH-MODULES | approved（在册 · capability/lg_rag/hitl 行备注段） | approved | Y | — | ✅ |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | Y | N | — |

reviews：task_hitl_approval_consumption_loop_audit_R1_20261010.md 存在且 R1 增量复核 PASS？ **是**（残留 NIT 计数口径已回改 14 处）
pre-30 invoke：required ∩ {10,20,00} 齐全？ **是**（00_gate_signoff_t1 / 10_task / 20_audit 三件在册）
机械辅助：`npx spec-wave verify --target . --task docs/tasks/active/task_hitl_approval_consumption_loop.md` → **VERIFY: PASS · EXIT=0**（本帽亲跑 2026-10-10）

**git_branch 字段核验（00 合流裁定 · 注记 2026-10-10）**：task 表 `git_branch` 溯源 07f9cc1（落稿）/0c5d148（B-1 修复）/HEAD 三态均为 `task/hitl-approval-consumption-loop` —— **源头即正确，无 diff 可修，不产生空 commit**（留痕备 00 查）。

---

## Commit 拆分（中文 conventional · 未 push 未开 PR）

| # | hash | 内容 |
|---|------|------|
| 1 | f7177bf | feat(lg_rag): D1 审批消费门 + D2 unlock 回填 + F1 payload 增键（nodes.py） |
| 2 | b281d7c | test(capability): B1 14 处 sync→async 随改 + A4④ 设计真态段双断言改写 |
| 3 | 8503456 | test(hitl): 新增 tests/test_hitl_approval_consumption.py 29 枚（TA1/TA2①-⑦/TA3/TA5）+ nodes.py UP017 lint 修复 |
| 4 | c70a9d4 | docs(graph+invoke): 图谱 lg_rag/hitl 行备注 + HG-GRAPH-MODULES 在册行 + 本 invoke |
| 5 | 80eb872 | test(hitl): T1 验收增强 29→34 枚（TA2⑧ Db 双 store TTL 真读组 / TA1 span 双面 / TA3③ resume 成环机制段 / TA4-D / TA5 台账 / TA6 409 保留）· 30 收尾棒 |

---

## 验收自证（TA1–TA7 逐项 · 实跑留证）

### TA1（消费放行）

tests/test_hitl_approval_consumption.py::test_ta1_approval_consumed_allows_redispatch ✅——预置匹配 approved 单（三元组+TTL 新鲜）→ _delegation_issue_block_reason 返 None；caplog 断言 delegation_approval_consumed 恰 1 条且不含参数原值（记动作不记内容）。**收尾棒增强（80eb872）**：台账双面补齐——span metadata 面 monkeypatch `_record_span_metadata` spy 断言恰 1 次且含 subtask_id/capability_id/ttl_remaining_seconds>0（logger+span 双面 · 台账纪律钉死）。

### TA2（消费边界否定 · 变异式七组）

tests 内 27 枚全绿：① pending/rejected 不生效 ② 三元组任一不匹配/缺 capability_id 键/prefix_touch 类型守卫（参数化 5 例）③ 超 TTL float 拦（InMemory 组）④ ISO str 双形态（新鲜放/过期拦）⑤ store 读异常 fail-closed + warning 台账（FP-1）⑥ TTL env 解析 8 例（默认 3600 · 域 [1,86400] · 非法/越界回退）⑦ _decided_at_ts 归一 7 例（bool 显式排除）。**收尾棒增强（80eb872）**：⑧ **Db 双 store TTL 组**（test_ta2_ttl_db_store_real_read_path_iso_str / test_ta2_ttl_db_store_expired_not_consumed · 真 DbHitlStore 经 acreate→adecide→alist/aget 真读路径 · 实收 ISO 8601 str 类型钉死 · 过期半经 SQL 拨回 decided_at 2h · 本机 DB_AVAILABLE=True **真跑非 skip** · 实操-B 履约闭环）

### TA3（单子任务形态 resume 成环）

机制段 pytest ✅：test_ta3_unlock_refilled_for_delegation_issue（真链 _join_subtasks→_observe→_persist_hitl · unlock=被拦 sid + payload capability_id 键）+ test_ta3_prefix_touch_unlock_stays_empty（FP-4 形态守卫 · 409 不放宽）。**收尾棒增强（80eb872）**：③ **成环机制段** test_ta3_single_subtask_resume_loop_completes——单子任务计划全真链：join 拦 → persist（unlock=sid 回填断言）→ observe 图真挂起（interrupt hitl_waiting）→ store.adecide(approved) → resume_hitl_run 图真恢复（verdict=replan · hitl_unlocked_ids=[sid]）→ 消费门放行（_delegation_issue_block_reason=None）→ _issue_delegation_token 真签发 → tool_exec_node 真执行（罐头回显 · Host 写放行 env 与消费门正交）→ _observe done==planned==1 且 unsatisfied=False（done{completed} 机制段收口）；live HTTP/SSE 段留 40。

### TA4（反回归钉死）

git diff master -- app/ops/capability/registry.py app/ops/capability/policy.py app/ops/capability/delegation.py → 空（逐字节零 diff · auto_approve_ok 纯函数不动）；test_allow_tags_does_not_waive_deny_write 及 capability/hitl 既有测试全量内原样绿。**收尾棒增强（80eb872）**：实操-D 断言化 test_ta4_consumption_hit_does_not_waive_gateway_or_policy——消费命中（签发判定 None）后 ② 无令牌 enforce 验签门照拒 ③ 有令牌但无 Host 写放行 → Policy 写闸仍裁 write_not_confirmed（消费不过 gateway/Policy 钉死）。

### TA5（off 零 diff）

test_ta5_off_mode_zero_store_touch ✅：off 模式 _join_subtasks 全程 store.alist spy 零调用 · 无 delegation_issue 拦截产出（消费路径零触达）。**收尾棒增强（80eb872）**：补 caplog 断言 off 下零 delegation_approval_consumed 台账（无假台账钉死）。

### TA6（decide 落库不动）

git diff master -- app/ops/hitl/store.py app/ops/hitl/router.py → 空；test_hitl_pending_decide 20 用例原样绿（全量内）；router.py:404-411 409 守卫一行未动（diff 空实证）。**收尾棒增强（80eb872）**：409 保留断言化 test_ta6_prefix_touch_empty_unlock_resume_still_409——prefix_touch_required 类空 unlock 单据批准后 POST resume 仍 409（detail 含 unlock_subtask_id · HTTP 层真端点 · 承 test_hitl_resume _client 范式）。

### TA7（工程面）

- 全量：SILICONFLOW_API_KEY=dummy-probe pytest tests -q → **1708 passed · 1 skipped · 0 failed**（36.04s）
- ruff 触及路径：nodes.py 6 枚全为 master 基线同型同数（对拍实证）；tests/test_hitl_approval_consumption.py 零告警（初版 4 枚已修：F401 未用 import · UP017×3 → datetime.UTC）；其余触及文件零新增
- ./scripts/graph-compile.sh EXIT=0（graph.json 仅 generated_at 噪音已回退）
- capability_acceptance.sh 门禁：失败 0 · 跳过 1（联调桩目录 ops-desk-mock-oa 不在 · 环境性）（报告 .acceptance-reports/capability-acceptance-20261010-091448.md）
- B1 十四处随改亲跑：pytest 三文件 62 passed + redlines（默认跑 · 全量内含绿）+ capability_step_contract_gate.py 补 await（门禁绿实证）
- task lint PASS · verify EXIT=0（首输出 GATE_VERIFY 节）
- **收尾棒复跑（80eb872 落盘后 · .env 已复原主仓逐字节一致）**：全量 `SILICONFLOW_API_KEY=dummy-probe LG_RAG_DELEGATION_TOKEN_MODE=off pytest tests -q` → **1713 passed · 1 skipped · 0 failed**（353.35s · skip=integration MCP 外网用例 · 另 .env 翻转前同suite 37.69s 同数绿）；ruff 触及路径七文件 13 错与 base 7853334 同文件同规则同计数**逐枚同构**（仅行号漂移 · 零新增），新测试文件单跑 ruff 零告警；graph-compile.sh EXIT=0（graph.json 仅 freeze_id/generated_at 日期派生噪音 · checkout 还原不入 commit）；capability_acceptance.sh mode=off 覆盖重跑 **失败 0 · 跳过 1 · CAP_EXIT=0**（联调层 SKIP=桩目录 ops-desk-mock-oa 在主仓旁而非 worktree 旁 · 环境性 · 报告 capability-acceptance-20261010-093543.md）；TA 新测试文件 34 枚两轮全绿（含 Db 组真跑非 skip · DB_AVAILABLE=True）

### 过程留痕（两棒卡滞 + 授权落地）

30 首棒（7cdbe6c9）落 f7177bf 后于长生成卡滞 · interrupt 止损 → 续跑落 b281d7c（62 绿）后再卡于新测试文件生成 → interrupt；接管棒（3869f0af）同型卡滞 interrupt。维护者 2026-10-10 授权例外句「授权 00 本窗亲自落地剩余面（推荐）」→ TA 测试文件（29 枚）/lint 修复/图谱回写/本 invoke 由 00 亲自落地（分段落盘纪律）。delegate-only 例外仅此一次本 task 剩余面。

### 过程留痕（收尾棒 · 2026-10-10 收尾段）

30 收尾棒（ Harness 30 接管）在 8503456/c70a9d4 基础上补契约缺口五件（Db 双 store TTL 组 · TA1 span 双面 · TA3 成环机制段 · TA4-D · TA6 409 保留 → 29→34 枚 · 80eb872）。**环境性红钉案（T3 先例口径）**：收尾段 worktree `.env` 一度被并发 40 帽翻成 `LG_RAG_DELEGATION_TOKEN_MODE=enforce`（live 三 env 组所需）→ 该窗口内 capability_acceptance.sh 单测/编排两层红（permission_denied: delegation no_token · 3 用例+3 检查项）与全量 5 红——实证 `LG_RAG_DELEGATION_TOKEN_MODE=off` 显式 export 覆盖后全绿（非本 task 代码归因）；.env 已按 00 裁定复原与主仓逐字节一致（diff 空），门禁证据以 mode=off 覆盖重跑为准（capability-acceptance-20261010-093543.md · 失败 0）。graph.json freeze_id 为日期派生噪音（graph_yaml_to_json.py:65-68 当日日期生成）→ checkout 还原不入 commit。

### 留转 40

1. live HTTP/SSE 全链（三 env 组 · 无 shim）：挂起→pending→decide(approved)→resume 200→done{completed} 实录（T1 手动模式 · handoff 验收令第一段）
2. TA4/TA6 diff 空组复跑（registry/policy/delegation/store/router）
3. 全量 + 门禁复跑

### B1 · 14 处 sync→async 随改亲跑记录

b281d7c 内：tests/test_step_contract.py（7）+ tests/test_lg_rag_delegation_wiring.py（3）+ tests/test_capability_testing_write.py（2 · 含 488-493 双断言改写）+ tests/eval/test_capability_redlines.py（1 · 默认跑 · 全量内含绿）+ scripts/acceptance/capability_step_contract_gate.py（1 · 补 await · 门禁绿实证）；三文件亲跑 62 passed · 全量 1708 零新增红。

---

## 重要发现 / 偏差登记

无内容偏差。过程偏差：30 两棒长生成卡滞（interrupt ×2 留痕）→ 维护者授权例外「00 本窗亲自落地剩余面」（2026-10-10）→ TA 测试/ lint 修/图谱/本 invoke 由 00 落地；实现主体（f7177bf/b281d7c）为子 Agent 交付。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-10 | 30 骨架先行落盘（GATE_VERIFY PASS · git_branch 字段核验源头正确 · 实现开工） |
| 2026-10-10 | 30 收尾棒增量回填：commit 表第 5 行（80eb872）· TA1 span 双面 / TA2⑧ Db 双 store TTL 真读组 / TA3③ 成环机制段 / TA4-D / TA5 台账 / TA6 409 保留逐节补证 · TA7 净态复跑留证（1713 绿 · ruff 同构 · 门禁 CAP_EXIT=0）· 过程留痕钉案 .env 并发翻转环境性红（非代码归因 · 复原留证） |
