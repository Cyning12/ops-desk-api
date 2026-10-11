# 审查文：task_hitl_approval_consumption_strategy_env · 20-task-audit R1

> **hat**：20-task-audit（R1 · 书面审查 · 不实现代码）
> **审查对象**：`docs/tasks/active/task_hitl_approval_consumption_strategy_env.md`（T3 · D3 strategy 候选 map env 追加口 · commit 07f9cc1）
> **对照 SPEC**：SPEC-hitl-approval-consumption_v1.md（signed · HG-SPEC-SIGNOFF=approved 2026-10-10 · 只读对照）
> **日期**：2026-10-10 · **审查帽**：R1

---

## 结论（一 · 摘要：内容 / 流程闸分列）

| 维度 | 结论 |
|------|------|
| **task 内容可执行性** | **PASS（零内容阻塞）**——SPEC 承接闭合 · TC1–TC3↔A4/A5/A8 映射闭合 · 锚点全部实读吻合 · 思考轮 R0–R5 回填闭合 · failure_paths 8 条均可机断 |
| **流程闸** | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES **三闸全 pending**（属实时序 · 本帽不代签）→ **30 拒开工存续**；`npx spec-wave verify` 复跑 **EXIT=2** 实证（见 §十） |
| **非阻塞提示** | 2 条（B1 漏登 eval golden 行 · 图谱行转述性引文）——不阻塞 R1 裁定，落 §十一 留 30/40 吸收 |

**裁定**：**PASS（内容面）**。HG-AUDIT-R1 仍 pending → 本文文末只附维护者签闸清单，**不附 30 Prompt**。

---

## 二 · SPEC 承接闭合核对（D3 / Q4-S1 / FP-5 / A4+A5/A8 面）

task 头部声称承接「D3 · Q4 · FP-5 · A4（+ A5/A8 存续面）」，逐条对 SPEC v1 实读核对：

| SPEC 条目 | SPEC 原文要点（行号） | task 承接面 | 核对 |
|-----------|----------------------|-------------|------|
| **D3** env 追加口 | `OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS` 逗号分隔/strip/去空去重/默认不设=对 master 逐字节零 diff；map 解析后追加（含未知 key）；下游闸全链不动；生效记台账（SPEC :92-95） | 钉死契约 7 行（task :72-78）逐字对应：env 形态/追加语义含未知 key/下游闸不动/台账设则记未设不记 | ✅ 闭合 |
| **Q4 = S1** | env 追加集裁定（S2 JSON 覆盖难审计弃 · S3 复用测试钩子半径过大弃 · SPEC :155-159） | task R2 节「SPEC 裁定存续（不重开）」+ 双弃理由原样引述（task :182）；钉死契约「禁复用覆盖口当 env 口」（task :74） | ✅ 闭合 |
| **FP-5** | env 口注入高危/写 id → 下游 ∩visible + deny_high_risk（判序在前）+ Policy 写闸全链仍在；断言「仍被裁」（SPEC :195） | failure_paths FP-5 行（task :105）+ TC2 断言化（task :132）——见 §五 | ✅ 闭合 |
| **A4** env 口验收 | ①不设→各 key 含未知 key 逐字节一致 ②设→追加且 ∩visible/stripped 不变 ③FP-5 断言（SPEC :210） | ①②→TC1 ①②（task :131）；③→TC2（task :132） | ✅ 闭合（映射表见 §三） |
| **A5 本 task 面** | registry/policy 闸序段 git diff 空 + `test_allow_tags_does_not_waive_deny_write` 原样绿（SPEC :211） | TC2 尾句原样承接（task :132）+ B1 行（task :123） | ✅ 闭合（A5 的「审批消费不过 gateway/Policy」属 T1 消费门面 · 正确划出） |
| **A8 本 task 面** | pytest 全绿/ruff 零新增/graph-compile EXIT=0/图谱回写（SPEC :214） | TC3 全项承接（task :133）；图谱四行中本 task 只写 lg_rag 行（strategy 归属段）· 其余三行属 T1/T2 面——切片正确 | ✅ 闭合 |
| 缺口 3 背景 | config.py:14-23 静态 map + builder.py:177-182 ∩visible（SPEC :49-51） | 背景节逐字承接 + 40 invoke :33 证据源（task :47, :64） | ✅ 闭合 |

**非范围对账**：task 非范围 6 条（task :91-96）与 SPEC §3 非范围无冲突；T1/T2 面划出与 SPEC D1/D2/D5 归属一致；「SPEC 文档本身任何改动」划出符合「SPEC 在 spec 分支 · 随首个实现 PR 带入」纪律。

