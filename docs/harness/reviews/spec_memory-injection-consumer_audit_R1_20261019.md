# 20-spec-audit R1 书面审：SPEC-memory-injection-consumer v0

> **hat_id**：20-spec-audit（R1 · 轻量路径：10-spec 思考轮 R0–R5 已内联 SPEC §8，单轮 R1）
> **审查对象**：`docs/spec/memory-injection-consumer/SPEC-memory-injection-consumer_v0.md`（draft · 162 行 · HG-SPEC-SIGNOFF=pending）
> **审查日期**：2026-10-19 · **审查人**：Harness 20-spec-audit（书面审 · 不改 SPEC 实质 · **不代签** HG-SPEC-SIGNOFF）
> **结论**：**fail（退回 10-spec 修订后再审）** · 阻塞项 B1/B2（均涉 SPEC 实质，本帽无权代改）· 非阻塞 N1–N3 · **建议维护者暂勿签 HG-SPEC-SIGNOFF**
> **⚠️ 终裁以文末「R2 复审（2026-10-19）」为准**：v0.1 修订后 R2 判 **conditional_pass · 建议可签 HG-SPEC-SIGNOFF**
> **实证复核范围**：SPEC 全文 162 行逐行 · 源码实读 `app/ops/lg_rag/continuity.py:130-215,330-369,401-524,546-573` · `app/ops/lg_rag/multi/nodes.py:1030-1230,1420-1449,1660-1711,2020-2134` · `app/ops/lg_rag/graph.py:56-103,149-289` · `app/ops/lg_rag/nodes.py:48-53,117-273` · 全仓 grep：`write_episode` / `assemble_graph_messages_with_memory` / `state.messages` 消费点 / `MEMORY_FACTS_ENABLED`·`MEMORY_EPISODES_ENABLED` 默认值

## 一、委托方点名三大重点核对

### 1. 注入侧 / 消费侧锚点真实性 · **PASS（6 组锚点行号全部命中，其中 1 组措辞欠精确 → N1）**

| SPEC 锚点 | 实证结果 |
|---|---|
| `continuity.py:341-354` facts 注入（独立 SystemMessage 插前缀系统消息后） | ✅ 逐字一致：`inject_memory_facts_block` def :341、`return [*messages[:idx], SystemMessage(content=block), *messages[idx:]]` :354 |
| `continuity.py:483-514` episodes 注入（`[相似经验]`） | ✅ 逐字一致：分节注释 :483 → `return inject_memory_facts_block(messages, episode_block)` :514；召回失败降级不注入 :502-506 |
| 开关 `MEMORY_FACTS_ENABLED` / `MEMORY_EPISODES_ENABLED` 默认关 | ✅ :134-144 / :200-215，未设/非法值均回退 false |
| `multi/nodes.py:1163-1170` planner 只吃 query | ✅ supervisor_node 先 `_last_user_text(state["messages"])`（:1106）取 query，`provider.complete([system, user=query])` :1163-1170——注入块不进 prompt |
| `multi/nodes.py:2035-2043` aggregator 只吃 query+子任务结果 | ✅ `_aggregator_plain_messages(query, payload)` :2035-2043；on 态 `_aggregator_isolated_messages(query, results, payload)` :2046+ 同样不含 history（补引建议 → N2）；调用点 aggregator_node :2107 同为 `_last_user_text` 取 query |
| `multi/nodes.py:1432-1435` rag 工人不传 history | ✅ 事实成立：`astream_router_agent(result["input"], thread_id=...)` 未传 `history_turns`（graph.py:278 缺省 None），fresh 装配发生在 `_astream_with_tracing` graph.py:199-206；措辞「输入隔离」与 security-input-isolation 术语撞车 → N1 |
| `multi/nodes.py:1041-1063` `_worker_state` 带全量 messages 但 rag 工人不用 | ✅ :1054 `"messages": list(state.get("messages") or [])` 在册；rag 工人路径（:1432-1435）只用 `result["input"]`，不读该 messages |

