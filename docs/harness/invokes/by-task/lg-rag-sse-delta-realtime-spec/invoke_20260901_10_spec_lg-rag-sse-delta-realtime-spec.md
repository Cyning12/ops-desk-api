# Invoke：10-spec · lg-rag-sse-delta-realtime-spec（T5.1）

---

## 元信息表

| 字段 | 值 |
|---|---|
| hat_id | 10-spec |
| task_slug / spec_slug | `lg-rag-sse-delta-realtime-spec` |
| task_paths | `docs/tasks/active/task_lg_rag_sse_delta_realtime_spec.md` |
| related_review_or_none | 无（本帽结束后交 20-spec-audit） |
| git_branch | `task/lg-rag-sse-delta-realtime-spec` |
| created_utc_or_local | 2026-09-01 |
| notes | docs-only · 无 30；不新 freeze / 不新 event_type；05 主写回 §10.4.1 |

---

## 裁决

- 问题在 **投递时效 / 缓冲**，非缺 `event_type`、非 web 解析失败的默认结论。  
- 跨端 SoT = SSE 上 delta **到达时间线**；禁止把前端假打字机写入契约。  
- 真值落点 = 既有 `05`（不另开平行真源文件）。  
- 本窗 **禁 30**；不改 `app/` / `tests/`；不签发 HG-SPEC-SIGNOFF。

## 结论摘要

05 §10.4.1 钉死：尽快 yield、burst 验收定义、降级可观测、默认不攒批、反代/Vite 检查清单、progress 与终答阶段分离、实现另 task `lg-rag-sse-delta-realtime`。  
应然 vs 实然：sink 竞速 yield 意图对齐；缺口候选 = emit 路径 persist-before-yield + 中间层缓冲。

## 交付

- `docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md`（§4.2 / §8 / §10.4.1 / §11）  
- `docs/spec/agent-infra/WAVE_READINESS_lg_rag_sse_v0.md` 路径表补 T5.1  
- wiki：`docs/coding_wiki/volatile.md` · `context.md`  
- task + 本 invoke  
- 下一棒：**20-spec-audit**

## 可复制 Prompt 快照（下一棒）

hat_id：20-spec-audit  
task_slug：lg-rag-sse-delta-realtime-spec  
本帽禁区：不改 SPEC 实质内容；不代签 human_gate；结论落盘 `docs/harness/reviews/`

必读：`docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §4.2 · §10.4.1 · §11.3  
`docs/tasks/active/task_lg_rag_sse_delta_realtime_spec.md`（00 定夺逐项核对）

只做什么：
1. 书面审 05 T5.1：范围/非目标/验收/burst 定义/代理清单是否可执行
2. 逐项核对 00 定夺落入情况（SoT · 吐出时效 · freeze · 红线）
3. 核对未新 event_type / 未新 freeze / 未改 delta 键语义
4. 审查文落盘，结论 pass / 阻塞项

禁止代签 HG-SPEC-SIGNOFF。禁止改 `app/**`。

## 签收栏

**20-spec-audit** pass（`task_lg_rag_sse_delta_realtime_spec_audit_R1_20260901.md`）  
**HG-SPEC-SIGNOFF=approved** · 00 代签 · 维护者令「签收」· 2026-09-01

---

## 交付摘要

| 项 | 内容 |
|---|---|
| **验证** | `task lint --file docs/tasks/active/task_lg_rag_sse_delta_realtime_spec.md` → exit **0** · **PASS**（W4：无思考轮节 · SPEC §10.4.1 承载合法）；`task lint-wiki-delta --target .` → exit **0** · **PASS**（scope=all · scanned=104 · issues=0） |
| **变更路径** | 05 · WAVE_READINESS · coding_wiki volatile/context · task · 本 invoke · 00 invoke |
| **未改** | `app/` · `tests/` · 图谱 · freeze 字段语义 · 人工闸 HG-SPEC-SIGNOFF（仍 pending） |
| **内容可交 20** | 是 |
| **需 00 定夺** | 是否开实现 task `lg-rag-sse-delta-realtime`（本波仅建议） |
| **下一棒** | 20-spec-audit |

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-01 | 10-spec 首稿：05 §10.4.1 落盘 · task 自检 · 交 20 |
