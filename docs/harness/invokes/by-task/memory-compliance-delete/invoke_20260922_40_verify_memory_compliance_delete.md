# invoke · 40 核验 · memory-compliance-delete（记忆合规物理删除权）

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 40 核验（不签任何人闸 · 不改实现码） |
| **核验对象** | 30 交付 `3d0a6b3`（feat）+ 图谱回写 `9308bec` + HG-GRAPH-MODULES 行 ratify `741f585` |
| **task** | `docs/tasks/active/task_memory_compliance_delete.md`（验收 22 条 · B1 11 行） |
| **SPEC** | `docs/spec/memory-compliance-delete/SPEC-memory-compliance-delete_v1.md`（signed · S1 同步物理删除 + A1 日志审计 + 默认干跑双闸门） |
| **分支** | `task/memory-compliance-delete`（全程核验 · 禁止 master/main 改码 · 禁止 push · 已遵守；基线对照走 git worktree 未切分支，用后已 remove） |
| **改动纪律** | 40 不改实现码；唯一临时改码 = 变异检验①复做（已 `git checkout` 还原 · 工作树净，仅 `.coding-kit/events/` 未跟踪属 harness 过程产物） |

## 总判定

**PASS（22/22 验收条亲核通过）**，无阻塞问题；2 条环境/工具既有事项如实知会（见「问题清单」）。

## 核验证据（全部真跑留痕）

### 1. 全量 pytest + 基线红对照（worktree · 未切分支）

- 当前 HEAD（741f585）：`pytest tests` = **1345 passed / 3 failed / 1 skipped**，collected = **1349**（与 30 自称逐字一致）。
- 3 红 = `test_capability_http_adapter::test_urllib_transport_honors_explicit_capability_proxy` + `test_chat_ws::test_ws_message_streams_events` + `test_chat_ws::test_ws_second_message_while_active_rejected`。**基线对照实证**：`git worktree add /tmp/ops-desk-api-baseline-10d72e7 origin/master`（= `10d72e7` · detached · 未切分支）+ 补同 `.env`，同 .venv 复跑该 3 用例 **同样 3 failed** → 环境性基线红，与本次改动无关，30 自称属实。
- 基线 collect-only = **1333**（真跑复核 task 基线数属实）；1349 − 1333 = **+16 新增**（与 30 自称一致）。
- `test_memory_embedding_backfill` 偶发 flaky：本轮全量跑未复现（30 记录可信，未作否决项；若复现按 flaky 复跑区分，不影响本波判定）。

### 2. 谓词防线读码（不可逆操作核心防线）

- `service.py:254-259` `_purge_predicate(tenant_id, user_id)` 返回**有且仅有** `tenant_id ==` 与 `user_id ==` 两个条件——无 status/key/source_run_id，全 status 无差别。
- count 与 DELETE **共用同一谓词对象**（`:271` /`:281`）——干跑/实删同计数口径是结构性保证而非约定；锚点测试 `test_purge_predicate_anchor_only_tenant_user` 编译 DELETE 断言含 tenant/user、不含 status/key/source_run_id，亲跑通过。
- `PurgeReport`（:234-251）frozen dataclass 字段族 `dry_run/scanned/deleted/by_status/elapsed_s/recorded_at`，docstring 钉死计数守恒（实删 deleted==scanned · 干跑 deleted==0 · sum(by_status)==scanned）。

### 3. 双闸门三态亲跑复测（16 新测全绿）

`pytest tests/test_memory_purge_db.py tests/test_admin_memory_purge.py -v` = **16 passed**（亲跑 · 非采信）：

| 态 | 请求 | 实测 |
|---|------|------|
| 缺 expected_count | `dry_run=false` 无 expected_count | **400** · 表行 2→2 零删除（`test_real_purge_missing_expected_count_400`） |
| 计数不等 | `expected_count=99`（实际 2） | **409** · detail.current_count=2 · 零删除（`test_real_purge_count_mismatch_409_zero_delete`） |
| 计数等 | 先干跑 scanned=3 → 实删 expected_count=3 | **200** · deleted==3==expected · 表行零残留（`test_real_purge_count_match_200_deleted_eq_expected`） |
| 重放 | 同 expected_count=3 再发 | **409**（幂等防线 · 同测 :175-184） |

鉴权面：`test_unauthorized_rejected_and_zero_delete`（无凭证 → 401/403 且表行零变化）PASSED；空白 400 与 strip 透传、500 不静默（rollback + detail.stage）均亲跑通过。

### 4. AdminSyncAuth 挂载对齐读码

- `app/ops/admin/memory.py:77` `_user: OpsUser | None = AdminSyncAuth` —— 与先例 `admin/sync.py:32` **逐字一致**，零新鉴权面。
- `deps.py:86-116` 复核：`secrets.compare_digest`（:98）· token 空则 Bearer 路径禁用（:97-103）· 非 maintainer 403（:105-111）· `AdminSyncAuth = Depends(require_admin_sync)`（:116）。
- `app/ops/router.py` +2 行注册（:6 import · :27 include），前缀 `/api/ops` 下 `/api/ops/admin/memory/purge`（tags=["admin"]）。

### 5. 审计断言亲核（记动作不记内容）

- 日志格式串 `service.py:284-290`：`"memory purge_by_user tenant=%s user=%s dry_run=%s affected=%d"`——参数位只有 tenant/user/dry_run/affected，**物理无 key/value 位置**；实删/干跑/幂等 0 行同路径全含。
- caplog 断言读码：`test_dry_run_default`（:181-187）断言 `tenant=/user=/dry_run=True/affected=0` 在场**且** `"project.primary_repo"`（key）与 `"cyning/ops-desk"`（value）**不在场**；实删（:205-207 `affected=4`）与幂等（:224 `affected=0`）同形。三处均亲跑通过。

