# Task：memory-injection-consumer（memory 注入消费面实证与处置 · 先证后修 · 默认关）

> **状态**：draft（2026-10-19 10-task 落稿 · 待 20-task-audit R1 → HG-AUDIT-R1 → 30）
> **类型**：verify+feature（Phase A spy 实证**零生产码改动** → Phase B 按实证证据裁定分支处置；**不**新增路由 / 表 / 一级模块 / SSE `event_type`）
> **依据**：SPEC `docs/spec/memory-injection-consumer/SPEC-memory-injection-consumer_v0.md`（signed · v0.1 已含第三结局行双案并列 · HG-SPEC-SIGNOFF=approved 2026-10-19 维护者会话签收）· 审查文 `docs/harness/reviews/spec_memory-injection-consumer_audit_R1_20261019.md`（R1 **fail** 退回 → v0.1 修订 → 同文末尾 **R2 复审 conditional_pass** · R2-N1~N3 移交本 task 吸收）
> **建议序**：2/5（query-coref-rewrite 已随 PR #284 合入 master → **本 task** → scenario-stage-rewire → delegation-naming-boundary → tech-graph-flow-resync）
> **分支**：本文件落盘于文档线 `docs/task-memory-injection-consumer`（自 master fc5d9bd 切出）；30 开工分支 `task/memory-injection-consumer`（30 开工前自 master 切出）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `memory-injection-consumer` |
| **git_branch** | `task/memory-injection-consumer` |
| **implement_repo** | `ops-desk-api` |
| **spec** | `docs/spec/memory-injection-consumer/SPEC-memory-injection-consumer_v0.md`（signed · v0.1） |
| **test_strategy** | `required` |
| **test_strategy_note** | 承 SPEC 元信息并对齐五结局口径（R2-N1 吸收）：Phase A：spy/fake LLM provider 断言各节点实际收到的消息清单（注入开 × `mode=basic/router/supervisor` 三模式 × facts/episodes 矩阵）· **观测-only 零生产码改动** · Phase B：按 Phase A 证据经 **HG-PHASE-B-DECISION** 裁定点选定结局（五案完备预写：①疑点推翻关 task / ②B-a 接线 / ③B-b 收窄 / ④a 扩展接线 / ④b 全模式收窄，30 不临场发明表外方案）· 全程默认关零 diff · 假 LLM 注入即可机断，**不打真模型** |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` 预期（Phase A 零图谱变更；Phase B 各结局均只改 prompt 组装 / 跳过注入查询，不增 `event_type`/路由/表；仅 `docs/_tech_graph/l1/01_modules.md` `memory` 行备注按裁定结局回写）。若 30 实判越出 none → 回 SPEC 判 G-L*，**禁** silent 扩 |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` `memory` 行备注按 Phase B 裁定结局回写（③B-b：写明「supervisor 不消费」；④b 全模式收窄：写明「当前无任何消费点，功能休眠」；②/④a 接线案：接线面备注）；Phase A 阶段零图谱变更 |
| **graph_delta_note** | 无模块增删仅行备注；偏离回炉补闸 |
| **wiki_delta** | `n/a`（30 实判，可选 volatile 短注） |
| **wiki_delta_note** | 契约真值以 SPEC 为准；本 task 不新增契约面 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `required` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿（本文件）→ 20-task-audit R1 → HG-AUDIT-R1（维护者已授权 00 代签后续文档闸 · **落闸动作在 20-task-audit 之后由 00 执行**，起草时 pending）→ 30 **Phase A**（spy 实证 · 零生产码）→ **Phase B 裁定点**（HG-PHASE-B-DECISION 落签）→ 30 **Phase B**（按裁定结局实施）→ 40 → PR+CI 绿 → CLOSE → **下游棒**：scenario-stage-rewire（建议序 3/5 · 另 SPEC/task） |
| **freeze_id** | 对照 `lg-rag-sse-v1` / `lg-rag-http-v1`：SSE 帧与请求体零变化（承 SPEC「无契约变更（SSE/HTTP 零动）」）。若 30 需要透出任何新帧/字段（各结局均不需要）→ 回本 SPEC 升 freeze，**禁** silent 扩 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-SPEC-SIGNOFF | approved | 10, 20 | 2026-10-19 维护者会话签收 · 见 SPEC 闸表与审查文（R1 fail → v0.1 → R2 终裁 conditional_pass · R2-N1~N3 移交本 task 吸收） |
| **HG-AUDIT-R1** | **approved** | 30 | 2026-10-19 维护者授权 00 代签（会话原话「授权00签收后续文档」）· 依据审查文 `docs/harness/reviews/task_memory_injection_consumer_audit_R1_20261019.md`（R1=conditional_pass · 阻塞 0 · 锚点 30 处零漂移 · N1 未覆盖象限径按 FP-9 处置 / N2 TC5 收紧白名单 / N3 开关锚点行号按实校正，三条均 30 吸收） |
| HG-GRAPH-MODULES | approved | 30 | `docs/_tech_graph/l1/01_modules.md` 闸登记表在册 approved（`memory` 行 :36 · `lg_rag` 行 :35 起在册）· graph_change_layer=none 预期不再签；30 实判越出 → 回本表补签 |
| **HG-PHASE-B-DECISION** | **pending** | 30（Phase B） | **Phase B 显式裁定点**：Phase A 实证表落 invoke 后，由维护者（或经授权 00）按 Phase A 证据裁定结局分支并在本表 + invoke 裁定记录位落签（写明「因 Phase A 实证行 X → 裁定结局 Y」）；30 **不得临场发明表外方案**（承 SPEC §2 自锁条款原样继承）；Phase A（观测-only）不受本闸阻塞 |