**结论**：承接声称逐条成立，无漏承、无超承。

---

## 三 · 验收 TC1–TC3 ↔ SPEC A4/A5/A8 映射闭合性

| SPEC 验收 | 拆解子句 | task 落点 | 可机断性 |
|-----------|----------|-----------|----------|
| **A4①** 不设 env 逐字节零 diff | 各 key（supervisor/default/未知 key）对拍 | TC1①「返回 list 内容与顺序对拍」（:131） | ✅ 机断（断言比对字面期望集 · 见 §四讨论） |
| **A4②** 设 env 追加语义 | map 命中 key + 未知 key 两例；∩visible/stripped 不变 | TC1②（:131） | ✅ 机断（两例断言 + stripped 语义断言） |
| **A4② 解析形态** | strip/去空/保序去重/全空白=不设 | TC1③（:131）+ 实操-A 四例（:106） | ✅ 机断（四例参数化断言） |
| （task 新增钉）覆盖口隔离 | 覆盖口生效时 env 不混入 | TC1④（:131）+ 实操-D（:109） | ✅ 机断；SPEC 未明示两键交互——本帽复核见 §七 |
| **A4③ = FP-5** | env 含高危/写 id 仍被下游裁 | TC2 首句（:132）+ FP-5 行（:105） | ✅ 机断（选型断言并留痕 · 见 §五） |
| **A5 本 task 面** | registry/policy diff 空 + 钉死测试原样绿 | TC2 尾句（:132） | ✅ 机断（git diff 空 + 点名测试绿） |
| **A8 本 task 面** | pytest 全绿 / ruff 零新增 / graph-compile EXIT=0 / 图谱回写 / 台账 | TC3（:133） | ✅ 机断（命令退出码 + diff 空 + 台账断言「设则记未设不记」） |
| B1 旧测 | 六文件清单全绿亲跑落 40 invoke | 验收第 4 条（:134） | ✅ 机断（命令+结果留痕） |
| lint 双闸 | task lint + lint-wiki-delta | 验收第 5 条（:135） | ✅ 机断（本帽已复跑 task lint PASS · 见 §十） |

**闭合性裁定**：A4 三子句全数映射（①②→TC1 · ③→TC2），无悬空；A5/A8 的本 task 切片面无漏项；TC1④ 为 task 层新增钉（SPEC 沉默面），已按 R2 留转程序由本帽复核（§七）。**映射闭合**。

---

## 四 · 重点核查 1：env 追加集默认零 diff 断言可机断性

**零 diff 论证复核（对照 config.py:29-45 实读）**：函数三分支——①覆盖口非 None 直返（:39-40）②map 命中 `list(mapped)`（:45）③未命中 `[]`（:43-44）。task 钉「不设/全空白 env → 追加集为空 · 返回路径与现状一致」（:72）：三分支各自零 diff 成立（追加空集且不改返回构造 = 内容与顺序不变）。✅ 论证成立。

**可机断性复核**：TC1① 表述为「对 master 逐字节一致（返回 list 内容与顺序对拍）」。运行时无法真的 checkout master 对拍——机断落地形态 = **字面期望 list 断言**（如 supervisor→静态五枚字面量、default→`["utc_now_iso"]`、未知 key→`[]`），配合「不设 env 与设全空白 env 两态结果相等」断言。现有 `tests/test_strategy_builder.py:45-50` 已有未知 key=`[]` 与 supervisor 集断言先例，30 按此形态扩展即可机断。**裁定：可机断成立**；建议 30 以字面量断言实现（非动态取 master），此为实现形态提示、非内容阻塞。

**补充钉的机断性**：「不设 env 不记台账」（:78）与 TC3「env 生效台账断言（设则记 · 未设不记）」（:133）互锁，双向可断言。✅

---

## 五 · 重点核查 2：FP-5（env 注入高危/写 id 仍被裁）断言化

**下游裁剪链实读复核**（task R3 声称「四层下游任一皆可裁」:194）：

