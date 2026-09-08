# Task：lg-rag SSE · subtask.progress 可读 `message`

> **状态**：active（2026-09-08 · 维护者授权 00 统筹 · 00 代签闸）  
> **类型**：传输 / 子任务过程可读文案  
> **上游**：[`05_lg_rag_transport_and_session_plan_v0.md`](../../spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md) **§10.7**（拟增补 `message`）  
> **前置**：`lg-rag-sse-subtask-steps`（`status=step` + detail 已合 · PR [#127](https://github.com/Cyning12/ops-desk-api/pull/127)）  
> **分支**：`task/lg-rag-sse-subtask-message`（实现时切出；本草稿可先落盘）  
> **帽子**：10 起草 → 人签闸 → 20（可选）→ 30+40  
> **授权**：维护者令「身为 00 统筹 api 和 web 的任务 task_lg_rag_sse_subtask_message · 授权签收后续文档，直至完成并 PR」（含闸表 / 过程 invoke·reviews 代签；**不含**未明示的 00 亲自 30 改码）  
> **无关**：LLM 真·思考链 token · 新 `event_type` · web UI 实现 · 改 step/detail 语义 · 改 keepalive/idle

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lg-rag-sse-subtask-message` |
| **git_branch** | `task/lg-rag-sse-subtask-message` |
| **implement_repo** | `ops-desk-api`（api-first；web 另 task 消费 `message`） |
| **test_strategy** | `required` |
| **test_strategy_note** | mock emit：`running`/`step`/`done` 帧含非空 `message`；文案由 step+detail 确定性生成；截断上限可断言；旧测不要求无 message；不连真 LLM |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` · `10_flow_lg_rag` 备注 |
| **graph_delta_note** | 不新增一级模块；`emit_*` / message 辅助函数进 G-L2 indexes（若新增符号） |
| **wiki_delta** | `docs/coding_wiki/volatile.md` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,00,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | `lg-rag-sse-v1`（不新 freeze；不新 event_type；payload 增可选 `message`） |
| **close_pr_policy** | `required` |
| **related_pr** | （待开） |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | api-first |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-09-08 · **00 代签 · 维护者授权签收后续文档** |
| HG-AUDIT-R1 | **approved** | 30 | 2026-09-08 · **00 代签 · 维护者授权签收后续文档** · R1 [pass-with-notes](../../harness/reviews/task_lg_rag_sse_subtask_message_audit_R1_20260908.md) · N1–N3 收入定夺/必读 |
| HG-GRAPH-MODULES | approved | — | 不新增一级模块 · **00 代签**（仅 G-L1 备注 + G-L2 indexes 若增符号） |

---

## 背景与目标

`subtask.progress` 已有 `status=running|step|done` 与 `step`/`detail`，但**无现成可读句子**。前端若要「打印思考/过程」，只能本地映射或空白。本波在 **api** 为各进度帧增加可选 **`message`（中文短句）**，由 `step`+`detail`（及 running/done 上下文）**确定性模板**生成，旧客户端忽略未知键即可。

完成态：EventStream 上同 `subtask_id` 的过程帧可直接 `append(message)` 上屏，无需 web 维护完整 step 词典（web 仍可覆盖展示）。

---

## 00 定夺（草案 · 待人签）

| 项 | 钉死（草案） |
|---|---|
| **slug** | `lg-rag-sse-subtask-message` |
| **字段** | `payload.message`：可选 `string`；UTF-8；**截断上限钉死 200 字**（R1-N3：常量 `SUBTASK_MESSAGE_MAX_LEN = 200`，单测断言无歧义） |
| **哪些帧** | `running` / `step` / `done` **均应尽量带**；缺映射时可用兜底短句（如「子任务进行中」/「步骤：{step}」），**禁止**空字符串冒充有内容 |
| **生成方式** | **确定性模板**（代码内映射表）；**禁止**再调 LLM 写「思考」；**禁止**把模型 CoT / raw prompt 塞进 `message` |
| **step 示例** | `retrieve`+`phase:start`→「开始检索…」；`retrieve`+`phase:done`+`hit_count`→「检索完成，命中 N 条」；`grade`+`gate_action`→含动作语义；`rewrite`+`current_query`→「改写查询：…」（query 截断） |
| **running / done** | running：含 type/input 摘要的一句；done：一句结果摘要（可基于 `subtask_result` 轻量键，勿塞全文 evidence） |
| **契约** | 05 §10.7 增补 `message` 行；freeze 仍 `lg-rag-sse-v1` |
| **机制** | 集中在 `progress_stream`（或同目录小模块）生成后写入 payload；`emit_subtask_running` / `emit_subtask_step` / done 映射处调用；**模板生成必须纯同步**（R1-N2：done 挂载点 `map_node_update` 为纯同步函数） |

---

## 范围

1. 05 §10.7：payload 表增可选 `message`；联调项补「过程区可见中文短句」  
2. `progress_stream`（及 done 映射路径）：生成并挂载 `message`  
3. 单测：关键 step/detail 组合断言 `message` 非空且含关键数字/动作词  
4. G-L1 备注 + volatile 短注  

## 非范围

- 新 `event_type` / 新 freeze  
- 子任务内 token 级「思考流」或假打字机  
- web 仓 UI（另开 `web-lg-rag-sse-subtask-message` 或并入既有 web task）  
- 改 `step`/`detail` 结构语义（仅消费它们生成文案）  
- 改 idle / keepalive / aread 行为  

---

## 验收标准

- [ ] `npx --yes dsh-coding-kit task lint-wiki-delta --target .` 通过  
- [ ] mock：`status=running` 帧含非空 `message`  
- [ ] mock：至少一帧 `status=step`（含 `detail.phase` 或 `gate_action`）含可读 `message`，且与 detail 数字/动作一致  
- [ ] mock：`status=done` 帧含非空 `message`（或文档钉死「done 可选」且测覆盖声明）  
- [ ] `message` 超长被截断（单测）  
- [ ] 05 §10.7 落盘；旧客户端兼容说明（忽略未知键）  
- [ ] ruff · 相关 pytest · graph-compile（若动 yaml）  
- [ ] keepalive / T5 delta / step 旧测不回归  

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 未知 `step` / 缺 detail | 兜底短句（含 step 名）；不抛 | — | 仍有一行过程文案 |
| `message` 生成异常 | 打日志；帧仍发（可无 message）；不中断节点 | 是 | 过程可能仅见 step 码 |
| 误塞 evidence 全文进 message | 拒合入；截断/测拦 | — | — |
| HG-AUDIT-R1 pending 即 30 | **拒开工** | 是 | 须先人签 |

---

## 给执行帽的必读列表

1. `AGENTS.md` · `docs/standards/CODING_BACKEND_L2_v1_zh.md`  
2. 05 §10.7（现行 running/step/done）  
3. `app/ops/lg_rag/progress_stream.py` · `app/ops/lg_rag/sse_stream.py` map done · `app/ops/lc_evidence_chain/step_hook.py`（R1-N1 路径修正）  
4. 前置 task：`docs/tasks/active/task_lg_rag_sse_subtask_steps.md`（或归档后 `done/`）  

---

## 依赖与协作

| 项 | 说明 |
|---|---|
| api | 本 task |
| web | 消费 `message` 直接上屏；可后置；不阻塞本仓合入 |
| 前置归档 | 建议 CLOSE/归档 `lg-rag-sse-subtask-steps` 后再开本波 30（非硬阻塞草稿） |

---

## 思考轮控制

| 项 | 值 |
|---|---|
| **rounds_planned** | R0–R1 |
| **early_stop** | yes |
| **early_stop_reason** | 方案 B 已由维护者选定；字段与生成方式边界清晰；残余为文案词典粒度 |
| **residual_risks** | 文案过简/过噪；done 摘要与 `subtask_result.output` 重复；web 未跟进时仅 api 可观测 |

### R0

- **问题**：前端要打印过程但 payload 无可读正文。  
- **结论**：api 增可选 `message`；确定性模板；不新 event_type。  

### R1

- **问题**：message 是否 LLM 生成？是否改 step 枚举？  
- **结论**：否 / 否；只消费既有 step+detail；截断防噪声。  

---

### 自检结论（执行者）

（30/40 回填 · draft 阶段空）

### KPI（00）

（CLOSE 回填）

### 经验总结

（CLOSE 回填 · 若 `experience_capture=required`）

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-08 | **10-task**：维护者选 B；落盘 draft · 闸 pending |
| 2026-09-08 | **00**：维护者令统筹并授权签收后续文档；代签 HG-TASK-DRAFT / HG-GRAPH-MODULES；前置 subtask-steps CLOSE（#129）；HG-AUDIT-R1 待 20 R1 落盘后代签 |
| 2026-09-08 | **20 R1** pass-with-notes（0 阻塞 · N1 必读路径 / N2 同步约束 / N3 截断常量 200）→ 全收入 · **00 代签 HG-AUDIT-R1** |
