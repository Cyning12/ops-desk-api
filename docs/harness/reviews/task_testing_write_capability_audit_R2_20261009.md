# task_testing_write_capability 审查（R2 · 20-task-audit）

> **审查对象**：`docs/tasks/active/task_testing_write_capability.md` 修订版（commit 2bc48e5 · 承接 30 GATE_STOP 实证与维护者裁定四=乙）
> **审查帽**：20-task-audit R2（书面复审 · 未改 task 实质内容 · 未代签任何 human_gate · 未执行 30）
> **日期**：2026-10-09 · **审查时仓态**：worktree `ops-desk-api-worktrees/d2-testing-write-capability` · 分支 `task/testing-write-capability` · 工作树净
> **前置链**：10 落稿（54c6101）→ 20 R1 PASS（审查文 `task_testing_write_capability_audit_R1_20261009.md`）→ 00 代录三闸（13ef6d7）→ 30 GATE_STOP 零 diff（599df9b · loader V1/V2/V7 夹击实证）→ 维护者裁定四=乙 → 10-task 修订（2bc48e5 · HG-TASK-DRAFT / HG-AUDIT-R1 回退 pending）
> **复审范围**（10-task 留转 · invoke_20261009_10_task_revise）：裁定四 loader V1 放宽语义 · V8 对称适配 · F7 波及面闭合 · A8 可机断性 · 钉死契约新增两字段与 loader 实证一致性 · 甲乙丙丁裁决理由 · R1 结论存续性
> **结论**：**PASS**（内容零阻塞 · 复审七要点逐条成立 · 非阻塞观察项 3 条 O5–O7 · 流程闸 HG-TASK-DRAFT / HG-AUDIT-R1 pending 待维护者重签）

---

## 结论摘要

| 维度 | 结论 |
|------|------|
| task **内容**可执行 | ✅ **PASS · 零内容阻塞**——裁定四与 loader 实证逐行一致；V1 放宽语义（二选一 · 仅 write 强制）与 read 零 diff 论证经源码实读成立；V8 对称适配无误伤面；F7 波及面闭合（一条非阻塞提醒）；A8 四断言可机断；甲乙丙丁裁决理由完备；R1 结论未被修订破坏 |
| **流程闸** HG-TASK-DRAFT | `pending`（修订后如实回退 · blocks 20/30 · 待维护者重签） |
| **流程闸** HG-AUDIT-R1 | `pending`（本 R2 审查文即其重签前置交付 · R1 审查未覆盖 loader 冲突的登记属实） |
| **流程闸** HG-GRAPH-MODULES | `approved` 在册（裁定四扩大 schema 面仍为 l1 模块内增量 · 备注已补 · 30 同步 01_modules.md 义务不变——维持 approved 合理） |
| lint 复跑 | `npx spec-wave task lint --file docs/tasks/active/task_testing_write_capability.md` → **LINT: PASS · EXIT=0**（2026-10-09 本帽复跑 ✓） |
| verify 复跑 | `npx spec-wave verify --target . --task ...` → **VERIFY: BLOCKED · EXIT=2**（HG-TASK-DRAFT / HG-AUDIT-R1 pending · 闸回退后属实时序 · 符合预期） |
| draft 洁净度 | ✓ 工作树净；修订仅触 task md + 10 invoke（diff 全为文档）；`app/`/`tests/` 零改动 |

---

## 复审要点逐条裁定（委托令七条）

### 1. 裁定四 loader V1 放宽语义（「http 块键 或 顶层键」二选一 · 仅 write 强制 · read 零 diff）✅

实读 `manifest.py:818-830` 实证：`_validate_invariants` 以 `is_write = spec.side_effect in WRITE_SIDE_EFFECTS`（:823）门控 V1，`http_block = spec.http or {}`（:824）——local_fn 恒走空 dict 分支，故 V1 对 write+local_fn 必触发（30 探针实证一致）。放宽为「`http.idempotency_key` 或顶层 `idempotency_key` 任一非空」后：

- **仅 write 强制**成立：V1 判定整体在 `is_write` 门内，read 条目本就不进此分支——放宽不触碰 read 路径。
- **read 零 diff 论证成立**：顶层键缺省 None（F7 钉死）→ 存量 manifest（builtin 五枚 + oa.readonly 三枚）解析出的新字段恒 None → V1/V8 新旧分支对存量清单均不触发，校验行为逐字节不变。
- **V7 边界不动**（:533-540 实读：原始数据上校验「仅 kind=http 可声明 http 块」）→ 顶层键是 local_fn 唯一合法声明位，与裁定四「非 http 块」语义自洽。