| 层 | 锚点 | 实读结果 |
|----|------|----------|
| ∩visible | `builder.py:177-182` | ✅ 节点函数内每轮调 `get_candidate_capability_ids` → `build_allowlist_from_candidates(candidates, visible_ids)`，stripped 台账照旧（:188-189） |
| deny 判序 | `registry.py::_match_filter :112-140` | ✅ `deny_high_risk`（:128）在 `deny_write`（:130）**之前**；`allow_write_tags_any` 只豁免 deny_write 一层（:131-136）· docstring :118 明示「deny_high_risk 永不豁免」 |
| Policy 写闸 | `policy.py:96-105` | ✅ high_risk 闸（:96-99）+ 写闸 `write_not_confirmed`（:102-105）在案 |
| 计划校验 | `_subtasks_have_valid_tool_ids`（40 invoke :33 引 nodes.py:147-157） | ✅ 幻觉 id 拒 → fallback（既有面 · 本 task 不动） |

**断言化充分性**：TC2 要求「env 含高危/写 capability id → 仍被下游裁（∩visible 不可见 · 或经可见性豁免路径仍被 deny_high_risk/deny_write/Policy 裁 · **按既有测试面选型断言并留痕**）」+ registry/policy diff 空 + `test_allow_tags_does_not_waive_deny_write` 原样绿。三层防线并行：行为断言（选型）+ 代码 diff 空（机械）+ 钉死测试绿（机械）。**裁定：FP-5 断言化闭合**。

**非阻塞提示**：「按既有测试面选型」给 30 留了选型自由度（如：env 注入 `testing.write.echo` 且 visible 不含 → stripped 断言；或构造 high_risk id 走 `_match_filter` 断言）。选型自由度可接受（B1 已点名 `test_capability_domain_allowlist.py:102-112` 与 `test_capability_testing_write.py` 两个现成面），建议 30 将选型与理由落 30 invoke 留痕，便于 40 复检。

---

## 六 · 锚点实读复核（config.py:14-45 · builder.py:177-182 · 全锚点表）

本帽对 task「现状锚点」表与 B1 表全部行号**逐条实读复核**（base worktree = commit 07f9cc1 工作区 · 代码面与 master 4d905e0 一致）：

| task 声称 | 实读结果 | 核对 |
|-----------|----------|------|
| `config.py:1-6` docstring：禁止 None=全开 · 未知 key→[] · 测试可 patch 覆盖 | :1-6 逐字吻合 | ✅ |
| `config.py:14-23` `CAPABILITY_ALLOWLIST_BY_KEY` supervisor 五枚 + default | :14-23 · 五枚（utc_now_iso/mock_get_issue_status/mock_get_deploy_info/get_issue_by_number/get_pr_by_number）· default=`list(MINIMAL_READONLY_CAPABILITY_IDS)`（:22）· :11 最小只读集 | ✅ |
| `config.py:25-26` `CANDIDATE_CAPABILITY_IDS` 覆盖口 · 注释「禁止用 None 表示全开」 | :25-26 逐字吻合 | ✅ |
| `config.py:29-45` 分支结构：覆盖口直返 :39-40 · 未命中 [] :43-44 · 命中 `list(mapped)` :45 | 逐行吻合 | ✅ |
| `builder.py:177-182` 节点内每轮调用 → ∩visible | :177-179 调用 · :180-182 `build_allowlist_from_candidates` · 在节点函数体内（非模块级固化） | ✅ |
| `delegation.py:100-107` env 先例（strip/lower/回退） | :99-102 `delegation_mode()` 函数内读 env strip().lower() 回退 off · :105-107 `_env_int` low/high | ✅（且为「调用点读取」先例同形态） |
| `baseline.py` `OPS_CAPABILITY_ALLOW_WRITE_TAGS` 逗号分隔先例 | :40 常量 · :44「逗号分隔；空/未设 → None」 | ✅ |
| `registry.py:112-140` deny 判序 | 见 §五表 | ✅ |
| `policy.py:96-105` 写闸 | 见 §五表 | ✅ |
| `01_modules.md` lg_rag 行 strategy 归属裁定 | 行 35 载「路径覆盖补记：`app/ops/strategy/**`（S1 薄包 · Builder/Intent/Critic · 消费方 `lg_rag/multi` · 非一级模块 · 承 prompts 先例归属本行）」 | ✅ 裁定在册（引文为转述 · 见 §十一 nit-2） |
| 40 invoke :33 证据（live 静态五枚 + shim 补位） | `invoke_20261009_40_verify_testing-write-capability.md` :33 逐字吻合（含 `CANDIDATE_CAPABILITY_IDS` 运行期覆盖 shim 登记） | ✅ |
| B1 `test_lg_rag_supervisor_capability_catalog.py:50-57` | :50-57 `test_supervisor_cap_filter_lists_local_fn` 含 mock_get_issue_status/utc_now_iso 断言 | ✅ |
| B1 `test_capability_domain_allowlist.py:102-112` | :102-112 `test_allow_tags_does_not_waive_deny_write` 逐字吻合 | ✅ |
| env 名 `OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS` 未被占用 | 全仓 grep：仅 task 文档三处引用 · 代码零使用 | ✅ 无冲突 |

