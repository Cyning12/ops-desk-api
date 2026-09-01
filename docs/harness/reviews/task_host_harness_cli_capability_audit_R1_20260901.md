# Task Audit R1：host-harness-cli-capability

> **hat_id**：20-task-audit  
> **task**：`docs/tasks/active/task_host_harness_cli_capability.md`（C1 · harness CLI Capability：verify / task_lint [/ status 可选]）  
> **上游 SPEC**：`docs/spec/agent-infra/06_host_comms_boundary_spec_v0.md`（**signed**）§3（永久禁令 A/B）· §7（Capability 白名单）· §8（Skills≠verify）· §10（C1 行）· §15（思考轮承载）  
> **先例**：`docs/harness/reviews/task_lg_rag_deprecate_chat_stream_audit_R1_20260831.md`（同款 W4 豁免处理 · 同款「00 代签待 R1 落盘」流程）  
> **日期**：2026-09-01 · 审查人：20-task-audit  
> **10 lint**：PASS（W4 无思考轮节 · SPEC 06 §15 承载合法）· 本帽复跑 `dsh-coding-kit@1.10.0 task lint` → **PASS（exit 0）** 核实；`lint-wiki-delta --target .` → **PASS** 核实

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **pass** · 零阻塞 · 不退回 10 · **无「必须退回 00 改钉」级问题** |
| **流程闸** | `HG-AUDIT-R1` **仍 pending**（正确 · 20 不代签）· `HG-TASK-DRAFT` / `HG-GRAPH-MODULES` 已 approved（00 代签 · 维护者 Prompt 授权留痕） |
| **30 授权** | **未签发** · pending 时禁止附 30 Prompt；真值仍在 task 人工闸表；**可交 00 代签 HG-AUDIT-R1** |

---

## 审查核对（对照 SPEC 06 §3/§7/§8/§10/§15 · 现网代码只读 · 10 自检两处事实修正）

