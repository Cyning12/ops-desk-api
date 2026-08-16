# Task Audit R1：lc-evidence-http

> **task**：`docs/tasks/active/task_lc_evidence_http.md`  
> **日期**：2026-08-16 · 审查：00 统筹（维护者会话授权「签收 · 当前 agent 身为 00」）  
> **结论**：`pass` · 建议 `HG-AUDIT-R1=approved`

---

## 核对

| 项 | 审阅 |
|---|---|
| 上游 | 旁路 `lc_evidence_chain` 已合入 master（PR #33）；web freeze `lc-evidence-http-v1` 已签 |
| 范围 | 薄 HTTP `POST /api/ops/lc-evidence/invoke` · cookie 鉴权 · `{ok,data}` · **显式序列化 snippet** |
| 非范围 | 改 graph / SSE / tracing / 前端 / 改 prompt |
| 验收 | 401 / 422 / 200+snippet / refuse=200 / 500 envelope · 不改 `graph.py` · ruff/pytest/graph-compile |
| failure_paths | 未登录、空 query、refuse、上游失败、漏 snippet、误挂 chat/stream |
| freeze | `lc-evidence-http-v1`；变更须升 freeze_id |
| `wiki_delta` | `n/a` · `graph_change_layer=G-L1`（模块备注 + 契约消费方） |
| 思考轮 | R0–R5 闭合；`early_stop=no`；残余风险（snippet / 500 外壳）已写入 |

## 内容

**零阻塞。** 方案与 web SPEC §3.2 一致；专用 response schema 是正确选择（`EvidenceItem.snippet` 为 `@property`）。

## 流程闸

| 闸 | R1 时 | 00 签收 |
|---|---|---|
| HG-TASK-DRAFT | pending → 建议 approved | 本会话 00 代签 |
| HG-AUDIT-R1 | pending → 建议 approved | 本会话 00 代签（本审查文留痕） |
| HG-GRAPH-MODULES | approved | 保持 |

## 条件

- 30 不得 `ChainResult.model_dump()` 直接当 HTTP body
- 500 顶层 `{ok:false,error:{code,message}}`（勿只放在 FastAPI `detail` 里，前端按 envelope 拆）
- 与 `task/lc-evidence-langfuse-tracing` 分分支，不叠提交
- 人工联调 1 问为验收项；机械项不挡 40

## HG-AUDIT-R1 建议

**approved**（00 统筹 · 维护者授权代签 · 本文件留痕）
