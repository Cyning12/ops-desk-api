# R1 审查 · fix-432-replay-owner-race（2026-11-17）

## 结论

GO · 通过（本审查已核对范围/非范围/验收/失败路径与先例对齐 · 轻量测试侧修复卡 · 承 #384 波先例裁定 · 风险面收敛 · 零阻塞）。

## 核查项

1. **机制链闭合**：load_events_after（event_store.py:361）→ :381 assert_run_owned → :354 run_owner 反查 OpsLgRagRunEvent 事件表 → 行未对其它会话可见即 owner=None → :356 抛 LgRagRunNotFoundError，抢跑于 :382-383 在飞闸（应抛 LgRagRunInFlightError）。与 #384 波 TC-B4 实证根因同构。
2. **先例对齐**：修法逐字承 b61c1227（40×50ms 有界轮询 run_owner 可见 · 上限 2s  fail-loud 不兜底 · 零断言弱化）。TC-B4 合入后 CI 未再同形红（d002e4f0 起绿史实证先例有效）。
3. **生产侧取舍论证**：备选=归属闸对刚建 run 短暂可见性容忍（run_owner 重试/读未提交）。裁定不动生产侧——① 归属闸是 replay 面跨租户 404 语义的安全闸，容忍窗会软化「不存在 vs 不可见」边界；② 竞态仅在测试用 bus.publish 作同步点时触达，生产 SSE 路径读己所写无此窗口；③ 先例已立且 CI 实证有效，测试侧修法 blast radius 最小。
4. **覆盖缺口完整性**：全 tests/ grep load_events_after 调用面——test_lg_rag_sse_resume.py（:267/:289/:305）· test_lg_rag_replay_resume_follow.py（:229/:245）· TC-B5-orphan（:465/:471/:480）均为直接 persist_run_event awaited 提交落库，无 bus 同步点即无竞态；TC-B1 :174 末次读取在 worker task 完成后（提交先于 task done）且 run_owner 已可见，安全。缺口恰为两件。
5. **断言安全**：等待循环只前置时序、不改任何断言语义；循环耗尽即自然抛 NotFound（fail-loud），不吞错。

## 风险登记

- R-1：极端 CI 调度下 2s 上限仍不足（低概率 · TC-B4 先例同上限绿史佐证）→ 暴露后如实登记另卡，不放大上限不弱化断言（红线）。
- R-2：未来新增同 family 用例复犯 → 本卡范围 1.2 grep 复核口径可复用为排査模板。
