---
title: task · feat · P3-T2b create_schedule 写类 capability（对话化创建定时任务）
---

# task · feat · P3-T2b create_schedule 写类 capability（对话化创建定时任务）

> **状态**：`active`（2026-11-16 落卡 · 夜间自动执行波）
> **来源**：issue Cyning12/ops-desk-workspace#23（m03064/m03283/m03498 夜间授权 · 设计真源 workspace 14-p3-schedule-taskcard-design.md 终稿 R1-R23 · 契约真源 15-p3-contracts.md commit 62af6ea §2 · 操作真源 lead 委派书）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | p3-t2b-create-schedule-capability |
| base | 17337d35 |
| 关联 issue | Cyning12/ops-desk-workspace#23 |
| 关联 PR | 待定（feat PR · 本波） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack；本波为 capability manifest + adapter 面 |
| graph_change_layer | G-L1（01_modules.md capability 行备注 + schedule 行 deps 登记 + HG-GRAPH-MODULES 签收行） |
| review_hat | 20（R1 审查文已落盘 · GO） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 30 | approved 2026-11-16 · 授权 issue #23 m03064/m03283/m03498（夜间授权）+ 14 设计终稿 + 15 契约 §2 为唯一范围真源 |
| HG-AUDIT-R1 | approved | 30 | approved 2026-11-16 · 同上授权（14 终稿 + 15 契约即审计真源）+ R1 审查文 docs/harness/reviews/task_p3_t2b_create_schedule_capability_audit_R1_20261116.md（GO） |
| HG-GRAPH-MODULES | approved | 30 | approved 2026-11-16 · 同上授权（capability 行备注 + schedule 行 deps 登记属图谱登记义务 · 随 30 交付回填） |

## 背景

P3（Schedule/TaskCard 面）第 2b 单。T2 已交付 schedule 数据面 + REST 管理面（双表 + store + 四端点，PR #420）；本波交付**对话化创建主体**：写类 capability `ops.schedule.create`——supervisor 在用户说「每天/定时/提醒我」时经 catalog 引导选中本能力，走既有写闸链（registry → policy → args schema → V1 幂等键 → W1 HITL 确认卡 → 执行），执行体直调 T2 store（与 REST 同一套归属校验 + 双上限 + 词表校验，不复制逻辑）。W1 HITL 卡题钉死「创建定时任务 = 承诺未来 LLM 花费」，复用既有 HitlApprovalCard（web 零改动）。契约逐字以 15 §2 为准；体例承 P2a/T1 五步法与 stage W 写闸链先例。

## 范围

1. **manifest**（`app/ops/capability/manifests/ops.schedule.v1.yaml` · 新文件 · 15 §2.1 逐字字段族）：
   - id=ops.schedule.create · kind=local_fn · description/when_to_use/when_not_to_use 逐字（catalog 引导语：用户说「每天/每小时/定时/稍后自动执行」时选中；一次性立即执行不选中）。
   - tags=[schedule, write] · risk_level=medium（不触 deny_high_risk · 该层永不豁免）· side_effect=write · enabled=true · tenant_scoped=true（V13）。
   - hitl.required=true（V2）· snapshot_fields 九键=[thread_id, name, instruction, schedule_kind, run_at, interval_seconds, time_of_day, timezone, max_fires]。
   - idempotency_key="{{request_id}}"（V1 write 幂等键声明位）。
   - args_schema：properties 十键（契约九键 + request_id 可选 · 偏差 D3）· required=[thread_id, name, instruction, schedule_kind] 逐字不动 · additionalProperties=false。
   - output_fields=[schedule_id, next_fire_at, status, humanized_display] · output_schema=JSONPath 词表（偏差 D2：required=["$.schedule_id","$.next_fire_at","$.status"]）。
   - reversible=true · execution_type=instant · max_reversal_latency=0 · requires_stop_support=false（承 ops.write.v1.yaml 字段族）。
   - adapter 冒号串 `local_fn:app.ops.schedule.service:create_schedule_from_capability`（偏差 D1：契约嵌套 map 形态 → loader 白名单字符串形态）。
