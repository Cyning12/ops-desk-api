# Invoke：memory-injection-consumer · 10 任务起草（2026-10-19）

- **hat**：10-task · **task**：docs/tasks/active/task_memory_injection_consumer.md（draft · HG-AUDIT-R1=**pending** · HG-PHASE-B-DECISION=**pending**）
- **建议序**：2/5（query-coref-rewrite 已随 PR #284 合入 master → **本 task** → scenario-stage-rewire → delegation-naming-boundary → tech-graph-flow-resync）
- **分支**：`docs/task-memory-injection-consumer`（自 master fc5d9bd 切出 · 已核 `git branch --show-current`）；30 开工分支 `task/memory-injection-consumer` **未切**，30 开工前按 task 文件自 master 切出
- **写入面**：仅 task 文件 + 本 invoke（两处分）；零 `app/` / `tests/` 改码

## 一、签收与审查依据（R1→v0.1→R2 链）

| 依据 | 实录 |
|------|------|
| SPEC 签收 | `docs/spec/memory-injection-consumer/SPEC-memory-injection-consumer_v0.md` 状态行（:3）：`signed`（**HG-SPEC-SIGNOFF=approved · 2026-10-19 维护者会话签收** · 20-spec-audit R2 终裁 conditional_pass）· §9 修订记录（:164-166）v0 draft → v0.1 修订 → 人签三行同载 |
| R1 审查 | `docs/harness/reviews/spec_memory-injection-consumer_audit_R1_20261019.md`：R1 **fail**（阻塞 B1 现状锚点自述与代码矛盾 · B2 分支表漏「三模式均零消费」结局；非阻塞 N1–N3）→ 退回 10-spec |
| v0.1 修订 | SPEC §2 分支表新增第三结局行（:66 双案并列：扩展接线 / 全模式收窄）· 现状锚点末条改写（:10 三模式均疑似零消费）· FP-3 双分支判定（:97）· §6 验收新增第三结局条（:110） |
| R2 复审 | 同审查文文末「R2 复审（2026-10-19）」节（:110-152）：B1/B2/FP-3/§6/N1/N2 六项退回面全部实证闭合 · 合格面对拍零改动 · 自锁未破坏 · **conditional_pass · 建议可签 HG-SPEC-SIGNOFF** · 新增 R2-N1~N3 移交 00/task 吸收 |
| 下游链 | HG-SPEC-SIGNOFF=approved → 00 出 task（本棒 · R2-五下一棒 :146-148）→ 20-task-audit → HG-AUDIT-R1 → 30 |

## 二、R2-N1~N3 吸收位置索引（task 文件行号）

| nit | 审查文原文坐标（R2-三节） | task 吸收位置 |
|------|--------------------------|---------------|
| **R2-N1** 三处「二选一」口径与 §2 五结局不齐 | 审查文 :136（track :4 · §1 :44 · test_strategy_note :23） | task :18（test_strategy_note 改五案口径）· **:50-52（「目标」节口径对齐段：点名三处残留坐标 · 全文统一五结局口径）** · :196-198（R2 轮裁定）· :219（自检可追溯行）· :230（修订记录） |
| **R2-N2** B-a 触发语与第三结局行重叠，需显式互斥（B-a/B-b 前提=router/basic 有消费者坐实） | 审查文 :137 | task :75（Phase B 节标题「触发显式互斥」）· :79（互斥声明段）· **:84-85（②B-a/③B-b 触发行补「且 router/basic 有消费者坐实」前提）** · :86-87（④a/④b 前提=三模式均零消费）· :199（R2 轮：结局空间完备无漏论证）· :219（自检） |
| **R2-N3** §7 回滚句未含第三结局两案 | 审查文 :138 | task **:91（回滚段：第三结局两案同为默认关下行为 · 扩展接线回滚=移除接线恢复原组装 · 全模式收窄回滚=恢复注入查询路径）** · :200（R2 轮）· :230（修订记录） |
| （附带）R1 N3 pre-30 invoke 缺失 | 审查文 :88 | 本 invoke 即补落 `docs/harness/invokes/by-task/memory-injection-consumer/` 首篇 |

## 三、亲读复核实录（起草前真读 · master fc5d9bd · 不全信审查文转述）

