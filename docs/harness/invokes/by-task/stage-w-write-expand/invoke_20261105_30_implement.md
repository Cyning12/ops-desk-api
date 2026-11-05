# invoke · task_stage_w_write_expand 30 实现（2026-11-05 · 30 帽 · Q1=S1 仓内落笔型写 · 红测先行红→绿可见）

| 项 | 内容 |
|----|------|
| **时间** | 2026-11-05 |
| **性质** | hat 30 实扫落码（第二条真实窄写能力 `ops.write.run_note` 端到端接入既有受控写闸链） |
| **分支** | `agent/stage-w-impl-d5d8a1204a9c`（base master `6955b4c` = PR #326 合入点） |
| **依据** | issue #323 维护者 comment `6652738841`（四闸齐 · 30 开工令 · Q1=S1 执行口径）+ SPEC v0.1（HG-SPEC-SIGNOFF approved）+ task 档四闸 approved |

## 人工闸扫描（GATE_VERIFY · 30 改码前首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | 维护者 comment `6652738841`「四闸齐」 | Y | Y | ✅ |
| HG-AUDIT-R1 | approved（lead 代录 · 依据 `6652283580` + PR #326 审查文） | 同上 | Y | Y | ✅ |
| HG-GRAPH-MODULES | approved（口径签 · 随 30 回写回签确认） | 同上 | Y | Y | ✅ |
| HG-STAGE-W-EXPAND-DESIGN | approved（Q1=S1 中签 · Q2 env 显式 opt-in · Q3 新表走修订表回填） | 同上 | Y | Y | ✅ |

- reviews：`docs/harness/reviews/task_stage_w_write_expand_audit_R1_20261105.md` 在册且 R1 PASS（PR #326 合入）——**是**
- pre-30 invoke：`required ∩ {10,20,00}` 齐全（`invoke_20261105_10_task_draft.md` / `invoke_20261105_20_audit.md`）——**是**
- 机械辅助：`npx spec-wave verify --target . --task docs/tasks/active/task_stage_w_write_expand.md` → **VERIFY: PASS**（改码前实跑 · 四闸 approved 输出如上表）

**结论：可进入读码/改码**（首输出于改码前完成 · 本 invoke 为过程留痕）

## 30 实扫结论（Q1=S1 落笔目标选型）

- 既有 DB 面实扫（`app/db/models.py` 全表逐条）：turns / receipts / idempotency / hitl / memory 各面**无适配面**（消息 SoT 不写便签 · 回执台账不混业务数据 · HITL 表结构 freeze · memory 域闸分立）。
- **Q3 裁定（随签义务履行）**：新表 `ops_capability_notes` + alembic `20261105_capability_notes`（head 自 `20260923_memory_episodes` · upgrade/downgrade 可逆 · 唯一约束 `(tenant_id, idempotency_key)` + 索引 `(run_id)`/`(approval_id)`）→ task 档修订表已回填。
- 幂等双保险（FP-4）：幂等 store claim（租户内键 · 租约语义照旧）+ 落笔表唯一约束 DB 级兜底（`ON CONFLICT DO NOTHING` · store 进程丢失模拟形态断言不双写）。

## 交付面（本 PR）

| 面 | 内容 |
|----|------|
| 新能力 manifest | `app/ops/capability/manifests/ops.write.v1.yaml`——`ops.write.run_note`（run 备注/审计便签 · `tenant_scoped: true` · `hitl.required: true` + snapshot_fields · 顶层 `idempotency_key: "{{request_id}}"` · 独立写 tag `run_note` · **不进默认加载面**） |
| 执行体 | `app/ops/capability/defaults.py::ops_write_run_note`（async local_fn · tenant 只取 ctx fail-closed · approval_id 落便签行 · 成功 complete / 无副作用 release）+ `app/ops/capability/note_store.py`（DB IO 集中 · 延迟 import 对齐 idempotency/receipts 先例 · `.importlinter` 白名单同例登记） |
| loader | `manifest.py` **V13**（SPEC v0.1 Q4/A2+）：write 级能力 `tenant_scoped: true` 强制 · mock 特例清单不扩容（仅 `testing.write.echo` · testing/mock tag 谓词 · 冒充 id 无谓词 tag 亦拦）· 口径仅 `side_effect=write`（承「本波不碰 irreversible」钉死 · V1/V2 对 irreversible 照旧） |
| 新表 | `app/db/models.py::OpsCapabilityNote` + `alembic/versions/20261105_capability_notes.py` |
| 测试 | `tests/test_stage_w_write_expand.py` 16 枚（红测先行：先红 16 errors/2 failed → 全绿 16 passed） |
| 既有 probe 适配 | `tests/test_capability_testing_write.py` A8② probe 补 `tenant_scoped: true` 过 V13（断言对象 V1 放宽面不变 · 注释留痕） |
| D4 回写 | `docs/_tech_graph/l1/01_modules.md` capability 行 + db 行登记 + **HG-GRAPH-MODULES 30 回写回签行**（承 :134 先例 · task 档闸表同签确认） |
| task 档 | D1–D4 / A1–A8 勾选 + 修订表 30 行 + 30 自检结论 |

## 红线对拍

- **闸链零新建**：复用 PR #303 编排层审批闸 · `blocked_by=capability_write_hitl_required` 语义零改（nodes.py **零 diff**）
- **判序零 diff**：`registry.py` / `policy.py` **零 diff**（git 对拍）
- **deny_high_risk 永不豁免**：未触可见性判序 · 放行 tag 只豁免 deny_write 既有机制
- **resume 单路径**：grep 断言绿（`_execute_decided_resume` 唯一定义 router.py · auto_resume 同源 import）
- **SSE 零改 / web freeze 不破**：lg_rag / SSE 事件表 / hitl 消费语义零 diff（hitl 既有测试全组绿）
- **租户封闭**：intent/审批/执行三处 tenant_id 一致断言 · 跨租户守卫复用 F1–F6 既有面

## 验证（本地真 PG opsdesk_test）

| 命令 | 结果 |
|------|------|
| `pytest tests/test_stage_w_write_expand.py` | **16 passed** |
| `pytest tests`（全量） | **2056 passed · 5 failed 均为 master `6955b4c` 既有本地产能红**（临时 worktree 复证零我的增量）：episode_pattern_mine（未提交文件瞬时态 · 提交后自愈）/ write_replay_guard TC8 + strategy_scenario（diff-whitelist 锚点 `a1591e9`/`d337486` 后 scripts 漂移 · CI 无 PG skip 面）/ memory_vector_p1 + multi_replica_dualproc（env 依赖 · CI skip 面） |
| `ruff check app tests` | 零新增 |
| `./scripts/graph-compile.sh` | EXIT=0 |
| `npx spec-wave task lint` / `verify` | PASS / PASS |

## 出货

- PR 待 lead 终审验收（issue #323 令）· 合并由维护者执行
- 下一棒：40 复跑（live 面证据）→ PR+CI 绿+merge → CLOSE（docs/tasks/close/ 四字段）
