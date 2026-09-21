# invoke · 30-implement · memory-compliance-delete

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 30（实现 · 不签任何人闸 · 图谱新签行留 00 代录位） |
| **task** | `docs/tasks/active/task_memory_compliance_delete.md`（signed · HG-TASK-DRAFT/HG-AUDIT-R1=approved） |
| **SPEC** | `docs/spec/memory-compliance-delete/SPEC-memory-compliance-delete_v1.md`（signed · a65ce3b · S1 同步物理删除 + A1 日志审计 + 默认干跑双闸门） |
| **分支** | `task/memory-compliance-delete`（每次 commit 前 `git branch --show-current` 核验 · 禁止 master/main 直改 · 禁止 push） |

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved | Y | 20-R1, 30 | ✅ |
| HG-AUDIT-R1 | approved | approved | Y | Y | ✅ |
| HG-GRAPH-MODULES | approved | approved | Y | —（模块表已建置 · 新签义务随 30 落盘留 00 代录位） | ✅ |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | — | N | — |

reviews：`docs/harness/reviews/task_memory_compliance_delete_audit_R1_20260922.md` 存在且 R1 通过 ✓
pre-30 invoke：{10, 20} 齐全 ✓（`invoke_20260922_10_*` / `invoke_20260922_20_*`）
机械辅助：`npx spec-wave verify --target . --task docs/tasks/active/task_memory_compliance_delete.md` = **VERIFY: PASS**（真跑）

结论：**可进入读码/改码**。

## 实现纪要（D1–D4 · 实现序承 SPEC §8：D4 图谱 → D1 purge → D2 路由 → D3 断言）

- **D4-a 图谱先行**：`01_modules.md` `admin` 行备注（`POST /admin/memory/purge` 首个 admin 面不可逆写端点 · AdminSyncAuth · dry_run 默认 true + expected_count 双闸门 · 审计记动作不记内容）+ `api` 行注册备注（`admin_memory_router`）+ 人签记录新行 **pending（留 00 代录位 · 30 不签闸）**；`./scripts/graph-compile.sh` 绿（graph.json 同步再生成）。
- **D1 service 层**：`app/ops/memory/service.py` 新增 `PurgeReport`（frozen dataclass · `dry_run/scanned/deleted/by_status/elapsed_s/recorded_at` backfill 字段族 · 计数守恒：实删 `deleted==scanned` · 干跑 `deleted==0` · `sum(by_status)==scanned`）+ `purge_by_user(tenant_id, user_id, *, dry_run=True, session=None)`——谓词含且仅含 tenant+user（`_purge_predicate` 锚点函数收口，越域防线 · 变异检验①兜底对象）；全 status 无差别整行 DELETE（embedding 列随行消失 · 行零残留 = 两通路零残留）；`dry_run=True` 默认零写（同谓词 count + by_status 分桶 · 干跑/实删同口径）；单条 DELETE 单事务原子；session 纪律沿用模块先例（传入只 flush · 不传自开 commit）；审计 `logger.info("memory purge_by_user tenant=%s user=%s dry_run=%s affected=%d")` 记动作不记内容（实删/干跑/幂等 0 行全含 · affected=实删行数 · 干跑恒 0）；module docstring 补「运行期不物理删 · 合规物理删除只走管理面 purge」。
- **D2 管理面入口**：新文件 `app/ops/admin/memory.py`（`APIRouter(prefix="/admin/memory", tags=["admin"])` · `POST /purge` · `_user: OpsUser | None = AdminSyncAuth` 逐字对齐 admin/sync.py :32 先例）；请求体 `{tenant_id, user_id, dry_run: bool = true, expected_count: int | None = null(ge=0)}`；空白 strip 后空 → 400（不触库）；双闸门：默认干跑零写 echo `dry_run` · 实删缺 `expected_count` → 400（不触库）· 同 session 内干跑探针计数不等 → **409 零删除**（detail 含 expected/current 计数）· 等 → 200 实删 commit 且 `deleted==expected_count`；500 不静默（`except HTTPException: raise` 先行 → 异常 rollback + `logger.exception` + 500 · admin/sync.py :35-45 先例同形）；`app/ops/router.py` +2 行注册。
- **D3 删除后断言**：`tests/test_memory_purge_db.py`（7 用例 · 真 PostgreSQL · `mfp-test-%` 夹具自清理）+ `tests/test_admin_memory_purge.py`（9 用例 · `mfpa-test-%`）——谓词锚点编译断言（含且仅含 tenant/user · 无 status/key）· 干跑前后逐行对拍零写 · 四态+embedding 行整删 · 幂等 deleted==0 · 他 tenant 同 user/同 tenant 他 user 快照逐行不动 + 跨 tenant 0 行 · `recall_active` 零命中 · `recall_with_vector` 零命中（`MEMORY_FACTS_VECTOR_RECALL_ENABLED=true` + FakeEmbedder 1024 维确定性先例同形）· caplog 审计字段存在且不含 key/value · 干跑/实删同谓词计数口径对拍 · 路由面 401/403 零删除 + 双闸门三态 + 空白 400 + strip 透传 + 幂等重放 409 + 500 rollback 零删除。

## 关键实现裁定（30 如实记录 · 非偏离）

