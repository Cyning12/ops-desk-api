# invoke · 10 起草 · p2c-t1-planner-tool-awareness

> **task_slug**：p2c-t1-planner-tool-awareness
> **日期**：2026-11-17
> **授权**：issue Cyning12/ops-desk-workspace#23（m03064/m03734 夜间授权 · 委派书 p2c-t1-planner-tool-awareness）

## 内容

1. 落卡 docs/tasks/active/task_p2c_t1_planner_tool_awareness.md（体例照 docs/tasks/done/task_fix_planframe_truncation.md）：Harness 元信息表（task_slug/base=b8d11262/关联 issue/wiki_delta n/a/graph_change_layer G-L1/review_hat 20）· 人工闸表三行 approved · 背景（12 §5-1 退化实测 + §5-2 shadowing 残余 + 13 §7-2 fail-closed + 退化机理）· 范围 6 条 · 非范围 5 条 · 失败路径 8 条 · 验收标准 9 条 · 必读列表 · 思考轮 R0-R5（actual_last_round=R5）。
2. 勘察结论入档：退化机理 = 模板 lg_rag.supervisor.system.md v3 无「何时该选工具」正向引导 + 无 few-shot + 「简单问题只给 rag」单边引导；catalog 行被动罗列缺决策锚。
3. 硬化设计定稿：新增 _build_catalog_block(caps) 唯一装配点 + _TOOL_AWARENESS_GUIDANCE 静态常量（选择原则 + 1 条 JSON few-shot + rag 兜底从句 · 零 capability id）；_format_capability_catalog 本体零改；supervisor_node 装配改调新函数（suffix/base 两路自动覆盖）；模板资产 v3 零 bump。
4. §5-2 裁定登记：Host 侧 description 首句二次蒸馏本波不做（透传 ~100% 属实但重写同源不可信文本无法中和投毒 · 真缓解属 server 向 G12 翻译器策略 · 蒸馏增预算无选定率收益）。
5. registry entry（status=active · base=b8d11262 · allowed_app_files=[app/ops/lg_rag/multi/nodes.py] · banned_prefixes=[alembic/, scripts/]）。

## 验证台账

| 检查 | 结果 |
|------|------|
| npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_p2c_t1_planner_tool_awareness.md | PASS |
| npx spec-wave verify --target . --task docs/tasks/active/task_p2c_t1_planner_tool_awareness.md | 人工闸三行 approved（30 放行依据） |

## 偏差

无。

## 结果

10 起草完成 · 进 20-R1 审查文。
