# task_testing_write_capability 审查（R1 · 20-task-audit）

> **审查对象**：`docs/tasks/active/task_testing_write_capability.md`（D2 · behavior 小 task · 免 SPEC · 注册非只读测试 capability 补齐 HITL 全链可审对象 · commit 54c6101）
> **审查帽**：20-task-audit（书面审查 · 未改 task 实质内容 · 未代签任何 human_gate · 未执行 30）
> **日期**：2026-10-09 · **审查时仓态**：worktree `ops-desk-api-worktrees/d2-testing-write-capability` · 分支 `task/testing-write-capability`（base master 57fbf84）· 工作树净
> **开窗授权**：00 委托令「审查帽 20-task-audit 审 D2 task」
> **需求真值**（免 SPEC 依据）：`docs/acceptance/20261009_chat-history-hitl-ux_local_acceptance.md:45` 偏差登记 #1——「阶段 3 真实图挂起 → decide → resume 解锁全链未验（全只读能力面无可审对象）→ 注册非只读测试 capability → 另立 task」（实读确认 :32 全只读/无真实挂起可触发的设计真态记述一致）
> **结论**：**PASS**（内容零阻塞 · 范围/非范围闭合 · 验收可机断 · 锚点全实证 · 思考轮 R0–R5 闭合 · 非阻塞观察项 4 条 · 三流程闸全 pending 待维护者签）

---

## 结论摘要

| 维度 | 结论 |
|------|------|
| task **内容**可执行 | ✅ **PASS · 零内容阻塞**——钉死契约 9 条逐条与源码实证一致；范围 F1–F6 与非范围互斥闭合；验收 A1–A7 均可对命令输出/registry 断言机断；failure_paths 覆盖充分；思考轮控制表完整 early_stop at R5 有理由 |
| **流程闸** HG-TASK-DRAFT | `pending`（blocks 20-R1/30 · 本审查承 00 委托令执行书面审，不代签） |
| **流程闸** HG-AUDIT-R1 | `pending`（本审查文落盘即其前置交付 · 人签后方 approved） |
| **流程闸** HG-GRAPH-MODULES | `pending`（`graph_change_layer=l1` 一致 · blocks 30） |
| lint 复跑 | `npx spec-wave task lint --file docs/tasks/active/task_testing_write_capability.md` → **LINT: PASS** exit 0（2026-10-09 本帽复跑 ✓） |
| draft 洁净度 | ✓ `app/` 内 `allow_write_tags_any` / `OPS_CAPABILITY_ALLOW_WRITE_TAGS` / `testing_write_echo` grep 零命中；manifests/ 仅 builtin.v1.yaml + oa.readonly.v1.yaml（无提前实施） |

本审查文按结论机读口径书写：「结论」起首节 · 通过词落节内 · 实质内容充足 · 无否定共现。

---

## 审查要点逐项核对

### 1. 锚点实证（委托令四锚 + task 现状锚点表 10 行 · 全逐行实读）✅

| 锚点 | 实证结果 |
|------|----------|
| `manifests/builtin.v1.yaml:7-29` | ✓ 字段族范式成立：id/kind/description/when_to_use/when_not_to_use/tags/risk_level/side_effect/enabled/tenant_scoped/args_schema/reversible/execution_type/max_reversal_latency/requires_stop_support/adapter 逐字段齐。⚠ 行窗轻微越界：首枚条目实为 :8-26（:7 为 `capabilities:` 头 · :27-29 已入第二条目）——非阻塞（观察项 O1） |
| `delegation.py:488-514` | ✓ `auto_approve_ok` 三条件逐行实证：① scope 越界 :505-506 ② side_effect ∉ READONLY_SIDE_EFFECTS :507-511（词表 :80 = {none, read} ✓）③ kind ∈ NON_AUTO_KINDS :512-513（:82 = {sandbox, cli} ✓）；函数止于 :514 |
| `nodes.py:277-295` | ✓ 触发链逐行实证：tool 空 :283-285 → None；**tool ∉ effective_scope :287-288 → None（不走 HITL）**；未注册 :289-291 安全默认交人；auto_approve_ok False → 审批原因串 :292-295 |
| `nodes.py:701-726` | ✓ 落点实证：contract gate :693-707 之后；`_delegation_active()` 且 type==tool :710；`blocked["blocked_by"]="delegation_issue_hitl_required"` :714 · `blocked["hitl_required"]=True` :715；审计 `AUDIT_TOKEN_ISSUE_HITL_REQUIRED` :721-725 |
| `nodes.py:252-254` | ✓ `_delegation_active()` = mode != off · 默认 off 逐字节零 diff |
| `baseline.py:33-44` | ✓ `deny_write=True` :43（注 :40-42「第一期只读：写能力在裁剪阶段就不进模型视野」）；两层「显式打开」纪律 :17-18 ✓；DOMAIN_ALLOW_TAGS 语义=豁免 kinds 裁剪 :11-15 ✓（支撑裁定二否掉岔路②） |
| `registry.py:112-133` | ✓ 判序实证：enabled :118 → kinds（allow_tags_any 只豁免本层 :120-125）→ deny_high_risk :126 → **deny_write :128**（WRITE_SIDE_EFFECTS={write,irreversible} · types.py:26 ✓）→ tags_any 收窄 :131-133。新豁免分支落 :128 处不触及 :126 → deny_high_risk 无豁免口的钉死语义在判序上天然成立 |
| `types.py:136-164` | ✓ CapabilityFilter 为 `@dataclass(frozen=True)` · 全字段带默认 → 新增 `allow_write_tags_any=None` 后向兼容；全仓测试 CapabilityFilter 构造 15 处皆关键字传参（grep 实证）→ 加字段零破坏 |
| `manifest.py:54,60,150-165` | ✓ MANIFEST_DIR :54 · `OPS_CAPABILITY_EXTRA_MANIFESTS` :60 · 禁目录扫描纪律 :57 · 默认空→不加载 :155-164 |
| `strategy/builder.py:28` + `nodes.py:92` + `admin/capability.py:179` | ✓ 三处行号全中；BUILDER_CAP_FILTER / _SUPERVISOR_CAP_FILTER 确为模块级常量（import 固化）。⚠ 两瑕疵：task 锚点写「builder.py:28」省略 `strategy/` 路径段（行号内容正确）；「baseline_filter 三使用点」实为 **4 个调用点**——遗漏 `evals/agent/golden/capability/runner.py:120`（node_role="golden"）——非阻塞（观察项 O2：env 读取点在 baseline_filter 内部 · 默认空 → 第四调用点同样零 diff） |
| `hitl/router.py:5-10` | ✓ pending :9 · decide :10 · resume :8 三路由真值 |
| `defaults.py:42-74` | ✓ 罐头范式实证：`mock_get_issue_status` :42-51 · `mock_get_deploy_info` :54-63 · `utc_now_iso` :66-74（docstring「无副作用 · 不连外网」:67 ✓）· 纯函数零 IO |
| `tests/conftest.py:29` | ✓ env setdefault 先例存在（`OPS_CHAT_TRACER`）——钉死契约「对齐 conftest 先例」有据 |