附加自述核查：`write_episode` 全仓无生产调用方 ✅（app/ 内仅 episode_service.py:71 定义与文档引用）；注入落点「前缀系统消息之后」✅。

### 2. 『先证后修』纪律是否可被 Phase B 绕过 · **PASS（结构上不可绕过）**

- §3 非范围首条「❌ 跳过 Phase A 直接接线（本 SPEC 核心纪律）」+ §4 方案 A/B 均以「不实测就改/砍」为由弃置 + §7 风险表「Phase A 被跳过或形式化 → SPEC 明文禁止；20-task-audit 核对 invoke 实证表」三层互锁。
- 验收条「Phase B 分支选择有 Phase A 证据引用（invoke 内写明『因 FP-x 选 B-a/B-b/关闭』）」把分支触发绑定到实证台账，30 无自由裁量空间；§2「30 不临场发明第三方案」锁死临场发挥。
- 结构裁定：Phase A 零生产码改动（spy 只在测试，R3 自证）与 Phase B 同 task 两阶段串行，无并行跳过面。**纪律设计本身合格**。

### 3. B-a/B-b 分支验收是否互斥完备 · **FAIL（完备性缺口 → B2）**

- 互斥性 ✅：结局空间划分清楚——{三模式均有消费者 → 关 task}、{supervisor 零消费 → B-a XOR B-b，由维护者按 Phase A 证据裁定}；SPEC §7 明示不预设，裁定权上交合规。
- 完备性 ❌：见下方 B2——分支表漏掉静态证据指向的最可能结局。

## 二、阻塞项（退回 10-spec 修订；本帽不改 SPEC 实质）

### B1（中）· 现状锚点第 3 条与所引代码矛盾：router/basic 同样不消费注入块

SPEC 头「现状锚点」末条自述：「**但** router/basic 模式主图直接吃 `state.messages`（direct_answer/rag 节点），注入在那两条链路**可能**有效——『零效果』疑似为 supervisor 模式特有」。

代码实证（逐节点）：

| 节点 | 实证 | 注入块是否进 LLM |
|---|---|---|
| basic 图 | graph.py:56-62 `START → rag → END`，唯一节点即 rag_node | 否（同下行） |
| rag_node | nodes.py:153-154 `query = state.get("current_query") or _last_user_text(state["messages"])` → `ainvoke_evidence_answer(query)` 只传 query 字符串 | **否** |
| direct_answer_node | nodes.py:255-263 重建 `[system=render("lg_rag.direct.system"), user=query]` | **否** |
| router_node | nodes.py:119 `_last_user_text` → `_classify_route(query)` | 否 |
| rewrite_node | nodes.py:209-218 同上 query-only | 否 |
| `_last_user_text` 语义 | nodes.py:48-53 只取末条 **HumanMessage**；注入块是 SystemMessage（continuity.py:354） | —— |

注入块经 graph.py:199-206 进 `payload["messages"]`，但 router/basic 三模式所有 LLM 消费点都只提取 `_last_user_text` 或重建双消息 prompt——**注入块在 router/basic 同样到不了任何 LLM**。静态证据指向「三模式全零消费」，而非 SPEC 自述的「supervisor 特有」。

影响：该自述是 Phase A 的先验假设与 FP-3 的框架前提（「若 direct_answer/rag 收到注入块 → 零效果为 supervisor 特有坐实」）。虽有「可能」对冲，但作为「现状锚点」写出与所引代码相反的机制描述，会误导签收人与 00 起 task 时的分支预期。退回修订：把该条改为「router/basic 节点亦仅取 `_last_user_text` 重建 prompt，注入块疑似三模式全零消费，待 Phase A 实证」（或删除该对冲，统一交由 Phase A）。

### B2（中高）· Phase B 分支表不覆盖「三模式均零消费」结局，与 SPEC 自锁纪律冲突

承 B1：Phase A 最可能的实证结局是 router/basic **也**零消费。分支表（§2）三个结局均无法妥善处置该情形：

