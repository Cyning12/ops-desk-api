# SPEC：web-integration（ops-desk-web 联调需求 · 既有后端功能面接通）v0

> **状态**：`draft-v0`（填肉毕 · 待 20-spec-audit → HG-SPEC-SIGNOFF）
> **立项**：2026-10-11 维护者令（m02397）：「为 web 项目生成联调需求 spec，让前端项目把已经存在功能联调完成」
> **上游**：A 面 `docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md`（signed · B1/B2 task 在途）· B 面 `docs/spec/dialogue-full-view/SPEC-dialogue-full-view_v0.md`（signed · task 未拆）· 验收基线 `docs/acceptance/20261010_hitl-consumption-loop_local_acceptance.md`
> **分仓纪律**：承 A/B 面先例——本 SPEC 钉联调需求面+契约指针；实现落 ops-desk-web 仓

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **spec_slug** | `web-integration` |
| **implement_repo** | `ops-desk-web`（主体）· `ops-desk-api`（原则零改动 · 缺口另立 task） |
| **graph_change_layer** | n/a（本 SPEC 无后端图谱变更预期；若联调暴露后端缺口 → 缺口 task 按实判） |
| **freeze_id** | 无（前端联调 · 零迁移预期） |
| **review_hat** | `20-spec-audit` |
| **orchestration** | 10-spec（00 代笔骨架+盘点棒回填）→ 20-spec-audit → HG-SPEC-SIGNOFF → 拆 task（web 仓执行） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | pending | 待 20-spec-audit R1 后维护者签 |

---

## 1. 背景与目标

### 1.1 背景

- 后端 ops-desk-api 经 chat-history-hitl-ux 链（PR #204 系）+ 签发审批消费回路战役（T1/T2/T3/保号 · PR #216/#218/#220/#221 + #224）+ A 面目录（在途）已具备完整功能面；2026-10-10 增量验收 8/8 PASS。
- 前端 ops-desk-web 已有对话 UI（SSE + HITL 交互在案），但**既有后端功能未全量接通**——各面联调状态参差，缺一份权威联调需求清单。
- web 仓现状（2026-10-11 只读盘点）：Vue 3.5 + vue-router 4 + Pinia 3 + Element Plus 2.10 · axios（cookie 会话 withCredentials · baseURL=/api · 租户头 X-Ops-Tenant-Id）· SSE 原生 fetch+ReadableStream（useLgRagSse.ts · 120s 可重置 idle 超时 · 坏行跳过）。**9 页已接通 8 个后端面**：login/overview/issues/pulls/graph/chat(SSE+replay+历史+HITL 两步审批)/lc-evidence/lg-rag-invoke；ObsView 只读本地 fixture 无后端面。
- **未接通缺口**：① Capability 目录页（web 无路由 · 依赖 B1/B2 合入）② `hitl.waiting` 帧未入前端 SSE 事件清单（useLgRagSse.ts:28-29 仅 6 型）③ decide 未传 `resume_mode` 可选键（SPEC v1 D5 · 两步钉死现状与默认 manual 兼容）④ `done{resumed}` 终态语义待核前端处理 ⑤ `/chat/models` 无人消费 ⑥ `WS /chat/ws` 未用（SSE 方案已立）。

### 1.2 目标

1. **一份清单**：既有后端功能面 × 前端接通状态 × 联调需求，逐面钉端点契约指针与验收场景。
2. **联调可验收**：每面给可机断/可复跑的联调验收场景（S 编号），web 仓照单执行。
3. **缺口闭环**：联调暴露的后端缺口一律另立 task（本 SPEC 不动后端）。

## 2. 现状锚点 · 后端端面清单（逐一亲读核真 · base master `cae745e` · 路由注册 `app/ops/router.py:19-34` 前缀 `/api/ops`）

### 2.1 认证会话（`app/ops/auth.py`）

| 端点 | 锚点 | 契约要点 |
|---|---|---|
| `POST /auth/login` | auth.py:58 | 邀请码制（scripts/create_initial_user.py 每次新铸）· 会话=cookie（allow_credentials=true · main.py:35-41 CORS） |
| `POST /auth/logout` | auth.py:112 | |
| `GET /auth/me` | auth.py:131 | 当前用户（role 单值） |
| `POST /auth/tenant` | auth.py:149 | |

### 2.2 对话流式（`app/ops/lg_rag/router.py` + `app/ops/chat/`）