1. **审计 affected 口径**：实删 = 实删行数（含幂等 0）；干跑 = 0（真实零写 · `dry_run=True` 标志与 `scanned` 报告字段已携带计数信息）——与 revoke「affected=实际影响行数」先例同口径，钉死日志格式逐字未改。
2. **双闸门探针同 session**：路由实删路径在同一 `get_db` session 内先做干跑探针计数再 DELETE——同事务隔离级收窄 count→delete 竞态窗；409 路径零写不触 commit（隐式 rollback）。
3. **`_purge_predicate` 锚点函数**：谓词收口为模块级私有函数，测试编译 DELETE 语句做「含且仅含 tenant_id+user_id」锚点断言（行为面由越域测试 + 变异检验①双兜底）。
4. **测试夹具租户前缀独立**：`mfp-test-%` / `mfpa-test-%` 与既有 `mf-test-%`/`mfv1-test-%` 零交叉，互不清理。

## B1 旧测影响面处置回填（11 行）

| # | 处置（task 钉死） | 实测 |
|---|------|------|
| 1 test_memory_service_db 13 用例 | 回归 + 新增 purge 断言 | 全绿零改动；purge service 断言落 `test_memory_purge_db.py`（#10） |
| 2 test_memory_vector_p1 9 用例 | 回归 + 新增向量零命中 | 全绿零改动；`test_vector_path_zero_hit_after_purge`（FakeEmbedder 先例同形）新增 |
| 3 test_memory_embedding_backfill 15 用例 | 回归 | 全绿零改动（全量轮未现偶发 flaky） |
| 4 gate/injection/extract/time_decay 58 用例 | 回归 | 全绿零改动（purge 不触闸/装配/抽取/衰减路径） |
| 5 test_admin_sync 10 + test_auth 相关 | 回归 + 新路由鉴权断言 | 全绿零改动；`test_unauthorized_rejected_and_zero_delete`（401/403 + 表行零变化）新增 |
| 6 test_admin_capability_observability 12 用例 | 回归 + override 先例沿用 | 全绿零改动；`as_admin` fixture 逐字沿用 `dependency_overrides[require_admin_sync]` 先例形态 |
| 7 hitl_resume / hitl_resume_events | 回归 | 全绿零改动（与 purge 路由正交） |
| 8 graph/issues/pulls/admin_sync_sender | 回归 | 全绿零改动（sync payload 面零改动） |
| 9 evals/input_isolation recall mock | 回归 | 全绿零改动（purge 不触装配/evals 路径） |
| 10 新增守护义务 | 新增 | `tests/test_memory_purge_db.py`（7）+ `tests/test_admin_memory_purge.py`（9）= **16 新增**（collected 1333→1349） |
| 11 alembic 链 | 无（零迁移钉死） | `git diff master -- alembic/` = **0 行**（迁移 diff 为空断言成立） |

## 验证结果（全部真跑）

- `pytest tests` 全量：**1349 collected（基线 1333 + 新增 16）= 1345 passed / 3 failed / 1 skipped**；3 failed 均为基线环境性同款（`test_capability_http_adapter::test_urllib_transport_honors_explicit_capability_proxy` · `test_chat_ws` 两条 · 与前序 invoke 留痕名单逐字一致），memory/admin 相关面零失败；`memory_backfill` 偶发 flaky 本轮未出现
- `ruff check app tests`：**57 errors = 基线 57 零新增**（新文件全部 `All checks passed!`；router.py I001 经 `git show HEAD:` 对拍为基线既有未动）
- `./scripts/graph-compile.sh`：绿（exit=0 · graph.json 再生成入 docs commit）
- alembic 零迁移：`git diff master -- alembic/` = 0 行
- 生产 diff 白名单：`git diff master --stat -- app/` = `service.py`（purge 块 + docstring）+ `router.py`（+2 行注册）+ `admin/memory.py`（新增）+ README（文档）· 无越界文件

## 双闸门三态实测（test_admin_memory_purge）

| 态 | 请求 | 实测 |
|---|------|------|
| 缺 expected_count | `dry_run=false` 无 expected_count | **400** · 表行 2→2 零删除 |
| 计数不等 | `expected_count=99`（实际 2） | **409** · detail.current_count=2 · 表行零删除 |
| 计数等 | 先干跑取 scanned=3 → 实删 expected_count=3 | **200** · deleted==3==expected · 表行 0 残留 · 同 expected 重放 → 409（幂等防线） |

## 变异检验 ×3（做完即还原 · 还原后复绿）

| # | 变异 | 预期 | 实测 |
|---|------|------|------|
| ① 谓词可检 | `_purge_predicate` 临时去 tenant_id 谓词 | 「他 tenant 行不动」必挂 | **2 failed**（`test_purge_predicate_anchor_only_tenant_user` + `test_cross_tenant_and_other_user_zero_impact`）→ 还原 16/16 全绿 ✓ |
| ② 全量可检 | DELETE 临时只删 `status='active'` 行 | 表行零残留断言必挂 | **2 failed**（`test_real_purge_all_status_rows_gone` + `test_purge_idempotent_second_delete_zero`）→ 还原 16/16 全绿 ✓ |
| ③ 审计可检 | 临时去掉 purge 审计 `logger.info` | caplog 断言必挂 | **3 failed**（`test_dry_run_default_*` + `test_real_purge_*` + `test_purge_idempotent_*` 全挂）→ 还原 16/16 全绿 ✓ |

## 闸纪律

- 未签任何人闸：图谱人签记录新行写为 **pending（30 已交付 · 留 00 代录位 · 30 回写内容待 00 ratify）**。
- 未切 master/main · 未 push；commit 前逐次 `git branch --show-current` = `task/memory-compliance-delete`。
- 形态零偏离：零新一级模块/零新表列（alembic diff 空）/零 SSE 事件/零 DB 审计表/状态机与 recall/revoke 语义零改动——graph_delta_note 回炉条款未触发。
