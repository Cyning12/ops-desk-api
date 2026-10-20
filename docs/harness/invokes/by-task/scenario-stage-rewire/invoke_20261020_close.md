# invoke · CLOSE（scenario-stage-rewire · 2026-10-20）

## 归档
- task 移 docs/tasks/done/task_scenario_stage_rewire.md（done/ 移动面已预登记 #3 闸白名单 · O1 裁定预防件）
- PR #286（task/scenario-stage-rewire → master）

## 五棒流闭环
- SPEC signed（2026-10-19 维护者 · 裁定 (a) 摘除）→ 10-task（188 行 lint PASS）→ 20-task-audit R1=conditional_pass（阻塞 0 · 锚点 20 命中/2 漂移）→ HG-AUDIT-R1=approved（00 代签）→ 30（红测 4 红→35 绿 · TC1–TC10 全 ✅）→ 40=approve（阻塞 0 · 复跑 1743/0）→ PR CI 4/4 绿

## 棒内裁定链（00 裁定 · 均有 invoke）
1. 跨波次基线闸修正：#2 闸固定基线跨波次失效（master 自 PR #285 即红 · CLOSE done/ 面未登记）→ _resolve_base 四态化 + done/ 补登记（invoke_20261020_30_cross_wave_base_fix.md）
2. O1 预防：#3 闸同款四态化 + CLOSE 移动面预登记 + _WAVE_TIP 占位（merge 后钉锚）
3. O2：banned 禁区断言先于态 3 skip（untracked 防绕过实测截停）
4. O4：builder.py docstring 重复句去重

## 遗留挂账（移交）
- multi/__init__.py:5 过期 docstring → #5 图谱波次清扫
- dormant audit 性质无覆盖（O3）→ 复用须另立 SPEC 时补测
- builder 直导循环 import 预存 · sse_stream.py:64 / intent.py:94 留尸（D6 互锁登记）
- GATE_VERIFY 机读误报第三次（闸表真值为准 · 机读启发式待修）

## merge 后动作
- _WAVE_TIP 钉锚为 #3 合并 commit（态 2 牙全量生效）· 00 落 master 小提交并验证