| 端点 | 锚点 | 契约要点 |
|---|---|---|
| `POST /lg-rag/stream` | lg_rag/router.py:289 | SSE · 帧型 7 枚：`run.start`/`answer`/`subtask.progress`/`node.progress`/`hitl.waiting`/`done`/`error`（B面 R1 实 grep 核真 · `query` 系 run.start payload 键非帧型） |
| `POST /lg-rag/invoke` | lg_rag/router.py:222 | 非流式一发一收 |
| `POST /lg-rag/replay` | lg_rag/router.py:332 | 断线补齐 `seq > after_seq` · 须登录 · 仅本人 run（跨用户 404 · 游标非法 422） |
| `POST /chat/stream` | chat/router.py:33 | **410 Gone**（验收 D3 在案 · 走 lg-rag/stream） |
| `GET /chat/models` | chat/router.py:49 | |
| `GET /chat/sessions/latest` | chat/router.py:60 | |
| `WS /chat/ws` | chat/ws.py:79 | websocket 面（联调取舍待 D 块） |
| `done` 帧语义 | event_store.py:95-107 | 含 HITL resume 流终态=`done{resumed}`（`completed` 字面结构性不可达 · SPEC-hitl-consumption §9 序1 钉案） |

### 2.3 HITL 审批（`app/ops/hitl/router.py`）

| 端点 | 锚点 | 契约要点 |
|---|---|---|
| `GET /hitl/pending` | hitl/router.py:160 | 待审单（{items,count} 外形先例） |
| `GET /hitl/requests` / `{request_id}` | hitl/router.py:83/:98 | 单据查询 |
| `POST /hitl/requests/{id}/decide` | hitl/router.py:184 | decide 载荷可选键 `resume_mode∈{inherit,immediate,manual}`（SPEC v1 D5 · 白名单未知值 400）· 重复 decide 锁拒 |
| `POST /hitl/requests/{id}/resume` | hitl/router.py:466 | 手动续跑（auto_resume=manual 默认时必需） |
| `GET /hitl/runtime` | hitl/router.py:75 | persistence 形态机读（{persistence,store_class,...}） |

### 2.4 会话历史（`app/ops/lg_rag/history_router.py`）

| 端点 | 锚点 | 契约要点 |
|---|---|---|
| `GET /chat/threads` | history_router.py:100 | 会话列表 |
| `GET /chat/threads/{thread_id}/history` | history_router.py:127 | 会话历史回放 |

### 2.5 Capability 目录（A 面 · B1/B2 合入后生效）

| 端点 | 锚点 | 契约要点 |
|---|---|---|
| `GET /capability/mine` | B1 task（PR 在途） | 当前用户可见集 · 九键白名单投影（排除 adapter/args_schema）· {items,count} |
| `GET /admin/capability/runtime` | admin/capability.py:79 | maintainer 面 · B2 后 summary 增 `manifest_errors`/`manifest_error_details` |
| `GET /admin/capability/catalog`·`/metrics`·`/receipts`·`/idempotency` | admin/capability.py:163/:217/:228/:255 | maintainer 面 |

### 2.6 仪表盘只读面

| 端点 | 锚点 |
|---|---|
| `GET /overview` | overview.py:65 |
| `GET /graph` | graph.py:15 |
| `GET /issues` · `GET /pulls` | issues.py:28 · pulls.py:28 |
| `POST /lc-evidence/invoke` | lc_evidence_chain/router.py:117 |
| `POST /admin/memory/purge` · `/admin/sync/*` | admin/memory.py:73 · admin/sync.py:17（Bearer 机读/maintainer · deps.py:86-103） |

### 2.7 机读契约总口

- FastAPI 默认 OpenAPI：`/openapi.json` + `/docs`（main.py:29-33 未关）——联调期字段级真值源。
- CORS 配置键：`cors_origins`（app/config.py:45 · 默认 `http://localhost:5173,http://127.0.0.1:5173` · 逗号分隔 · get_cors_origins :78-80 解析）。web vite dev 默认 :5173 直连免配；自定义端口/主机须设后端 env `CORS_ORIGINS`。

## 3. 设计纪律（签收时锁死）

1. **后端零改动原则**：本 SPEC 只消费既有端点；联调暴露的后端缺口一律另立 task，禁在本链夹带后端 diff。
2. **契约回兼容**：前端既有消费面（chat-history-hitl-ux 已交付面）零回归——新接通不破坏已接通。
3. **帧契约以 7 型为准**（§2.2）；未知帧型前端须容错跳过不炸（向后兼容新增帧）。
4. **权限口径**：cookie 会话 + CORS credentials；maintainer 面端点前端按角色隐藏（`/auth/me` role 驱动）。
5. **语义边界照登**：`done{resumed}` 为含 HITL 流唯一终态（禁等 `completed`）；`/chat/stream` 410 走 lg-rag。

