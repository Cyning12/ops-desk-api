---
title: task · feat · P3-T6 幂等转正 DB（多副本前置唯一转正项 · R9 四条件）
---

# task · feat · P3-T6 幂等转正 DB（多副本前置唯一转正项 · R9 四条件）

> **状态**：`active`（2026-11-16 落卡 · 夜间自动执行波）
> **来源**：issue Cyning12/ops-desk-workspace#23（m03064/m03283/m03498/m03551 夜间授权 · 设计真源 workspace 14-p3-schedule-taskcard-design.md 终稿 R1-R23 §6.4/§10 · 契约真源 15-p3-contracts.md commit 62af6ea · 操作真源 lead 委派书）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | p3-t6-idempotency-db-default |
| base | 87fd1ddf |
| 关联 issue | Cyning12/ops-desk-workspace#23 |
| 关联 PR | 待定（feat PR · 本波） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack；本波为 capability 持久化默认值翻转 |
| graph_change_layer | G-L1（01_modules.md capability 行登记 + HG-GRAPH-MODULES 签收行） |
| review_hat | 20（R1 审查文已落盘 · GO） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 30 | approved 2026-11-16 · 授权 issue #23 m03064/m03283/m03498/m03551（夜间授权）+ 14 设计终稿 §6.4 R9 + 15 契约为唯一范围真源 |
| HG-AUDIT-R1 | approved | 30 | approved 2026-11-16 · 同上授权（14 终稿即审计真源）+ R1 审查文 docs/harness/reviews/task_p3_t6_idempotency_db_default_audit_R1_20261116.md（GO） |
| HG-GRAPH-MODULES | approved | 30 | approved 2026-11-16 · 同上授权（capability 行备注登记义务 · 随 30 交付回填） |

## 背景

P3（Schedule/TaskCard 面）第 6 单 · 多副本前置唯一转正项。设计 14 §6.4 R9 + Q3 裁定「接受默认转 db（platform）· 附 LB6 四条件」：现状 `configure_persistence_from_env()`（app/ops/capability/persistence.py:31）在未设 `OPS_CAPABILITY_PERSISTENCE` 时落 `null`（不防重 + WARNING）——多副本部署忘配即静默不防重。本波把**未设（含空串）默认值翻转为 `db`**（DbIdempotencyStore 跨实例防重 + DbReceiptSink 回执落库 · :320/:48 现役转正），显式 `null` 保留为回退口。装配仍是部署动作：显式 `db` 是生产推荐写法，代码默认只决定「没写时走哪边」；刻意不做自动探测（默认 db 是配置面默认值变更，非运行时自适应）。

## 范围

1. **默认值翻转**（`app/ops/capability/persistence.py`）：:39 `or MODE_NULL` → `or MODE_DB`（未设/空串 → db）；docstring 改写（R9①：装配是部署动作不是代码默认值 · 刻意不做自动探测——默认 db 是**配置面默认值变更，非运行时自适应** · 显式 null 回退旧默认）；非法值 ERROR 文案词表补 null；null 分支 WARNING 文案改写为「显式回退」口径；`describe_persistence()` null 分支 note 同步口径。
2. **调用方口径同步**：`app/ops/capability/__init__.py:102` 注释（W6「默认不启用」→ 新默认）· `app/ops/admin/capability.py:12/:17` docstring（「没配 = 没有防重」→「显式 null = 没有防重 · 未设默认 db」）。
3. **测试**（真 PG postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 委派层 monkeypatch.delenv · CI 终裁）：
   - `tests/test_capability_persistence_db.py`：默认用例翻转（未设 → "db" + Db 装配）· **env 四分回归矩阵**（显式 db / 显式 memory / 显式 null / 未设=新默认 db · R9②）· **fail-closed 回归**（Db store 连接故障 → ainvoke ok=False 且下游传输零调用 · R9③ + 失败路径表 R-P3-10）· **显式 null 回退回归**（显式 null → mode null + Null 装配 + WARNING · R9③）· **默认面防重双调实证**（未设 env → 双调第二调 `duplicated` · 传输仅一次 · 回执单行）· 既有 DbIdempotencyStore 测试复跑。
   - `tests/test_log_init_window.py`：TC1/TC1补组/TC3 钉死格式换显式 "null" 探针 + 新文案钉死；新增未设（空串≡未设）→ INFO「能力层持久化：db（跨实例防重 + 回执落库）」窗口可见组。
   - `tests/test_admin_capability_observability.py` 零改实证（fixture 复位推导 mode · 翻转后断言仍成立）。
