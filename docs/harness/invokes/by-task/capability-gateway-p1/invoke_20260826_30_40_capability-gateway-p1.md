# Invoke：30（含 40）· capability-gateway-p1

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `capability-gateway-p1` |
| freeze_id | 无 |
| task_paths | `docs/tasks/active/task_capability_gateway_p1.md` |
| related_review_or_none | `docs/harness/reviews/task_capability_gateway_p1_audit_R1_20260826.md` |
| git_branch | `task/capability-gateway` |
| worktree_root | `.`（主仓 `ops-desk-api`） |
| created_utc_or_local | 2026-08-26 |
| notes | 仅 P1；**未** commit / **未** push / **未** PR；交 00 验收 |

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved（PROMPT） | Y | N（22-R1） | Y |
| HG-AUDIT-R1 | approved | approved（PROMPT） | Y | Y | Y |
| HG-GRAPH-MODULES | approved | approved（PROMPT · 不增一级） | Y | Y | Y |

reviews：`task_capability_gateway_p1_audit_R1_20260826.md` 存在且 R1 通过？ **是**

pre-30 invoke：`required ∩ {10,20,00}` 齐全？ **是**（有 00 + 10；`required_invoke_hats=10,30` · `default`）

`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_capability_gateway_p1.md` → **VERIFY: PASS**

结论：**可进入读码/改码**

---

## 可复制 Prompt 快照

见同目录 `PROMPT_30_execute.md`（本轮按该复制区执行）。

---

## 交付范围（30）

1. `schemas_for_llm(*, filter) -> list[dict]`：OpenAI/LangChain tools 风格（`type=function` + `function.{name,description,parameters}`）
2. Filter 复用 P0（kinds / tags_any 等）
3. 可选 thin 适配：`as_structured_tools` / `as_tool_node`（`adapters/langchain_tools.py`）+ smoke 单测；**未**改 `multi/graph.py` / lg_rag 拓扑为必挂 FC
4. 无 `args_schema`：**跳过**（注释钉死，与 schemas / adapter 一致）
5. G-L1 `lg_rag` 备注补 P1；**未**改 `app/ops/chat/graph.py` · 无 P2/P3 · 无 Agently · 无真外网

---

## 验证摘要（30/40）

| 项 | 结果 |
|---|---|
| GATE_VERIFY | PASS（三闸 approved） |
| harness verify | `npx dsh-coding-kit verify --target . --task docs/tasks/active/task_capability_gateway_p1.md` → **PASS** |
| ruff（触及路径） | `ruff check app/ops/capability tests/test_capability_gateway.py` → exit **0** |
| pytest | `.venv/bin/pytest tests/test_capability_gateway.py tests/test_lg_rag_multi.py -q` → exit **0** · **20 passed**（capability 11 + multi 9） |
| `git diff` · `app/ops/chat/graph.py` | **0**（零改动） |
| `app/ops/lg_rag/multi/graph.py` | **0**（未改拓扑） |
| Agently / 真外网 | **未**引入 / **未**连 |
| commit / push / PR | **未执行** |

**变更路径（本 task）**

- `app/ops/capability/gateway.py`（`schemas_for_llm`）
- `app/ops/capability/adapters/langchain_tools.py`（新建 · 可选 StructuredTool/ToolNode）
- `app/ops/capability/adapters/__init__.py` / `__init__.py`（导出）
- `tests/test_capability_gateway.py`（P1 单测）
- `docs/_tech_graph/l1/01_modules.md`（`lg_rag` 备注）
- 本 invoke

**无 args_schema 钉死**：`schemas_for_llm` / `as_structured_tools` **跳过**该条目（不吐残缺 FC schema）。

---

## 给 00

- 分支 `task/capability-gateway`；本 invoke 已落盘
- **可关账条件已满足（实现+40）**：验收路径齐、pytest/ruff 绿、`graph.py` 零 diff、未 commit/push
- 请 00 勾 task 验收项并决定是否 commit / PR
