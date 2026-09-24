# Task：Agent Host V1-B · 可见集两阶段 + manifest 可撤销性四字段（场景维裁剪 scenario_trim + 剔除台账 + 四字段 schema/加载期校验/缺失默认 HITL）（host-v1-visibility-scenario-policy）

> **状态**：`active`（2026-09-23 · 20-task-audit **R2 PASS-WITH-NITS**（零阻塞 · N-R2-1 已微修）· HG-AUDIT-R1=**approved** 00 代录 · 30 可委派开工）  
> **类型**：feature（治理面增强 · **零 alembic 义务**（零新表零列 · SPEC §3 锁死）· **有图谱义务按实判**（capability/lg_rag 行备注 + 人签新行 00 代录位 · 不新增一级模块））  
> **上游 SPEC**：`docs/spec/host-v1-visibility-scenario-policy/SPEC-host-v1-visibility-scenario-policy_v0.md`（**signed** · HG-SPEC-SIGNOFF=approved 2026-09-23 · 00 代录 · Q1 3 档对齐 03 / Q2 仅意图+健康度 / Q3 execution_type 正交映射签收锁死）  
> **前波**：`docs/tasks/done/task_host_v1_delegation_token.md`（V1-A CLOSE · PR #179 · requested_scope 是本波裁剪输入）  
> **分支**：`task/host-v1-visibility-scenario-policy`（**禁止 master/main 直改 · 30 由 00 委派子 Agent 执行**）  
> **10 注**：2026-09-23 · 本棒由 00 亲起（无初稿时起草第一步 · 承 harness-00-delegate-only 例外条款）；HG-AUDIT-R1 落稿时待签（10 帽不签）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `host-v1-visibility-scenario-policy` |
| **git_branch** | `task/host-v1-visibility-scenario-policy` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 两阶段裁剪矩阵断言（S1–S5 × risk_level 组合 × requested_scope 交集）· 安全默认断言（fallback/歧义→空集+台账）· 剔除台账 caplog/span 双通道 · 四字段加载期校验（非法 ManifestError · 矛盾拒 · process 无 stop 拒）· 缺失默认 HITL 三档（off/observe/enforce）· builtin 四字段全覆盖 · off 零 diff |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` 行备注（`capability` 行：manifest 四字段 schema+加载期校验+缺失派生 HITL · `lg_rag` 行：场景维第二阶段裁剪+剔除台账+intent_fallback channel；**不新增一级模块**（strategy 承 C2 裁定归属 lg_rag 行）；HG-GRAPH-MODULES 随 30 交付 00 代录） |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md`（capability 与 lg_rag 两行备注 + 人签新行 · 零新一级模块 · 零新跨模块边） |
| **graph_delta_note** | **回炉补闸条款**：若 30 实现形态偏离本预判（新增一级模块 · 新增表/列触发 alembic · 新增 SSE 事件类型 · 新增 HTTP 路由 · 改 freeze 契约 · 改意图 schema/IntentV1 字段 · 改基线 filter 既有语义），不得沿用本裁定——退回 10-spec/10-task 补闸 + `docs/_tech_graph/` 如实登记后续做 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 契约真值在 SPEC `host-v1-visibility-scenario-policy`；builder/scenario docstring 同步属范围项非 wiki |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 单 task 直通：10 落稿 → 20-task-audit → HG-AUDIT-R1（00 代录）→ 30（00 委派子 Agent · 实现序：D1 intent_fallback channel → D4 四字段 schema+加载校验 → D2 scenario_trim+Builder 接线 → D3 台账 → D5 断言收口）→ 40 → PR+CI 绿+merge → 图谱回写（00 代录）→ CLOSE |
| **freeze_id** | 无（manifest 向后兼容演进 · 不改 lg-rag-sse-v1 / lg-rag-http-v1 / lc-evidence-http-v1 · SSE 零新事件类型 · 零新路由） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20-R1, 30 | 2026-09-23 · 00 代录（维护者令原话：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」+ 本窗令「继续，完成后自行进行下一波，无特殊情况无需停下等待接收命令」） |
| HG-AUDIT-R1 | **approved** | **30** | 2026-09-23 · **00 代录**（维护者令原话：「签收，并生成对此长程任务的00启动Prompt，新窗口执行，授权00签收所有过程文档，完整落地1.0版本内容」+ 本窗令「授权00可以签收所有过程文档」「继续，完成后自行进行下一波，无特殊情况无需停下等待接收命令」）；依据：20-task-audit **R2 PASS-WITH-NITS** 零阻塞（`docs/harness/reviews/task_host_v1_visibility_scenario_policy_audit_R2_20260923.md` · B-1 catch-22 消解经交换律数学核验 · N1–N5 闭环）；R1 FAIL 经 10-spec 澄清+回填后 R2 通过；N-R2-1 残留 nit 已微修留痕（修订记录） |
| HG-GRAPH-MODULES | approved | **30** | 2026-09-23 真读 `docs/_tech_graph/l1/01_modules.md`：模块表已建置（签录链完整至 2026-09-23 V1-A 回写行）；`capability`/`lg_rag` 行在表；图谱新签义务（两行备注 + 人签新行 00 代录位）**随 30 交付落盘**；不新增一级模块 |
| HG-PILOT-OPSDESK-GLAYER | n/a | 物理分层试点改码 | 本 task 不涉物理分层试点改码 |

