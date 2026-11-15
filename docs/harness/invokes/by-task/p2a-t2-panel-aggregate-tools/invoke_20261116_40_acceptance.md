# invoke · 40_acceptance · p2a-t2-panel-aggregate-tools

## 内容

P2a-T2（面板聚合双工具 get_overview / graph_snapshot）验收：目标套件全绿 + 全量对拍失败集恒等 + ruff/graph-compile/spec-wave 绿 + CI 四绿 + 偏差如实登记。

## 验证台账

| 项 | 命令 | 结果 |
|---|---|---|
| T2 新测试文件 | pytest tests/test_capability_panel_aggregate_tools.py -q -rs（五键 blank） | 24 passed · 0 skipped（PG _DB_MARK 用例全跑实证） |
| capability 电池（十件） | pytest 新文件+manifest+panel_tools+testing_write+reconcile+stage_w+env_extra+domain_allowlist+overview+graph -q（五键 blank） | 150 passed 0 failed |
| manifest V10 nullable | pytest tests/test_capability_manifest.py -q | 绿（参数化 +nullable 两负样本 + 合法形状断言扩 nullable 键） |
| 全量套件（提交后） | pytest tests -q（五键 blank） | 2148 passed · 余红 16 枚 |
| 全量对拍 | base 8af02c4a worktree + 同五键 blank 跑同 18 枚子集 | **失败集恒等**：branch 提交后 16 枚 = base 16 枚逐名对应（外部环境/.env 污染既有红）；脏树期 wave_gate_registry/tc8/episode_pattern_mine 三枚红为在途面守卫语义（registry :88-90 closed entry 同样咬）提交后复绿 3 passed |
| ruff | ruff check app tests | All checks passed |
| graph-compile | ./scripts/graph-compile.sh | ok（10 md · check-only） |
| spec-wave | task lint --file + verify --task | PASS · 三闸 approved 可 30 |
| CI（终裁 · 无 .env） | gh pr checks 404 --watch | **四绿**：pytest 2m20s · check 17s · import-linter 11s · lint-wiki-delta 12s（run 43745466184 等） |

## 结果

feat PR #404 squash merge → master 94f5ba87。验收十条全勾（task 档自检结论）。

## 偏差记录

承 invoke_20261116_30_impl.md 五项（when_to_use 承 T1 先例 · V10 白名单 +nullable 扩 manifest.py 入 allowed 面 · builtin 头注释纠 stale · 六锚 7→9 既定推进 · OPS_CAPABILITY_EXTRA_MANIFESTS 本地 .env 污染面新发现——测试策略已改钉五键 blank），无新增。
