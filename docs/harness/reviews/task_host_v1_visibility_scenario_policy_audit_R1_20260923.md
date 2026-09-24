# 审查文：task_host_v1_visibility_scenario_policy · 20-task-audit R1（2026-09-23）

> **hat_id**：20-task-audit · **轮次**：R1 · **审查对象**：`docs/tasks/active/task_host_v1_visibility_scenario_policy.md`（draft · 264 行）
> **对照真值**：SPEC `docs/spec/host-v1-visibility-scenario-policy/SPEC-host-v1-visibility-scenario-policy_v0.md`（signed · 230 行）· 种子 `08_host_v1_wave_spec_outlines_v0.md` §2 · 03 轨 `03_strategy_and_intent_plan_v0.md`（active）
> **方法**：全部真读真跑——task/SPEC/种子/03 轨逐行读；代码锚点 5 处亲读；grep 亲跑；pytest collect 亲跑；图谱签录链亲读

---

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **FAIL** —— 1 项阻塞（B-1：D2 落点/白名单与钉死顺序自相矛盾，验收不可兼得）+ 5 条非阻塞 nit |
| **流程闸** HG-AUDIT-R1 | **pending（如实）** → 30 拒开工维持；本帽不签发 |

**总结论：FAIL · 退回 10-task**。阻塞项为 task 内部矛盾（非 SPEC 语义错误）：钉死契约要求场景维 stage 2 插于 requested_scope 交集**之后**，而 V1-A 已 merge 的交集实际落在 supervisor 节点（`multi/nodes.py:934-948`），task 却把 D2 接线钉死在 `strategy/builder.py` 且 diff 白名单不含 `multi/nodes.py`——30 无论怎么落地都必挂一条验收。须 10-task 修订落点/锚点/白名单后重交 R2。

---

## 一、阻塞项清单（FAIL 级别）

### B-1 · D2 场景维接线落点与钉死管线顺序自相矛盾（验收 catch-22）

**钉死契约自己的要求**：

- task :86（钉死契约 · 管线顺序 FP-6）：「基线（stage 1）→ requested_scope 交集（V1-A 既有）→ 场景维（stage 2）→ 最终可见集；只收窄不放宽」；failure_paths :124 同款钉死。承 SPEC §5 FP-6（SPEC :172）。

**代码真值（本帽亲读）**：

- 图顺序：`strategy_builder → supervisor`（`app/ops/lg_rag/multi/graph.py:98`）。
- Builder 节点（`app/ops/strategy/builder.py:120-167`）只做 stage 1：baseline_filter 可见集 ∩ candidates → 写 `allowed_capability_ids`（:163-166）；**不读 requested_scope**（此时 supervisor plan 尚未产出，`state.delegation_scope` 尚不存在）。
- requested_scope 交集实际落在 **supervisor 节点**：`app/ops/lg_rag/multi/nodes.py:934-948`（`_parse_requested_scope` → `effective_scope_from_requested(requested_scope, allowed_ids)` :937-939 → 写 `delegation_scope` :940）；state channel 真值 `app/ops/lg_rag/state.py:246-249/:277`。

**task 的矛盾落点**：

- task :68（现状锚点 · D2 接线）：「Builder 两阶段落点 `builder.py:38-59/:74-80`」——亲读现文件，`:74-80` 是 `effective_scope_from_requested` 的 **docstring**（函数 :67-105），不是接线点；
- task :101（范围 D2）：「`strategy/scenario.py` 新纯函数 + **Builder 接线**（stage 2 插于 scope 交集后）」；
- task :196（依赖 · 改造对象）：「`strategy/builder.py`（:74-80 stage 2 接线）」——**未列 `multi/nodes.py`**；
- task :162（验收 D5 · diff 白名单）：「只含 strategy/scenario.py 新增 + strategy/intent.py + strategy/builder.py（stage 2 接线）+ lg_rag/state.py + capability/types.py + capability/manifest.py + manifests/builtin.v1.yaml + 测试/图谱/文档」——**不含 `multi/nodes.py`**。

**后果（不可兼得）**：

- 30 按钉死顺序（:86/:124）实现 → stage 2 必须接在 supervisor 节点交集（nodes.py:937-940）之后 → diff 必含 `multi/nodes.py` → 白名单断言 :162「只含」**必挂**；
- 30 按白名单只在 builder.py 接线 → Builder 运行时 requested_scope 尚不存在（图顺序 builder→supervisor），只能退化为「基线→场景维→scope 交集」→ 违反 :86/:124 钉死顺序 + SPEC FP-6 → 钉死契约**必破**。

**退回回填位置（task 小节标题）**：「现状锚点」D2 接线行（:68）·「范围」D2（:101）·「钉死契约」管线顺序行（:86）·「依赖 · 改造对象」（:196）·「验收标准 D5 · diff 白名单」（:162）。