---

## 背景与目标

现状（SPEC §1 锁死 · 本帽复核一致）：Builder allowlist 是身份维单阶段（`baseline.py:33-44` 基线 deny_high_risk+deny_write 已只读）；`IntentV1.risk_hint` 三档已在（`schemas/intent.py:25-28` · U2 消解）但**无任何消费者**；`intent.py:22-24` fallback 默认 `risk_hint="low"` 是安全裂缝；manifest 无可撤销性声明。

一句话目标（SPEC 锁死）：可见集升级两阶段——身份维（既有基线）→ 场景维（`scenario_trim` 确定性收窄 · 安全默认宁可无工具 · 剔除项进台账）；manifest 四字段 schema 化 + 加载期强制校验 + 缺失默认 HITL 三档灰度。

设计纪律（30 不得违反 · 承 SPEC §1 签收锁死）：

1. **Host 权威**：`scenario_trim` 纯代码零 LLM 零 IO 可重放；裁剪键只取意图字段+fallback 标记；策略键不可由模型写入。
2. **默认关双开关**：`LG_RAG_VISIBILITY_SCENARIO_MODE`（场景维）与 `OPS_CAPABILITY_REVERSIBILITY_MODE`（四字段缺失默认 HITL）各 off|observe|enforce 默认 off；非法值回退 off。
3. **审计记动作不记内容**：剔除记 id+reason 码+计数；缺失记 undeclared 标记；不记 query/intent 原文。
4. **与 03 轨边界**：IntentV1 字段零改动（只消费 risk_hint）；prompt 资产 `lg_rag.intent.system` 零改动。
5. **零 freeze 动**：不改 freeze 契约 · SSE 零新事件 · 零新路由 · 零新表；manifest 演进向后兼容（缺字段不报错）。

---

## 现状锚点（只读 · 30 必读 · 10 已扫）

