# Invoke：30（含 40）· capability-gateway-p2

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `capability-gateway-p2` |
| freeze_id | 无 |
| task_paths | `docs/tasks/active/task_capability_gateway_p2.md` |
| related_review_or_none | `docs/harness/reviews/task_capability_gateway_p2_audit_R1_20260826.md` |
| git_branch | `task/capability-gateway` |
| worktree_root | `.`（主仓 `ops-desk-api`） |
| created_utc_or_local | 2026-08-26 |
| notes | 仅 P2；**未** commit / **未** push / **未** PR；交 00 验收 |

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved（PROMPT） | Y | N（22-R1） | Y |
| HG-AUDIT-R1 | approved | approved（PROMPT） | Y | Y | Y |
| HG-GRAPH-MODULES | approved | approved（PROMPT · 不增一级） | Y | Y | Y |

reviews：`task_capability_gateway_p2_audit_R1_20260826.md` 存在且 R1 通过？ **是**

pre-30 invoke：`required ∩ {10,20,00}` 齐全？ **是**（有 00 + 10；`required_invoke_hats=10,30` · `default`）

`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_capability_gateway_p2.md` → **VERIFY: PASS**

结论：**可进入读码/改码**

---

## 可复制 Prompt 快照

见同目录 `PROMPT_30_execute.md`（本轮按该复制区执行）。

---

## 交付范围（30）

1. MCP / sandbox / cli 各 1 个 mock 探针 adapter（`MockMcpAdapter` / `MockSandboxAdapter` / `MockCliAdapter`）
2. `probes.register_p2_probes(*, enabled=False)`：默认**不**进 `ensure_default_capabilities`；本地可 `enabled=True` 开启
3. 短文档：`docs/guides/GUIDE_capability-gateway-p2-probes_v0.md` + 模块 docstring
4. 单测 mock；**未**接真外网 / 真 MCP / 生产 sandbox；**未**改 `chat/graph.py`；无 skill P3；无 Agently
5. G-L1 `lg_rag` 备注补 P2；可选 `run_code` **未**包装进 defaults（cli 为零 subprocess 罐头）

---

## 验证摘要（30/40）

| 项 | 结果 |
|---|---|
| GATE_VERIFY | PASS（三闸 approved） |
| harness verify | `npx dsh-coding-kit verify --target . --task docs/tasks/active/task_capability_gateway_p2.md` → **PASS** |
| ruff（触及路径） | `ruff check app/ops/capability tests/test_capability_gateway.py` → exit **0** |
| pytest | `.venv/bin/pytest tests/test_capability_gateway.py tests/test_lg_rag_multi.py -q` → exit **0** · **24 passed**（capability 15 + multi 9） |
| `git diff` · `app/ops/chat/graph.py` | **0**（零改动） |
| Agently / 真外网 | **未**引入 / **未**连 |
| commit / push / PR | **未执行** |

**变更路径（本 task）**

- `app/ops/capability/adapters/mcp.py`（新建）
- `app/ops/capability/adapters/sandbox.py`（新建）
- `app/ops/capability/adapters/cli.py`（新建）
- `app/ops/capability/probes.py`（新建 · 注册辅助）
- `app/ops/capability/adapters/__init__.py` / `__init__.py`（导出）
- `tests/test_capability_gateway.py`（P2 单测）
- `docs/guides/GUIDE_capability-gateway-p2-probes_v0.md`
- `docs/_tech_graph/l1/01_modules.md`（`lg_rag` 备注）
- 本 invoke

**默认关闭钉死**：defaults 仅 `local_fn` 两枚 mock；探针须显式 `register_p2_probes`。

---

## 交 00

- 验收标准可勾选；建议关账前确认未把探针误写入 defaults。
- **可否关账**：是（40 绿 · graph.py 0 · multi 不回归 · 未 commit/push）。
