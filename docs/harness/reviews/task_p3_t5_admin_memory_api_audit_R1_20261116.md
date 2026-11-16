# task_p3_t5_admin_memory_api · R1 审查文（20 帽）

- 时刻：2026-11-16
- 审查人：exec-p3-t5（20 帽 · 夜间授权 issue Cyning12/ops-desk-workspace#23 m03064/m03283/m03498 · 00 代签体系）
- 对象：`docs/tasks/active/task_p3_t5_admin_memory_api.md` v1

## 审查项

1. **范围对账**：task 范围 6 条与 15-p3-contracts.md §5 逐字对账——§5.2
   facts 分页浏览（tenant_id 必填 · status 默认 active 词表校验 · kind 可选 ·
   limit 默认 50 上限 200 T1 钉值 · cursor keyset max_length=512 · 投影十二
   字段不含 embedding · 响应壳 {"ok","data":{"facts","next_cursor"}}）、§5.3
   revoke（路径 {key} · body 显式 tenant_id/user_id 可选 · 复用 service.py:168
   revoke_by_key 语义只动 active 行 · 幂等 200 affected=0 否 409 · 审计
   logger.info 记 key/tenant/affected）、§5.4 episodes 只读（投影十一字段 ·
   run_id/status/outcome 过滤 · 单条 revoke 不做 N2）、§5.1 admin 面=跨租户
   运维面（AdminSyncAuth · tenant/user 显式传入 · Bearer 优先 · 非 maintainer
   403「Maintainer role required」· token 禁入日志）1:1 落入；委派书内联面
   （鉴权矩阵/幂等/审计留痕/405 只读/图谱行备注+签收行）全部锚定。GO。
2. **非范围**：三开关放量（T7）· web /admin/memory 页（T9）· purge 缺口收紧
   （SP3 登记不修）· episodes 单条 revoke（R13-N2）· propose→confirm（§4.2
   降级登记）均明示排除；零 DDL（revoked/expired 既有 CHECK 已含）→
   banned_prefixes=[alembic/, scripts/]。GO。
3. **路径钉名 {key} 裁定**：14 §4.1 表内写 {fact_id}，15 §5.3 钉 {key} 且
   委派书同钉 {key}——15 为契约/schema 真源（其 §0 声明与 14 冲突处 14 优先，
   但本条为端点 schema 面属 15 管辖且委派书双重确认 {key}），按 {key} 落地；
   revoke_by_key 语义（tenant+user+key 谓词）亦只能承 key 路径。GO。
4. **tenant 范围 revoke 裁定（user_id 缺省）**：不改 service.revoke_by_key
   签名（最小改动 · 既有调用面零影响），user_id 给定时直调复用、缺省时 admin
   层手写同形 UPDATE（只动 active 行 + 同审计形态）——满足 §5.3「承
   revoke_by_key 签名」语义复用要求且幂等性同质（谓词 status='active'）。
   显式空白 user_id → 400（防「慎用全撤」被笔误盲发 · purge :84 strip 先例）。
   GO。
5. **cursor 本地复刻裁定**：admin-outbound import-linter 契约 forbidden 含
   app.ops.lg_rag——复用 history.encode_cursor/decode_cursor 须改 .importlinter
   或破边；admin/memory.py 内本地最小复刻（base64url JSON {ts,id} · 坏形 422）
   ~25 行保 import-linter 零改动（承 T4「零 .importlinter 改动」体例）。GO。
6. **零 router.py 改动**：admin_memory_router（prefix=/admin/memory）已于
   app/ops/router.py:33 注册，三端点挂既有 router 对象——挂载面零改，
   registry allowed_app_files 仅 app/ops/admin/memory.py 一件。GO。
7. **既有资产复用**：AdminSyncAuth（deps.py:115 零新鉴权面）· revoke_by_key
   （service.py:168 幂等带审计）· purge 审计/500 不静默先例（admin/memory.py
   同文件）· 响应壳 {"ok","data"} 与 keyset 体例（runs_router）· 测试面
   override_auth_viewer/maintainer + Bearer（test_admin_sync）与
   真 PG 五键 fixture（test_admin_memory_purge）。零新造轮。GO。
8. **失败路径**：9 条覆盖 401/403 矩阵零写/422 五路（缺 tenant · 词表外
   status/kind/outcome · limit 超界 · 坏 cursor）/幂等 200 affected=0 否 409/
   episodes 写动词 405/404/500 不静默/并行冲突和解登记，均可机判。GO。
9. **验收可机判**：10 条验收逐条锚到 tests/test_admin_memory_api.py 具名
   用例或 lint/CI 命令；测试纪律真 PG + 五键 blank 前缀承委派书；脏树期
   wave_gate_registry 红为在途面咬禁改面常态（commit 后转绿 · CI 终裁）。GO。
10. **思考轮**：R0-R5 表 + actual_last_round=R5 + 六小节齐备；R3 记录
    cursor 本地复刻/tenant 范围 revoke/零 router.py 改动/keyset 排序键/
    episodes 直读 ORM 五决策。GO。
11. **registry entry**：status=active · base=17337d35 · allowed_app_files 一件
    （app/ops/admin/memory.py）· allowed_tree_files 六件（task active+done/
    审查文/01_modules/registry/测试文件）· allowed_tree_prefixes=invokes 目录 ·
    banned=[alembic/, scripts/] · yaml safe_load 验证通过。GO。
12. **人工闸**：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三行 approved，
    依据 issue #23 m03064/m03283/m03498 夜间授权；01_modules.md admin 行
    备注+签收行随 30 交付回填（memory 行不动——端点归属 admin 面 · 承
    memory-compliance-delete 登记在 admin 行先例）。GO。

## 结论

**GO · 通过（零阻塞项）** —— task v1 可进 30 实施（夜间授权窗口 · 30 台账见 invoke_20261116_30_impl.md · 40 验收台账见 invoke_20261116_40_acceptance.md）。