- **B-a 接线**：只接 planner/aggregator，router/basic 依旧「开了开关零效果」——直接违反 SPEC 自身 R1 失败定义「失败=不存在『开了开关零效果』的静默状态」；
- **B-b 收窄**：只跳过 supervisor 注入，router/basic 继续为无人消费的块支付召回查询与 token——静默浪费仍在；
- **疑点推翻行**：触发条件是「三模式均有消费者」，不适用。

即 SPEC §2 自锁「两条分支的实现方案都已在 §4 预写，30 不临场发明第三方案」，但证据指向的结局恰恰没有预写方案——30 将被迫临场发明，或带着已知静默无效面关 task。退回修订（二选一或等价处置）：
1. 分支表增补第三结局行「router/basic 亦零消费」的处置预案（如 B-a 扩展为「接线进 supervisor + router/basic 消费点」或 B-b 扩展为「全模式跳过/收窄」，具体由 10-spec 裁定）；或
2. 显式声明「router/basic 零消费若坐实则另立 SPEC」并进非范围 + 验收条对应改写（此选项需论证为何割裂处置优于本波一并处理）。

## 三、结构核对表（其余各项）

| 项 | 裁定 | 摘要 |
|---|---|---|
| 范围内聚（Phase A+B 同 task 两阶段） | ✅ | 阶段串行、触发条件明示；Phase A 零生产码改动可验收（spy 只在测试） |
| 非范围与范围互斥 | ✅ | §3 五条与范围无重叠；「不开默认开关」与 FP-1/验收「全程默认关零 diff」互锁 |
| 验收可机断 | ✅（B2 修订后需同步补） | 现有五条均可 spy/金样断言；但缺「三模式均零消费」结局对应验收条 |
| failure_paths 充分 | ⚠️（承 B2） | FP-1~FP-6 覆盖开关默认/三模式实证/两分支后验/疑点推翻；FP-3 框架前提承 B1 偏差 |
| R0–R5 思考轮闭合 | ✅ | §8 表 + 各轮小节齐全；`actual_last_round=R5`；R5 reason=「人签未发生」诚实；R2 弃案理由机制性 |
| 人工闸纪律 | ✅ | HG-SPEC-SIGNOFF=pending 在表；本帽不代签；SPEC §9/R5 声明「本文件不授权改 app/」 |
| graph_change_layer=none 预期 | ✅ | Phase B 两分支均只改 prompt 组装/跳过查询，不增 event_type/路由/表；`01_modules.md` 回写义务已挂（B-b 行 + §7） |

## 四、非阻塞 nits（修订时顺手吸收）

| ID | 位置 | 内容 |
|---|---|---|
| N1 | 现状锚点 :1432-1435 行 | 「输入隔离重建 fresh messages」措辞撞车 security-input-isolation（既定 D2 术语）；实际机制是调用方未传 `history_turns`（graph.py:278 缺省 None）→ fresh 装配在 graph.py:199-206。建议改写为「rag 工人调 `astream_router_agent` 不传 history_turns，子图按 query 重新装配」 |
| N2 | 现状锚点 :2035-2043 行 | 只引 off 态 `_aggregator_plain_messages`；on 态 `_aggregator_isolated_messages`（:2046-2063）同样只吃 query+results+payload，建议补引以免「on 态吃 history」误读 |
| N3 | invoke_slug | `docs/harness/invokes/by-task/memory-injection-consumer/` 当前不存在（SPEC 阶段思考轮内联 §8，轻量路径可接受）；按仓纪律 pre-30 invoke 缺失拒改码——移交 00 起 task 时同步补 |

## 五、HG-SPEC-SIGNOFF 建议

**建议维护者暂勿签 HG-SPEC-SIGNOFF**：B1（锚点自述与代码矛盾）+ B2（分支表漏最可能结局）均涉 SPEC 实质，须退回 10-spec 修订后重交 20-spec-audit（R2）。本帽**不代签**；维持：不出 task / 不改码 / 30 拒开工。

退回范围是**窄幅**的：先证后修骨架、Phase A 矩阵、spy 实证方法、闸纪律均合格，仅需修订 ① 现状锚点末条自述、② §2 分支表 + §5 FP-3 + §6 验收条对「三模式均零消费」结局的覆盖。

