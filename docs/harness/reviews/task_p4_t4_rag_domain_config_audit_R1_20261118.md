# R1 审查文 · task_p4_t4_rag_domain_config（2026-11-18）

> **审查帽**：20-task-audit（R1）
> **task**：docs/tasks/active/task_p4_t4_rag_domain_config.md（10 波落卡版）
> **日期**：2026-11-18
> **授权链**：issue Cyning12/ops-desk-workspace#23（m03064/m03796 夜间授权）· 需求真源 workspace 18-p4-generalization-design.md §2.3 RAG 域化 + §10 P4-T4 任务行 + §13 失败路径 · 口径真源 19-p4-contracts.md §4（commit e453a36 钉死）· 委派书 p4-t4-rag-domain-config

## 结论

**GO · PASS · 零阻塞** — task 档范围/非范围/验收/failure_paths/思考轮（R0-R5）齐备，与 19 契约 §4.1-§4.4 钉死口径逐条对齐，修法裁定「collection 三级回退 fail-closed · glossary 按域文件回退+按域缓存 · rag 子任务域闸（本域未配置检索）· 影子写 None-skip · importlib 运行期解析守静态边界 · ingest/source_type 不泛化」为契约内最小改动面，可进 30。

## 核对项表

| 核对项 | 结论 | 依据 |
|--------|------|------|
| 范围-委派书六条全覆盖 | PASS | collection 三级回退（范围 1）· glossary 按域回退+缓存（范围 2）· rag 子任务域闸 fail-closed（范围 3 · 委派书①「不回落 ops_knowledge」实现点）· 影子写 skip（范围 4）· ingest/source_type 不泛化钉死（范围 5 + 非范围 1）· 域解析复用 T2 current_domain（范围 1 _current_domain 单一真源）· 测试五类（范围 6）· 图谱 rag/lg_rag 行备注+签收行（范围 7） |
| 19 §4.1 矩阵逐格 | PASS | ops 链 QDRANT_COLLECTION_OPS→QDRANT_COLLECTION→ops_knowledge（零 diff）· 非 ops 单级 QDRANT_COLLECTION_<DOMAIN_UPPER> 缺省 None · 空白串视同未配置 · domain=None 解析当前部署域——验收 1/2/3 机判锚定 |
| fail-closed 主防线可机判 | PASS | 域闸 output=「本域未配置检索」+ patch astream_router_agent 断言零调用（验收 4）· 影子写 None-skip 零 DLQ（验收 6）· LB3/R-P4-7 跨域泄漏防线闭合 |
| glossary 19 §4.2 口径 | PASS | glossary.<domain>.yaml 存在则读否则 glossary.yaml（回退判定=文件存在 · 坏件显式炸承 T2 口径）· 按域缓存 _TABLES · 不交付 oa glossary（刻意不交付死配置 · 验收 5） |
| 非范围-静态边界 | PASS | .importlinter 零触（非范围 4）· rag→prompts 与 lg_rag→rag.backend 走 importlib 运行期解析（承 lg_rag/continuity.py→session.summary 先例）· lg_rag→prompts 静态合法（nodes.py:76 既有边）——契约面与修法面一致 |
| 非范围-T2/T5/ingest 边界 | PASS | T2 prompt 面仅消费不动 · T5 oa 资产不交付 · ingest.py 零 diff 机判（验收 7 · 19 §4.3 钉死） |
| 失败路径完备 | PASS | 跨域泄漏/解析失败回落/空白串/缓存串扰/静态边界/ops 漂移/并行冲突/环境性红八条——每条含处置与防线归属；「解析失败回落 ops」的残余风险已显式登记（前提=domain_context 仓内 stdlib-only） |
| 思考轮 R0-R5 控制 | PASS | actual_last_round=R5 · 各轮有实质结论（R3 关键决策五条含裁定理由）· 无空转轮 |
| 过闸体例 | PASS | Harness 元信息表齐（base=370a137a · graph_change_layer=G-L1 · review_hat=20 · wiki_delta=n/a）· 人工闸表三行 approved 注授权真源 · registry entry status=active 字段齐（allowed_app_files 四件/allowed_tree_files 六件/banned_prefixes=[alembic/, scripts/]）· 照 task_p4_t2_prompt_domain_loader 体例 |

## 关键决策复核

- **importlib 运行期解析双处**（backend._current_domain · nodes.py 闸内 qdrant_collection）：守 rag-outbound/lg-rag-outbound 静态 forbidden，.importlinter 零改动，承仓内既定先例（continuity.py）——裁定成立，图谱备注级登记义务已入范围 7。
- **闸插点**（emit_subtask_running 之后、set_chain_step_hook 之前）：running 帧保 §10.7 UX，未装 hook 不触 astream ⇒ 「后端调用零发生」可机判——裁定成立。
- **影子写 skip 而非 DLQ**：collection None=禁用域预期态非故障，DLQ 留真故障——裁定成立且 ops 域零 diff（ops 链恒非 None）。
- **qdrant_retriever.py:38 不加 None 闸**：非子任务路径在契约 fail-closed 面外，维持现有异常→fallback 行为——裁定成立，已入限制登记 1，最小改动面。

## 偏差确认

- 10 波纯文档面零 app 代码改动，无偏差；30/40 波偏差回填义务已写入实现备忘占位。

## 机读通过词

PASS（npx --yes spec-wave@3.5.0 task lint --target . --task docs/tasks/active/task_p4_t4_rag_domain_config.md）