**结论**：锚点表零虚报、零错位；「10 已逐行实读」声称经 20 抽全检复核成立。

---

## 七 · R2 留转复核：覆盖口生效时不追加 env（SPEC 未明示两键交互）

task R2 residual_risks 明文留转：「覆盖口生效时不追加 env 一钉留 20 复核（SPEC 未明示两键交互）」（:165, :170）。本帽裁定：

- **SPEC 字面存续性**：Q4-S1 裁定原文「map 解析后追加」（SPEC :157）。覆盖口分支（config.py:39-40）在 map 解析**之前**短路直返——「覆盖口生效时不追加」并不违反「map 解析后追加」字面（覆盖口路径本就不经 map 解析）。✅ 不与 SPEC 冲突。
- **语义合理性**：`CANDIDATE_CAPABILITY_IDS` 定位是测试/运维显式覆盖钩子（:25-26 注释在案）；若 env 在覆盖口生效时混入，既有测试面会被运行环境污染（实操-D 场景真实：40 invoke 的 shim 正是运行期覆盖该全局）。「测试钩子纯净」钉守住 B1 `test_capability_testing_write.py` 面零漂移。✅ 方向正确。
- **断言化兜底**：TC1④ + 实操-D 双向断言（覆盖口生效时 env 集不混入）。✅ 可机断。

**20 裁定：认可该新增钉（PASS）**，无需退回 10-task；SPEC 侧无需修订（沉默面由 task 钉死即够 · 若维护者希望 SPEC 层明示，可在下一 SPEC 修订顺带吸收，非本 task 阻塞）。

---

## 八 · B1 旧测影响面完整性（10 实扫声称 · 20 复扫）

行为变更类 task 须有「旧测 grep 影响面」——B1 节在案（:115-124 · 六文件），满足 checklist 硬性项。本帽独立复扫（grep `get_candidate_capability_ids|CANDIDATE_CAPABILITY_IDS|CAPABILITY_ALLOWLIST_BY_KEY|MINIMAL_READONLY_CAPABILITY_IDS|strategy.config` 全仓 `*.py`）：

**触点全集**：
- 生产面：`builder.py:16,177`（唯一生产调用点 · 与 task R3「无模块级固化消费方」声称一致 ✅）· `strategy/__init__.py:12,20`（re-export · 非消费）
- 测试面：`test_strategy_builder.py`（:12,45,46,50,110,119 + 4 处 patch :74,97,155,186）· `test_strategy_scenario.py:257`（patch）——**均在 B1 清单** ✅
- **漏登一处**：`tests/eval/test_eval_agent_golden.py:32` `_CANDIDATE_PATCH = "app.ops.strategy.builder.get_candidate_capability_ids"`——**不在 B1 六文件清单**。

**漏登影响评估（非阻塞理由）**：①该文件 patch 的是 builder 模块绑定名、整体替换函数——config.py 内部追加 env 的逻辑改动对该 patch 面天然零 diff；②env 默认不设 → 三分支零 diff（§四论证）；③`pyproject.toml:77` `testpaths=["tests"]` → `tests/eval/` 在 TC3 `pytest tests` 全量回归范围内，40 全绿亲跑义务兜底。

**结论**：B1 清单存在且主干完整，漏登一行属非阻塞疏漏 → 落 §十一 nit-1（建议 30 补登 B1 行或在 40 invoke 亲跑记录中显式含 eval golden 文件）。

---

## 九 · 思考轮审查（阶段 C · 控制表 / 回填闭合 / early_stop）

