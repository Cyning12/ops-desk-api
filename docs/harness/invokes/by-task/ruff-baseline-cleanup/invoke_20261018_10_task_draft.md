# Invoke：ruff-baseline-cleanup · 10 task draft（2026-10-18）

> **帽位**：10-task（受 00 委派 · 方向 A1 维护者 m01071「开始A1」选定）
> **产出**：`docs/tasks/active/task_ruff_baseline_cleanup.md`（draft · HG-TASK-DRAFT/HG-AUDIT-R1 pending · HG-GRAPH-MODULES n/a）
> **纪律**：零 git 操作 · 零业务码改动 · 仅落 task 档 + 本 invoke 两件

## 一 · 范围（起草落框）

F1 `--fix` 自动修 28 处逐类复核 · F2 人工裁定 24 处（F811 九对逐对 diff 裁定表为核心 · N818 默认 noqa 不改名）· F3 format 漂移 223 文件一次性收口（独立 commit · 破约回退明裁）· F4 CI ruff 闸裁定（实况未接 · 默认建议接入 pytest.yml 并注明 CI 改动 · 维护者签闸可改判）· F5 invoke 留档。30 棒走 `task/ruff-baseline-cleanup` worktree PR 流；硬闸 = PR CI pytest 绿 + 本地红集 ⊆ 基线 19 红集（零新增红）。

## 二 · 实证锚点（全部 10 亲跑 2026-10-18 · master `c956d87` · 非转述）

| 项 | 命令 | 实录 |
|----|------|------|
| ruff 版本 | `uv run --extra dev ruff --version` | **0.15.21**（uv.lock:1831-1835 钉 · pyproject.toml:47 specifier `>=0.5,<1` · 本 task 不升级） |
| check 总量 | `uv run --extra dev ruff check app tests` | **Found 52 errors · 28 fixable with --fix**（8 hidden unsafe fixes 不启用）——与 00 提供基线一致 |
| 分布 | `... --statistics` | F811×9 · I001×9[*] · C408×7 · SIM117×7[*] · E402×5 · SIM300×4[*] · UP035×3[*] · F401×2[*] · UP045×2[*] · C401×1 · N814×1 · N818×1 · UP034×1[*] |
| F811 九对 | `--select F811 --output-format concise` | redlines：572→777 · 617→822 · 640→845 · 703→908 · 743→948；manifest：468→523 · 476→531 · 554→597 · 581→624（均先定义被后定义遮蔽成死码 · 两版是否发散待 30 逐对 diff） |
| E402 | `--select E402` | http_generic.py:65-66（:63-64 注释 + :66 既有 noqa:F401 互证有意布局 · 判 noqa 留痕或上移）· test_lg_rag_sse_token_stream.py:32,33,39 |
| format 漂移 | `ruff format --check app tests` | **223 would reformat / 103 ok**（app 115/74 · tests 108/29）——漂移面巨大，故 F3 默认取一次性收口 |
| CI 闸 | 亲读 `.github/workflows/` 六件 | pytest.yml:52-53 Ruff 段**整段注释**；lint-wiki-delta/import-linter/tech-graph/deploy-api/ops_sync_kimi_code 均无 ruff → 存量 52 未拦根因 |
| pytest 基线 | `.venv/bin/python -m pytest tests -q --tb=no` | **19 failed, 1828 passed, 1 skipped（68.77s）** —— 本地非全绿，红集清单见 §四 |

## 三 · 裁定记录（10 层面 · 终裁在维护者签闸 / 30 实证）

1. **F3 format**：漂移 223/326 文件（68%）→ 起草本 task 采纳「一次性 `ruff format app tests` 收口 · 独立 commit 隔离机器 diff」，而非「不修只钉现状」（钉现状会让每个后续 PR 持续吃 format 噪音）。破约（新增红/import-linter 红）即回退明裁。
2. **F4 CI**：ruff 未入 CI 是存量扩散根因 → 默认建议本 task 内解开 pytest.yml:52-53 并改为 `.venv/bin/ruff check app tests`（uv.lock 同源 · 禁 pip 漂移版）；**CI 改动须 PR 注明**；维护者签闸时可改判不接（30 明裁留档）。
3. **N818 CircuitOpen**（app/ops/capability/circuit.py:76）：app 侧公开异常名，重命名 = API 语义变更 → 非范围，默认 noqa 留痕。
4. **pytest 硬闸形态**：00 委派口径「pytest 全量绿」，但亲跑实证本地基线 19 红（master 干净态）→ task 落为「PR CI pytest 绿 + 本地红集 ⊆ 基线 19 红集（零新增红）」，更贴合仓实况且仍可机断。
5. **GRAPH 闸**：graph_change_layer=none（纯 lint/format · 无新模块/路由/表/事件）→ HG-GRAPH-MODULES 标 n/a（零图谱变更先例口径）。

