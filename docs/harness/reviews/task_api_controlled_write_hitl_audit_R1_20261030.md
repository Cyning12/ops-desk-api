# task_api_controlled_write_hitl 审查（R1 · 20-task-audit）

> **审查对象**：`docs/tasks/active/task_api_controlled_write_hitl.md`（阶段 W · api 受控写 + HITL task 壳 · **HG-TASK-DRAFT approved** 2026-10-30 维护者签收 · 00 代录 · 余三闸 pending）
> **审查帽**：20-task-audit（书面审查 · **未改 task 实质内容** · **未代签任何 human_gate** · 未执行 30）
> **日期**：2026-10-30 · **审查时仓态**：分支 `task/api-controlled-write-hitl`（`git branch --show-current` 核实 ✓ · base `master`）· 工作树净
> **开窗授权**：维护者令（00 转发）：审查帽 R1 审阶段 W task 壳 · 只审不改 · 发现实质问题退回 10
> **上游真值**：`docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md` §8（实读 §8.1–8.4）· workspace `05_post_h_stage_brief_v1_zh.md`（H α 验收 E=span `approval_id` 预留 · 「刻意未做：写能力/HITL」）· workspace `06_stage_t_second_tenant_prep_v0_zh.md`（Fixture 轨 CLOSE · 生产 P 轨另轨 NO-GO）· contracts `api-v1-tenant-readonly-context-draft.md`（F1–F6 freeze 2026-09-18 · 2026-10-30 复核维持）
> **结论**：**PASS**（内容零阻塞 · 六项审查清单全核 · 码面锚点全实证 · lint 复跑 PASS · **minor 1 条**（M1 行为变更类「旧测 grep 影响面」验收项建议补列）· **note 2 条** · 三流程闸 pending 待维护者签 · 不附 30 Prompt）

---

## 结论摘要

| 维度 | 结论 |
|------|------|
| task **内容**可执行 | ✅ **PASS · 零内容阻塞**——范围 W0–W5 与非范围互斥闭合；四闸 blocks 语义闭环；验收可勾可机断；failure_paths 11 条与三条 freeze 红线自洽；思考轮 R0–R3 闭合 early_stop 有据 |
| **流程闸** HG-TASK-DRAFT | `approved`（2026-10-30 维护者签收 · 00 代录 · blocks 20-R1 已解锁 → 本审查合法启动） |
| **流程闸** HG-AUDIT-R1 | `pending`（本审查文落盘即其前置交付 · 人签后方 approved · blocks 30） |
| **流程闸** HG-GRAPH-MODULES | `pending`（`graph_change_layer=G-L1` 薄增量不新增一级模块 · 与图谱实态一致 · blocks 30） |
| **流程闸** HG-STAGE-W-DESIGN | `pending`（承载 §8.1 进入条件「审批与令牌设计签收」· 新增必要且口径清晰 · blocks 30） |
| lint 复跑 | `npx spec-wave task lint --file docs/tasks/active/task_api_controlled_write_hitl.md` → **LINT: PASS** exit 0（2026-10-30 本帽复跑 ✓ 与 task 自检结论一致） |
| draft 洁净度 | ✓ 本分支仅 task 文档 + invoke 落盘（git log 两笔 docs commit）· `app/` 零改动 · 无提前实施 |

---

## 审查清单逐项核对

### 1. 范围 / 非范围 ✅

- **范围守住「受控写 + HITL api 最小竖切」**：W0 Policy 审批闸接通 → W1 decide/resume 接合 auto-resume → W2 tenant_scope 下推一致 → W3 观测审计（`approval_id` 落 span）→ W4 首条极窄写能力端到端 → W5 图谱薄备注。与 §8.1 W 行定义「首条极窄写能力；结构化 Intent + confirmation + Policy；幂等与审计」逐条对应，无越界项。
- **非范围完整**（委托令 7 项逐项在表）：web UI ✓（审批台另 task · freeze 仅保持消费语义）· 阶段 P 平台项 ✓（服务化 Registry / 本体治理 / 多 Agent 委派）· 改 SSE freeze ✓（`lg-rag-sse-v1` 事件表 / keepalive / 410 叙事）· 生产 P 轨数据 ✓（另轨 workspace `07` §4）· 自动改码/提 PR/合并 ✓（§8.3 Coding Agent 线非本产品）· OA 签名面 ✓ · iOS ✓。
- **刻意不做**与上游一致：§8.2「写不能早于租户封闭」前提=T 已 CLOSE（PR #142 `f048c57` ∈ master · web PR #76）已在背景节核对引述；H α 简报「刻意未做：写能力/HITL、改 SSE freeze」与本 task 衔接正确。

### 2. 人工闸表 ✅

