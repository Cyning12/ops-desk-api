# Invoke：30（含 40）· structured-output-gateway-p2

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `structured-output-gateway-p2` |
| freeze_id | 无 |
| task_paths | `docs/tasks/active/task_structured_output_gateway_p2.md` |
| related_review_or_none | `docs/harness/reviews/task_structured_output_gateway_p2_audit_R1_20260826.md` |
| git_branch | `task/structured-output-gateway` |
| worktree_root | `.`（主仓 `ops-desk-api`） |
| created_utc_or_local | 2026-08-26 |
| notes | 仅 P2；**未** commit / **未** push / **未** PR；交 00 验收 |

---

## GATE_VERIFY（首输出 · 读 task 表）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved（PROMPT） | Y | N | Y |
| HG-AUDIT-R1 | approved | approved（PROMPT） | Y | Y | Y |
| HG-GRAPH-MODULES | approved | approved（PROMPT · 仅备注） | Y | Y | Y |

reviews：`task_structured_output_gateway_p2_audit_R1_20260826.md` 存在且 R1 通过？ **是**

pre-30 invoke：`required ∩ {10,20,00}` 齐全？ **是**（有 00 + 10；`required_invoke_hats=10,30` · `default`）

`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_structured_output_gateway_p2.md` → **VERIFY: PASS**

结论：**可进入读码/改码**

---

## 可复制 Prompt 快照

见同目录 `PROMPT_30_execute.md`（本轮按该复制区执行）。

---

## 交付范围（30）

1. Pydantic schemas：`RouteDecision` / `SubtasksPlan`+`SubtaskItem` / `ExtractResult` → `app/ops/structured_output/schemas/`
2. router：`_parse_route` / `_classify_route` → Gateway `parse_only`；保留非 JSON `"rag"|"direct"|"refuse"` 宽容路径；metadata 增 `structured_output_fallback`
3. supervisor / `_parse_subtasks` → complete 一次 + `parse_only`（注释说明避免双重 LLM）；fallback 单 rag；`supervisor_fallback` + `structured_output_fallback` 并存
4. `info_extract_node` → complete 一次 + `parse_only`；非法 → 空结构 + `structured_output_fallback`
5. mock 单测 `tests/test_lg_rag_structured_output_p2.py`；既有 `test_lg_rag_*` 不回归
6. G-L1 `01_modules.md` `lg_rag` 备注：结构化节点走 Gateway（P2）+ graph-compile
7. **未改** `app/ops/chat/graph.py` · multi/graph 拓扑边 · Capability Gateway · Agently · `app/tools/` 草稿 · 无关 active

选型注释（落地）：三处均「节点已 complete → 仅 parse_only」，不用 `acomplete_structured`，避免本波双重 LLM。

---

## 验证摘要（30/40）

| 项 | 结果 |
|---|---|
| GATE_VERIFY | PASS（三闸 approved） |
| harness verify | `npx dsh-coding-kit verify --target . --task docs/tasks/active/task_structured_output_gateway_p2.md` → **PASS** |
| ruff（触及路径） | `ruff check app/ops/lg_rag/nodes.py app/ops/lg_rag/multi/nodes.py app/ops/structured_output tests/test_lg_rag_structured_output_p2.py` → exit **0** |
| pytest | `.venv/bin/pytest tests/test_lg_rag_structured_output_p2.py tests/test_lg_rag_router.py tests/test_lg_rag_multi.py tests/test_structured_output_*.py tests/test_lg_rag_basic.py tests/test_lg_rag_retry.py -q` → exit **0** · **59 passed** |
| `git diff` · `app/ops/chat/graph.py` | **0 bytes**（零改动） |
| multi/graph.py · lg_rag/graph.py 拓扑 | **0 bytes**（零改动） |
| `./scripts/graph-compile.sh` | exit **0** |
| Agently / Capability Gateway | **未**引入 |
| `app/tools/` 草稿 | **未**纳入 |
| commit / push / PR | **未执行** |

**变更路径（本 task）**

- `app/ops/structured_output/schemas/`（新：route / subtasks / extract）
- `app/ops/lg_rag/nodes.py`（router Gateway + metadata）
- `app/ops/lg_rag/multi/nodes.py`（supervisor / extract Gateway + metadata）
- `tests/test_lg_rag_structured_output_p2.py`（新）
- `docs/_tech_graph/l1/01_modules.md`（`lg_rag` 备注 · P2）
- `docs/_tech_graph/**` graph-compile 衍生（`graph.json` / flow md `generated_at` 等）
- 本 invoke

**40 结论：PASS**（可交 00 机械关账；本子 agent 不 commit / push）

---

## 下一棒

00 机械核对验收勾选与关账；本子 agent **不** commit / push。