---

## 背景与目标

### 问题（承 SPEC §1）

V1-B 波次交付了 memory facts/episodes 注入（默认关），但 2026-10-19 supervisor 全流程审核疑点 #2（高置信）：注入写进 `state.messages` 后，supervisor 链路所有 LLM 消费点（planner / aggregator / rag 工人）**都不读 `state.messages`**；R1 审查进一步实证：router/basic 四节点（rag_node / direct_answer_node / router_node / rewrite_node）同样只取 `_last_user_text`（仅末条 HumanMessage）或重建双消息 prompt——注入块疑似**三模式均到不了任何 LLM**。静默无效比没有更糟（运维以为有记忆增强，实际没有）。**但疑似≠坐实**：本 task 强制「先证后修」，禁止跳过实证直接接线。

### 目标（承 SPEC §1 一句话目标 · R2-N1 口径对齐）

实证确认 memory 注入在三模式下的真实消费面（Phase A）；再按实证证据经**显式裁定点**选定处置结局（Phase B）。**口径对齐（R2-N1 吸收）**：SPEC 头部 track 行（:4）· §1 一句话目标（:44）· test_strategy_note（:23）三处「二选一 / 接线或按模式跳过」系 v0.1 残留措辞，与 §2 分支表现实不齐；本 task 全文统一采用「**Phase B 处置分支由 Phase A 证据裁定 · 结局空间五案完备预写**（①疑点推翻关 task / ②B-a 接线 / ③B-b 收窄 / ④a 扩展接线 / ④b 全模式收窄）」口径，不再使用「二选一」。处置结论由 Phase A 证据决定，本 task 不预设。

---

## 范围

单 task 两阶段串行（Phase A 先行 → 显式裁定点 → Phase B；承 SPEC §2，全部结局的处置方案均已预写，30 不临场发明表外方案）：

### Phase A · 实证（零生产码改动 · 观测-only）