### 2. 起草者自报六裁定 · 逐条核验 ✅（1 条带非阻塞观察）

| # | 自报裁定 | 核验结论 |
|---|----------|----------|
| 1 | 独立 testing.v1.yaml 经 EXTRA_MANIFESTS 显式加载；并入 builtin 破 `test_capability_manifest.py:83` count==5 且 off 非零 diff | ✅ 实证：:83 `assert result.capability_manifest_count == 5` 在；`manifests/` 已有 `oa.readonly.v1.yaml` 独立文件先例（非默认加载 · 测试显式路径加载）——裁定一机制可行性有仓内先例支撑 |
| 2 | 可见性放行=新字段 allow_write_tags_any + env 默认空；与 domain_allowlist:102-112「一个 tag 不换全部豁免」钉死语义一致 | ✅ 实证：:102-112 `test_allow_tags_does_not_waive_deny_write` 断言 allow_tags_any 命中仍被 deny_write 裁；新字段是**显式独立豁免维度**（不触碰 allow_tags_any 语义），且判序上 deny_high_risk(:126) 在 deny_write(:128) 之前、豁免分支只落 :128 → 「deny_high_risk 永不豁免」机械成立；默认 None → `_match_filter` 逐字节零 diff |
| 3 | adapter 落 defaults.py 罐头纯函数零 IO | ✅ 范式实证（见锚点表）；钉死契约禁 import IO 库 + A5 grep 防线 + 零 IO 单测三层闭合 |
| 4 | env 生效时机：模块级常量 import 固化 → 钉死契约足够 30 执行 | ✅ 模块级常量实证（builder.py:28 · nodes.py:92）；钉死契约:82「测试内显式重建 filter · 禁止依赖 import 顺序巧合」+ failure_paths 第 8 行双落，30 可执行无歧义 |
| 5 | B1 旧测影响面 10 文件清单 | ✅ 10 文件锚点全实证（manifest :58-83/:300 ✓ · domain_allowlist :89-112/:129-166/:169-190 ✓ · supervisor_catalog :50-57 成员断言非总数 ✓ · admin_observability :173-200 ✓ · visibility_and_receipts :82+ ✓ · redlines :1745-1884 落 R14/R15 区段 ✓）。⚠ 反向 grep 发现 2 个直接使用面未列：`test_lg_rag_structured_output_p2.py:22-28`（BUILDER_CAP_FILTER 直接用户 · 成员断言）、`test_multi_replica_dualproc.py:723-730`（catalog visible_ids 双实例一致性断言）——均为相对断言 · 默认空下零 diff 成立 · A2④ 全量 pytest 对照 master 基线兜底 → **非阻塞**（观察项 O3：建议 30 亲跑时将两文件并入 B1 执行清单） |
| 6 | graph_change_layer=l1 与 HG-GRAPH-MODULES pending 口径一致 | ✅ 一致：l1 模块内增量（边界不变）对应闸表 pending · blocks 30；graph_delta 落 `docs/_tech_graph/l1/01_modules.md` 与 profile `graph_modules_path` 一致 |

