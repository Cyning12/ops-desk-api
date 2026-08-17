# Invoke：50 · lc-evidence-chain-hardening

> **hat_id**：50  
> **审查**：00 独立机械复检 · **不**改 `app/` 业务码

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 50 |
| task_slug | `lc-evidence-chain-hardening` |
| freeze_id | `lc-evidence-http-v1`（保持，未升） |
| task_paths | `docs/tasks/active/task_lc_evidence_chain_hardening.md` |
| related_review_or_none | `docs/harness/reviews/task_lc_evidence_chain_hardening_audit_R1_20260817.md` |
| git_branch | `task/lc-evidence-chain-hardening` |
| worktree_root | `.` |
| created_utc_or_local | 2026-08-17 |
| notes | 00 复检；Langfuse token 人工项不挡关账 |

---

## 复检（对照验收 · 抽读实现）

| 验收 | 50 | 证据 |
|---|---|---|
| D1 usage 上报；返回仍 `str`；两 Provider 一处 helper | **pass** | `BaseProviderImpl._complete_from_stream`；siliconflow/bailian `complete()` 只调 helper；lazy import tracing |
| tracing 关不上报不抛 | **pass** | `_report_complete_usage` 先 `tracing_enabled()`；单测 `test_complete_usage_silent_when_tracing_off` |
| D2 grader 异常 → refuse / HTTP 200 | **pass** | `_grade_chunks_llm` except → `[]`；`test_ainvoke_grader_llm_error_refuses`；`test_invoke_grader_llm_error_is_200` 走真实 ainvoke |
| answer/retrieve 仍 500 | **pass** | `test_invoke_upstream_failure_envelope` 仍在 |
| D3 kept 降序 + 同档稳定 | **pass** | `sorted(..., reverse=True)`；`test_decide_kept_orders_exact_before_relevant_stable` 期望 `[2,4,1,3]` |
| 不改 `graph.py` | **pass** | `git diff origin/master -- app/ops/chat/graph.py` 空 |
| freeze 未升；无 CE→EXACT | **pass** | 备注仍 `lc-evidence-http-v1`；grader 无 `rerank_score` |
| G-L1 一句 + compile | **pass** | `01_modules.md` 两行备注；`graph-compile.sh` OK |

## 00 独立重跑（2026-08-17）

| 命令 | 退出码 | 输出 |
|---|---|---|
| 主仓 `.venv/bin/ruff check` 触及路径 | 0 | All checks passed |
| 主仓 `.venv/bin/pytest` 三文件 `-q` | 0 | **48 passed** in 0.12s |
| `git diff origin/master -- app/ops/chat/graph.py` | 0 | 空 |
| `./scripts/graph-compile.sh` | 0 | OK: 00_main / 10_flow_auth / 10_flow_chat / 11_flow_sync_to_chat |
| `npx @cyning/harness verify --target . --task docs/tasks/active/task_lc_evidence_chain_hardening.md` | 0 | VERIFY: PASS |

**50 结论：PASS（机械）** · Langfuse UI token 为人工可选，不挡 CLOSE。

---

## 下一棒

`harness task close` → 提交 → PR 合入 `master`（禁止直推 master）。