## 4. 联调分面与验收场景（F/S 编号）

> 现状列经 2026-10-11 web 仓只读盘点核真（锚点见各面行）。

| 面 | 现状 | 联调需求 | 验收场景 |
|---|---|---|---|
| **F1 认证会话** | ✅ 已接通（api/auth.ts:16-40 · 路由守卫 ensureMe router/index.ts:88-100 · 401 全局跳登录） | 回归验证为主；role 驱动菜单（maintainer 面入口隐藏）待核 | S1 冷启动登录→me→刷新会话存续→logout 清空→401 跳登录 |
| **F2 对话流式** | ✅ 已接通（useLgRagSse.ts:104/:127 stream · :150 replay 复用管线 · 120s idle 超时） | 回归验证；`hitl.waiting` 帧补入事件清单（缺口②）；未知帧容错实证 | S2 提问→帧序渲染→中途断网→replay 补齐零丢失→帧计数一致 |
| **F3 HITL 审批** | ✅ 已接通（api/hitl.ts:20-91 pending/decide/resume · decide 不自动 resume 两步钉死） | 回归验证 + decide 卡片增 `resume_mode` 可选键 UI（缺口③ · 默认 inherit 不破坏两步）；`done{resumed}` 终态渲染核（缺口④） | S3 全链复跑（六 env 组 · 验收 20261010 口径）：挂起→审批→decide→resume→done{resumed} 渲染；auto_resume=immediate 时 UI 自适应展示自动续跑 |
| **F4 会话历史** | ✅ 已接通（chatHistory.ts:20/:101/:113 threads+history · chat.ts:22 sessions/latest） | 回归验证 | S4 多轮后刷新→历史完整回放→切换 thread 正确 |
| **F5 Capability 目录** | ❌ 未接通（web 无路由/页面 · 依赖 B1/B2 PR 合入） | **新建目录页**：/capability/mine 可见集表（九键投影）；maintainer 角色增 manifest_errors 展示（B2 面） | S5 普通用户只见可见集（零探测面）· maintainer 见故障详情；空集/故障态渲染 |
| **F6 仪表盘** | ✅ 已接通（overview.ts:62 · issues.ts:47 · pulls.ts:40 · graph.ts:26） | 回归验证 | S6 四端点渲染+筛选交互 |
| **F7 lc-evidence / lg-rag invoke** | ✅ 已接通（lcEvidence.ts:9/:153 · lgRag.ts:9/:151 同步 envelope） | 回归验证 | S7 同步调用成功/失败态渲染 |
| **F8 B面全量展示** | ⏸ 部分（node.progress 已入帧清单但无折叠层级/导出/拓扑） | 【待 D4 裁定：含→按 B面 SPEC 拆 task；不含→留后续】 | 待 D4 |
| **F9 Obs 页** | ⏸ fixture-only 无后端面（obs.ts:55-73） | 明确不在联调范围（照登防误列） | n/a |
| **F10 杂项** | `/chat/models` 无人消费 · `WS /chat/ws` 未用 | 【待 D5 裁定：models 接模型切换 or 标注弃用 · WS 标注弃用倾向】 | 待 D5 |

## 5. 联调环境与配置

- 后端起法（验收便签口径 · 20261010 文档坑位 1-4）：logging 须自带 basicConfig 启动器 · env 启动瞬间生效 · curl 全 URL+Content-Type · 六 env 组（HITL 挂起链：LG_RAG_DELEGATION_TOKEN_MODE=enforce · OPS_CAPABILITY_EXTRA_MANIFESTS · OPS_CAPABILITY_ALLOW_WRITE_TAGS=testing · OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS · OPS_HITL_PERSISTENCE=db · OPS_CAPABILITY_ALLOW_WRITE=1）。
- 登录：scripts/create_initial_user.py 一次性邀请码制。
- web 仓：无 .env 文件；vite dev proxy `/api → process.env.VITE_API_PROXY || http://127.0.0.1:8000`（vite.config.ts:90-99 · 注释钉死必须 127.0.0.1——macOS localhost 走 IPv6 会打到 Docker 旧镜像 404）。
- web 仓既有 SPEC/契约档：docs/spec/web-lg-rag-sse-t2（SSE 契约）· web-chat-history-hitl-ux · docs/checklists/CHECKLIST_lg_rag_sse_joint_release_v1.md；跨仓 POINTER docs/_tech_graph/l0/POINTERS_cross_repo.md；SSE 设计真值 ops-desk-workspace/docs/02-backend-analysis/01-sse-chat-design.md（web AGENTS.md 必读）。

