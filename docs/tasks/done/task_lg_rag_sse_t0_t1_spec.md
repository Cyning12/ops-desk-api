# Task：lg-rag 传输主线 · T0+T1 Spec 签收（含 Obs-I/O 优先级）

> **状态**：completed（2026-08-30 · **HG-SPEC-SIGNOFF approved** · 维护者令「签收」）  
> **类型**：Spec / 规划签收（**docs-only**）  
> **上游**：`docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md`  
> **分支**：`task/lg-rag-sse-t0-t1-spec`  
> **帽子**：**00 统筹**；本波 **未**改 `app/`。  
> **无关**：E5；chat 兼容；T2 实现码；单独 Obs-I/O task。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lg-rag-sse-t0-t1-spec` |
| **git_branch** | `task/lg-rag-sse-t0-t1-spec` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `n/a` |
| **graph_change_layer** | `none` |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `00` |
| **orchestration** | L0 `05` + session ROADMAP；**Obs-I/O 不单开 task** |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | — | 2026-08-30 · 00 代签 |
| HG-SPEC-SIGNOFF | **approved** | — | 2026-08-30 · **00 代签 · 维护者令「签收」** · 真值 `05` |
| HG-AUDIT-R1 | n/a | — | 本波无 30 |
| HG-GRAPH-MODULES | n/a | — | 无图谱变更 |

---

## 验收

- [x] `05` 含优先级表与 T0/T1 条文  
- [x] session 主线 ROADMAP 存在且声明非 chat 兼容  
- [x] H3 ROADMAP 标注归档参考  
- [x] `HG-SPEC-SIGNOFF=approved`

---

## CLOSE

| 项 | 值 |
|---|---|
| 签收 | 2026-08-30 · 维护者「签收」 |
| PR | （docs · 待维护者令提交/开 PR） |
| 下一棒 | 00 拆 `lg-rag-sse-stream-updates`（T2 · 验收含 Obs-I/O）；**须维护者令「开工」** |