### 2. V8 对称适配误伤面 ✅（无误伤先例）

`manifest.py:870-874` 实读：V8 现仅查 http 块键；对称适配扩为「read 声明顶层键同样 ManifestError」，延续「只读不需要幂等键」语义，方向正确。误伤面 grep 实证：

- `manifests/builtin.v1.yaml`（5 枚 local_fn · 全 side_effect=read）与 `manifests/oa.readonly.v1.yaml`（3 枚 http · 全 side_effect=read）**均无顶层 `idempotency_key`**（全仓 grep：yaml manifest 零命中）。
- 仓内声明幂等键的 yaml 仅 `evals/agent/golden/capability/cases_v1.yaml` fixture（均在 http 块内；其 V8 用例系故意触发）；tests 内构造均为 `http={...}` dict 形（非顶层键）。
- 附带实证：loader 对条目**顶层未知键当前静默忽略**（无顶层白名单校验；白名单仅存在于 output_schema V10 :307-310 / fallback V11 :405-416 / visibility :575-579 三个子块）→ 新增顶层解析无既有校验冲突。

### 3. F7 波及面闭合性 ✅（一条非阻塞提醒）

F7 列：manifest.py 解析 + CapabilitySpec 承载 + schema 文档 + A8 单测 + 01_modules.md 图谱。逐项核查：

| 面 | 核查结论 |
|----|----------|
| CapabilitySpec 承载 | ✓ `types.py:76-133` frozen dataclass 全字段带默认 · 增可选字段默认 None 后向兼容——**有仓内直接先例**：SPEC host-v1-visibility-scenario-policy（V1-B · :94「`CapabilitySpec` 增四字段（frozen dataclass 兼容 · 默认 None=未声明）」）同形态已落地 |
| defaults.py 罐头签名 | ✓ 无需动：`_DEFAULT_SPECS` 五枚全 `side_effect="read"` + kind=local_fn（:77-155 实读），不触发 V1/V8 新分支；F2「不进 _DEFAULT_SPECS」与本面无交叉 |
| delegation.py 判定面 | ✓ 无波及：`auto_approve_ok`（:488-514）只读 scope / side_effect / kind 三维度，不读幂等键；钉死契约「判定逻辑零改动」保持成立 |
| 既有 manifest 回归测试 | ✓ `test_capability_manifest.py:83` count==5、domain_allowlist:102-112 钉死语义等 B1 清单断言均不经顶层键路径，默认 None 下零 diff |
| 01_modules.md | ✓ graph_delta 行已补「manifest 顶层 idempotency_key 字段 + loader V1 放宽（裁定四）」；capability 行（01_modules.md:34）模块内增量备注义务已在闸表登记 |
| **golden eval 套件** | ⚠ **F7 未列**——`evals/agent/golden/capability/baseline_v1.json:102,134` 将 V1/V8 错误文案**逐字钉死**（`error_contains: "capabilities[0] V1: side_effect=write 必须有 idempotency_key"` 等），且 `tests/eval/test_eval_agent_golden.py:26,36` 经 pytest 加载 cases_v1.yaml 对拍。放宽语义本身**不要求改文案**（V1 仍对「两键皆缺」触发），但若 30 顺手改写 V1/V8 文案则 golden 红。A8③「既有 manifest 测试原样绿」+ A2④ 全量 pytest 兜底已机械覆盖此面 → **非阻塞**（观察项 O5） |

### 4. A8 四断言可机断性 ✅

① 两键皆缺 → ManifestError（`pytest.raises` + 消息含 V1）② 顶层键 → 加载成功（registry 断言）③ read 无顶层键 → 既有 manifest 测试原样绿（命令输出断言）④ read 误声明顶层键 → ManifestError（V8）。四条全部可对 pytest 输出机断，无人工判读残留；与既有测试文件（`test_capability_manifest_http.py:131` V1 用例 / :276 V8 用例）同构，落点明确。

### 5. 钉死契约新增两字段与 loader 实证一致性 ✅

- `hitl.required: true`（task :79）↔ V2 `manifest.py:832-836` 实读一致（`is_write and not spec.hitl_required` → ManifestError）；与本 capability「就是用来触发 HITL」用途自洽。
- 顶层 `idempotency_key` 非空（task :79）↔ 裁定四 V1 放宽语义一致；「非 http 块——V7 禁 local_fn 声明 http 块」↔ :533-540 实读一致。
- failure_paths 第 10 行锚点 `manifest.py:826-836` 覆盖 V1（:826-830）+ V2（:832-836）✓；F7 锚点 V1 :826-830 / V8 :870-874 全中。
- 表行数勘正属实：failure_paths 表现实 **10 行**（:111-120），R4 小节与控制表「十条」一致（R1 观察项 O4 已闭环）。

