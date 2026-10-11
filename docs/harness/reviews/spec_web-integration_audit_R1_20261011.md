# SPEC 书面审查：web-integration · R1（20-spec-audit）

## 元信息

| 字段 | 值 |
|---|---|
| **帽** | 20-spec-audit（SPEC 书面审 · 不实现代码 · 不改 SPEC 实质内容 · 不签 HG-SPEC-SIGNOFF） |
| **日期** | 2026-10-11 |
| **对象 SPEC** | `docs/spec/web-integration/SPEC-web-integration_v0.md`（v0 · draft-v0 · commit 95dd2e7 · 分支 task/web-integration-spec · HG-SPEC-SIGNOFF=pending） |
| **立项令** | 维护者令（m02397）：「为 web 项目生成联调需求 spec，让前端项目把已经存在功能联调完成」 |
| **轮次** | R1 |
| **实证复核范围** | 后端锚点亲读于主仓 `/Users/cyning/Desktop/Ops-desk/ops-desk-api`（master cae745e · 与 SPEC §2 声明 base 一致）；web 仓锚点亲读于 `/Users/cyning/Desktop/Ops-desk/ops-desk-web`（HEAD 71d348d · 只读零改动）；上游 A 面 SPEC 亲读于 worktree t-tool-catalog-page（42803fc）· B 面 SPEC 亲读于 worktree t-dialogue-full-view（06147fb） |

---

## 一、审查要点五条 · 逐条裁定

### 1. 锚点亲读核真（56 枚锚点逐一打开 · 55 过 1 偏）

**§2 后端端面清单（base master cae745e · 38 枚）**：

| 锚点 | 结果 | 实证 |
|---|---|---|
| router.py:19-34（前缀 `/api/ops` · 14 枚 include_router） | ✅ | :19 `APIRouter(prefix="/api/ops")` · :21-34 依序 auth/overview/issues/pulls/graph/admin_sync/admin_capability/admin_memory/chat/chat_ws/lc_evidence/lg_rag/chat_history/hitl |
| auth.py:58 login · :112 logout · :131 me · :149 tenant | ✅ | 四端点装饰器行逐一对上 |
| lg_rag/router.py:289 stream · :222 invoke · :332 replay | ✅ | :289 `@router.post("/stream")` · :222 `/invoke` · :332 `/replay`（docstring「未知/跨用户 run_id → 404」实证） |
| chat/router.py:33 stream=410 · :49 models · :60 sessions/latest | ✅ | :33-46 raise 410 + `Link: </api/ops/lg-rag/stream>; rel="successor-version"` · 匿名探针 401 在 410 前（注释在案） |
| chat/ws.py:79 websocket | ✅ | :79 `@router.websocket("/ws")`（OPS_CHAT_WS_ENABLED=false 可关停 · 注释在案） |
| event_store.py:95-107 done 终态语义 | ✅ | `run_is_terminal` docstring「done 帧且 payload.status != 'waiting_approval'（缺省 coalesce completed）→ 终态；done{waiting_approval} 挂起非终态」· 判定代码 :105-111 随附（close/acceptance 档引 :99-107 · 与 :95-107 同块 · 见 N3） |
| hitl/router.py:160 pending · :83/:98 requests · :184 decide · :466 resume · :75 runtime | ✅ | 五端点装饰器行逐一对上；pending 返回 `{items, count}`（:180 实证 · MaintainerUser cookie 面） |
| history_router.py:100 threads · :127 history | ✅ | threads 返回 `{ok:true, data}` envelope（与 §9 T-W1「threads envelope 例外照登」互洽 ✓） |
| admin/capability.py:79 runtime · :163 catalog · :217 metrics · :228 receipts · :255 idempotency | ✅ | 五端点装饰器行逐一对上 |
| overview.py:65 · graph.py:15 · issues.py:28 · pulls.py:28 · lc_evidence_chain/router.py:117 · admin/memory.py:73 | ✅ | 逐一对上 |
| admin/sync.py:17 | ⚠ **偏差（N1）** | :17 实为 `router = APIRouter(prefix="/admin/sync")` 定义行；端点 `@router.post("")` 在 **:28** |
| deps.py:86-103（Bearer 机读/maintainer） | ✅ | `require_admin_sync` :86 起 · Bearer 比对 + cookie maintainer 双路径实证 |
| main.py:29-33（OpenAPI/docs 未关）· :35-41（CORS allow_credentials=true） | ✅ | :29-33 `FastAPI(...)` 默认 docs 开 · :35-41 `add_middleware(CORSMiddleware, allow_credentials=True)` |
| config.py:45 cors_origins 默认 `http://localhost:5173,http://127.0.0.1:5173` · :78-80 get_cors_origins | ✅ | 逐字对上 |
| scripts/create_initial_user.py（邀请码每次新铸） | ✅ | 文件在仓 |