## 六、下一棒

**退回 10-spec** 修订 v1 → 20-spec-audit R2 复审 → HG-SPEC-SIGNOFF 人签 → 00 起草 task（slug=`memory-injection-consumer`，分支 `task/memory-injection-consumer`，同步补 invoke）。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-10-19 | R1：锚点 6 组行号全命中（1 组措辞 N1）；先证后修纪律结构合格；B1 router/basic 消费自述与代码矛盾 + B2 分支表漏「三模式均零消费」结局 → **fail 退回 10-spec**；N1–N3；不代签 HG-SPEC-SIGNOFF |

---

# R2 复审（2026-10-19）

> **复审对象**：`docs/spec/memory-injection-consumer/SPEC-memory-injection-consumer_v0.md` v0.1（同路径 · 165 行 · HG-SPEC-SIGNOFF 仍 pending）
> **复审触发**：10-spec 按 R1 退回面完成窄幅修订（§9 修订记录 v0.1 行在册）
> **结论**：**conditional_pass（PASS-WITH-NITS）** · R1 阻塞项 B1/B2 与 nits N1/N2 全部真实闭合 · 合格面确认未动 · 「30 不临场发明表外方案」自锁未被破坏 · 新增非阻塞 R2-N1~N3 移交 00/task 吸收 · **建议维护者可签 HG-SPEC-SIGNOFF**（本帽仍不代签）
> **R2 实证范围**：v0.1 全文 165 行逐行对拍 R1 版 · 新增锚点实测 `app/ops/lg_rag/nodes.py:48-53,119,153-154,209-218,255-263` · `app/ops/lg_rag/graph.py:56-62,199-206,278` · `app/ops/lg_rag/multi/nodes.py:2046-2047`（on 态签名）

## R2-一、退回面逐条验收

| R1 退回项 | v0.1 处置 | 实证 | 裁定 |
|---|---|---|---|
| **B1** 现状锚点末条自述与代码矛盾 | 改写为第 10 行：router/basic 四节点（rag_node `nodes.py:153-154` · direct_answer_node :255-263 · router_node :119 · rewrite_node :209-218）均只取 `_last_user_text`（:48-53）或重建双消息 prompt；basic 图 `graph.py:56-62` 唯一节点即 rag_node；结论「注入块疑似**三模式均到不了任何 LLM**」 | 新增 7 处锚点全部与 R1 实测记录逐字一致（:153-154 `ainvoke_evidence_answer(query)` · :255-263 重建 `[system, user=query]` · :48-53 仅取末条 HumanMessage · graph.py:56-62 `START → rag → END`）；「疑似/仍须 Phase A 实证坐实」对冲措辞保留，先证后修立场未动摇 | ✅ **闭合** |
| **B2** 分支表漏「三模式均零消费」结局 | §2 分支表新增第三结局行（第 66 行）：触发「router/basic 亦无消费者坐实」，内容双案并列预写——(a) 扩展接线（direct_answer/rag prompt 组装注入块，复用注入文本不重复查询）/ (b) 全模式收窄（三模式统一跳过注入 + 图谱与文档写明「功能休眠」，消费点需求另立 SPEC），维护者按 Phase A 证据裁定；§2 引言改「**全部结局**的处置方案都已在下表预写，30 不临场发明表外方案」 | 自锁核查：第三结局两案均**预写**（非占位符），与非范围无冲突（接线只改 prompt 组装 = graph_change_layer=none 预期内；全模式收窄 = 跳过查询，不触「不开默认开关」）；结局空间完备：{均有消费者→关} ∪ {仅 supervisor 零消费→B-a/B-b} ∪ {三模式均零消费→扩展接线/全模式收窄}，无漏 | ✅ **闭合** |
| FP-3 框架前提承 B1 偏差 | 改双分支判定（第 97 行）：「若 direct_answer/rag 亦未收到注入块 → 三模式均零消费坐实，走 §2 第三结局行；若收到 → 零效果为 supervisor 特有坐实」 | 两个走向各有归属分支，无悬空结局 | ✅ **闭合** |
| §6 验收缺第三结局对应条 | 新增第 110 行：invoke 写明所选结局 + Phase A 证据引用；扩展接线 → 金样断言 direct_answer/rag 实际收到注入块；全模式收窄 → 三模式注入查询全跳过（零 DB 命中）+ 图谱/文档休眠声明落盘 | 两个子案均可机断（金样断言 / spy DB 断言），与既有验收风格一致 | ✅ **闭合** |
| **N1** :1432-1435 措辞撞车 | 第 9 行改机制精确表述：「rag 工人调 `astream_router_agent` 未传 `history_turns`（`graph.py:278` 缺省 None，fresh 装配在 `graph.py:199-206`）」 | graph.py:278 `history_turns` 缺省 None · :199-206 `assemble_graph_messages_with_memory` 装配入 payload，逐字一致 | ✅ **闭合** |
| **N2** aggregator 只引 off 态 | 第 9 行补引「on 态 `_aggregator_isolated_messages` :2046-2063 同样只吃 query+results+payload」 | 签名实测 multi/nodes.py:2046-2047 `(query, results, payload)` 三参无 history，引述成立 | ✅ **闭合** |

