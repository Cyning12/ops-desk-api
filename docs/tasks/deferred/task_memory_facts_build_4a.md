# task（对接草案 · 未排期）：memory-facts 真实构建（原 memory-injection-consumer 结局 ④a）

> **状态**：deferred 对接文档，**不是 active task**（受 PRIORITY_DEFERRED DEF-005 保护，拒开工）。  
> **由来**：2026-10-20 维护者裁定 memory-injection-consumer Phase B 走 ④b（全模式收窄 + 功能休眠）；同示「未来走 ④a 即真实构建 memory-facts 之时」，留本文档对接，**开工前须先做遗留问题分析**。  
> **前置真值**：SPEC docs/spec/memory-injection-consumer/SPEC-memory-injection-consumer_v0.md · Phase A 实证 docs/harness/invokes/by-task/memory-injection-consumer/invoke_20261019_30_phaseA_spy_matrix.md · ④b 实施 task docs/tasks/done/task_memory_injection_consumer.md（CLOSE 后）。

## 触发条件（Revisit）

维护者显式下令「真实构建 memory-facts」→ 删除 PRIORITY_DEFERRED DEF-005 行 → 走 00/10 正式开 task。

## Phase A 实证基线（④b 实施前的零消费事实，接线工作的起点）

- 注入块（facts + episodes）在 basic / router（rag 回环+direct）/ supervisor（planner/内层工人/aggregator）**三模式 9 个 LLM 消费点全零到达请求面**；唯一编程读取点为 continuity.py 装配幂等去重。
- 各消费点 user prompt 构造现状：nodes.py classify :83-89（query 原文）/ rewrite :214-220（original）/ direct :255-266（_last_user_text）；multi/nodes.py planner :1163-1170（_last_user_text）/ 内层工人 classify :1432（子任务原文）/ aggregator :2110-2123（原始问题+子任务JSON）；basic 链 grader/answer（lc_evidence_chain）。

## 开工前遗留问题分析清单（维护者 2026-10-20 令：先分析再动工）

1. **supervisor 复装配双注入**：内层 rag 工人复走装配（episodes recall 被调 2 次；user_id 未传致 facts skip continuity.py:458、tenant 在 episodes 不命中 :500 skip 再注入）——接线前须定「每请求注入一次」语义与跨层传递方式。
2. **逐点接线设计**：9 个消费点各自定「注入块进哪几次 LLM 调用、放在 system 还是 user、与 query_rewrite 改写后文本（先重写后召回钉死）的相对顺序」；basic/router 回环多次调用的成本与去重。
3. **块总量上限复评**：④b task 定值 8000 字符（超截尾 + span memory_injection_truncated=true）——④a 真实消费后复评该上限与截尾策略。
4. **开关矩阵**：MEMORY_FACTS_* / MEMORY_EPISODES_* / MEMORY_FACTS_VECTOR_RECALL_ENABLED 与向量召回分流的组合语义（Phase A 实测：向量分流可绕过 recall_active mock）——接线后开关默认值与灰度路径须重定。
5. **休眠声明回收**：④b 落的功能休眠声明位置即 ④a 的摘除点，接线 PR 须同步回收声明。
6. **金样与评测**：金样仅中文三类（#1 residual 同源）；④a 须带 golden-eval 口径（含「注入生效」正向断言与「注入关」零 diff 对拍）。
7. **历史窗口径**：query_rewrite 重写器吃原始历史窗 [-6:]（#1 40-O1 挂账）——memory 注入与历史窗/压缩历史的口径须统一设计。
8. **环境卫生**：本机 .env 泄漏致 16 项 capability/strategy 预存失败（#1/#2 反复挂账）——建议先立治理任务，否则 ④a 验收噪音大。

## 非范围（对接草案口径）

- 不动 memory 写入侧（extract/store/recall 生成逻辑）——本文档只管「注入块 → LLM 消费面」的接线。
- 不在本草案期改任何 app/ 代码。
