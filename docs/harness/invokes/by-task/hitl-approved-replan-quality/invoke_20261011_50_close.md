---
hat: 50
task_slug: hitl-approved-replan-quality
date: 2026-10-11
---

# invoke · 50+CLOSE · hitl-approved-replan-quality（SPEC §9 序1 · approved 恒 replan+盲循环收口）

## 收口结论

- 链路全通：10-task 落稿（00f0ecc 骨架 → f71200b 填肉 v1 · 00 代笔 · 骨架棒卡滞 interrupt 留痕）→ 20-task-audit R1 BLOCKED（b4c1382 · B-1 lint E3/E5 结构闸）→ B-1 修订 54a3897 → R2 PASS（e9b2c9a · 零实质改动）→ 三闸 approved（5afb111 · 维护者授权 m01606/m00255 · 00 代录）→ 30 红测先行（9b56343 RED → ebe2a01 feat D1=C 转绿 → 3a8533f invoke → 403a0e9 自检回填 v1.1）→ f299526 merge master 解锁 live → 40（4f389cf · **PASS-WITH-NITS** · TC3 live 双 run 对照 · TC4 全量对拍零新增红 · TC5 台账链可断 · N1 照登留另立 task）。
- PR [#233](https://github.com/Cyning12/ops-desk-api/pull/233)：MERGED 2026-10-11T02:10:47Z · squash `be1469d6bfa93626626504b41b210775d4faaae9`（base master · head task/hitl-approved-replan-quality）。
- 归档：task → done/（头部状态 done（CLOSED 2026-10-11）· 分支行补 merge 事实 · 经验总结五条回填 · 修订表 v1.3 CLOSED 行）；active README 登记表补行；done README Hub engineering 域表行+修订记录 CLOSE 行补登；CLOSE 文档 `docs/tasks/close/close_hitl_approved_replan_quality_20261011.md` 落盘（九节 + 维护者验收 checklist）。
- 双址过渡：审查文 R1/R2 复制落址A（`docs/harness/reviews/task_hitl_approved_replan_quality_audit_R{1,2}_20261011.md` · 档头注来源 · 址B 原件原址原内容不动）——规约 §二 过渡期口径第三例（序2 教训 → 序3 规约 · 本 task 循例）· verify 按最高 R 轮消费 R2（PASS 机读口径满足）。

## 交付摘要

| 项 | 内容 |
|---|---|
| **产出（D1=C 混合案）** | B 读步：suffix 模板 v1→v2 `$preserved_block` 注入（保号行名单+locked 终态摘要截断 200 防爆）· C 写步：`_join_subtasks` 分发层 write 孪生 guard-skip 结构护栏（canonical tool+sort_keys 规范化入参 · 仅 WRITE_SIDE_EFFECTS 注册能力 · 先于签发不派发不消费 · output 照抄 + `write_replay_guard_skip`/`replay_of` 台账 · off 整段零触达） |
| **diff 面** | PR #233：13 文件 956+/11-；生产面仅 nodes.py +163 三处 + suffix 模板 + assets README · **app/ops/hitl/ 零 diff · 消费门/保号三路径/router/resume 零触碰** |
| **验收** | TC1 红测先行（9b56343 RED 两枚签名与 live D1 同形 → ebe2a01 绿）· TC2 边界六枚 · TC3 live 双 run 对照（run1 6d467359… locked 空：护栏命中孪生 `:2`→replay_of=`:1` · run2 3f2c58bf… locked=[:1]：suffix v2 激活零孪生 · write 执行均=1 · FP-3 对照 approved 步正常 consumed 重跑）· TC4 全量 7 failed/1769 passed 与 master 基线逐枚同名同因零新增 · TC5 台账链 token_issue→guard→consumed→issued→verified→guard_skip 可断（新键仅两枚） |
| **红线** | 钉死契约五全过：write 零重发结构性（非纯提示词）· 保号机制零 diff · 双 resume 路径同口径 · reject 零 diff · 全量零新增红 |

## 钉案登记（详见 CLOSE 文档第四节）

1. N1：locked 空走基础 prompt（nodes.py:1172-1173 else 分支）preserved_block 不注入——契约红线不破（护栏兜底）· 去盲路径覆盖缺口 · **建议另立 task**。
2. N2：prompt 内容级直证不可观测（app INFO 不 dump prompt · langfuse 仅 SPAN 无 GENERATION input）——TC1-b 单测钉死+live 行为对照间接实证闭环。
3. N3：worktree compose 5432/6333 被主仓占用 → 复用主仓 healthy 容器零残留（非本 diff 引入）。
4. 环境坑位复发：NO_PROXY 含 [::1] 致 httpx InvalidURL（验收坑位 1 复发 · 剥 no_proxy 后通）· live 前置须核代理变量。
5. 机械闸基线：序3 后仓级 verify 已转绿——本 CLOSE 复跑 verify EXIT=0 PASS + task lint PASS（与序2 CLOSE 录 REAL_EXIT=2 的口径不同 · 如实录新基线）。

## 质量钉（CLOSE 机械闸复跑）

- 仓级 verify：`npx --yes spec-wave@3.2.0 verify --target . > /tmp/close_verify_hitl_replan.txt 2>&1; echo EXIT=$?` → **EXIT=0 · VERIFY: PASS**（挪档 done/ 后零新增缺口 · 址A 复制件供门禁消费）。
- task lint：`npx --yes spec-wave task lint --file docs/tasks/done/task_hitl_approved_replan_quality.md` → **EXIT=0 · LINT: PASS**（done/ 路径复跑）。
- graph-compile：本 CLOSE 无图谱变更 · n/a。

## 移交

- worktree `t-hitl-approved-replan-quality` 与本地/远端分支 `task/hitl-approved-replan-quality`、`close/hitl-approved-replan-quality` **待 CLOSE PR 合并后由 00/维护者清理**（本 CLOSE 在该 worktree 内作业无法自清 · CLOSE 文档第六节在案）。
- live 测试 thread 两枚留库（6d46735942af47f6bf4e9c075ff2ca4d / 3f2c58bfef0542a78ae89fc6a332cf77 · 台账取证用 · 留维护者处置）。
- 维护者验收 checklist 见 CLOSE 文档第九节（令③ m01606 口径：复跑=40 invoke 双 run 场景 · 台账键 write_replay_guard_skip/replay_of grep 法 · suffix v2 注入行为对照）。