| 核查项 | 结果 |
|--------|------|
| 控制表完整 | ✅ R0–R5 六轮齐 · `actual_last_round`=R5 · early_stop=yes · reason/residual_risks 列齐 |
| 轮回填闭合 | ✅ R0 问题框定（SPEC D3 承接 + 40 invoke :33 实证）· R1 范围/非范围 · R2 方案裁定（SPEC Q4 存续 + 三新增钉）· R3 交叉验证（调用面/图谱/FP-5 链/零 diff 四条实证）· R4 failure_paths 推演（FP-5 + 实操 A–F 七条 → 实际落表 8 行含闸行）· R5 验收机断化收敛 |
| R3 声称复核 | 「builder.py:177 节点内每轮调用」✅ 实读吻合；「config.py:39-45 分支结构」✅；「lg_rag 行 strategy 归属裁定在册」✅（01_modules.md 行 35） |
| early_stop 理由 | 「单文件小改动面 · 裁定全存续 · 锚点实读闭环」——本帽复核：改动面确为 config.py 单文件 + 图谱行备注；SPEC Q4 裁定存续无重开；锚点全实证（§六）。**理由成立 · 风险已在 R2 residual 明示并留 20（§七已裁）** ✅ |
| 回填真实性 | 无「先写结论后编轮次」迹象：R4 推演条数与 failure_paths 表一一对应（含实操-E 零 diff 微差 ↔ TC1 · 实操-F lint 红 ↔ 验收第 5 条） |

**思考轮审查：通过**。

---

## 十 · 流程实证（lint / verify 复跑）

本帽在 worktree（分支 `task/hitl-approval-consumption` · commit 07f9cc1）亲跑：

| 命令 | 结果 |
|------|------|
| `npx spec-wave task lint --file docs/tasks/active/task_hitl_approval_consumption_strategy_env.md` | **LINT: PASS**（EXIT=0） |
| `npx spec-wave verify --target . --task docs/tasks/active/task_hitl_approval_consumption_strategy_env.md` | **EXIT=2 · VERIFY: BLOCKED**——HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸 pending（与 task 人工闸表一致 · **属实时序**：本审查文落盘在先、维护者签闸在后） |

三闸 pending ⇒ **30 拒开工存续**。本帽不代签任何闸；HG-AUDIT-R1 待维护者人签（00 代录）。

---

## 十一 · 阻塞 / 非阻塞清单 与 回填清单

**内容阻塞**：**无**（零阻塞）。

**非阻塞提示（不退回 · 留 30/40 吸收）**：

- **nit-1 · B1 漏登 eval golden 行**：`tests/eval/test_eval_agent_golden.py:32` patch 同一函数 · 未列入 B1 六文件清单。建议 30 在 B1 表补登一行（或 40 invoke 亲跑记录显式含该文件）。TC3 全量回归已兜底（§八）。对应 task 小节：「B1 · 旧测影响面」。
- **nit-2 · 图谱行引文为转述**：task :62 引 lg_rag 行文字省略了「Builder/Intent/Critic ·」片段（原文见 01_modules.md 行 35「路径覆盖补记」段）。语义无损，仅引文精确性提示，无需改 task。
- **nit-3 · TC1① 机断形态建议**：以字面期望 list 断言实现「对 master 逐字节对拍」（§四），30 落地形态提示。

**回填清单（退回 10-task 项）**：**空**——本 R1 无需退回。

---

## 十二 · 裁定

- **内容面：PASS（R1 终轮 · 零内容阻塞 · 签收本 task 书面审查）**——SPEC 承接闭合（§二）· TC1–TC3↔A4/A5/A8 映射闭合（§三）· 零 diff 断言与 FP-5 断言化均可机断（§四/§五）· 锚点全实证（§六）· R2 留转钉认可（§七）· 思考轮通过（§九）。
- **流程闸：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 pending（属实时序）**——30 拒开工存续，维护者签闸后方可下发 30。
- 本轮为 R1 且内容零阻塞 → **签收 / 关闭本审查轮**（如维护者签闸后无 task 改动，无需 R2）。

---

## 维护者签闸清单（00 代录口径）

```text
## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（docs/harness/reviews/task_hitl_approval_consumption_strategy_env_audit_R1_20261010.md · 裁定 PASS · 三 nit 非阻塞）
- [ ] 在 task 人工闸表将 HG-TASK-DRAFT 改为 approved（维护者 · 日期 · 00 代录）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期 · 00 代录）
- [ ] 在 task 人工闸表将 HG-GRAPH-MODULES 改为 approved（维护者 · 日期 · 00 代录 · `graph_change_layer=G-L1` 行备注在册）——承 task_testing_write_capability 先例（维护者口头人签「在册」· 00 代录 · 图谱回写为 30 交付义务随交付落盘）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
```

> 注：HG-GRAPH-MODULES 同属 blocks-30 闸（verify EXIT=2 实证）。task 表「随 30 回写由 00 代录」口径与先例一致——**闸在 30 前签 approved（在册备注 · 00 代录），图谱 lg_rag 行备注的实际回写是 30 交付义务**（task F4 + TC3 已钉）。