| 主题 | 路径 · 锚点 | 现状 |
|------|-------------|------|
| 意图风险档（**D1 消费对象**） | `app/ops/lg_rag/schemas/intent.py:25-28` | `risk_hint: Literal["low","medium","high"]` 已在 · 零消费者 |
| fallback 裂缝（**D1/S1 关键**） | `app/ops/strategy/intent.py:22-24/:52-92` | fallback_intent_dict() 默认 risk_hint=low；span 已记 `intent_fallback`（:86 · 同名 channel 对齐）；节点返回仅 `{**bump, "intent": intent}`——需增 `intent_fallback` channel |
| Builder 两阶段落点（**D2 接线 · R1 B-1 修正行号**） | `app/ops/strategy/builder.py:39-60`（build_allowlist_from_candidates · stripped 审计先例 :55-59）· `:63-75`（effective_scope_from_requested · MAX_SCOPE_IDS=64） | V1-A 已升级「声明∩裁剪」；**场景维 stage 2 落 Builder**（基线→有效可见集 · 意图图序已可得） |
| supervisor 交集真值（**D2 令牌面接线 · R1 审查 B-1 补锚**） | `app/ops/lg_rag/multi/nodes.py:933-948` | V1-A 已 merge：`effective_scope_from_requested(requested_scope, allowed_ids)`（:937）写 `delegation_scope`（:940）；requested_scope 仅在 supervisor LLM 产出后存在——**本波交集输入改场景维后有效可见集** |
| stage 1 基线（**不改动对象**） | `app/ops/capability/baseline.py:33-44` | baseline_filter deny_high_risk+deny_write（Builder/Supervisor 共用单一真相） |
| CapabilitySpec（**D4 扩字段对象**） | `app/ops/capability/types.py:72-118` | frozen dataclass；risk_level/side_effect 两维不可互代（:7-13）；hitl_required 加载期强校验（write/irreversible/high 必须 True :95-96） |
| manifest 加载校验面（**D4 落点**） | `app/ops/capability/manifest.py` | 单文件整文件失败不留半套（:13-14）· 多文件隔离 · 禁自动热加载（:17-19）；V9 visibility 声明强校验/V10 output_schema 校验先例在案 |
| builtin manifest（**D4 存量补齐对象**） | `app/ops/capability/manifests/builtin.v1.yaml` | 全量能力四字段补齐（数据面） |
| state channel 先例 | `app/ops/lg_rag/state.py`（V1-A） | delegation_scope/delegation_token 两 channel 先例（可选键形态） |
| 命名冲突扫 | grep `scenario_trim\|reversible\|execution_type\|max_reversal_latency\|requires_stop_support` 于 app/tests | **零真冲突**（命中均 `irreversible` 子串 · `intent_fallback` 与既有 span 同名对齐） |
| 测试基线 | `.venv/bin/python -m pytest tests --collect-only -q` | **1420 collected**（2026-09-23 本帽真跑） |
| alembic 义务 | 无 | 零新表零列；迁移 diff 为空入验收断言 |

---

## 钉死契约（自 SPEC §2/§4/§5 锁死；30 不得静默改义）

| 项 | 钉死 |
|----|------|
| **意图消费（D1）** | IntentV1 字段零改动；`intent_node` 增写 `intent_fallback: bool` channel（state 可选键 · 承 V1-A 先例）；档位口径进 builder/scenario docstring |
| **scenario_trim（D2）** | 新纯函数 `app/ops/strategy/scenario.py`：`(base_visible, intent, intent_fallback) -> (final_visible, stripped[(id, reason)])`；规则表 S1 fallback→∅ · S2 needs_tool=False→∅ · S3 domain=unknown+needs_tool→∅ · S4 risk_hint=high→剔 risk_level=medium · S5 low/medium 不追加；`is_composite`/`summary` 不作裁剪键 |
| **管线与落点（FP-6 · SPEC R1 B-1 澄清）** | 语义=三重交集（基线 ∩ 场景维 ∩ requested_scope · 交换律等价 · 只收窄不放宽）；落点按数据可得性：**Builder 内** 基线→scenario_trim→有效可见集（供 supervisor 规划）· **supervisor 节点内**（`multi/nodes.py:933-948`）`delegation_scope = requested_scope ∩ 有效可见集`（V1-A 交集输入由裸 allowlist 改为场景维后有效可见集 · 本波对 V1-A 唯一接线改动） |
| **模式（D2）** | `LG_RAG_VISIBILITY_SCENARIO_MODE=off\|observe\|enforce` 默认 off；observe 记 `would_strip` 不生效；非法回退 off |
| **剔除台账（D3）** | logger + span 双通道；id+reason 码+计数；off 零日志 |
| **四字段（D4）** | `CapabilitySpec` 增 `reversible/execution_type/max_reversal_latency/requires_stop_support`（默认 None=未声明）；execution_type ∈ instant\|target\|process |
| **加载期校验（D4）** | 非法类型/词表 → ManifestError 整文件失败；`side_effect=irreversible`+`reversible=true` → ManifestError；`execution_type=process` 且 `requires_stop_support` 非 true → ManifestError；缺字段不报错 |
| **缺失默认 HITL（D4）** | `OPS_CAPABILITY_REVERSIBILITY_MODE=off\|observe\|enforce` 默认 off；observe 台账 `reversibility_undeclared would_default_hitl`；enforce 未声明能力 `hitl_required` 派生 True（**显式声明合法 → 不派生** · FP-7） |
| **存量补齐（D4）** | builtin.v1.yaml 全量能力补四字段（enforce 升级路径零误伤） |
| **图谱** | capability/lg_rag 行备注 + HG-GRAPH-MODULES 人签新行（**00 代录位**）；`./scripts/graph-compile.sh` 绿；零新一级模块 |

