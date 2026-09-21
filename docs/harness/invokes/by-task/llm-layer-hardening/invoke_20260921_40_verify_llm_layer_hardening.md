# Invoke · 40 verify · llm-layer-hardening

> **hat**：40  
> **日期**：2026-09-21  
> **分支**：`task/llm-layer-hardening`（核验前后均 `git branch --show-current` 确认；未切 master · 未 push）  
> **task**：`docs/tasks/active/task_llm_layer_hardening.md`（signed）  
> **禁区**：未改实现码（变异检验一处改判据已 `git checkout` 还原并复跑确认绿）；未签任何 human_gate；未 CLOSE / git mv done

---

## 质量门（本帽真跑 · 实录）

| 命令 | 结果 | 证据摘要 |
|------|------|----------|
| `pytest tests -q` | **3 failed, 1137 passed, 1 skipped**（15.92s） | 失败三条：`test_chat_ws.py::test_ws_message_streams_events` / `test_ws_second_message_while_active_rejected` / `test_capability_http_adapter.py::test_urllib_transport_honors_explicit_capability_proxy` —— 与 30 自称完全一致 |
| 基线对照（git worktree @ master `5deb430`） | **同 3 条在 master 上同错复现**（3 failed, 4 passed） | `RuntimeError: Event loop is closed`（WS portal-loop 环境性）+ proxy 断言；**未动工作树**（worktree 法，非 stash），置信度：高 |
| `ruff check app tests` | 57 errors；**master worktree 同跑 57 errors** | 零新增，与基线逐数一致 |
| alembic 往返（dev 库 opsdesk） | upgrade head → 表/双索引在位 → downgrade -1 → 表删（count=0）→ re-upgrade → 表回（count=1）→ 终态 `20260921_llm_usage (head)` | 表结构与钉死契约逐列一致（id/run_id text/surface/task_type/provider/model/3×tokens/attempts/created_at · 索引 `(run_id)` `(surface,created_at)` · 无 FK）；往返只增删空新表，dev 数据零触碰 |
| `./scripts/graph-compile.sh` | **exit 0** | warning 均为既有词汇登记档提示（triggers/branches 开放惯例），非本波新增 |
| 新测计数 | 四新文件 `--collect-only` = **49 条**（retry 13 / circuit 9+参数化 / routing 21+参数化 / usage 6，总数与 30 自称 49 一致；分项粒度差异系参数化计数口径） | `tests/test_llm_{retry,circuit,routing,usage}.py` |

---

## 验收标准逐条对照（24 条）

### D1 · 重试（5/5 PASS）

| # | 验收点 | 结论 | 证据 |
|---|--------|------|------|
| 1 | 可重试错误退避至 max_attempts · 延迟序列 `0 ≤ d ≤ min(cap, base×2^i)` · 不假 sleep | ✅ | `test_request_error_retries_to_max_attempts`：`_FailingClient.created == 4`（env=4）· `len(delays)==3` · 逐条界断言；假时钟 monkeypatch `app.llm.retry.sleep` |
| 2 | 400（retryable=False）零重试 | ✅ | `test_4xx_zero_retry`：`calls == 1` · `retry_delays == []` · status_code==400 |
| 3 | 流中已吐首 chunk 后零重试零换模型 · error 事件 · 正文不重复 | ✅ | `test_no_retry_after_first_content_chunk`：`calls==1` · answer=="Hello" · answer 事件恰 1 · 尾帧 error retryable=True |
| 4 | bailian 链先同候选退避再 fallback · 链序/事件语义不变 | ✅ | 改编 `test_fallback_emits_event`：`call_log == [pro]×3 + [flash]` · 事件恰一次 from/to 不变 |
| 5 | `OPS_LLM_RETRY_ENABLED=false` 逐字节一致 | ✅ | `test_retry_disabled_byte_identical`：`created==1` · 零退避 |

### D2 · 熔断（5/5 PASS）

