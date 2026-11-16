---
title: task · feat · P3-T5 admin memory 浏览/撤销端点（治理线）
---

# task · feat · P3-T5 admin memory 浏览/撤销端点（治理线）

> **状态**：`active`（2026-11-16 落卡 · 夜间自动执行波）
> **来源**：issue Cyning12/ops-desk-workspace#23（m03064/m03283/m03498 夜间授权 · 设计真源 workspace 14-p3-schedule-taskcard-design.md 终稿 R1-R23 §4.1 · 契约真源 15-p3-contracts.md §5 · 操作真源 lead 委派书）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | p3-t5-admin-memory-api |
| base | 17337d35 |
| 关联 issue | Cyning12/ops-desk-workspace#23 |
| 关联 PR | 待定（feat PR · 本波） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack；本波为 admin memory 治理面三端点 |
| graph_change_layer | G-L1（01_modules.md admin 行备注 + HG-GRAPH-MODULES 签收行） |
| review_hat | 20（R1 审查文已落盘 · GO） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 30 | approved 2026-11-16 · 授权 issue #23 m03064/m03283/m03498（夜间授权）+ 14 设计终稿 §4.1 + 15 契约 §5 为唯一范围真源 |
| HG-AUDIT-R1 | approved | 30 | approved 2026-11-16 · 同上授权（14 终稿 + 15 契约即审计真源）+ R1 审查文 docs/harness/reviews/task_p3_t5_admin_memory_api_audit_R1_20261116.md（GO） |
| HG-GRAPH-MODULES | approved | 30 | approved 2026-11-16 · 同上授权（admin 行备注属图谱登记义务 · 随 30 交付回填） |

## 背景

P3（Schedule/TaskCard 面）第 5 单（治理线）。admin memory 面现仅 `POST /admin/memory/purge`（admin/memory.py:73 物理删除 · 合规删除权），L2 记忆产品化缺浏览/撤销治理面——14 §4.3 裁定三开关放量第二步（写面灰度）以「admin 浏览/撤销面」为前置（02 §4「开启前必须可审」）。本波补三端点：facts 分页浏览 / facts revoke（幂等带审计）/ episodes 只读浏览。schema 逐字以 15 §5 为准；**admin 面=跨租户运维面**（R7 · LB4）：AdminSyncAuth（机器 Bearer 或 maintainer cookie），tenant_id/user_id 一律显式传入而非会话推导，与 F4 关系按「运维面例外」登记（03-security-audit §4 · SP3 purge 同缺口登记不本波收紧）。

## 范围

1. **三端点**（`app/ops/admin/memory.py` 扩展现有 router · 承 purge 同文件同鉴权面 · 15 §5 schema 逐字）：
   - `GET /api/ops/admin/memory/facts`：query tenant_id（必填 · 缺 422）· user_id（可选）· status（默认 active · 词表校验 active/superseded/revoked/expired · 词表外 422）· kind（可选 · fact/preference 词表校验 422）· limit（默认 50 · 上限 200 · 超界 422）· cursor（keyset max_length=512 · 坏 cursor 422）。投影字段：id/tenant_id/user_id/key/value/kind/source_run_id/source_turn/status/expires_at/created_at/updated_at（**不含 embedding**）。响应壳 `{"ok":true,"data":{"facts":[…],"next_cursor":…|null}}`。keyset 排序 (created_at DESC, id DESC) 承 lg_rag history 先例。
   - `POST /api/ops/admin/memory/facts/{key}/revoke`：body 显式 `{"tenant_id":…,"user_id":…}`（user_id 可选 · 缺省对该 tenant 下所有用户同 key 生效——15 §5.3「慎用」）；**复用 service.py:168 revoke_by_key 语义**（只动 status='active' 行 → 天然幂等）：user_id 给定时直调 `revoke_by_key(tenant_id, user_id, key, session=db)`，缺省时同语义 tenant 范围 UPDATE（同文件内手写同形 stmt · 不改 service 签名）。幂等响应：成功 200 `{"ok":true,"data":{"affected":N}}`；已撤销/无匹配 → **200 affected=0**（不 409 不报错）。审计 `logger.info` 记 key/tenant/affected 不记内容（purge 先例）。
   - `GET /api/ops/admin/memory/episodes`：query tenant_id（必填）· run_id/status（active/revoked 词表校验）/outcome（success/failure/partial 词表校验）可选 · limit/cursor 同 facts。投影字段：id/tenant_id/run_id/task_domain/context_fingerprint/plan_summary/tool_sequence/outcome/failure_class/status/created_at。**只读**：单条 revoke 不做（R13-N2）。
