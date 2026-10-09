# 10 invoke · hitl-approval-consumption（SPEC 起草 · 签发审批消费回路）

> **帽**：10-spec · **SPEC**：docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v0.md（draft）
> **分支**：spec/hitl-approval-consumption（worktree spec-hitl-approval-consumption · base origin/master ca4148f · 含 D2 merge）
> **日期**：2026-10-09 · **结论**：**SPEC v0 初稿落盘**（R0–R5 全轮回填 · Q1–Q5 全答 · HG-SPEC-SIGNOFF=pending）
> **授权源**：维护者裁定（2026-10-09）：「另立task，此次完成后写入到spec文档中」

---

## 立项依据（三实证缺口 · 源证据行号 · 本帽于 ca4148f 逐一复核源码成立）

| # | 缺口 | 源证据 | 源码锚点（本帽复核） |
|---|------|--------|----------------------|
| 1 | 审批结果不被签发判定消费（批准→放行半环断） | 30 invoke :52-61（探针实证 re-blocked）· 40 invoke :44 | delegation.py:488-514（三条件 :502-513 纯读注册表）· nodes.py:277-295（不读审批记录）✅ |
| 2 | 单子任务计划 resume 409 | 30 invoke :53-54 · 40 invoke :42（run 0eb059a5 · detail 逐字一致） | nodes.py:1440-1445（unlock=depends_on∩plan_prefix_ids）· router.py:403-411 ✅ |
| 3 | 第四道门（候选 map 无 env 口） | 40 invoke :33（SSE 帧实证 · shim 补位登记） | strategy/config.py:14-23（静态 map）· builder.py:177-182（candidates∩visible）· nodes.py:147-157 ✅ |

反回归锚点同步复核：registry.py:112-140（deny 判序）· policy.py:96-105（写闸 write_not_confirmed）· store.py（adecide 只受理 pending :89-99,159-163 · 重复 409 守卫 router.py:265-274）· models.py:481（status 注释已预留 expired 语义位）。

## 思考轮执行记录（R0–R5 · 结论已回填 SPEC §7）

- **R0**：维护者裁定 + 30/40 invoke 全文 + 上表全部锚点复核 → 三缺口成立且互补（D1+D2 配对成环 · D3 独立门）。
- **R1**：范围锁 D1 消费门 / D2 unlock 回填 / D3 env 口 / D4 审计测试；非范围锁挂起与 decide 落库机制、UI、deny 判序与写闸；**边界澄清立字据**：`_persist_hitl` 的 unlock 计算修正与 payload jsonb 增记 capability_id 属范围内接线修补（零迁移 · 不动守卫与状态机）——留 20-spec-audit 复核此解释。
- **R2**：Q1 消费键三元组（弃：仅二元 / 会话级）· Q2 编排层消费保 auto_approve_ok 纯函数（弃：改 capability 包纯函数）· Q3 unlock=被拦 sid 自身+形态守卫（弃：放宽 router 409）· Q4 env 追加集默认空零 diff（弃：JSON 覆盖 / CANDIDATE_CAPABILITY_IDS 全局钩子）· Q5 TTL 读时判过期默认 3600s（弃：永久有效 / 一次性写回）。
- **R3**：FP-1~FP-7 全正面裁定；最锋利边界=消费安全语义四重（读时活状态 · fail-closed · TTL · 单据类型守卫）与 unlock 语义扩展的形态守卫。
- **R4**：验收 A1–A8 全可机断；A2 变异式否定断言组；A5/A7 以「git diff 为空 + 既有测试原样绿」双钉反回归；A3 机制段 pytest + live 段留 40（承 testing-write-capability 分工先例）。
- **R5**：开放裁定无遗留；图谱义务定（capability/lg_rag/hitl/strategy 四行备注 · 无新一级模块 · 零 alembic）；**本帽不代签 HG-SPEC-SIGNOFF**——下一棒 20-spec-audit。

early_stop=no · 无增轮。

## 留转 20-spec-audit 审查要点

1. **消费键粒度**：Q1 三元组 (run_id, subtask_id, capability_id) + payload 增键——增键是否越「HITL 挂起与 decide 落库本身不动」非范围边界（本帽裁定属接线修补 · SPEC §3 已立字据）。
2. **TTL 默认值 3600s**（Q5）是否过宽/过窄；读时判过期不写 expired 状态是否够审计。
3. **Q2 async 化冲击面**：`_delegation_issue_block_reason` 调用链（nodes.py 签发路径）sync→async 的波及范围须 task 阶段点名。
4. **Q3 形态守卫完备性**：除 delegation_issue_hitl_required 外是否还有其他 blocked_by 会产生空 unlock（prefix_touch_required 按定义有前缀步骤 · 须复核实证）。
5. **Q4 fail-closed 语义**：env 追加集对未知 key 也生效（运维显式）是否削弱「未知 key → []」口径——本帽裁定 fail-closed 管默认不管显式，留审。
6. **安全语义可查性**：「仅 approved 且未过期未撤销」落实为「读时 status==approved + TTL」——撤销端点属非范围，翻转即失效的天然兼容性须审计确认。

## 下一棒 Prompt（可复制）

> 你是 Harness 20-spec-audit 审查帽。书面审查 docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v0.md（draft · base master ca4148f · worktree spec-hitl-approval-consumption）：核对范围/非范围/验收/failure_paths 与 R0–R5 思考轮控制，重点核「留转审查要点」六条与三缺口源码锚点（行号以 master ca4148f 复核）。结论落盘 docs/harness/reviews/ 审查文。**不改 SPEC 实质内容**（问题退回 10-spec）；**不代签 HG-SPEC-SIGNOFF**（仅维护者人签）。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-09 | 10-spec 起草落盘：SPEC v0 初稿（三缺口实证锚定 · D1–D4 · Q1–Q5 · FP-1~FP-7 · A1–A8 · R0–R5）· 不 push 不开 PR · 留转 20-spec-audit |