---

## 范围（单 task 直通 · SPEC §2 D1–D5）

- [ ] **D1 · intent_fallback channel（必做）**：`intent_node` 返回增 `intent_fallback`；`state.py` 增 channel；span 同名对齐（:86 已有）
- [ ] **D4 · manifest 四字段（必做）**：CapabilitySpec 扩字段 + manifest.py 加载校验（非法/矛盾/process-stop 三硬规则）+ 缺失派生三档 + builtin.v1.yaml 全量补齐
- [ ] **D2 · 场景维裁剪（必做 · 核心）**：`strategy/scenario.py` 新纯函数 + Builder 接线（stage 2：基线→有效可见集）+ supervisor 接线（`nodes.py:933-948` 交集输入改有效可见集）+ 三档模式
- [ ] **D3 · 剔除台账（必做）**：logger + span 双通道（id+reason+计数）
- [ ] **D5 · 测试与图谱（必做 · 否决面）**：SPEC §2 D5 八组断言全落 + 图谱两行备注 + HG-GRAPH-MODULES 人签新行（00 代录）+ graph-compile 绿

**竖切结论**：D1→D4→D2→D3→D5 同 task 一次提交；scenario_trim 不配安全默认（S1/S3）= 裁剪无底线；不配台账 = 剔除不可复盘（#11 清单落空）；四字段不配加载校验 = 声明面裸奔。耦合面可控（两个新文件 + 四处接线 + manifest 数据 + 测试/图谱）。

### 非范围

承 SPEC §3（锁死 · 越任一条即回炉）：HITL 三档执行侧体系 · 意图 schema 演进（IntentV1 零改动）· 会话上下文参与裁剪 · 动态 StateGraph · 跨进程可见集下发 · 改 freeze/新 SSE 事件/新路由/新表 · 撤销执行器 · 改 03 prompt 资产 · 历史文档回改。

---

## failure_paths

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| `HG-AUDIT-R1` 未签即 30 | **拒开工** | 是 | 是 |
| B1 旧测影响面未逐条处置即 30 交付 | **拒收**（闸前置） | 是 | 是 |
| 验收缺裁剪矩阵/安全默认/台账/四字段校验/三档/全覆盖/零 diff/变异检验任一 | **拒收**（防空真规则） | 是 | 是 |
| **意图风险档误判过度裁剪**（SPEC FP-1） | 安全默认方向正确（宁缺毋滥）；误判进剔除台账可复盘；observe 期 would_strip 报告后再 enforce | 是 | 否 |
| **fallback 裂缝**（SPEC FP-5 · SO 失败默认 low 虚假宽松） | S1 规则：`intent_fallback=True` → 空集 + 台账；断言化（fallback→∅） | 是（重试请求） | 是（无工具退化 · 既有 rag fallback 承接） |
| **存量 manifest 默认 HITL 误伤**（SPEC FP-3） | 三档灰度：off→observe 台账→enforce；enforce 前 builtin.v1.yaml 四字段全量补齐（本波义务） | 是 | 否 |
| **裁剪耗时**（SPEC FP-4） | 纯代码无 IO <10ms · 注记级 smoke 断言 | — | 否 |
| **叠加顺序歧义**（SPEC FP-6） | 钉死：基线→scope 交集→场景维；只收窄不放宽；矩阵断言覆盖 | — | 否 |
| **派生与显式声明冲突**（SPEC FP-7） | 声明优先：显式合法四字段 → 不派生；断言化 | — | 否 |
| **03 轨风险档演进冲突**（SPEC FP-2） | 以现行 risk_hint 三档为准；03 改口径 → 对齐回 10-spec | — | 否 |
| **observe→enforce 灰度误伤**（SPEC FP-8） | 双开关独立灰度；enforce 前观察期报告 | 是 | 否 |
| **畸形 intent dict**（键缺失/类型错） | 缺 `risk_hint` → 视同 high（安全默认收紧）；缺 `domain` → 视同 unknown（S3 生效）；断言化 | 是 | 否 |