**建议方向（供 10-task 参考 · 本帽不代决）**：stage 2 接线改钉 supervisor 节点路径（`multi/nodes.py:937-940` 交集之后 · 消费 intent + intent_fallback + delegation_scope/allowlist），白名单补 `multi/nodes.py`；并在 task 注明与 SPEC :71「两阶段管线（Builder 内）」措辞的关系——SPEC FP-6 钉死顺序（SPEC :172）为更锋利锁死语义，若 00 认定该措辞差异触及 SPEC 实质 → 回 10-spec 澄清而非 task 独断。

---

## 二、逐面核对（证据带行号）

### 面 1 · 范围 / 非范围 / 验收 / failure_paths 与 SPEC 一致性 ⚠（B-1 外其余一致）

| 核对项 | task 证据 | SPEC 证据 | 结论 |
|--------|-----------|-----------|------|
| 范围 D1–D5 | task :99-103（实现序 D1→D4→D2→D3→D5） | SPEC §2 :61-117（D1–D5） | 块划分一致；D2 落点矛盾见 B-1 |
| D1 不新增意图字段 · 增 intent_fallback channel | task :99 · 钉死 :84 | SPEC :63-65 | 一致（U2 消解 · 消费既有 risk_hint） |
| D4 四字段 + 三硬规则 + 三档派生 + 存量补齐 | task :100 · 钉死 :89-92 | SPEC :94-106 | 一致（字段/类型/词表/校验三规则/声明优先全对齐） |
| 非范围 | task :109 | SPEC §3 :123-129（七条 ❌） | 全收（HITL 执行侧/意图 schema/会话上下文/动态图/跨进程/freeze/撤销执行器/03 prompt）；task 增「历史文档回改」标准项 |
| failure_paths | task :117-128（12 行：SPEC FP-1~8 + 过程三 + 畸形 intent） | SPEC §5 :167-174（FP-1~FP-8） | FP 八条逐条翻四列语义一致（FP-5 fallback 裂缝 task :121 ↔ SPEC :171；FP-3 灰度+补齐 :122 ↔ SPEC :169；FP-7 声明优先 :125 ↔ SPEC :173）；「畸形 intent 缺键视同 high/unknown」:128 是 task 增补的安全默认，方向与 SPEC Host 权威一致（但计数行未算入，见 N1） |
| 验收 ↔ SPEC §6（10 条） | task :136-162 | SPEC :180-189 | §6-1~7、9 均映射（D1/D2/D3/D4/D5）；§6-8 冻结回归与 §6-10 PR/CI 无独立勾选（orchestration/白名单隐含承载 · 见 N4） |
| 种子/03 轨方向偏离 | task 全文 | 种子 08 §2 :76-104（B1/B2 → D 块）· 03 轨 :115（风险档）· :142（S2 intent-schema-v1 #80 MERGED） | 零偏离；Q1/Q2/Q3 已由 SPEC 作答未重开；「风险档对齐 03」实证成立（risk_hint 代码真值 `schemas/intent.py:25-28` 亲读） |

### 面 2 · R0–R5 思考轮控制 ✅（1 处计数 nit）

- 控制表 task :221-226：R0–R5 齐全 · early_stop 全 no · residual 两条（观察期报告质量 · 误判靠台账复盘）如实携带至 R5/:228。
- R2 :223 正确「继承 SPEC §4 三组裁定不重演」。
- **N1（nit）**：R3 :224 与 R3 小节 :244 称「failure_paths **11 条**（FP-1~8+过程三）」，正文 :117-128 实为 **12 行**（多出「畸形 intent」:128——R3 小节自己也把它当增补边界叙述，却未计入计数）。

### 面 3 · 验收可执行断言（防空真）⚠（计数 nit + B-1 殃及白名单条）

- 实点勾选：人工闸 1（:134）+ D1×2（:138-139）+ D2×3（:143-145）+ D3×1（:149）+ D4×4（:153-156）+ D5×3（:160-162）= **14 条**，另变异检验 3 条（:166-168）。
- **N2（nit）**：R4 :225、自检 :256 与本文标题均称「验收 **16 条**」——实际 14（+3 变异 = 17），任一口径都不是 16；R4 自给的分解式（1/2/3/1/4/3）加总即为 14，自称与分解式自相矛盾。
- 断言质量本身达标：裁剪矩阵五行规则逐行否定断言（:143）· 畸形 intent 安全默认（:144）· 三档（:145/:155）· ManifestError 三硬规则（:153-154）· builtin 全覆盖（:156）· 变异检验三条（安全默认/校验/台账 · :166-168）满足不验收空真。
- D5 白名单条（:162）因 B-1 成为不可满足断言，随 B-1 一并退回。

