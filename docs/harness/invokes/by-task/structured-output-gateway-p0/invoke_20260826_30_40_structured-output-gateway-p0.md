# Invoke：30（含 40）· structured-output-gateway-p0

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `structured-output-gateway-p0` |
| freeze_id | 无 |
| task_paths | `docs/tasks/active/task_structured_output_gateway_p0.md` |
| related_review_or_none | `docs/harness/reviews/task_structured_output_gateway_p0_audit_R1_20260826.md` |
| git_branch | `task/structured-output-gateway` |
| worktree_root | `.`（主仓 `ops-desk-api`） |
| created_utc_or_local | 2026-08-26 |
| notes | 仅 P0；**未** commit / **未** push / **未** PR；交 00 验收 |

---

## GATE_VERIFY（首输出 · 读 task 表）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved（PROMPT） | Y | N | Y |
| HG-AUDIT-R1 | approved | approved（PROMPT） | Y | Y | Y |
| HG-GRAPH-MODULES | approved | approved（PROMPT · 非新增一级） | Y | Y | Y |

reviews：`task_structured_output_gateway_p0_audit_R1_20260826.md` 存在且 R1 通过？ **是**

pre-30 invoke：`required ∩ {10,20,00}` 齐全？ **是**（有 00 + 10；`required_invoke_hats=10,30` · `default`）

`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_structured_output_gateway_p0.md` → **VERIFY: PASS**

结论：**可进入读码/改码**

---

## 可复制 Prompt 快照

见同目录 `PROMPT_30_execute.md`（本轮按该复制区执行）。

---

## 交付范围（30）

1. 新建 `app/ops/structured_output/`：`extract_json_object` · `deterministic_repair` · `parse_only` / `ParseOutcome`
2. `app/ops/lg_rag/multi/nodes.py`：`_extract_json_object` 委托公共实现（不改 supervisor fallback 业务语义）
3. `tests/test_structured_output_parse_only.py`：合法 / fence / 杂讯 / repair / schema 失败 Host 权威
4. G-L1 `docs/_tech_graph/l1/01_modules.md` `lg_rag` 行备注一句（不新增一级模块）
5. **未改** `app/ops/chat/graph.py` · Capability Gateway · Agently 依赖 · 无关 active task · `app/tools/` 草稿

---

## 验证摘要（30/40）

| 项 | 结果 |
|---|---|
| GATE_VERIFY | PASS（三闸 approved） |
| harness verify | `npx dsh-coding-kit verify --target . --task docs/tasks/active/task_structured_output_gateway_p0.md` → **PASS** |
| ruff（触及路径） | `ruff check app/ops/structured_output app/ops/lg_rag/multi/nodes.py tests/test_structured_output_parse_only.py` → exit **0** · All checks passed |
| pytest | `.venv/bin/pytest tests/test_structured_output_parse_only.py tests/test_lg_rag_multi.py -q` → exit **0** · **21 passed**（本 task 12 + multi 9） |
| `git diff` · `app/ops/chat/graph.py` | **0 bytes**（零改动） |
| `./scripts/graph-compile.sh` | exit **0** |
| Agently / requirements | **未**引入 |
| `app/tools/` 草稿 | **未**纳入 |
| commit / push / PR | **未执行** |

**变更路径（本 task）**

- `app/ops/structured_output/__init__.py`
- `app/ops/structured_output/extract.py`
- `app/ops/structured_output/repair.py`
- `app/ops/structured_output/parse.py`
- `app/ops/lg_rag/multi/nodes.py`（委托公共 extract）
- `tests/test_structured_output_parse_only.py`
- `docs/_tech_graph/l1/01_modules.md`（`lg_rag` 备注）
- `docs/_tech_graph/**` graph-compile 衍生（`graph.json` / flow md `generated_at` 等）
- 本 invoke

**40 结论：PASS**（可交 00 机械关账；本子 agent 不 commit / push）

---

## 下一棒

00 机械核对验收勾选与关账；本子 agent **不** commit / push。
