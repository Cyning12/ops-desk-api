# CLOSE：hitl-replan-carry-and-persist-guard（2026-10-10）

> **task**：[`../done/task_hitl_replan_carry_and_persist_guard.md`](../done/task_hitl_replan_carry_and_persist_guard.md)（已归档 done/）
> **类型**：SPEC 承接后续裁定（SPEC v1 FP-3 偏差实证后维护者双裁定落地：① replan 保号 ② `_persist_hitl` 建单前检查）
> **关账日期**：2026-10-10 · 帽位：CLOSE

---

## 一 · task 目标

修复消费回路两条 live 实证偏差，使批准→放行→消费→终态末段可达：

1. **replan 保号**：supervisor replan 三路径（正常 LLM / fallback carry / 空 allowlist 短路）对 `hitl_unlocked_ids` ∩ 未解决步骤保留原 `subtask_id`（原行带回 · 置于 locked 前缀之后 LLM 新后缀之前 · LLM 新步骤照常盖章新 id）→ 消费键 `(run_id, subtask_id, capability_id)` 可命中。
2. **建单前检查**：`_persist_hitl` `acreate` 前查同三元组新鲜 approved 单据 → 命中则跳过建单（防 resume 重放孤儿 pending）；匹配语义镜像消费门（同一 TTL/归一/blocked_by 守卫 · 禁第二份实现）；读异常 **fail-open 照建 + `hitl_persist_guard_read_failed` warning 台账**（维护者裁定采纳）。

## 二 · 合并链