### 面 4 · B1 旧测影响面处置三态 ✅

- 三态齐全：回归×5 组（:176-180）· 新增×1（:181 两个新测试文件）· 迁移无×1（:182）。
- **亲跑复核**：`ls tests/ | grep -iE 'strategy|intent|manifest|baseline|scenario|visibility|capability|lg_rag_multi|builder|policy'` → **19 文件**（与 :172 一致）；组计数核验：g1×1 + g2×2 + g3×2 + g4×11（14 个 capability 面 − g3 的 2 个 manifest − g5 的 admin_observability）+ g5×3 = 19 ✓，无缺漏无重复。
- 组 2 诚实标注「节点返回 dict 多一键 · 既有断言若按精确匹配须复核——30 逐条核」（:177），组 3 标注 builtin 计数断言风险（:178）——旧测影响面预判诚实，加分项。

### 面 5 · 钉死契约与 SPEC §2/§4/§5 锁死一致 ⚠（B-1 外一致）

| 钉死项 | task | SPEC | 结论 |
|--------|------|------|------|
| D1 intent_fallback channel · IntentV1 零改动 | :84 | SPEC :63-65 | 一致 |
| S1–S5 规则表（fallback→∅ / needs_tool=False→∅ / unknown+needs_tool→∅ / high 剔 medium / low·medium 不追加）· is_composite/summary 不作键 | :85 | SPEC :77-83 | 逐行一致 |
| 管线顺序 基线→scope 交集→场景维 | :86 | SPEC FP-6 :172 | 语义一致 · **落点矛盾见 B-1** |
| 三档模式双开关 · 非法回退 off | :87 · :91 | SPEC :52 · :84 · :104 | 一致 |
| 剔除台账 logger+span · id+reason+计数 · off 零日志 | :88 | SPEC :89-90 | 一致 |
| 四字段定义 + execution_type 三值词表 | :89 | SPEC :96-101 · Q3 :153-157 | 一致 |
| 加载期三硬规则（非法词表/矛盾 irreversible+reversible=true/process 无 stop） | :90 | SPEC :103 · :157-159 | 一致 |
| 缺失默认 HITL 三档 · 显式声明不派生 | :91 | SPEC :104-105 · FP-7 :173 | 一致 |
| builtin 全量补齐 | :92 | SPEC :105 | 一致 |
| 图谱两行备注 · 零新一级模块 | :93 | SPEC :21 | 一致 |

### 面 6 · 闸表四行诚实 ✅

| 闸 | task 表 :39-42 | 本帽复核 | 结论 |
|----|----------------|----------|------|
| HG-TASK-DRAFT approved（00 代录 · 双令） | :39 | 与 SPEC :4 状态行双令原话一致（首令承 invoke :5-6 · 次令「继续…下一波」SPEC/task 留痕一致） | 诚实 |
| **HG-AUDIT-R1 pending（blocks 30）** | :40 | 本审查文落盘前确为 pending；本帽不代签 | **诚实 · 维持 pending** |
| HG-GRAPH-MODULES approved | :41 | 亲读 `01_modules.md`：签录链末行 = 2026-09-23 **V1-A 回写行**（task_host_v1_delegation_token · 00 代录 ratify）；capability/lg_rag 行在表 | 诚实 |
| HG-PILOT-OPSDESK-GLAYER n/a | :42 | 不涉物理分层试点 | 诚实 |

---

## 三、代码锚点抽验（抽 5 亲读）+ 命名冲突/基线亲跑

