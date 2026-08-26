# Invoke：30（含 40）· structured-output-gateway-p3

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `structured-output-gateway-p3` |
| freeze_id | 无 |
| task_paths | `docs/tasks/active/task_structured_output_gateway_p3.md` |
| related_review_or_none | `docs/harness/reviews/task_structured_output_gateway_p3_audit_R1_20260826.md` |
| git_branch | `task/structured-output-gateway` |
| worktree_root | `.`（主仓 `ops-desk-api`） |
| created_utc_or_local | 2026-08-26 |
| notes | 仅 P3；**未** commit / **未** push / **未** PR；交 00 验收关账 |

---

## GATE_VERIFY（首输出 · 读 task 表）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved（PROMPT） | Y | N | Y |
| HG-AUDIT-R1 | approved | approved（PROMPT） | Y | Y | Y |
| HG-GRAPH-MODULES | approved | approved（PROMPT · 不增一级模块） | Y | Y | Y |

reviews：`task_structured_output_gateway_p3_audit_R1_20260826.md` 存在且 R1 通过？ **是**

pre-30 invoke：`required ∩ {10,20,00}` 齐全？ **是**（有 00 + 10；`required_invoke_hats=10,30` · `default`）

`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_structured_output_gateway_p3.md` → **VERIFY: PASS**

结论：**可进入读码/改码**

---

## 可复制 Prompt 快照

见同目录 `PROMPT_30_execute.md`（本轮按该复制区执行）。

---

## 交付范围（30）

1. `parse_only` 接通 `ensure_keys`（点分路径 presence/not_null；约定写在 `parse._walk_dot_path`）与 `validate` callable（`None`=通过 / `str`=reason）
2. `acomplete_structured` 传入并复用；失败 reason 进 OUTPUT CORRECTION（除非 `no_retry`）
3. `no_retry`：不注入 correction、敏感规则文案不得出现在 messages（单测钉死）
4. 并存策略文档：`docs/guides/DESIGN_structured-output-gateway-coexistence_v0.md`
5. SPEC §9 修订记录追加「P0–P3 落地状态」一行
6. 单测：`tests/test_structured_output_p3.py`（mock only）
7. **未改** `app/ops/chat/graph.py` · 未新接业务节点 · 无 Capability / Agently · 未动无关 active / `app/tools`

`graph_delta`：**none**（仅 API + 文档；不增一级模块）

---

## 验证摘要（30/40）

| 项 | 结果 |
|---|---|
| GATE_VERIFY | PASS（三闸 approved） |
| harness verify | `npx dsh-coding-kit verify --target . --task docs/tasks/active/task_structured_output_gateway_p3.md` → **PASS** |
| ruff | `ruff check app/ops/structured_output tests/test_structured_output_*.py` → exit **0** |
| pytest | `.venv/bin/pytest tests/test_structured_output_p3.py tests/test_structured_output_complete.py tests/test_structured_output_parse_only.py -q` → **26 passed** |
| `git diff` · `app/ops/chat/graph.py` | **0 bytes**（零改动） |
| Agently / Capability Gateway | **未**引入 |
| 新业务节点 / chat graph | **未**改 |
| commit / push / PR | **未执行** |

**变更路径（本 task）**

- `app/ops/structured_output/parse.py`（ensure_keys / validate）
- `app/ops/structured_output/complete.py`（接通参数；去 P3 预留 del）
- `app/ops/structured_output/__init__.py`（导出 `check_ensure_keys`）
- `tests/test_structured_output_p3.py`（新）
- `docs/guides/DESIGN_structured-output-gateway-coexistence_v0.md`（新）
- `docs/spec/agent-infra/SPEC-structured-output-gateway_v0.md`（修订记录一行）

---

## 交 00

- 验收标准已落地；建议 00 勾选 task 验收项、更新 50、关账 CLOSE。
- **可否关账**：**是**（技术交付完成；待 00 人工确认关账流程）。
- 工作树有 diff，**未** commit / **未** push。
