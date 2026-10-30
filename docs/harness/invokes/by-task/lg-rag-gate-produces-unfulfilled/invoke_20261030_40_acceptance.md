# Invoke：40 验收⑤ live 复跑 — lg-rag-gate-produces-unfulfilled（2026-10-30）

| 字段 | 值 |
|---|---|
| hat_id | 40（live 实证 · 维护者 m00143「开始40」授权） |
| task_slug | `lg-rag-gate-produces-unfulfilled`（已 CLOSED · 本 invoke 核销维护者 checklist 验收⑤） |
| task_paths | `docs/tasks/done/task_lg_rag_gate_produces_unfulfilled.md`（验收⑤真值）· `docs/tasks/close/close_lg_rag_gate_produces_unfulfilled_20261030.md`（checklist） |
| git_branch | `master`（受验 HEAD = 30e1dea · 含 PR #297 squash 0a5d6109 + 姊妹 PR #294/#295/#296 全链） |
| created_utc_or_local | 2026-10-30 17:22–17:33（Asia/Shanghai） |
| env | uvicorn :8011（HEAD 码 · .env 真 key SiliconFlow DeepSeek-V4-Flash · langfuse tracer on）· dev 库 `opsdesk`（docker compose db+qdrant） |

---

## 总结论

**PASS**——验收⑤核销：复跑 #2140 query（`#2140 这个 issue 在说什么？调用write本地落盘结论`），**t2 write 实际执行成功、全程无 budget_exhausted、无 contract_missing_field 拦截**。对照钉案 run d3a49（635 事件 · 400s · budget_exhausted 死锁）：本次全程 19 事件、两段合计约 8.4 分钟（含人工审批间隔），死锁形态零复现。

## Run 事件链（run `25abecd64908416ba28100cecaf300a5` · thread `e385503beb7843ce8ce8f5e479c628a5`）

### 段一：发起 → HITL 挂起（seq 1–9 · latency 162s）

| seq | role | event | 要点 |
|---|---|---|---|
| 1 | system | run.start | query 落帧 |
| 2 | strategy_builder | node.progress | allowed=[utc_now_iso, mock_get_issue_status, mock_get_deploy_info, get_issue_by_number, get_pr_by_number, testing.write.echo] |
| 3 | supervisor | node.progress | 计划 2 步：**t1 get_issue_by_number produces=[title, body]（真实字段 · 无猜 status——task A 消猜生效）**；t2 testing.write.echo produces=[written] · consumes_resolved t1=[title, body] |
| 4–6 | subtask_join / tool_exec | t1 执行 done | get_issue_by_number(2140) 返回真实 issue（MoonshotAI/kimi-code#2140 · open · 标题 feat: support per-call model and thinking_level…） |
| 7 | subtask_join | t2 blocked | blocked_by=delegation_issue_hitl_required（write 能力审批 · 预期路径） |
| 8 | system | hitl.waiting | 单据 hitl_76bc2879d63c46fd8fd5 · unlock=t2 |
| 9 | system | done | status=waiting_approval · latency_ms=162069 |

**闸行为核验**：t1 produces [title, body] 与 t2 consumes 全命中 → 判定3 未触发（无拦截、无重规划循环）；契约链一次通过。

### 段二：批准 → resume → t2 执行 → 闭合（seq 10–19）

- decide：`POST /hitl/requests/hitl_76bc2879d63c46fd8fd5/decide` {decision:approved, resume_mode:manual} → 200（单据 thread_id 非空 = e385503b…）
- resume：`POST …/resume` → 200 accepted · replay.cursor=:9
- 恢复段写窗内 `POST /lg-rag/replay follow=false` → **409「Resume is writing new events; retry after it settles.」**（replay-resume-ux-opt F1 谓词 live 附带复验 PASS）

| seq | role | event | 要点 |
|---|---|---|---|
| 10 | system | hitl.resumed | approved=[t2] decided_by=admin |
| 11–13 | observe/supervisor/subtask_join | 解锁重跑 | 日志：HITL 已批准，解锁 1 步并从可恢复点重跑 |
| 14 | tool_exec | subtask.progress | **t2 testing.write.echo 执行 done**：args 携 t1 真实 title+body 注入；返回 written:false + note「语义 mock · 无真实写操作（testing-write-capability 测试专用）」（能力契约即如此 · testing.v1.yaml output_fields=[tool,input,written,note]） |
| 15–16 | subtask_join/observe | 观察回收 | |
| 17 | aggregator | answer | final:true · 答复如实陈述 t2 为 mock 未真实落盘（LLM 未粉饰） |
| 18 | critic | node.progress | |
| 19 | system | done | **status=resumed** · latency_ms=326522 · events_persisted=9 |

uvicorn 日志锚点：`HITL 恢复完成 request=hitl_76bc2879d63c46fd8fd5 … replay=25abecd64908416ba28100cecaf300a5:19`（17:32:57）。

## 与 d3a49 钉案对照

| 维度 | d3a49（修复前） | 25abecd6（本次） |
|---|---|---|
| 事件数 / 耗时 | 635 / 400s budget_exhausted | 19 / 162s+327s（含人工审批间隔） |
| t1 produces | 猜 [title,body,status] 未兑现 status | [title,body] 全真实（task A 消猜） |
| 闸判定3 | 拦死 t2 · 重规划两轮照抄 | 未触发 · 一次通过 |
| t2 write | 从未执行 | 批准链路后实际执行 done |
| 终态 | budget_exhausted | done{resumed} |

## 质量门与副作用披露

- ruff/全量对拍：本 invoke 零代码改动，不触发（承 CLOSE 档 ④ 在案结论）。
- 副作用（dev 库 `opsdesk`）：单据 hitl_76bc2879d63c46fd8fd5 已 approve 且 run 已闭合 done@19；为 admin 铸 session 行（2h 自过期 · 2026-10-30 19:22 CST 失效）；run 事件 19 行留存为证据。
- 环境复原：uvicorn :8011 已停；db/qdrant 容器已 stop（发起前 daemon 本为停止态）。
- OTel exporter 403（Forbidden）为既有环境噪音（trace exporter 端点拒收），与验收面无关。

**40 结论：验收⑤ PASS，CLOSE 档维护者 checklist 可核销。**
