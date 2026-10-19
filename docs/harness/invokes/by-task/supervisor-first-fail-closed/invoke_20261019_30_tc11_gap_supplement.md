# invoke · 30 · TC11 枚举缺口补录记录（2026-10-19）

> **帽**：30（实现）· **任务**：supervisor-first-fail-closed
> **依据**：00 定夺（2026-10-19 本窗 send_message）——「镜像转红改写为 raises SupervisorPlanError 属枚举清单缺口补录，非范围分叉」，要求落本 invoke 保持可追溯。

## 背景

TC11 枚举清单未覆盖、但断言**正是 D2 明文废止行为**（首次·无 locked·规划失败 → 静默单 rag fallback）的旧测，红测改写阶段发现 4 条；转绿全量跑阶段又发现 1 条同类 + 1 条夹具同步。

## 缺口条目（00 定夺批 4 条 · 转红改写）

| # | 文件:行号（改写前） | 原断言 | 处置 |
|---|---|---|---|
| 1 | tests/test_lg_rag_multi.py:179-195 | 非法 JSON → 静默 fallback 单 rag | 转红改写 `test_decompose_invalid_json_fails_closed`（raises SupervisorPlanError） |
| 2 | tests/test_lg_rag_multi.py:198-212 | LLM 异常 → 静默 fallback 单 rag | 转红改写 `test_decompose_llm_exception_fails_closed`（raises） |
| 3 | tests/test_lg_rag_multi.py:229-259 | plan 非法 tool id → 静默 fallback 单 rag | 转红改写 `test_invalid_tool_id_in_plan_fails_closed`（raises） |
| 4 | tests/test_lg_rag_supervisor_capability_catalog.py:204-233 | tool 不在 allowlist → 静默 fallback | 转红改写 `test_supervisor_tool_not_in_allowlist_fails_closed`（raises） |

理由链（00 原话）：① 不可能保绿（行为本身被 D2 改）；② 删除犯「误删合法回归」；③ 转红改写与既有枚举项（structured_output_p2 / capability_catalog:115-145）处置一致。10-task 已并行补录 task 真值（commit 7b6b54b）。

## 转绿阶段追加发现（同类镜像 · 本 invoke 补记）

| # | 文件:行号 | 形态 | 处置 |
|---|---|---|---|
| 5 | tests/eval/test_input_isolation.py:226-252（② G4） | 诱导非法 tool id → 断言 fallback 单 rag + gateway 零请求 + span invalid_tool_id | 镜像转红改写：raises SupervisorPlanError + gateway 零请求 + span `supervisor_invalid_tool_id`/`supervisor_plan_failed` 双标记（核心红线断言「越权零请求」保留） |
| 6 | tests/test_step_contract.py:553（前驱失败⇒后继零请求） | replan 第二轮 provider 不可解析、locked 空 → D2 raise；**非**废止行为断言，被测契约（depends_on 拦截）与 fail-closed 正交 | **夹具同步**：`monkeypatch.setenv(LG_RAG_SUPERVISOR_PLAN_ON_FAIL, single_rag)` 保持旧收尾形态，断言逐字零改动（fail-closed 本身已由 #1-#3 与 structured_output_p2 覆盖） |

#5 与 00 批准的 4 条同类（断言被 D2 废止行为本身），按同一定夺镜像处置；#6 非废止行为断言，属 TC11「夹具同步」类。两者均在本 invoke 补记，供 40/维护者复核。

## 落点 commit

- 红测改写（含 #1-#4）：d97c1aa
- 实现 + #5/#6：fb43562
