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
| 3 | （本棒） | test(hitl): 新增 tests/test_hitl_approval_consumption.py 29 枚（TA1/TA2①-⑦/TA3/TA5）+ nodes.py UP017 lint 修复 |
| 4 | （本棒） | docs(graph+invoke): 图谱 lg_rag/hitl 行备注 + HG-GRAPH-MODULES 在册行 + 本 invoke |

---

## 验收自证（TA1–TA7 逐项 · 实跑留证）

### TA1（消费放行）

tests/test_hitl_approval_consumption.py::test_ta1_approval_consumed_allows_redispatch ✅——预置匹配 approved 单（三元组+TTL 新鲜）→ _delegation_issue_block_reason 返 None；caplog 断言 delegation_approval_consumed 恰 1 条且不含参数原值（记动作不记内容）。

### TA2（消费边界否定 · 变异式七组）

tests 内 25 枚全绿：① pending/rejected 不生效 ② 三元组任一不匹配/缺 capability_id 键/prefix_touch 类型守卫（参数化 5 例）③ 超 TTL float 拦 ④ ISO str 双形态（新鲜放/过期拦 · 实操-B · alist 真读路径喂 str）⑤ store 读异常 fail-closed + warning 台账（FP-1）⑥ TTL env 解析 8 例（默认 3600 · 域 [1,86400] · 非法/越界回退）⑦ _decided_at_ts 归一 7 例（bool 显式排除）。

### TA3（单子任务形态 resume 成环）

机制段 pytest ✅：test_ta3_unlock_refilled_for_delegation_issue（真链 _join_subtasks→_observe→_persist_hitl · unlock=被拦 sid + payload capability_id 键）+ test_ta3_prefix_touch_unlock_stays_empty（FP-4 形态守卫 · 409 不放宽）。resume 真恢复链由 D2 既有 test_capability_testing_write.py A4④ ④段（decide→resume_hitl_run→verdict=replan · 解锁留痕）存续绿覆盖；live HTTP/SSE 段留 40。

### TA4（反回归钉死）

git diff master -- app/ops/capability/registry.py app/ops/capability/policy.py app/ops/capability/delegation.py → 空（逐字节零 diff · auto_approve_ok 纯函数不动）；test_allow_tags_does_not_waive_deny_write 及 capability/hitl 既有测试全量内原样绿。

### TA5（off 零 diff）

test_ta5_off_mode_zero_store_touch ✅：off 模式 _join_subtasks 全程 store.alist spy 零调用 · 无 delegation_issue 拦截产出（消费路径零触达）。

### TA6（decide 落库不动）

git diff master -- app/ops/hitl/store.py app/ops/hitl/router.py → 空；test_hitl_pending_decide 20 用例原样绿（全量内）；router.py:404-411 409 守卫一行未动（diff 空实证）。

### TA7（工程面）

- 全量：SILICONFLOW_API_KEY=dummy-probe pytest tests -q → **1708 passed · 1 skipped · 0 failed**（36.04s）
- ruff 触及路径：nodes.py 6 枚全为 master 基线同型同数（对拍实证）；tests/test_hitl_approval_consumption.py 零告警（初版 4 枚已修：F401 未用 import · UP017×3 → datetime.UTC）；其余触及文件零新增
- ./scripts/graph-compile.sh EXIT=0（graph.json 仅 generated_at 噪音已回退）
- capability_acceptance.sh 门禁：失败 0 · 跳过 1（联调桩目录 ops-desk-mock-oa 不在 · 环境性）（报告 .acceptance-reports/capability-acceptance-20261010-091448.md）
- B1 十四处随改亲跑：pytest 三文件 62 passed + redlines（默认跑 · 全量内含绿）+ capability_step_contract_gate.py 补 await（门禁绿实证）
- task lint PASS · verify EXIT=0（首输出 GATE_VERIFY 节）

### 过程留痕（两棒卡滞 + 授权落地）

30 首棒（7cdbe6c9）落 f7177bf 后于长生成卡滞 · interrupt 止损 → 续跑落 b281d7c（62 绿）后再卡于新测试文件生成 → interrupt；接管棒（3869f0af）同型卡滞 interrupt。维护者 2026-10-10 授权例外句「授权 00 本窗亲自落地剩余面（推荐）」→ TA 测试文件（29 枚）/lint 修复/图谱回写/本 invoke 由 00 亲自落地（分段落盘纪律）。delegate-only 例外仅此一次本 task 剩余面。

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
