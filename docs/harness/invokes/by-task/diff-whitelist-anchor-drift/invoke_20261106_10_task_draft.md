# invoke · 10 起草 · diff-whitelist-anchor-drift（2026-11-06）

| 项 | 值 |
|----|----|
| hat | `10`（task 起草 · 承 issue #337 维护者令） |
| task_slug | `diff-whitelist-anchor-drift` |
| task 文件 | `docs/tasks/active/task_diff_whitelist_anchor_drift.md` |
| 分支 | 落稿 `agent/diff-whitelist-task-5e3e38c2abdd`（部署绑定末段=工单名）；30 执行分支预登记 `fix/diff-whitelist-anchor-drift`（base `master` · 待闸签收后另行授权） |
| 指令来源 | issue #337 维护者 comment [`6682233401`](https://github.com/Cyning12/ops-desk-api/issues/337#issuecomment-6682233401)（2026-11-06 18:01）：「请按 Harness 流程起草 fix task 文档（10 帽活：只产 task 档 + lint PASS + PR；30 待闸签收后另行授权）」四要求（设计闸决策点=诊断裁决 / 红测先行入 test_strategy / 红线入 failure_paths / lint PASS 出货）· 受理依据 = 维护者 2026-11-06 13:40 多选授权（lead 代行签收与验收） |

## 输入真值（已读）

- issue #337 正文（backlog：本地全量 pytest 既有 4 failed 中 2 条为 diff-whitelist 锚点漂移 · 要求=修锚点或刷新基线 whitelist · 纯测试基建 · 来源 #323 40 invoke 增强/收尾清单）。
- 维护者 comment `6682233401`（题面 = stage-w-004/stage-w-002 本地基线红 · 四要求：① task 档含范围/非范围/验收/failure_paths/人工闸表/思考轮 · 设计闸决策点=诊断裁决（二选一必须有证据——先跑两条用例拿当前实际行号与输出再裁）；② 红测先行写进 test_strategy · 负样本=修复后两条本地基线红转绿（pytest 命令级可复验）；③ 红线入 failure_paths：只动测试基建 · 不碰实现/SSE/freeze；④ lint PASS 后出 PR 待审）。
- stage-w invoke 证据链（`docs/harness/invokes/by-task/stage-w-write-expand/` 30 :58 / 40 :30 / 50 :35 · 留转③ = 本 task 立项来源）。

## 10 档取证（诊断证据 · 只读不改）

**环境**：工作树 @ `d594dc3`（= origin/master · 干净树零未提交改动 · untracked 空集）· `.venv/bin/python -m pytest`（本机 venv 补装 pytest/pytest-asyncio/respx · 承 ops-write-catalog-reconcile 先例）。

**实测（2026-11-06 · 修复前基线红 · 输出全文摘录）**：

```
$ .venv/bin/python -m pytest \
    tests/test_lg_rag_write_replay_guard.py::test_tc8_diff_whitelist \
    tests/test_strategy_scenario.py::test_diff_whitelist_scenario_stage_rewire
...
E  AssertionError: 禁改面（scripts/ alembic/ 及其余 app/）出现改动:
   ['alembic/versions/20261105_capability_notes.py', 'app/db/models.py', 'app/main.py',
    'app/ops/capability/defaults.py', 'app/ops/capability/manifest.py',
    'app/ops/capability/manifests/builtin.v1.yaml', 'app/ops/capability/manifests/ops.write.v1.yaml',
    'app/ops/capability/manifests/testing.v1.yaml', 'app/ops/capability/note_store.py',
    'app/ops/capability/types.py', 'app/ops/hitl/router.py', 'app/ops/hitl/store.py',
    'app/ops/issues.py', 'app/ops/lg_rag/event_store.py',
    'app/ops/lg_rag/multi/step_contract.py', 'app/ops/lg_rag/router.py',
    'app/ops/lg_rag/thread_store.py', 'app/ops/overview.py',
    'app/ops/prompts/assets/lg_rag.supervisor.suffix.system.md',
    'app/ops/prompts/assets/lg_rag.supervisor.system.md', 'app/ops/pulls.py',
    'app/ops/tenant_context.py', 'scripts/graph-compile.sh']
tests/test_lg_rag_write_replay_guard.py:450: AssertionError
E  AssertionError: 禁改面（scripts/ alembic/）出现改动:
   ['alembic/versions/20261105_capability_notes.py', 'scripts/graph-compile.sh']
tests/test_strategy_scenario.py:554: AssertionError
FAILED tests/test_lg_rag_write_replay_guard.py::test_tc8_diff_whitelist
FAILED tests/test_strategy_scenario.py::test_diff_whitelist_scenario_stage_rewire
========= 2 failed in 0.21s =========
```

**溯源（banned 文件 → 合入 commit · 均钉锚后合法波次）**：

| 文件 | 锚窗 | 溯源 | 判定 |
|------|------|------|------|
| `scripts/graph-compile.sh` | `git log d337486..HEAD --` | `6c9d0e6`（specwave 3.3.0→3.5.0 钉位全量对齐） | 合法后续波次 |
| `scripts/graph-compile.sh` | `git log a1591e9..HEAD --` | `6c9d0e6`（同上） | 合法后续波次 |
| `alembic/versions/20261105_capability_notes.py` | `git log a1591e9..HEAD --` | `51030a4`（stage-w · PR #327 `ops.write.run_note` 新迁移） | 合法后续波次 |

**锚可解析性**：`git rev-parse --verify d337486^{commit}` / `a1591e9^{commit}` / `c17e63b^{commit}` / `63bad3d^{commit}` 四锚皆命中（wave tip = PR #288 / PR #286 合并 commit）→ 非锚点对象缺失。

