# invoke · 10-spec 修订（v1）· hitl-approval-consumption · 2026-10-10

## 帽与授权
- 帽：10-spec（修订）· 代笔：00（delegate-only 窗）
- 授权链：维护者 2026-10-09「授权00签收所有过程文档」+「今晚完成你可以自主判断完成的部分」；本 SPEC 为过程文档（非实现码 · app/ tests/ 零触碰）

## 退回原因（v0 → v1）
v0 漏覆盖终局路线文档 §4 两裁定（docs/guides/DESIGN_agent_contribution_endgame_v0_zh.md :82-83）：
1. 批准后自动继续 = 可配置（全局默认 + 按审批单覆盖 · 触发器三选一 + 补偿扫描 + 行锁防重）
2. 无状态恢复纪律锁死（禁进程内存挂起态 · resume 从事件表重建）
handoff 令：docs/harness/invokes/by-task/_prompts/PROMPT_00_hitl-consumption-loop-handoff_20261009.md 第一棒。

## 过程留痕（子 Agent 卡滞实录）
1. 首派 10-spec 修订棒（314c8872）：实证读取完成、裁定已定（触发器=进程内后台任务），全文生成阶段卡滞约 8 轮零落盘 → interrupt。
2. 重派（85246adf）：收紧增量落盘纪律，落 90 行骨架后填充阶段再滞 → interrupt ×2。
3. 裁决：00 代笔填充 v1 全文（260 行）——裁定全部继承首棒定案（触发器=进程内后台任务+PG 行锁+补偿扫描 · 否决轮询工人/LISTEN-NOTIFY · 配置面=全局 env + 单据级 resume_mode），骨架结构继承重派棒。文档类产出 · 实现码纪律未涉。

## v1 修订点（相对 v0）
- 新增 D5「批准后自动继续（可配置面）」：OPS_HITL_AUTO_RESUME（manual 默认零 diff / auto）+ decide 载荷可选键 resume_mode ∈ {inherit, immediate, manual}（白名单 · 未知值 400）+ 触发器（进程内后台任务走 resume 同路径）+ PG 行锁认领防多副本重复 + 启动/定时补偿扫描兜底 + 单次 decide 最多触发一次
- 设计纪律增第 6 条：无状态恢复纪律 SPEC 级锁死
- Q6（触发器选型三案）/ Q7（配置面三案）；FP-8~FP-11；A9（auto 全链 done{completed} · handoff 验收令）/ A10（无状态恢复钉死组）
- 吸收 R1 nits：N3（TTL 合法域 [1,86400] 承 delegation.py:107）· N4（decided_at 双 store 类型归一 · A2 双 store 断言）；N1（锚点行号精度 router.py:404-411 已随文引用修正）· N2（async 波及面点名 nodes.py:711 + test_capability_testing_write.py:492）随 Q2 落注
- v0 A1–A8 / Q1–Q5 / FP-1~FP-7 存续性逐条确认（R4）

## 机械闸
- v1 status=draft · HG-SPEC-SIGNOFF=pending（待 20-spec-audit R2 → 维护者人签 00 代录）
- 未 push · 未开 PR · 工作树仅 v1 + 本 invoke

## 下一棒
20-spec-audit R2（重点：D5 三裁定机制性理由 · A9/A10 可机断 · decide 载荷增键边界 · FP-8~FP-11 充分性 · v0 存续性未被破坏）。