| 项 | 约定 |
|---|---|
| 方法 | spy/fake LLM provider 记录每次 `complete` / `complete_stream` 实收消息清单；注入开关开，造 facts/episodes 各 ≥2 条（测试夹具） |
| 矩阵 | `mode=basic / router / supervisor` × facts / episodes 全组合 |
| 产出 | 实证表（哪个节点收到/没收到注入块 · 逐格「收到/未收到」）落 invoke；结论触发 Phase B 裁定点 |
| 纪律 | **Phase A 不动 `app/` 任何生产码**（观测-only 零行为变化）；spy 只在 `tests/`；不打真模型 |

Phase A 观测点清单（消费面枚举 · 锚点已经 10-task 亲读复核，见「依赖」节；行号 30 按实校正）：

- **supervisor**：planner（`app/ops/lg_rag/multi/nodes.py:1163-1170` 只传 `[system, user=query]`）· aggregator（off 态 `_aggregator_plain_messages` :2035-2043 · on 态 `_aggregator_isolated_messages` :2046-2048 三参无 history）· rag 工人（:1432-1435 调 `astream_router_agent` 未传 `history_turns`；`graph.py:278` 缺省 None，fresh 装配在 `graph.py:199-206`；`_worker_state` :1041-1063 虽带全量 messages 但 rag 工人内部只用 `result["input"]`）
- **router/basic**：router_node（`app/ops/lg_rag/nodes.py:119`）· rewrite_node（:209-218）· rag_node（:153-154 只传 query 字符串给 `ainvoke_evidence_answer`）· direct_answer_node（:255-263 重建 `[system, user=query]`）· `_last_user_text`（:48-53 仅取末条 HumanMessage，注入块是 SystemMessage 天然不可见）· basic 图（`graph.py:56-62` 唯一节点即 rag_node）
- **注入侧对照**：facts 注入 `inject_memory_facts_block`（`app/ops/lg_rag/continuity.py:349-362` · 独立 SystemMessage 插前缀系统消息后 · 空块原样返回）· episodes 注入面（`MEMORY_EPISODES_HEADER` :200 · `render_memory_episodes_block` :316 · 落点 `inject_memory_facts_block(messages, episode_block)` :527）· 开关 `memory_facts_enabled` :142-151 / `memory_episodes_enabled` :208-222 均默认关、非法值回退关

### Phase B · 处置（显式裁定点 · 五结局完备预写 · 触发显式互斥）

**裁定点设计（本 task 核心结构）**：Phase A 实证表落 invoke 后 → **HG-PHASE-B-DECISION 人工闸**：维护者（或经授权 00）按 Phase A 证据裁定结局，在 task 闸表 + invoke 裁定记录位落签（写明「因 Phase A 实证行 X → 裁定结局 Y」）→ 30 按裁定结局实施。**30 不得临场发明表外方案**（承 SPEC §2 自锁条款原样：「全部结局的处置方案都已在下表预写，30 不临场发明表外方案」）。

触发条件**显式互斥**（R2-N2 吸收：B-a/B-b 以「router/basic 有消费者坐实」为前提，消除与第三结局行的触发重叠）：

| 结局 | 触发（互斥） | 内容（承 SPEC §2 原样） |
|---|---|---|
| **① 疑点推翻** | 三模式均有消费者坐实（每模式 ≥1 个 LLM 消费点实收注入块） | Phase B 整体不做，invoke 记录「疑点不成立」关 task；零生产码改动 |
| **② B-a 接线** | supervisor 零消费坐实 **且 router/basic 有消费者坐实**（R2-N2 前提）**且** 裁定「supervisor 应有记忆增强」 | planner system 尾部 + aggregator user 头部注入 `[已知事实]`/`[用户偏好]`/`[相似经验]` 块（复用 continuity 已产出的注入文本，**不重复查询**）；rag 工人**不**接（输入隔离是既定设计，另案） |
| **③ B-b 收窄** | supervisor 零消费坐实 **且 router/basic 有消费者坐实**（R2-N2 前提）**且** 裁定「本波不接」 | supervisor 模式跳过注入（省无谓查询与 token）；router/basic 维持；`01_modules.md` `memory` 行写明「supervisor 不消费」 |
| **④a 扩展接线** | **三模式均零消费坐实**（router/basic 亦无消费者）**且** 裁定接线 | 在 ②B-a 基础上将接线面扩至 router/basic 消费点——direct_answer/rag 节点 prompt 组装注入块（复用注入文本，不重复查询） |
| **④b 全模式收窄** | **三模式均零消费坐实** **且** 裁定收窄 | 三模式统一跳过注入 + `01_modules.md` `memory` 行与文档写明「当前无任何消费点，功能休眠」，消费点需求另立 SPEC 再接 |