**§4/§1 web 仓锚点（HEAD 71d348d · 18 枚）**：

| 锚点 | 结果 | 实证 |
|---|---|---|
| api/auth.ts:16-40（login/me/tenant/logout） | ✅ | 四函数覆盖该区间 |
| router/index.ts:88-100（ensureMe 守卫） | ✅ | :88 `router.beforeEach` · :90 `await auth.ensureMe()` · 401 跳登录 :97/:112 |
| useLgRagSse.ts:104 stream path · :127 streamLgRag · :150 replayLgRag · :110 120_000 idle 超时 · :83-91 坏行跳过 | ✅ | 逐一对上（fetch+ReadableStream · 可重置 idle 计时器 :166-180 · JSON.parse catch continue :88-91） |
| useLgRagSse.ts:28-29「仅 6 型」 | ✅（字面成立 · 但见 BLOCKER B1） | :28 doc comment `run.start · node.progress · subtask.progress · answer · done · error` 恰 6 型无 hitl.waiting；`event_type: string`（:29）运行时全透传 |
| api/hitl.ts:20-91（pending/decide/resume） | ✅ | HITL_PENDING_PATH :20 · resume 函数 :88-94（区间尾微溢 · 不列 nit）；「decide 成功后由调用方显式第二步触发」注释实证两步钉死 |
| chatHistory.ts:20/:101/:113 · chat.ts:22 | ✅ | CHAT_THREADS_PATH :20 · fetchThreads ~:101 · fetchThreadHistory ~:110-113 · fetchLatestSession :21-25 |
| overview.ts:62 · issues.ts:47 · pulls.ts:40 · graph.ts:26 | ✅ | 四处 http.get 行逐一对上 |
| lcEvidence.ts:9/:153 · lgRag.ts:9/:151 | ✅ | PATH 常量 :9 · envelope http.post 行对上 |
| obs.ts:55-73（fixture-only） | ✅ | loadObsStatusFixture :55 起 · 动态 import fixtures/obs/*.json · 零后端调用实证 |
| vite.config.ts:90-99（proxy `/api → process.env.VITE_API_PROXY \|\| http://127.0.0.1:8000` · 127.0.0.1 注释钉死） | ✅ | :90-99 逐字对上（macOS localhost IPv6 撞 Docker 旧镜像 404 注释在案） |
| §5「web 仓无 .env 文件」 | ✅ | 仓根无 .env* |
| §1.1 栈版本「Vue 3.5 + vue-router 4 + Pinia 3 + Element Plus 2.10 · axios · X-Ops-Tenant-Id · baseURL=/api · withCredentials」 | ✅ | package.json：vue ^3.5.18 · vue-router ^4.5.1 · pinia ^3.0.3 · element-plus ^2.10.4 · axios ^1.10.0；tenant.ts:5 `TENANT_HEADER='X-Ops-Tenant-Id'` · http.ts:48-49 |
| §1.1「9 页已接通 8 个后端面 · ObsView fixture-only」 | ✅ | src/views/ 恰 9 枚 .vue · 路由 9 条；8 页有后端面、Obs fixture-only 与代码一致 |

### 2. 覆盖完整性 —— PASS

- **注册面对拍**：router.py:21-34 共 **14 枚** include_router，§2.1-2.6 全覆盖（auth/overview/issues/pulls/graph/admin_sync/admin_capability/admin_memory/chat/chat_ws/lc_evidence/lg_rag/chat_history/hitl）——**无漏面、无错面**。
- **前端 9 页 × F1-F10 映射**：Login→F1 · Overview/Issues/Pulls/Graph→F6 · Chat(SSE+replay+历史+HITL)→F2/F3/F4 · LcEvidence+LgRag→F7 · ObsView→F9（照登防误列 ✓）· 缺口页 Capability→F5 · B 面→F8 · 杂项→F10 —— **9 页无遗漏**，F8/F10 以 D4/D5 挂起态如实照登。
- **机读契约总口**（/openapi.json + CORS env 键）§2.7 在案，联调期字段级真值源可及。

### 3. 契约准确性 —— PASS（1 引用不确 → N3）

| 表述 | 结果 | 实证 |
|---|---|---|
| 帧型 7 枚（run.start/answer/subtask.progress/node.progress/hitl.waiting/done/error · `query` 系 run.start payload 键非帧型） | ✅ | sse_stream.py：run.start :343 · answer :368/:481 · subtask.progress :373 · node.progress :201/:460 · hitl.waiting :440 · done :466/:483 · error :516；resume 路径 hitl/resume.py:126/:144 同 7 型 |
| done{resumed} 终态语义 · completed 字面结构性不可达 | ✅ | hitl/resume.py:131 硬编码 `status = waiting_approval if re_interrupted else "resumed"`；sse_stream.py:482-490 纯流终帧**不带 status 键**（event_store coalesce 缺省 completed）——「字面 completed」在含 HITL resume 流结构性不可达成立；与 close_hitl_replan_carry_and_persist_guard_20261010.md:36 钉案①、验收档 :106 一致 |
| decide 可选键 resume_mode∈{inherit,immediate,manual} · 白名单未知值 400 · 重复 decide 锁拒 | ✅ | hitl/router.py:125 默认 inherit · :206-210 手工白名单 400（非 Pydantic 422 · SPEC v1 D5 :106 逐字吻合）· adecide pending 守卫（重复 decide 409 · v1 :117） |
| /chat/stream 410 Gone 走 lg-rag | ✅ | chat/router.py:33-46 + Link successor-version 头 |
| 九键白名单投影（排除 adapter/args_schema）· {items,count} | ✅ | A 面 SPEC B1 字段族恰 **9 键**：id/kind/description/when_to_use/tags/risk_level/side_effect/enabled/status；纪律 #4 显式排除 adapter · 非范围排除 args_schema |
| replay「跨用户 404 · 游标非法 422」 | ✅ | lg_rag/router.py:218-219（403 mismatch / 422 余）· :337 docstring |
| S3「六 env 组 · 验收 20261010 口径」· §1.1「8/8 PASS」 | ✅ | 验收档 :20 六 env 组逐键对上 · :11「✅ 8 项全 PASS」 |
| §5 logging basicConfig 坑位 · env 启动瞬间生效 | ✅ | 与 hitl-approval-consumption v1 §9 序 2（仓级 logging 缺失）一致 |
| A 面 signed · B 面 signed | ✅ | A 面闸表 HG-SPEC-SIGNOFF=**approved**（2026-10-11 · 授权 m01606 · 依据 R1 PASS-WITH-NITS）；B 面 SPEC 头 `signed`（2026-10-11 00 代录）——两面上游状态属实（A 面自身 :4 状态行仍 draft 未回写系 A 面链事项 · 见 N6，非本 SPEC 之误） |

### 4. 可执行性 —— **FAIL（BLOCKER B1）**

- S1-S7 场景可复跑性：S1/S2/S4/S6/S7 为回归型场景、步骤可机断可复跑 ✅；S3 全链复跑锚定验收档六 env 组 ✅；S5 依赖 B1/B2 合入以 FP-2 wait 照登 ✅。
- T-W1~W4 拆分粒度：T-W1 回归批可先行、T-W3 wait B1/B2、T-W4 待裁定——粒度合理；**唯 T-W2 内容列混入已交付工作（见 B1）**。
- D/Q 块真开放项：D1（二选一+倾向 A）、D2、D4、D5、Q2/Q3/Q5 均为留给维护者的真开放项 ✅；**D3 与 Q4 的现状前提失真（见 B1）**；Q1/Q6 重复（N5）。

### 5. 内部一致性 —— PASS（附 N5）

- 状态行 `draft-v0`（待 20-spec-audit → HG-SPEC-SIGNOFF）· 闸表 HG-SPEC-SIGNOFF=pending · 修订记录 v0-draft/v0 两行 · 元信息 review_hat=20-spec-audit —— 互洽 ✅。
- 编号面：F1-F10 · S1-S7 · D1-D5 · Q1-Q6 · FP-1~FP-5 · T-W1~W4 连续无缺 ✅；唯 Q1 与 Q6 同问「本 SPEC 档落位」且倾向相反（Q1 承 A/B 面先例暂落 api 仓 · Q6 倾向落 web 仓），属重复登记（N5）。
- **§1.1 自身矛盾点**：:33 已把「HITL 两步审批」列为已接通面，:34 缺口②/§4 F2/Q4/T-W2 却把 hitl.waiting 帧驱动渲染当作待裁定的新工作——见 B1。

---

## 二、阻塞清单（BLOCKER · 退 00 修订 · 零改 SPEC 本体由本帽严守）

### B1 · hitl.waiting 缺口表述失真：Q4 双前提皆假 · T-W2 混入已交付工作 · §1.1 自相矛盾

**实证（web 仓 HEAD 71d348d 亲读）**：

1. **帧驱动审批卡已存在**：`src/stores/chat.ts:709` `case 'hitl.waiting'` 已在 processFrame 管线消费该帧；:396 钉案「hitl.waiting 帧 → 消息流内联审批卡片（reason + 申请 id + 批准/驳回 → B2 decide → resume 两步链）」；:158「待审批卡片态（hitl.waiting 帧 / 历史 terminal_status=waiting_approval 映射）」；:240 payload.requests 提取器在案。即 web-chat-history-hitl-ux（F2）已交付「审批卡帧驱动」。
2. **「现状 pending 轮询」不存在**：chat.ts:435 明钉「B2 pending 核对快照（动作后刷新 + 进入 waiting_approval thread 一次性核对 · **不轮询** · 非全局面板）」；chat.ts/ChatView.vue 全无 setInterval/poll。
3. **SPEC 自相矛盾**：§1.1 :33 自述「chat(SSE+replay+历史+**HITL 两步审批**)」为已接通面；同段 :34 缺口②、§4 F2 联调需求、Q4、§9 T-W2 却把 hitl.waiting 渲染当作未定态新工作。

**SPEC 受染面**：

- **Q4**：「裁定补入渲染（审批卡帧驱动提示）还是仅容错跳过（**现状 pending 轮询已够**）」——两个选项的前提皆假（审批卡帧驱动已存在；pending 轮询不存在）。维护者将基于错误现状做裁定。
- **T-W2**：「hitl.waiting 帧补入事件清单**与审批卡帧驱动提示**（Q4 裁定后）」——后半为已交付工作，照拆 task 将令 web 仓重做既有功能。
- **D3**（待审单刷新「帧驱动 vs 轮询 pending」）：现状既非纯轮询（无轮询）也非缺帧驱动（审批卡已帧驱动），二选框架失真。
- **真实残留**（字面成立的部分）：仅 `useLgRagSse.ts:28` 帧型 doc comment 清单 6 型未收 hitl.waiting（`event_type: string` 运行时全透传 · 属清单/类型文档级补全）。

**修订建议（退 00）**：缺口② 改述为「useLgRagSse.ts:28 帧型清单注释/类型枚举未收 hitl.waiting（运行时 chat store :709 已消费 · 审批卡已帧驱动 · 属清单补全非新渲染）」；Q4 撤销或重写为清单补全的形式化确认；T-W2 删「审批卡帧驱动提示」保留清单补入+未知帧容错实证；D3 按「动作后刷新+入 thread 一次性核对（不轮询）」现状重写二选框架；§1.1 :33-34 对齐。

---

## 三、非阻塞清单（nits · 不阻签收 · 随 00 修订一并消化）

| # | 级别 | 内容 | 实证 / 建议 |
|---|---|---|---|
| N1 | 锚点偏差 | §2.6 `admin/sync.py:17` 实为 router 定义行；端点 `@router.post("")` 在 **:28**；且「`/admin/sync/*`」复数表述 vs 该文件仅单端点 | 改 `admin/sync.py:28` · 单数端点照实 |
| N2 | 行注错行 | §2.5 :88 把「B2 后 summary 增 `manifest_errors`/`manifest_error_details`」注在 `GET /admin/capability/runtime` 行；实际 B2 落点在 **catalog**（t-tool-catalog-page 分支 capability.py:217-218 实证 · A 面 SPEC B2 节「catalog 响应 summary 增 manifest_errors」） | 注记挪至 :89 catalog 行 |
| N3 | 引用不确 | §2.2 :64「SPEC-hitl-consumption §9 序1 钉案」：slug 实为 **hitl-approval-consumption**；其 §9 序 1 主题是 replan 盲循环，done{resumed}/completed 字面不可达的真钉案在 `close_hitl_replan_carry_and_persist_guard_20261010.md:36`（钉案①）与验收档 :106；另 close/acceptance 引 event_store **:99-107** 而本 SPEC 引 :95-107（同 docstring 块 · 覆盖无误） | 引用改指 close 档钉案①/验收档 :106 · slug 补全 · 行号可对齐 :99-107 |
| N4 | 数字失真 | FP-5/T-W2「chat-store **28 枚**测试面全绿为闸」与现状不符：web 仓 HEAD 71d348d 实测 tests/chat-store.spec.ts **65** 条 it · chat-store-hitl.spec.ts 21 条 · 全仓 225 条；仓内 docs 亦无 28 枚出处 | 闸意（既有测试全绿为回退闸）有效 · 数字按实改或改述「chat-store 相关 spec 全绿」 |
| N5 | 重复登记 | Q1 与 Q6 同问「本 SPEC 档落位」且倾向相反（Q1 承先例暂落 api 仓钉契约面 · Q6 倾向落 web 仓） | 合并为一问 · 倾向收敛 |
| N6 | 观察（非本 SPEC 责任 · 转 A 面链） | A 面 tool-catalog-page 闸表 HG-SPEC-SIGNOFF=approved（:27）但 SPEC :4 状态行仍 `draft` 未回写；本 SPEC :5 称 signed 与闸表一致，表述无误 | 移交 A 面链回写状态行 · 本 SPEC 无需动 |

---

## 结论：R1 BLOCKED

锚点亲读核真 **55/56 通过**（唯 admin/sync.py:17 行号偏差 → N1）；router.py:19-34 注册面 14 枚对拍**无漏面无错面**；前端 9 页 × F1-F10 映射完整；帧型 7 枚、done{resumed} 终态语义、resume_mode 白名单 400、410 Gone、九键投影等契约表述与代码/上游 SPEC 原文逐一吻合；S1-S7 可复跑、T-W1/W3/W4 粒度合理。**唯 BLOCKER B1**：hitl.waiting 缺口表述失真——帧驱动审批卡 web 仓已交付（chat.ts:709/:396）、pending 轮询现状不存在（chat.ts:435 钉「不轮询」），致 Q4 双前提皆假、T-W2 混入已交付工作、D3 二选框架失真、§1.1 :33-34 自相矛盾，照此签收将误导维护者裁定与 task 拆分。**退 00 修订**（修订建议见 B1 末节），N1-N6 随修订一并消化；修订后 R2 复审。**HG-SPEC-SIGNOFF 维持 pending**（本帽不签）。