## 四 · pytest 本地基线 19 红集（master c956d87 亲跑 · 30/40 对拍基准）

- tests/eval/test_capability_redlines.py::test_r1_write_blocked_without_host_policy_and_no_downstream_request
- tests/eval/test_capability_redlines.py::test_r11_session_budget_and_kill_switch_block_before_downstream
- tests/eval/test_eval_capability_golden.py::test_case_matches_expect[invoke_write_without_host_policy_is_blocked_with_zero_requests]
- tests/eval/test_eval_capability_golden.py::test_no_drift_against_committed_baseline
- tests/test_admin_capability_observability.py::test_metrics_exposes_write_blocked_counter
- tests/test_capability_http_adapter.py::test_gateway_blocks_write_without_host_policy
- tests/test_capability_lookups.py::test_tool_exec_lookup_ainvoke_and_error_continues
- tests/test_capability_lookups.py::test_tool_exec_prefers_args_over_input_no_db
- tests/test_capability_lookups.py::test_tool_exec_prefers_args_over_input
- tests/test_capability_testing_write.py::test_a6_manifest_loads_and_fields_pinned
- tests/test_capability_visibility_and_receipts.py::test_policy_blocked_write_records_nothing
- tests/test_hitl.py::test_db_store_alist_really_executes_on_asyncpg
- tests/test_hitl_approval_consumption.py::test_ta4_consumption_hit_does_not_waive_gateway_or_policy
- tests/test_lg_rag_multi.py::test_unknown_tool_at_invoke_recorded_and_continues
- tests/test_multi_replica_dualproc.py::test_hitl_cross_instance_resume
- tests/test_multi_replica_dualproc.py::test_resume_without_checkpointer_503
- tests/test_strategy_builder.py::test_get_candidate_unknown_key_fail_closed
- tests/test_strategy_env_extra_candidates.py::test_tc2_fp5_deny_order_still_cuts_write_and_high_risk
- tests/test_strategy_env_extra_candidates.py::test_tc2_fp5_policy_write_gate_still_blocks

> 注：红集多为环境依赖面（PG 实连/multi-proc/golden 对拍等）；与 close_hitl_resume_async §三 TC7 所录「7 failed/1815 passed · 与 master 基线同集」口径不同系执行机环境差异，本 task 以本清单为对拍基线。

## 五 · 门禁实录（10 亲跑）

- `npx spec-wave task lint --file docs/tasks/active/task_ruff_baseline_cleanup.md` → **EXIT=0 · LINT: PASS**（首跑 E5 缺 ### 自检结论 节 · 已补空槽待 30/40 回填后 PASS）。
- `npx spec-wave task lint-wiki-delta --target . --scope active` → **EXIT=0 · LINT-WIKI-DELTA: PASS**（scanned: 1 · missing: 0 · issues: 0）。
- 委派口径的命令 `npx spec-wave lint-wiki-delta --scope active` 为**未知命令**（CLI 无此顶层子命令）→ 采用与 CI 一致的 `task lint-wiki-delta` 形态，实证 PASS，如实照登。
- 未跑 `spec-wave verify`（闸全 pending · 属 30 开工前 GATE_VERIFY 面）。

## 六 · 交接

- 00/维护者：签 HG-TASK-DRAFT →（授权则 20 R1）→ 签 HG-AUDIT-R1 → 30 开工。F3/F4 默认建议见 §三.1/§三.2，签闸时可改判。
- 30：必读 task 档「给执行帽的必读列表」+ 本 invoke §二/§四；禁信转述，F811 九对亲读两版再裁定。