| 审查点 | 结论 |
|--------|------|
| SPEC 06 §7 钉死项：白名单仅 `harness.*` 三条 | **一致 · 不退回 00**。task 00 定夺「Capability 全集」= `harness.verify`（必做）· `harness.task_lint`（必做 · `task lint` 与 `lint-wiki-delta` 两子操作）· `harness.status`（可选）——与 §7 白名单表逐行对应；「新增须 SPEC 修订」由非范围「通用 shell / 可传任意命令的 npx 封装（永久禁令）」+ 00 定夺「本波只做三条白名单」锁住 |
| Policy 默认关 → `policy_blocked` | **一致**。00 定夺 Policy 行「`risk_level=high` · 默认关 → `policy_blocked` · 禁止本波把默认改开」与 §7「默认关（block → policy_blocked）」、§13 failure_paths「Policy 默认关时调用 harness.* → policy_blocked」对齐；非范围明列「Policy 默认开」 |
| env 钉 `DSH_CODING_KIT_VERSION` 缺失即不可用 | **一致**。00 定夺「缺失 → Capability 返回不可用错误（非静默漂版）」与 §7「无 env 时 Capability 不可用而非静默漂版」、§12 风险表「kit 版本漂移」逐字对齐；验收条 4 + failure_paths 行 2 双钩可验收 |
| mock subprocess 不真跑 npx | **一致**。test_strategy_note「CI/本地不真跑 npx、不装 npm、不断网」+ 非范围「真跑 npx 的测试进 CI/本地默认路径（仅 mock）」与 §7 测试行「mock subprocess + fixture JSON；CI 不断网装 npm」对齐 |
| §3 永久禁令 A（通用 shell）是否被开口子 | **未开口子 · 反而收紧落地**。命令向量硬编码三形态 + `asyncio.create_subprocess_exec` 禁 shell=True + 参数白名单（`task_path` 须在 `docs/tasks/` 内 · 拒绝对路径/..逃逸/shell 元字符）是禁令 A 的实现侧收紧；task 无任何「任意命令」通道 |
| §8 Skills≠verify | **无冲突**。本 task 正是 §8「C1 CLI Capability 必做」的落地波；未以 Skill 宣称替代机械闸 |
| 10 修正 ①：`CapabilityResult.data` → `output` | **与现网相符 · 未越权**。types.py L33–42 现网核实：`CapabilityResult` 字段 = `ok / output / error / capability_id / duration_ms / meta`，**无 `data`**；00 定夺「返回」行与验收条 1 已改 `output`，修正仅为字段名对齐现网契约，范围实质零改 |
| 10 修正 ②：注册走代码路径 `gateway.register` 非 manifest | **与现网相符 · 未越权**。manifest.py 现网核实：`ALLOWED_KIND = "local_fn"`（L31）· adapter 前缀白名单仅 defaults/lookups（L32–34）· 非法 adapter 整文件失败（L243–244）→ subprocess cli adapter **不可能**经 builtin.v1.yaml 注册；`gateway.register` 存在（gateway.py L38）· registry 重复 id → ValueError（registry.py L33–35）· 测试 `clear()`（L64–66）均在。builtin.v1.yaml 现网 5 枚全 local_fn（自检陈述属实 ✓）。修正为机制表述对齐现网，非范围变更 |
| 10 新增验收钩：双键 + Policy 门先于 adapter | **现网事实成立**。policy.py `check_invoke` 次序现网核实：risk=high 先查 `allow_high_risk`（L64–67）→ kind=cli 再查 `allow_cli`（L74–77），故 kind=cli 且 risk=high 须 **双键同开**；env 键 `OPS_CAPABILITY_ALLOW_HIGH_RISK` / `OPS_CAPABILITY_ALLOW_CLI`（L25–27）与 `_host_policy` dict 通道（L42–46）均与 task 陈述一致。gateway `_prepare_call`（L127–174）在 L158 `check_invoke` **先于** L251 `adapter.invoke` → 验收条「默认关时 adapter invoke 零调用（mock 计数断言）」与现网网关语义一致，可验收 |
| `adapters/cli.py` 不复用 | **一致**。现网核实 MockCliAdapter（L13–26）：mock-only · 零子进程 · docstring 明钉「真实 bash 高风险，禁止进 defaults / CI 默认路径」——00 定夺「专用白名单 adapter · 不复用」与现网语义相容，且非范围明列「改 `adapters/cli.py` mock-only 语义」 |
| 命令向量/参数白名单/超时/截断可验收性 | **可验收**。命令向量钉死三形态（verify / task lint / lint-wiki-delta）含 `--yes dsh-coding-kit@<pin>` 钉版；禁 shell=True 有「grep 断言或代码审查条」（验收条 7）；逃逸拒绝用例**具体三类**：`../` · 绝对路径 · shell 元字符（验收条 5）；超时 ≤180s → `cli_failed: timeout` 不挂起（验收条 6 · mock 模拟）；JSON 解析失败 → `cli_failed` + 截断 stderr（failure_paths 行 3） |
| failure_paths 完备性 | **完备**（五行）：Policy 默认关 ✓ · env 未钉 ✓ · npx 非零退出/JSON 解析失败 ✓ · subprocess 超时 ✓ · task_path 逃逸拒绝（不执行）✓——覆盖 SPEC §13 中 C1 相关两行（kit env 未钉 · Policy 默认关）并补齐实现侧三条 |
| 非范围：C2/C3/C4 · 产品主路径 · Policy 默认开 | **齐全**。C2 Prompt Pack / C3 受控写盘 / C4 `/obs` UI 各另 task（与 §10 波次表 + §10 顺序钉「C1→C2→C3 串行 · C4 仅 web 可并行」一致，task orchestration 行同钉）；「把 `harness.*` 接进产品 lg-rag/Chat 主路径」明列排除（§9 session 隔离「共用内核 · 不共用 Pack」语义相容）；另有 comms session / PromptAssembly 接线（C2）排除——与范围互斥无重叠 |
| graph_delta（capability 行备注 · 不新增一级模块 · G-L2 条件钩） | **合理**。现网核实 `docs/_tech_graph/l1/01_modules.md` L26 `capability` 行存在（H2 已建 · HG-GRAPH-MODULES 历史 L58–66 多次「行备注 · 不新增一级模块」先例）；`10_flow_capability.md`/.graph.yaml 存在（L81 ✓），graph_delta「capability flow（若存在则备注）」实已坐实为存在；「若增 `implementedBy` → 同步 G-L2 indexes」为条件钩、不预加义务；graph_change_layer=`G-L1` 合理；HG-GRAPH-MODULES=approved（00 代签）成立 |
| wiki_delta=`n/a` | **合理**。行为真值在 SPEC 06 §7/§8 + 本 task；不晋升 coding_wiki；验收条 13 `lint-wiki-delta` 钩在（本帽复跑 PASS） |
| 思考轮 W4 豁免（SPEC 06 §15 承载） | **合法 · 不退回**。本帽复跑 `task lint` → PASS · W4「无思考轮节（SPEC 承载 / bugfix 轨合法豁免）」；SPEC 06 §15 R0–R5 回填完整（R4 明钉「实现可测性 policy_blocked / dry-run / mock subprocess 留给 C1–C3 task」——即本 task 的验收即 SPEC 思考轮的执行层落地）；与 T5/T6 先例同款处理，20 不把缺节当内容阻塞 |
| 人工闸表与 invoke 留档 | **合规**。required_invoke_hats=`10,00,30`；00/10 invoke 已落盘 `docs/harness/invokes/by-task/host-harness-cli-capability/`（两文件 glob 核实 ✓）；HG-TASK-DRAFT approved（00 代签 · 维护者 Prompt 授权 · 2026-09-01）· HG-GRAPH-MODULES approved · HG-AUDIT-R1=pending 待本审查落盘后 00 代签——符合 SPEC §6 闸纪律「00 代签 ≠ 模型自签」区分；§3 永久禁令 B 未被触碰（本帽亦不签发） |
| 行为变更类 task「旧测 grep 影响面」（K7 checklist） | **已钩**。本 task 为**新增** Capability（不改默认值/校验/fallback 语义），验收条 10「pytest 相关绿（**含 capability 旧测零破坏**）」+ 验收条 12「单测 `clear()` 隔离防重复 id ValueError」已覆盖影响面；30 自检时建议附 `tests/` 内 capability 相关测试文件清单（grep `capability`）逐一点名 |
| freeze / 05 契约 | **无冲突**。freeze_id=`n/a` 且注明「不改 lg-rag-sse-v1 · Capability 入出参 JSON 契约由本 task 30 自检记录 · SPEC 06 §16 不预冻」——与 §16「C1 起若出现新契约由对应实现 task 定义 freeze，不在本 SPEC 预冻」逐字对齐 |