### 6. 变异检验①复做（谓词可检）

- 临时去 `_purge_predicate` 的 tenant_id 谓词 → `pytest` 两文件 = **2 failed**（`test_purge_predicate_anchor_only_tenant_user` + `test_cross_tenant_and_other_user_zero_impact`，与 30 留痕逐字一致）/ 14 passed。
- `git checkout -- app/ops/memory/service.py` 还原 → **16/16 复绿** · `git status` 净（变异零残留）。
- ②全量可检 / ③审计可检：采信 30 invoke 留痕（各含具体挂测名与还原复绿记录；同断言织体、同操作形态，①为不可逆操作核心防线故 40 亲复①）。

### 7. ruff / graph-compile / alembic

- `ruff check app tests` = **57 errors = 基线 57**（对基线 worktree 同 .venv 直跑对拍 · 零新增）。
- `./scripts/graph-compile.sh` 绿（exit=0）；运行后 `graph.json` 仅 `generated_at` 时间戳漂移，已 `git checkout` 还原（工具既有行为 · 非本波引入）。
- `git diff master --numstat -- alembic/` = **0 行**（零迁移钉死成立）。
- 生产 diff 白名单：`git diff master --stat -- app/` 仅 `service.py`（purge 块+docstring）+ `admin/memory.py`（新增）+ `router.py`（+2）+ `README.md`（文档）；tests/ 仅 2 个新测试文件——无越界文件。

### 8. B1 抽核（5 行亲跑）+ 图谱行 ratify 真读

- 抽 5 行全符：#1 `test_memory_service_db.py`=13 · #2 `test_memory_vector_p1.py`=9 · #3 `test_memory_embedding_backfill.py`=15 · #5 `test_admin_sync.py`=10 · #6 `test_admin_capability_observability.py`=12 且 override 先例（`dependency_overrides[require_admin_sync]` :33-35）在案；#11 alembic diff=0（见 §7）。命名扫 `purge_by_user|PurgeReport|admin/memory`：命中仅限 4 个本波新文件，既有文件零命中（无冲突）。
- 图谱 `01_modules.md` 真读：`api` 行（:20）注册备注 `admin_memory_router` ✓；`admin` 行（:30）备注（首个 admin 面不可逆写端点 · AdminSyncAuth · 默认干跑 + expected_count 双闸门 · 审计记动作不记内容）✓；HG-GRAPH-MODULES 新行（:93）= **approved**。
- ratify `741f585` diff 真读：新行由「pending（30 已交付 · 留 00 代录位）」翻转为「approved（00 代录 · 30 回写内容 00 ratify 2026-09-22）」——**单行真 ratify 非空签**，diff 仅该行 + graph.json 同步。
- D4 文档：`app/ops/memory/README.md` 新增「合规物理删除」节（:19-27 · 双闸门/幂等/审计不记内容/残余风险如实承认）+ 故障语义行（:82）+ 模块职责行（:13）；`service.py` docstring（:7-8）补「运行期不物理删 · 合规物理删除只走管理面 purge_by_user」。

## 22 条验收判定汇总

| 块 | 条数 | 判定 |
|----|------|------|
| 人工闸（HG-AUDIT-R1 approved 后 30 · HG-GRAPH-MODULES 新签 ratify） | 1 | ✅（闸表 :39-40 真读 · ratify 741f585 真读） |
| D1 · service 层 purge（谓词锚点 / 四态+embedding 整删 / 干跑对拍计数守恒 / 幂等同口径 / 审计字段） | 5 | ✅ 读码 + 亲跑 |
| D2 · 管理面入口（401/403 零删除 / 默认干跑 echo / 双闸门三态 / 空白 400） | 4 | ✅ 亲跑 9 路由测全绿 |
| D3 · 删除后断言（recall_active 空 / recall_with_vector 空 / 全 status 零残留 / 越域零影响） | 4 | ✅ 亲跑 7 service 测全绿 |
| D4 · 图谱/文档（零 alembic · admin/api 行备注 + 人签 ratify · graph-compile 绿 · README/docstring） | 2 | ✅ 真读核验 |
| 变异检验（①40 亲复 2 挂→还原绿 · ②③ 采信 30 留痕） | 3 | ✅ |
| 工程（B1 闸前置回填抽核 · pytest 1345/3/1 基线红对照 · ruff 57=基线 · diff 白名单） | 3 | ✅ |
| **合计** | **22** | **22/22 PASS** |

## 问题清单

1. **3 红基线环境性**（worktree @ 10d72e7 + 同 .env 实证同红：capability proxy urllib 传输 + chat_ws ×2）——非本波问题，合并前不阻塞但应知会维护者。
2. `graph-compile.sh` 运行即扰动 `graph.json` 时间戳——工具既有行为非本波引入，已还原。
3. 残余风险承 SPEC §7 四条（双闸门只锁数量不锁主体 / 同计数内容替换竞态 / 审计日志面不可机查台账 / 删除权受理核验另案）——SPEC/task/代码 docstring/README 四处口径一致，30 无超额声称。

## 诚实定性复核

删除不可逆如实定性（防线全在闸前与断言层 · 删后不可恢复不虚假承诺）；双闸门防不住「计数碰巧相等的错目标」如实承认（SPEC §7①）；审计落日志面非机查台账如实承认（§7③ · 升级路径在案）。30 交付无超额声称，属实。
