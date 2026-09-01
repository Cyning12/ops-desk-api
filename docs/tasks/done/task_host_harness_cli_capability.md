# Task：Host C1 · harness CLI Capability（verify / task_lint）

> **状态**：completed（2026-09-01 CLOSE · PR [#114](https://github.com/Cyning12/ops-desk-api/pull/114) MERGED）  
> **类型**：Capability / Host 沟通轨实现  
> **上游**：[`06_host_comms_boundary_spec_v0.md`](../../spec/agent-infra/06_host_comms_boundary_spec_v0.md)（**signed** · #111）§7/§8/§10 · [`02_agent_host_plan_v0.md`](../../spec/agent-infra/02_agent_host_plan_v0.md)（H2 ✓ CLOSE）  
> **前置**：C0 CLOSE · [`task_host_comms_boundary_spec`](./task_host_comms_boundary_spec.md) · [#111](https://github.com/Cyning12/ops-desk-api/pull/111)  
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
| **related_pr** | `#114` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | C 轨串行：C0 ✓ → **C1** → C2 → C3；C4 跨仓 web 可后与 C3 尾并行 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-09-01 · **00 代签 · 维护者 Prompt 授权** |
| HG-AUDIT-R1 | approved | 30 | 2026-09-01 · **00 代签 · 维护者 Prompt 授权** · 见 `docs/harness/reviews/task_host_harness_cli_capability_audit_R1_20260901.md`（R1 pass · 内容零阻塞） |
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

- [x] `harness.verify`：mock subprocess 下解析 fixture `--json` 输出 → `CapabilityResult.output` 正确透传（`test_verify_success_json_passthrough_via_ctx` 断言 output==fixture 及关键字段）  
- [x] `harness.task_lint`：`task lint` 与 `lint-wiki-delta` 两子操作 mock 断言（`test_task_lint_success_via_env_open` / `test_lint_wiki_delta_success`）  
- [x] Policy 默认关 → `policy_blocked`；Host 策略通道开 → 放行（ctx `_host_policy` 与 env `OPS_CAPABILITY_ALLOW_*` 双通道均测）  
- [x] env `DSH_CODING_KIT_VERSION` 缺失 → `capability_unavailable` 类错误（含非法 pin 值用例；零子进程调用）  
- [x] 参数白名单：`task_path` 逃逸（`../` · 绝对路径 · shell 元字符 · 反斜杠 · 空格 · 出 `docs/tasks/` 前缀）→ `invalid_args` 拒绝且不执行（13 参数化用例）  
- [x] 超时 → `cli_failed: timeout` 错误返回不挂起（adapter 直测 + gateway 路径；proc.kill 断言）  
- [x] 命令向量硬编码 `npx --yes dsh-coding-kit@<env pin>`（argv 逐元素断言）；无 shell=True（`test_no_shell_mode_in_source` grep 断言 + kwargs 无 shell 键断言）  
- [x] `harness.status`：**不做 · C4 开工时补**（SPEC 06 §7 可选；自检结论显式注明）  
- [x] `01_modules.md` capability 行备注 + 人签记录行 + `10_flow_capability` 描述备注；**未增 `implementedBy`** → G-L2 `by_path`/`by_symbol` 无需同步  
- [x] `ruff check` 触及路径绿（全量 `app tests` 亦绿）；`pytest` CI 等价 496 passed 39 skipped（capability 旧测 57 passed 零破坏）；`./scripts/graph-compile.sh` exit 0  
- [x] 注册机制：`register_harness_cli_capabilities()` 走 `gateway.register` 后 `list_capabilities` 可见（`enabled=True`）；幂等重复注册返回空不 ValueError；测试 `clear()` 隔离  
- [x] Policy 门先于 adapter：默认关时 subprocess **零调用**（mock 计数断言）；adapter `kind="cli"` 字面钉死（断言）；开启须 `allow_high_risk` **且** `allow_cli` 双键（单键各测均 blocked）  
- [x] `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` 通过（exit 0 · PASS）

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

### 自检结论（执行者）

> **30+40** · 2026-09-01 · 分支 `task/host-harness-cli-capability` · 三闸 approved（开工前 GATE_VERIFY + 收尾复跑 verify 均 PASS）

**自检命令（逐条退出码 · 全绿）**

| 命令 | 退出码 | 结果 |
|---|---|---|
| `npx dsh-coding-kit@1.10.0 verify --target . --task docs/tasks/active/task_host_harness_cli_capability.md` | 0 | **VERIFY: PASS**（开工前 + 收尾复跑） |
| `.venv/bin/ruff check app/ops/capability/harness_cli.py tests/test_capability_harness_cli.py`（+ 全量 `ruff check app tests`） | 0 | All checks passed |
| `DATABASE_URL=postgresql+asyncpg://127.0.0.1:1/invalid .venv/bin/pytest tests -q`（CI 等价口径） | 0 | **496 passed · 39 skipped**（含新测 32；capability 旧测 57 passed 7 skipped 零破坏；本机 PG 不可达 → test_chat_ws 2 个 pre-existing 失败按 CI 语义 skip，未复现不纠缠） |
| `./scripts/graph-compile.sh` | 0 | 9 graphs OK · mermaid normalize OK |
| `npx --yes dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_host_harness_cli_capability.md` | 0 | LINT: PASS（W4 合法豁免 · SPEC 06 §15 承载） |
| `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` | 0 | PASS（scanned 100 · issues 0） |

**R1 非阻塞 5 条逐项处置**

| # | 处置 |
|---|---|
| ① 自检表行号小差 | 以字段名为准：`CapabilityResult.output`（无 `data`）已对齐现网契约 |
| ② 超时/截断数值 | 30 定：`TIMEOUT_SECONDS = 120.0`（≤180s 上限内）· `MAX_STREAM_BYTES = 64 KiB`（stdout/stderr 各自）；断言落 `test_timeout_and_truncation_constants` + `test_stdout_truncation` |
| ③ adapter `kind` 字面 | 钉死 `"cli"`（docstring 注明漏接风险）；断言 `spec.kind == "cli"` + `HarnessCliAdapter.kind == "cli"`（`test_register_visible_enabled_and_kind_literal_cli`） |
| ④ status 不做 | **显式注明**：`harness.status` 本波**不做**（SPEC §7 可选）· C4 开工时补；验收条 8 按「不做」分支勾选 |
| ⑤ 逃逸错误前缀族 | 定 `invalid_args:`（与 `policy_blocked:` / `cli_failed:` 同族）；错误族全集：`policy_blocked:*`（gateway）· `capability_unavailable:*` · `cli_failed: timeout` · `cli_failed: exit_code=N` · `cli_failed: invalid_json` · `invalid_args:*`（`HarnessCliError`） |

**关键实现事实**

- 新模块 `app/ops/capability/harness_cli.py`：`HarnessCliAdapter`（kind="cli" · `asyncio.create_subprocess_exec` 逐 argv · 禁 shell）+ 命令向量三形态硬编码（`verify --target . --task <path> --json` / `task lint --file <path>` / `task lint-wiki-delta --target .`）+ `_validate_task_path` 白名单 + `_kit_pin` env 钉版 + `register_harness_cli_capabilities()` 幂等注册（代码路径 `gateway.register`；**不**挂 `ensure_default_capabilities`/probes 默认目录——保业务默认目录仅 local_fn · capability 旧测零破坏，锚点 `test_not_in_default_registry`）
- 新测试 `tests/test_capability_harness_cli.py`：32 用例全 mock subprocess（CI/本地不真跑 npx、不装 npm、不断网）
- 图谱：`01_modules.md` capability 行备注 + 人签记录行；`10_flow_capability.graph.yaml` description 备注 + version→2026-09-01（生成物 md / shared/graph.json 随 graph-compile 刷新）；未增 implementedBy → G-L2 indexes 无需同步
- Capability 入出参契约（本 task 自检记录 · SPEC 06 §16 不预冻）：verify 入 `{"task_path"}` 出=透传 parsed JSON dict；task_lint 入 `{"op"[, "task_path"]}` 出 `{"op","passed","exit_code","stdout","stderr"}`
- 禁区核对：未改 `adapters/cli.py` mock-only 语义（零 diff）；未接产品 lg-rag/Chat 主路径；Policy 默认未改开；无通用 shell 通道；未切分支/未 push/未开 PR
- 已知未测项：真 npx 执行（task 钉死仅 mock）；`harness.status`（不做 · C4 补）；业务侧接线（C4 obs 显式调 `register_harness_cli_capabilities()`）

**不 CLOSE（留给 00）。**

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-01 | **00**：C0 CLOSE（#111/#112）后起草 C1；钉 slug=`host-harness-cli-capability`；全集=verify+task_lint 必做 / status 可选；命令向量硬编码 · 禁 shell=True · 参数白名单；env 钉 `DSH_CODING_KIT_VERSION` 缺失即不可用；Policy 默认关 |
| 2026-09-01 | **10-task**：现网核对修正 2 处（`CapabilityResult.data`→`output`；manifest 仅 local_fn → 注册走代码路径 `gateway.register` · builtin.v1.yaml 不适用）；补验收钩 2 条（注册可见性 · Policy 门先于 adapter / cli+high 双键）；补 `### 自检结论`（W4 合法：思考轮由 SPEC 06 §15 承载）；invoke 落盘；00 定夺实质零改 · HG-AUDIT-R1 保持 pending · 下一棒 20-task-audit |
| 2026-09-01 | **20** R1 **pass**（内容零阻塞；非阻塞 5 条已录审查文）· **00** 代签 `HG-AUDIT-R1` → approved；可派 30 |
| 2026-09-01 | **30+40**：实现 `app/ops/capability/harness_cli.py`（`harness.verify` / `harness.task_lint` 白名单 CLI Capability · 禁 shell · env 钉版 · 参数白名单 · 超时 120s/截断 64KiB）+ `tests/test_capability_harness_cli.py` 32 用例（全 mock subprocess）；注册走代码路径 `register_harness_cli_capabilities()`（不进业务默认目录）；`harness.status` 不做（C4 开工时补）；图谱 capability 行 + `10_flow_capability` 描述备注；R1 非阻塞 5 条逐项处置；验收 13 条勾选 · 自检全绿（verify/ruff/pytest 496/graph-compile/lint-wiki-delta）；invoke 落盘；**不 CLOSE（留给 00）** |
| 2026-09-01 | **00 CLOSE**：PR [#114](https://github.com/Cyning12/ops-desk-api/pull/114) MERGED（CI 三绿）；无 Alembic；归档 done/ · Hub 补登 · CLOSE invoke 留档 |

---

## 关账（CLOSE）

| 项 | 值 |
|---|---|
| PR | [#114](https://github.com/Cyning12/ops-desk-api/pull/114) **MERGED** 2026-09-01 |
| 交付 | `app/ops/capability/harness_cli.py`（`harness.verify`/`harness.task_lint` 白名单）+ 32 mock 用例 · Policy 默认关 · env 钉版 |
| 生产 | 无 Alembic；Capability 默认 `policy_blocked`（须 Host 策略通道显式开启）· 业务零影响 |
| 00 复检 | 独立复跑：496 passed / 39 skipped · ruff 触及路径净 · graph-compile 0 · PR #114 CI 三绿 |
| 归档 | 2026-09-01 · 00 关账 · 维护者 Prompt 授权 |

### KPI

Task_KPI%: 100 · D1 范围钉死仅三条白名单 Capability · D2 闸齐（三代签 + 20 R1 pass）· D3 过程档齐（invoke 10/00/30_40 + R1 审查）· D4 图谱 capability 行/flow 备注已随 #114 · D5 关账补登 2026-09-01
