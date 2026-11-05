# SPEC：阶段 W 扩写能力（stage-w-write-expand · 受控写闸链上接入第二条真实窄写能力）（v0）

> **层级**：L1 波次 SPEC（阶段 W 的扩切片 · 承 api-controlled-write-hitl 竖切收口）
> **状态**：`v0-signed`（20-spec-audit R1 审毕 · HG-SPEC-SIGNOFF=**approved**（2026-11-05 维护者人签 · B1 已修订）· 可拆 task）
> **上游**：[`task_api_controlled_write_hitl`](../tasks/done/task_api_controlled_write_hitl.md)（CLOSE · PR #303 merge `09f97f4`）+ 三个接合缝 fix（PR #307 join-gap · PR #313/#314 tenant-fix · PR #319 decide-owner-fallback · issue #315 CLOSE）· [`docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md`](../discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md) §8.1 阶段序 H→T→W→P
> **立项令**：维护者 2026-11-05 在「下一 task 方向」决策中选「阶段 W 扩写能力」（active 为空时的排期裁定）
> **下游**：20-spec-audit → HG-SPEC-SIGNOFF（人签 · 00 代录）→ 00 出 task（新设 `HG-STAGE-W-EXPAND-DESIGN` 选型闸 · 类比 HG-STAGE-W-DESIGN 先例）→ 20-task-audit → HG-AUDIT-R1 → 30 → 40 → PR+CI 绿+merge → 图谱回写 → CLOSE
> **Open Folder（实现）**：`ops-desk-api/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `stage-w-write-expand` |
| **invoke_slug** | `stage-w-write-expand`（SPEC 与 task 阶段共用） |
| **test_strategy** | `required` |
| **test_strategy_note** | pytest 单测/集成为主（审批闸负样本 + tenant_scope 下推负样本 + 幂等重放 + 审计串链断言 + 反回归对拍）；**不连真外网 / 不写生产数据**；若 Q1 裁定外部写（S2），契约测用 canned adapter，live 面留 40 复跑；不开新 freeze 面 |
| **默认分支** | task 阶段 `task/stage-w-write-expand`（自 `master` 分出；**禁止 master/main 直改**）；本 SPEC 起草于 `spec/stage-w-write-expand` |
| **graph_change_layer** | `G-L1` 行备注预估（capability 行备注「阶段 W 扩写」；不新增一级模块；30 实扫为准） |
| **freeze_id** | 无（SSE `lg-rag-sse-v1` 事件表零改 · web `hitl-browser-decide-v1` 消费语义稳定 · 租户契约 F1–F6 不破；倾向零 alembic——落笔目标若须新表 → Q1/Q3 裁定并在 task 修订表回填） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | **approved** | 维护者 2026-11-05 人签（lead 代行，依据 issue #323 的 20-spec-audit R1 审查 PR #324「fail·仅 B1」+ 本 commit Q4 豁免口径修订 diff 轻量确认；00 代录）；Q1 选型留 HG-STAGE-W-EXPAND-DESIGN task 闸 |

---

## 1. 背景与目标

### 现状（2026-11-05 实态）

阶段 W api 侧已收口：写类 capability 走 Policy 写闸 + HITL 审批闸（无审批 fail-closed 挂起）→ decide/resume 接合 auto-resume 单路径 → tenant_scope 下推一致 → span `approval_id` 审计串链（PR #303 + fix #307/#313/#319 全合入 master）。

但受控写闸链上**只有一条语义 mock 写能力** `testing.write.echo`（[`testing.v1.yaml`](../../app/ops/capability/manifests/testing.v1.yaml)）：罐头纯函数零 IO，且**不进默认加载面**（须经 `OPS_CAPABILITY_EXTRA_MANIFESTS` 显式加载 + `OPS_CAPABILITY_ALLOW_WRITE_TAGS=testing` 放行 + `tenant_scoped: false`）。生产路径上**没有任何真实写能力**经审批闸——闸链建成了，但没有真实业务流量走它。

### 一句话目标

把**第二条、真实、极窄、单租户内无害**的写能力端到端接入既有受控写闸链（intent → Policy → HITL 审批 → resume 单路径 → 执行 → 审计），使阶段 W 从「闸链 + mock 演示」升级为「闸链 + 一条真实业务写竖切」。

### 设计纪律（签收时锁死 · 反回归钉死）

1. **闸链零新建**：复用 PR #303 落地的编排层审批闸（`app/ops/lg_rag/multi/nodes.py` `tool_exec_node`），不新建第二道闸、不改 `blocked_by=capability_write_hitl_required` 语义。
2. **判序零 diff**：`registry.py::_match_filter` deny 判序（`deny_high_risk` 在 `deny_write` 前）与 `policy.py` 闸序段逐字节零 diff；`deny_high_risk` 永不豁免。
3. **resume 单路径**：复用 `router._execute_decided_resume`；禁第二条恢复实现 / HTTP 自调。
4. **租户封闭**：新写能力 `tenant_scoped: true`（与 testing.write.echo 的 false 形成对照），写 intent / 审批 / 执行全链带 tenant_id；跨租户写 fail-closed 对外 404（F1–F6 存续）。
5. **显式打开纪律**：新能力默认**不进**默认加载面（沿 testing.v1.yaml 三层「显式打开」先例：manifest env 显式加载 + 写 tag 显式放行），默认零 diff。
6. **幂等**：写 manifest 顶层 `idempotency_key` 声明位强制（loader V1 纪律），重放不双写。

---

## 2. 范围（D 块展开）

### D1 · 第二条窄写能力选型与接入（必做 · 选型挂 Q1 + HG-STAGE-W-EXPAND-DESIGN）

- 按 Q1 裁定的一条真实写能力，端到端经既有闸链：`side_effect: write`（**先 write 级可逆，不碰 irreversible**）→ Policy 写闸 → HITL 审批闸挂起 → decide(approved) → resume 单路径续跑 → 执行 → span `approval_id` 串链审计。
- manifest 字段族对齐 builtin.v1.yaml/testing.v1.yaml 范式；`hitl.required: true` 显式声明；`tags` 含独立写 tag（不放行 `testing` tag 复用）。
- 能力可见性经 `∩ visible`（strategy builder）与 allowlist 全链照旧——新能力可达 ≠ 默认可达。

### D2 · 租户下推与负样本（必做）

- 新能力 `tenant_scoped: true`；写路径 A 会话写 B 资源 → 对外 404 / 头 session 不一致 403（复用阶段 T F1–F6 与 PR #313 消费守卫）。
- 负样本断言：无审批直接执行 fail-closed 挂起；env 未显式开启时能力不可见；幂等重放不双写。

### D3 · 审计与观测（必做）

- 既有 `capability_write_approval_consumed` 台账 + span `approval_id` 串链对新能力原样生效（只验不建）；若 30 实扫发现落值缺口 → 修订表回填，不静默扩面。

### D4 · 图谱与文档回写（必做）

- `docs/_tech_graph/l1/01_modules.md` capability 行一句备注（G-L1）；不新增一级模块；HG-GRAPH-MODULES task 阶段随 30 回写。

---

## 3. 非范围

- ❌ **第三条及更多写能力**（本波只扩一条；批量接入属阶段 P/本体治理）
- ❌ **irreversible 级写**（先 write 级可逆；不可逆写另案）
- ❌ **自动改码 / 自动提 PR / 自动合并**（§8.3 显式排除，血统不变）
- ❌ **web UI / 审批台前端**（web 面已 CLOSE；`hitl-browser-decide-v1` 消费语义禁改）
- ❌ **SSE 事件表改动**（`lg-rag-sse-v1` freeze 不破；复用 `hitl.waiting`/`done{status}` 叙事）
- ❌ **闸链改造**：HITL 表结构、decide/resume 状态机、auto-resume 触发器/补偿扫描一行不动（jsonb 载荷增键若必需 → 修订表回填）
- ❌ **OA 签名面 / iOS / 阶段 P 平台项**
- ❌ **生产 P 轨数据**（Fixture/测试面 only）

---

## 4. 开放裁定（必答题 · 留 20-spec-audit 复核与 HG-STAGE-W-EXPAND-DESIGN 选型签收）

### Q1 · 第二条写能力选型（**核心裁定** · 维护者拍板）

| 方案 | 做法 | 收益 | 代价 / 风险 |
|---|---|---|---|
| **S1 · 仓内落笔型写**（如 run 备注/审计便签写入既有 DB 面） | local_fn adapter，落笔既有表/jsonb 面（若须新表 → 修订表回填 alembic 义务） | 零外网零外部凭据；爆炸半径最小；fixture 轨全可控 | 业务价值偏「演示升级」；落笔目标表需选型 |
| **S2 · issue 备注写**（经 `http_generic` adapter 调外部 Forge API） | 真实业务价值最高（企业只读助手的自然下一步） | 真实用户价值；验证租户下推的真实外网语义 | 需外部 token/env 管理面；外网失败路径多（FP 增项）；契约测需 canned 替身 |
| **S3 · sync 触发写**（复用 `app/ops/admin/service.py::process_sync_payload` 面） | 仓内既有唯一真实写面接 capability | 零新增外部依赖 | 属 sync 产品域，与 capability 面接合的边界需另评；可能扭曲 sync 面职责 |

> 10-spec **建议序**：S1 先行（把闸链从 mock 带到真实落笔、风险最低），S2 作下一波独立 SPEC（业务价值最大但 env/凭据面需单独设计）。最终由维护者在 HG-STAGE-W-EXPAND-DESIGN 签收裁定。

### Q2 · 加载面形态

| 方案 | 做法 | 裁决建议 |
|---|---|---|
| **S1 · env 显式 opt-in**（沿 testing.v1.yaml 纪律：`OPS_CAPABILITY_EXTRA_MANIFESTS` 显式加载 + 写 tag 显式放行） | 默认零 diff；运维显式打开 | **建议裁定**（纪律连续性优先） |
| S2 · 直接进 builtin.v1.yaml 默认面 | 开箱即用 | 默认面即写面，与「写显式打开」精神相悖 |

### Q3 · 幂等键与落笔目标的形态

- 顶层 `idempotency_key` 声明位强制（loader V1）；若 Q1=S1 且须新表 → task 修订表回填零/非零 alembic 义务与迁移面；若 Q1=S2 → http 块键合法（V7 禁 local_fn 声明 http 块纪律自动满足）。

### Q4 · tenant_scoped 强制

- 新写能力一律 `tenant_scoped: true`（testing.write.echo 的 false 是 mock 特例，不复制）；30 加加载期断言「除 mock 特例清单（`testing.write.echo`，以 `testing`/`mock` tag 为谓词）外，写能力 `tenant_scoped` 必须为 true；特例清单不扩容」。

---

## 5. failure_paths

| # | 路径 | 裁定 |
|---|---|---|
| FP-1 | 无审批直接执行新写能力 | fail-closed 挂起 pending（既有闸链原样生效）· 负样本断言 |
| FP-2 | 跨租户写（A 写 B）/ 头 session 不一致 | 对外 404 / 403（F1–F6 + PR #313 消费守卫原样） |
| FP-3 | env 未显式开启 | 能力不可见（默认加载面零 diff 断言） |
| FP-4 | 幂等键重放 | 不双写（幂等键强制度照旧） |
| FP-5 | 审批过期（TTL）后执行 | 读时判过期不消费 → 回到挂起态（PR #307 W-fix-1 语义原样） |
| FP-6（S2 时启用） | 外部 API 失败 / 超时 / 凭据缺失 | 执行失败可观测（span+事件）· 审批记录不丢 · 按幂等键可重试；**审批 ≠ 执行成功**语义在审计上显式区分 |
| FP-7 | 静默改闸链 / 判序 / SSE 事件表 / web 契约 | 20/40 审查拒收退回（红线） |

---

## 6. 验收标准（可机验）

1. **A1 端到端竖切**：选定写能力 fixture 轨可达「plans 含写 tool → hitl.waiting → pending → decide(approved) → resume（含 auto 模式）→ 执行落笔 → done{completed}」全链自动化断言。
2. **A2 负样本组**：无审批 fail-closed；跨租户 404；头/session 403；env 未开启不可见；幂等重放不双写。
3. **A3 租户下推**：写 intent/审批/执行三处 tenant_id 一致（断言 + M1 式影响面逐条标注）。
4. **A4 审计串链**：span `approval_id` + `capability_write_approval_consumed` 台账对新能力落值；审批决策与执行结果可串链查询。
5. **A5 反回归钉死**：`registry.py::_match_filter` / `policy.py` 闸序段 git diff 为空；PR #303/#307/#313/#319 既有测试原样绿；resume 单路径无第二实现（grep 断言）。
6. **A6 freeze 零破**：SSE 事件表零 diff；`hitl-browser-decide-v1` 400/404/409/422 语义回归绿。
7. **A7 工程面**：`pytest tests` 全绿（CI 为准）；`ruff` 触及路径零新增；`./scripts/graph-compile.sh` EXIT=0；G-L1 备注回写。
8. **A8 lint**：`npx spec-wave task lint` PASS。

---

## 7. 思考轮回填（R0–R5）

- **R0（读人聊/目标）**：维护者 2026-11-05 方向裁定「阶段 W 扩写能力」；磁盘实态实读：W 竖切 + 三 fix CLOSE、active 为空、全仓唯一 write capability = testing.write.echo（mock · opt-in · tenant_scoped=false）。
- **R1（范围/非范围）**：范围 = 一条真实窄写能力接入既有闸链（闸链零新建）；非范围重点 = 不多扩、不碰 irreversible、不做 web/平台项。
- **R2（方案对比）**：Q1 三案（S1 仓内落笔 / S2 issue 备注 / S3 sync 触发）+ Q2 两案 + Q3/Q4 技术裁定建议；核心选型留维护者（HG-STAGE-W-EXPAND-DESIGN）。
- **R3（边界/失败路径）**：FP-1~FP-7 逐条锚既有语义（fail-closed / F1–F6 / TTL 读时过期 / 幂等键）；S2 增 FP-6 外部失败面。
- **R4（验收/可测性）**：A1–A8；pytest 不连外网（S2 canned 替身）；live 留 40。
- **R5（签收就绪）**：Q1 无最终裁定（留人签）→ 本 SPEC 为「可审可签」态；交 20-spec-audit 书面审 → 维护者签 HG-SPEC-SIGNOFF（可同时裁定 Q1 或留 task 闸）→ 00 拆 task。

### 思考轮控制

| 轮 | 状态 | 说明 |
|---|---|---|
| R0 | done | 维护者方向令 + W 收口实态实读 |
| R1 | done | 一条真实窄写能力 + 八条非范围锁定 |
| R2 | done | Q1 三案 + Q2/Q3/Q4；核心选型留人签 |
| R3 | done | FP-1~FP-7 锚既有裁定 |
| R4 | done | A1–A8 + test_strategy |
| R5 | done | 交 20-spec-audit → HG-SPEC-SIGNOFF → 00 拆 task |
| early_stop | no | — |

---

## 8. 关联

- 上游 task：[`task_api_controlled_write_hitl`](../tasks/done/task_api_controlled_write_hitl.md)（CLOSE · PR #303）· fix 链：`task_api_w_join_gap_fix` / `task_api_w_hitl_tenant_fix` / `task_fix_hitl_decide_owner_fallback`
- 上游讨论：[`2026-09-17_interview_gaps_adoption_and_landing_v0.md`](../discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md) §8.1（W 定义「首条极窄写能力」→ 本波扩第二条）
- 代码锚点：`app/ops/capability/types.py`（WRITE_SIDE_EFFECTS）· `registry.py:112-140,120`（deny 判序/写闸）· `gateway.py:1318`（span `approval_id`）· `app/ops/lg_rag/multi/nodes.py`（tool_exec 审批闸 · PR #303）· `app/ops/hitl/{router,auto_resume,resume}.py`（单路径恢复）· `manifests/testing.v1.yaml`（三层显式打开先例）· `app/ops/admin/service.py:50`（S3 候选面）
- freeze 契约：web `../ops-desk-web/src/api/hitl.ts`（hitl-browser-decide-v1）· workspace 租户契约 F1–F6
- 图谱：`docs/_tech_graph/l1/01_modules.md` capability 行

## 修订记录

| 日期 | 版本 | 内容 |
|---|---|---|
| 2026-11-05 | v0 | 10-spec 初稿：R0–R5 全轮；Q1 选型三案留维护者（HG-STAGE-W-EXPAND-DESIGN 先例）；FP-1~FP-7；A1–A8；HG-SPEC-SIGNOFF=pending |
| 2026-11-05 | v0.1 | B1 修订：§4 Q4 加载期断言补 mock 特例豁免口径（testing.write.echo 清单 + testing/mock tag 谓词 · 特例清单不扩容）；HG-SPEC-SIGNOFF 人签 approved（依据 PR #324 R1 审查 + 修订 diff 轻量确认 · 00 代录）|
