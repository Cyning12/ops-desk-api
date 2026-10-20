# invoke · 30 Phase A · memory-injection-consumer 实证矩阵（spy 实录）

- **帽**：30（实现者，委派子代理） · **日期**：2026-10-19
- **分支**：task/memory-injection-consumer（自 docs/task-memory-injection-consumer 尖端 414270d 切，同 #1 先例）
- **范围**：**Phase A only**（观测-only · 零生产码改动）；HG-PHASE-B-DECISION 仍 pending，本棒不触任何 Phase B 结局实施
- **闸链**：HG-AUDIT-R1=approved（2026-10-19 维护者授权 00 代签，见 invoke_20261019_gate_sign_hg_audit_r1.md）

## GATE_VERIFY 误报记录（沿 #1 先例，以 task 闸表真值为准）

`npx spec-wave verify --target . --task docs/tasks/active/task_memory_injection_consumer.md`
输出 HG-AUDIT-R1=approved ✅、HG-GRAPH-MODULES=approved ✅，但将 HG-PHASE-B-DECISION=pending
粗粒度判为 blocks 30 → VERIFY: BLOCKED EXIT=2。**此为误报**：task 人工闸表 :40 明示
「Phase A（观测-only）不受本闸阻塞」，blocks_hats 实为「30（Phase B）」。沿 #1 先例以
task 闸表真值为准继续 Phase A，误报记录于此。另：HG-TASK-DRAFT 显示 pending 系 task 头部
状态行残留 draft 措辞，闸表真值 HG-AUDIT-R1=approved。

## 方法（task 为唯一真值）

SpyProvider（tests/test_memory_injection_consumer.py）逐次记录每次 complete/complete_stream
的消息清单快照；哨兵 FACT_VALUE=PHASEA-SENTINEL-FACT-7f3d2c、PREF_VALUE=PHASEA-SENTINEL-PREF-51aa、
EPISODE_SUMMARY 含 PHASEA-SENTINEL-EPISODE，加三个 HEADER（continuity.py:128/:130/:200）组成
markers，命中 LLM 请求面即「消费」。patch 点（全 monkeypatch，测试内自恢复）：
app.ops.lg_rag.nodes.get_llm_provider、app.ops.lg_rag.multi.nodes.get_llm_provider、
app.ops.lc_evidence_chain.grader.get_llm_provider、app.ops.lc_evidence_chain.answer.get_llm_provider、
app.ops.lc_evidence_chain.chain.retrieve_evidence、app.ops.lg_rag.nodes.ainvoke_evidence_answer（仅
supervisor 场景）、app.ops.memory.service.recall_active、
app.ops.memory.episode_service.recall_success_episodes；tracing 四处置 False + LANGFUSE 双键
delenv（本机 .env 免疫）。**.env 泄漏修复实录**：首版 fixture 漏 delenv
MEMORY_FACTS_VECTOR_RECALL_ENABLED——本机 .env 置 true 触发 continuity.py:464 向量分流
（recall_with_vector 绕过 recall_active mock）致 4 场景装配面缺 facts 块全红；补 delenv 后
.env 在场/parked 双跑均 7/7 绿（hermetic 达成）。每场景先断言装配面（注入块确在 state.messages），再断言消费面零命中——
防止「装配没发生」造成空转绿；另有 test_spy_assertion_has_teeth 自牙测钉死断言器有效性。

## 实证矩阵（注入开 MEMORY_FACTS_ENABLED=true ∧ MEMORY_EPISODES_ENABLED=true × 三模式）

