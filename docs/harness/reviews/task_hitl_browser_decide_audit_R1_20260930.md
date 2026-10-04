# R1 审查 · task_hitl_browser_decide（帽 20-task-audit）

## 元信息

| 项 | 值 |
|---|---|
| **审查帽** | 20-task-audit（任务书面审查 · 不实现代码 · 不改 task 实质内容） |
| **日期** | 2026-09-30 |
| **审查对象** | `docs/tasks/active/task_hitl_browser_decide.md`（B2 HITL 浏览器决策面 · slug `hitl-browser-decide`） |
| **对照真值** | SPEC `docs/spec/chat-history-hitl-ux/SPEC-chat-history-hitl-ux_v0.md`（signed 2026-09-30 · §2 B2 / §4 Q2·Q5 / §5 FP-3·FP-6 / §6 B2）· SPEC 审查 `docs/harness/reviews/spec_chat_history_hitl_ux_audit_R1_20260930.md`（PASS-WITH-NITS · N1-N4）· 标准 `docs/standards/CODING_BACKEND_L2_v1_zh.md` · 依赖契约 `.importlinter`（`hitl-outbound` :180-203）· 维护者裁定 D1/E1（2026-09-30 · 原话「冲突部分安全推荐方案进行」） |
| **审查方式** | 真值源真读 + 代码锚点逐条核实（read/grep）+ 机跑实证（task lint / lint-wiki-delta / spec-wave verify / git branch） |
| **轮次** | R1（HG-AUDIT-R1 仍 pending · 20 只书面审 · 不代签 human_gate） |

---

## 机跑证据（命令 · 退出码）

| 命令 | 结果 | 退出码 |
|---|---|---|
| `git branch --show-current` | `task/chat-history-hitl-ux` | 0 |
| `npx --yes spec-wave@3.0.1 task lint --file docs/tasks/active/task_hitl_browser_decide.md` | `LINT: PASS · task_hitl_browser_decide.md` | **0** |
| `npx --yes spec-wave@3.0.1 task lint-wiki-delta --target .` | `LINT-WIKI-DELTA: PASS`（scanned 147 · missing 0 · issues 0） | **0** |
| `npx --yes spec-wave@3.0.1 verify --target . --task docs/tasks/active/task_hitl_browser_decide.md` | `VERIFY: BLOCKED · HG-AUDIT-R1 pending`（三闸 pending · 30 不可开工） | **2**（流程闸未签 · 非内容缺陷） |

---

## 核对项表 · 流程闸（与内容分开列）

| # | 核对项 | 证据 | 判定 |
|---|--------|------|------|
| P1 | HG-TASK-DRAFT | task 人工闸表 L39 = `pending` · blocks「20-R1, 30」 | ⏳ pending（维护者尚未扫签） |
| P2 | HG-AUDIT-R1 | task 人工闸表 L40 = `pending` · blocks 30；本 R1 审查文落盘后交维护者人签 | ⏳ pending（20 不代签） |
| P3 | HG-GRAPH-MODULES | task 人工闸表 L41 = `pending` · blocks 30；`graph_change_layer=G-L1` · `graph_delta=docs/_tech_graph/l1/01_modules.md`；实读该文件 L39 已有 `hitl` 行（现载「HMAC 签名面 + 管理员面双鉴权口径」），本 task 为 **行备注** 非新增一级模块 | ⏳ pending（随交付签录） |
| P4 | HG-PILOT-OPSDESK-GLAYER | task 人工闸表 L42 = `n/a`（复用既有 G-L1 模块，不涉物理分层试点新增） | ✅ n/a 恰当 |
| P5 | 分支隔离（禁 master 直改） | 实测 `git branch --show-current` = `task/chat-history-hitl-ux`，与 SPEC §Harness 元信息 L19「默认分支 task/chat-history-hitl-ux · 禁止 master 直改」一致 | ✅ |
| P6 | task lint 机械闸 | `task lint` = **PASS · EXIT=0** | ✅ |
| P7 | 附加机械闸（task 验收 L128） | `task lint-wiki-delta` = **PASS · EXIT=0**（`wiki_delta=n/a` 如实） | ✅ |
| P8 | spec-wave verify | **EXIT=2 · BLOCKED**（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸 pending）· 30 必须拒开工 | ⏳ 属实（非内容缺陷） |
| P9 | invoke 快照（`required_invoke_hats=10,30,40`） | 实测 `docs/harness/invokes/by-task/chat-history-hitl-ux/invoke_20260930_10_chat-history-hitl-ux.md` 已落盘；20 不在 required 集合，按 skill 分工免落盘（reviews 硬闸由本文承接） | ✅ |

---

## 核对项表 · 内容

