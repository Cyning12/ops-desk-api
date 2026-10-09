# 30 invoke · testing-write-capability（GATE_STOP · 钉死契约与 loader 强校验冲突 · 未改码）

> **帽**：30-implement · **task**：docs/tasks/active/task_testing_write_capability.md  
> **分支**：task/testing-write-capability（worktree d2-testing-write-capability）  
> **日期**：2026-10-09 · **结论**：**STOP（零 diff）**——钉死契约字段组合（side_effect: write + kind: local_fn）在 manifest 加载期被 V1/V2 强校验拦截，契约不可按字面实现；须退回 10-task 补裁（R2 第四裁定）

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved | Y | Y | — |
| HG-AUDIT-R1 | approved | approved | Y | Y | ✅ |
| HG-GRAPH-MODULES | approved | approved | Y | — | ✅ |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | Y | N | — |

reviews：task_testing_write_capability_audit_R1_20261009.md 存在且 R1 PASS？ **是**  
pre-30 invoke：required ∩ {10,20,00} 齐全（verify 硬闸）？ **是**  
机械辅助：`npx spec-wave verify --target . --task docs/tasks/active/task_testing_write_capability.md` → **VERIFY: PASS · EXIT=0**

闸面可开工；但读码后发现**内容级阻塞**（非闸阻塞），按「30 不得静默改义」STOP。

---

## 阻塞实证（机断可复现）

### 冲突点

task 钉死契约 :79 / A6 :147 钉死 manifest 条目：`side_effect: write` + `kind: local_fn`（字段族对齐 builtin.v1.yaml 范式）。

但 `app/ops/capability/manifest.py` `_validate_invariants` 对**所有 kind** 的写能力施加两条加载期强校验：

- **V1（manifest.py:826-830）**：`is_write and not http_block.get("idempotency_key")` → ManifestError「必须有 idempotency_key」。`spec.http` 对 local_fn 恒为 None → http_block={} → **必触发**。
- **V2（manifest.py:832-836）**：`is_write and not spec.hitl_required` → ManifestError「必须 hitl.required: true」。
- **V7（:533-540 / :864-868）**：仅 kind=http 可声明 http 块 → local_fn **无法**用 http 块满足 V1。

推论：`side_effect ∈ {write, irreversible}` + `kind: local_fn` 的 manifest 条目**永不可加载**（V1 必拦）。全仓既有写能力测试（test_capability_manifest_http.py:131 / test_capability_http_adapter.py 等）全部走 kind=http 路径，无 local_fn write 先例——实证支持该推论。

### 复现（本帽实跑留证）

```bash
PYTHONPATH=. uv run python /tmp/probe_v1.py
# 输出：
# ManifestError: capabilities[0] V1: side_effect=write 必须有 idempotency_key
```

探针 manifest 即按 task :79 钉死字段书写（side_effect: write · kind: local_fn · risk_level: medium · tags:[testing,mock,write] · enabled:true · tenant_scoped:false · 可撤销性四字段齐 · adapter 指 defaults 罐头 · hitl.required: true），仍被 V1 拦截。

### 为什么 30 不能自行绕过

| 候选绕法 | 否决理由 |
|---|---|
| manifest 加 http 块满足 V1 | V7 禁止（仅 kind=http） |
| 改 V1 收窄到 kind=http | 改 loader 判定语义，task 非范围未授权；V1 设计意图覆盖所有 kind（「写操作必须有幂等键」），30 无权静默改义 |
| 不经 manifest loader 注册（defaults.py 直接 register） | 违反钉死契约「仅经 OPS_CAPABILITY_EXTRA_MANIFESTS 显式加载」+ R2 裁定一 |
| side_effect 改非 write | 违反钉死契约（write 是触发 auto_approve_ok 条件②的唯一挂钩点） |
| hitl.required: true | 可满足 V2 但救不了 V1 |

---

## 处置建议（退回 10-task 补 R2 裁定四 · 供维护者裁定 · 30 不预选）

| 选项 | 内容 | 代价 |
|---|---|---|
| 甲 | task 补裁：V1 收窄为 kind=http 专属（local_fn 进程内适配器直接拿 ctx，无「重复提交多张单据」传输面），写进 task 范围 + failure_paths | loader 一行改动 + 单测；语义改动需 20 复审 |
| 乙 | manifest 增顶层 `idempotency_key` 字段（非 http 块）供 local_fn write 声明，V1 改读该字段 | loader + 字段族改动面更大 |
| 丙 | 测试 capability 改走 kind=http 假端点 | 违反「语义 mock 零 IO」精神与 adapter 钉死，不建议 |
| 丁 | 放弃 manifest 路径，特例注册 | 破 off 零 diff 纪律，不建议 |

另注：无论选哪项，`hitl.required: true` 都需补进 task :79 字段钉死清单（V2 强制，且与「该 capability 就是用来触发 HITL」语义自洽）。

---

## 本帽已做 / 未做

- 已做：必读 4 件全读（task / R1 审查 / CODING_BACKEND_L2 已在任务链中 · GATE_VERIFY fragment）；verify EXIT=0；锚点实读（manifest.py 全文 · types.py · registry.py · baseline.py · defaults.py · builtin.v1.yaml · conftest.py:29 · hitl/router.py）；阻塞实证探针（已删 /tmp/probe_v1.py）；uv.lock 探针副作用已 `git checkout` 还原；工作树 **git status CLEAN**。
- 未做（STOP 纪律）：未改任何 app/ 或 tests/ 文件；未写 testing.v1.yaml；未跑 pytest 全量（无 diff 可验）；未动图谱（HG-GRAPH-MODULES「在册」附带义务随实现一并交付，实现未发生故无图谱增量）；未 commit。

## 留转清单

1. **退回 10-task**：R2 补裁定四（V1 与 local_fn write 的冲突消解路径）+ :79 补 hitl.required: true + failure_paths 增「loader V1/V2 拦截」行；20 复审后重签 HG-AUDIT-R1（内容实质变更，R1 审查文未覆盖本冲突）。
2. 维护者重新签闸后重新下发 30。
3. 本 invoke 未 commit（保持工作树净），由 00/维护者决定是否随 task 修订一并落盘。
