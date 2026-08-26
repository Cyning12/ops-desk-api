# Invoke：30（含 40）· capability-gateway-p0

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `capability-gateway-p0` |
| freeze_id | 无 |
| task_paths | `docs/tasks/active/task_capability_gateway_p0.md` |
| related_review_or_none | `docs/harness/reviews/task_capability_gateway_p0_audit_R1_20260826.md` |
| git_branch | `task/capability-gateway` |
| worktree_root | `.`（主仓 `ops-desk-api`） |
| created_utc_or_local | 2026-08-26 |
| notes | 仅 P0；**未** commit / **未** push / **未** PR；交 00 验收 |

---

## GATE_VERIFY（首输出 · 读 task 表）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved（PROMPT） | Y | N（22-R1） | Y |
| HG-AUDIT-R1 | approved | approved（PROMPT） | Y | Y | Y |
| HG-GRAPH-MODULES | approved | approved（PROMPT · 仅备注、不增一级） | Y | Y | Y |

reviews：`task_capability_gateway_p0_audit_R1_20260826.md` 存在且 R1 通过？ **是**

pre-30 invoke：`required ∩ {10,20,00}` 齐全？ **是**（有 00 + 10；`required_invoke_hats=10,30` · `default`）

`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_capability_gateway_p0.md` → **VERIFY: PASS**

结论：**可进入读码/改码**

---

## 可复制 Prompt 快照

见同目录 `PROMPT_30_execute.md`（本轮按该复制区执行）。

---

## 交付范围（30）

1. 新建 `app/ops/capability/`：`register` / `unregister` / `list_capabilities` / `invoke`；`CapabilitySpec` / `CapabilityResult` / `CapabilityFilter`；`LocalFnAdapter`
2. 迁移 `MOCK_TOOLS` 两枚 mock → Gateway 默认注册；`tool_exec_node` 改调 `invoke`
3. 未知 id → `ok=False`（错误文案含「未知工具」），不中断后续子任务
4. invoke 写当前 span metadata：`capability_id` · `kind` · `ok` · `error` 截断；兼容现 `trace_span("tool_exec")`（不另开根 span）
5. 重复 id：**拒绝覆盖**（`ValueError`）注释钉死 + 单测
6. 单测 + G-L1 `lg_rag` 备注 + graph-compile
7. **未改** `app/ops/chat/graph.py` · P1–P3 · Agently · `app/tools/run_code.py` 强制接入 · 无关 active task

---

## 验证摘要（30/40）

| 项 | 结果 |
|---|---|
| GATE_VERIFY | PASS（三闸 approved） |
| harness verify | `npx dsh-coding-kit verify --target . --task docs/tasks/active/task_capability_gateway_p0.md` → **PASS** |
| ruff（触及路径） | `ruff check app/ops/capability app/ops/lg_rag/multi/nodes.py tests/test_capability_gateway.py` → exit **0** |
| pytest | `.venv/bin/pytest tests/test_capability_gateway.py tests/test_lg_rag_multi.py -q` → exit **0** · **17 passed**（capability 8 + multi 9） |
| `git diff` · `app/ops/chat/graph.py` | **0 bytes**（零改动） |
| `./scripts/graph-compile.sh` | exit **0** |
| Agently / requirements | **未**引入 |
| `app/tools/run_code.py` | **未**强制接入 |
| commit / push / PR | **未执行** |

**变更路径（本 task）**

- `app/ops/capability/`（`__init__` / `types` / `registry` / `gateway` / `defaults` / `adapters/local_fn`）
- `app/ops/lg_rag/multi/nodes.py`（MOCK_TOOLS 迁出；`tool_exec_node` → `capability_invoke`）
- `tests/test_capability_gateway.py`
- `docs/_tech_graph/l1/01_modules.md`（`lg_rag` 备注）
- 本 invoke

**重复 id 钉死**：`register` 已存在 → `ValueError`（拒绝覆盖）；须先 `unregister`。

---

## 给 00

- 分支 `task/capability-gateway`；本 invoke 已落盘
- **可关账条件已满足（实现+40）**：验收路径齐、pytest/ruff/graph-compile 绿、`graph.py` 零 diff、未 commit/push
- 请 00 勾 task 验收项并决定是否 commit / PR