---

## 验收标准

- [ ] 人工闸：HG-AUDIT-R1 approved 后方可勾选下列码项（图谱新签义务随 30 交付落盘 00 代录；**30 偏离预判 → 回炉补闸条款生效**）

### D1 · intent_fallback（映射 SPEC §6-1/2）

- [ ] `intent_node` 写 `intent_fallback` channel；SO 成功=False · SO 失败/异常=True（断言）
- [ ] IntentV1 字段零改动（schema diff 为空断言）

### D2 · 场景维裁剪（映射 SPEC §6-1/2）

- [ ] 裁剪矩阵断言：S1 fallback→∅ · S2 needs_tool=False→∅ · S3 unknown+needs_tool→∅ · S4 high→剔 medium 留 low · S5 low/medium 不追加；含 requested_scope 交集叠加
- [ ] 畸形 intent：缺 risk_hint→视同 high；缺 domain→视同 unknown（断言）
- [ ] 三档模式：off=现状零 diff · observe=would_strip 不生效 · enforce=剔除生效

### D3 · 剔除台账（映射 SPEC §6-3）

- [ ] 剔除项 id+reason+计数进 logger（caplog 断言）+ span metadata 断言；不含 query/intent 原文；off 零日志

### D4 · manifest 四字段（映射 SPEC §6-4/5/6）

- [ ] 非法值（execution_type 词表外/类型错/负时延）→ ManifestError 整文件失败
- [ ] 矛盾声明（irreversible+reversible=true）→ ManifestError；process 无 stop → ManifestError
- [ ] 缺失默认 HITL 三档：off 无行为 · observe 台账 · enforce 派生 hitl_required=True 且显式声明不派生
- [ ] builtin.v1.yaml 四字段全覆盖断言

### D5 · 图谱 / 工程（映射 SPEC §6-7/8/9/10）

- [ ] 零 alembic（迁移 diff 为空断言）；capability/lg_rag 行备注 + HG-GRAPH-MODULES 人签新行（00 代录）；`./scripts/graph-compile.sh` 绿
- [ ] 全量 `pytest tests` 绿（基线 **1420 collected** · 无既有用例删除 · 新增数如实入 40）；`ruff check app tests` 净增 0
- [ ] 生产路径 diff 白名单：`git diff master -- app/` 只含 strategy/scenario.py 新增 + strategy/intent.py（fallback channel）+ strategy/builder.py（stage 2 接线）+ lg_rag/multi/nodes.py（:933-948 交集输入改有效可见集 · R1 审查 B-1 补列）+ lg_rag/state.py（channel）+ capability/types.py（四字段）+ capability/manifest.py（校验+派生）+ manifests/builtin.v1.yaml（数据补齐）+ 测试/图谱/文档
- 注记（承 SPEC §6-8/§6-10 · 不计验收计数 · R1 审查 N4）：SSE 零新事件/零新路由由 off 零 diff + B1 组 5 回归覆盖；PR+CI 绿+merge 由 orchestration 流程承载（承「PR 过 CI 自动 merge」先例）

### 变异检验（不验收空真规则）

- [ ] ① **安全默认可检**：临时 S1 规则放行（fallback 不空集）→ 安全默认断言必挂；恢复后全绿
- [ ] ② **校验可检**：临时摘除矛盾声明校验 → ManifestError 断言必挂；恢复后全绿
- [ ] ③ **台账可检**：临时摘除剔除台账 → caplog 断言必挂；恢复后全绿

### 旧测影响面清单（B1 · 2026-09-23 10-task 实扫落盘）

