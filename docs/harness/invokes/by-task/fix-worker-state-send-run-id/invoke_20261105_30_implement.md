# Invoke · 30 帽 · 实扫落码（fix-worker-state-send-run-id）

| 字段 | 值 |
|------|-----|
| hat_id | `30`（fix 实扫落码 · 案 A · 六交付条件） |
| task_slug | `fix-worker-state-send-run-id` |
| task_paths | `docs/tasks/active/task_fix_worker_state_send_run_id.md` |
| related_review_or_none | `docs/harness/reviews/task_fix_worker_state_send_run_id_audit_R1_20261105.md`（20-R1 · lead 人审转录） |
| git_branch | `fix/worker-state-send-run-id`（reset 自 origin/master `5bec9d6` = PR #331 squash 合入点 + 闸表签认 cherry-pick） |
| created_utc_or_local | 2026-11-05 |
| notes | 30 授权 = issue #329 comment `6658823187`（六交付条件 · GATE_VERIFY 闸据=task 档闸表）；GATE_VERIFY 首输出：VERIFY: PASS（四闸 approved · 20-R1 审查文 + 10/20 invoke 齐）；交付条件逐条见 §2 |

---

## §1 · 落码摘要

- **实现（改码面唯一）**：`app/ops/lg_rag/multi/nodes.py::_worker_state` 非空才写 `run_id`（镜像 supervisor_started_at 可选键先例 · FP-7 空串不写入 · 注释留痕缺陷机制与案 A 依据）；delegation 分支 :1666 重复赋值行保留（同值幂等）
- **新测 6 枚**（`tests/test_fix_worker_state_send_run_id.py`）：红测负样本（维护者红线 · 真派发路径 route_next_subtask → _worker_state 产载荷 → tool_exec_node · 预置 approved 单据 → 消费命中 + 真落笔三照：便签行/回执/消费台账 span · approval_id 串链）+ 键集钉双形态（有值含 run_id · 空值不写入）+ delegation on 对拍 + FP-9 防误读（无审批仍 fail-closed 拦死 · 零落笔）
- **旧测适配 1 枚**（适配不放宽）：`test_lg_rag_delegation_wiring.py::test_off_mode_dispatch_zero_diff`——off 模式零 diff 契约收窄为「不注入委派 artifact」，载荷身份键 run_id 随案 A 裁决全派发路径下发；委派 artifact 不注入断言保留
- **旧测 grep 影响面清单**（授权条件② · 如实列出）：`test_step_contract.py` worker_state 三测（断言对象 assigned_subtask 子树 · 零影响实跑）/ `tests/eval/test_capability_redlines.py` R14 段直调（零影响实跑 29 passed）/ `test_lg_rag_delegation_wiring.py`（适配 1 枚 · 见上）——除此三处外无 `_worker_state` / `route_next_subtask` 键集等值断言

## §2 · 验证（六交付条件逐条）

| # | 条件 | 结果 | 证据 |
|---|------|------|------|
| 1 | 红测先行可见红→绿（真派发路径 · 消费命中+真落笔三照） | ✅ | 修复前 `pytest tests/test_fix_worker_state_send_run_id.py` → **3 failed 3 passed**（KeyError: 'run_id' · 消费门再拦 = 40 偏差#1 单测形态）；修复后 → **6 passed** |
| 2 | 旧测适配清单随 PR（适配不放宽） | ✅ | §1 清单三处如实列出 · 适配 1 枚带案 A 裁决依据注释 |
| 3 | 改码面唯一 | ✅ | delta 恰 3 文件：nodes.py `_worker_state` +8 / 新测 +347 / wiring 适配 ±9；闸链/HITL 表/状态机/auto-resume 零 diff |
| 4 | 四红线零 diff 对拍 | ✅ | `git diff`：registry.py / policy.py / event_store / hitl/** 零 diff；SSE 事件表零 diff（不触事件面）；web `hitl.ts` freeze 未碰（跨仓）；消费门 `_write_execution_approval` 逐字节不变；resume 单路径 grep 断言（A5 形态）由 stage_w 16 枚承接全绿 |
| 5 | ruff + pytest 全量 + graph-compile 绿 | ✅ | `ruff check app tests` 零新增；`pytest tests`（本地真 PG）2063 passed · 4 failed = master 既有本地产能红（diff-whitelist 锚点漂移 ×2 / env 依赖 ×2 · CI skip 面 · 承 stage-w 40 登记）· **零新增红**；`graph-compile.sh` EXIT=0 |
| 6 | PR 说明逐条对照验收标准 | ✅ | 30 PR 描述含验收标准逐项对照表 |

## §3 · 工程面命令留痕

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `npx spec-wave verify --target . --task docs/tasks/active/task_fix_worker_state_send_run_id.md`（开工前） | 0 | VERIFY: PASS · 四闸 approved |
| `pytest tests/test_fix_worker_state_send_run_id.py`（修复前 / 后） | 1 → 0 | 3 failed → 6 passed（红→绿） |
| `pytest <关联回归 10 文件>` | 0 | 154 passed |
| `pytest tests/eval/test_capability_redlines.py` | 0 | 29 passed |
| `pytest tests`（全量） | 0* | 2063 passed · 4 failed（既有基线 · 零新增） |
| `ruff check app tests` | 0 | 零新增 |
| `./scripts/graph-compile.sh` | 0 | EXIT=0 |
| `npx spec-wave task lint --file docs/tasks/active/task_fix_worker_state_send_run_id.md` | 0 | LINT: PASS（30 回填后复跑） |

## §4 · 下一棒

`40` 复跑照旧（独立复跑不采信自报 + 红线对拍 + 回归亲跑 + 条件触发 live 免 shim 八段复跑销 40 偏差登记①）→ lead 终审 → CLOSE

---

### 修订

| 日期 | 说明 |
|------|------|
| 2026-11-05 | 30 实扫棒 invoke 落档 |
