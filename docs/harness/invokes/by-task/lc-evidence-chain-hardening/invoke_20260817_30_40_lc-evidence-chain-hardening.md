# Invoke：30（含 40）· lc-evidence-chain-hardening

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `lc-evidence-chain-hardening` |
| freeze_id | `lc-evidence-http-v1`（保持，未升） |
| task_paths | `docs/tasks/active/task_lc_evidence_chain_hardening.md` |
| related_review_or_none | `docs/harness/reviews/task_lc_evidence_chain_hardening_audit_R1_20260817.md` |
| git_branch | `task/lc-evidence-chain-hardening` |
| created_utc_or_local | 2026-08-17 |
| notes | 子 agent 30+40；未 commit / 未 push；Langfuse UI token 为人工项 |

---

## GATE_VERIFY（首输出 · 读 task 表）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved（00 代签） | Y | N（blocks 22-R1） | Y |
| HG-AUDIT-R1 | approved | approved（00 代签） | Y | Y | Y |
| HG-GRAPH-MODULES | approved | approved | Y | Y | Y |

reviews R1：是（`task_lc_evidence_chain_hardening_audit_R1_20260817.md`）  
pre-30 invoke：是（00、10、20 已齐；缺 30 不挡开工）  
`npx @cyning/harness verify --target . --task docs/tasks/active/task_lc_evidence_chain_hardening.md`：PASS  
结论：**可开工**

---

## 实现要点（30）

1. D1：`BaseProviderImpl._complete_from_stream` 聚合 stream；usage / `model.fallback` 纯 meta 帧不拼正文；usage 构造 `LlmUsage` 后 `update_current_generation_usage`（函数内 lazy import `app.ops.tracing`）。SiliconFlow / Bailian `complete()` 改调该 helper；返回仍 `str`。
2. D2：`_grade_chunks_llm` 捕获完成期异常 → `logger.exception` + span metadata `grade_failed=true` + `grades=[]` → `decide_grade` refuse。HTTP 走真实 `ainvoke` 仍 200。answer / retrieve 失败仍 500。
3. D3：`decide_grade` 过滤后 `kept` 按 `relevance.level` 降序（`sorted` 稳定，同档保序）。
4. D4：G-L1 `01_modules.md` 的 `lc_evidence_chain` / `llm` 备注补「complete 路径上报 usage；grader 故障 refuse」；依赖方向列未改；`llm` 出边仍「—」。
5. 单测 mock：usage 上报 / tracing 关静默；grader `complete` 抛 `LlmProviderError` → ainvoke refuse + HTTP 200；kept 排序；既有 upstream 500 保留。
6. **未改** `app/ops/chat/graph.py` · **未升** `lc-evidence-http-v1` · **未做** CE→EXACT。

---

## 验证摘要（30/40）

| 命令 | 退出码 | 关键输出 |
|---|---|---|
| 开工前 `npx @cyning/harness verify --target . --task docs/tasks/active/task_lc_evidence_chain_hardening.md` | 0 | VERIFY: PASS |
| 主仓 `.venv/bin/ruff check app/llm/providers app/ops/lc_evidence_chain tests/test_llm_providers.py tests/test_lc_evidence_chain.py tests/test_lc_evidence_http.py` | 0 | All checks passed |
| 主仓 `.venv/bin/pytest tests/test_llm_providers.py tests/test_lc_evidence_chain.py tests/test_lc_evidence_http.py -q` | 0 | **48 passed** in 0.17s |
| `git diff origin/master -- app/ops/chat/graph.py` | 0 | 空 |
| `./scripts/graph-compile.sh` | 0 | OK: 00_main / 10_flow_auth / 10_flow_chat / 11_flow_sync_to_chat |
| 收尾 `npx @cyning/harness verify --target . --task docs/tasks/active/task_lc_evidence_chain_hardening.md` | 0 | VERIFY: PASS（WARN：缺 30 invoke 将由本文件补齐；工作区未 clean） |

本 worktree 无 `.venv`；ruff/pytest 使用 `/Users/cyning/Desktop/Ops-desk/ops-desk-api/.venv/bin/`（cwd=本 worktree，`import app` 落本仓）。

**40 结论：PASS**（机械项）  
已知未测：Langfuse UI token（人工可选）。

---

## 下一棒

交还 **00** 机械核对 → 50。不要 push。
