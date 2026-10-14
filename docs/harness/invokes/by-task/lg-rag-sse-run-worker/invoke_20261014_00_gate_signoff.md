# invoke · 00 · lg-rag-sse-run-worker · 人签代录（三闸 + D1–D3）

| 项 | 内容 |
|----|------|
| **时间** | 2026-10-14 |
| **帽** | 00（delegate-only · 未改实现码 · 未改旧 disconnect task） |
| **维护者令** | 「确认并授权重新签 D1」+ 此前「授权签收后续过程文档」 |
| **task** | `docs/tasks/active/task_lg_rag_sse_run_worker.md` |
| **审查** | 20 R1 **PASS-WITH-NITS** · `task_lg_rag_sse_run_worker_audit_R1_20261014.md` |

## 三闸

| human_gate_id | 落录 |
|---|---|
| HG-TASK-DRAFT | pending → **approved** |
| HG-AUDIT-R1 | pending → **approved** |
| HG-GRAPH-MODULES | pending → **approved**（30 须入册 `run_worker`） |

## 裁定

| ID | 已签 |
|----|------|
| **D1** | **A+B**（B 主 · A=补偿 · 不赌 ASGI） |
| **D2** | 成功普通 `done`；失败 `error{stage:lg_rag.worker_failed}`；补偿可 `done{status:'disconnected'}` |
| **D3** | **须同步开 web task**（本棒 api；CTA 另仓） |

## 关联

与 `task_lg_rag_sse_disconnect_completion` **co-CLOSE**（旧正文不改）。

## 验证

```text
npx --yes spec-wave@3.3.0 verify --target . --task docs/tasks/active/task_lg_rag_sse_run_worker.md
# 2026-10-14：VERIFY: PASS
```

## 下一棒

已派 **30**（B1：RunWorker + subscribe 拆分 · 红测先行）

本窗未改实现码 · 已派子 Agent：30