| 模式 | 节点（LLM 消费点） | user 消息构造证据（base 414270d 行号） | facts/prefs 块 | episodes 块 |
|---|---|---|---|---|
| basic | chain grade_chunk · lc_evidence_chain/grader.py:28 | query+证据批（chain 内部拼装） | **未收到** | **未收到** |
| basic | chain answer_question · lc_evidence_chain/answer.py:153 | query+kept 证据 | **未收到** | **未收到** |
| router | router_node.classify · lg_rag/nodes.py:83-89 | :86 user=query 原文 | **未收到** | **未收到** |
| router | rewrite_node · lg_rag/nodes.py:214-220 | :217 user=original query | **未收到** | **未收到** |
| router | direct_answer_node · lg_rag/nodes.py:258-266 | :255/:262 user=_last_user_text（纯 query，非整包 state.messages） | **未收到** | **未收到** |
| router(rag) | chain grader ×2 / answer ×1（rewrite 回环：irrelevant→refuse→rewrite→exact→answer） | 同 basic | **未收到** | **未收到** |
| supervisor | supervisor_node.planner · multi/nodes.py:1163-1170 | :1106/:1167 user=_last_user_text | **未收到** | **未收到** |
| supervisor | 内层 rag 工人 classify（astream_router_agent · multi/nodes.py:1432） | user=子任务 input 原文 | **未收到** | **未收到** |
| supervisor | aggregator_node · multi/nodes.py:2110-2123 | :2040-2041 user=原始问题+子任务结果 JSON | **未收到** | **未收到** |
| supervisor | critic / strategy_builder / observe（默认路径） | 规则实现无 LLM：app/ops/strategy/ 全目录 grep 零 provider；observe _satisfied_by_model 受 LG_RAG_REACT_SATISFACTION!=1 默认短路（multi/nodes.py:1676）；multi spy 全程仅 2 次调用实证拓扑 | n/a | n/a |

装配面 recall 计数（AsyncMock await_count 实证）：

| 模式 | facts recall | episodes recall | wiring 证据 |
|---|---|---|---|
| basic | 1 | 1 | 入口装配单点 |
| router | 1 | 1 | 同上 |
| supervisor | **1** | **2** | 内层 rag 工人复跑 astream_router_agent 复装配：user_id 未传 → facts skip（continuity.py:458 tenant/user 缺一即跳）；tenant ContextVar 仍在 → episodes 不命中 :500 skip，再注入一次（进工人 state.messages，但仍不进任何 LLM 请求） |

**结论边界**：「零消费」精确含义 = 注入块零到达 LLM 请求面 ∧ 无节点以编程方式读取块内容
（唯一读取点 continuity.py:546-548 为装配幂等去重，属装配内部）。注入块确存在于
state.messages（每场景 _assert_assembled 钉死，checkpoint 持久化可见）。

## 五结局证据命中情况（task :83-87 互斥结局）

- 结局①（三模式均有消费者 → 疑点推翻关 task）：**未命中**——无任何节点消费。
- 结局②/③前提（supervisor 零消费 ∧ router/basic 有消费者）：**未命中**——router/basic 亦零消费。
- 结局④前提（三模式均零消费）：**命中**——三模式全部 LLM 消费点（grader/answer/classify/
  rewrite/direct/planner/aggregator/内层 classify）均未收到 facts/prefs/episodes 块。
  → 裁定空间落在 ④a（扩展接线）/ ④b（全模式收窄），**归 HG-PHASE-B-DECISION 裁定，本棒不实施**。
- FP-9 触发象限（supervisor 有消费 ∧ router/basic 零消费）：**未命中**，无需走 N1 径。

## 测试结果（CI 等价：park .env 跑后复原）

- 新文件：tests/test_memory_injection_consumer.py **7/7 全绿**（0.19s）。
- 全量回归（.env parked）：**1908 passed / 4 failed / 1 skipped**（36s）。4 失败全部环境依赖、
  与本 diff 无关：test_memory_vector_p1 embedder 项缺 SILICONFLOW_API_KEY（.env 复原后转绿，
  已对拍）；test_hitl.py:420 asyncpg 与 test_multi_replica_dualproc ×2 需本机 live PG
  （.env 复原后仍失败，属已知基线：本机无 PG 实例）。本 diff 为纯新增测试文件，未触
  conftest/共享 fixture，旧测行为按构造不受影响的判断已由失败签名（DB 连接/embedder key）
  证实。
- ruff check app tests：**All checks passed**。
- 红测说明：断言全部按读码对拍后的真实行号/协议书写并首开即绿；防空转绿由
  test_spy_assertion_has_teeth（含哨兵 RecordedCall 必 raise）+ 每场景装配面先行断言承担。

## 禁区自查

- diff 面：仅 tests/test_memory_injection_consumer.py（新增）+ 本 invoke 文档；
  test_phase_a_diff_whitelist 以白名单形态（^(tests/|docs/harness/invokes/by-task/
  memory-injection-consumer/)）+ 显式黑名单（^(app/|scripts/|alembic/)，含 untracked）
  在测试内持续强制（N2 吸收）。工作区预存 untracked backups/ 与旁案 review 文档未动。
- 未动 app/ 任何生产码；未碰 Phase B 任何结局实施；未改 task/SPEC/闸表。
- 未开 PR。