2. **loader 白名单扩列**（`app/ops/capability/manifest.py`）：`_PREFIX_TO_MODULE` 加第三前缀 `local_fn:app.ops.schedule.service:` → `app.ops.schedule.service`（importlib 运行期解析 · attr isidentifier 非下划线 · 最小改动）。
3. **adapter**（`app/ops/schedule/service.py` 新文件 · `create_schedule_from_capability(payload, *, ctx)` · 承 defaults.py ops_write_run_note 先例）：
   - tenant_id / user_id **只取 ctx**（与 Principal 同源 · 禁取模型产出）：缺 tenant_id → PermissionError(tenant_scope_missing) fail-closed；缺 user_id（委派 off 模式）→ fail-closed 不落笔；user_id str → uuid.UUID 转换（OpsSchedule.user_id UUID(as_uuid=True)）。
   - 幂等键：args.request_id 缺省回退 ctx `f"{run_id}:{subtask_id}"`（偏差 D3 · 两者皆无 → ValueError 不落笔）；claim(capability_id+tenant_id+key) → duplicate 直返首执对账载荷；in_flight → RuntimeError；失败 release（可安全重试）；成功 acomplete（回执 id 由 gateway 落完回执后补上）。
   - 执行直调 `store.create_schedule`（kw-only · 与 REST 同校验路径）：词表外 kind / interval<300 / run_at 非未来 / 双上限 20/200 / 非 thread_owner → ScheduleValidationError 422 文案**透传不改写**（15 §2.4-3 · Agent 把 detail 原文转述给用户）。
   - run_at 字符串 → aware datetime 解析；timezone 透传 store（默认 Asia/Shanghai）。
   - approval_id 从 ctx 串链（A4 审计 · 与 span approval_id 同源）；输出含 output_fields 四键 + idempotency_key + receipt dict + duplicated 标记（gateway 回执面消费）。
   - DB IO 延迟 import（store/idempotency 在函数内 · 能力面顶层零 DB 依赖 · importlib 解析白名单可静态过）。
4. **catalog 可见性**（`app/ops/strategy/config.py`）：supervisor allowlist 9→10 追加 `"ops.schedule.create"`（`CAPABILITY_ALLOWLIST_BY_KEY["supervisor"]` 末位追加 · 既有九枚不动）。
5. **W1 HITL**（零新码 · 既有闸链消费 manifest）：side_effect=write 无批准 → 编排层 tool_exec_node blocked=capability_write_hitl_required + write_intent（snapshot_fields 九键投影）→ _persist_hitl → interrupt；批准注入 `_host_policy.allow_write` + `ctx.approval_id` 重派执行；拒绝 → hitl_rejected 零写。卡题「创建定时任务 = 承诺未来 LLM 花费」由既有 HitlApprovalCard 渲染（web 零改动 · freeze 帧 hitl.waiting 不变）。
6. **测试**（真 PG postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五字符 `p3t2b` 前缀 · CI 终裁 · `tests/test_p3_t2b_create_schedule_capability.py`）：
   - manifest 校验链（V1-V13 锚）：加载成功 + id/kind/tenant_scoped(V13)/hitl.required(V2)/idempotency_key(V1) 逐字段断言 + when_to_use/when_not_to_use 逐字断言（catalog 引导语）。
   - adapter 执行（承 stage W E2E 体例 · _observe_graph_factory(InMemorySaver)）：HITL 拒绝路径（无批准 → blocked + hitl_required + 零行落库）· HITL 通过路径（批准 → 真行落库 · output 四键 + humanized_display + approval_id 串链）。
   - 双上限 422 文案透传断言（per-user 20 · per-tenant 200 · 逐字 §1.8 词表）；词表外 kind 422 透传。
   - 幂等重放：同 request_id 二次调用 → duplicated=true 零新行。
   - allowlist 计数断言：supervisor 候选集含 ops.schedule.create 且长度 9→10。
   - 委派层用例 monkeypatch.delenv（三键 LG_RAG_DELEGATION_TOKEN_* · 承 stage W 体例）。