### 6. 裁定四甲乙丙丁裁决理由完备性 ✅

四条裁决各有机制性理由且与 30 invoke 选项表（invoke_20261009_30 :64-69）对应无跳跃：

- **甲否**（V1 收窄 kind=http 专属）：摘掉 local_fn 幂等护栏 = 缩小安全校验语义、风险后置——成立（V1 设计意图「写操作必须有幂等键」原覆盖所有 kind，:826 注释实证）。
- **乙采纳**（顶层字段）：V1 不变量全 kind 保持 + 只为 local_fn 开合法声明位 + 缺省 None 后向兼容 + 不改判序语义——成立，且有 V1-B SPEC 先例支撑此演进形态。
- **丙否**（kind=http 假端点）：违反「语义 mock 零 IO」钉死 + 引入假 HTTP 面——成立。
- **丁否**（放弃 manifest 特例注册）：破 off 零 diff 纪律与裁定一——成立（EXTRA_MANIFESTS 默认空 → 不加载 → 零 diff 是裁定一赖以成立的机制）。

### 7. R1 结论存续性 ✅（修订未破坏既有结论）

- **裁定一二三**：R2 小节原文保留（diff 仅标题「三裁定」→「四裁定」+ 追加裁定四段），实证基础（count==5 / domain_allowlist:102-112 / 罐头范式）未受影响。
- **B1 清单**：10 文件清单未动（diff 不触 B1 节）。
- **A1–A5 / A7**：逐字未动；A6 由五字段扩为七字段（增 hitl.required + 顶层幂等键），属裁定四附带落盘的必要扩展，方向与 loader 实证一致。
- **R1 观察项勘正**：O1（builtin 行窗 :8-26——实读复核 :8 起 id、:26 止 adapter ✓）· O2（strategy/builder.py:28 路径段补齐 + 第四调用点 evals runner.py:120 ✓）· O4（八条→十条 ✓）三项全部正确闭环。
- **闸表回退**：HG-TASK-DRAFT / HG-AUDIT-R1 回退 pending 的理由登记（内容实质变更 · R1 未覆盖 loader 冲突）属实；HG-GRAPH-MODULES 维持 approved 在册合理（裁定四仍 l1 模块内增量 · 备注已补记扩大面）。

---

## 非阻塞观察项（不阻 30 · 供维护者/30 参考）

| # | 项 | 性质 |
|---|----|------|
| O5 | F7 波及面未列 golden eval 套件：`baseline_v1.json:102,134` 逐字钉死 V1/V8 错误文案（经 tests/eval/test_eval_agent_golden.py 进 pytest）。**30 应保持 V1/V8 文案逐字节不变**（放宽只消触发条件、无需改文案）；若确需改文案，须同步 golden baseline 并在 invoke 记明 | 波及面枚举提醒 · A8③+A2④ 全量回归已机械兜底 |
| O6 | F7「schema 字段族文档」仓内无独立 schema 文档；字段族真值= `types.py` CapabilitySpec 注释 + `builtin.v1.yaml` 头注释/字段族范式 + `01_modules.md` capability 行备注三处。30 落地时按此三处同步并在 invoke 注明口径 | 指代澄清 · 不影响可执行性 |
| O7 | 顶层 `idempotency_key` 对 local_fn 当前**无运行期消费方**（http_generic 只消费 http 块键 :781；gateway.py:494 读 adapter 返回值）——定位即裁定四所述「加载期护栏/声明位」，语义如实；未来 local_fn 接真实写时消费面另立 task | 语义定性确认 · 非缺陷 |

## 阻塞项

**无内容阻塞。**

## 回填清单

无（零内容阻塞 · 无退回 10-task 项）。

---

## 维护者签闸（20 R2 后 · 30 前）

- [ ] 已读 R2 审查结论（本文件）
- [ ] 在 task 人工闸表将 HG-TASK-DRAFT 改为 approved（维护者 · 日期）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期 · 注明 R2 PASS）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt（30 交付面=F1–F7 全量 · 含 loader V1/V8 适配 + A8 单测 + 01_modules.md 同步；注意 O5 文案钉死约束）

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-09 | 20-task-audit R2 落盘：PASS（复审七要点逐条成立 · 内容零阻塞 · 非阻塞观察项 O5–O7）· HG-TASK-DRAFT / HG-AUDIT-R1 pending 待维护者重签 · 不附 30 Prompt |
