# invoke · 30 实现 · ops-write-catalog-reconcile（2026-11-06）

| 项 | 值 |
|----|----|
| hat | `30`（实现 · 承 issue #336 维护者 30 授权令） |
| task_slug | `ops-write-catalog-reconcile` |
| task 文件 | `docs/tasks/active/task_ops_write_catalog_reconcile.md` |
| 分支 | `fix/ops-write-catalog-reconcile`（base `origin/master` `fd0fbbe` = PR #354 squash 合入点） |
| 指令来源 | issue #336 维护者 comment [`6680378035`](https://github.com/Cyning12/ops-desk-api/issues/336#issuecomment-6680378035)（2026-11-06 16:13）：30 前置齐备（PR #354 合并 · 四闸 approved · 设计闸裁决=**案③两者**）· 六交付条件 · 依据 2026-11-06 13:40 授权 |
| 30 交付面 | `tests/test_ops_write_catalog_reconcile.py`（新增 · 19 枚）+ task 档（闸表签认回填 + 30 自检结论 + 修订记录）· **app/ 零 diff** |

## 六条件逐条对照

| # | 条件 | 结果 | 证据 |
|---|------|------|------|
| 1 | 红测先行：两族对账测试先红后绿，构造漂移即红实证留 invoke | ✅ | 漂移矩阵 10/10 被拦实证（见下「红证据」）· args 负样本 3/3 fail-closed 实证 · 对账实扫**真发现 2 枚声明↔行为漂移**（偏差①② · 见下专节） |
| 2 | 旧测影响面 grep 实扫如实登记（零适配也写明）· 适配禁放宽 | ✅ | grep 实扫：引用 run_note 的既有测试族 4 文件（stage-w / planner-args / worker-state + manifest 族）· **零既有测试触碰**（git diff 实证）· 关联回归 **114 passed**（stage-w 16 + manifest/testing-write/approval-gate/idempotency/reversibility 101 − 重叠 + planner-args/worker-state 13）· 零放宽零适配如实登记 |
| 3 | 改码面=纯测试面：app/ 一行不动 | ✅ | `git diff origin/master...HEAD --name-only \| grep -v '^docs/'` = 空集 · 唯一非 docs 文件 = 新增测试 |
| 4 | 红线零 diff（SSE 事件表零 diff / fail-closed 不放宽 / resume 单路径不涉）随 PR 对拍留证 | ✅ | app/ 零 diff ⇒ SSE 事件表/闸链/消费门零触碰 · 既有断言零删零松（diff 实证）· resume 单路径本 task 不涉（task 档非范围） |
| 5 | 机检绿：ruff + pytest + graph-compile + CI 4/4 | ✅ | ruff All checks passed!（I001 自修 1 枚）· 全量 **2102 passed · 4 failed = master 基线同 4 红**（独立复证：worktree @ `fd0fbbe` 同 4 红逐字复现 · diff-whitelist ×2 + env 依赖 ×2 · stage-w 40 档登记口径一致）· graph-compile EXIT=0 · CI 待跑（出货后补登） |
| 6 | PR 逐条对照验收 · 30 invoke 落档 | ✅ | 本 invoke 即档 · PR 描述六条件对照表 |

## 交付内容（案③两者 × A1 双口径）

**族① 一致性机检（13 枚 · CI 常驻 · 双向漂移秒红）**：
- A1 声明基准 ↔ `ops.write.v1.yaml` 真文件 ↔ 加载后 `CapabilitySpec`/adapter 全字段对账（`_reconcile_loaded_spec` · 22 项字段含 args_schema 子键/output_fields/snapshot_fields/adapter 函数身份）
- raw YAML ↔ loader 映射无损回环（解析面 ↔ 注册面）
- 三层显式打开判据对账（默认加载面排除 + builtin 五枚基线 · 放行谓词 tag 声明）
- 可见性闸 ↔ 声明对账（未放行不可见 / 放行 run_note 可见 / testing tag 不解锁）
- **漂移矩阵 10 例**（参数化）：每枚漂移须被 loader（V1 幂等键/V2 hitl/V8 side_effect/adapter 解析）或 A1 对账断言拦下