2. **鉴权**：三端点一律 `AdminSyncAuth`（deps.py:115 · Bearer `OPS_ADMIN_SYNC_TOKEN` 或 cookie maintainer · 未授权 401 · cookie 非 maintainer 403「Maintainer role required」· token 禁入日志）——零新鉴权面。
3. **cursor 工具**：admin/memory.py 内本地最小 keyset cursor 编解码（base64url JSON {ts,id} · 坏形 422）——admin→lg_rag 出边被 import-linter admin-outbound forbidden，禁复用 lg_rag/history.py；本地复刻其 encode/decode 形态（~25 行 · R3 裁定记录）。
4. **挂载**：承 admin 既有路由面——`admin_memory_router`（prefix=/admin/memory）已在 app/ops/router.py:33 注册，本波零 router.py 改动（端点挂在既有 router 对象上）。
5. **测试**（`tests/test_admin_memory_api.py` · 真 PG opsdesk_test · 五键 blank 前缀 · CI 终裁）：
   - 鉴权矩阵：三端点无凭据 401 · cookie 非 maintainer（override_auth_viewer）403 · 未授权 revoke 零写（表行 status 不变）。
   - facts：分页跨页不重不漏（keyset）· 默认 status=active 过滤 · status/kind 显式过滤 · limit=201/0 → 422 · 词表外 status/kind → 422 · 坏 cursor → 422 · 缺 tenant_id → 422 · 投影无 embedding 键。
   - revoke：首撤 200 affected=N · 重放 200 affected=0 · 无匹配 key 200 affected=0 · 缺 user_id tenant 范围撤销 · 审计留痕断言（caplog 记 key/tenant/affected · 不含 value）。
   - episodes：只读浏览 200 + 过滤（run_id/status/outcome）· 写动词 405（POST/DELETE /episodes 与 /episodes/{id} 404/405）· 投影字段断言。
6. **图谱**：`docs/_tech_graph/l1/01_modules.md` admin 行备注尾增 P3-T5 段（三端点登记）+ HG-GRAPH-MODULES 签收行（承 :143-:144 先例）。

## 非范围

- 不碰三开关放量（MEMORY_FACTS_ENABLED / MEMORY_FACTS_EXTRACT_ENABLED / MEMORY_FACTS_VECTOR_RECALL_ENABLED · T7）。
- 不碰 web /admin/memory 页（T9 · ops-desk-web 仓）。
- 不收紧 purge 缺口（SP3 登记不修 · 03-security-audit §4 运维面例外）。
- 不做 episodes 单条 revoke（R13-N2：status CHECK 已有 + revoke_by_run 已存在 + 召回双层过滤已够）。
- 不做 propose→confirm（14 §4.2 降级登记 P3 后续候选）。
- 不碰 alembic/（零 DDL · 状态机 revoked 值既有 CHECK 已含）· scripts/ · schedule/ · lg_rag/ 本体。

## 失败路径

- 未授权（无 Bearer 无 cookie / 错误 Bearer）→ 401；cookie 非 maintainer → 403；revoke 未授权零写。
- 缺 tenant_id / tenant_id 空白 strip 后空 → 422/400（词表参数 Query 校验 422 · strip 先例对齐 purge :84）。
- 词表外 status/kind/outcome → 422（词表校验）。
- limit=0 / limit>200 → 422（Query ge=1 le=200）；cursor 超 512 → 422；坏 cursor → 422。
- revoke 已 revoked/superseded/expired 或无匹配 key → 200 affected=0（幂等成功 · R7 钉死否 409）。
- episodes 写动词（POST/PUT/PATCH/DELETE）→ 405/404（只读面零写）。
- revoke 服务异常 → 500 不静默（rollback + logger.exception + HTTPException · admin/sync.py 先例）。
- 并行 agent 撞 registry.yaml / 01_modules.md 同区冲突 → 保留双方 entry 手动解，冲突块如实登记。

## 验收标准

