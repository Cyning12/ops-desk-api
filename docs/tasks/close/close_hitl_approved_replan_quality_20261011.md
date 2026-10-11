# CLOSE：hitl-approved-replan-quality（2026-10-11）

> **task**：[`../done/task_hitl_approved_replan_quality.md`](../done/task_hitl_approved_replan_quality.md)（已归档 done/ · 状态行回填 CLOSED）
> **类型**：质量收口（消费回路血统延续 · 功能缺口 · SPEC §9 序1 · 维护者令 2026-10-11 立项）
> **关账日期**：2026-10-11 · 帽位：CLOSE（50）

---

## 一 · 任务信息

| 字段 | 值 |
|------|----|
| task_slug | `hitl-approved-replan-quality` |
| 目标 | approved 恒 replan + LLM 盲循环收口：批准步骤「自然完成」双重结构性不可达 → replan 保号注入去盲 + write 孪生结构护栏（write 零重发红线） |
| 依据 | SPEC `docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` §9 序1（2026-10-11 维护者令登记 · 维护者令立项）· T4 CLOSE 钉案② `docs/tasks/close/close_hitl_replan_carry_and_persist_guard_20261010.md` §四.2 · 语义边界登记 `docs/acceptance/20261010_hitl-consumption-loop_local_acceptance.md` |
| 分支 / base | `task/hitl-approved-replan-quality`（worktree `t-hitl-approved-replan-quality` · base master `cae745e` · 中途 merge origin/master 入序2/序3 解锁 live） |
| PR / merge | PR [#233](https://github.com/Cyning12/ops-desk-api/pull/233) · **MERGED 2026-10-11 · squash commit `be1469d`** |
| 帽链 | 10 落稿（00f0ecc 骨架 → f71200b 填肉 v1 · 00 代笔 · 骨架棒卡滞 interrupt 留痕）→ 20-task-audit R1 **BLOCKED**（b4c1382 · B-1 lint E3/E5 结构闸）→ B-1 修订（54a3897 · lint EXIT=0 零 warn 亲跑）→ R2 **PASS**（e9b2c9a · 零实质改动）→ 三闸 approved（5afb111 · 维护者授权 m01606/m00255 · 00 代录）→ 30 红测先行（9b56343 RED → ebe2a01 feat 转绿 · 3a8533f invoke · 403a0e9 自检回填 v1.1）→ f299526 merge master 解锁 live → 40 核验（4f389cf · **PASS-WITH-NITS**）→ PR #233 → CLOSE |

## 二 · 交付清单

### 交付摘要（D1=C 混合案）

| 面 | 内容 | 锚点 |
|----|------|------|
| **B 读步：replan 注入去盲** | suffix 模板 v1→v2 增 `$preserved_block` 段：replan 时注入保号行名单（原 sid 明示）+ locked 前缀带终态 output 摘要（截断 200 防爆）——破「LLM 只见 locked 只读行、保号 sid 与终态结果双盲」的恒 replan 盲循环 | `app/ops/prompts/assets/lg_rag.supervisor.suffix.system.md` v2 · `app/ops/lg_rag/multi/nodes.py`（supervisor prompt 装配处 · 注入段） |
| **C 写步：write 孪生 guard-skip 结构护栏（契约 1 核心）** | `_join_subtasks` 分发层**先于签发**检查：canonical 键 `_guard_write_key`（tool 名 + sort_keys 规范化入参 · 仅 `WRITE_SIDE_EFFECTS` 注册能力）命中**异 sid 已成功终态** write → **guard-skip：不派发不消费**，output 照抄原终态 + `write_replay_guard_skip`/`replay_of` 台账；同批双胞胎首发照派、次发挂起待下一 join pass；off 模式整段零触达（承 off 零 diff 先例） | `app/ops/lg_rag/multi/nodes.py`（`_join_subtasks` 分发层 · `_guard_write_key` · guard 段） |
| **台账** | 新键两枚：`write_replay_guard_skip`（guard 命中留痕 · 载荷 subtask_id/replay_of/capability_id）· `replay_of`（孪生 → 原终态 sid 指针）；既有键（`delegation_approval_consumed`/`hitl_persist_guard_skip`/token_*）零 diff | nodes.py guard 段 + 40 invoke TC5 台账链 |
| **测试** | 新测 `tests/test_hitl_approved_replan_quality.py`（341 行 · 8 枚）：TC1-a write 孪生 guard-skip · TC1-b replan prompt 注入保号行+终态摘要 · TC2 边界组六枚（FP-3 反面/异 args 区分/error 终态不拦/同批双胞胎/off 零介入/canonical 确定性+空保号零 diff）；`tests/test_prompt_assets.py` +11（suffix v2 模板锚定） | tests/ |
| diff 总面 | 13 文件 956+/11-；生产面仅 `app/ops/lg_rag/multi/nodes.py`（+163 三处插入）+ suffix 模板（+5/-2）+ assets README（+2/-1）· **`app/ops/hitl/` 零 diff · 消费门/保号三路径/router/resume 零触碰** | PR #233 squash `be1469d` |

### 钉死契约五自查（30/40 双侧实证 · 详见 40 invoke §契约自查）

1. **契约 1（已终态 write 零重发 · 禁纯提示词约束）** ✅：分发层 guard-skip 先于签发、不派发不消费——结构护栏非 prompt 乞求；机断面=delegation 执行计数台账（live 双 run write 执行均=1 · token_issued 各 approved 步恰好 1 枚）。
2. **契约 2（保号机制零回归）** ✅：`hitl_unlocked_ids`/保号集合/`delegation_approval_consumed`/`hitl_persist_guard_skip` 台账键零 diff · 保号 TB 组（T4 14 枚）+ 消费门 34 枚 = 48 全绿。
3. **契约 3（手动/auto resume 双路径同口径）** ✅：`resume.py:131` 出口一致零触碰 · FP-3 反面实证（approved 步自身 consumed 命中原 sid 正常重跑）双 run 同框取证。
4. **契约 4（reject 路径零 diff）** ✅：reject 分支零触碰（diff 面无）· 既有 reject 测试全绿。
5. **契约 5（pytest 全量零新增红）** ✅：7 failed/1769 passed/1 skipped 与 9b56343 分支基线及 master `cae745e` 基线逐枚同名同因（环境性：capability_lookups×3 + alist_really_executes + unknown_tool + dualproc×2）· ruff 55=55 持平（涉改 6=6）。

### 反回归基线

- TB 组：保号+消费门 48 + 本 task 新测 8 + prompt_assets 37 = **93 绿**。
- 全量对拍：7 红集合与 master 基线**逐枚同名同因零新增**（40 invoke §TC4 七枚逐名表）。
- capability acceptance 门禁：失败 2 跳过 1 与 master `cae745e` 同形（既有环境性）。

## 三 · 核验结论（40 PASS-WITH-NITS · 独立复核不轻信自述）

40 复核（HEAD `403a0e9` 起 · 全程亲跑留证 · 详见 [40 invoke](../../harness/invokes/by-task/hitl-approved-replan-quality/invoke_20261011_40_verify.md)）：TC1 红测时序实证（9b56343 RED 两枚签名与 live D1 同形 → ebe2a01 转绿）· TC2 六枚全绿 · **TC3 live 双 run 对照** · TC4 全量对拍零新增红 · TC5 台账链 grep 可断 → 裁定 **PASS-WITH-NITS**（N1 照登见 §四）。

### TC3 live 双 run 对照（本 task 核心实证 · 维护者复跑口径见 §九 checklist）

| run | thread_id | 剧本 | 结果 |
|-----|-----------|------|------|
| run1 | `6d46735942af47f6bf4e9c075ff2ca4d` | 单写步 · approve 后 locked=空（注入**未激活**） | LLM 仍产孪生 `:2` → **护栏命中**：`write_replay_guard_skip {"subtask_id":":2","replay_of":":1","capability_id":"testing.write.echo"}` · write 执行=1 · 零孤儿 pending · FP-3 对照：approved `:1` 正常 consumed 命中原 sid + token_issued 重跑 |
| run2 | `3f2c58bfef0542a78ae89fc6a332cf77` | rag+write 双步 · approve 后 locked=`[:1]` 非空（suffix v2 注入**激活** · prefix_len=1） | LLM **零孪生** verdict=settle · `:2` 重跑 exactly once（token_issued `dt-2-d74362139f2e` 仅此 1 枚）· `:1` rag 零重跑 · write 执行=1 |

**对照语义**：同一改动 off/on 活体对照——locked 空（注入 off）时 LLM 照样产孪生、由护栏结构兜底；locked 非空（注入 on）时 LLM 直接不产孪生。两层各实证其位，互不寄生。

### CLOSE 质量钉复跑（本帽 · 归档后仓态）

- `npx --yes spec-wave@3.2.0 verify --target . > /tmp/close_verify_hitl_replan.txt 2>&1; echo EXIT=$?` → **EXIT=0 · VERIFY: PASS**（重定向取真码 · 挪档 done/ 后本 task 审查文已由址A 复制件供门禁消费 · 零新增缺口）。
- `npx --yes spec-wave task lint --file docs/tasks/done/task_hitl_approved_replan_quality.md` → **EXIT=0 · LINT: PASS**（done/ 路径复跑）。

## 四 · 偏差与 nit（如实照登）

1. **N1 · locked 空路径 preserved_block 不注入（nit · 建议另立 task）**：locked=空时 supervisor 走 `_build_supervisor_system` 基础 prompt（`nodes.py:1172-1173` else 分支），保号行注入仅覆盖 suffix v2 路径——契约红线不破（护栏兜底 · run1 实证），但「读步去盲」存在路径覆盖缺口；40 裁定不阻塞本 task 收口，**建议另立 task 裁定**（基础 prompt 路径是否同注保号行）。
2. **N2 · prompt 内容级直证不可观测（观测口径照登）**：app INFO 台账不 dump prompt · langfuse 仅 SPAN 无 GENERATION input——注入内容级直证不可得；以 TC1-b 单测钉死（prompt 组装断言）+ TC3 live 行为对照（run1/run2 off/on）间接实证闭环。
3. **N3 · worktree compose 端口被主仓占用（环境处置照登）**：worktree compose 5432/6333 与主仓容器冲突 → live 复用主仓 healthy 容器（零新增容器 · 零残留）——非本 diff 引入，口径先行登记防误判。
4. **环境坑位复发照登**：`NO_PROXY` 含 `[::1]` 致 httpx `InvalidURL`（验收文档坑位 1 复发 · 剥 no_proxy 后通）——非本 diff 引入；live 环境准备须先核代理变量。
5. **机械闸基线照登**：本 CLOSE 复跑仓级 verify **EXIT=0 PASS**（序3 基线收口后口径 · 93 存量豁免命中 · 本 task 址A 复制件供档零新增缺口）· task lint done/ 档 **EXIT=0 PASS**——与序2 CLOSE（lint/verify REAL_EXIT=2 轻量格式固有）口径不同：序3 后两闸已转绿，本档如实录新基线。
6. **R1 nit 闭合照登**：R1 NIT-1（FP-1 退路措辞）/NIT-2（契约 5 环境性红名单 30 首步锁定）/NIT-3（序2 merge 为 40 闸）均随 B-1 修订（54a3897）与 30/40 流程闭合（R2 PASS 在案）。

## 五 · 签录（闸与审查文链）

| 环节 | 文档 / 实证 |
|------|------------|
| 人工闸 | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-IMPL 三闸 **approved**（2026-10-11 · 维护者授权 m01606/m00255 · 00 代录 · task 人工闸表为真值）· HG-PILOT n/a |
| 20 R1 审查 | 址B 原件 `docs/audits/task-review/20261011_hitl-approved-replan-quality_r1.md`（**BLOCKED 退 10 修订** · B-1 lint E3/E5 结构闸 · 内容面六要点全成立：锚点 8 处亲读逐字核真含 nodes.py:1759 恒 replan 决策点漂移校正 · D1 倾向 C 成立 · 契约 5 条可机断）· 址A 过渡复制件 `docs/harness/reviews/task_hitl_approved_replan_quality_audit_R1_20261011.md`（本 CLOSE 落） |
| 20 R2 审查 | 址B 原件 `docs/audits/task-review/20261011_hitl-approved-replan-quality_r2.md`（**PASS** · B-1 回填四项全落零实质改动 · lint 亲跑 EXIT=0）· 址A 过渡复制件 `docs/harness/reviews/task_hitl_approved_replan_quality_audit_R2_20261011.md`（本 CLOSE 落 · verify 按最高 R 轮消费此件） |
| invokes | `docs/harness/invokes/by-task/hitl-approved-replan-quality/`：10_task_draft / 20_task_audit_r1 / 20_task_audit_r2 / 30_implementation / 40_verify / 50_close（本 CLOSE 落盘） |
| 合并 | PR [#233](https://github.com/Cyning12/ops-desk-api/pull/233) MERGED 2026-10-11 · squash `be1469d6bfa93626626504b41b210775d4faaae9` |

## 六 · 资源清理

- **本 CLOSE 不删任何东西**：worktree `t-hitl-approved-replan-quality` 与本地/远端分支 `task/hitl-approved-replan-quality`、`close/hitl-approved-replan-quality` **移交 00/维护者统一清理**——本 CLOSE 在该 worktree 内作业无法自清，且 CLOSE PR 未合并前 close 分支在役；**CLOSE PR 合并后**：`git worktree remove` + 删除两条分支（task 分支已 squash 合入 master `be1469d` · 删除安全 · 远端一并清）。
- live 现场零残留：复用主仓 healthy 容器未新起（N3）· 测试 thread 两枚留库（`6d46735942af47f6bf4e9c075ff2ca4d` / `3f2c58bfef0542a78ae89fc6a332cf77` · 台账取证用，留维护者处置）。
- 先例对照：序2/序3 各 CLOSE 亦将 worktree/分支清理留 00（active README 登记表在案）· 本件同口径。

## 七 · 后续建议

1. **N1 路径覆盖（另立 task · 最高优先）**：locked 空走基础 prompt 时 preserved_block 不注入（nodes.py:1172-1173 else 分支）——裁定基础 prompt 路径是否同注保号行/终态摘要，消「读步去盲」路径缺口。
2. **prompt 注入观测增强（可选）**：langfuse GENERATION 级 input 留痕或台账注入标记（如 `suffix_injected {prefix_len}` 结构化行），使 prompt 类改动内容级直证可得（N2 口径升级）。
3. **护栏覆盖面自增说明**：guard 基于 `WRITE_SIDE_EFFECTS` 注册集合 canonical 判定——后续新注册 write 能力**自动入护栏覆盖**，无需逐能力维护；新增副作用能力时配套 canonical 入参稳定性测试即可。
4. **验收环境坑位固化**：`NO_PROXY` `[::1]` 坑位两度复发（验收文档坑位 1 · 本 task live）——建议 RUNBOOK/验收文档固化「live 前置：剥 no_proxy · 核容器归属」检查行。

## 八 · 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-11 | CLOSE 落稿（CLOSE 棒 · worktree `t-hitl-approved-replan-quality` · 分支 `close/hitl-approved-replan-quality` · base origin/master `be1469d`）：九节沿仓内先例（序2/序3 CLOSE 文档）· 质量钉复跑（verify EXIT=0 PASS · task lint PASS）后回填 · 审查文 R1/R2 复制落址A 过渡（双址规约 §二）· README 双侧补登 + 50 invoke 落盘 |

## 九 · 附录

### PR / merge 事实

- PR [#233](https://github.com/Cyning12/ops-desk-api/pull/233) · base `master` ← head `task/hitl-approved-replan-quality` · **MERGED 2026-10-11T02:10:47Z（10:10 +08:00）** · squash `be1469d6bfa93626626504b41b210775d4faaae9` · 13 文件 956+/11-。

### commit 链（task 分支 · 按时序）

`00f0ecc`（10 骨架）→ `f71200b`（10 填肉 v1 · 00 代笔）→ `b4c1382`（20 R1 BLOCKED+invoke）→ `54a3897`（B-1 修订）→ `e9b2c9a`（20 R2 PASS+invoke）→ `5afb111`（三闸代录 approved）→ `9b56343`（TC1 红测 RED）→ `ebe2a01`（feat D1=C 落地）→ `3a8533f`（30 invoke）→ `403a0e9`（30 自检回填 v1.1）→ `f299526`（merge origin/master 解锁 live）→ `4f389cf`（40 收口 v1.2）。

### 关键路径指针

| 类别 | 路径 |
|------|------|
| 生产码 | `app/ops/lg_rag/multi/nodes.py`（`_join_subtasks` guard 段 · `_guard_write_key` · suffix 注入段 · :1172-1173 N1 缺口） |
| 模板 | `app/ops/prompts/assets/lg_rag.supervisor.suffix.system.md`（v2 · `$preserved_block`）· `app/ops/prompts/assets/README.md` |
| 测试 | `tests/test_hitl_approved_replan_quality.py`（8 枚）· `tests/test_prompt_assets.py` |
| 审查文（址B 原件） | `docs/audits/task-review/20261011_hitl-approved-replan-quality_r1.md` · `..._r2.md` |
| 审查文（址A 过渡复制件） | `docs/harness/reviews/task_hitl_approved_replan_quality_audit_R1_20261011.md` · `..._R2_20261011.md` |
| invokes | `docs/harness/invokes/by-task/hitl-approved-replan-quality/`（10/20r1/20r2/30/40/50） |
| 双址规约 | `docs/harness/CONVENTION_review_gate_dual_address_v1_zh.md`（序3 立 · §二 过渡期口径） |

### 维护者验收 checklist（令③ m01606 口径）

1. **复跑口径 = 40 invoke 双 run 场景**：按 [40 invoke](../../harness/invokes/by-task/hitl-approved-replan-quality/invoke_20261011_40_verify.md) §TC3 剧本复走两 thread——run1 单写步 approve 后 locked=空（注入 off · 期望护栏命中中性化孪生）；run2 rag+write approve 后 locked 非空（suffix v2 on · 期望 LLM 零孪生）。两 run write 执行计数均须=1 · 零孤儿 pending · FP-3 对照（approved 步自身正常 consumed+重跑）。
2. **台账键 `write_replay_guard_skip`/`replay_of` grep 法**：服务台账 `grep write_replay_guard_skip`——run1 期望恰好 1 行、载荷 `{"subtask_id":":2","replay_of":":1","capability_id":"testing.write.echo"}`；run2 期望 grep 空（零孪生不触发护栏）。`replay_of` 仅随 guard-skip 出现 · `delegation_approval_consumed` 命中原 sid · `token_issued` 每 approved 步恰好 1 枚——新键仅此两枚，其余台账键零 diff（TC5 口径）。
3. **suffix v2 注入行为对照**：locked 非空 → suffix v2 激活（prefix_len=1 · 保号行+终态摘要注入）→ LLM verdict=settle 零孪生；locked 空 → 基础 prompt（N1 缺口在案）→ LLM 产孪生由护栏兜底。单测面：`tests/test_hitl_approved_replan_quality.py` TC1-b + `tests/test_prompt_assets.py` suffix v2 锚定共钉死模板/装配；prompt 内容级直证不可观测属已知口径（N2 · langfuse 无 GENERATION input）。

### CLOSE 复跑命令留痕

```bash
npx --yes spec-wave@3.2.0 verify --target . > /tmp/close_verify_hitl_replan.txt 2>&1; echo "EXIT=$?"   # EXIT=0 · VERIFY: PASS
npx --yes spec-wave task lint --file docs/tasks/done/task_hitl_approved_replan_quality.md       # EXIT=0 · LINT: PASS
```