| # | 验收点 | 结论 | 证据 |
|---|--------|------|------|
| 1 | fail_max 次环境失败 → open · 随后零出网 · `circuit_open` retryable=False | ✅ | `test_env_failures_trip_breaker_then_zero_network`：`network_calls` 前后不变 · `state=="open"` · `blocked_calls ≥ 1` |
| 2 | advance 拨时间（不真等 60s）→ 探测成功 closed / 失败回 open | ✅ | `test_advance_then_probe_success_closes`（`advance("siliconflow",61)` → 200 → closed · fail_counter=0）· `test_advance_then_probe_failure_reopens` |
| 3 | 业务错误 × fail_max 以上不熔 | ✅ | `test_business_errors_never_trip`：6×401 · state closed · 6 次真出网 |
| 4 | 跳闸那次保根因（非 CircuitBreakerError 替换） | ✅ | `test_trip_call_keeps_root_cause`：跳闸次 status_code==503 · 无 circuit_open 字样 |
| 5 | snapshot 字段可断言 | ✅ | `test_snapshot_fields`：state/fail_counter/seconds_until_half_open/blocked_calls/scope |

### D3 · 路由（4/4 PASS）

| # | 验收点 | 结论 | 证据 |
|---|--------|------|------|
| 1 | grader 档命中 · `OPS_LLM_TIER_GRADER_MODEL` 覆盖 · `RAG_GRADER_MODEL` 兼容 | ✅ | `test_grader_tier_default_matches_legacy`（Qwen/Qwen3.6-27B · tier_default）· `test_env_tier_override` · `test_legacy_rag_grader_model_still_works`（source=rag_grader_model）· grade 节点三测 |
| 2 | answer/extract/structured 各档独立 · 未知 task/非法档回退+warning | ✅ | `test_each_tier_env_independent`（参数化四档）· `test_unknown_task_falls_back_with_warning` · `test_invalid_tier_env_falls_back_with_warning` |
| 3 | 未分档调用点逐字节一致 | ✅ | `test_answer_node_default_byte_identical`（默认全局 model）· `test_structured_default_byte_identical`（model=None 注入路径不动） |
| 4 | span metadata 含 task→model 决策与档来源 | ✅ | `test_answer_node_route_span_metadata` / `test_grade_node_route_span_metadata` 断言 route dict 全字段 |

### D4 · 成本归集（5/5 PASS）

| # | 验收点 | 结论 | 证据 |
|---|--------|------|------|
| 1 | chat run 两行同 run_id · task_type=answer/grader · tokens 与 fake 一致 · 按 run_id 聚合 | ✅ | `test_chat_run_two_calls_same_run_id`：两行 · `{answer,grader}` · tokens 逐字段等值 · 聚合合计 `(16, 9)` |
| 2 | lg_rag hex run_id 落行 `surface=lg_rag` 可区分 | ✅ | `test_lg_rag_surface_distinguishable` |
| 3 | 无 usage 末帧 → 无行（非 0 假账） | ✅ | `test_no_usage_frame_no_row`：answer 正常返回 · `_rows_for(run_id) == []` |
| 4 | 落表故障不挡主答 + log/计数 | ✅ | `test_persist_failure_does_not_block_answer`：answer=="Answer" · `persist_failure_count() ≥ 1` · caplog "ops_llm_usage persist failed" |
| 5 | alembic upgrade/downgrade 可逆 | ✅ | 本帽在 dev 库真跑往返（见质量门表） |

### 工程（5/5 PASS）

| # | 验收点 | 结论 | 证据 |
|---|--------|------|------|
| 1 | 闸前置：旧测影响面 12 条逐条处置 | ✅ | diff 实核：改编 #2（429/500/503+SSE+传输错 假时钟+次数/退避界）· #3 · #4（fail_max=99 隔离熔断+3×3 出网）· #6（`provider_calls==3`）· #10（conftest autouse `_reset_llm_circuit` 对齐 capability 先例）全落地；回归 #1/#5/#7/#8/#9/#11/#12 在全量跑中绿（#8 `provider.calls==1` 零重试风暴契约不破）；删除 0 条 |
| 2 | ruff + pytest 绿 | ✅（附注） | ruff 57=master 57 零新增；pytest 1137+1skipped 绿 · 3 failed 经 master worktree 对照证为基线环境性（见下「基线失败核验」） |
| 3 | 图谱 llm/db 行 + HG-GRAPH-MODULES 新行 + graph-compile 绿 | ✅ | `01_modules.md:32` llm 行四块机制备注 + 出边 +db · `:33` db 行登记 `ops_llm_usage` · `:88` HG-GRAPH-MODULES 新行 00 代录 approved（2026-09-21）· compile exit 0 |
| 4 | 新 env 非法值回退 + warning 全覆盖 | ✅ | retry 5 参数化 + circuit 3 env + routing 非法档/未知 task，均断言回退默认值且 caplog 含 invalid 警告 |
| 5 | 变异检验 | ✅ | **本帽亲自复做**：`base.py` 删 `or not exc.retryable` → `test_4xx_zero_retry` 真 fail（`assert 3 == 1`）→ `git checkout` 还原 → 13 条 retry 测复跑全绿 → 工作树干净 |

