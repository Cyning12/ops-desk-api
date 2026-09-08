# Invoke · 40 · lg-rag-sse-subtask-message

- **hat**：40（自检验收 + 收口）
- **task_slug**：`lg-rag-sse-subtask-message`
- **日期**：2026-09-08
- **分支**：`task/lg-rag-sse-subtask-message`（已核对 `git branch --show-current`）

## 质量门（本帽真跑 · 退出码实录）

| 命令 | 退出码 | 结果 |
|---|---|---|
| `uv run pytest tests/test_lg_rag_sse_subtask_message.py -q` | **0** | 20 passed |
| `uv run pytest tests -q`（全量） | **1** | 653 passed / 2 failed / 1 skipped；2 失败均为 `tests/test_chat_ws.py` WS 用例（`test_ws_message_streams_events` · `test_ws_second_message_while_active_rejected`）——**存量本地环境失败**，00 已 stash 对照验证干净树同样失败，本波未触碰 chat/ws 路径；PR #129 CI pytest 绿 |
| `uv run pytest tests -q -k "lg_rag or keepalive or delta"`（相关子集） | **0** | 133 passed / 523 deselected |
| `uv run ruff check app/ops/lg_rag tests/test_lg_rag_sse_subtask_message.py`（触及路径） | **0** | All checks passed |
| `uv run ruff check app tests`（全量） | **1** | 2 errors 均为**存量**：`app/ops/rag/tokenizer.py` UP035 · `tests/test_rag_chunker.py` I001，本波未触碰这两个文件 |
| `./scripts/graph-compile.sh` | **0** | 9 graphs · 132 nodes · 194 edges · check 全 OK · mermaid normalize ok |
| `npx --yes dsh-coding-kit task lint-wiki-delta --target .` | **0** | PASS（scope=all · scanned=109 · issues=0） |
| `npx --yes dsh-coding-kit verify --target . --task docs/tasks/active/task_lg_rag_sse_subtask_message.md` | **0** | VERIFY: PASS（三闸均 approved） |
| `npx --yes dsh-coding-kit task lint --file docs/tasks/active/task_lg_rag_sse_subtask_message.md` | **0** | LINT: PASS（W3 占位符 warn 于本轮回填后消解） |

> 注：`dsh-coding-kit task verify --task` 子命令在本版 CLI 不存在（exit 1 · 报「子命令未知」），按仓内既有惯例以顶层 `verify --target . --task <file>`（30 同款）与 `task lint --file` 为实际 verify 门，均 PASS。

## 验收标准逐条对照（task 文档 8 条）

| # | 验收标准 | 结论 | 证据 |
|---|---|---|---|
| 1 | `lint-wiki-delta --target .` 通过 | ✅ | exit 0 · PASS（scanned=109 · issues=0） |
| 2 | mock：`status=running` 帧含非空 `message` | ✅ | `test_emit_running_frame_has_message`（sink 断言 payload.message 非空且含 type/input 摘要）；`test_running_message_type_and_input` / `test_running_message_unknown_type_fallback` |
| 3 | mock：`status=step` 帧（含 `detail.phase` / `gate_action`）含可读 `message`，与 detail 数字/动作一致 | ✅ | `test_emit_step_frame_message_matches_detail`；`test_step_retrieve_start`（「开始检索…」）· `test_step_retrieve_done_hit_count`（命中数 5 入文案）· `test_step_grade_done_gate_action_semantics`（kept_count=3 + 「部分作答」/「拒答」）· `test_step_rewrite_current_query` · `test_step_answer_done_chars` |
| 4 | mock：`status=done` 帧含非空 `message` | ✅ | `test_map_node_update_done_has_message`（sse_stream done 挂载）· `test_done_message_from_subtask_result_output` · `test_done_message_extract_dict_output` · `test_done_message_error` · `test_done_message_bare_fallback_non_empty`（兜底禁空串） |
| 5 | `message` 超长被截断（单测） | ✅ | `test_message_truncated_at_max_len` 断言 `SUBTASK_MESSAGE_MAX_LEN = 200` 上限（R1-N3 收入） |
| 6 | 05 §10.7 落盘；旧客户端兼容说明（忽略未知键） | ✅ | 05 §10.7 增补段（2026-09-08）：payload 表 message 行 + 「**旧客户端忽略未知键即可，无需升级**」+ 联调项 + §11.4 修订记录行 |
| 7 | ruff · 相关 pytest · graph-compile | ✅（带存量标注） | 触及路径 ruff exit 0；全量 ruff exit 1 = 2 处既有问题（tokenizer UP035 · test_rag_chunker I001，非本波文件）；相关 pytest 20+133 passed；graph-compile exit 0 |
| 8 | keepalive / T5 delta / step 旧测不回归 | ✅ | `-k "lg_rag or keepalive or delta"` 133 passed；全量 653 passed，仅 `test_chat_ws.py` 2 例存量本地失败（与本波无关，00 对照验证） |

**勾选数：8 / 8**（第 7、8 条附存量失败如实标注，非本波引入）。

## 存量问题声明（非本波 · 不修）

1. `tests/test_chat_ws.py` 2 个 WS 用例本地环境失败（干净树同败 · CI 绿），与 lg-rag SSE 无关。
2. ruff 全量 2 errors：`app/ops/rag/tokenizer.py:11` UP035 · `tests/test_rag_chunker.py:7` I001（既有，按 P-07 不顺手改）。
3. `uv.lock` 为环境副作用变动，**不入本次提交**。

## 残余风险

- 文案词典粒度有限，未知 step 仅兜底短句（含 step 名）；web 未消费前仅 api 可观测（web task 后置，不阻塞本仓）。
- done 摘要基于 `subtask_result` 轻量键，可能与 `output` 首句重复（可接受）。
- message 生成异常路径已测降级（`test_emit_step_message_failure_degrades` / `test_map_node_update_done_message_failure_degrades`），帧仍发不中断节点。

## 收口动作

- task 文档「### 自检结论（执行者）」已回填（帽 40-self-check）。
- 验收复选框 8 条逐条核对后勾选。
- 提交：`feat(lg-rag): subtask.progress 可选可读 message（确定性模板 · §10.7）`（排除 uv.lock）→ push `task/lg-rag-sse-subtask-message`；**不开 PR**（close_pr_policy=required 留待人签 / 维护者指令）。