- **4 闸 blocks 语义闭环**：HG-TASK-DRAFT（approved）blocks 20-R1+30 → 已解锁本审查；HG-AUDIT-R1 / HG-GRAPH-MODULES / HG-STAGE-W-DESIGN 三闸 pending 均 blocks 30 → 30 开工须三闸齐，与验收标准首条「四闸均 approved 后方可勾选码项」一致，无「闸外开工」缝隙。
- **HG-STAGE-W-DESIGN 必要性成立**：§8.1 W 进入条件明载「T 跨租户负样本门禁达标；**审批与令牌设计签收**」——前者已满足，后者仓内无现成闸承载，新增专属闸是唯一直接载体（R1 思考轮推导路径与之一致）。**口径清晰**：闸说明钉死三要素——首条极窄写能力选型 + 结构化 Intent/confirmation 载荷 + 审批令牌（审批者身份/时效/范围），与 §8.1「结构化 Intent + confirmation」对得上，不空泛。
- 20 帽纪律：HG-TASK-DRAFT 已 approved 故本 R1 合法；本帽不代签余三闸。

### 3. 验收可勾性 + failure_paths 与 freeze 自洽 ✅

- **验收 11 条均可勾**：W0–W4 各有负样本/全链/观测断言锚点（「单测绿」「逐条一致」「fixture 轨可演示 + 自动化断言」）；freeze 回归两条（`hitl-browser-decide-v1` decide 400/404/409/422 + pending 字段族；SSE 事件表零 diff）均可对命令输出/契约对照机断；`graph-compile.sh` 绿 + 不新增一级模块可机断；lint PASS 可机断。闸前置条款（首条）防「先勾码项后补签」。
- **failure_paths 11 条**（实数 11 行 ✓ 无计数瑕疵）与三条 freeze 红线逐条自洽：
  - `hitl-browser-decide-v1`：decide 未知 resume_mode→400 / 重复已决→409 / 未知·跨用户→404（表内第 7 行）与 web freeze 消费语义一致；
  - F1–F6：跨租户写对外 404 不泄漏存在性（第 5 行 · F4）· 头/session 不一致 403（第 6 行 · F1=C）· fail-closed 方向与 freeze 表一致；
  - `lg-rag-sse-v1`：误改 event_type/新增事件 → 审查拒收（第 10 行）· 补偿扫描重建不依赖进程内存态（第 8 行）· SSE 零改契约（钉死契约第 7 条）互锁；
  - resume 单路径红线（第 4 行）与 `auto_resume.py` docstring 钉死一致。
  - 每条均含处置/重试/用户可见三列，无「只列风险不给出口」项。

### 4. 思考轮 R0–R5 完整性 + early_stop at R3 ✅

- 控制表表头（轮/结论/early_stop/reason/residual_risks）齐 · `actual_last_round=R3` 行在 · R4/R5 标注「未开 · early_stop」不空槽 · R0–R3 各轮有独立小节展开。
- **early_stop at R3 依据成立**：reason 写明「问题面已框死（契约锚点齐）；实现细节（intent 载荷字段、令牌时效）属 HG-STAGE-W-DESIGN 与 30 实扫，非 10 轮次能钉」——与锚点实证（本审查 §5 全中）互证：30 性质确为「接线 + 负样本」而非新建子系统，继续 R4/R5 不产生 10 层新信息。无跳跃。
- **residual_risks 处置合理**：「intent 载荷→迁移面膨胀」挂账 HG-STAGE-W-DESIGN（blocks 30 · 设计签收时必触）+ 30 实扫后回填——有闸承接非空挂；「设计签收周期长则 W 顺延」为进度风险如实定性。

### 5. 码面实态一致性（锚点抽验 · 只读）✅