| # | 核对项 | 证据 | 判定 |
|---|--------|------|------|
| C1 | 范围忠实承接 SPEC §2 B2 三行 | SPEC §2 B2 L75-77：`GET /hitl/pending`（新增 · cookie maintainer · 当前用户可见 pending）· `POST /hitl/requests/{id}/decide`（新增 · `{decision: approved\|rejected}` · 与 callback 同语义）· `resume` 复用零改动；task 范围 P1/P2/P3（L79-81）逐条对齐，P4 为测试件 | ✅ |
| C2 | SPEC §6 B2 四条验收逐条落位 | SPEC §6 B2 L174-177 四条 → task 验收 L115-116（pending 401/403）· L118-120（decide→store 置决 · 409/404/422）· L120（decide→resume→`done{completed}`）· L121（rejected→resume 收工）· L124（OA 签名面回归 callback zero-diff + `test_hitl.py` 全绿）——**四条全覆盖且更细**（另加异 owner 404 L122 与 N2 持久化 L123） | ✅ |
| C3 | 非范围锁死（越任一条即停） | task L86-92 八条：OA 签名面（`_require_signed`/callback/`GET requests`/`GET runtime`/`signature.py` 零 diff）· resume 语义鉴权不动 · 不自动 resume · 零新表/迁移/协议改 · 零新 SSE · 前端归 F2 · 不改两 store 既有语义（含 `WHERE status='pending'` 守卫）；与 SPEC §3 非范围 L95-100、Q3/Q5 裁定一致 | ✅ |
| C4 | 验收全可机断 | task L115-128 共 14 条：断言字段族 / 401·403 / 过滤 / store 行状态 / 409·404·422 / 集成终帧 / replay 路径 / 越权 404 / N2 db 重启 / `test_hitl.py` 绿 / `pytest tests` 绿 / `lint-imports` 绿 / `graph-compile.sh` exit 0 / `lint-wiki-delta`；全部可对 pytest/diff/grep/命令机械断言，无主观措辞 | ✅ |
| C5 | decision 语义等价 callback | callback 路径实读 `app/ops/hitl/router.py` :122-137：`adecide(request_id, decision, by, note)` → `None` 时 `aget` 区分 404 / 409；task P2（L80）明示「复用 `store.adecide`」+ 复用同一语义 + 不自动 resume；task 验收 L118「语义等价 callback」 | ✅ |
| C6 | `adecide` pending 守卫两实现语义一致（重复决定 409 如实） | `app/ops/hitl/store.py` 实读：`InMemoryHitlStore.adecide` :83-99（:93-94 `status != STATUS_PENDING` → return None）；`DbHitlStore.adecide` :215-228 对 `_DECIDE` :159-163（`... WHERE id=:id AND status='pending' RETURNING id`）判空 → None；协议 :41-48。两实现一致，路由据 aget 区分 404/409。task failure_paths L103「重复/已决 → 409」、非范围 L92「不改既有守卫」、必读 L147 均如实 | ✅ |
| C7 | 裁定 D1（`MaintainerUser`）核对 | task 裁定 D L58-63 明载采纳 D1；failure_paths L100-101（无 cookie 401 / 非 maintainer 403）与验收 L116 对齐；`app/ops/deps.py` 实读 `require_maintainer` :56-63（role!='maintainer'→403，`get_current_user` :18-53 无 cookie→401）、`MaintainerUser` :115；既有 `resume` 用 `AdminSyncAuth`（router.py:242）保持零改动，与 D1 一致 | ✅ 无悬置 |
| C8 | 裁定 E1（owner 过滤）核对 | task 裁定 E L65-71 明载采纳 E1；`GET /hitl/pending` 归属经 `run_owner`（`app/ops/lg_rag/event_store.py` :50-69 实读，run 不存在返回 `None`）；裁定「解析不到 → 排除 + error 日志（不 500）」落 failure_paths L105、范围 P3 L81；验收 L117「异 owner 不出现」——**但「解析不到 → 排除 + logger.error + 不 500」未成独立可机断验收项**（见 nit N2） | ✅（附 nit N2） |
| C9 | OA 签名面零 diff 回归钉死 | 非范围 L86 逐件钉死：`GET /hitl/requests` · `GET /hitl/runtime` · `POST /hitl/callback` 契约与鉴权不动 · `signature.py`/`_require_signed` 零 diff；验收 L124 钉 `test_hitl.py` 全绿 + callback HMAC 零 diff + `signature.py` 零 diff。代码锚点实读：`_require_signed` :54-62 · callback :98-138 · `list_requests` :73-85 · `runtime` :65-70 · `resume` :240-330；既有 `tests/test_hitl.py` :340 `test_list_requests_requires_signature` · :316 callback unsigned 401 · :281/`:300` callback approve/dup 409 均在册 | ✅（`/runtime` 独立回归见 nit N3） |
| C10 | `hitl-outbound` 契约放行 `hitl.router → deps` 与 `→ lg_rag.event_store` | `.importlinter` :180-203 实读：`source_modules=app.ops.hitl`；`forbidden_modules` 含 `app.ops.deps` 但经 `ignore_imports: app.ops.hitl.router -> app.ops.deps` 白名单放行；`app.ops.lg_rag` **不在** forbidden（契约名即「hitl 允许 → db/lg_rag」）。router.py :31 已 `from app.ops.deps import AdminSyncAuth`（新端点再取 `MaintainerUser` 同边）、:190 局部 `from app.ops.lg_rag.event_store import last_seq, run_owner`——**无新跨模块边**。task 验收 L126 `lint-imports` 绿可兜底 | ✅ |
| C11 | failure_paths 完备锋利 | task L98-109 共 10 条：401/403/404 不泄露/409/422/null store 与 owner 解析失败不 500/decide 后未 resume 仍挂/重启丢申请(FP-6)/OA diff 拒收/未签闸 30 拒开工；均含「可重试/用户可见」，与 SPEC FP-3（L156）· FP-6（L159）对齐 | ✅ |
| C12 | test_strategy 与 N2 持久化路径 | `test_strategy=required`（L19）；note L20 明列集成测：401/403 · owner 过滤 · decide→resume 全链（图替身）· 重复 409 · 跨用户 404 · **`OPS_HITL_PERSISTENCE=db` 下 decide→重建 store（模拟重启）→resume（N2 · `DB_AVAILABLE` 门控）**；P4 L82 指定 `tests/test_hitl_pending_decide.py`；验收 L123 独立 N2 项——**SPEC 审查 N2 已闭合** | ✅ |
| C13 | 思考轮 R0–R5 控制表与回填闭合 | task L156-165 控制表六轮 R0-R5 全 `no` early_stop · `actual_last_round=R5`；L167-189 六节详述（范围/方案/失败语义/可测性/交付判定）；L193 自检结论；R5 `residual_risks` 如实登记「E1 下多 maintainer 不能互批他人 run（按归属隔离设计）」，与裁定 E 一致 · `early_stop=no` 理由成立（无提前停止） | ✅ 闭合 |
| C14 | 行为变更类「旧测 grep 影响面」条款 | 本 task 为**增量新端点**（非改默认值/校验/策略门/fallback 语义），K7 机械条款不严格触发；但 `test_strategy_note` L20 与必读 L149 只点名 `tests/test_hitl.py` + `tests/test_hitl_resume.py`，**未列 `tests/test_hitl_resume_events.py`**（该文件实证存在，13 测含 `_open_event_sink` owner 解析 :283/:302——与新端点 owner 反查同源）。全量验收 L125 `pytest tests` 绿可在套件层兜底 | ✅（附 nit N1） |
| C15 | 锚点真实（逐条实读，非只信 task） | 全部命中：`hitl/router.py` `_require_signed` :54-62 ✓ · callback :98-138 ✓ · resume :240-330 ✓ · `hitl/store.py` `adecide` 协议 :41-48 ✓ / Db :215-228 ✓（InMemory :83-99 另见）· `deps.py` require_maintainer :56-63 ✓ / require_admin_sync :86-111 ✓ · `event_store.py` `run_owner` :50-69 ✓ · `tests/conftest.py` `override_auth_maintainer` :383 / `override_auth_viewer` :405 ✓ · 先例 `docs/tasks/done/task_lg_rag_sse_resume.md` 存在 ✓。SPEC 审查 N1（`GET /requests` 锚点应为 :73-83）在 task 中未复现错误区间 | ✅ |
| C16 | 维护者令 / 裁定留痕 · 两 store 复用不越界 | task 已定夺节 L54-71 三处留痕「维护者令 2026-09-30 采纳 D1/E1」；非范围 L89/L92 明确不改 `HitlStore` 协议与两实现语义，承 SPEC §2 B2「复用既有 store」 | ✅ |