其余可执行性：验收含 ruff/pytest/graph-compile/lint-wiki-delta 全绿；必读列表含 SPEC §3/§7/§8 + 现网七文件只读参考 + L2 规范 + 图谱行；`close_pr_policy=required`、`kpi_aggregator=CLOSE` 与 C 轨串行编排一致。

---

## 阻塞

无。

---

## 非阻塞风险（不退回 10 · 30 知情即可）

1. **自检表行号小差**：10 自检称 `CapabilityResult` 字段在「types.py L33–41」，现网 `meta` 字段实落在 **L42**（L33 为 `@dataclass` 装饰器）——字段名核对（`output` 无 `data`）实质无误，仅行区间差一行；30 以字段名为准即可，不构成阻塞。
2. **超时/截断数值未钉死**：task 钉「≤180s」上限与「截断上限」方向，具体秒数与 stdout/stderr 截断字节数由 30 落地定——SPEC 06 §7 同样未钉数值，属实现自由度；30 须把选定值写进单测断言与自检记录（验收条 6 只要求「不挂起 + 错误返回」语义）。
3. **kind 字面量依赖**：验收条 11 建议 adapter `kind="cli"`——现网 policy.py L74 只认字面 `"cli"`，若 30 自定义其他 kind 字符串，`allow_cli` 门会静默漏接（仅剩 high_risk 单键）。建议 30 自检清单写明「kind 字面必须为 `cli`」并加一条单测断言 `spec.kind == "cli"`，task 未钉死、非契约项。
4. **`harness.status` 可选分支**：验收条 8 已分「做则 mock 断言 / 不做则非范围注明（C4 开工时补）」——30 若选不做，须在自检记录显式写「status 未做 · 非范围注明」，避免该验收条半悬挂；SPEC §7 status 行标「可选」、§10 C4 行「C1 status」为软依赖，不做不阻塞 C4（C4 task 自补）。
5. **逃逸校验的错误分类**：failure_paths 行 5「task_path 逃逸 → 校验错误」与验收条 5「拒绝（断言）」未钉错误串前缀（`cli_failed` vs `invalid_args` 类）——30 落地时定并写入自检；建议与 `CapabilityResult.error` 既有风格（`policy_blocked: *` / `cli_failed: *`）保持一致前缀族，便于 C4 `/obs` 投影聚合。

---

## 回填清单

无（内容零阻塞 · 不改 task 实质 · **不改**人工闸表 status）。

---

## 签收

**内容签收 · pass**（终轮 R1）。流程闸 `HG-AUDIT-R1` 仍 **pending**（本帽不签发）——**可交 00 代签 HG-AUDIT-R1**；pending 期间禁止下发 30 Prompt。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（00 代签 · 维护者 Prompt 授权 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
