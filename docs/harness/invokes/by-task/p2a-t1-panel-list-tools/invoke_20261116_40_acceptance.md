# invoke_20261116_40_acceptance

## 内容

P2a-T1（面板列表双工具 query_issues / query_pull_requests）验收：目标套件全绿 + 全量对拍失败集恒等 + ruff/graph-compile/spec-wave 绿 + 偏差如实登记。

## 验证台账

| 项 | 命令 / 方法 | 结果 |
|---|---|---|
| 目标套件（InMemory+真 PG 双层） | OPS_HITL_PERSISTENCE= OPS_CAPABILITY_ALLOW_WRITE= OPS_CAPABILITY_ALLOW_WRITE_TAGS= OPS_CAPABILITY_PERSISTENCE= uv run pytest tests/test_capability_manifest.py tests/test_capability_panel_tools.py -q | 38 passed · 0 skipped（真 PG 层 4 用例真跑 · DB_AVAILABLE=true） |
| 真 PG 双租户 | _DB_MARK 用例：A3+B1 issues / A2+B1 prs seed | 跨租户空集 · 分页 total/page 正确 · 过滤（label/module/state/ci_status）正确 |
| 闸矩阵 | adapter 直调 + gateway 层 | page_size=0/21、page=0/-1、state 词表外 → LookupError → ok=False；additionalProperties 多余键 → args_schema_invalid；tenant_scope_missing ×2；委派层默认 off（monkeypatch.delenv 防 .env enforce） |
| catalog 体积红线 | _format_capability_catalog(7 specs) | ≤6000 字符断言通过（args_schema 无 per-prop description） |
| span payload tenant_id | patch update_current_span_metadata ×3 | 正常/reject/无 ctx 三路径 payload 含 tenant_id |
| ruff | uv run ruff check app tests | 绿 |
| graph-compile | ./scripts/graph-compile.sh | 绿（01_modules.md capability 行备注 + 人签行 splice） |
| spec-wave task lint | npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_p2a_t1_panel_list_tools.md | PASS（W2/W5/W6 warn-only · p1-t4 先例同 warns） |
| 全量 pytest（branch） | 主 checkout（带 .env） | 2118 passed · 20 failed（次轮；首轮 24 含脏树 registry 闸噪点已自愈） |
| 全量对拍 | master worktree + 同 .env 跑同失败子集 | **失败集恒等**：branch 19 = master+env 18 + stage_w count 锚（本单既定推进 5→7 后复绿）；其余 18 枚逐名对应（.env 四键污染所致，承 api-controlled-write-hitl invoke_20261030_30_implement.md:49 先例 · CI 无 .env 不红） |

## 结果

验收通过：设计终稿 §7 第一行全部验收勾选项达成（§5 测试矩阵绿 · 跨租户空集 · page_size=21 被 adapter 拒 · span payload tenant_id 实证 · catalog ≤6000）。

## 偏差记录

1. **when_to_use 必填冲突（R2 vs loader）**：manifest.py:523-526 要求 when_to_use 非空否则 ManifestError 整文件失败 → 两枚新条目填简短引导（与 description 一致），when_not_to_use 缺省不填。登记于 registry note 与 task 档实现备忘。
2. **_DEFAULT_SPECS 同步**：test_capability_manifest.py 钉 set(_BUILTIN_IDS)==硬编码 ids → defaults.py 同步 +2（fallback 路径契约不漂移）。设计未显式覆盖，按最小改动裁定。
3. **既有循环 import**：直接 import app.ops.strategy.config 触发 strategy.builder ↔ lg_rag.multi.nodes 循环（master 基线 git stash 实证既有），与本单无关。
4. **五枚基线锚推进 ×3 处**：test_capability_manifest.py（计数 5→7 · _BUILTIN_IDS +2 · 设计内）+ test_strategy_env_extra_candidates.py（静态对拍锚五枚→七枚 · 偏差二）+ test_capability_testing_write.py:329 / test_stage_w_write_expand.py:260（count==5→7 · 偏差三）。语义断言均未动。
5. **闸表格式两轮修正**：verify 机判要求 `### 人工闸`（嵌 Harness 元信息节内 · 表头 human_gate_id|status|blocks_hats|说明）+ 思考轮控制表（R0-R5 槽位+点名小节）+ 20-R1 审查文（docs/harness/reviews/task_p2a_t1_panel_list_tools_audit_R1_20261116.md · GO）；HG-AUDIT-R1 补登 approved（同依据：issue #23 m03064+08 设计终稿 · 授权范围零新增 · task 档修订记录如实登记）。
6. **本地全量 20 failed 皆环境性**：仓根 .env（LG_RAG_SUPERVISOR_PLAN_ON_FAIL=single_rag :86 · LG_RAG_DELEGATION_TOKEN_MODE=enforce :79 · OPS_CAPABILITY_EXTRA_MANIFESTS :81 · OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS :83）conftest import 期载入；master+同 .env 对拍逐名同红；CI 无 .env。