- [ ] facts 分页浏览：跨页不重不漏 + 默认 status=active + status/kind 过滤 有锚 → tests/test_admin_memory_api.py::test_facts_pagination_keyset / test_facts_default_status_active / test_facts_filter_status_kind
- [ ] facts 参数校验：limit=201/0 · 词表外 status/kind · 坏 cursor · 缺 tenant_id → 422 有锚 → test_facts_limit_422 / test_facts_vocab_422 / test_facts_bad_cursor_422 / test_facts_missing_tenant_422
- [ ] 投影无 embedding：facts 响应对象键集合断言 有锚 → test_facts_projection_excludes_embedding
- [ ] revoke 幂等：首撤 200 affected=N · 重放 200 affected=0 · 无匹配 200 affected=0 有锚 → test_revoke_first_affected_n / test_revoke_replay_affected_0 / test_revoke_no_match_affected_0
- [ ] revoke 缺 user_id tenant 范围生效（同 tenant 异 user 同 key 全撤）有锚 → test_revoke_tenant_wide_without_user
- [ ] 审计留痕：caplog 断言 logger.info 记 key/tenant/affected 且不记 value 有锚 → test_revoke_audit_log
- [ ] 鉴权矩阵：三端点无凭据 401 · viewer 403 · 未授权 revoke 零写 有锚 → test_facts_unauthorized_401 / test_revoke_unauthorized_401_zero_write / test_episodes_unauthorized_401 / test_facts_viewer_403 / test_revoke_viewer_403_zero_write / test_episodes_viewer_403
- [ ] episodes 只读：GET 200 过滤锚 + 写动词 405/404 锚 → test_episodes_list_and_filters / test_episodes_write_verbs_rejected
- [ ] `pytest tests/test_admin_memory_api.py` 真 PG 全绿；`ruff check app tests` 绿；lint-imports 零新 forbidden 出边（admin→memory.service/deps 既有白名单 · admin→db 允许）
- [ ] 01_modules.md admin 行备注 + HG-GRAPH-MODULES 签收行已回写

### 自检结论

（30 交付后回填）

## 必读列表

- 设计真源：`../ops-desk-workspace/docs/01-scope/03-general-agent/14-p3-schedule-taskcard-design.md` 终稿（R1-R23 · §4.1 三端点 · §4.3 放量前置 · R7 跨租户运维面 · R13-N2 episodes 不撤）
- 契约真源：`../ops-desk-workspace/docs/01-scope/03-general-agent/15-p3-contracts.md`（§5.1 admin 面钉死 · §5.2 facts · §5.3 revoke · §5.4 episodes · §0 词表总表）
- 先例：`app/ops/admin/memory.py`（purge :73 鉴权/审计/500 不静默）· `app/ops/memory/service.py`（revoke_by_key :168 · revoke_by_source :138）· `app/ops/lg_rag/history.py`（encode/decode_cursor :61-80 形态 · 禁直引 · 本地复刻）· `app/ops/lg_rag/runs_router.py`（keyset 分页 + 响应壳）· `tests/test_admin_memory_purge.py`（鉴权矩阵/真 PG fixture）· `tests/test_admin_sync.py`（override_auth_viewer/maintainer + Bearer 用例）
- 体例：`docs/tasks/done/task_p3_t2_schedule_ddl_rest.md` · `docs/tasks/done/task_p3_t4_runs_readonly_api.md` · registry `docs/harness/audit_gates/registry.yaml`

## 思考轮

| 轮 | 结论 | early_stop |
|----|------|-----------|
| R0 | 范围对账（委派书 vs 14 终稿 §4.1 / 15 契约 §5）done | false |
| R1 | 失败路径推演（鉴权矩阵 · 幂等 200 affected=0 · 422 词表/limit/cursor · 405 只读）done | false |
| R2 | 非范围边界（T7 开关 / T9 web 页 / SP3 purge 缺口 / episodes revoke / propose→confirm）done | false |
| R3 | 关键决策记录（cursor 本地复刻 · tenant 范围 revoke 手写同形 stmt · 零 router.py 改动 · keyset 排序键）done | false |
| R4 | 体例对账（T2/T4 模板/registry/invokes/审查文/图谱登记）done | false |
| R5 | 收尾复核（验收 checklist 全锚定）done | false |

actual_last_round: R5

### R0 · 范围对账

委派书与 14 终稿/15 契约逐条对照：三端点（15 §5.2/§5.3/§5.4 schema 逐字 · 投影字段清单 · limit 默认 50 上限 200 T1 钉值 · cursor max_length=512）、AdminSyncAuth 复用 + admin 面=跨租户运维面（R7 · 15 §5.1 · tenant/user 显式传入）、revoke 复用 service.py:168 revoke_by_key 语义 + 已撤销 200 affected=0 否 409（R7 · 15 §5.3）、episodes 只读不做单条 revoke（R13-N2 · 15 §5.4）、审计 logger.info 记动作不记内容（15 §5.1 · purge 先例）、测试矩阵（鉴权 401/403 · 分页/过滤 · 幂等 · 审计留痕 · 只读 405/404）。委派书与契约一致零冲突；14 §4.1 表内路径写 {fact_id} 而 15 §5.3 钉 {key}——契约/schema 面 15 为真源（委派书同钉 {key}），按 {key} 落地。

