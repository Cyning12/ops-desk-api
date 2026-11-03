# invoke · task_api_w_join_gap_fix 30 实现（2026-11-02 · 30 帽 · api 仓）

| 项 | 内容 |
|----|------|
| **时间** | 2026-11-02 |
| **分支** | `task/api-w-join-gap-fix`（PR #307 随动） |
| **范围** | W-fix-1（HITL 手动 resume TTL 闸 + `STATUS_EXPIRED` 启用）· W-fix-2（issues/pulls/overview 只读面租户谓词）· freeze 增补条 · `tenant_id=''` 实扫回填 · G-L1 薄备注 |

## GATE_VERIFY（开工首输出 · 机械+人工双轨）

`npx spec-wave verify --target . --task docs/tasks/active/task_api_w_join_gap_fix.md` → **VERIFY: PASS · EXIT=0**（复跑于 e8e12b6 机读修复后；图谱锚点检查 INFO 跳过 · 不影响）

| 闸 | status（task 闸表真值） | blocks_30 | 判定 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 20-R1, 30 | ✅ |
| HG-AUDIT-R1 | approved | 30 | ✅ 可 30 |
| HG-GRAPH-MODULES | approved | — | ✅ |
| HG-W-FIX-DESIGN | approved | 30 | ✅ 可 30（四决策钉死） |

闸事件留痕：首跑曾因闸表 status 格附注（`approved（签名附注）`）被 spec-wave 3.5.0 精确等值判 pending（EXIT=2）→ 30 拒开工并报回 → 00 修复（e8e12b6 闸格裸 approved 化 · 语义零变更）→ 复跑 PASS 后开工。

## 红测先行（先于实现 · 已验红）

新建两测试文件，实现前运行：**6 failed（恰为负样本 ×6）· 6 passed（正样本 ×6）**，红得干净、无连带误伤：

- `tests/test_hitl_resume_ttl_gate.py`（6 测）：过期 approved resume → 409 + detail 含 `approval_expired` 与「过期」+ 单据置 `expired`；env 旋钮同源实证（90s · 超龄 409）；approved 缺 `decided_at` fail-closed → 409+expired；未过期 approved 正样本 200 且单据不误置 expired；rejected 拨回 2h 仍 200（驳回收工豁免闸）；decide 超龄 pending 仍成功（store 层 · 决策③）。
- `tests/test_tenant_readonly_surface.py`（6 测 · 全 DB-gated）：B session 三端点空集/归零（issues/pulls `total==0` · overview cycle/review `sample_size==0` + throughput `0` + trend 全零；sync_run/scan_snapshot 全局不断言）；A 显式 state 正样本（`total==1` · cycle sample==1 · throughput==1 · trend 末日各 1）。

## 实现清单

### W-fix-1 · HITL 手动 resume TTL 闸（决策①③④）

- `app/ops/hitl/router.py`：`resume_request` 状态守卫后增 TTL 闸（仅罩 approved）——`decided_ts is None or time.time() - decided_ts > ttl` → `store.amark_expired` + **409** detail `approval_expired：批准已超执行权 TTL（{ttl}s）过期，单据已置 expired 终态；请重新发起审批`（中文含「过期」命中 web mapping `/过期|expired/i`）。惰性助手 `_approval_ttl_seconds()`/`_decided_at_ts()` 复用 `app/ops/lg_rag/multi/nodes` 真源（auto_resume 同款防环模式 · **单一旋钮 `OPS_HITL_APPROVAL_CONSUMPTION_TTL_SECONDS` 禁第二判据**）。rejected 豁免；decide 路径零触碰。
- `app/ops/hitl/store.py`：`STATUS_EXPIRED` 死码激活——新增 `amark_expired(request_id)`（Protocol/InMemory/Null/Db 四实现）；approved→expired **单向**迁移（InMemory 判 status 守卫 ≡ Db `WHERE status='approved'` · 并发重复 mark 至多一胜）；Db 用 `_MARK_EXPIRED` UPDATE+RETURNING，零新列零迁移。