**10 档诊断倾向（证据归 10 · 裁决属闸）**：两枚 banned 文件全部可溯源至钉锚后的合法波次合入 · 四锚皆可解析 → 证据形态指向 **whitelist 过期（基线漂移）→ 刷新基线**一支；最终二值裁决与刷新形态（重钉 `_BASE` / 改固定波次窗语义 / 调 `_allowed` 面）由 HG-DIFF-WHITELIST-DIAGNOSIS 签认（FP-5 禁自裁）。

## R 轮结论摘要

| 轮 | 结论 |
|----|------|
| R0 | 缺陷 = diff-whitelist 锚点漂移 ×2（测试基建面）：钉锚停 2026-10-20 波次切出点 · diff 窗随 master 增长 · 后续合法波次撞 banned 前置（O2 挡在态③ skip 前）→ 常态红；实跑取证双用例（:450 22 件 / :554 2 件）+ 溯源 `6c9d0e6`/`51030a4`（residual_risk：题面 stage-w-004/002 编号与用例 id 无字面对应 · 按实测+登记链双向锁定） |
| R1 | 范围 = 诊断裁决执行 + 红转绿证据 + 红线对拍；非范围八条（裁决自裁/实现/SSE·freeze/删闸/其他测试文件/回退他人合入/spec-wave 上游/web·iOS） |
| R2 | 设计闸二值（HG-DIFF-WHITELIST-DIAGNOSIS）：修锚点（锚真漂移：对象缺失/改写/钉错 · 证据=rev-parse 失败）/ 刷新基线（锚可解析 ∧ banned 全溯源合法波次 · 子形态=重钉/改固定窗/调白名单面 · 签认指明）；10 档证据指向刷新基线一支 · 裁决属闸 |
| R3 | FP-1~FP-9：四闸拒开工 / 禁拆闸强转绿 FP-2 / SSE·freeze 零 diff FP-3 / 不碰实现 FP-4 / 裁决属闸 FP-5 / 证据先于裁决 FP-6 / 不修史 FP-7 / 改码面收敛 FP-8 / 闸表契约 FP-9 |
| R4 | 红测先行：负样本 = 修复后两条本地基线红转绿（pytest 命令级可复验 · 修复前 2 failed 输出全文已备）· 防恒绿失效含回归牙对拍 |
| R5 | 落稿 · A1 锚点语义专节钉死 · 四闸 pending · NO-GO 20/30 · lint PASS 出货待审 · 30 待闸签收后另行授权 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：①题面 stage-w-004/stage-w-002 编号与仓内用例 id 无字面对应（按实测+登记链锁定两枚 · 设计闸可澄清）；②刷新基线子形态待 HG-DIFF-WHITELIST-DIAGNOSIS 签认指明

## task_slug 说明

`diff-whitelist-anchor-drift`（fix/测试基建面类 · 承载面 = 两枚 diff-whitelist 闸的锚点/whitelist 基线）；task 文件 / 30 分支 `fix/diff-whitelist-anchor-drift` / invoke 目录同名一致。

## A1 锚点语义（task 档专节钉死 · 本 invoke 摘要）

A1 = 漂移归因锚点：①**证据先于裁决**（先实跑两条用例留存行号输出全文 · banned/violations 逐路径 `git log` 溯源 · 无证据不裁决）；②**二值归因**（锚点真漂移→修锚点 / whitelist 过期→刷新基线 · 逐文件证据 · 禁混合口径）；③**闸语义不破**（四态/banned 前置 O2/回归牙原样保留或经签认等价改写 · 禁删闸/豁免 banned 强转绿）。红线继承：实现零 diff · SSE/freeze 零 diff · 改码面收敛（只动测试基建）。

## 闸表（全部 pending）

| 闸 | blocks | 说明 |
|----|--------|------|
| HG-TASK-DRAFT | 20-R1, 30 | 初稿未经 20-task-audit 审查与维护者签收 |
| HG-AUDIT-R1 | 30 | 20-task-audit R1 审查文未落盘 |
| HG-GRAPH-MODULES | 30 | `none` 口径待签（纯测试基建面 · 承 ops-write-catalog-reconcile 先例；30 实扫出图谱面须回签） |
| HG-DIFF-WHITELIST-DIAGNOSIS | 30 | **设计闸 · 诊断裁决**：锚点真漂移→修锚点 / whitelist 过期→刷新基线（二选一 · 证据先行——10 档实测证据已备 · 形态倾向与最终裁决随签认落闸表行） |

## 自检

| 命令 | 结果 |
|------|------|
| `.venv/bin/python -m pytest tests/test_lg_rag_write_replay_guard.py::test_tc8_diff_whitelist tests/test_strategy_scenario.py::test_diff_whitelist_scenario_stage_rewire`（取证 · 只读） | **2 failed**（预期红 · 修复前基线证据 · 输出全文见上） |
| `npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_diff_whitelist_anchor_drift.md` | **PASS**（2026-11-06 · 零 warn） |
| `npx --yes spec-wave@3.5.0 task lint-wiki-delta --target .` | **PASS**（scope all · 本档 wiki_delta 预填） |

## 禁区复核

- 未改 `app/` / `alembic/` / `scripts/` / `tests/`（仅 `docs/tasks/active/` + `docs/harness/invokes/` + 本 invoke；两枚闸用例只跑取证不改一行）。
- 未签任何 human_gate（四闸 pending 待维护者/lead 签收；诊断裁决留 HG-DIFF-WHITELIST-DIAGNOSIS 随档裁决）。
- 10 档取证只读（pytest 单跑 / git log / rev-parse / grep · 零仓内状态变更 · untracked 空集）。
