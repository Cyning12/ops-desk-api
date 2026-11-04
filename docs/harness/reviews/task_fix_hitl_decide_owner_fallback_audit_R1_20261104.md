# 审查文 · 20-R1 · fix-hitl-decide-owner-fallback（2026-11-04）

> **审查轨**：20-R1（task 审查 · 唯一轮）
> **审查执行者**：cyning12-bot（00/10/20 同棒 · **自签**）
> **签认依据**：issue [#315](https://github.com/Cyning12/ops-desk-api/issues/315) 维护者评论 [#6623212135](https://github.com/Cyning12/ops-desk-api/issues/315#issuecomment-6623212135)（B+C 设计决策签认 + 10 帽授权）+ 评论 [#6623253310](https://github.com/Cyning12/ops-desk-api/issues/315#issuecomment-6623253310)（**全程委托**：00 帽自签本单全部过程文档——闸表签收 + 20-R1 审查文，签认依据=该评论，全程留痕；出货后由 lead（维护者代理人）审查验收并决策 merge）
> **效力声明**：本文为委托自签的过程文档；merge 前由 lead 复审，验收结论反馈请求者（依 #6623253310）

---

## §1 · 审查对象

- **task 档**：`docs/tasks/active/task_fix_hitl_decide_owner_fallback.md`（10 起草壳 · 零 `app/` diff）
- **上游证据**：issue #315 正文（现象 · 实测锚 · 判读）· workspace `invoke_20261104_10_c6_retest.md` §5 · 维护者 B+C 签认评论 #6623212135
- **授权边界**：本棒只产 task 档 + 20-R1 审查文 + invoke + 闸表代录；**不含 30 改码**（#6623212135「30 改码待闸签收后另行授权」）

## §2 · 逐项核对

| # | 核对项 | 结论 | 证据 |
|---|--------|------|------|
| 1 | 证据链：缺陷锚点与码面一致 | PASS | `hitl/router.py:240-243` decide 404 分支 · `:152-178 _run_owner_of` 无帧→None · `event_store.py:93-110 run_owner` 无帧返 None · `lg_rag/router.py:387-449` invoke 零事件帧；实测单 `hitl_503224fd719a42c8b0fa` decide 404 滞留 pending |
| 2 | 签认落地：B+C 方向与红线全入档 | PASS | 契约表「①兜底机制源 / ②作用面 / ③文档声明口径」+ 红线行（SSE 事件表零 diff · 负样本「sync invoke→decide 不再 404」）· 不选 A 理由入背景与 R0 |
| 3 | 预存在行为归因 | PASS | task 背景明示「非 PR #313 引入」· 与 #313（resume 链租户快照）无因果 |
| 4 | 机制源裁决可红测 | PASS | thread 末位反查的两大前提已核码面：`_prepare_thread` 跨用户 thread 404 在建单前（`lg_rag/router.py:330-345`）· `persist_thread_turns` dispatch 后落 thread 行含 interrupt（`thread_store.py:63-89` · invoke `:426`） |
| 5 | 作用面不越授权 | PASS | 兜底落 `_run_owner_of` 单一 helper（pending :201 / decide :240 同源）· `_open_event_sink`（:382-416 直引 run_owner）明示不动 · 无 schema 迁移 |
| 6 | freeze 双红线 | PASS | `lg-rag-sse-v1`（事件表零 diff）+ `hitl-browser-decide-v1`（404/409 语义不破）均入 failure_paths 与验收 grep 项 · freeze 文件本体不动 |
| 7 | 闸设计 | PASS | HG-DECIDE-FALLBACK-DESIGN 承载三决策点恰当 · 四闸 approved（00 代录 · 本 PR 第二棒） |
| 8 | 机械面 | PASS | `npx spec-wave task lint` → LINT: PASS · `npx spec-wave verify --target . --task …` → VERIFY: PASS（2026-11-04 · 图谱锚点检查 vocabulary_empty 跳过照登）· 零 `app/` diff 符合 10 帽授权 |

## §3 · HG-DECIDE-FALLBACK-DESIGN 三决策点裁决（00 代录 · 依据 #6623253310）

1. **兜底机制源**：**thread 末位反查**——`run_owner(run_id)` 返 None 时按单据 `thread_id` 查 `OpsLgRagThread.user_id`；thread 行缺失/解析失败 → 维持 None（fail-closed）。弃项「建单打 user_id 戳」（schema 迁移 + nodes 穿线）超「decide 反查兜底」薄改授权，revive 另立 task。
2. **作用面**：`_run_owner_of` 单一 helper（`GET /pending` 与 `POST /decide` 同源受益）；**不动** `_open_event_sink`——sink=None 现状继续（resume 执行不落恢复段事件），sync 面无 replay 消费者，差异由文档声明承载。
3. **文档声明口径**：`docs/guides/RUNBOOK_hitl_ops_v1_zh.md` 增补「sync invoke 面 HITL 审批链行为差异」小节（invoke 不落事件帧 → thread 兜底 → decide 可达 → resume 无 replay 追帧面 · 结果经线程历史/再次 invoke 可见）；`_run_owner_of` docstring 同步；不新增 freeze。

## 结论 · 20-R1 审查 PASS（委托自签 · 零阻塞）

**20-R1：APPROVED（委托自签）** · 语义面逐项核对通过（§2 八项全 PASS）· 三决策点已裁决（§3）· 00 代录四闸 approved（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES / HG-DECIDE-FALLBACK-DESIGN）。

**待 lead 复审项（merge 前）**：§2 第 4 项机制源前提的码面抽查 · §3 决策点与维护者 B+C 签认语的一致性（「按单据自身 run_id 判定归属」落地解读为「单据行 thread_id → thread 属主」——run_id 本身无帧即无归属，解读留痕于此，lead 可驳回要求重裁）。

---

### 修订

| 日期 | 说明 |
|------|------|
| 2026-11-04 | 20-R1 审查文落档（委托自签 · 依据 issue #315 评论 #6623212135 + #6623253310 · 随 task 起草 PR 出货 · 待 lead 复审） |
