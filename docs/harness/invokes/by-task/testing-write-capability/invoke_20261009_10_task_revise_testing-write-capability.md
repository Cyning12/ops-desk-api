# 10-task invoke · testing-write-capability（修订 · 承接 30 GATE_STOP · R2 裁定四=乙落盘）

> **帽**：10-task · **task**：docs/tasks/active/task_testing_write_capability.md  
> **分支**：task/testing-write-capability（worktree d2-testing-write-capability）  
> **日期**：2026-10-09 · **性质**：修订（非新起草）· 承接 30 GATE_STOP invoke（invoke_20261009_30_implement_testing-write-capability.md）与维护者裁定四（2026-10-09 · 选项乙）

---

## 触发

30 实证：task 钉死契约字段组合 `side_effect: write` + `kind: local_fn` 被 loader 不变量夹击不可加载——

- **V1**（manifest.py:826-830）：write 必须 `http_block.idempotency_key`；spec.http 对 local_fn 恒 None → 必触发 ManifestError（探针复现留证于 30 invoke）。
- **V2**（manifest.py:832-836）：write 必须 `hitl.required: true`。
- **V7**（manifest.py:533-540）：仅 kind=http 可声明 http 块 → local_fn 无法用 http 块满足 V1。

全仓既有写能力测试全走 kind=http 路径，无 local_fn write 先例。30 按「不得静默改义」STOP（零 diff）。

## 维护者裁定（2026-10-09 · 裁定四 = 乙）

**manifest 增顶层 `idempotency_key` 字段供 local_fn write 声明**（不改判序语义 · 甲/丙否决）。本帽已把裁定全文落进 task R2 裁定四，含：

- **字段语义**：顶层 `idempotency_key`（非 http 块）供 local_fn write 声明幂等键；http 能力仍走 `http.idempotency_key` 不变；缺省 None。
- **loader 校验改动点**：V1 放宽为「http 块键 **或** 顶层键」二选一（任一非空即满足）· **仅 write 强制** · read 不受影响；V8 对称适配（read 误声明顶层键同样 ManifestError）；V2/V7 不动。
- **波及面**：manifest.py 校验（解析 + CapabilitySpec 承载 + V1 放宽 + V8 适配）+ schema 字段族文档 + loader 校验单测（A8）+ `docs/_tech_graph/l1/01_modules.md` 图谱同步（仍 l1）。
- **岔路裁决**：甲否（摘掉 local_fn 的幂等键护栏 · 缩小安全校验语义）· 乙采纳（不变量全 kind 保持 · 缺省 None 后向兼容）· 丙否（违反语义 mock 零 IO）· 丁否（破 off 零 diff）。

## 修订清单落盘对照（八项全落）

| # | 项 | 落盘位置 |
|---|----|----------|
| 1 | R2 增裁定四 + 控制表同步 | task「### R2 · 方案裁定（四裁定）」裁定四段 · 思考轮控制表 R2/R5 行 |
| 2 | 钉死契约补 hitl.required: true + 顶层 idempotency_key | task 钉死契约「capability 字段钉死」行 |
| 3 | 范围增 loader V1 放宽 + 适配/测试 | 范围 F7 · F4 引用扩 A8 |
| 4 | failure_paths 增「loader V1/V2 拦截」行 | failure_paths 表第 10 行（30 实证案例） |
| 5 | 验收同步：A6 更新 + 新增 A8 | 验收标准 A6（增 hitl/顶层键两字段）· A8（无键仍 ManifestError / 有顶层键可加载 / read 零 diff / read 误声明 V8 拦） |
| 6 | off 零 diff 论证补强 | 钉死契约「off 零 diff」行 + R3 小节（顶层键缺省 None → 存量 manifest 校验行为逐字节不变） |
| 7 | 闸表回退 | HG-TASK-DRAFT → pending · HG-AUDIT-R1 → pending（待 20 R2 + 维护者重签）· HG-GRAPH-MODULES 维持 approved 在册 + 备注补「裁定四扩大 schema 面 · 仍在 l1 · 30 同步 01_modules.md 义务不变」 |
| 8 | 20 R1 O1/O2/O4 勘正 | 锚点表 builtin.v1.yaml:7-29 → :8-26（O1）· builder.py:28 → strategy/builder.py:28 + 第四调用点 evals/agent/golden/capability/runner.py:120（O2）· 控制表 R4「八条」→「十条」+ R4 小节勘正注记（O4） |

另同步：状态行 / orchestration（30 GATE_STOP → 10 修订 → 20 R2 → 重签 → 30）/ graph_delta 行（+顶层字段+loader 放宽）/ 依赖表（+30 GATE_STOP invoke）/ 修订表。

## 机械闸复跑

- `npx spec-wave task lint --file docs/tasks/active/task_testing_write_capability.md` → **LINT: PASS · EXIT=0**
- `npx spec-wave verify --target . --task docs/tasks/active/task_testing_write_capability.md` → **VERIFY: BLOCKED · EXIT=2**（HG-TASK-DRAFT / HG-AUDIT-R1 pending 拒 30 · 闸回退后的属实时序 · 非回归）

## 本帽边界

- 未动任何 `app/` / `tests/` 实现码（10-task 不实现）。
- 未代签任何 human_gate；闸回退为状态如实登记（内容实质变更 · R1 审查文未覆盖 loader 冲突），重签权属维护者。
- 30 GATE_STOP invoke 按维护者令先行 commit 保留历史。

## 留转

1. **20-task-audit R2 复审要点**：裁定四 loader V1 放宽语义（二选一 · 仅 write 强制 · read 零 diff 论证）· V8 对称适配 · F7 波及面闭合 · A8 可机断性 · 钉死契约新增两字段与 loader 实证一致性（manifest.py:826-836 / :533-540）。
2. 维护者重签 HG-TASK-DRAFT / HG-AUDIT-R1 后重新下发 30。
3. 30 实现时 F7 与 F1–F6 一并交付，图谱 01_modules.md 同步义务不变（HG-GRAPH-MODULES 在册备注）。
