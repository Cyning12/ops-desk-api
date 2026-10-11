---
hat: 30
task_slug: n40-1-log-init-window
date: 2026-10-11
---

# invoke · 30-implementation · n40-1-log-init-window（logging 初始化窗口收口）

## GATE_VERIFY（开工首步 · 首输出闸扫描）

命令：`npx spec-wave verify --target . --task docs/tasks/active/task_n40_1_log_init_window.md > /tmp/verify30_n40-1-log-init-window.log 2>&1; echo $?` → **EXIT=0 · VERIFY: PASS**（重定向取真码，未走管道 tail）。

| human_gate_id | task表status | blocks_30 | 30 影响 |
|---------------|--------------|-----------|---------|
| HG-TASK-DRAFT | approved | 22-R1, 30 | — |
| HG-AUDIT-R1 | approved | 30 | ✅ 可 30 |
| HG-GRAPH-MODULES | approved | — | ✅ |

三闸 approved 与 Prompt 声称一致（以 task 表为真值核验）；reviews：docs/harness/reviews/task_n40_1_log_init_window_audit_R1_20261011.md 存在且 PASS-WITH-NITS；pre-30 invoke：10/20 齐全（verify 硬闸通过）。

## 修法裁定：方向 A（main.py 行序上移）——实证裁定留痕

- **裁定：A**。依据：① 窗口根因即行序（import 链 :9-12 先于 :38 模块级调用），最小面即正解（钉死契约 6）；② `_init_logging` 纯 stdlib（logging/os · 亲读 :18-35 函数体逐字不动地上移），零循环 import 风险；③ 方向 B（抽 app/ops/logging_config.py）的复用价值当前无消费者——scripts/evals/alembic 自含 logging 配置面属本 task 非范围，为其臆造共享模块反而触发 G-L2 indexes 同步义务与维护面，收益为负；④ 承 task 倾向 A 且 R1 审查未异议。
- **落地形状**：常量 `_LOG_FORMAT`/`_LOG_LEVEL_NAMES` + `_init_logging()` 定义 + 模块级调用整体上移至首个 app 包 import 之前；app 包四 import（config/hitl/router/tracing）随仓内既有先例（tests/conftest.py:158-167、scripts/、evals/ 共 60+ 处）挂 `# noqa: E402`。函数体与 docstring 逐字未动。
- diff 面：`app/main.py` +10/-5（含 4 行 N-40-1 注释），**capability 发射点字面零 diff**（app/ops/capability/__init__.py、persistence.py、manifest.py 均未触碰）——钉死契约 6 的 GATE_STOP 兜底未触发。
- **图谱回写处置**：方向 A 零新模块/零新符号/零新边 → graph_change_layer 预判 `n/a` 照实成立，G-L2 义务不触发；`./scripts/graph-compile.sh` EXIT=0（再生的 docs/_tech_graph/shared/graph.json 噪音已 `git checkout` 还原）。

## RED → GREEN 证据（红测先行 · 子进程 import 探针）

探针纪律（承 CLOSE 偏差 4）：`PYTHONPATH=仓根` + 显式 env + 主仓 venv python（worktree 无 .env，config.py:11 load_dotenv 锚定本文件路径故无渗入；仍显式控 env 防主仓 .env 场景假绿——`OPS_CAPABILITY_PERSISTENCE=""` 空串 ≡ 未设走 :39 `or MODE_NULL` 同一路径，且 load_dotenv 不覆盖既有 env）。

- **RED（修复前 · base main.py）**：tests/test_log_init_window.py **5 failed / 2 passed**——TC1 窗口 WARNING 裸格式实证（stderr 首行 `能力层持久化未配置（OPS_CAPABILITY_PERSISTENCE 未设）：…` 无 asctime/name/level）；TC2 db 模式 stderr **空**（INFO 整行被吞实证）；TC2 memory 裸 WARNING；TC3 BOGUS 组中格式化 ERROR 告警行（`… app.main ERROR OPS_LOG_LEVEL='BOGUS' …`）已存续但窗口 WARNING 裸格式致断言红。
- **GREEN（修复后）**：同文件 **7/7 passed** + 上游 tests/test_logging_init.py 3/3 回归绿（共 10 passed in 10.47s）。

## 测试断言化（tests/test_log_init_window.py · 7 例）

| 例 | 对应验收 | 口径 |
|----|----------|------|
| test_tc1_window_warning_uses_pinned_format | TC1 核心 | 默认 env 窗口 WARNING 须匹配 `<asctime> app.ops.capability.persistence WARNING …` + 裸格式行禁存 |
| test_tc1_window_invalid_persistence_error_formatted | TC1 补组（**R1 N-1 回填**） | 非法 OPS_CAPABILITY_PERSISTENCE 值：persistence.py:60-64 ERROR + :65-68 WARNING 两行同窗均钉死格式——窗口发射点**四处计全**（:48/:54/:60-64/:65-68） |
| test_tc2_window_info_visible_db_mode | TC2 | db 模式 :48 INFO 行钉死格式可见（修复前整行被吞） |
| test_tc2_window_warning_formatted_memory_mode | TC2 memory 子组（**R1 N-4 口径**） | 断言对象 = persistence.py:54 **WARNING 格式化行**（非 INFO） |
| test_tc3_invalid_log_level_falls_back_info_with_alert | TC3 | BOGUS → ROOT_LEVEL=INFO fail-closed + app.main 格式化 ERROR 告警行存续 + 窗口 WARNING 钉死格式 |
| test_tc3_debug_effective / test_tc3_default_info | TC3 | DEBUG 生效 / 缺省 INFO |

