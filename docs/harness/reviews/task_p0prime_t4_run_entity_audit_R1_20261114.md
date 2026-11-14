# R1 审查：p0prime-t4-run-entity

- **日期**：2026-11-14 · **审查人**：维护者授权 00 代录（m00177「签收，开始」覆盖 P0' T1–T7）· **结论**：approved

## 审查面

1. **裁定符合性**：列清单、run_id 型、不加 FK、uq 不动、orphan 改走 runs 表——逐条对齐 A1 原文；T3 先行（关键链）已闭环（1456f3b9/cc622403）。
2. **风险**：① 状态更新反噬事件插入——独立 try 隔离已入设计；② 长 run 误伤——末帧活跃度判定保留；③ tenant 补行不可知——DEFAULT '' + 记注，承 ops_capability_notes 先例；④ CI 无 PG 假绿——本地真 PG（brew postgresql@18 + opsdesk_test）实证，CI 缺口已登记 issue #23 另 task 议。
3. **freeze 红线**：零帧格式变更；replay/resume 读面不动。
4. **范围纪律**：ops_goals（T5）不混入；checkpointer（T3）不再动。

## 签收

HG-AUDIT-R1 approved。