## R2-二、合格面未动核查（对拍 R1 版）

§1 背景与「先证后修」核心纪律原样 · §3 非范围五条逐字未动（73-77）· §4 方案对比三弃一采原样 · §8 R0–R5 思考轮表与各小节原样（`actual_last_round=R5` · R5「人签未发生」诚实标记）· 人工闸表 HG-SPEC-SIGNOFF=pending 原样（未越权签）· 元信息 test_strategy/freeze_id/graph_change_layer 原样。**确认修订方自核属实：合格面零改动**。

## R2-三、新增非阻塞 nits（移交 00 起草 task 吸收；不退回）

| ID | 位置 | 内容 |
|---|---|---|
| R2-N1 | 头部 track 行（:4）· §1 一句话目标（:44）· test_strategy_note（:23） | 三处仍写「二选一」/「接线或按模式跳过」，与 §2 分支表现实（B-a/B-b/扩展接线/全模式收窄/关闭 五结局）措辞不齐。机制上第三结局两案 = 接线/收窄的扩展形态，无实质冲突；建议 task 阶段或签收前顺手对齐口径 |
| R2-N2 | §2 分支表 B-a/B-b 触发行 | B-a 触发语「supervisor 零消费坐实」在「三模式均零消费」情形下字面也成立，与第三结局行存在触发重叠；§6 新增验收条（:110）已兜底裁定路径，无实质歧义风险。建议 task 把触发写成显式互斥（B-a/B-b 前提 = router/basic 有消费者坐实） |
| R2-N3 | §7 回滚句（:123） | 「回滚：B-a/B-b 均为开关默认关下的行为」未含第三结局两案（扩展接线/全模式收窄同为默认关下行为，回滚语义自然延伸）；建议补「第三结局两案同」 |

## R2-四、HG-SPEC-SIGNOFF 建议（R2 终裁）

**建议维护者可签 HG-SPEC-SIGNOFF**（conditional_pass：R2-N1~N3 为措辞/显式化 nits，不阻塞人签，移交 task 阶段吸收）。本帽**不代签**；人签前维持：不出 task / 不改码 / 30 拒开工。

## R2-五、下一棒

人签（或维护者授权）→ **00 起草 task**（slug=`memory-injection-consumer`，分支 `task/memory-injection-consumer`）：
1. 吸收 R2-N1~N3 + R1 N3（补 `docs/harness/invokes/by-task/memory-injection-consumer/` invoke）进 task；
2. task 草稿 → 20-task-audit → HG-AUDIT-R1 人签 → 30。

| 日期 | 摘要 |
|------|------|
| 2026-10-19 | R2：v0.1 复审——B1/B2/FP-3/§6/N1/N2 六项退回面全部实证闭合，合格面对拍零改动，自锁未破坏；新增 R2-N1~N3 非阻塞；**conditional_pass · 建议可签 HG-SPEC-SIGNOFF（不代签）** |