**族② 端到端实跑（6 枚 · 真闸链驱动 · 补「声明有·行为无」行为层实证）**：
- 声明→行为逐条映射全链：闸拦（hitl.required）→ pending（snapshot_fields 快照对账）→ 图挂起 → decide(approved) → resume 单路径 → 消费命中 → 真落笔 → **输出契约双向对账** → audit 串链四处同单 → 幂等重放
- args_schema 行为层负样本 3 例（缺必填/多送键/类型错 → `args_schema_invalid` fail-closed · 零落笔 · 放行面俱在照样拦）
- 无审批零落笔 fail-closed 常驻扎钉

## 红证据（构造漂移即红 · 先红后绿）

漂移矩阵脚本实跑输出（30 自检亲跑 · 2026-11-06）：

```
[RED] idempotency_key 声明位被删 → ManifestError: capabilities[0] V1: side_effect=write 必须有 idempotency_key
[RED] hitl.required 漂移为 false → ManifestError: capabilities[0] V2: side_effect=write 必须 hitl.required: true
[RED] risk_level 漂移为 high → 对账断言红
[RED] 独立写 tag run_note 丢失 → 对账断言红
[RED] adapter 目标函数漂移为不存在函数 → ManifestError: capabilities[0] adapter 属性不可调用或不存在: no_such_fn
[RED] args_schema 缺必填 request_id（幂等键源裸奔） → 对账断言红
[RED] args_schema additionalProperties 放宽 → 对账断言红
[RED] output_fields 丢 written（结果契约漂移） → 对账断言红
[RED] hitl snapshot_fields 丢 note（审批快照漂移） → 对账断言红
[RED] side_effect 漂移为 read（写闸逃逸） → ManifestError: capabilities[0] V8: side_effect=read 不应声明 idempotency_key
```

args_schema 负样本 fail-closed 实跑输出：

```
[fail-closed] 缺 request_id → ok=False error=args_schema_invalid: 缺必填字段: request_id meta=True
[fail-closed] 多送键 → ok=False error=args_schema_invalid: 禁止额外字段: ['extra'] meta=True
[fail-closed] 类型错 → ok=False error=args_schema_invalid: 字段 run_id 期望 type=['string']，实际=int meta=True
```

## 对账实扫发现：声明↔行为漂移 2 枚（偏差登记 · A1 双向漂移实证）

1. **偏差①（行为有·声明无）**：成功路径 adapter 出键 `receipt`（抓取载荷 `{"note_id","run_id","tenant_id"}`，`defaults.py:217`），未在 manifest `output_fields` 声明。
2. **偏差②（声明有·行为无）**：`duplicate_of` 为**重放路径条件出键**——成功路径永不出键（仅 duplicated=False 伴随），声明未标注路径条件。

处置：两偏差在测试内**精确钉死**（成功路径键集 = 声明 − {duplicate_of} ∪ {receipt} 且 receipt 载荷逐值对账；重放路径键 ⊆ 声明且含 duplicate_of 不含 note_id）· 声明面对齐（manifest `output_fields` 增补 receipt / 标注 duplicate_of 路径条件）**建议另案裁决**——本 task 改码面禁动实现（FP-4）与基准（FP-9）。这正是 #336 题面「能力声明↔实际行为对账」缺口的实证价值。

## 终态工程面

| 项 | 结果 |
|----|------|
| 新测 | `pytest tests/test_ops_write_catalog_reconcile.py -q` → **19 passed** |
| 关联回归 | 8 文件 **114 passed**（见条件 2） |
| 全量 | **2102 passed · 4 failed（master 基线同 4 红 · worktree `fd0fbbe` 独立复证）· 2 skipped** · 零新增红 |
| ruff | `ruff check app tests` → All checks passed! |
| graph-compile | EXIT=0 |
| task lint / lint-wiki-delta | 双 PASS |
| app/ diff | **零**（纯测试面 · #336 红线） |
| 环境注记 | venv 补装 pytest-asyncio（pyproject 已声明）· 真 PG opsdesk_test 本地可达（DB 用例真跑非 skip）· CI pytest workflow 无 postgres service 的 skip 绿缺口为既有已知（test-baseline-reds F4 登记 · 非本 task 范围） |

## 禁区复核

- 未改 `app/` / `alembic/` / 既有 `tests/`（git diff 实证 · 唯一新增 = 对账测试文件）。
- 未签任何 human_gate（四闸由 lead 签认 · PR #354 review `5797443083` · 本档闸表如实回填）。
- A1 锚点语义未改义（task 档专节仍为唯一真源 · 偏差①②为对账**发现**非语义变更）。
- manifest `ops.write.v1.yaml` 本体零改动（对账基准只读 · FP-9）。
