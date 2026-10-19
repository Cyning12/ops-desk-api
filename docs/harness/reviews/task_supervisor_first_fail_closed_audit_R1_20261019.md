# 20-task-audit R1 书面审：task_supervisor_first_fail_closed

> **hat_id**：20-task-audit（R1 · 书面审 · 不改 task 实质 · **不代签** HG-AUDIT-R1）
> **审查对象**：`docs/tasks/active/task_supervisor_first_fail_closed.md`（draft · 208 行 · HG-AUDIT-R1=pending）
> **审查日期**：2026-10-19 · **审查人**：Harness 20-task-audit
> **结论**：**fail（退回 10-task 补列 1 项）** · 六大核对重点中 5 项全绿、第 5 项（验收完备性）发现 **1 个内容阻塞 B1**（行为变更类 task 缺「旧测 grep 影响面」验收项 · 实证影响面存在且不小）· 非阻塞观察 2 项 · **HG-AUDIT-R1 建议维持 pending，待 B1 补列后维护者人签**
> **对照真值（全部实读）**：SPEC `docs/spec/supervisor-first-fail-closed/SPEC-supervisor-first-fail-closed_v0.md`（signed · 186 行逐行）· R1 spec 审查 `docs/harness/reviews/spec_supervisor-first-fail-closed_audit_R1_20261019.md`（conditional_pass · N1–N4）· 00 三条定夺 `docs/harness/invokes/by-task/supervisor-first-fail-closed/invoke_20261019_00_start.md`（22 行逐行）
> **实证锚点复核（本帽亲读）**：`app/ops/lg_rag/multi/graph.py:80-106`（:96-98 图边 `START → intent_node → strategy_builder → supervisor` 逐行在册）· `app/ops/lg_rag/multi/nodes.py:1090-1234`（:1094 `locked = _locked_prefix(state)` · :1157-1193 fallback 分叉 :1158 `if locked:` → :1189 `_carry_plan` / :1192 `else` → :1193 单 rag `t1`；另注意 :1114 prompt 构面用 `locked or preserved`、fallback 分叉判据确为单变量 `locked`）· `app/ops/strategy/builder.py:108-192`（:121-122 只读 `state.intent`+`intent_fallback` · :162-163 `needs_tool is False` → 空 allowlist）· `app/ops/strategy/scenario.py:40-94`（:49-52 默认 off · :70-91 S1–S5 · :81-90 S4 缺省 risk_hint 视同 high）· tests/ 影响面 grep（`supervisor_fallback` 10 命中 · `intent_node` 25 命中 · `needs_tool` 61 命中 · `scenario_trim|intent_fallback` 24 命中）

## 一、六大核对重点核对表

| # | 核对重点 | 裁定 | 摘要 |
|---|---------|------|------|
| 1 | 范围/非范围/验收/failure_paths 与 SPEC 一致性 | ✅ PASS | D1/D2/D3 承 SPEC §2 逐行不走样（触发四形态、默认不写单 rag、span `supervisor_plan_failed=true`、灾备 env 三档不扩权、D3 主路径不写 intent / Builder 不清空 / scenario 短路不裁）；SPEC 非范围 8 条全数在册并扩至 11 条（+不扩判据 `locked or preserved` · +前端零改码 · +起草阶段零 `app/` 改码），与范围无重叠；SPEC FP-1~FP-8 全数承接（task FP-1~FP-8）+ FP-1b（00 定夺②）+ FP-9（流程闸），无漏；SPEC §6 验收 7 条全数映射进 TC1–TC10 |
| 2 | 三条 00 定夺落点正确性 | ✅ PASS | ① web 同步仅列「下游/后续棒」表（task:92-96）+ 非范围（task:89）+ orchestration 下游棒（task:29），**不进范围** ✅；② N2 归 error → FP-1b（task:107）+ TC2b（task:125）+ D2 判据行（task:69），判据保持 `if locked:` 不扩，与 nodes.py:1158 实证一致（:1114 的 `locked or preserved` 仅属 prompt 构面，非失败分叉判据）✅；③ N1→TC6（task:129 S4 缺省 risk_hint→high 收紧显式 · `visible` 进=出逐 id 对拍）· N3→TC9（task:132 回写 05 §4.2 词表 + 01_modules.md 备注）· N4→invoke 已在册 ✅ |
| 3 | 首次失败 vs 重规划沿用后缀分叉 | ✅ PASS | FP-1/FP-1b vs FP-5 成对互斥；分叉判据单一变量 `locked`（D2 task:69 · FP-1b task:107 双处钉死「不扩」）；非范围双向锁死（task:87 禁重规划改硬失败 · task:88 禁扩判据）；FP-5「不收缩成只剩前缀」与 nodes.py:1160-1166 注释同源 |
| 4 | 不新增 SSE event_type / freeze 纪律 | ✅ PASS | freeze_id 行（task:30）对照 `lg-rag-sse-v1`：不升 freeze、不新增 `event_type`、仅扩 `error.stage` 字面量，承 run-worker / disconnect-completion 先例且挂回写 05 §4.2 义务；元信息 graph_change_layer=none + 「若需新增 event_type → 回 SPEC 判 G-L* 并升 freeze，禁 silent 扩」（task:19）升级回路完整 |
| 5 | 验收可机断性 | ⚠️ **B1** | TC1–TC10 逐条可假 LLM/抛错注入/夹具机断，无人工判断依赖（TC1 断言编译图边集合而非源码字符串 · TC7 router/basic 零 diff 在列）；**但本 task 属行为变更类（改 fallback 语义/默认值），验收标准缺「旧测 grep 影响面」项**——见下节 B1 |
| 6 | 思考轮 R0–R5 闭合 + HG-AUDIT-R1=pending | ✅ PASS | 控制表 R0–R5 齐全、early_stop 全 false、`actual_last_round=R5`、各轮小节（R0–R5 + 自检结论）齐备；R5 residual=`HG-AUDIT-R1=pending` 与人工闸表（task:37）一致；闸表三行（HG-SPEC-SIGNOFF=approved · HG-AUDIT-R1=pending blocks 30 · HG-GRAPH-MODULES=approved）与 invoke 闸态一致 |