**接线案（②/④a）共用约束**：注入块进 prompt 总量上限 **8000 字符**（SPEC §7「块总量设上限（task 阶段定数值）」授权本帽定值：承窗先例 query+answer 各截 4000 的量级 ×2），超出截尾 + span `memory_injection_truncated=true`；facts revoked/为空时**不出现空块标题**（承 continuity 空块原样返回语义）。

**回滚（R2-N3 吸收）**：B-a/B-b 均为开关默认关下的行为，回滚=恢复原注入路径；**第三结局两案（扩展接线/全模式收窄）同为开关默认关下的行为，回滚语义自然延伸——扩展接线回滚=移除接线恢复 prompt 原组装，全模式收窄回滚=恢复注入查询路径**。

## 非范围

承 SPEC §3 五条原样继承：

- ❌ 跳过 Phase A 直接接线（本 SPEC 核心纪律）
- ❌ 改注入文本格式 / 记忆召回排序 / 写入闸（memory-facts 系列 SPEC 的领域）
- ❌ rag 工人子图吃历史（输入隔离是既定设计，改动另立 SPEC）
- ❌ 开默认开关（所有记忆开关维持默认关）
- ❌ episodes 写路径接线（write_episode 全仓无生产调用方是另一疑点，另案）

task 级补充：

- ❌ Phase A 阶段改任何 `app/` 生产码（观测-only；spy 只在 `tests/`）
- ❌ 30 临场发明上表五结局之外的处置方案（承 SPEC §2 自锁条款）
- ❌ 未经 HG-PHASE-B-DECISION 落签即进入 Phase B 改码
- ❌ 注入块重复查询（接线案复用 continuity 已产出文本，不二次召回）
- ❌ **本起草阶段零 `app/` / `tests/` 改码**（仅 docs；30 开工以 HG-AUDIT-R1=approved 为前提）

---

## 失败路径（failure_paths）

承 SPEC §5 FP-1~FP-6 原样（措辞按五结局口径对齐），并增 FP-7~FP-9（裁定点与闸纪律）：

| ID | 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----|----------|----------|--------|----------|
| FP-1 | 开关默认关 | 三模式零 diff（spy 断言无任何注入块） | — | 零 diff |
| FP-2 | 注入开 × supervisor | 实证记录每个 LLM 节点的消息清单；若 planner/aggregator 消息内无注入块 → supervisor 零消费坐实 | — | — |
| FP-3 | 注入开 × router/basic | 同上；若 direct_answer/rag 亦未收到注入块 → 「三模式均零消费」坐实，走结局 ④a/④b；若收到 → 「零效果为 supervisor 特有」坐实，走结局 ②/③ | — | — |
| FP-4 | 接线案（②/④a）实施后 | 目标节点 prompt 含注入块；facts revoked/为空时不出现空块标题；块总量 ≤8000 字符，超出截尾 + span `memory_injection_truncated=true` | — | 正常作答 |
| FP-5 | 收窄案（③/④b）实施后 | 对应模式不再查询 facts/episodes（spy DB 断言零命中）；未收窄模式不变 | — | 零 diff |
| FP-6 | 实证推翻疑点（结局①） | 关 task，零生产码改动落盘 | — | — |
| FP-7 | Phase B 未裁定即改码 | HG-PHASE-B-DECISION=pending → 30 拒开工（闸真值=本表，非聊天/invoke 字面） | 是 | — |
| FP-8 | HG-AUDIT-R1 未签即 30 | GATE_VERIFY 拒开工 | 是 | — |
| FP-9 | 30 提出表外方案 | 违反 SPEC §2 自锁 → 退回裁定点，由维护者裁定是否另立 SPEC | 是 | — |