7. **图谱**：`docs/_tech_graph/l1/01_modules.md` capability 行备注（ops.schedule.create 条目 + adapter 白名单第三前缀）+ schedule 行 deps 补 capability.idempotency（adapter 延迟 import 新边登记）+ HG-GRAPH-MODULES 签收行（承 T2 :143 先例）。

## 非范围

- 不碰 worker/点火循环/启动补链/`OPS_SCHEDULE_ENABLED` 总闸（T3 并行波）。
- 不碰 REST 面（T2 已交付 · 本波只复用 store）。
- 不碰 web（HitlApprovalCard 既有渲染零改动）。
- 不碰 runs/events 端点（T4 已合）· 不碰 scripts/ · skill_registry/ · lg_rag/ 本体（编排层闸链零改动）。

## 失败路径

- 词表外 schedule_kind / interval<300 / run_at 非未来 / time_of_day 非法 → store 422 文案透传（零写）。
- per-user active ≥20 / per-tenant 全量 ≥200 → 422 逐字文案透传（零写）。
- thread 存在且非调用者所有 → 422 逐字文案透传（零写 · R6）；thread 不存在 → 允许（fire 时 worker 自建）。
- HITL 未批准 → blocked + 零写；用户拒绝 → hitl_rejected 零写。
- 同幂等键重放 → duplicated=true 返回首执对账载荷（零新写）；in_flight → RuntimeError（不落笔）。
- ctx 缺 tenant_id / user_id → fail-closed（不落笔 · 非模型产出谓词）。
- 回退 = revert 本波 PR（manifest 为 EXTRA_MANIFESTS 显式加载面 · 默认面零 diff · 删文件即回滚）。
- 并行 agent 撞 registry.yaml / 01_modules.md 同区冲突 → 保留双方 entry 手动解，冲突块如实登记。

## 验收标准

- [x] manifest 加载成功且 V1/V2/V13 逐字段断言有锚 → test_manifest_fields_pinned（idempotency_key/hitl_required/tenant_scoped + 字段族钉死）
- [x] catalog 引导语 when_to_use/when_not_to_use 逐字断言有锚 → test_manifest_fields_pinned（spec.when_to_use/when_not_to_use 逐字）
- [x] HITL 拒绝路径 → test_hitl_rejected_settles_without_write（闸拦 blocked + hitl_required + 零行落库锚）
- [x] HITL 通过路径 → test_hitl_approve_resume_real_write（真行落库 tenant/user/thread/排期字段 + output 四键 + approval_id 串链锚）
- [x] 双上限 422 逐字透传 → test_adapter_422_dual_quota_passthrough；词表外 kind → test_adapter_422_kind_vocabulary_passthrough；interval<300 → test_adapter_422_interval_passthrough
- [x] 幂等重放 duplicated=true 零新行 → test_adapter_idempotent_replay_no_double_write；回退键 {run_id}:{subtask_id} 重放不双写 → test_adapter_request_id_fallback_run_subtask
- [x] allowlist 计数 9→10 有锚 → test_allowlist_supervisor_9_to_10（+test_capability_supervisor_smoke_assertions/test_strategy_env_extra_candidates 钉演进）
- [x] 委派层 delenv fail-closed → test_delegation_off_failclosed_no_user_id（ENV_MODE=off 缺 user_id 谓词零落笔锚）
- [x] `pytest tests` 目标测试绿（14/14 · 真 PG opsdesk_test）；全量净树 2382 passed, 1 skipped EXIT=0（提交后闸测试全自解 · CI 终裁见 invoke_40）
- [x] `ruff check app tests` 绿（All checks passed）
- [x] 01_modules.md capability 行备注 + schedule 行 deps 补 capability.idempotency + HG-GRAPH-MODULES 签收行已回写

### 自检结论

