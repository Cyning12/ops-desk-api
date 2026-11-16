# R1 审查文 · task_fix_planframe_truncation

> **审查帽**：20-task-audit（R1）
> **task**：docs/tasks/active/task_fix_planframe_truncation.md
> **日期**：2026-11-17
> **授权链**：issue Cyning12/ops-desk-workspace#23（m03064/m03283/m03694 夜间授权）· 发现真源 workspace docs/01-scope/03-general-agent/13-p2b-skill-verification.md §7.1（P2b-T5a 附带发现 · H1b/H2b/H3c 恰 800 截断实测）· 委派书 fix-planframe-truncation

## 结论

**GO · PASS · 零阻塞** — task 档范围/非范围/验收/failure_paths/思考轮（R0-R5）齐备，与委派书四条（勘察截断点 · 裁定修法 · 改动+测试 · 图谱+freeze 核实）逐条对齐，修法裁定「落库全文 · SSE 帧面截断保持」为委派书预批倾向，可进 30。

## 核对项

| 项 | 结论 | 依据 |
|----|------|------|
| 范围5条 ↔ 委派书 | 一致 | 拆两常量+persist_node_payload 落库全文 · resume 同修 · history 读时截断 · 真 PG 测试 · 图谱签收+freeze 核实 · 过闸落盘 |
| 非范围 | 一致 | SSE 面 800 口径数值不动 · runs_router/event_store/map_node_update 签名零触 · 存量不回填 · alembic//scripts/ 禁入 · freeze 词表不动 |
| 验收标准 | 8 条全机判锚 | SSE 面零 diff · 落库全文新断言 · resume 同修新断言 · history 读时截断新断言 · 七文件回归+全量 · ruff · 图谱两件 · 过闸四件 |
| failure_paths | 6 条 | 保险丝命中 · 键集漂移 · 读时截断遗漏 · 并行冲突 · 环境性红对照 · 脏树期 registry 红常态 |
| 思考轮 | R0-R5 齐 · actual_last_round=R5 | 表头 `| 轮 | 结论 | early_stop |` 合规 |
| 人工闸表 | 三行 approved | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES · issue #23 授权 |
| 体例 | 照 fix-434 done 模板 | registry/invokes/图谱签收承 fix-434-worker-thread-upsert 先例 |
| 仓规条款一 | 遵守 | 本审查文即 20-R1 路径 · 未用 --allow-no-review |

## 关键决策复核

- **截断点定位准确**：sse_stream.py:68 `_PAYLOAD_MAX=800` + :90-128 `_summarize_payload` 逐 key json.dumps 后超 800 截断为字符串；emit（:279-329）`p_payload = payload`（:305）同一 dict 双用 SSE+persist——落库即截断形态，与冒烟 §7.1「恰 800 字符」实测吻合。第二路径 hitl/resume.py:155-156 `map_node_update` 截断 payload 直接 persist，同修必要。
- **拆两常量成立**：_PAYLOAD_MAX=800 为 SSE 推送面尺寸契约（前端零影响必须保持）；落库面无需该上限但需保险丝——_PERSIST_PAYLOAD_MAX=32_000 对齐 `_ANSWER_MAX=32_000`（sse_stream.py:69 answer 终帧先例），非无限大，兜病理尺寸。
- **参数化单一真源**：`_summarize_payload(node_output, max_len=_PAYLOAD_MAX)` 默认参数保既有调用零 diff；`persist_node_payload` 调同一实现传 32_000——键集/结构同一真源，防未来只改一处的漂移。
- **emit kw-only persist_payload=None**：run.start/hitl.waiting/done/error 等帧型不落双面（None→落本体零 diff），仅节点帧（:461-474 主循环）传双面；map_node_update 签名不变（freeze 面 · 3 元组保持，多测试直接调用 :384-393 等不受影响）。
- **history 读时截断必要**：history.py:217 注释假设「帧内已是截断过的安全大小」在落库全文后破；summarize_subtasks 透传四键中 subtask_result/answer_preview 为风险键，读时截断 ≤800/≤200 承 SSE 旧口径，history 响应尺寸契约保持。message/step 为模板生成短文本（build_subtask_done_message ≤200 口径）不触。
- **回放端点零改动成立**：runs_router.py:122-154 payload 原样透传（500 帧分页 + event_store.py:529-538 白名单 SQL 过滤），落库全文即回放全文。
- **freeze 核实成立**：05 spec 钉 answer 32_000 截断、message ≤200、input/detail「截断预览」字样，未钉 node.progress 键值 800 上限——帧类型不变、仅持久化内容长度变，lg-rag-sse-v1 freeze 词表不受影响，workspace 契约文档无需同步。

## 偏差确认

无（委派书四条全覆盖 · 无裁剪）。

## 机读通过词

PASS（spec-wave task lint 命令：`npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_fix_planframe_truncation.md`）
