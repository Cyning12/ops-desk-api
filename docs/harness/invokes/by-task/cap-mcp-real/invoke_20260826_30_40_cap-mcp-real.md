# Invoke：30（含 40）· cap-mcp-real

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `cap-mcp-real` |
| freeze_id | 无 |
| task_paths | `docs/tasks/active/task_cap_mcp_real.md` |
| related_review_or_none | `docs/harness/reviews/task_cap_mcp_real_audit_R1_20260826.md` |
| git_branch | `task/cap-mcp-real` |
| worktree_root | `.`（主仓 `ops-desk-api`） |
| created_utc_or_local | 2026-08-26 |
| notes | U3 真 MCP；本地可 commit；**未** push |

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved（PROMPT） | Y | N（22-R1） | Y |
| HG-AUDIT-R1 | approved | approved（PROMPT） | Y | Y | Y |
| HG-GRAPH-MODULES | approved | approved（PROMPT · 仅备注） | Y | Y | Y |

reviews：`task_cap_mcp_real_audit_R1_20260826.md` 存在且 R1 通过？ **是**

pre-30 invoke：`required ∩ {10,20,00}` 齐全？ **是**（有 00 + 10；`required_invoke_hats=10,30` · `default`）

`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_cap_mcp_real.md` → **VERIFY: PASS**

结论：**可进入读码/改码**

---

## 可复制 Prompt 快照

见同目录 `PROMPT_30_execute.md`（本轮按该复制区执行）。

---

## 交付范围（30）

1. 新增 `McpClientAdapter`（可注入 `McpTransport` / `FakeTransport`；可选薄 `HttpJsonRpcTransport`）
2. 统一仍走 gateway `invoke → CapabilityResult`；失败/异常 → `ok=False`
3. env：`OPS_CAPABILITY_MCP_ENABLED` 默认 false；未启用 / 无 endpoint → 不注册真 client
4. 保留 `MockMcpAdapter` + `probes`；既有 capability 测绿
5. FakeTransport 单测：成功 + error + exception；`@pytest.mark.integration` 默认 skip
6. ROADMAP / 域 README / G-L1 一行「真 MCP · 默认关 · CI 不外网」
7. **未**改 `chat/graph.py`；无 Agently；无重 MCP SDK

---

## 验证摘要（30/40）

| 项 | 命令 / 检查 | 结果 |
|---|---|---|
| GATE_VERIFY | 读 task 人工闸表 | 三闸 approved · 可 30 |
| harness verify | `npx dsh-coding-kit verify --target . --task docs/tasks/active/task_cap_mcp_real.md` | **PASS** |
| pytest | `.venv/bin/pytest tests/test_capability_gateway.py -q` | **27 passed, 1 skipped** |
| ruff | `.venv/bin/ruff check app/ops/capability app/config.py tests/test_capability_gateway.py` | **PASS** |
| `app/ops/chat/graph.py` | `git diff --stat` | **0**（零改动） |
| 默认路径外网 | FakeTransport 单测；HttpJsonRpc 仅显式构造；integration skip | **PASS** |
| graph-compile | `./scripts/graph-compile.sh` | OK；时间戳噪声已还原，仅留 `01_modules.md` 备注 |
| push | — | **未执行** |

**变更路径（本 task）**

- `app/ops/capability/adapters/mcp_client.py`（新建）
- `app/ops/capability/adapters/__init__.py` / `__init__.py` / `mcp.py` / `probes.py`
- `app/config.py` · `.env.example` · `pyproject.toml`（integration marker）
- `tests/test_capability_gateway.py`
- `docs/spec/agent-infra/capability/ROADMAP_portable_core_v0.md` · `README.md`
- `docs/_tech_graph/l1/01_modules.md`
- 本 invoke

---

## 结论

U3 真 MCP adapter 已落地：可注入 FakeTransport 保 CI 零外网；env 默认关；Mock 探针保留。可本地 commit；等待 00 收官。