| 锚点 | 实证结果 |
|------|----------|
| hitl-auto-resume（PR #223） | ✓ `git log` 实证 `Merge pull request #223`（acceptance/20261010-hitl-consumption-loop）已合；后续 claim-race PR #224/#225 亦已合，与 task「auto-resume 已合」一致 |
| `router._execute_decided_resume` 单路径 | ✓ `app/ops/hitl/router.py:425` 定义在；`auto_resume.py:225-227` 惰性 import 同源调用；docstring :14/:36 钉死「禁 HTTP 自调 · 禁第二条实现」；resume 异步化面 :476/:493/:499 同源复用——单路径主张成立 |
| `gateway.py:1318` approval_id span | ✓ 逐字命中 `:1318 "approval_id": (ctx or {}).get("approval_id") if ctx else None` · 注释「写路径 HITL 预留（本波可空）」· 与 H α 验收 E 预留口径一致（预留未启用 → W 落值） |
| tenant_scope 既有下推 | ✓ `app/ops/tenant_context.py` 在 · `alembic/versions/20260918_tenant_readonly.py` 在（`f048c57` ∈ master）；F1–F6 freeze 表逐条与 task 钉死契约第 5 条一致 |
| `types.py` 写判定词表 | ✓ `SIDE_EFFECTS` :23 / `WRITE_SIDE_EFFECTS={write,irreversible}` :24 |
| `registry.py:120-121` deny_write | ✓ deny_write 判序块实证在 :119-123 窗（deny_high_risk 在前永不豁免 · `allow_write_tags_any` 只豁免本层）；行窗与 task 锚点 :120-121 吻合 |
| decide 两步钉死 / resume_mode 白名单 | ✓ `hitl/router.py:180` decide 端点在 · docstring「两步钉死 · T2 起可配置」· 白名单手工校验 :203-207（未知值 400 · decision 非法 422 既有形态）；⚠ task 锚点表写「router.py:184 白名单」实为 :203（行号漂移 · 见 N1） |
| `OPS_HITL_AUTO_RESUME` 三态 | ✓ `auto_resume.py:49-61` env ∈ {manual 默认 · auto} 非法回退 manual（fail-closed）· FOR UPDATE SKIP LOCKED 认领 :17 · 补偿扫描 :53——与 task「manual=现状零 diff」口径一致 |
| 图谱锚点（profile `graph_modules_path`） | ✓ `docs/_tech_graph/l1/01_modules.md` `capability`（:34）与 `hitl`（:39）一级模块条目均在，task W5「薄备注 · 不新增一级模块」落点真实可达 |

### 6. lint 复跑 ✅

`npx spec-wave task lint --file docs/tasks/active/task_api_controlled_write_hitl.md` → **LINT: PASS · task_api_controlled_write_hitl.md**（exit 0 · 2026-10-30 本帽复跑 · 与 task 自检结论表记录一致）。

---

## minor（建议 10-task 补列 · 不阻本 R1 结论）

| # | 项 | 依据与建议 |
|---|----|-----------|
| M1 | **行为变更类「旧测 grep 影响面」验收项缺失**：W0 给写类 capability 新挂审批闸属策略门语义变更（此前 policy 放行即可执行 → 此后未批准即挂起），按 20-task-audit K7 checklist 应含「旧测 grep 影响面」项。现验收仅有「既有 capability/hitl/tenant 回归绿」总括条款。实测影响面温和（write 能力现状 default deny_write 裁剪 · testing.write.echo 仅显式 opt-in），但 `tests/test_capability_testing_write.py` / `test_capability_idempotency.py` / `test_capability_delegation.py` 等触及 write 语义面，30 需明确哪些旧测预期改变、哪些必须原样绿 | 建议 10-task 在验收标准补一条：「旧测 grep 影响面：grep 既有 write/irreversible 调用与断言面（capability/hitl/delegation/idempotency 各测试文件）逐条标注 30 处理方式（原样绿 / 预期改 / 新增负样本）」；维护者签 HG-AUDIT-R1 前补列或书面认可总括回归条款兜底 |

## note（不阻 · 供维护者/30 参考）

| # | 项 |
|---|----|
| N1 | 现状锚点表「resume_mode 白名单 router.py:184」实际白名单校验在 `router.py:203-207`（:184 为 docstring 提及）——行号漂移 · 语义锚点正确 |
| N2 | task `required_invoke_hats=10,20,30,40` 含 20 → 本帽 invoke 快照已随本审查落盘 `docs/harness/invokes/by-task/api-controlled-write-hitl/invoke_20261030_20_task_audit.md`（纪律项 · 非内容问题） |

## 阻塞项（blocker）

**无内容阻塞。**

## 回填清单

- M1（minor · 退回 10-task 补列一条验收项，或由维护者书面认可兜底）；N1 可随 10 补列顺手修正（非强制）。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论（本文件）
- [ ] 处置 M1：10-task 补列「旧测 grep 影响面」验收项，或书面认可既有回归条款兜底
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] 在 task 人工闸表将 HG-GRAPH-MODULES 改为 approved（维护者 · 日期 · graph_change_layer=G-L1 薄增量口径确认）
- [ ] 在 task 人工闸表将 HG-STAGE-W-DESIGN 改为 approved（维护者 · 日期 · 首条写能力选型 + Intent/confirmation 载荷 + 审批令牌设计签收后）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

**是否建议维护者签余下三闸**：建议签——本 R1 内容零阻塞；HG-AUDIT-R1 与 HG-GRAPH-MODULES 可在 M1 补列后随即签；HG-STAGE-W-DESIGN 为设计签收闸，按 §8.1 进入条件独立推进（审批与令牌设计签收后签），三者无先后互锁。

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-30 | 20-task-audit R1 落盘：PASS（内容零阻塞 · minor M1 · note N1/N2）· 锚点 9 项全实证 · lint 复跑 PASS · 三流程闸 pending · 不附 30 Prompt |
