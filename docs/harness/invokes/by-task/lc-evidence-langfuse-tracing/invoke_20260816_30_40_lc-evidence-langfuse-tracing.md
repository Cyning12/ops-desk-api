# Invoke：30（含 40）· lc-evidence-langfuse-tracing

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `lc-evidence-langfuse-tracing` |
| task_paths | `docs/tasks/active/task_lc_evidence_langfuse_tracing.md` |
| related_review_or_none | `docs/harness/reviews/task_lc_evidence_langfuse_tracing_audit_R1_20260816.md` |
| git_branch | `task/lc-evidence-langfuse-tracing` |
| created_utc_or_local | 2026-08-16 |
| notes | 子 agent 30+40；未 close / 未开 PR；本机 Langfuse UI 为人工项 |

---

## GATE_VERIFY（首输出 · 读 task 表）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved | Y | N | Y |
| HG-AUDIT-R1 | approved | approved | Y | Y | Y |
| HG-GRAPH-MODULES | approved | approved | Y | Y | Y |

reviews R1：是 · pre-30 invoke 10：是 · `npx @cyning/harness@2.24.0 verify`：PASS · 结论：可开工

---

## 交付范围（30）

1. `chain._trace_config()`：对齐 Chat `service._trace_config`；`run_name`/`langfuse_tags`=`lc-evidence-chain`
2. `ainvoke_evidence_answer`：tracing 开时 `ainvoke(..., config=...)`
3. `grader` / `answer`：自研 `provider.complete` 外包 `trace_span(..., run_type="llm")` → generation
4. 步骤内 `update_current_span_metadata`（gate_action / hit_count / kept_count / best_relevance）
5. CLI：`tracing on/off` + 开时 `flush_traces()`
6. 单测开关路径 + G-L1 一行备注
7. **未改** `chat/graph.py` · **无**新 HTTP · **未**另造 tracing 主开关

---

## 验证摘要（30/40）

| 项 | 结果 |
|---|---|
| GATE_VERIFY / harness verify | PASS |
| ruff（相关路径） | exit 0 |
| pytest `tests/test_lc_evidence_chain.py` | 14 passed |
| `git diff origin/master -- app/ops/chat/graph.py` | 空 |
| generation 保证 | 代码路径：`trace_span(run_type="llm")` → Langfuse `as_type=generation`（grade_llm / answer_llm） |
| 本机 Langfuse UI smoke | **未做**（人工项 · 维护者 keys） |
| 关账 / PR | **未执行**（留给父窗 50 + 维护者确认） |

**40 结论：PASS**

---

## 下一棒

父窗 50 汇总 → 等维护者确认（含 UI 抽检）→ CLOSE / PR。