PASS（2026-11-16 close）。PR Cyning12/ops-desk-api#425 CI 四 job 全绿（check /
import-linter / lint-wiki-delta / pytest 2m37s · exact head e99842a0）· squash merge
57e0c727。14 用例真 PG 全绿；rebase 3683b8df 上面全量净树 2405 passed, 1 skipped
EXIT=0（脏树期 9 红=6 钉演进已修+3 净树门提交后自解，承 p3-t4 台账口径）；ruff 绿；
spec-wave task lint PASS（W3 回填后消除）· verify PASS（三人工闸 approved）。
偏差 D1（adapter 冒号串）/D2（output_schema JSONPath required 三键）/D3（request_id
可选+回退键）+ 限制 L1-L3 已登记实现备忘；钉演进两件（smoke/env_candidates 9→10）
承 P2a-T1/T2 先例已入 registry allowed_tree_files。过程：PR #425 事件派发异常
（opened/reopened/两 push 未派发 · 同期他波正常 → #425 特异性偶发）两轮 rebase
解冲突（p3-t5/p3-t3 先后合入 · 追加型双侧全保留）后派发恢复。

## 必读列表

- 设计真源：`../ops-desk-workspace/docs/01-scope/03-general-agent/14-p3-schedule-taskcard-design.md` 终稿（R1-R23 · T2b 行 :348）
- 契约真源：`../ops-desk-workspace/docs/01-scope/03-general-agent/15-p3-contracts.md`（commit 62af6ea · §2 create_schedule capability 契约 · §1.8 双上限与 422 文案词表 · §7.3 幂等装配）
- 先例：`app/ops/capability/manifests/ops.write.v1.yaml` · `app/ops/capability/defaults.py`（ops_write_run_note :185）· `app/ops/schedule/store.py`（create_schedule :271）· `tests/test_stage_w_write_expand.py`（E2E 体例）
- T2 体例：`docs/tasks/done/task_p3_t2_schedule_ddl_rest.md` · registry `docs/harness/audit_gates/registry.yaml`

## 思考轮

| 轮 | 结论 | early_stop |
|----|------|-----------|
| R0 | 范围对账（委派书 vs 14 终稿 R1-R23 / 15 契约 §2）done | false |
| R1 | 失败路径推演（§2.4 + 422 透传 + HITL 零写 + 幂等）done | false |
| R2 | 非范围边界（T3 worker / REST 面 / web / T4 切面）done | false |
| R3 | 关键决策记录（D1 adapter 冒号串 / D2 output_schema 词表 / D3 request_id 回退键 / service 延迟 import 新边）done | false |
| R4 | 体例对账（T2 模板/registry/invokes/审查文/图谱登记）done | false |
| R5 | 收尾复核（验收 checklist 全锚定）done | false |

actual_last_round: R5

### R0 · 范围对账

委派书与 15 §2 逐条对照：manifest 字段族（§2.1 逐字）· 加载放行纪律（§2.2 EXTRA_MANIFESTS 显式加载 + ALLOW_WRITE_TAGS=schedule 只豁免 deny_write · deny_high_risk 永不豁免）· W1 HITL 卡题钉字（§2.3）· 执行语义（§2.4 直调 store + 幂等 + 422 透传 + 不发 run）。委派书内联面（五步法先例 · 双上限 20/200 · interval≥300 · 归属=调用者 · allowlist 9→10 · 图谱登记）全部锚定。

### R1 · 失败路径推演

见「失败路径」节。新增推演：HITL 批准后 graph resume 重派 → 同 subtask_id/run_id 重放 → 回退幂等键 f"{run_id}:{subtask_id}" 命中 duplicate（不双写）；批准注入 _host_policy.allow_write 只对本次调用有效（policy.write_allowed 读 _host_policy · gateway.py 先例）；user_id 在委派 off 模式 ctx 不注入 → fail-closed（生产 .env LG_RAG_DELEGATION_TOKEN_MODE=enforce 委派常开 · 归属谓词永取 ctx 非模型产出）。

### R2 · 非范围边界

T3 切面=不建 worker/tick/补链/OPS_SCHEDULE_ENABLED；REST 面=T2 已交付只复用 store；web 切面=HitlApprovalCard 既有渲染零改动；T4 已合不碰 runs/events。编排层 tool_exec_node 闸链零改动（既有 HITL 消费 manifest 声明）。scripts/skill_registry 零触。

### R3 · 关键决策记录