| 环节 | 实证 |
|------|------|
| 交付链 | `228d7d2` feat(lg-rag) 保号+建单检查 → `687689d` TB1–TB6 断言化 14 枚 → `b857af6` 30 invoke+图谱在册回写 → `67148a9` 40 核验回填 |
| PR | [#221](https://github.com/Cyning12/ops-desk-api/pull/221) · **MERGED · merge commit `85058f7`**（2026-10-10 · CI 绿） |
| 改动面 | `app/ops/lg_rag/multi/nodes.py` +102/-7（`_unlocked_preserved_rows` 保号段 + `_stamp_host_plan` preserved 形参 + supervisor 三路径接线 + `_approved_fresh_for_subtask` 建单检查 + `_persist_hitl` 接线）· `tests/test_hitl_approval_consumption.py` +512（TB1–TB6 共 14 枚）· 图谱 l1/01_modules.md+graph.json 各 ±4 · 面外零 |
| 反回归 | T1 34 枚 + T2 39 枚 + observe/resume 面 B1 合计 107 枚全绿 · 空 unlocked 逐字节零 diff（TB4 五键序列化对拍）· 消费门/auto_resume/store/resume.py diff 空 |

## 三 · 40 核验结论与 live 实证

**40 核验七项全过（独立复跑 · 不采信 30 自报）**，详见 [40 invoke](../../harness/invokes/by-task/hitl-replan-carry-and-persist-guard/invoke_20261010_40_verify.md)：

- **靶点一 · 保号消费命中原 sid**（T1 :1→:11 重盖章偏差正面收口）：run `568d288a` 四轮 approve :1/:2/:3 各自 `delegation_approval_consumed` 台账在案（消费键三元组命中原 sid）；run `a0850a8e` consumed{:1} + token_issued/verified + echo 真执行。
- **靶点二 · 重放不重建孤儿单**（T2 hitl_5cefb116 偏差正面收口）：每次 resume 重放期 `hitl_persist_guard_skip` 在案（不再建单）· 终态 run（92539a4a · a0850a8e）pending 归组计数=0。
- **终态语义**：run a0850a8e 两轮 approve → seq23 **done{status:resumed} 终态** · Round3 探测 NO_PENDING——done{resumed} 语义=终态达成（event_store.py:99-107 判定 · 见钉案①）。
- 全量 pytest 4 failed/1762 passed（4 红=仓级基线环境性同签名 · 零新增红）· ruff 触及面零新增 · graph-compile EXIT=0 · 14 枚 TB 抽跑全绿（TB3/TB6 断言强度亲读非假绿 · TB6⑦ Db store 真跑）。

## 四 · 三条钉案登记（如实 · 后续 task 建议）

1. **resume.py:131 resumed 语义（面外既有设计 · 语义终态已达成）**：TB8 字面 `done{completed}` 在含 HITL 手动 resume 流**结构性不可达**——`app/ops/hitl/resume.py:131` 硬编码 `status=waiting_approval if re_interrupted else "resumed"`（本 task diff 空）；终态语义判定在 `event_store.py:99-107`（done 且 status≠waiting_approval 即终态 · 缺省 coalesce completed）· `history.py:161-168` 同义。字面 completed 仅纯 stream 无挂起流（sse_stream.py:482-490 终帧不带 status 键）可读得。**结论：语义终态达成 · 不阻塞收口**。
2. **approved 路径自然完成双重结构性不可达（建议另立后续 task）**：① LLM 不知晓保号行（钉死契约明写保号只管 id 带回）→ 每轮 replan 必新铸 echo 步 → 新 pending；且 observe 解锁剪旧结果（nodes.py :1766-1791 keep=plan_ids-approved）使 LLM 永远看不到已执行 echo 结果 → **盲循环**；② `app/ops/hitl/router.py:328-357` `_collect_decisions` 聚合同 run 全部已决申请：approved 非空 → verdict 恒 =replan 而非 settle（驳回轮实测：rej :4 但 approved=[:1,:2,:3] 非空 → 仍 replan）。**均为面外既有语义 · 建议后续 task 裁定**（如：replan 提示词注入保号行执行摘要 / `_collect_decisions` 聚合口径裁定）。
3. **仓级 verify 92 缺口基线（仓级 · 非本 task 归因 · 照登不新增）**：`npx spec-wave verify` REAL_EXIT=2「VERIFY: BLOCKED · 仓级 reviews 缺口 92」——缺口全在 `docs/tasks/done/` 遗留档（missing R<n> review / 结论节语义判）· spec-wave 3.0.1 与 npx 解析的 3.0.2 对拍同结果 · **主仓 master 对拍同 BLOCKED 同 92** → 仓级基线。另钉：30 自报「verify EXIT=0」不准（疑管道吞退出码）· 40 以 REAL_EXIT 为准。

## 五 · 闸与审查文链

| 环节 | 文档 |
|------|------|
| 20 R1 审查 | [`docs/harness/reviews/task_hitl_replan_carry_and_persist_guard_audit_R1_20261010.md`](../../harness/reviews/task_hitl_replan_carry_and_persist_guard_audit_R1_20261010.md)（PASS 零阻塞 · N-1~N-3 非阻塞注记 · 锚点 6 组抽核逐行吻合 · 留转六条全裁定成立 · T1=34/T2=39 枚亲跑 collect 实证） |
| 人工闸 | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸维护者签（00 代录 2026-10-10 · `invoke_20261010_00_gate_signoff.md` 留痕） |
| invokes | [`docs/harness/invokes/by-task/hitl-replan-carry-and-persist-guard/`](../../harness/invokes/by-task/hitl-replan-carry-and-persist-guard/)（00 签闸 / 10 落稿 / 20 审查 / 30 实现 / 40 核验） |
| 上游偏差源 | T1 40 invoke :31-40（sid 递增实证）· T2 40 invoke :48/:55-57（消费失配 + 孤儿 pending）· SPEC v1 :77/:193（Q1 消费键三元组 · FP-3 原裁定本 task 修正其覆盖假设） |

## 六 · 验收文档 / 图谱回写类

**N/A**——本 task 图谱 G-L1 行备注（lg_rag/hitl 两行）已随 30 回写并入 PR #221（HG-GRAPH-MODULES 在册 · 40 项 6 实证 diff 在册）；无独立验收文档面；wiki_delta=n/a（task 元信息钉）。

## 七 · 学习要点

1. **字面终态 vs 语义终态须起草期区分**：验收写 done{completed} 字面前，先实读终态判定段（resume.py:131/event_store.py:99-107）——语义终态口径可省 40 钉案一轮。
2. **live 核验环境陷阱**：worktree .venv 空壳 + 主仓 venv editable 安装 → import 解析错代码（须 sys.path 钉 worktree + CODE_UNDER_TEST 日志自证）；代理 NO_PROXY 含 IPv6 项炸 httpx（剥代理连 NODE_USE_ENV_PROXY 一起 pop）。
3. **verify 自报须核退出码**：管道吞退出码实证一例；仓级 BLOCKED 与 task 归因用主仓对拍分离。
4. **空集零 diff 总闸**（钉死契约三 + TB4 五键序列化对拍）是「可选路径新增」类改动零回归的最强保险，值得作为标准验收件。

## 八 · 改进建议

1. **后续 task 候选**（钉案②）：approved 路径自然完成的结构性收口——replan 提示词注入保号行执行摘要（破 LLM 盲循环）与 `_collect_decisions` 聚合口径裁定（纯驳回 + 历史 approved 混合时的 settle 判定），建议合并评估后另立 10-task。
2. **仓级 verify 92 缺口清零**（钉案③）：done/ 遗留档 reviews 缺口属仓级卫生项，建议另立 chore task 批量补登或在 verify 配置中将遗留档标 baseline——当前每 task CLOSE 均须重复「仓级基线照登」钉案，信噪比递减。
3. **Harness 流程**：30 GATE_VERIFY 自报退出码须附 REAL_EXIT 取证（防管道吞码）；worktree live 核验启动器模板（sys.path 钉 + CODE_UNDER_TEST 自证 + 代理剥离清单）建议沉淀为 40 复用片段。
