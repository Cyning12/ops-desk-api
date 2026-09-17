# Invoke · 40 verify · capability-contract-hardening

> **hat**：40  
> **日期**：2026-09-17  
> **分支**：`task/capability-contract-hardening`（已核对 `git branch --show-current`）  
> **task**：`docs/tasks/active/task_capability_contract_hardening.md`  
> **禁区**：未扩 T/W/P；未 commit/push；未 CLOSE / git mv done

---

## 质量门（本帽真跑 · 退出码实录）

| 命令 | 退出码 | 结果 |
|------|--------|------|
| `ruff check app/ops/capability app/ops/strategy app/ops/lg_rag/multi app/ops/lg_rag/schemas tests/test_capability_* tests/test_strategy_builder.py tests/test_lg_rag_supervisor_capability_catalog.py` | **0** | All checks passed |
| `pytest`（30 声明 6 文件） | **0** | **76 passed**, 8 skipped（PG 不可用 · 既有 skip） |
| `./scripts/graph-compile.sh` | **0** | 9 graphs · 132 nodes · 194 edges · check OK · mermaid normalize ok |
| `npx --yes spec-wave verify --target . --task docs/tasks/active/task_capability_contract_hardening.md` | **0** | VERIFY: PASS（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均 approved） |
| `npx --yes spec-wave task lint-wiki-delta --target .` | **0** | LINT-WIKI-DELTA: PASS（scanned=113 · issues=0） |
| `git diff --stat -- app/ops/chat/graph.py` | **0** | 零 diff |

---

## 验收标准逐条对照（A–F + 门禁）

| # | 验收点 | 结论 | 证据 |
|---|--------|------|------|
| A | 默认 lookup + `utc_now_iso` 有最小 `args_schema`；不合规 → `ok=False` / `args_schema_invalid` | ✅ | `defaults.py` / `builtin.v1.yaml`；`schema_validate.py`；`test_args_schema_invalid_returns_ok_false` · `test_args_schema_lookup_rejects_wrong_number_type` |
| B | `SubtaskItem.args`；`tool_exec` 优先 args、兼容 input；节点级单测 | ✅（40 小修） | `subtasks.py` · `nodes.py`；原 PG 测 `test_tool_exec_prefers_args_over_input`（本环境 skip）；**40 补** `test_tool_exec_prefers_args_over_input_no_db`（mock 优先 args + 真 Gateway 拒非法 schema） |
| C | agent_type/mode allowlist；`None`≠全开；未知 key 安全默认 | ✅ | `strategy/config.py` map + fail-closed `[]`；`test_build_allowlist_none_is_empty_not_full_open` · `test_get_candidate_unknown_key_fail_closed` |
| D | `tenant_scoped`；lookup=True；缺租户拒；有谓词可过 | ✅ | `types.py` · Policy `tenant_scope_missing`；`test_lookup_tenant_scoped_missing_ctx_blocked` · policy 对称测；tool_exec 注入试点 `tenant_id` |
| E | span：args 摘要、policy、`subtask_id`；`approval_id` 预留 | ✅ | `_write_span_metadata`；`test_invoke_span_metadata_includes_subtask_and_args_summary` |
| F | 「注册表」口径；业务不变量不进 schema | ✅ | `01_modules.md` / `10_flow_capability*`「进程内注册表 / 非跨进程注册中心」；CODING **P-16**；defaults docstring |
| 门禁 | pytest 集合绿 · ruff · graph-compile · lint-wiki-delta · chat 零 diff · 无新一级模块 | ✅ | 本帽真跑全绿；`HG-GRAPH-MODULES` 签收行已在 `01_modules.md` |

**勾选数：验收条全 ✅**（相对 30：B 无 PG 可跑缺口已小修）。

---

## failure_paths 抽查

| 路径 | 姿态 | 抽查 |
|------|------|------|
| args 不符 schema | `ok=False` · `args_schema_invalid` | ✅ 单测 + Gateway `_prepare_call` |
| 未知 allowlist key | 空 / 不可见 | ✅ fail-closed `[]` |
| `tenant_scoped` 缺 ctx | `tenant_scope_missing` | ✅ |
| 未知 capability_id | `ok=False` · 图不垮 | ✅ 既有路径保留 |
| 误扩 T/W / chat 拓扑 | 拒收 | ✅ 未扩；`chat/graph.py` 零 diff |
| 「注册中心已上线」 | 拒收 | ✅ 触及文档为否定表述 |

---

## 40 小修

- `tests/test_capability_lookups.py`：新增 `test_tool_exec_prefers_args_over_input_no_db`（验收 B 在无 PG 环境可证）。

---

## 残留风险 / 关账注意

1. `app/ops/capability/schema_validate.py` 仍为 **untracked（??）**——50/commit 须纳入，否则 A 校验源文件丢失。
2. 最小自研 schema 校验器非完整 JSON Schema（30 已记）；复杂 schema 后续再议。
3. 直接 Gateway 调 lookup 须自带 `tenant_id`（tool_exec 已注试点）；行为变更面已测。
4. 本环境 8 skipped 均为 PG 不可用；有 PG 时原 lookup 金样仍应绿。

---

## 结论

**40 PASS** · verify PASS · 交 **50+CLOSE** · 未 commit/push · 未 CLOSE