> 扫描口径（真跑）：`ls tests/ | grep -iE 'strategy|intent|manifest|baseline|scenario|visibility|capability|lg_rag_multi|builder|policy'`（命中 19 文件归并 6 组）· 命名冲突扫零真冲突 · 基线 1420 collected

| # | 锚点 | 本波影响 | 处置 |
|---|------|----------|------|
| 1 | `tests/test_strategy_builder.py` | Builder 守护；场景维默认 off + S2/S5 承接既有行为 → 零改动全绿；新增未声明兼容断言在 V1-A 已立 | 回归（零改动） |
| 2 | `tests/test_intent_node.py` · `test_intent_schema.py` | intent 守护；schema 零改动 · 节点增 channel（返回 dict 多一键 · 既有断言若按精确匹配须复核——30 逐条核） | 回归（零改动预判 · 30 复核精确匹配断言） |
| 3 | `tests/test_capability_manifest.py` · `test_capability_manifest_http.py` | manifest 校验守护；新校验只拒非法/矛盾声明 · 既有合法 manifest 不受影响；builtin 补齐后加载断言同步 | 回归（零改动 · builtin 数据面变化须同步断言若涉计数） |
| 4 | `tests/test_capability_gateway.py` · `test_capability_policy.py` · `test_capability_visibility_and_receipts.py` · `test_capability_domain_allowlist.py` · `test_capability_delegation.py` 等 capability 面（11 文件） | CapabilitySpec 扩字段默认 None 向后兼容 → 零改动全绿 | 回归（零改动） |
| 5 | `tests/test_lg_rag_multi.py` · `test_lg_rag_supervisor_capability_catalog.py` · `test_admin_capability_observability.py` | supervisor/admin 观测守护；场景维 off 零 diff → 零改动全绿 | 回归（零改动） |
| 6 | 新增义务：`tests/test_strategy_scenario.py`（裁剪矩阵/安全默认/畸形 intent/三档/台账/变异检验①③）+ `tests/test_capability_reversibility.py`（四字段校验/三档派生/builtin 全覆盖/变异检验②） | — | 新增（用例数如实入 40 记录） |
| 7 | alembic 链 | 本波**无迁移义务**（零新表零列 · SPEC §3 锁死） | 无（迁移 diff 为空断言入 D5） |

---

## 依赖

| 依赖 | 说明 |
|------|------|
| SPEC | `docs/spec/host-v1-visibility-scenario-policy/SPEC-host-v1-visibility-scenario-policy_v0.md`（signed · Q1/Q2/Q3 裁定锁死） |
| 规划/种子 | `docs/spec/agent-infra/07_host_v1_landing_plan_v0.md` · `08_host_v1_wave_spec_outlines_v0.md` §2（双 signed） |
| 03 策略轨 | `docs/spec/agent-infra/03_strategy_and_intent_plan_v0.md`（active · S1–S4 CLOSE）；**risk_hint 真值载体** = `docs/tasks/done/task_intent_schema_v1.md`（S2 · PR #80 MERGED）+ 代码 `app/ops/lg_rag/schemas/intent.py:25-28`（R1 审查 N5 精确化） |
| 前波 | `docs/tasks/done/task_host_v1_delegation_token.md`（V1-A CLOSE · requested_scope/effective_scope 真值） |
| 编码规范 | `docs/standards/CODING_BACKEND_L2_v1_zh.md` |
| 图谱 | `docs/_tech_graph/l1/01_modules.md`（2026-09-23 真读核验 · capability/lg_rag 行 · 签录链至 V1-A 回写行） |
| 改造对象 | `app/ops/strategy/scenario.py`（新增）· `strategy/intent.py`（:52-92 fallback channel）· `strategy/builder.py`（:39-75 stage 2 接线）· `lg_rag/multi/nodes.py`（:933-948 交集输入改有效可见集 · R1 B-1 补列）· `lg_rag/state.py`（channel）· `capability/types.py`（:72-118 扩字段）· `capability/manifest.py`（校验+派生）· `capability/manifests/builtin.v1.yaml`（数据补齐） |
| 先例 · 纯函数闸 | `app/ops/lg_rag/multi/step_contract.py` · `app/ops/capability/delegation.py`（V1-A · 零 LLM 零 IO 形态） |
| 先例 · 三档模式 | `app/ops/capability/delegation.py`（LG_RAG_DELEGATION_TOKEN_MODE · off/observe/enforce 形态） |
| 先例 · 加载期校验 | `app/ops/capability/manifest.py`（V9 visibility / V10 output_schema 强校验 · ManifestError 整文件失败） |
| 测试锚点 | B1 清单 6 组 |
| 格式基准 | `docs/tasks/done/task_host_v1_delegation_token.md`（V1-A · 五棒全通 · 格式对齐此） |