| # | 锚点 | 复核结果 |
|---|------|----------|
| 1 | `schemas/intent.py:25-28` | ✅ 亲读：`risk_hint: Literal["low","medium","high"]` :25-28 · default low · 「不得绕过 Policy」description 在案；U2 消解声明属实（零消费者由 task 全文及 SPEC :40 一致佐证） |
| 2 | `strategy/intent.py:22-24 · :52-92` | ✅ 亲读：`fallback_intent_dict()` :22-24 返回 `IntentV1()` 默认 → risk_hint="low"（**裂缝属实**）；`intent_node` :52-92 · span `"intent_fallback": fallback` 在 :86 · 返回仅 `{**bump, "intent"}` :92（channel 增写落点成立） |
| 3 | `strategy/builder.py` | ⚠ 亲读：`build_allowlist_from_candidates` 现 :39-60（task 写 :38-59 · V1-A 合入后 +1 行漂移 · N3）；stripped 审计现 :53-59；`effective_scope_from_requested` :67-105 · MAX_SCOPE_IDS :63-64 均在；**但 :74-80 是该函数 docstring 而非接线点**，且 requested_scope 交集不在本文件（在 multi/nodes.py:934-948）——支撑 B-1 |
| 4 | `capability/types.py:72-118` | ✅ 亲读：`CapabilitySpec` frozen dataclass :71-118 逐行吻合；两维不可互代 :7-13 · hitl_required 加载期强校验注 :95-96 在案；现无可撤销性四字段（扩字段落点成立） |
| 5 | `capability/manifest.py` | ✅ 亲读：单文件整文件失败不留半套 :13-14 · 禁热加载 :17-19 · ManifestError :110 · V10 output_schema 校验 :264-309 · V11 fallback 校验 :317+ 先例在案（task :71/:199 称 V9/V10 先例 · V9 visibility 强校验由 types.py:107-110 注与 manifest 校验面佐证） |
| 6 | 命名冲突扫 | ✅ 亲跑：`scenario_trim|execution_type|max_reversal_latency|requires_stop_support` 于 app/tests **零命中**；`\breversible\b` 词边界 app 零命中（裸 reversible 命中均 irreversible 子串 · task :74 排除声明属实）；`intent_fallback` 仅 intent.py:86 span 一处（同名 channel 对齐零冲突） |
| 7 | 测试基线 | ✅ 亲跑 `pytest tests --collect-only -q` → **1420 collected**（与 :75 一致；较 V1-A 时 1368 净增 52 · V1-A 已合入佐证） |
| 8 | V1-A 前置 | ✅ `app/ops/capability/delegation.py` 存在 · `docs/tasks/done/task_host_v1_delegation_token.md` 存在 · state.py delegation_scope/delegation_token channel :246-249/:277-278（task :73 先例属实） |
| 9 | 当前分支 | ✅ master；task :232 如实声明 30 须切分支 |

---

## 四、非阻塞 nit 清单（随 B-1 退回一并回填）

| # | 内容 | 建议处置 |
|---|------|----------|
| N1 | R3 行（:224）与 R3 小节（:244）称「failure_paths 11 条」，正文实为 12 行（8 SPEC + 3 过程 + 1 畸形 intent :128） | 改计数为「12 条（8+3+1）」并点名畸形 intent 增补行 |
| N2 | 「验收 16 条」（标题/R4 :225/自检 :256）与实际勾选 14 条不符（+3 变异=17 亦非 16）；R4 分解式 1+2+3+1+4+3 自加总即 14 | 统一为实际数（14 + 变异 3） |
| N3 | 锚点行号漂移：build_allowlist :38-59 → 现 :39-60；stripped 审计 :54-58 → 现 :53-59（V1-A 合入所致）；另 :68/:196 的「:74-80 接线点」实为 docstring（随 B-1 一并重钉） | 行号按现文件重钉 |
| N4 | SPEC §6-10「PR+CI merge」与 §6-8/D5-8「冻结回归（SSE 零新事件等）」无独立验收勾选（orchestration :32 与 freeze_id/白名单隐含承载） | 建议 D5 补注显式化映射（与 V1-A 审查 N4 同款） |
| N5 | task :192 称 03 轨「risk_hint 真值」——03 plan 文本无 risk_hint 字面（:115 仅「风险档」方向），真值载体是 S2 done task（#80）+ 代码；实质正确但指针可更准 | 依赖行改写「03 轨 S2（task_intent_schema_v1 · #80）落地 risk_hint · 代码真值 schemas/intent.py:25-28」 |

---

## 五、纪律自查

- 本帽未改 task/SPEC 实质内容 · 未动 `app/` 代码 · 未签发任何 human_gate。
- HG-AUDIT-R1 仍 **pending**（task :40）；因结论 FAIL（内容阻塞），按帽规**不附 30 Prompt、不指示 30 开工**，下一棒 = **10-task**。

## 退回 10-task 回填清单

1. **B-1（阻塞）**：重钉 D2 stage 2 接线落点（建议 supervisor 节点 `multi/nodes.py` 交集之后）· 同步修订「现状锚点 :68」「范围 D2 :101」「钉死契约 :86」「依赖 · 改造对象 :196」「验收 D5 白名单 :162」；注明与 SPEC :71「Builder 内」措辞关系（触及 SPEC 实质 → 回 10-spec）。
2. **N1**：failure_paths 计数 11 → 12。
3. **N2**：验收计数 16 → 14（+变异 3）。
4. **N3**：builder 锚点行号按现文件重钉。
5. **N4**：D5 补注 SPEC §6-8/§6-10 映射。
6. **N5**：03 轨依赖行指针精确化。

回填后重交 20-task-audit R2。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-09-23 | 20-task-audit R1：六面全核 + 锚点 5+4 亲读亲跑（grep 零真冲突 · pytest 1420 · 图谱末行=V1-A 回写行）→ **FAIL**（阻塞 B-1：D2 落点/白名单与钉死顺序自相矛盾 · 验收 catch-22）+ N1–N5 · 退回 10-task · HG-AUDIT-R1 维持 pending |
