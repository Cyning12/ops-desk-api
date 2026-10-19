# invoke · 30 retro · supervisor-first-fail-closed（2026-10-19）

> **帽**：30（实现）· experience_capture=required 经验捕获

## 做得对的

- **红测先行救了范围**：先把 TC1-TC11 落成红测再动码，D2 触发面（LLM 异常/解析失败/非法 tool id 三通道合一 `subtasks is None`）在写实现前就被测试钉死，实现时只需在唯一 `else` 分叉插 fail-closed，diff 极小。
- **00 定夺闭环**：枚举外 4 条旧测没有自行处置，先报 00 拿书面定夺再镜像改写；转绿阶段新发现的第 5 条（input_isolation ②）按同一定夺同类处理并 invoke 补记，可追溯。
- **baseline 对照法**：全量 16 红时，用 `git worktree` 挂 7b6b54b + 同 .env 跑同一批，14 条确认是本地 .env 污染（`LG_RAG_DELEGATION_TOKEN_MODE=enforce` 等）既有红，只有 2 条是真回归 —— 避免把环境污染误算进本 task。

## 教训（下次注意）

- **本地 .env 是测试污染面**：app/config.py `load_dotenv` 在 import 时生效，`LG_RAG_DELEGATION_TOKEN_MODE`/`OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS` 等会让「未知 key → []」「未知工具」类断言本地红。跑全量前先 `env` 对照或显式 override；CI 无 .env 才是真绿。
- **SSE 帧 data 是事件信封不是 payload**：新测试 `json.loads(data)["payload"]["stage"]`，信封（event_type/seq/cursor）与 payload 两层别混——一条 KeyError 换来的。
- **scenario 安全默认方向**：「无 intent 短路」只对 `None`/空 dict 生效；非 dict 垃圾 intent 必须保留旧的「视同 high 收紧」安全默认（test_malformed_intent_non_dict 钉着），短路条件写宽了会把安全默认短路掉。
- **嵌套 `with pytest.raises` 触发 SIM117**：红测阶段就写成 `with (..., pytest.raises(...)):` 合并形，省一轮 ruff 返工。

## 遗留风险

- `done.degraded` 仅在 single_rag 灾备时出现（正常终帧零 diff）；前端不识该键无碍，但 ops-desk-web 下游棒（00 记录：另 task 呈现 `error{stage:supervisor_plan}`）落地前，用户只能区分「error 终态」与「答完」。
- 灾备 single_rag 路径复用旧 fallback 打标（`supervisor_fallback=true`），与 fail-closed 的 `supervisor_plan_failed=true` 互斥由代码路径保证，无交叉测试（两档 env 互斥）。
