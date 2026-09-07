# Task：lg-rag T5.1 · 终答 delta 实时投递 SPEC（pacing / anti-buffer）

> **状态**：completed（2026-09-01 CLOSE · SPEC 随 T5.1 实现 [#122](https://github.com/Cyning12/ops-desk-api/pull/122) 落地）  
> **类型**：Spec 增量签收（**docs-only** · 无 30）  
> **上游**：[`05_lg_rag_transport_and_session_plan_v0.md`](../../spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md) §4.2 · §10.4 · §11  
> **前置**：T5 CLOSE · [`task_lg_rag_sse_token_stream`](./task_lg_rag_sse_token_stream.md) · [#105](https://github.com/Cyning12/ops-desk-api/pull/105)；web T5 打字机已合；联调观察（2026-09-01）「有 delta 帧仍一次性出全文」  
> **分支**：`task/lg-rag-sse-delta-realtime-spec`  
> **帽子**：00 起草闸；**10-spec** 落盘 05；**20-spec-audit** 审；本波 **无 30**。  
> **无关**：改 `app/**` · 开实现 PR · 新 `event_type` · 新 freeze · web/iOS 假打字机 · 改 replay / `thread_id` / `cursor` 语义

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lg-rag-sse-delta-realtime-spec` |
| **git_branch** | `task/lg-rag-sse-delta-realtime-spec` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `n/a` |
| **test_strategy_note** | docs-only SPEC 增量；无代码改动；验收=05 §10.4.1 章节齐全 + §11 T5.1 勾选 + 20-spec-audit + 维护者可后签 HG-SPEC-SIGNOFF |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | docs-only 契约增量；不改模块表 / flow / indexes（实现波若改 stream 符号再按 05 §9.3 T5 钩） |
| **wiki_delta** | `docs/coding_wiki/volatile.md` |
| **wiki_delta_note** | 另补 `docs/coding_wiki/context.md` 链 05 §10.4.1；真值在 05，wiki 只指针不双份正文 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,00` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | `lg-rag-sse-v1`（**不**新 freeze；不新 event_type；不改 delta/content/final 键语义） |
| **close_pr_policy** | `required` |
| **related_pr** | （待开 docs PR） |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 本波仅 05 落盘；实现缺口另 task（建议 slug `lg-rag-sse-delta-realtime`）；与 T6/C 轨正交 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | — | 2026-09-01 · **00 代签 · 维护者 Prompt 授权**（api 00/10-spec · T5.1 docs-only） |
| HG-SPEC-SIGNOFF | **approved** | — | 2026-09-01 · **00 代签 · 维护者令「签收」** · 见 `docs/harness/reviews/task_lg_rag_sse_delta_realtime_spec_audit_R1_20260901.md`（pass · 内容零阻塞） |
| HG-AUDIT-R1 | n/a | 30 | 本波 **无 30**（docs-only）；实现另 task 再开此闸 |
| HG-GRAPH-MODULES | n/a | — | 无图谱变更 |

---

## 00 定夺（已落入 05 §10.4.1）

| 项 | 钉死 |
|---|---|
| **slug（本波）** | **`lg-rag-sse-delta-realtime-spec`**（docs-only） |
| **实现 slug（建议 · 不强制本波创）** | `lg-rag-sse-delta-realtime` · 分支 `task/lg-rag-sse-delta-realtime` |
| **SoT** | 打字机观感跨端 SoT = **SSE 上 delta 的到达时间线**；前端定时器缓冲 **非**协议义务 |
| **吐出时效** | chunk → sink → emit → **尽快 yield**；禁止「节点整段完成后再一次性吐全部 delta」为默认 |
| **burst** | 终答窗口内客户端时间戳同秒倾泻、而 provider 流式跨秒 → 投递层异常/缓冲，非默认「解析失败」 |
| **降级** | 允许整段 `content`（T2）+ 日志可观测；禁止静默攒 chunk 却声称 T5 流式成功 |
| **freeze** | 沿用 `lg-rag-sse-v1`；不新 freeze；不新 `event_type` |
| **非目标** | web 假打字机入契约 · token 化 progress · 改 replay 形状 · 改 thread_id/cursor |

---

## 范围

1. 修订 `05_lg_rag_transport_and_session_plan_v0.md`：§4.2 `answer` 旁注 · **§10.4.1 T5.1** · §8 / §11.4 修订表 · §11.3 T5.1 勾选  
2. wiki 短注：`coding_wiki/volatile.md` + `context.md` 指针  
3. WAVE_READINESS 路径表补 §10.4.1（不重开 T5/T6 闸）  
4. 20-spec-audit 审查文 + HG-SPEC-SIGNOFF（**已签**）

## 非范围

- 改 `app/**` / `tests/**` · 开实现 PR  
- 新增 `event_type`（如 `answer.delta`）· 新 freeze · 改 `delta`/`content`/`final` 键语义  
- 要求客户端强制假打字机  
- 改 web / iOS 代码 · 改 nginx 现网（SPEC 给检查清单；运维另波）  
- 处理联调业务错误（如 RAG DB 事务 aborted）  
- 本波创建实现 task（仅建议 slug）

---

## 验收标准

- [x] 05 含 **§10.4.1 T5.1**（背景/动机 · 00 定夺表 · 吐出时效 · burst 定义 · 降级 · 框架层攒批默认 · 代理检查清单 · 常见坑 · 实现候选触点 · 应然 vs 实然）  
- [x] §4.2 `answer` 行旁注：delta 须持续刷出、不得等节点结束批量 flush  
- [x] §8 修订表 2026-09-01 行（动机 = 防 burst + 跨端通用，非改 event_type）  
- [x] §11.3 T5.1 可勾选验收 ≥5 条（live 时间线 · mock 慢 chunk · 降级日志 · replay 形状 · 反代检查项）  
- [x] `docs/harness/reviews/` 落 20-spec-audit 且结论 pass  
- [x] HG-SPEC-SIGNOFF=approved（00 代签 · 维护者令「签收」）  
- [x] `app/` · `tests/` **零改动**  
- [x] `npx --yes dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_lg_rag_sse_delta_realtime_spec.md` 通过（W4 合法）  
- [x] `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` 通过  

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 把前端假打字机写入契约 | 05 红线；20 审退回 | — | SPEC 非目标表 |
| 新增 event_type / 新 freeze | 停写 · 短报维护者 | — | 本 task 非范围 |
| 范围蔓延到 `app/**` | 拒改码；实现另 task | — | PR / diff 检查 |
| 用户口头「开工实现」 | ≠ 闸；本波无 30；HG-AUDIT-R1 仍 n/a | — | 人工闸表 |
| 声称与 05 定夺冲突 | STOP · 以 05 §10.4.1 表为准 | — | — |

---

## 给执行帽的必读列表

1. 本 task（含 **00 定夺**）  
2. `docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §4.2 · §10.4.1 · §11.3  
3. 只读对照（不改）：`app/ops/lg_rag/answer_stream.py` · `sse_stream.py` · `router.py`  
4. nginx 指针：`ops-desk-workspace/deploy/nginx/ops-desk.conf`（仓外 · `proxy_buffering off`）

---

### 自检结论

> **10-spec** · 2026-09-01 · 分支 `task/lg-rag-sse-delta-realtime-spec` · docs-only · 无 30  
> **签收后**：HG-SPEC-SIGNOFF=**approved**（00 代签 · 维护者令「签收」· 2026-09-01）· 20 审查 pass

**05 章节核对**

- [x] §2 波次表 T5.1 行  
- [x] §4.2 `answer` 旁注 + T5.1 冻结补充  
- [x] §8 修订表 2026-09-01  
- [x] §10.4 表交叉 T5.1 · **§10.4.1** 全文  
- [x] §11.3 T5.1 勾选 · §11.4 修订行  

**00 定夺落 SPEC**

| 00 定夺项 | SPEC 落点 | 结果 |
|---|---|---|
| SoT = SSE 到达时间线 | §10.4.1 定夺表 SoT | ✅ |
| 尽快 yield · 禁节点结束批量 flush | 吐出时效 + §4.2 旁注 | ✅ |
| burst 定义 | 定夺表 burst | ✅ |
| 降级可观测 · 禁静默攒帧称 T5 成功 | 定夺表降级 | ✅ |
| 代理检查清单 | §10.4.1 部署表 | ✅ |
| 默认不攒批 | 框架层节 | ✅ |
| freeze `lg-rag-sse-v1` | T5.1 冻结补充 | ✅ |
| progress ≠ 投递失败 | 与 progress 关系 | ✅ |
| 红线 / 实现另 task | 非目标 + 实现波次 | ✅ |

**禁区**

- [x] 无 `app/` · `tests/` diff（本帽结束时核对）  
- [x] 无新 event_type / 新 freeze  
- [x] invoke 落盘：`docs/harness/invokes/by-task/lg-rag-sse-delta-realtime-spec/`（00 + 10-spec）
- [x] `task lint` PASS（W4）· `lint-wiki-delta` PASS（scanned=104 · issues=0）
- [x] 下一棒曾为 20-spec-audit → **已完成**；HG-SPEC-SIGNOFF 已签  
- 关账：开 docs PR → merge → `task close`；实现缺口另开 `lg-rag-sse-delta-realtime`（须维护者令「开工」）

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-01 | **00+10-spec**：维护者 Prompt 授权落盘 05 T5.1；本 task 起草；HG-TASK-DRAFT 代签；HG-SPEC-SIGNOFF pending |
| 2026-09-01 | **20-spec-audit** pass · **HG-SPEC-SIGNOFF=approved**（00 代签 · 维护者令「签收」）；不授权 30；实现另 task |