## R1 NIT×4 回填闭合

- **N-1（发射点四处计全）**：已断言化——TC1 补组覆盖 :60-64 ERROR（非法值）+ :65-68 WARNING 同窗两行；四处（:48 INFO db / :54 WARNING memory / :60-64 ERROR 非法值 / :65-68 WARNING null）全有探针组。
- **N-2（env 门控发射点登记）**：全集已闭合——默认 env 面窗口发射仅 persistence 一处（R1 棒 DEBUG 降门槛探针 + 全仓 grep 双重实证）；门控面 manifest.py:218 ERROR（OPS_CAPABILITY_EXTRA_MANIFESTS 坏文件）与 :827/:840 WARNING（reversibility 门控 · 当前 builtin 全声明不发射）登记在案。**修法为发射点无关全覆盖**（初始化行序前移后，凡窗口期经 root 发射的记录一律钉死格式/按级别可见），门控发射点同受益、无需逐一断言。
- **N-3（lint-wiki-delta 钉版）**：TC4 执行以钉版形态为准：`npx --yes spec-wave@3.0.1 task lint-wiki-delta --target .` → EXIT=0 · `LINT-WIKI-DELTA: PASS`（scanned: 160 · issues: 0）。
- **N-4（TC2 memory 断言口径）**：memory 组断言对象 = persistence.py:54 WARNING 格式化行（test_tc2_window_warning_formatted_memory_mode · 非 INFO），本文件 docstring 与上表口径写清。

## TC4 工程面

- **pytest 全量对拍**：修复分支两轮全量 = **4 failed / 1791→1792 passed / 1 skipped**；base（HEAD main.py · 排除新测试文件）全量 = **4 failed / 1785 passed**。红集逐名一致且均为环境性：test_hitl.py::test_db_store_alist_really_executes_on_asyncpg（asyncpg 真库）· test_memory_vector_p1.py::test_embedder_failure_degrades_with_marker（SILICONFLOW_API_KEY 缺失 · 承 repo-logging-init 30 invoke 同红钉案）· test_multi_replica_dualproc.py×2（hitl store=db 前置 · 真库）。**零新增归因红**。注：首轮修复分支全量曾见 test_memory_embedding_backfill.py::test_resume_after_consecutive_page_failures 一红，该例在 base 隔离跑绿、修复分支隔离跑绿、修复分支第二轮全量亦绿 → 序依赖 flaky，不归因本 diff（承 prompt 钉案：本地基线 4-7 红环境性，勿当回归修）。
- **ruff**：触及路径 `app/main.py` + `tests/test_log_init_window.py` All checks passed（EXIT=0）；全仓 55 errors 与上游 30 invoke 登记基线持平（全 pre-existing · 零新增 · 触及文件不在其列）。
- **graph-compile**：EXIT=0（再生噪音 graph.json 已还原，工作树零残留）。
- **lint-wiki-delta**：钉版 @3.0.1 PASS（见 N-3）。

## 钉死契约自查（7 条）

1. OPS_LOG_LEVEL 语义零 diff：`_init_logging` 函数体逐字未动（fail-closed / .strip().upper() 归一 / 非法值 ERROR 告警行存续——TC3 断言实证）。
2. 格式钉死零 diff：`_LOG_FORMAT` 常量 :9（原 :14）逐字未动；探针断言按 `<asctime> app.ops.capability.persistence WARNING …` 正则核验。
3. uvicorn 共存零 diff：未触碰 uvicorn/uvicorn.access logger（函数体未动 · propagate 链未动）。
4. 幂等存续：basicConfig root 已有 handler 天然 no-op（--reload supervisor 子进程 / 自写启动器零 diff · 承上游 N-6 论证存续）。
5. pytest/caplog 面零 diff：全量对拍零新增归因红（见 TC4）；conftest 面未动。
6. 最小面：app/main.py +10/-5 · capability 发射点字面零 diff（git diff 实证 · GATE_STOP 未触发）。
7. 零新依赖（stdlib only · requirements 未动）· 零新 env · 零新表/迁移 · 零新 SSE 事件。

## 偏离 task 记录

- 无实质偏离。两处口径显式化（不属扩缩范围）：① TC1「显式清 OPS_CAPABILITY_PERSISTENCE」落地为显式空串（≡ 未设同一代码路径，且防 .env 渗入 · 上文探针纪律）；② TC2 memory 子组按 R1 N-4 口径断言 WARNING 行。

## 遗留

- 40 帽：live 验收（uvicorn 实跑 / access log 单行）承上游分工归 40 面；master 带 .env 环境的 4 红基线复跑口径承 repo-logging-init N-5 deferred 40。
- test_memory_embedding_backfill flaky（序依赖 · 双版本隔离均绿）建议另案登记，不入本 task 范围。