### W-fix-2 · 只读面租户谓词（F4 口径）

- `app/ops/tenant_context.py`：新增 `tenant_from_request_state(request)`——读 `request.state.ops_tenant_id`（deps.py:43-45 注入），缺失/空白回落 `TENANT_A`（与 deps 回落同值 · 兼容 dependency_overrides 测试路径）。
- `app/ops/issues.py:29` `list_issues` / `app/ops/pulls.py:30` `list_pulls`：stmt/count_stmt 基底加 `tenant_id ==` 谓词。
- `app/ops/overview.py:67` `get_overview`：cycle/review/throughput/双 trend 五条查询加谓词；`OpsSyncRun`/`OpsScanSnapshot` 无 tenant_id 列（全局 repo 级）不加谓词。
- 详情路由不存在（三端点仅 `@router.get("")`）→ F4「详情 404」条件不触发，只做列表空集/指标归零。

### freeze 增补条（决策②）

- 落点：`docs/tasks/done/task_hitl_browser_decide.md` 新增「freeze 增补条款（hitl-browser-decide-v1）」节 + 修订记录行（注明「2026-11-02 HG-W-FIX-DESIGN 签署生效」）。
- 定位经过：api 仓无 `docs/contracts/hitl*`；workspace contracts 无 hitl 契约件；freeze 本体 = web 仓 `src/api/hitl.ts` 头注释（红线不动 web 仓 · web 侧镜像壳 `task_web_hitl_resume_expired_mapping` :71 亦钉「本壳不改 freeze 文件」）→ api 侧落点取 freeze 上游真值 task 文件（hitl.ts 头注释自认「上游真值 = task_hitl_browser_decide.md」）。
- 增补条内容：触发（approved 超 TTL/decided_at 不可解析 fail-closed）· 出口（409+`approval_expired` 中文含「过期」）· 终态（expired · 决策④）· TTL 单一旋钮（默认 3600s · [1,86400]）· 作用面收窄（decide 不拒超龄 pending · rejected 豁免 · 决策③）· web 渲染语义增量（onResume mapping · W-fix-1-web 承接）。

### `tenant_id=''` 实扫（task :82 N3 回填）

`docker exec ops-desk-api-db-1 psql -U ops -d opsdesk`（2026-11-02）：

| 表 | `tenant_id=''` 行数 | 总量 | 处置 |
|---|---|---|---|
| `ops_issues` | **0** | 881（全 `ops-desk-pilot`） | 谓词面 · 从严直落 |
| `ops_pull_requests` | **0** | 1855（全 `ops-desk-pilot`） | 谓词面 · 从严直落 |
| `ops_hitl_requests` | **40** | — | 不在 W-fix-2 谓词面（task :91 仅 issues/pulls/overview · hitl 读面无租户谓词）· 如实记录不处置 |

谓词面两表 0 行 → 按 N3 默认**从严**直落（`tenant_id ==` 即天然排除 '' 行），无偏离、无需维护者加签。已回填 task 修订表。

## 旧测 grep 影响面清单（task :128 · 逐条标注 · 无静默改测）

判定基准：W-fix-1 只改 HTTP `resume_request` 入口（approved+超龄才拒；旧测 decide 均 `adecide` 现造、decided_at=now 远在默认 TTL 3600s 内）；W-fix-2 只读面经 override 测试路径 state 缺失→回落默认租户 `ops-desk-pilot`，与种子数据同租户。

### resume/HITL 面（grep `resume` 命中 20 文件）

