# invoke · 10 · memory-compliance-delete · task 落稿

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 10-task（SPEC signed 后落稿 · 本棒由 00 委派 10-task 帽 Agent 执行） |
| **文件** | `docs/tasks/active/task_memory_compliance_delete.md` |
| **上游** | `docs/spec/memory-compliance-delete/SPEC-memory-compliance-delete_v1.md`（signed · HG-SPEC-SIGNOFF=approved 2026-09-22 · a65ce3b · S1 同步物理删除 + A1 日志审计 + 默认干跑双闸门签收锁死） |
| **格式基准** | `docs/tasks/done/task_security_input_isolation.md`（真读对齐字段 · PR #161 已合 · CLOSE 归档） |

## 结论

**PASS（落稿）** · 范围 D1 service 层物理删除（`purge_by_user(tenant_id, user_id, *, dry_run=True, session=None) -> PurgeReport` 落 `app/ops/memory/service.py` · DELETE 谓词含且仅含 tenant+user · 全 status 整行删除（embedding 列随行消失）· 干跑默认零写 + 计数守恒（实删 deleted==scanned · 干跑 deleted==0）· 幂等第二次 0 行 · 审计 `logger.info` 记动作不记内容 · 方案 S1 承 SPEC §4 裁决不重演）/ D2 管理面入口（`POST /admin/memory/purge` 新文件 `app/ops/admin/memory.py` + router.py 注册 · AdminSyncAuth 逐字对齐 admin/sync.py :32 · 请求体 `{tenant_id, user_id, dry_run=true, expected_count=null}` · **双闸门**：默认干跑零写 echo 标志 · 实删缺 expected_count → 400 · 计数不等 → 409 零删除 · 计数等 → 200 且 deleted==expected_count · 空白 strip 后空 400 · 500 不静默 :35-45 先例）/ D3 删除后断言（recall_active 零命中 · recall_with_vector 零命中（mock embedder）· 表行全 status 零残留 · 越 tenant/越 user 零影响 · caplog 审计字段存在不含内容）/ D4 图谱文档（零 alembic · admin 行备注 + api 行注册备注 + 人签新行 00 代录位 · graph-compile 绿 · memory README + docstring 同步）；非范围沿用 SPEC §3（其它业务表 · DSR 自动化 · 状态机改动 · 用户自助端点 · 批量/定时 purge · RAG/Qdrant/Langfuse 删除 · 新审计表 · 前端 UI · 历史回改 10 条）；验收 **22 条**全否定性断言化逐块映射 SPEC §6（人工闸 1 / D1×5 / D2×4 / D3×4 / D4×2 / 变异检验×3 / 工程×3）· 与 SPEC 实质差异**零**；failure_paths **13 条**（SPEC §5 十条翻四列 + 过程三）；R0–R5 全轮无 early_stop。

## 实扫留痕（本帽真跑）

- `git branch --show-current` = `task/memory-compliance-delete` ✓（SPEC 签收 a65ce3b 后）
- revoke 纪律：`revoke_by_source` :134-163 / `revoke_by_key` :166-201 均为逻辑失效（docstring :7 明示不物理删）；谓词钉死 :176-177（跨 tenant = 0 行）；审计记动作不记内容 :159-162/:197-200；session 纪律 :10-11；strip 先例 :110-115——与 SPEC §1 一致
- AdminSyncAuth：deps.py :86-116（`secrets.compare_digest` :98 · token 空 Bearer 路径禁用 :97-103 · maintainer 403 :105-111）；挂法先例 admin/sync.py :32；500 不静默先例 :35-45——本帽逐行复核一致
- 模型：models.py status CHECK 四值 :500-503 · `supersedes` FK `ondelete="SET NULL"` :545-549 · `embedding` Vector(1024) deferred :558-560——两通路同源一张表复核成立
- 路由面：router.py :4-5/:24-25 注册 `admin_sync_router` + `admin_capability_router`；`app/ops/admin/` ls 实证 `__init__/capability/schema/service/sync/sender` **无 memory.py**（新增义务）；admin 面零写操作路由（本 purge 是首个不可逆写端点）
- 向量通路：`_VECTOR_RECALL_SQL` :281-289 查表本身 · `_vector_top_m` 双保险 :461-469 · 回退 span `memory_vector_degraded` :494-501
- 命名冲突扫：`grep -rn 'purge_by_user\|PurgeReport\|admin/memory' app/ tests/ evals/ docs/_tech_graph/` = **零命中**（全仓 purge 命中仅 Dockerfile apt-get 与 SPEC 文档）
- pytest 基线真跑：`python -m pytest tests --collect-only -q` = **1333 collected**
- 文档落点：`app/ops/memory/README.md` **存在**（ls 实证）
- B1 落盘 **11 行**（回归×9 · **改编×0** · 新增×1 · 迁移无×1 · 删除×0）；关键实证：无既有用例依赖「ops_memory_facts 行不可物理删除」反向断言 → 改编面为零钉死；用例计数 10 文件真跑（memory_service_db 13 / memory_gate 15 / memory_injection 23 / memory_vector_p1 9 / memory_extract_p1 14 / memory_embedding_backfill 15 / memory_time_decay_tz 6 / admin_sync 10 / admin_capability_observability 12 / auth 10）
- HG-GRAPH-MODULES 真值核验：**真读** `docs/_tech_graph/l1/01_modules.md`——模块表已建置（bootstrap 签 2026-07-16 · 签录链完整至 :92）· `admin` 行 :30 · `memory` 行 :28（**无对外 HTTP 端点**——purge 首个对外入口落 admin 模块内）· `api` 行 :20 → 有图谱义务按实判（admin 行备注 + api 行注册备注 + 人签**新行留 00 代录位**随 30 交付落盘 · llm-layer-hardening/session-summary-fallback/security-input-isolation 先例）+ **偏离回炉补闸条款**钉死
- SPEC §1 锚点复核**零语义偏差**

## 闸态

- `HG-TASK-DRAFT` = **落稿时待签**（00 验收代录/人签 · 本帽不签）
- `HG-AUDIT-R1` = **落稿时待签**（blocks 30 · 20 审后人签/授权代录）→ **30 拒开工**
- `HG-GRAPH-MODULES` = **approved（模块表已建置 · 本帽真读）** + 本 task 新签义务（admin 行备注 POST /admin/memory/purge 首个 admin 面不可逆写端点 · api 行注册备注 · 人签记录新行 00 代录位 · 随 30 交付落盘）；偏离（新增一级模块/表列/新 SSE 事件/新建 DB 审计表/改状态机与 recall/revoke 既有语义）→ 回炉补闸
- `HG-PILOT-OPSDESK-GLAYER` = n/a

## lint

`npx spec-wave task lint --file docs/tasks/active/task_memory_compliance_delete.md` = **PASS**（exit 0 · 2026-09-22 真跑；初跑 W5 思考轮槽位提醒已修：补 `### R5 · 交付判定` 节后复跑零告警 PASS）

## 下一棒

20-task-audit 书面审（对照 SPEC）→ HG-TASK-DRAFT + HG-AUDIT-R1 人签 → 30（`task/memory-compliance-delete` · 承 SPEC §8 序：D4 图谱 → D1 purge 函数 → D2 admin 路由 → D3 断言 · 状态机/recall/revoke 既有语义零改动）→ 40（干跑对拍 + 双闸门三态 + 两通路零命中 + 越域零影响 + 变异检验三条）→ CLOSE。后续 20/30/40 invoke 由各棒落盘本目录（命名对齐 `invoke_<yyyymmdd>_<hat>_<verb>_memory_compliance_delete.md`）。