4. **文档同步**（承 T3 文档同步先例）：`.env.example:147` 段（「空=null」→「未设=db（P3-T6 新默认）· 显式 null 回退」）· `docs/guides/GUIDE_env_inventory_v1.md:15` 行补注 · `docs/guides/RUNBOOK_local-acceptance_v1_zh.md:91` 行改新默认口径。
5. **图谱**：`docs/_tech_graph/l1/01_modules.md` capability 行备注（P3-T6 默认翻转 · 不新增一级模块 · 不增 implementedBy）+ HG-GRAPH-MODULES 签收行。
6. **风险登记**（R9④ · R-P3-10 落本档「实现备忘 · 风险登记」）：默认 db 后**热路径每次写能力调用多两次 DB 写**（idempotency claim + receipt），且可用性耦合反转——DB 故障时写能力按既有 persistence 闸 fail-closed（ok=False · 绝不静默放行重复执行）· 观测端点 `/admin/capability/runtime` mode 可见 · 显式 null/memory 回退口保留。

## 非范围

- 不碰熔断/预算/nonce（维持进程内声明）。
- 不碰 device_tokens（R3 已降契约草案）。
- 不碰 hitl 面同形装配（`OPS_HITL_PERSISTENCE` / app/ops/hitl/persistence.py 不在本波）。
- 不改契约文档 15-p3-contracts.md（§7.3/§7.5「代码默认仍是未设（null）· T2b 附带条件」与 14 终稿 + 委派书矛盾 · 以 14 终稿 + 委派书为准 · 矛盾登记偏差 D1 · 跨仓文档非本波 allowed_tree）。
- 不碰 scripts/ · alembic/ · lg_rag/ 本体；不新增表/迁移/路由/SSE 事件类型。

## 失败路径

- 幂等 DB store 不可用（DB 连接故障）→ capability 调用 **fail-closed**（既有语义：`adapters/http_generic.py::_aclaim` 异常 → gateway `_aerr_result` ok=False · 绝不静默放行重复执行）+ span 告警（R-P3-10）。
- 显式 `OPS_CAPABILITY_PERSISTENCE=null` 回退 → 不防重 + WARNING（`/admin/capability/runtime` mode=null · health warn 可见）。
- 非法值 → ERROR「无法识别（仅 db / memory / null）」+ null 兜底（不悄悄退回某个实现）。
- 默认 db 且 DB 不可用 → 进程启动照常（DbIdempotencyStore 构造不连库）；首次写能力调用 fail-closed（同上首条）。
- 回退 = revert 本波 PR + 部署面显式 `OPS_CAPABILITY_PERSISTENCE=null`。
- 并行 agent 撞 registry.yaml / 01_modules.md 同区冲突 → rebase origin/master 保留双方 entry 手动解，冲突块如实登记。

## 验收标准

- [ ] persistence.py:39 未设/空串 → `"db"`（configure 返回 + DbIdempotencyStore/DbReceiptSink 装配）有锚 → tests/test_capability_persistence_db.py::test_configure_persistence_defaults_to_db
- [ ] docstring 改写含「装配是部署动作，不是代码默认值」「刻意不做自动探测」「默认 db 是配置面默认值变更，非运行时自适应」（R9①）→ app/ops/capability/persistence.py:1-16
- [ ] env 四分回归矩阵（显式 db / 显式 memory / 显式 null / 未设）全绿（R9②）→ test_configure_persistence_env_matrix
- [ ] fail-closed 回归：Db store 连接故障 → ainvoke ok=False 且下游传输零调用（R9③）→ test_default_db_store_failure_fails_closed
- [ ] 显式 null 回退回归：显式 null → mode "null" + Null 装配 + WARNING（R9③）→ test_configure_persistence_explicit_null_fallback
- [ ] 默认面防重双调实证：未设 env → 第二调 `meta.duplicated` · 传输仅一次 · 回执单行 → test_default_surface_double_invoke_dedup
- [ ] 既有 DbIdempotencyStore 测试复跑全绿（真 PG opsdesk_test）→ pytest tests/test_capability_persistence_db.py
- [ ] test_log_init_window 钉死格式同步：显式 null 窗口 WARNING 新文案 + 未设窗口 INFO db 新增组全绿 → pytest tests/test_log_init_window.py
- [ ] .env.example + GUIDE_env_inventory + RUNBOOK 注记同步（承 T3 先例）
- [ ] 01_modules.md capability 行登记 + HG-GRAPH-MODULES 签收行回写
- [ ] `npx --yes spec-wave@3.5.0 task lint --file` PASS · spec-wave verify 三闸 PASS · `ruff check app tests` 绿