---

## 给执行帽的必读列表

1. `AGENTS.md`（新会话启动纪律 · 分支纪律 · GATE_VERIFY）
2. 本 task（钉死契约 · 闸 · 非范围 · B1）
3. SPEC `docs/spec/host-v1-visibility-scenario-policy/SPEC-host-v1-visibility-scenario-policy_v0.md`（§2 D1–D5 / §3 非范围 / §4 Q1–Q3 / §5 FP-1~FP-8 / §6 验收）
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`
5. 代码：`app/ops/strategy/intent.py`（:22-24 fallback · :52-92 节点）· `app/ops/strategy/builder.py`（:39-75）· `app/ops/lg_rag/multi/nodes.py`（:933-948 交集面）· `app/ops/capability/baseline.py` · `app/ops/capability/types.py`（:72-118）· `app/ops/capability/manifest.py`（校验面）· `app/ops/capability/delegation.py`（三档模式先例）
6. 先例：`tests/test_strategy_builder.py`（裁剪断言范式）· `tests/test_capability_manifest.py`（加载校验断言范式）· `tests/test_capability_delegation.py`（V1-A 三档断言范式）
7. `docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | SPEC signed（HG-SPEC-SIGNOFF=approved 2026-09-23 00 代录）；范围 D1–D5 承 SPEC §2 不重开；本帽实扫复核：risk_hint :25-28 · fallback 裂缝 :22-24 · Builder 落点 :39-75 + supervisor 交集面 nodes.py:933-948（R2 审查 N-R2-1 微修）· 命名零真冲突 · 基线 1420 | no | — | 无 |
| R1 | 开工闸：HG-TASK-DRAFT approved（00 代录 · 双令留痕）· HG-AUDIT-R1 **pending**（blocks 30 → **30 拒开工**）· HG-GRAPH-MODULES=approved（真读核验 · 图谱新签义务随 30 落盘） | no | — | 无 |
| R2 | 竖切：D1→D4→D2→D3→D5 同 task 一次提交；方案对比继承 SPEC §4 三组裁定（Q1 3 档对齐弃细分 · Q2 仅意图弃会话上下文 · Q3 正交映射弃派生），不重演 | no | — | 无 |
| R3 | failure_paths **12 条** = SPEC FP-1~FP-8 翻四列 + 过程三 + 畸形 intent 安全默认一（R1 审查 N1 计数修正）；fallback 裂缝（FP-5）是最锋利边界（S1 空集+断言化）；畸形 intent 缺键视同 high/unknown 安全默认补齐 | no | — | ① 场景维 enforce 前依赖观察期报告质量 ② 误判过度裁剪只能靠台账复盘（方向正确性已锁） |
| R4 | 验收 **14 条**全否定性断言化逐块映射 SPEC §6（人工闸 1 / D1×2 / D2×3 / D3×1 / D4×4 / D5×3 = 14 · R1 审查 N2 计数修正 · 另变异检验×3 与注记不计入）；B1 实扫 6+1 组处置三态齐全（回归×5 · 新增×1 · 迁移无×1） | no | — | 无 |
| R5 | 可交 20-task-audit；与 SPEC 实质差异为零（锚点/B1/基线数/闸行留痕过程化落地）；HG-AUDIT-R1 落稿时待签 | no | — | 见 R3 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：见 R3/R5

### R0 · 问题框定

SPEC 已签收（Q1 3 档对齐 03 + Q2 仅意图+健康度 + Q3 正交映射锁死），本 task 只做可执行化拆解：U2 实证消解（risk_hint 已在零消费者）；fallback 裂缝是本波最锋利的安全边界。当前分支 master——**30 必须切 `task/host-v1-visibility-scenario-policy`**。