---

## 验收标准

全部可机断（spy/fake LLM 注入 / 夹具 / 零 diff 对拍 / diff 面断言，**不打真模型**）：

- [ ] **TC1 Phase A 实证矩阵全覆盖**：spy provider 下 `mode=basic/router/supervisor` × facts/episodes 全组合（注入开关开 · 各 ≥2 条夹具），每个组合断言每个 LLM 消费点实收消息清单；实证表（逐格「收到/未收到」）落 invoke。
- [ ] **TC2 默认关零 diff（FP-1）**：`MEMORY_FACTS_ENABLED`/`MEMORY_EPISODES_ENABLED` 未设/0 下，三模式装配输出消息序列与改前**逐元素相等**；spy 断言无任何注入块。
- [ ] **TC3 注入开 × supervisor（FP-2）**：planner（`multi/nodes.py:1163-1170`）/ aggregator（:2035-2043 off · :2046-2048 on）/ rag 工人（:1432-1435 经 `astream_router_agent` → 子图 router/rewrite/rag/direct_answer）实收消息清单逐点断言并记录注入块出现与否。
- [ ] **TC4 注入开 × router/basic（FP-3）**：router_node（`nodes.py:119`）/ rewrite_node（:209-218）/ rag_node（:153-154）/ direct_answer_node（:255-263）实收消息清单逐点断言；basic 图唯一节点 rag_node 同断言。
- [ ] **TC5 Phase A 零生产码**：Phase A 提交相对 master 的 diff 不含 `app/` 任何文件（`git diff --name-only` 断言；tests/ 与 docs/invoke 除外）。
- [ ] **TC6 裁定记录位**：invoke 写明「因 TC3/TC4 实证行 X → 裁定结局 Y」+ Phase A 证据引用；HG-PHASE-B-DECISION 在 task 闸表落签（维护者或经授权 00）；分支选择不属于五案之一 → 拒（FP-9）。
- [ ] **TC7 接线案验收（结局②/④a · FP-4）**：金样断言目标节点实际收到注入块（②：planner + aggregator；④a：再 + direct_answer/rag）；rag 工人不收到；facts revoked/为空 → 无空块标题；注入块总量 >8000 字符时截尾 + span `memory_injection_truncated=true`，≤8000 不截。
- [ ] **TC8 收窄案验收（结局③/④b · FP-5）**：③supervisor 模式 / ④b 三模式注入查询被跳过（spy DB 断言零命中）；未收窄模式（③下 router/basic）行为零 diff。
- [ ] **TC9 疑点推翻验收（结局① · FP-6）**：零生产码改动关 task；invoke 记录「疑点不成立」+ 三模式消费点证据引用。
- [ ] **TC10 图谱与契约守护**：不新增 SSE `event_type` / 路由 / 表 / 一级模块；`graph-compile` EXIT=0；`docs/_tech_graph/l1/01_modules.md` `memory` 行备注按裁定结局回写（③：「supervisor 不消费」· ④b：「当前无任何消费点，功能休眠」· ②/④a：接线面备注）。
- [ ] **TC11 反回归全量**：`pytest` 全量绿（新增覆盖 TC1–TC8）；`ruff check` 触及路径绿；默认关保证下既有用例零行为差。
- [ ] **TC12 旧测影响面（K7 惯例）**：30 红测先行前对下列装配/记忆面既有测试逐文件确认处置（行号 30 按实校正），**枚举外既有用例默认保持绿**（误删合法回归即红）：
  - `tests/test_memory_injection.py` / `tests/test_memory_episode_recall.py`（装配+记忆注入面）→ 默认关**保持绿**；注入开断言面是 Phase A spy 的天然落点。
  - `tests/test_lg_rag_session_continuity.py` / `tests/test_session_summary.py`（装配对拍 · off 态逐字节先例）→ 默认关**保持绿**。
  - `tests/test_memory_vector_p1.py` / `tests/test_memory_service_db.py` / `tests/test_memory_extract_p1.py`（召回/服务桩）→ 默认关**保持绿**；收窄案落地后核对「跳过注入查询」断言不与既有桩冲突。
  - `tests/test_input_isolation_wiring.py` / `tests/eval/test_input_isolation.py`（槽位归因面）→ 默认关**保持绿**；aggregator on 态接线若触槽位装配须逐条核对。

