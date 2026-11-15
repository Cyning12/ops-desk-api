# R1 审查 · task_p2a_t1_panel_list_tools

- 时刻：2026-11-16 · 审查人：执行代理（夜间授权窗口 · 授权 issue Cyning12/ops-desk-workspace#23 m03064 + 08 设计终稿）
- 对象：task 档 + registry entry + 勘察定论（R0）

## 审查项

1. 范围与 08 §7 T1 行逐字对齐：两枚列表 adapter + manifest +2 + supervisor allowlist +2 + span tenant_id + mock 收窄 + 测试基座，无溢出（T2 get_overview/graph_snapshot · mock 退役 · EXTRA_MANIFESTS 通路 · nodes.py 均明确非范围，承 §8）。
2. 红线：禁 freeze 帧/schema 触碰 · 禁图改动（span 仅 payload 元数据补全一行 · R3 签收条件）· 禁新 DDL/依赖——task 档失败路径与验收逐项可机断。
3. 契约：adapter 显式校验 page≥1、1≤page_size≤20、state 词表（R1：schema_validate 不校验 enum/min/max）；返回剔 uuid id 不带 body；tags=panel+域+readonly；output_schema 仅 required 三键口径。
4. 勘察定论复核：ci_status 词表不可钉（仓内无生产写入方 · admin/sender/mapper.py:93 恒 None）→ string 放行+description 列已知值，方向与 §1.3 一致；when_to_use loader 必填冲突（manifest.py:523-526）裁定为偏差登记，语义让位 loader 硬约束，合理。
5. registry allowed 面完整（app 5 文件 + tree 8 文件含三处存量锚推进 + invokes 前缀 · banned=alembic//scripts//app/ops/lg_rag/ · 偏差三条如实登记）。
6. 思考轮：R0-R5 槽位齐 · R5 early_stop 理由成立（设计终稿即审计真源 · 验收全机断）。

## 结论

GO，可进 30 实施（夜间授权窗口 · 30 台账见 invoke_20261116_30_impl.md · 40 验收台账见 invoke_20261116_40_acceptance.md）。