**核对计数**：内容 16 项 · 通过 16 · 不通过 0（C8/C11/C14 附非阻塞 nit）。

---

## 阻塞清单

**零内容阻塞 · 零流程内容阻塞。**

- 未发现需「退回 10-task」的实质缺口：SPEC §2/§6 B2 四条验收全覆盖，裁定 D1/E1 已落定且 task 无悬置，OA 签名面零 diff 回归在非范围 + 验收双处钉死，`adecide` pending 守卫两实现一致如实，`hitl-outbound` 契约放行口径经 `.importlinter` 实证成立。
- 流程闸 HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均 pending 属实且**符合本轮时序**（20 审完 → 维护者签 HG-AUDIT-R1 → 30）· 非 task 内容缺陷。`spec-wave verify` EXIT=2 即此三闸未签所致。

---

## 非阻塞清单（nits · 不影响 PASS）

| # | 级别 | nit | 建议处置 |
|---|------|-----|---------|
| N1 | 交付提示 · 旧测影响面枚举 | `test_strategy_note` L20 与必读 L149 仅列 `tests/test_hitl.py`/`test_hitl_resume.py`；`tests/test_hitl_resume_events.py`（owner 解析同源回归）与 `tests/test_lg_rag_sse_hitl.py` 未点名 | 30 实现时把这两个文件一并纳入回归清单；或在 task 验收 L124 补一句「既有 HITL 四测文件全绿」（全量 `pytest tests` 已可兜底，不阻塞） |
| N2 | 交付提示 · E1 未决分支 | 「run_owner 解析不到 → 排除 + error 日志 + 不 500」在裁定 E / failure_paths L105 有定义，但验收 L115-117 无独立可机断项 | 建议 30 在 `tests/test_hitl_pending_decide.py` 补一例「owner 不可解析 → 200 · 条目被排除 · `logger.error` 命中 · 不 500」，使裁定 E1 全可机断（不阻塞，行为已定义） |
| N3 | 交付提示 · `/runtime` 回归 | OA 面零 diff 验收 L124 只点名 callback + `signature.py` + `test_hitl.py`；`GET /hitl/runtime` 与 `GET /hitl/requests` 的零 diff 仅在非范围 L86 文字钉死（`requests` 有 `test_hitl.py:340` 签名断言兜底，`runtime` 无同形端点测试） | 建议验收补「`runtime`/`requests` handler 断言 `_require_signed`/鉴权未改」或明确「既有端点回归以 `test_hitl.py` 全绿为准」；行号漂移型 nit，不阻塞 |
| N4 | 观察 · `created_at` 形态 | pending 返回 `created_at`：`InMemoryHitlStore` 为 epoch float，`DbHitlStore` 经 `_row_to_dict` :250 为 ISO 字符串；两后端返回类型不同 | 验收未假定类型，暂不阻塞；建议 30 断言用「非空」而非固定类型，或在 task 注明按后端原样透传 |