## 依赖

- base：master（fc5d9bd · PR #284 已合入）；本文件落盘于文档线 `docs/task-memory-injection-consumer`；30 开工分支 `task/memory-injection-consumer`（30 开工前自 master 切出）。
- SPEC：`docs/spec/memory-injection-consumer/SPEC-memory-injection-consumer_v0.md`（signed · v0.1）全文。
- 审查文：`docs/harness/reviews/spec_memory-injection-consumer_audit_R1_20261019.md`（R1 fail 退回面 B1/B2 + N1–N3 · **文末 R2 复审节** conditional_pass + R2-N1~N3；吸收落点见本文件范围/回滚/口径段与 invoke 索引）。
- 锚点（**10-task 已在 master fc5d9bd 亲读复核**；router/basic 六处与 R1 实录逐字一致；continuity.py 注入侧因 PR #284 合入发生行漂移，下列为**校正后**行号；30 按实校正）：
  - `app/ops/lg_rag/nodes.py:48-53`（`_last_user_text` 仅取末条 HumanMessage）· `:119`（router_node）· `:153-154`（rag_node → `ainvoke_evidence_answer(query)`）· `:209-218`（rewrite_node 重建 `[system, user=original]`）· `:255-263`（direct_answer_node 重建 `[system, user=query]`）
  - `app/ops/lg_rag/graph.py:56-62`（basic 图 `START → rag → END`）· `:199-206`（`assemble_graph_messages_with_memory` fresh 装配入 payload）· `:278`（`history_turns` 缺省 None）
  - `app/ops/lg_rag/multi/nodes.py:1163-1170`（planner `[system, user=query]`）· `:2035-2043`（`_aggregator_plain_messages`）· `:2046-2048`（`_aggregator_isolated_messages` 三参无 history）· `:1432-1435`（rag 工人未传 `history_turns`）· `:1041-1063`（`_worker_state` 带全量 messages 但 rag 工人不用）
  - `app/ops/lg_rag/continuity.py:349-362`（`inject_memory_facts_block` · 独立 SystemMessage 插前缀系统消息后 · 空块原样返回）· `:316`（`render_memory_episodes_block`）· `:527`（episodes 注入落点 `inject_memory_facts_block(messages, episode_block)`）· `:142-151` / `:208-222`（开关默认关 · 非法值回退关）
  - `docs/_tech_graph/l1/01_modules.md`（`memory` 行 :36 备注回写点 · 闸登记表 :61 起）
- 编码规范：`docs/standards/CODING_BACKEND_L2_v1_zh.md`。
- 结构先例：`docs/tasks/done/task_query_coref_rewrite.md`（同波 1/5 · 元信息/闸表/TC 风格对齐源）；`docs/tasks/done/task_session_summary_fallback.md`（默认关零 diff · off 态对拍先例）。

## 给执行帽的必读列表