- **D1 adapter 冒号串**：契约 §2.1 写嵌套 map `adapter: {local_fn: app.ops.schedule.service.create_schedule_from_capability}`，loader 只收字符串白名单前缀（_resolve_local_fn_adapter）→ manifest 落 `adapter: local_fn:app.ops.schedule.service:create_schedule_from_capability` + _PREFIX_TO_MODULE 加第三前缀（最小改动 · importlib 运行期解析 · 白名单不放开任意 import）。
- **D2 output_schema 词表**：契约写 JSON-schema 风（type/properties/required/additionalProperties），V10 只收 {required:[$-paths], min_items, empty_is_suspicious, nullable} 未知键整文件拒 → 落 `required: ["$.schedule_id","$.next_fire_at","$.status"]`（语义等价 · output_fields 四键逐字不动）。
- **D3 request_id 可选 + 回退键**：契约 required=[thread_id, name, instruction, schedule_kind] 逐字不动；additionalProperties=false 要求 request_id 须声明 → 增 request_id 可选 property；adapter 取 args.request_id 缺省回退 ctx f"{run_id}:{subtask_id}"（HITL resume 重放同键不双写）；两者皆无 → ValueError 不落笔。
- **service 延迟 import 新边**：schedule/service.py → capability.idempotency（函数内延迟 import · T2 自注「schedule 禁引 capability」为本波必要豁免 · importlinter 无 schedule 契约零违规 · 01_modules schedule 行 deps 如实登记）。
- **归属谓词 fail-closed**：tenant_id/user_id 只取 ctx（与 Principal 同源）；委派 off 模式 ctx 无 user_id → 不落笔（生产 enforce 委派常开）。

### R4 · 体例对账

照 T2 模板：task 档结构/人工闸表/registry entry（base=17337d35 · banned_prefixes=[] 承 T2 先例 · 不碰 alembic 但沿用同纪律）/invokes by-task 四件（10/30/40/50 承 p3-t4 四件先例）/R1 审查文 GO 机读词/spec-wave task lint PASS 为闸 · 仓规条款一遵守（走 20-R1 审查文非 --allow-no-review）。

### R5 · 收尾复核

验收 11 条逐条锚到 tests/test_p3_t2b_create_schedule_capability.py 或文件证据；回退路径=revert PR（EXTRA_MANIFESTS 显式加载面默认零 diff）。

## 实现备忘

### 偏差登记

- **D1（adapter 形态）**：契约 §2.1 嵌套 map → 冒号串白名单形态（loader 约束 · 见 R3-D1）。
- **D2（output_schema 词表）**：契约 JSON-schema 风 → JSONPath required 词表（V10 约束 · 见 R3-D2）。
- **D3（request_id）**：契约 required 四键逐字不动；args_schema 增 request_id 可选 property + adapter 回退键 f"{run_id}:{subtask_id}"（见 R3-D3）。
- **D4（schedule→capability 新边）**：service.py 函数内延迟 import capability.idempotency（T2 自注豁免 · 01_modules 登记）。

### 限制登记

- **L1（委派 off 模式）**：ctx 无 user_id 注入 → capability fail-closed 不可用；生产 .env LG_RAG_DELEGATION_TOKEN_MODE=enforce 委派常开不受影响。
- **L2（DST）**：daily_at 排期算术承 T2 store（v1 不随 DST 校准 · 15 §1.2 钉明）。
- **L3（args 校验词表）**：manifest args_schema 的 minimum/enum/pattern/maxLength/format/default 键在最小校验器下透传不校验（schema_validate.py 只支持 type/properties/required/additionalProperties）；业务不变量全部由 store 422 词表兜底（与 REST 同路径）。

## 测试策略

pytest tests（CI 终裁 · 真 PG opsdesk_test · 五字符 `p3t2b` 前缀）；manifest 校验链 + adapter E2E（HITL 拒绝/通过/重放/双上限/委派 delenv）+ allowlist 计数；ruff check app tests；import-linter 零新 forbidden 出边（service→capability.idempotency 为函数内延迟 import · importlinter 无 schedule 契约 · 01_modules 登记）。

## 修订记录

| 日期 | 修订 |
|------|------|
| 2026-11-16 | 落卡（夜间自动执行波 · 授权 issue #23 m03064/m03283/m03498） |
