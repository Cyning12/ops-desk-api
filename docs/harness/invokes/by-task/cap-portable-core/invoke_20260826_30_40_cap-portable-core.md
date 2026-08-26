# Invoke：30（含 40）· cap-portable-core

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `cap-portable-core` |
| freeze_id | 无 |
| task_paths | `docs/tasks/active/task_cap_portable_core.md` |
| related_review_or_none | `docs/harness/reviews/task_cap_portable_core_audit_R1_20260826.md` |
| git_branch | `task/cap-portable-core` |
| worktree_root | `.`（主仓 `ops-desk-api`） |
| created_utc_or_local | 2026-08-26 |
| notes | U1+U2；本地可 commit；**未** push / **未**开新 PR |

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved（PROMPT） | Y | N（22-R1） | Y |
| HG-AUDIT-R1 | approved | approved（PROMPT） | Y | Y | Y |
| HG-GRAPH-MODULES | approved | approved（PROMPT · 仅备注） | Y | Y | Y |

reviews：`task_cap_portable_core_audit_R1_20260826.md` 存在且 R1 通过？ **是**

pre-30 invoke：`required ∩ {10,20,00}` 齐全？ **是**（有 00 + 10；`required_invoke_hats=10,30` · `default`）

`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_cap_portable_core.md` → **VERIFY: PASS**

结论：**可进入读码/改码**

---

## 可复制 Prompt 快照

见同目录 `PROMPT_30_execute.md`（本轮按该复制区执行）。

---

## 交付范围（30）

1. **U1**：ToolNode 桥迁至 `app.ops.capability.extras.langchain`；删除 `adapters/langchain_tools.py`；包 / adapters 默认 `__all__` 不再含 `as_tool_node` / `as_structured_tools`
2. 内核默认路径零 `langgraph` import（`rg` 仅命中 extras）
3. Mode A 主路径不变：`list_capabilities` + `invoke`；`schemas_for_llm` 仍为纯数据
4. 单测：默认导出断言 + extras ToolNode smoke；增强 `node_role` 占位 + tags/kinds filter
5. **U2**：`docs/guides/GUIDE_capability-portable-core-mode-a_v0.md` + ROADMAP 附录 A
6. G-L1 `capability` 行备注「可迁移内核 · Mode A」；`./scripts/graph-compile.sh` exit 0（generated 时间戳噪声已还原，仅保留 `01_modules.md`）
7. **未**改 `chat/graph.py`；无 Agently；无升 SPEC `_v1`

---

## 验证摘要（30/40）

| 项 | 命令 / 检查 | 结果 |
|---|---|---|
| GATE_VERIFY | 读 task 人工闸表 | 三闸 approved · 可 30 |
| harness verify | `npx dsh-coding-kit verify --target . --task docs/tasks/active/task_cap_portable_core.md` | **PASS** |
| pytest | `.venv/bin/pytest tests/test_capability_gateway.py tests/test_lg_rag_multi.py -q` | exit **0** · **30 passed**（capability 21 + multi 9） |
| ruff | `.venv/bin/ruff check app/ops/capability tests/test_capability_gateway.py` | exit **0** |
| `rg -n 'langgraph' app/ops/capability` | 仅 `extras/langchain.py`（doc + import） | **PASS** |
| `app/ops/chat/graph.py` | `git diff --stat` | **0**（零改动） |
| graph-compile | `./scripts/graph-compile.sh` | exit **0**（产物时间戳已 `git checkout` 还原无关 md/json） |
| SPEC `_v1` | 破坏面评估 | **不升**：仓内无生产默认导出引用；迁 extras + GUIDE；v0 ROADMAP 修订一行即可 |
| Agently / 真外网 / 动态 compile | — | **未**引入 / **未**连 / **未**做 |
| push / 新 PR | — | **未执行** |

**变更路径（本 task）**

- `app/ops/capability/extras/__init__.py`（新建）
- `app/ops/capability/extras/langchain.py`（新建 · 自 adapters 迁入）
- `app/ops/capability/adapters/langchain_tools.py`（删除）
- `app/ops/capability/__init__.py` / `adapters/__init__.py`（默认导出去桥）
- `tests/test_capability_gateway.py`
- `docs/guides/GUIDE_capability-portable-core-mode-a_v0.md`
- `docs/spec/agent-infra/capability/ROADMAP_portable_core_v0.md`（附录 A + 修订）
- `docs/_tech_graph/l1/01_modules.md`（capability 备注）
- 本 invoke

---

## 验收勾选（对照 task）

- [x] `rg langgraph` 仅 extras
- [x] 默认导出不含 `as_tool_node` / `as_structured_tools`
- [x] Mode A：`list` + `invoke` 主路径
- [x] 未知 id → `ok=False`（既有单测）
- [x] pytest 两文件绿
- [x] ruff 触及路径绿
- [x] `chat/graph.py` 零 diff
- [x] U2 文档 + list+filter 单测
- [x] G-L1 备注 + graph-compile exit 0
- [x] 无 Agently；无默认 CI 外网

---

## 交 00

- 可关账条件：实现 + 40 绿；**SPEC 不升 v1**。
- 残留风险：仓外若已 `from app.ops.capability import as_tool_node` 须改 extras；`node_role` 仍为占位不裁剪（文档已钉）。
- 本地 commit：由 30 按授权执行 `feat(capability): …`；**不** push。