1. 本 task 全文（含人工闸表 · **HG-AUDIT-R1=pending 未签不得 30**；**HG-PHASE-B-DECISION=pending 未裁定不得进 Phase B**；两闸 00/AI 不得在本帽代签）。
2. SPEC `docs/spec/memory-injection-consumer/SPEC-memory-injection-consumer_v0.md` 全文（§2 分支表五结局 · §3 非范围 · §5 FP-1~FP-6 · §6 验收 · §7 风险/回滚）。
3. 审查文 `docs/harness/reviews/spec_memory-injection-consumer_audit_R1_20261019.md`（R1 §一~§五 + **文末 R2 复审节**，R2-N1~N3 原文）。
4. 上列锚点文件全文相关段（禁信转述 · 行号按实校正）。
5. `docs/standards/CODING_BACKEND_L2_v1_zh.md`。
6. 先例：`docs/tasks/done/task_query_coref_rewrite.md`（同波结构）· `docs/tasks/done/task_session_summary_fallback.md`（默认关零 diff 接入模式）。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|------|-----------|----------------------|----------------|
| R0 | 问题框定承 SPEC + R1 实证：注入块疑似三模式均到不了任何 LLM（静态证据）；疑似≠坐实，先证后修 | false | — | — |
| R1 | 范围=Phase A spy 实证（观测-only 零生产码）+ Phase B 五结局完备预写；SPEC §3 五条非范围原样继承 | false | — | spy provider 可信度承 SPEC R2 挂账 |
| R2 | 方案承 SPEC §4 裁定 C（先证后修）；R2-N1~N3 逐条吸收：N1→口径对齐五结局 · N2→触发显式互斥（B-a/B-b 前提=router/basic 有消费者）· N3→回滚句补第三结局两案 | false | — | 块总量上限 8000 为本帽定值（SPEC §7 授权），实测若不足由 40 上抛 |
| R3 | 反例闭合：Phase A 被跳过→SPEC 明文禁止+FP-7/FP-8/FP-9 三闸互锁；表外方案→拒；默认关零 diff 三向互锁（FP-1/TC2/TC11） | false | — | 三模式均零消费下「接线 vs 收窄」争议上交裁定点（承 SPEC §7） |
| R4 | 验收 TC1–TC12 全部 spy/夹具/零 diff/diff 面机断；红测先行；不打真模型 | false | — | rag 工人子图观测依赖 `astream_router_agent` 链路 spy 穿透深度，30 实证 |
| R5 | 草稿可交 20-task-audit；**不可**当已签收 | false | — | **HG-AUDIT-R1=pending** · **HG-PHASE-B-DECISION=pending**（签前/裁定前 30 拒改码） |

**actual_last_round**：R5

### R0 · 问题框定

承 SPEC §8 R0 与 R1 审查 §一：注入侧 6 组锚点 R1 实测全命中；本帽在 master fc5d9bd 亲读复核 router/basic 六处锚点（nodes.py:48-53/:119/:153-154/:209-218/:255-263 · graph.py:56-62）逐字一致，supervisor 侧五处（multi/nodes.py:1163-1170/:2035-2043/:2046-2048/:1432-1435/:1041-1063 · graph.py:199-206/:278）一致；continuity.py 注入侧因 PR #284 漂移（:341-354→:349-362 等），已在「依赖」节按实校正。

### R1 · 范围收束

承 SPEC §2 两阶段串行 + §3 非范围五条原样。Phase A 观测-only 口径钉死：spy 只在 `tests/`，`app/` 零改动由 TC5 diff 面断言兜底；Phase B 不临场发明由 SPEC §2 自锁 + FP-9 兜底。

### R2 · 方案与 R2-N1~N3 裁定