### R1 · 开工闸

HG-TASK-DRAFT approved（00 代录 · 双令原话留痕）；HG-AUDIT-R1 **pending**（30 拒开工）；HG-GRAPH-MODULES **真读** `01_modules.md` 核验：模块表已建置 · 签录链完整至 V1-A 回写行 · capability/lg_rag 行在表 · 图谱义务=两行备注+人签新行随 30 落盘。

### R2 · 竖切

D1–D5 是不可拆语义单元：scenario_trim 不配安全默认 = 无底线；不配台账 = 不可复盘；四字段不配加载校验 = 声明面裸奔。实现序：D1 fallback channel（输入完备化）→ D4 四字段（独立面先行）→ D2 scenario_trim+接线 → D3 台账 → D5 断言收口。

### R3 · 失败语义

SPEC §5 八条全收翻四列，加过程三条与畸形 intent 安全默认一条共十二条。fallback 裂缝（FP-5）断言化堵死；存量误伤（FP-3）三档灰度+存量补齐双保险；畸形 intent 缺键安全默认（缺 risk_hint 视同 high · 缺 domain 视同 unknown）补种子未覆盖的边界。

### R4 · 可测性

验收 14 条全部可执行：裁剪矩阵五行规则逐行否定断言（fallback 必须空集是变异检验式安全默认）· 四字段三硬规则 ManifestError · 三档派生声明优先 · builtin 全覆盖 · off 零 diff 由 1420 基线零改动证明。变异检验三条（安全默认/校验/台账各配「破坏→必挂→恢复」）。

### R5 · 交付判定

可交 20-task-audit：与 SPEC 实质差异为零；HG-AUDIT-R1 落稿时待签；残余风险两条承 R3 如实携带。

### 自检结论

本稿：范围/非范围/验收/failure_paths 逐块映射 SPEC（§2→D1–D5 · §3→非范围 · §5→failure_paths+过程三 · §6→验收 14 条）；钉死契约自 SPEC §2/§4/§5 锁死；B1 实扫 6+1 组三态齐全；闸表四行诚实；思考轮 R0–R5 回填齐全无跳轮。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-09-23 | 10-task 落稿（SPEC signed 后 · 00 亲起）：锚点逐个复核（risk_hint :25-28 · fallback :22-24 · builder :74-80 · types :72-118 · manifest 校验面）· 命名冲突扫零真冲突（irreversible 子串排除）· pytest 基线 1420 真跑 · B1 6+1 组落盘 · HG-TASK-DRAFT 00 代录 approved（双令留痕）· HG-AUDIT-R1 pending 待 20-task-audit |
| 2026-09-23 | **R1 审查 FAIL 回填**（审查文 `docs/harness/reviews/task_host_v1_visibility_scenario_policy_audit_R1_20260923.md`）：**B-1 阻塞处置**——00 亲验代码真值（交集在 supervisor `nodes.py:933-948` 非 Builder）→ 回 10-spec 澄清（SPEC D2 管线段落+FP-6 措辞勘正 · 三重交集交换律等价语义零改 · 00 代录同令留痕）→ task 落点/白名单/锚点同步（Builder stage 2 + supervisor 交集输入改有效可见集 · 白名单补 nodes.py）；N1 计数 11→12 · N2 计数 16→14 · N3 锚点行号修正（builder :39-60/:63-75）· N4 §6-8/§6-10 映射注记 · N5 03 轨 risk_hint 真值载体精确化（S2 PR #80 + 代码）；重交 **R2** |
| 2026-09-23 | **R2 审查 PASS-WITH-NITS**（零阻塞 · 审查文 `docs/harness/reviews/task_host_v1_visibility_scenario_policy_audit_R2_20260923.md` · B-1 消解三方一致+交换律数学核验 · N1–N5 闭环）；N-R2-1 微修（R0 行锚点 :74-80→:39-75+nodes.py · 闸行措辞）；**00 代录 HG-AUDIT-R1=approved**（维护者令原话+本窗双令留痕）· 30 可委派开工（分支 `task/host-v1-visibility-scenario-policy`） |