## 二、阻塞项（内容 · 退回 10-task）

### B1 · 行为变更类 task 缺「旧测 grep 影响面」验收项（K7 checklist）

- **依据**：20-task-audit skill K7——行为变更类 task（改默认值 / 校验 / 策略门 / **fallback 语义**）验收标准须含「旧测 grep 影响面」项，缺则退回 10-task 补列。本 task D1（摘 `intent_node`）/ D2（首次失败改 error）/ D3（Builder 不清空 + scenario 短路）三项全是行为变更，正对条款。
- **实证影响面（本帽 grep · 真实存在，非假设）**：
  - `tests/test_intent_node.py:112-124`：断言 supervisor 图边 `("__start__", "intent_node")`、`("intent_node", "strategy_builder")`——**D1 必破**（须转红改写为 TC1 口径）。
  - `tests/test_lg_rag_multi.py:292`：断言 `"intent_node" in node_names`——**D1 必破**。
  - `tests/test_strategy_builder.py:120-131` `test_builder_needs_tool_false_empty_allowlist`——**D3 必破**（Builder 不再因前置意图 `needs_tool is False` 清空 allowlist）。
  - `tests/test_lg_rag_structured_output_p2.py:121-140`、`tests/test_lg_rag_supervisor_capability_catalog.py:143`：`supervisor_fallback` 元数据断言——D2 语义变更后须逐条处置（保留=重规划分支回归 / 改写=首次失败转 error）。
  - `tests/test_lg_rag_sse_stream.py:32,289` · `tests/test_lg_rag_sse_run_worker.py:66,135,199,252,500` · `tests/test_lg_rag_sse_disconnect_completion.py:24`：假流夹具 yield `intent_node` 事件——D1 摘节点后夹具须同步。
  - `tests/test_strategy_scenario.py`（24 命中）：`scenario_trim` 纯函数用例多半不受影响，但 `_apply_scenario_stage` 相关用例（:193-280）须逐条确认。
- **缺口性质**：TC5（重规划既有用例保绿）/ TC7（router/basic 零 diff）/ TC10（全量绿）只给终态判据，未枚举「哪些旧测合法转红改写、哪些必须保持绿」——30 红测先行时无处置清单，存在「误删合法回归」或「漏改旧语义断言」双向风险。
- **回填位置**：task `## 验收标准` 追加一条（建议编号 TC11 · 旧测 grep 影响面）：按上列 grep 面枚举受影响既有用例及处置（转红改写 / 保持绿 / 夹具同步），并声明枚举外既有用例默认保持绿。

## 三、非阻塞观察（不阻塞签闸 · 供 30 按实校正）

| ID | 位置 | 内容 |
|---|---|---|
| N-a | task 依赖锚点 builder.py | `:147 needs_tool is False → 空 allowlist` 实读为 docstring 行（:147），代码行在 :162-163；task 已自声明「行号录自 R1 审查实证 · 30 按实校正」，语义指向正确，不阻塞 |
| N-b | D2 边界 | nodes.py:1098-1112 空 allowlist 预检分支（`allowed_capability_ids is None or not allowed_ids` → 单 rag `t1` + `supervisor_empty_allowlist`）非「规划 LLM 失败」触发，不在 SPEC FP-1~FP-8 内；建议 30 实现时显式不动该分支语义（或在本 task/PR 说明其归属），避免与 D2「默认不写单 rag」混淆 |

## 四、HG-AUDIT-R1 建议

**建议维持 pending，不代签**。理由：B1 为内容阻塞，须先由 10-task 补列验收项；补列为纯文档增量（不改范围/非范围/既有 TC 实质），完成后维护者可凭本审查 + 补列 diff 轻量确认并人签 HG-AUDIT-R1 → approved，无需全量 R2 复审。签前 30 拒改码。

## 五、回填清单（退回 10-task）

| # | task 小节 | 动作 |
|---|-----------|------|
| 1 | `## 验收标准` | 追加 TC11「旧测 grep 影响面」：枚举第二节 B1 实证清单（test_intent_node 图边断言 · test_lg_rag_multi:292 · test_strategy_builder:120 · structured_output_p2 / capability_catalog 的 supervisor_fallback 断言 · SSE 假流 intent_node 夹具 · test_strategy_scenario 逐条确认），逐项标注处置（转红改写 / 保持绿 / 夹具同步），并声明枚举外既有用例默认保持绿 |
| 2 | `### 自检结论` | 补一行：K7 旧测 grep 影响面已列（TC11） |

## 六、下一棒

**退回 10-task**（仅补列 TC11 + 自检行 · **禁改 task 实质范围**）→ 维护者轻量确认 → 签 HG-AUDIT-R1 → 30。

```text
## 维护者签闸（10-task 补列后 · 30 前）

- [ ] 已读 R1 审查结论（fail · 仅 B1 一项 · 已补列）
- [ ] 核对补列 diff 仅涉验收标准 TC11 + 自检结论行
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
```

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-10-19 | R1：六大重点 5 绿；B1（K7 行为变更类缺「旧测 grep 影响面」验收项 · grep 实证影响面存在）阻塞 → **fail · 退回 10-task 补列 TC11**；非阻塞 N-a/N-b；HG-AUDIT-R1 维持 pending（不代签） |
