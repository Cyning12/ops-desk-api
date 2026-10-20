# invoke · 30 implement · scenario-stage-rewire（2026-10-20）

> 帽：30（摘除实施）· 分支 task/scenario-stage-rewire（base a1591e9 = docs/task-scenario-stage-rewire HEAD = master 51e75c9 + 文档线）
> task：docs/tasks/active/task_scenario_stage_rewire.md（188 行）· SPEC v0.1 signed · R1 审查文 conditional_pass

## 0. GATE_VERIFY 机读误报说明（承 #1/#2 先例 · 第三次）

`npx spec-wave verify --target . --task docs/tasks/active/task_scenario_stage_rewire.md` 机读报「HG-AUDIT-R1 非 approved」；
task 人工闸表（:33-39）真值 = HG-SPEC-SIGNOFF / HG-AUDIT-R1 / HG-GRAPH-MODULES **全 approved**。
授权链 `invoke_20261020_gate_sign_hg_audit_r1.md`（维护者授权 00 代签）在册。**以闸表真值为准开工**（#1/#2 同款误报两次先例）。

## 1. 锚点按实校正记录（30 亲读复核 · 吸收 R1 nits N1–N3）

| 项 | task 写 | 实测 | 处置 |
|---|---|---|---|
| N1 builder.py import 区间 | :17-20 | **:17-21**（三件 import 块含收束括号行） | 整句删（:17-21 五连行） |
| N2 D5 保留面 | :76-169 | **:75-181**（S1–S5 段实际起止） | 按 :75-181 逐字保留 |
| N3 文件头 docstring | — | tests/test_strategy_scenario.py:1-11 仍述被删三档模式 | 顺手改写（TC8 白名单内） |
| 调用点 | :158 | :158 命中 | 删 |
| 函数本体 | :111-128 | :111-128 命中（:118 scenario_mode() · off :119-120 / observe :124-126 / enforce :127-128） | 删 |
| docstring/两阶段注释 | :149 / :155-157 | 命中 | 改写为「allowlist = candidates ∩ 基线可见集直接求交（scenario 阶段已摘除 · 2026-10-20 · 与摘除前恒短路输出逐值等价）」 |
| multi/nodes.py | :1267 注释 | :1266-1269 四行注释段 | 仅注释行改写（禁出现 scenario_trim 字样 · 已验） |
| D3 env 台账 | GUIDE_env_inventory_v1.md:35 | 实路径 **docs/guides/**GUIDE_env_inventory_v1.md:35（task 未带 guides 段） | :35 行备注加 deprecated |
| D4 图谱 | 01_modules.md:35 lg_rag 行「路径覆盖补记」strategy 段（V1-B 备注处） | 命中（V1-B 段末「三重交集钉死…（R1 审查 B-1 澄清）；」） | 追加「scenario 裁剪已摘除（恒短路清理 · 2026-10-20 · 模块 dormant 保留）」· 不新行 |

## 2. 摘除面实施清单（D1–D6）

- **D1** app/ops/strategy/builder.py：三件 import（audit_scenario_stripped/scenario_mode/scenario_trim）整句删；`_apply_scenario_stage` 本体 :111-128 删；调用点 :158 删；docstring 句与两阶段注释改写（口径：恒短路逐值等价）。
- **D2** app/ops/strategy/scenario.py：本体 **dormant 保留零逻辑改动**；文件头加 dormant 注释（含「LG_RAG_VISIBILITY_SCENARIO_MODE 已废弃（2026-10-20）」「全仓零生产调用方」「复用须另立 SPEC 走全流程」）。模块内 os.environ.get(:51 旧址) 保留（dormant 本体残留 · 裁定口径）。
- **D3** docs/guides/GUIDE_env_inventory_v1.md:35：备注列加「已废弃 deprecated（2026-10-20 · scenario 阶段摘除 · 生产零消费 · scenario.py 本体 dormant 保留）」。
- **D4** docs/_tech_graph/l1/01_modules.md:35：lg_rag 行 V1-B 备注处追加（不新行）。
- **D5** tests/test_strategy_scenario.py：删六项 env/台账用例（:189-256）；改写四项去 env 耦合；保留 S1–S5+smoke（:75-181 / :386-395 逐字）；新增 env 失效断言（{None,off,observe,enforce,bogus}×{无/有 high intent} 10 参数矩阵）。全文 395→432 行。
- **D6** sse_stream.py:64 死映射 / intent.py:94 留尸 **不动**（互锁登记 · 见 §5 清单）。

## 3. 红测先行计数

测试文件先改写落盘、生产码未动时跑：`4 failed, 31 passed`。红集合恰为预期四件：

1. `test_env_mode_has_no_effect_on_builder_output[True-enforce]`（旧码 enforce+high intent 真裁 MEDIUM_CAP → 摘除后必绿）
2. `test_builder_has_no_scenario_residue`（残留四禁词 → 摘除后必绿）
3. `test_scenario_module_dormant_but_importable`（无 dormant 头 → 加注释后必绿）
4. `test_graph_and_env_inventory_synced`（文档未同步 → D3/D4 后必绿）

实施后同文件 **35 passed**（含后补 TC3 grep 半断言 · 仍 35 因断言并入既有用例）。

## 4. 验证矩阵（park .env · 2026-10-20）

| 项 | 命令 | 结果 |
|---|---|---|
| 全量 pytest | `.venv/bin/python -m pytest tests -q`（.env 已 park 至 /tmp/ops-desk-api.env.parked） | **1 failed, 1743 passed, 182 skipped** — 唯一失败 `test_memory_injection_consumer.py::test_phase_b_diff_whitelist`，与基线同一件（见 §6 对拍） |
| ruff | `.venv/bin/ruff check app tests` | All checks passed! |
| 图谱 | `./scripts/graph-compile.sh` | EXIT=0（mermaid normalize check 9 md OK） |
| import 分层 | `.venv/bin/lint-imports` | Contracts: 12 kept, 0 broken |

## 5. TC9 全仓引用清单（含「已知残留 · 不动」登记）

**_apply_scenario_stage**：摘除前仅 builder.py:111（本体）/:158（调用）+ tests + docs；摘除后 app/ 零命中。
**scenario_trim / scenario_mode / audit_scenario_stripped**：生产侧摘除前仅 builder.py（import :18-20 · 调用 :112/:118/:121/:125/:127）+ scenario.py 本体 + multi/nodes.py:1267 注释；摘除后仅 scenario.py 本体（dormant）。
**LG_RAG_VISIBILITY_SCENARIO_MODE**：app/ 内仅 scenario.py（:19 docstring · :38 常量 · :51 os.environ.get · dormant 本体残留）；机断断言 `env_key_hits == ["app/ops/strategy/scenario.py"]` 入 `test_builder_has_no_scenario_residue`。余命中全在 docs/tests。
**intent_node（app/ 内）**：
- chat/graph.py:14,30 + chat/nodes.py:56 —— chat 410 legacy 面 · 非范围不动
- multi/graph.py:82 注释 —— 已述直接求交口径 · 不动
- **multi/__init__.py:5 拓扑 docstring 过期 —— 已知残留 · 不动（TC8 白名单外 · 登记）**
- **sse_stream.py:64 死映射 _ROLE_ALIAS —— 已知残留 · 不动（D6 互锁 · 承 SPEC §7 风险表）**
- state.py:250 注释 · strategy/intent.py:52 注释 —— 不动
- **strategy/intent.py:94 留尸（IntentV1 唯一写入方未挂载）—— 已知残留 · 不动（D6 互锁）**

## 6. 对拍证据（.env 环境噪声铁证）

- **park .env 基线（a1591e9）**：1 failed, 1731 passed, 182 skipped；唯一失败 = `test_phase_b_diff_whitelist`（#2 白名单不含 #3 分支文件）。
- **park .env 摘除后**：1 failed, 1743 passed, 182 skipped；唯一失败 **同一 test id 同一根因**（#2 白名单为 #2 波次界 · #3 分支文件必然越界 · 分支既有结构失败 · 非本次摘除引入）。passed +12 = D5 改写后参数化用例数净增。
- **.env 在场基线（worktree /tmp/ops-desk-baseline-a1591e9 @ a1591e9 + .env）**：38 failed, 1694 passed, 182 skipped（test_react_observe / test_strategy_builder / test_strategy_env_extra_candidates 等 .env 噪声）；完整失败清单存 /tmp/baseline_env_present_a1591e9.txt。
- **.env 在场摘除后（worktree /tmp/ops-desk-impl-0312e7b @ 0312e7b + .env）**：38 failed, 1706 passed, 182 skipped；FAILED 清单（38 项 · /tmp/impl_env_present_0312e7b.txt）与基线清单（/tmp/baseline_env_present_a1591e9.txt · grep '^FAILED'）**逐项 IDENTICAL**（diff 零输出）。结论：.env 在场 38 败全为环境噪声（基线即败 · 摘除不增不减）。
- 预存现象备注：`import app.ops.strategy.builder` 直导触发循环 import（nodes.py:78 部分初始化）——pristine worktree 同现，非本次引入。

## 7. 禁区自查

- app/ 改动 ⊆ {builder.py, scenario.py（仅文件头注释）, multi/nodes.py（仅注释行）} · TC8 白名单机断绿（`test_diff_whitelist_scenario_stage_rewire` · _resolve_base 三级探测照抄 tests/test_memory_injection_consumer.py:585-609 · 钉锚 a1591e9）
- scripts/ alembic/ 零触达 · 零新 event_type / 路由 / 表
- SSE 帧 / HTTP 契约零变化（freeze lg-rag-sse-v1 / lg-rag-http-v1 · sse_stream.py 与 router 面不在白名单 · diff 零）
- scenario.py / IntentV1 未删 · chat 图未碰 · 无顺手清理（multi/__init__.py:5 过期 docstring 白名单外 · 登记不动）
- 枚举外冲突零发生（无 STOP 呈裁事项）
- untracked `backups/` 与 `docs/harness/reviews/task_query_coref_rewrite_review40_20261019.md` 为他务预存 · 本波不纳管不提交