### 自检结论

（draft 期占位 · 30 交付后回填）

## 必读列表

- 设计真源：`../ops-desk-workspace/docs/01-scope/03-general-agent/14-p3-schedule-taskcard-design.md` 终稿（R1-R23 · §6.4 R9 四条件 · §10 波次表 · §11 失败路径）
- 契约真源：`../ops-desk-workspace/docs/01-scope/03-general-agent/15-p3-contracts.md`（commit 62af6ea · §7.3/§7.5 口径矛盾见偏差 D1）
- 先例：`app/ops/capability/persistence.py` · `app/ops/capability/idempotency.py:320`（DbIdempotencyStore）· `tests/test_capability_persistence_db.py` · `tests/test_log_init_window.py` · `tests/test_multi_replica_dualproc.py`
- 体例：`docs/tasks/done/task_p3_t2_schedule_ddl_rest.md` · registry `docs/harness/audit_gates/registry.yaml`

## 思考轮

| 轮 | 结论 | early_stop |
|----|------|-----------|
| R0 | 范围对账（委派书 vs 14 终稿 §6.4/§10 / 15 契约 §7）done | false |
| R1 | 冲突对账（15 §7.3/§7.5「代码默认仍是未设（null）」vs 14 终稿 + 委派书翻转 → 照后者 · 登记 D1）done | false |
| R2 | 影响面枚举（翻转点唯一 persistence.py:39 · 测试三文件 · 文档三面 · 调用方注释两处 · observability 零改实证）done | false |
| R3 | 钉名与口径（WARNING「能力层持久化：null…」· ERROR 词表补 null · INFO db 不变 · 日志窗口探针纪律保留）done | false |
| R4 | 风险推演（R-P3-10 热路径 DB 写 + 可用性耦合反转 · fail-closed 既有语义承接 · 回退口保留）done | false |
| R5 | 收尾复核（验收 11 条全锚定 · 体例对账 T2/T3/T5 模板）done | false |

actual_last_round: R5

### R0 · 范围对账

委派书与 14 终稿逐条对照：§6.4 R9 四条件（docstring 改写 / env 四分矩阵 / fail-closed+显式 null 两回归 / 风险登记 R-P3-10）· §10 波次表 T6 行（「OPS_CAPABILITY_PERSISTENCE 默认 null→db · DbIdempotencyStore 现役转正」）· Q3 裁定「接受默认转 db（platform）· 附 LB6 四条件」。验收三键（默认面防重双调实证 · env 四分矩阵回归 · fail-closed+显式 null 回退验证）与委派书验收一致。

### R1 · 冲突对账

契约 15 §7.3 写「代码默认仍是未设（null），不在代码里改默认值」并把 R9 条件记作「T2b 附带条件」、§7.5 env 表标 T2b——与 14 终稿 §0/§6.4/§10 及委派书（未设=新默认 db · T6 承载）矛盾。14 终稿是三方评审合并终稿（R1-R23 全关闭）且委派书明确「默认值翻转」，**裁定：照委派书 + 14 终稿翻转代码默认 null→db**；契约 15 §7.3/§7.5 口径矛盾如实登记偏差 D1，不改契约文档（跨仓 · 非本波 allowed_tree）。翻转后显式 db 仍是生产推荐写法（部署清单），未设才走新默认。

### R2 · 影响面枚举

翻转点唯一：persistence.py:39 `or MODE_NULL` → `or MODE_DB`。`describe_persistence()`（:80）从实际对象推导 mode 故翻转后零改逻辑（仅 null 分支 note 口径同步）。测试：test_capability_persistence_db.py:312 默认用例翻转为 db + 补四分矩阵/fail-closed/显式 null/默认面双调；test_log_init_window.py TC1(:77)/TC1补组(:87)/TC3(:127) 探针 env 换显式 "null" 并钉新文案，新增未设 → INFO db 组（TC2 :106/:114 不受影响）；test_admin_capability_observability.py:79 靠 fixture 复位（reset_idempotency_store → Null）推导 mode 而非 env，预计零改（实证核销）；test_multi_replica_dualproc.py 显式 db 不受影响。文档：.env.example:147 段 / GUIDE:15 / RUNBOOK:91。调用方注释：capability/__init__.py:102 · admin/capability.py:12/:17。历史文档（docs/audits · docs/tasks/done · docs/tasks/close · 旧 invokes）不改。

