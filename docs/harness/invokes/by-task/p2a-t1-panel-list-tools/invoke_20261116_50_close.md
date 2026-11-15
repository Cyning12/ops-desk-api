# invoke_20261116_50_close

## 内容

P2a-T1 CLOSE 关账：registry status=closed 钉 wave_tip=f8a9054（PR #402 squash merge）；task 档 git mv 至 docs/tasks/done/；验收八勾回填；偏差终录。

## 验证台账（终）

| 项 | 结果 |
|---|---|
| PR | #402 · squash merge · merge sha f8a9054c922b32cc530de4fed7ea31f5687c796d（短 7：f8a9054） |
| CI 四件 | pytest 2m30s（含真 PG service 真跑）· check · import-linter · lint-wiki-delta 全绿（runs 43741245061-121） |
| 目标套件 | tests/test_capability_manifest.py + tests/test_capability_panel_tools.py：38 passed · 0 skipped（真 PG 层 4 用例真跑 · DB_AVAILABLE=true） |
| 闸矩阵 | page_size=0/21 · page=0/-1 · state 词表外 → LookupError → ok=False；additionalProperties 多余键 → args_schema_invalid；tenant_scope_missing ×2；委派层默认 off |
| catalog 红线 | _format_capability_catalog（7 specs）≤6000 字符断言绿 |
| span tenant_id | 正常/reject/无 ctx 三路径 payload 含 tenant_id（update_current_span_metadata 实证） |
| 真 PG 双层 | 双租户 seed（A3+B1 issues · A2+B1 prs）：跨租户空集 · 分页 total/page 正确 · label/module/state/ci_status 过滤正确 |
| 全量对拍 | branch vs master+同 .env worktree 失败集恒等（余红 18 枚逐名对应 · 皆仓根 .env 四键污染 · 承 api-controlled-write-hitl invoke_20261030_30_implement.md:49 先例） |
| spec-wave | task lint PASS · verify PASS（三闸 approved · 思考轮 R0-R5 齐） |
| graph-compile | 绿（01_modules.md capability 行备注 + HG-GRAPH-MODULES 人签行 splice 2026-11-16） |
| ruff | uv run ruff check app tests 绿 |

## 偏差终录（五条 · task 档/registry/40 台账同源）

1. when_to_use loader 必填（manifest.py:523-526）与 R2「不填」冲突 → 新条目填与 description 一致的简短引导，when_not_to_use 不填。
2. _DEFAULT_SPECS 同步 +2（test_capability_manifest 对齐断言前提 · fallback 路径契约不漂移）。
3. 存量「builtin 五枚基线」锚推进 5→7 ×3 处：test_capability_manifest（_BUILTIN_IDS+计数）· test_strategy_env_extra_candidates（静态对拍锚）· test_capability_testing_write:329/test_stage_w_write_expand:260（count）。
4. CI 实证另两枚同性质锚（本地被 .env 遮蔽）：test_capability_testing_write.py:77 局部 _BUILTIN_IDS 集合 · test_ops_write_catalog_reconcile.py:297 count==5 → 推进七枚（registry 偏差四）。
5. HG-AUDIT-R1 补登 approved + 20-R1 审查文补落（docs/harness/reviews/task_p2a_t1_panel_list_tools_audit_R1_20261116.md · 同授权依据 issue #23 m03064+08 设计终稿 · 授权范围零新增）；本地全量余红=.env 环境性。

## 结果

CLOSE 关账完成：registry closed · wave_tip=f8a9054 · task 档入 done/ · 验收八勾全绿。