| 锚点 | 实录 |
|------|------|
| `app/ops/lg_rag/nodes.py:48-53` | ✅ `_last_user_text` 仅取末条 HumanMessage（:50 `type=="human"` 判定）——注入块是 SystemMessage 天然不可见 |
| `nodes.py:119` router_node | ✅ `query = _last_user_text(state["messages"])` → `_classify_route(query)` |
| `nodes.py:153-154` rag_node | ✅ `query = state.get("current_query") or _last_user_text(...)` → `ainvoke_evidence_answer(query)` 只传 query 字符串 |
| `nodes.py:209-218` rewrite_node | ✅ `provider.complete([system=render("lg_rag.rewrite.system"), user=original])` 双消息重建 |
| `nodes.py:255-263` direct_answer_node | ✅ `complete_answer_streaming(provider, [system=render("lg_rag.direct.system"), user=query])` |
| `graph.py:56-62` basic 图 | ✅ `START → rag → END`，唯一节点即 rag_node |
| `multi/nodes.py:1163-1170` planner | ✅ `provider.complete([system, user=query])` 注入块不进 prompt |
| `multi/nodes.py:2035-2043 / :2046-2048` aggregator | ✅ off 态 `(query, payload)` 两参 · on 态 `(query, results, payload)` 三参，均无 history |
| `multi/nodes.py:1432-1435` rag 工人 | ✅ `astream_router_agent(result["input"], thread_id=...)` 未传 `history_turns` |
| `multi/nodes.py:1041-1063` `_worker_state` | ✅ :1054 `"messages": list(state.get("messages") or [])` 在册但 rag 工人路径只用 `result["input"]` |
| `graph.py:199-206 / :278` | ✅ fresh 装配 `assemble_graph_messages_with_memory` 入 payload · `history_turns: list[dict] | None = None` 缺省 |
| **continuity.py 行漂移（校正）** | SPEC/R1 录 `inject_memory_facts_block` :341-354；PR #284（query-coref-rewrite）合入后实测 **:349-362**（def :349 · 空块原样返回 :354-355 · 插入 return :362）；episodes 落点 **:527**（`inject_memory_facts_block(messages, episode_block)`）· `render_memory_episodes_block` :316 · `MEMORY_EPISODES_HEADER` :200；开关 `memory_facts_enabled` :142-151 / `memory_episodes_enabled` :208-222（SPEC 录 :134-144/:200-215，同因漂移）。**机制逐字一致，仅行号漂移**；task「依赖」节已按校正后行号落盘并注明「30 按实校正」 |
| HG-GRAPH-MODULES 真值 | `docs/_tech_graph/l1/01_modules.md:61` 起闸登记表在册 approved（`memory` 行 :36 · `lg_rag` 行 :35）；graph_change_layer=none 预期不再签，沿用在册状态 |

## 四、产出与闸态

- task 草稿：`docs/tasks/active/task_memory_injection_consumer.md`（Phase A 观测-only + Phase B 五结局完备预写 · 非范围十条（SPEC 五条原样 + task 级五条）· FP-1~FP-9 · TC1–TC12 · R0–R5 思考轮 actual_last_round=R5 · 自检结论六行）
- **Phase A/B 结构与裁定点设计**：Phase A（spy 矩阵实证三模式注入消费面 · 观测-only 零生产码 · TC5 diff 面断言兜底）先行 → **HG-PHASE-B-DECISION 显式裁定点**（新增人工闸 · 维护者或经授权 00 按 Phase A 证据落签 · 裁定记录位=task 闸表 + invoke · 写明「因实证行 X → 裁定结局 Y」）→ Phase B 按裁定结局实施；SPEC §2 自锁条款原样继承（FP-9：表外方案拒）
- 人工闸表：HG-SPEC-SIGNOFF=approved（2026-10-19 维护者 · 有依据）· **HG-AUDIT-R1=pending（00/AI 本帽不代签 · 维护者授权 00 代签后续文档闸的落闸动作在 20-task-audit 之后由 00 执行）** · HG-GRAPH-MODULES=approved（在册 · none 预期不再签）· **HG-PHASE-B-DECISION=pending（新增裁定点闸 · blocks 30 Phase B）**
- 本帽定值：接线案注入块总量上限 **8000 字符**（SPEC §7「task 阶段定数值」授权 · 承窗先例 4000×2 量级 · 超截尾 + span `memory_injection_truncated=true`）
- test_strategy=required · graph_change_layer=none · review_hat=20 · invoke_retention_profile=default（10,20,30,40）
- lint：`npx spec-wave task lint --file docs/tasks/active/task_memory_injection_consumer.md` → **PASS**（exit 0 · E1–E8 零 error · W 零提醒）
- 下一棒：20-task-audit R1 → 00 落签 HG-AUDIT-R1（维护者授权范围内）→ 30 Phase A（红测先行 · 零生产码）