### 3. 范围 / 非范围闭合 ✅

范围 F1–F6（manifest / adapter / filter 字段+豁免分支+env 透传 / 测试 / 图谱 l1 / 验收链证据）与非范围（不改 auto_approve_ok/触发链/HITL 链判定语义 · 不全局松 deny_write · 不开 deny_high_risk 豁免口 · 不动 DOMAIN_ALLOW_TAGS · 不接真实写 · 偏差 #2 compose 形态另立 task · builtin 五枚零改动 · 不动前端/compose）逐条互斥；与验收登记偏差 #1 处置口径逐项对应，无越界项。F2「不进 `_DEFAULT_SPECS`」实证合理（:77 起为硬编码回退表，注册只经 manifest 路径可保 off 零 diff）。

### 4. 验收可机断性（行为变更类加查）✅

| # | 验收 | 可机断性核验 |
|---|------|--------------|
| A1 | enforce 全链（挂起→pending→decide(approved)→resume→done{completed}） | ✓ 逐段对路由真值（router.py:8-10）与 nodes.py:710-726 落点；env 组三枚写成一组（EXTRA_MANIFESTS + ALLOW_WRITE_TAGS + enforce）与 failure_paths「env 半设」互锁；证据落 40 invoke 明确 |
| A2 | off 零 diff | ✓ 四子项均可机断（registry snapshot / 可见集 8 枚——与验收登记 :32「可见集 8 个 tool」真值一致 / count==5 原样绿 / 全量 pytest 对照基线） |
| A3 | 加载≠可见 | ✓ 只设 EXTRA_MANIFESTS → snapshot 含而 baseline 可见集不含，且钉死语义测试原样绿——直接机断 deny_write 未全局松 |
| A4 | 新增测试四面 | ✓ 三例单测（命中/未命中/high risk 不豁免）+ manifest 加载 + 罐头零 IO + enforce 集成断言，复用 hitl fixture 路径明确 |
| A5 | adapter 罐头防线 | ✓ grep 禁词清单 + docstring 关键词 + 40 逐行核，机械可查 |
| A6 | 字段钉死 | ✓ 五字段经 registry 断言机断 |
| A7 | B1 亲跑 | ✓ 命令+结果落 40 invoke；与 A2④ 形成双兜底 |

### 5. failure_paths 充分性 ✅（委托令 8 类逐项在表 · 实 9 行）

闸拒开工 :110 · 可见性被裁预案 :111（含 30 自检断言出口）· 罐头三层防线 :112 · risk high 误标 :113 · off 漂移 :114 · env 半设 :115 · 旧测破 :116（B1+A7 出口）· import 时机 :117 · lint 红 :118——每条均含处置路径，无「只列风险不给出口」项。⚠ 计数瑕疵：表实 **9 行**，R4 小节与 10-invoke 均写「八条」——非阻塞（观察项 O4 · 语义覆盖无损）。

### 6. 思考轮 R0–R5 ✅

槽位 `### R0`–`### R5` 齐 · 控制表表头（轮/结论/early_stop/reason/residual_risks）齐 · `actual_last_round` 行在 · early_stop at R5 有 reason（三裁定各有实证排除岔路 · 触发链与旧测面实读闭环 · 路由真值已核）· residual_risks 回填闭合（R2 判序护栏 → 本审查 §1 registry 判序实证复核通过；R3 env 时机 → 已钉死契约）。R2 三裁定的岔路排除（全局松/DOMAIN_ALLOW_TAGS/enabled=false）均有实证依据，无跳跃。

---

## 非阻塞观察项（不阻 30 · 供维护者/30 参考）

| # | 项 | 性质 |
|---|----|------|
| O1 | `builtin.v1.yaml:7-29` 行窗越界（首枚条目实 :8-26） | 锚点精度瑕疵 · 不影响语义 |
| O2 | 锚点表「builder.py:28」省 `strategy/` 路径段；「baseline_filter 三使用点」漏 `evals/agent/golden/capability/runner.py:120`（第 4 调用点） | 枚举瑕疵 · 默认空 env 下第四调用点同样零 diff |
| O3 | B1 清单漏 `test_lg_rag_structured_output_p2.py`（BUILDER_CAP_FILTER 直接用户）与 `test_multi_replica_dualproc.py:723-730`（catalog 一致性断言） | 影响面枚举不全 · 相对断言+A2④ 全量回归兜底 · 建议 30 并入亲跑清单 |
| O4 | failure_paths 表实 9 行 vs R4/10-invoke 写「八条」 | 计数瑕疵 · 覆盖维度无损 |

## 阻塞项

**无内容阻塞。**

## 回填清单

无（零内容阻塞 · 无退回 10-task 项）。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（本文件）
- [ ] 在 task 人工闸表将 HG-TASK-DRAFT 改为 approved（维护者 · 日期）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] 在 task 人工闸表将 HG-GRAPH-MODULES 改为 approved（维护者 · 日期 · graph_change_layer=l1）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-09 | 20-task-audit R1 落盘：PASS（内容零阻塞 · 非阻塞观察项 O1–O4）· 三流程闸全 pending · 不附 30 Prompt |