### R3 · 钉名与口径

钉死文案新旧对照：WARNING 旧「能力层持久化未配置（%s 未设）：**幂等防重与回执落库均未启用**，不可上生产」→ 新「能力层持久化：null（**幂等防重与回执落库均未启用**，不可上生产）」（显式 null 与非法值兜底共用 · 非法值另有 ERROR 行解释）；ERROR 旧「仅 db / memory」→ 新「仅 db / memory / null」（null 是合法显式值）；INFO「能力层持久化：db（跨实例防重 + 回执落库）」**逐字不变**（TC2 钉死行不动）。describe note null 分支：「未启用防重与回执落库（OPS_CAPABILITY_PERSISTENCE 显式 null 回退 / 非法值兜底）—— **不可上生产**」（observability 测试断言「不可上生产」子串存续）。日志窗口测试纪律（裸 python 子进程 · PYTHONPATH=仓根 · 显式 env 防仓根 .env 渗入）保留；空串≡未设口径在翻转后仍成立（or MODE_DB 同一路径）。

### R4 · 风险推演

R-P3-10（热路径 DB 写 + 可用性耦合）：默认 db 后每次写能力调用多两次 DB 写（claim INSERT ON CONFLICT + receipt INSERT）；DB 故障时 `_aclaim` 异常 → gateway `_aerr_result` ok=False（fail-closed · 绝不静默放行重复执行 · 与 14 §11 失败路径表一致）。可用性耦合**反转**：原口径「忘配 = 静默不防重」（安全隐患），新口径「DB 故障 = 写能力显式失败」（可用性敏感但安全）——多副本部署的安全默认应取后者。缓解：观测端点 mode/health 可见 · span 告警 · 显式 null/memory 回退口保留 · DbIdempotencyStore 构造不连库（启动零耦合 · DB 晚起不阻塞进程启动）。

### R5 · 收尾复核

验收 11 条逐条锚到测试名或文件行；体例照 T2 模板（人工闸表 / 思考轮表头 `| 轮 | 结论 | early_stop |` / 自检结论机读词 / registry entry base=87fd1ddf / invokes 四件 / R1 审查文 GO 机读通过词）；回退路径 = revert PR + 部署面显式 null。

## 实现备忘

### 偏差登记

- **D1（真源口径矛盾 · 2026-11-16）**：契约 15-p3-contracts.md §7.3「代码默认仍是未设（null），不在代码里改默认值」+ §7.5 env 表把 R9 条件记作「T2b 附带条件」，与 14 终稿 §0/§6.4/§10（T6 承载「默认 null→db」）+ 委派书矛盾。处理：照 14 终稿 + 委派书翻转；不改契约文档（跨仓 · 非本波 allowed_tree）；登记在此供 lead/00 跨仓和解。

### 风险登记

- **R-P3-10（热路径 DB 写 + 可用性耦合 · 承 14 §11）**：默认 db 后热路径每次写能力调用多两次 DB 写（idempotency claim + receipt 落库）；DB 不可用时写能力按既有 persistence 闸 fail-closed（ok=False · 不静默重复执行）+ span 告警。缓解：`/admin/capability/runtime` mode/health 可见 · 显式 null/memory 回退口保留 · DbIdempotencyStore 构造不连库（启动零耦合）。

### 限制登记

- **L1（同步 invoke 面）**：Db 版防重仅异步接口；同步 `invoke` 在 db 模式下对带幂等键的写能力 fail-closed（`HttpCapabilityError`「只支持异步接口，请走 ainvoke」· 红线 R8 既有语义不变）。
- **L2（hitl 面不联动）**：`OPS_HITL_PERSISTENCE` 同形装配默认值仍 null（非范围 · 跨波候选）。

## 测试策略

pytest tests（CI 终裁 · 真 PG opsdesk_test · 委派层 monkeypatch.delenv）；目标文件 tests/test_capability_persistence_db.py + tests/test_log_init_window.py 全绿 + 全量回归；ruff check app tests；import-linter 零新 forbidden 出边（本波不新增 import 边）；本地环境性红与基线逐签对照登记（仓根 .env 渗入先例承 T2）。

## 修订记录

| 日期 | 修订 |
|------|------|
| 2026-11-16 | 落卡（夜间自动执行波 · 授权 issue #23 m03064/m03283/m03498/m03551） |