- **R2-N1（口径不齐）**：SPEC 三处「二选一」系 v0.1 残留（§2 分支表实为五结局）；本 task 全文统一「五案完备预写」口径，test_strategy_note 同步对齐。
- **R2-N2（触发重叠）**：B-a/B-b 触发行补显式前提「router/basic 有消费者坐实」，与第三结局行（router/basic 亦无消费者）互斥；结局空间 {①均有} ∪ {②③仅 supervisor 零消费} ∪ {④a④b 三模式均零消费} 完备无漏。
- **R2-N3（回滚句）**：补「第三结局两案同为默认关下行为，回滚语义自然延伸」，接线案/收窄案回滚语义分别钉死。
- **块总量上限定值 8000 字符**：SPEC §7 授权 task 阶段定数值；取窗先例（query+answer 各截 4000）量级 ×2，截尾 + span 标记机断可测。

### R3 · 反例与边界

失败面全部收敛：Phase A 跳过（FP-7/FP-8 双闸拒开工）· 表外方案（FP-9 退回裁定点）· 空块标题（FP-4 否决）· 块膨胀（8000 截尾）· 默认关漂移（FP-1/TC2/TC11 三向互锁）。

### R4 · 验收/可测性

`test_strategy=required`；TC1–TC12 均 spy/fake LLM/夹具/零 diff/diff 面机断；Phase A 实证表本身即验收物（TC1 落 invoke）；裁定记录位（TC6）把分支选择绑定证据链。

### R5 · 收口

草稿交 20-task-audit；**HG-AUDIT-R1=pending**（维护者授权 00 代签的落闸动作在 20 之后执行）· **HG-PHASE-B-DECISION=pending**，两闸落签前 30 拒改码。本文件不授权改 `app/` / `tests/`。

### 自检结论（10-task · 2026-10-19）

- **范围/非范围互斥**：Phase A/B 与 SPEC §3 五条 + task 级五条无重叠；「Phase A 零生产码」与 TC5 diff 面断言互锁；「不临场发明」与 FP-9/HG-PHASE-B-DECISION 互锁；「不重复查询」与接线案「复用注入文本」互锁。
- **每条验收可机断**：TC1–TC12 全部 spy/夹具/零 diff/diff 面对拍，无人工判断项；TC7 边界（>8000 截 · ≤8000 不截）钉死闭区间口径。
- **R2-N1~N3 逐条可追溯**：N1→「目标」节口径对齐段 + test_strategy_note；N2→Phase B 分支表触发列（②③ 前提=router/basic 有消费者坐实）；N3→「回滚」段（第三结局两案同）。
- **先证后修结构**：Phase A（观测-only · TC1–TC5）先行 → HG-PHASE-B-DECISION 显式裁定点（挂人工闸 · 裁定记录位在闸表+invoke）→ Phase B（按裁定结局实施 · TC7–TC9 按结局取用）；SPEC §2 自锁条款原样继承，30 无临场裁量空间。
- **闸纪律**：HG-SPEC-SIGNOFF=approved（有依据）· **HG-AUDIT-R1=pending**（00/AI 本帽不代签 · 维护者授权 00 代签的落闸动作在 20-task-audit 之后执行）· HG-GRAPH-MODULES 在册 approved（graph_change_layer=none 预期不再签 · 越出回炉补签）· **HG-PHASE-B-DECISION=pending**（新增裁定点闸）。
- **零 SPEC 扩范围**：非范围五条原样继承；task 级补充五条均为纪律性约束（不加新功能面）；锚点复核发现 continuity.py 行漂移仅作「按实校正」记录，不改 SPEC 文本。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-19 | 10-task 草稿：承 SPEC（signed · v0.1）§2 五结局分支表 + §3 非范围五条原样；吸收 R2-N1~N3（N1→五结局口径对齐 · N2→触发显式互斥 · N3→回滚句补第三结局两案）；Phase A 观测-only 先行 + HG-PHASE-B-DECISION 显式裁定点；块总量上限定值 8000 字符（SPEC §7 授权）；failure_paths FP-1~FP-9；验收 TC1–TC12；锚点亲读复核（continuity.py 行漂移按实校正）；HG-AUDIT-R1=pending（00/AI 不代签）；文档分支 `docs/task-memory-injection-consumer`（自 master fc5d9bd 切出） |
