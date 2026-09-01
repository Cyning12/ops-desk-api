# Task：Host C1 · harness CLI Capability（verify / task_lint）

> **状态**：active  
> **类型**：Capability / Host 沟通轨实现  
> **上游**：[`06_host_comms_boundary_spec_v0.md`](../../spec/agent-infra/06_host_comms_boundary_spec_v0.md)（**signed** · #111）§7/§8/§10 · [`02_agent_host_plan_v0.md`](../../spec/agent-infra/02_agent_host_plan_v0.md)（H2 ✓ CLOSE）  
> **前置**：C0 CLOSE · [`task_host_comms_boundary_spec`](../done/task_host_comms_boundary_spec.md) · [#111](https://github.com/Cyning12/ops-desk-api/pull/111)  
> **分支**：`task/host-harness-cli-capability`  
> **帽子**：00 起草闸；**10** 补全；**20** 审；**30+40** 实现。  
> **无关**：C2 Prompt Pack · C3 写盘 · C4 UI · 产品 lg-rag/Chat 行为 · 通用 shell Capability · Policy 默认开

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `host-harness-cli-capability` |
| **git_branch** | `task/host-harness-cli-capability` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | mock subprocess（monkeypatch `asyncio.create_subprocess_exec`）+ fixture JSON；Policy 关 → `policy_blocked` 断言；env 缺失 → 不可用错误断言；**CI/本地不真跑 npx、不装 npm、不断网** |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md`（capability 行备注）· capability flow（若存在则备注） |
| **graph_delta_note** | `capability` 一级模块已存在（H2）；仅备注 `harness.*` 三条白名单 Capability；**不新增一级模块**；若增 `implementedBy` → 同步 G-L2 indexes |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 行为真值在 SPEC 06 §7/§8 + 本 task；不晋升 coding_wiki |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,00,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | `n/a`（不改 lg-rag-sse-v1；Capability 入出参 JSON 契约由本 task 30 自检记录 · SPEC 06 §16 不预冻） |
| **close_pr_policy** | `required` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | C 轨串行：C0 ✓ → **C1** → C2 → C3；C4 跨仓 web 可后与 C3 尾并行 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-09-01 · **00 代签 · 维护者 Prompt 授权** |
| HG-AUDIT-R1 | pending | 30 | 待 **20-task-audit** R1 落盘后 00 代签 |
| HG-GRAPH-MODULES | approved | — | 不新增一级模块（capability 已存在）· **00 代签** · 仅备注/flow |

---

## 00 定夺（草案 · 人可后签）

| 项 | 钉死 |
|---|---|
| **slug** | **`host-harness-cli-capability`** |
| **Capability 全集** | `harness.verify`（必做）· `harness.task_lint`（必做 · 含 `task lint` 与 `lint-wiki-delta` 两子操作）· `harness.status`（**可选**；做则 C4 受益，不做则 C4 开工时补） |
| **落点** | 新模块 `app/ops/capability/harness_cli.py`（专用白名单 adapter · **不复用** mock-only `adapters/cli.py`）；注册走**代码路径**（`gateway.register`，如 defaults ensure 追加）——现网 `manifest.py` 仅支持 `kind=local_fn` 且 adapter 前缀白名单仅 defaults/lookups，**builtin.v1.yaml 不适用**于 subprocess cli adapter；**不进**业务默认探针路径 |
| **命令向量** | 钉死形态 `npx --yes dsh-coding-kit@<pin> verify --target . --task <path> --json` / `task lint --file <path>` / `task lint-wiki-delta --target .`；`asyncio.create_subprocess_exec` **禁 shell=True**；参数白名单校验（`task_path` 须在 `docs/tasks/` 内 · 拒绝对路径/..逃逸/shell 元字符） |
| **kit 版本** | env `DSH_CODING_KIT_VERSION` 钉版（如 `1.10.0`）；**缺失 → Capability 返回不可用错误**（SPEC 06 §7：非静默漂版） |
| **Policy** | `risk_level=high` · **默认关** → `policy_blocked`；开启走现有 Host 策略通道（env / `ctx._host_policy`）；**禁止**本波把默认改开 |
| **超时/截断** | subprocess 超时（≤180s）+ stdout/stderr 截断上限；超时 → `cli_failed: timeout` 类错误 |
| **返回** | `CapabilityResult(ok, output=parsed_json, error=policy_blocked\|cli_failed\|capability_unavailable)` 语义对齐 H2 types（types.py 字段名 **`output`**，无 `data`） |
| **通用 shell** | **永久禁止**（SPEC 06 §3 禁令 A）；本波只做三条白名单 |
| **模块** | 不新增一级模块 |

---

## 范围

1. `harness.verify` / `harness.task_lint` 两条 Capability 实现 + 注册（`harness.status` 可选）  
2. env `DSH_CODING_KIT_VERSION` 钉版读取与缺失报错路径  
3. Policy 默认关接线（`policy_blocked`）+ Host 策略通道开启路径  
4. api 单测（mock subprocess + fixture JSON；policy_blocked / 不可用 / 成功解析 / 超时 / 参数逃逸拒绝）  
5. 文档/图谱：capability 行备注；若增 `implementedBy` → G-L2 indexes  
6. ruff + pytest + graph-compile

## 非范围

- **C2** Prompt Pack · **C3** 受控写盘 · **C4** `/obs` UI（各自另 task）  
- 通用 shell / 可传任意命令的 npx 封装（**永久禁令**）  
- Policy 默认开 · 把 `harness.*` 接进产品 lg-rag/Chat 主路径  
- 真跑 npx 的测试进 CI / 本地默认路径（仅 mock）  
- 改 `adapters/cli.py` mock-only 语义  
- comms session / PromptAssembly 接线（C2）

---

## 验收标准

- [ ] `harness.verify`：mock subprocess 下解析 fixture `--json` 输出 → `CapabilityResult.output` 正确透传（断言关键字段）  
- [ ] `harness.task_lint`：`task lint` 与 `lint-wiki-delta` 两子操作 mock 断言  
- [ ] Policy 默认关 → `policy_blocked`；Host 策略通道开 → 放行（mock 断言两种路径）  
- [ ] env `DSH_CODING_KIT_VERSION` 缺失 → `capability_unavailable` 类错误（非静默跑漂版）  
- [ ] 参数白名单：`task_path` 逃逸（`../` · 绝对路径 · shell 元字符）→ 拒绝（断言）  
- [ ] 超时 → 错误返回不挂起（mock 模拟）  
- [ ] 命令向量硬编码 `npx --yes dsh-coding-kit@<env pin>`；无 shell=True（grep 断言或代码审查条）  
- [ ] `harness.status` 若做：mock 断言；若不做：非范围注明（C4 开工时补）  
- [ ] `01_modules.md` capability 行备注；若增 `implementedBy` → G-L2 `by_path`/`by_symbol` 同步  
- [ ] `ruff check` 触及路径绿；`pytest` 相关绿（含 capability 旧测零破坏）；`./scripts/graph-compile.sh` exit 0  
- [ ] 注册机制：`gateway.register` 后 `list_capabilities` 可见（`enabled=True`）；单测 `clear()` 隔离防重复 id ValueError  
- [ ] Policy 门先于 adapter：默认关时 adapter `invoke` **零调用**（mock 计数断言）；若 adapter `kind="cli"`（建议）：开启须 `allow_high_risk` **且** `allow_cli` 双键（env `OPS_CAPABILITY_ALLOW_HIGH_RISK` / `OPS_CAPABILITY_ALLOW_CLI` 或 `ctx._host_policy` 对应键；check_invoke 先查 high_risk 再查 cli）  
- [ ] `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` 通过

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| Policy 默认关 | `policy_blocked` 错误 | 开策略后重试 | capability 错误 |
| env 未钉 | `capability_unavailable`（不静默漂版） | 设 env 后重试 | capability 错误 |
| npx 非零退出 / JSON 解析失败 | `cli_failed` + 截断 stderr | 是 | capability 错误 |
| subprocess 超时 | `cli_failed: timeout` | 是 | capability 错误 |
| task_path 逃逸 | 参数校验拒绝（不执行） | 否 | 校验错误 |

---

## 给执行帽的必读列表

1. 本 task（含 **00 定夺**）  
2. `docs/spec/agent-infra/06_host_comms_boundary_spec_v0.md` §3 · §7 · §8（signed）  
3. 只读参考：`app/ops/capability/registry.py` · `policy.py` · `types.py` · `gateway.py` · `defaults.py` · `manifest.py` · `adapters/cli.py`（mock-only · 勿复用）  
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`  
5. `docs/_tech_graph/l1/01_modules.md`（capability 行）

---

---

### 自检结论

> **10-task** · 2026-09-01 · 分支 `task/host-harness-cli-capability` · docs-only 本帽（不改 `app/` / `tests/`）· HG-AUDIT-R1 保持 **pending**（本帽不签发）

**现网事实核对**（只读 `app/ops/capability/` · 结论：2 处字段/机制不符已修正 · 其余一致）

| 核对项 | 现网事实 | 结果 |
|---|---|---|
| `CapabilityResult` 字段 | types.py L33–41：`ok / output / error / capability_id / duration_ms / meta` · **无 `data`** | ⚠️ 00 定夺「返回」与验收钩原写 `data` → **已改 `output`** |
| `PolicyDecision` 字段 | policy.py L30–35：`allowed: bool · reason: str\|None`（如 `policy_blocked: high_risk`） | ✅ task `policy_blocked` 语义一致 |
| `_host_policy` 通道 | policy.py L42–46：读 `ctx["_host_policy"]` dict；键 `allow_high_risk/allow_sandbox/allow_cli`；env `OPS_CAPABILITY_ALLOW_HIGH_RISK/_SANDBOX/_CLI` | ✅ task L55 陈述准确 |
| Policy 检查次序 | check_invoke：risk=high 先查 `allow_high_risk` → kind=cli 再查 `allow_cli` | ✅ 已补双键验收钩（事实补充） |
| 注册机制 | registry 拒绝重复 id 覆盖（ValueError）；manifest.py **仅 `kind=local_fn`** · adapter 前缀白名单仅 defaults/lookups；`ensure_default_capabilities` 优先 builtin YAML | ⚠️ 00 定夺「注册进 defaults/manifest」对 cli adapter 不成立 → **已改：注册走代码路径 `gateway.register`，builtin.v1.yaml 不适用** |
| builtin.v1.yaml 格式 | id/kind/description/tags/risk_level/enabled/adapter（5 枚 local_fn） | ✅ 已核，本波不动该文件 |
| `adapters/cli.py` | MockCliAdapter · mock-only · 零子进程 | ✅ 00 定夺「不复用」与现网一致 |

**00 定夺范围实质**：**零改动**（slug / 全集 verify+task_lint 必做、status 可选 / 命令向量硬编码禁 shell=True / 参数白名单 / env 钉 `DSH_CODING_KIT_VERSION` / Policy 默认关 / 禁通用 shell / 不新增一级模块 —— 全部保留）；仅修正字段名与注册机制表述，新增 2 条验收钩（注册可见性 · Policy 门先于 adapter/双键）。

**lint 与禁区**

- [x] `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_host_harness_cli_capability.md` → **PASS**（exit 0 · **W4 合法**：无思考轮节 · 思考轮由 SPEC 06 §15「思考轮控制（10-spec 回填）」承载，本 task 为 SPEC 落地执行波）
- [x] `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` → **PASS**
- [x] `app/` · `tests/` 零改动；人工闸状态未改（HG-AUDIT-R1 仍 pending · HG-GRAPH-MODULES approved 未动）
- [x] invoke 落盘：`docs/harness/invokes/by-task/host-harness-cli-capability/invoke_20260901_10_task_host-harness-cli-capability.md`（hat_id=10-task）
- 下一棒：**20-task-audit** R1 落盘 → 00 代签 HG-AUDIT-R1 → 30 开工

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-01 | **00**：C0 CLOSE（#111/#112）后起草 C1；钉 slug=`host-harness-cli-capability`；全集=verify+task_lint 必做 / status 可选；命令向量硬编码 · 禁 shell=True · 参数白名单；env 钉 `DSH_CODING_KIT_VERSION` 缺失即不可用；Policy 默认关 |
| 2026-09-01 | **10-task**：现网核对修正 2 处（`CapabilityResult.data`→`output`；manifest 仅 local_fn → 注册走代码路径 `gateway.register` · builtin.v1.yaml 不适用）；补验收钩 2 条（注册可见性 · Policy 门先于 adapter / cli+high 双键）；补 `### 自检结论`（W4 合法：思考轮由 SPEC 06 §15 承载）；invoke 落盘；00 定夺实质零改 · HG-AUDIT-R1 保持 pending · 下一棒 20-task-audit |
