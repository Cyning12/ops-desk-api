# invoke · 30 · llm-layer-hardening · 实现 D1–D5

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-21 |
| **帽** | 30-implement（闸已核验：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均 approved · `npx spec-wave verify` 已 PASS） |
| **分支** | `task/llm-layer-hardening`（每次 commit 前 `git branch --show-current` 核验；未 push） |
| **task** | `docs/tasks/active/task_llm_layer_hardening.md`（signed） |
| **上游** | `docs/spec/llm-layer-hardening/SPEC-llm-layer-hardening_v1.md`（signed） |

## 结论

**D1–D5 全量落地**。

- **D1 重试**：`app/llm/retry.py`（指数退避+full jitter · 仅 `LlmProviderError(retryable=True)` · 4 env 非法回退+warning）；`BaseProviderImpl.__init_subclass__` 边界统一包装 `_resilient_stream`（熔断 guard 外 / 重试内 / usage 观测同层）；流式首 content chunk 前限定；耗尽抛原始错误；Bailian 链内逐候选接入（先同模型退避再换模型，链语义不变）。
- **D2 熔断**：`app/llm/circuit.py`（pybreaker 复用 capability 模式 · provider 级 · 仅环境失败计数 · `throw_new_error_on_trip=False` 保根因 · open 零出网翻译 `circuit_open`（retryable=False）· snapshot/reset/trip/advance hook 不 sleep · 3 env）。
- **D3 路由**：`model_catalog.TASK_TIER_MODELS` + `resolve_task_model`（显式 > `OPS_LLM_TIER_*` > 档默认 > 全局默认；`RAG_GRADER_MODEL` 并入 grader 档；非法档/未知 task 回退+warning）；四调用点改造（answer/grader/extract/structured）+ span metadata `llm_route`；未分档调用点逐字节一致。
- **D4 成本归集**：`app/llm/usage.py`（ContextVar run 上下文 · ensure_task_type 内层不覆盖外层）+ `OpsLlmUsage` 模型 + alembic `20260921_llm_usage`（upgrade/downgrade 往返实测可逆）；注入点 chat streaming / chat 节点（state.run_id）/ lg_rag router / memory 抽取；无 usage 末帧不落行；落表故障 log+计数不挡主答。
- **D5 图谱文档**：`01_modules.md` `llm` 行备注更新 + `db` 行登记 `ops_llm_usage`（HG-GRAPH-MODULES 新行**留 pending 待 00 代录**，30 不签闸）+ `app/llm/README.md` 新建 + `.env.example` 增补；`graph-compile.sh` 绿。

## 验证（真跑）

- `pytest tests`：1137 passed · 1 skipped · 3 failed——3 个失败为**基线既有**（stash 对照同失败：`test_chat_ws.py` 2 条 WS portal-loop 环境性 + `test_capability_http_adapter` proxy 1 条），与本波无关。新增 49 条（retry 12 / circuit 10 / routing 21 / usage 6）全绿。
- `ruff check app tests`：57 errors = 基线存量（本波文件零新增）。
- alembic 往返（opsdesk_test）：upgrade 建表 → downgrade 删表 → re-upgrade 重建，全过。
- `./scripts/graph-compile.sh`：绿。
- 变异检验：重试判据改「全部错误都重试」→ `test_4xx_zero_retry` 真 fail（`assert 3 == 1`）→ 已还原。

## 旧测影响面 12 条处置核对

改编 4 条全落地：#2（429/500/503 + SSE 解析错 + 传输错五条假时钟化 + 调用次数/退避界断言）· #3（`test_fallback_emits_event` 假时钟 + 首候选 ×3 退避 + 事件恰一次 from/to 不变）· #4（`test_fallback_chain_exhausted` 假时钟 + fail_max=99 隔离熔断 + 3×3 出网断言 + exhausted 终态保留）· #6（`test_answer_node_handles_error` 假时钟 + 3 次尝试断言）· #10（conftest autouse `_reset_llm_circuit` 对齐 capability 先例）。回归 7 条全绿（#1 4xx/缺 key · #5 链语义三条+complete meta · #7 chat_nodes/ws 成功路径（ws 两条环境性失败基线既有）· #8 memory 抽取 `provider.calls==1` 零重试风暴契约不破 · #9 lg_rag 节点级 fallback 四文件 · #11 RAG_GRADER_MODEL 兼容（D3 新增断言覆盖）· #12 usage 钩点无 DB 不红）。删除 0 条。

## 遗留风险

① 重试默认参数（0.5s/8s/3 次）未经真实流量校准（承 SPEC residual ①）；② lg_rag supervisor 多节点并发下 ContextVar 传播依赖同任务链（入口注入+节点按 state 注入双保险，承 residual ②）；③ 占位价表偏差由手册 L8 另行（承 residual ③）；④ 边界包装对「先吐 meta chunk 再失败」的自定义 fake 会重试（真实 provider 首 content chunk 前无 meta chunk，bailian fallback 事件在链内层处理不受影响）。

## 下一棒

40 验收 → HG-GRAPH-MODULES 新行由 00 代录签收 → PR 合并。