| 测试文件 | 处置 | 理由 |
|---|---|---|
| `tests/test_hitl_resume.py` | **保留 · 零改** | HTTP resume 全链 · 行均现 decide（新鲜）→ 不触 TTL 闸 · 回归实测绿 |
| `tests/test_hitl_resume_async.py` | **保留 · 零改** | patch `resume_hitl_run` · 新鲜行 · 绿 |
| `tests/test_hitl_resume_events.py` | **保留 · 零改** | HTTP `/resume` 事件链 · 新鲜行 · 绿 |
| `tests/test_hitl_pending_decide.py` | **保留 · 零改** | decide 语义面（400/404/409/422）· 决策③钉死不动 · 绿 |
| `tests/test_hitl_auto_resume.py` | **保留 · 零改** | auto 路径（`aclaim_approved_for_resume`）不经手动闸 · 绿 |
| `tests/test_hitl.py` | **保留 · 零改** | OA 签名面/callback · 不经手动 resume 闸 |
| `tests/test_hitl_approval_consumption.py` | **保留 · 零改** | T1 消费门读时 TTL 语义本 task 未动；`test_ta4_consumption_hit_does_not_waive_gateway_or_policy` 为基线预存失败（与本 task 无关） |
| `tests/test_multi_replica_dualproc.py` | **保留 · 零改** | `test_hitl_cross_instance_resume` 基线预存失败（与本 task 无关 · 不新增） |
| `tests/test_write_approval_gate.py` `test_lg_rag_sse_resume.py` `test_lg_rag_sse_run_worker.py` `test_react_observe.py` `test_lg_rag_replay_resume_follow.py` `test_hitl_approved_replan_quality.py` `test_hitl_observe_config_injection.py` `test_lg_rag_basic.py` `test_memory_embedding_backfill.py` `test_capability_testing_write.py` | **保留 · 零改** | grep 命中「resume」均图内 `Command(resume)`/事件语义 · 不经 HTTP `resume_request` 入口 |
| `tests/test_hitl_resume_ttl_gate.py` | **新增** | W-fix-1 红测先行（6 测） |

### 只读面（grep issues/pulls/overview 命中）

| 测试文件 | 处置 | 理由 |
|---|---|---|
| `tests/test_issues.py` | **保留 · 零改** | override_auth_maintainer 不设 state → 回落 `ops-desk-pilot` 与种子同租户 · 断言 total==1 等全绿（实测） |
| `tests/test_pulls.py` | **保留 · 零改** | 同上 · 绿 |
| `tests/test_overview.py` | **保留 · 零改** | 同上 · 绿 |
| `tests/test_tenant_context.py` | **保留 · 零改** | ContextVar 面未动（HTTP 谓词走 `request.state` 不跨用 ContextVar）· 绿 |
| `tests/test_tenant_readonly_surface.py` | **新增** | W-fix-2 红测先行（6 测 · DB-gated） |

**结论：影响面内旧测零修改、零删除；全量「保留」**；唯一 FAILED 命中（`test_ta4…`、`test_hitl_cross_instance_resume`）均为基线预存失败清单内成员，非本 task 引入。

## 质量门

- `ruff check app tests` → **All checks passed**
- 新测 12/12 绿（红→绿闭合）；影响面回归批（10 文件 171 测）→ 170 passed + 1 failed（`test_ta4…` 基线预存）
- `./scripts/graph-compile.sh` → EXIT=0；`npx spec-wave task lint --file …` → PASS；`lint-wiki-delta` → PASS
- 全量 pytest vs 基线：**27 failed / 1997 passed / 2 skipped**（286.90s）vs 基线 27 failed / 1985 passed / 2 skipped——失败集**逐条一致零新增**（27 条清单与基线完全相同 · 含 `test_ta4…` 与 `test_hitl_cross_instance_resume`），passed +12 = 本 task 新测全绿 · 交付标准达成

## 图谱 G-L1 薄备注（`docs/_tech_graph/l1/01_modules.md`）

- `data` 行：issues/pulls/overview 租户谓词一句（F4 口径 · '' 从严 · sync/scan 全局豁免）
- `hitl` 行：resume TTL 闸一句（同判据单旋钮 · expired 终态 · rejected 豁免 · decide 不动）
- 底部 HG-GRAPH-MODULES 回写记录行（承 :134 先例）

## 红线自查

- SSE/event_type 零改（grep 无触碰）· decide 过期语义零改（decide 不拒超龄 pending 有测试守护）· web 仓零改 · workspace 仓零改 · :8000 uvicorn 进程未动