## 6. 开放裁定（D 块）

### D1 · 联调基线环境（二选一）
- **A 本地双跑**：web vite dev + api uvicorn（验收便签口径）。
- **B compose 全栈**：docker compose（D1 已透传 OPS_HITL_PERSISTENCE 可验持久化）。
- 倾向 **A**（vite proxy 已就绪 · 验收便签全链为本地口径）；compose 留持久化专项复验。

### D2 · SSE 断线策略（replay after_seq 已备 · 前端重连触发条件/退避钉多细）

### D3 · HITL 待审单刷新（帧驱动 vs 轮询 pending · 间隔）

### D4 · B面全量展示是否纳入本次联调（B面 SPEC signed 但 task 未拆；含→范围扩，不含→留后续）

### D5 · WS /chat/ws 面（联调 or 标注弃用倾向）

## 7. 开放问题（Q 块 · 待维护者）

- Q1：本 SPEC 档落 ops-desk-api `docs/spec/web-integration/` 还是 ops-desk-web `docs/`（承 A/B 面先例暂落 api 仓钉契约面）。
- Q2：F5 依赖 B1/B2 合入——联调启动是否等 PR 落地。
- Q3：lc-evidence 已有页面在联调范围（F7）；admin 面（sync/memory purge·Bearer 机读）无 web 页面 → 倾向不在范围，待维护者确认。
- Q4：`hitl.waiting` 帧前端未入事件清单——裁定补入渲染（审批卡帧驱动提示）还是仅容错跳过（现状 pending 轮询已够）？
- Q5：web 仓在途 task（task_web_specwave_upgrade_3_0_0 · task_web_tenant_context_chat）与本联调链的先后/并行关系。
- Q6：本 SPEC 落位——web 仓 docs/spec/ 已有四枚 SPEC 先例，倾向落 `ops-desk-web/docs/spec/web-integration/`（api 仓仅留指针），待维护者确认。

## 8. 风险与失败路径（FP 块）

- FP-1：web 仓既有实现与本 SPEC 契约冲突 → 以端点实际行为为准回填修订，禁前端迁就错误记忆。
- FP-2：B1/B2 未合入即联调 F5 → 阻塞，标 wait。
- FP-3：SSE 代理缓冲（vite proxy/反代）导致帧不实时 → 联调环境钉死直连或关缓冲配置。
- FP-4：web 仓在途 task（specwave 升级/租户上下文）与本联调链撞文件 → 拆 task 时按路由/store 隔离面钉死。
- FP-5：`hitl.waiting` 帧补入若改 useLgRagSse 管线 → 既有 6 型帧零回归（chat-store 28 枚测试面全绿为闸）。

## 9. 拆 task 规划（签收后执行 · 落 ops-desk-web 仓 docs/tasks/）

| task | 面 | 内容 | 依赖/闸 |
|---|---|---|---|
| **T-W1 回归批** | F1/F4/F6/F7 | 已接通四面回归验证（S1/S4/S6/S7）+ role 驱动菜单核对 + 契约对拍（snake_case 原始体/threads envelope 例外照登） | 无依赖 · 可先行 |
| **T-W2 SSE/HITL 增强批** | F2/F3 | `hitl.waiting` 帧补入事件清单与审批卡帧驱动提示（Q4 裁定后）· decide 卡片 `resume_mode` 可选键 UI · `done{resumed}` 终态渲染核对（S2/S3） | 既有 28 枚 Vitest 全绿为回退闸 · useLgRagSse 管线改动面钉死（FP-5） |
| **T-W3 Capability 目录页** | F5 | 新路由+页面：/capability/mine 可见集表 · maintainer manifest_errors 展示（S5） | **wait：B1/B2 PR 合入 master**（FP-2） |
| **T-W4 裁定后另立** | F8/F10 | B面全量展示（D4）· models/WS 取舍（D5） | 待维护者裁定 |

每 task 携对应 S 场景为验收令；web 仓在途 task（specwave 升级/租户上下文）隔离面拆 task 时钉死（FP-4）。

## 修订记录

| 版本 | 日期 | 作者 | 变更 |
|---|---|---|---|
| v0-draft | 2026-10-11 | 00（代笔 · 维护者令 m02397） | 骨架：端面清单 2.1-2.7 亲读核真 |
| v0 | 2026-10-11 | 00（代笔） | 填肉：web 仓盘点回填（Vue3 栈 · 8 面已接通 · 缺口 6 枚收敛 F5/F2/F3）· F1-F10 分面表现状列 · D1 倾向 A · Q4-Q6 增 · FP-4/5 增 · §9 拆 task 规划（T-W1~W4） |