### R1 · 失败路径推演

见「失败路径」节。新增推演：revoke key 路径参数含特殊字符（点分层键 deploy.window）→ FastAPI path 参数默认不含 / 即安全；facts status 词表含 expired（既有 CHECK 四值全收 · 词表校验对齐 §0 总表 facts.status 行）；episodes status 词表仅 active/revoked 二值（§0 episodes.status 行 · 与 facts 四值不同表）；user_id 空白串 strip 后空 → 视同缺省（tenant 范围）还是 400？裁定：显式传空白 user_id → 400（空白=调用方笔误非「慎用全撤」语义 · 防盲发 · strip 先例对齐 purge :84-87）；tenant_id 空白 → 400 同形。revoke 与并发写入竞态：只动 active 行 · 新写入 active 行在 UPDATE 后落库不受影响（幂等语义不锁未来写入 · 管理面低频可接受）。

### R2 · 非范围边界

T7 切面=不碰三开关 env/放量 runbook；T9 切面=不碰 web 仓 /admin/memory 页；SP3=purge 跨租户缺口登记不修；episodes 单条 revoke 不做（N2）；propose→confirm 不做（§4.2 降级登记）；零 DDL（revoked/expired 值既有 CHECK 已含 · embedding 列既有）→ banned_prefixes=[alembic/, scripts/]；schedule/lg_rag/hitl 零触。

### R3 · 关键决策记录

- **cursor 本地复刻**：keyset cursor 编解码照 lg_rag/history.py:61-80（base64url JSON · rstrip("=") · 坏形抛错映射 422）在 admin/memory.py 内本地实现 ~25 行——admin-outbound import-linter 契约 forbidden 含 app.ops.lg_rag，复用会破边或要求改 .importlinter（零改动体例优先）。
- **tenant 范围 revoke**：15 §5.3 user_id 可选缺省 tenant 全撤；service.revoke_by_key 签名 user_id 必填位置参数——不改 service 签名（最小改动），user_id 给定时直调复用，缺省时在 admin 层手写同形 UPDATE（同只动 active 行 + 同审计日志形态），语义对齐 §5.3「承 revoke_by_key 签名」。
- **零 router.py 改动**：admin_memory_router 已注册（app/ops/router.py:33 · prefix=/admin/memory），三端点挂既有 router 对象 → registry allowed_app_files 仅 app/ops/admin/memory.py 一件。
- **keyset 排序键**：(created_at DESC, id DESC)；id 为 UUID 列（PG UUID 有序），cursor payload {ts,id} · id 解析 uuid.UUID 失败 → 422。
- **episodes 查询直读 ORM**：episode_service 无 list 函数（只 write/revoke_by_run/recall_success），admin 观测面直读 app.db.models（admin→db 边允许 · purge 同文件已直用 AsyncSession）。

### R4 · 体例对账

照 T2/T4：task 档结构/人工闸表/registry entry（base=17337d35 · banned_prefixes=[alembic/, scripts/] 因零 DDL）/invokes by-task 四件/R1 审查文 GO 机读词/spec-wave task lint PASS 为闸；图谱登记=admin 行备注 + 签收行（memory 行不动——端点归属 admin 面 · 承 memory-compliance-delete 登记在 admin 行先例 :102）。

### R5 · 收尾复核

验收 10 条逐条锚到测试或 lint 证据；回退路径=revert 本波 PR（零 DDL 零数据迁移 · revert 即完整回退）。

## 实现备忘

### 偏差登记

（无 · 30/40 波如有冲突和解在此追加）

### 限制登记

- **L1（tenant 范围 revoke 慎用语义）**：缺省 user_id 对 tenant 下所有用户同 key 生效（15 §5.3 明示「慎用」）；v1 不加二次确认闸门（admin 面机器 Bearer 低频操作 · 与 purge expected_count 双闸门不同级——purge 是物理删除不可逆 · revoke 是状态机逻辑失效）。
- **L2（audit 不记内容）**：审计日志只记 key/tenant/affected（15 §5.1）；value 永不入日志。

## 测试策略

pytest tests（CI 终裁 · 真 PG opsdesk_test · 五键 blank 前缀）；目标文件 tests/test_admin_memory_api.py 全绿 + ruff check app tests + lint-imports 零改动（admin→memory.service/deps 既有白名单 · admin→db 允许）；spec-wave verify 三闸 approved。

## 修订记录

| 日期 | 修订 |
|------|------|
| 2026-11-16 | 落卡（夜间自动执行波 · 授权 issue #23 m03064/m03283/m03498） |