**勾选数：24/24 PASS。**

---

## 基线失败核验（3 条）

| 失败测 | 分支表现 | master worktree 表现 | 结论 |
|--------|----------|----------------------|------|
| `test_chat_ws.py::test_ws_message_streams_events` | AssertionError + `RuntimeError: Event loop is closed` | 同错复现 | **基线既有**（WS portal-loop 环境性），与本波无关 |
| `test_chat_ws.py::test_ws_second_message_while_active_rejected` | 同上 | 同错复现 | **基线既有** |
| `test_capability_http_adapter.py::test_urllib_transport_honors_explicit_capability_proxy` | FAILED | 同错复现 | **基线既有**（proxy 环境性） |

核验方式：`git worktree add /tmp/ops-desk-master master`（不动工作树、不 stash），用同一 `.venv` 对 master 代码跑同 3 测，全同错。置信度：**高**。worktree 已列入清理项（见残留）。

## failure_paths 抽查

| 路径 | 姿态 | 抽查 |
|------|------|------|
| 429/5xx/传输错退避重试 ≤ max_attempts | 自动 | ✅ D1-1/D1-4 |
| 4xx 其余/缺 key 零重试 | 原样上抛 | ✅ D1-2 + `test_missing_key_zero_retry` |
| 流中已吐正文后出错 | 零重试 · error 事件终结 | ✅ D1-3 |
| 重试耗尽抛原始错误 | 不包装丢根因 | ✅ `test_retry_exhaustion_raises_original_error`（status_code is None · 原文匹配） |
| 熔断 open 零出网 circuit_open | retryable=False | ✅ D2-1 |
| 业务错误风暴不熔 | closed | ✅ D2-3 |
| 路由档非法回退+warning | 不炸请求 | ✅ D3-2 |
| 落表异常不挡主答不静默 | log+计数 | ✅ D4-4 |
| 无 usage 末帧无行 | 不写 0 假账 | ✅ D4-3 |
| run 上下文缺失 | run_id=NULL · surface=background | ✅ `test_missing_context_background_surface` |
| 新 env 非法值 | 回退默认+warning | ✅ 工程-4 |
| 无变异检验却宣称有效 | 40 拒收 | ✅ 本帽亲自复做变异（工程-5） |

---

## 残留风险 / 关账注意

1. **3 条基线失败仍为红**（环境性 · master 同错）：建议维护者排期独立 fix 分支修 WS portal-loop 与 proxy 环境依赖，否则后续每波全量跑都带 3 红噪音。
2. `/tmp/ops-desk-master` worktree 为本帽核验所建，关账后可 `git worktree remove` 清理（本帽不留垃圾：已记录，由关账棒或维护者决定）。
3. `graph.json` 的 `generated_at` 时间戳漂移（graph-compile 副产物，内容零 diff）：本帽已 `git checkout` 还原，不混入 docs 提交；后续任何 graph-compile 真跑都会再脏该行，属既有工程现象。
4. `.coding-kit/events/` untracked（harness 运行时副产物，非本波交付），未纳入提交。
5. 承 30 遗留：重试默认参数（0.5s/8s/3 次）未经真实流量校准；ContextVar 在 lg_rag supervisor 并发下靠入口+节点双注入；占位价表偏差由手册 L8 另行——三条均继承 SPEC residual，非阻塞。

---

## 结论

**40 PASS-with-warnings** · 验收 24/24 · 3 红证为基线（高置信）· 变异检验亲自复做有效 · 工作树净（仅本帽两份 docs 待提交）· 未 commit 实现码 · 未 push · 未签闸 · 未 CLOSE
