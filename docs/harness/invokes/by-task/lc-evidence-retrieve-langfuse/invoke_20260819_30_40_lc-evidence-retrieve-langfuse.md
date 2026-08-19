# Invoke：30（含 40）· lc-evidence-retrieve-langfuse

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `lc-evidence-retrieve-langfuse` |
| task_paths | `docs/tasks/active/task_lc_evidence_retrieve_langfuse.md` |
| related_review_or_none | `docs/harness/reviews/task_lc_evidence_retrieve_langfuse_audit_R1_20260819.md` |
| git_branch | `task/lc-evidence-retrieve-langfuse` |
| created_utc_or_local | 2026-08-19 |
| notes | 子 agent 30+40；未 close / 未开 PR；本机 Langfuse UI 为人工项 |

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved | Y | N | Y |
| HG-AUDIT-R1 | approved | approved | Y | Y | Y |
| HG-GRAPH-MODULES | approved | approved | Y | Y | Y |

reviews：task_lc_evidence_retrieve_langfuse_audit_R1_20260819.md 存在且 R1 通过？ **是**

pre-30 invoke：`required ∩ {10,20,00}` 文件是否齐全？ **是**（10-task 已落档）

机械辅助：`npx @cyning/harness verify --target . --task docs/tasks/active/task_lc_evidence_retrieve_langfuse.md` · 父窗已 PASS

结论：**可进入读码/改码**

---

## 交付范围（30）

1. `retrieve.py`：`from app.ops.tracing import trace_span`；再导入 `rerank_model_name`
2. 查询 embed：`with trace_span("query_embed", run_type="llm", model=embedder.name):` 包 `asyncio.to_thread(embedder.embed, ...)`
3. `rerank_enabled()` 为真时：`with trace_span("rerank", run_type="llm", model=rerank_model_name()):` 包 `rerank_chunks`
4. 单测扩 `tests/test_lc_evidence_chain.py`：mock `trace_span`；embed 包裹 + rerank 开/关
5. **未改** `chat/graph.py` · `rag_nodes.py` · hybrid_recall · lg_rag · SDK 升包

---

## 验证摘要（30/40）

| 项 | 结果 |
|---|---|
| GATE_VERIFY / harness verify | PASS |
| ruff（相关路径） | exit 0（`.venv/bin/ruff check …`） |
| pytest `tests/test_lc_evidence_chain.py` | 19 passed |
| `git diff origin/master -- app/ops/chat/graph.py` | 空 |
| generation 保证 | `query_embed` / 条件 `rerank` → `run_type="llm"` → Langfuse generation |
| 本机 Langfuse UI smoke | **未做**（人工项 · 维护者 keys） |
| 关账 / PR | **未执行**（留给父窗） |

**40 结论：PASS**

---

## 下一棒

父窗验收 → 等维护者确认（含 UI 抽检）→ CLOSE / PR / merge master。