---

## 结论：R1 PASS-WITH-NITS

R1 书面审 **PASS-WITH-NITS**：范围 P1-P4 忠实承接 SPEC §2 B2 三行，SPEC §6 B2 四条验收逐条落位且更细；非范围八条锁死 OA 签名面/resume/自动 resume/新表/新 SSE；`adecide` pending 守卫两实现语义一致、重复决定 409 如实；`hitl-outbound` 经 `.importlinter` :180-203 实证放行 `hitl.router → deps` 与 `→ lg_rag.event_store`，无新跨模块边；裁定 D1（MaintainerUser）与 E1（owner 过滤 + 解析失败排除）与维护者令一致、无悬置；N2 持久化路径（db 下 decide→重启→resume）已入 `test_strategy` 与独立验收；思考轮 R0–R5 闭合、`early_stop=no` 理由成立。**零内容阻塞**；`task lint` PASS（EXIT=0）· `lint-wiki-delta` PASS（EXIT=0）· 分支隔离正确。四条非阻塞 nits（旧测影响面枚举 / E1 未决分支机断 / `runtime` 回归点名 / `created_at` 形态）转 30 顺手处理，不影响签闸。

流程闸现状（属实时序）：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES = **pending** → 30 **拒开工**；本帽不代签，须维护者签 HG-AUDIT-R1 后方可下发 30。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-09-30 | R1 审查落盘：真值源真读（SPEC/SPEC 审查/标准/.importlinter）+ 代码锚点逐条实读 + 机跑 `task lint`(EXIT=0)/`lint-wiki-delta`(EXIT=0)/`spec-wave verify`(EXIT=2·三闸 pending) + `git branch` 实证 · 内容 16/16 通过 · 零阻塞 · nit 4 |
| 2026-09-30 | R1 复核确认（20-task-audit 复审）：全部码面锚点重新实读零漂移（router :54-62/:98-138/:240-330 · store :41-48/:215-228 · deps :56-63/:86-111 · event_store :50-69 · conftest :383/:405）；机跑重跑一致（`task lint` EXIT=0 · `lint-wiki-delta` EXIT=0 · `verify` EXIT=2 三闸 pending · 分支 `task/chat-history-hitl-ux`）；`.importlinter` hitl-outbound :180-203 与 invoke 快照再证成立；结论维持 **PASS-WITH-NITS 零阻塞** |

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
