# R1 审查 · task_p2a_t2_panel_aggregate_tools

- 时刻：2026-11-16 · 审查人：执行代理（夜间授权窗口 · 授权 issue Cyning12/ops-desk-workspace#23 m03064 + 08 设计终稿）
- 对象：task 档 + registry entry + 勘察定论（R0）

## 审查项

1. 范围与 08 §7 T2 行逐字对齐：两枚聚合 adapter（get_overview/graph_snapshot）+ manifest +2 + supervisor allowlist +2 + 测试基座，无溢出（面板端点改动 · adapter 白名单扩容 · nodes.py · SSE 帧 · 新 DDL/依赖 · mock 退役均明确非范围，承 §8）。
2. 红线：禁 freeze 帧/schema 触碰 · 禁图改动 · 禁新 DDL/依赖——task 档失败路径与验收逐项可机断。
3. 契约：get_overview 无参数钉死（properties:{} + additionalProperties:false）· 返回逐键对齐 overview.py:169-180 · 空数据 null 逐键声明 · 禁「实时」；graph_snapshot view 词表 adapter 显式校验（R1：schema_validate 不校验 enum/min/max 既有事实）· 统一外壳 + scope:"global_repo" 常量；tags=panel+域+readonly。
4. 勘察定论复核：graph payload 为 kimi-code 外部自由 dict → module 过滤键缺失/结构漂移必须 fail-visible（warning:"module_filter_no_match" + 未过滤摘要），方向与 §1.5 一致；when_to_use loader 必填冲突（manifest.py:523-526）承 T1 偏差先例填简短引导，when_not_to_use 不填。
5. registry allowed 面完整（app 3 文件 + tree 含六处存量锚推进与新增测试 + 01_modules + registry + review + task active/done · invokes 前缀 · banned=alembic//scripts//app/ops/lg_rag/ · 偏差如实登记）。
6. 思考轮：R0-R5 槽位齐 · R5 early_stop 理由成立（设计终稿即审计真源 · 验收全机断）。

## 结论

GO，可进 30 实施（夜间授权窗口 · 30 台账见 invoke_20261116_30_impl.md · 40 验收台账见 invoke_20261116_40_acceptance.md）。
