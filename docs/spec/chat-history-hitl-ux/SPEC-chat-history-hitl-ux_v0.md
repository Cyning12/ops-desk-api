# SPEC：会话历史 + 中断续看 + HITL 审批面（chat-history-hitl-ux）（v0）

> **层级**：L1 功能轨（chat/lg-rag 观测面补强 · 承 D2 观察期实战发现）  
> **状态**：`signed`（HG-SPEC-SIGNOFF=**approved** · 2026-09-30 · **00 代录** · 维护者令原话：「先回答上面的问题，然后考虑前后端一起更新的任务」+ 四裁定原话「1、历史真源选事件，完整加载对话历史 2、复用 resume 3、SSE应该只需要前端更改吗？ 4、先在后端落盘合并的spec，实际spec后续交给前端agent再专项落盘」· 20-spec-audit R1 **PASS-WITH-NITS** 零阻塞 · nit 4 移交 task 阶段）  
> **立项令（原话留痕）**：维护者 2026-09-30「先回答上面的问题，然后考虑前后端一起更新的任务」+ 四项裁定原话：「1、历史真源选事件，完整加载对话历史 2、复用 resume 3、SSE应该只需要前端更改吗？ 4、先在后端落盘合并的spec，实际spec后续交给前端agent再专项落盘」  
> **上游实证**：D2 委派令牌闸本地观察期冒烟（2026-09-29/30 · run `09b639f7` done{waiting_approval} 用户视角「没有最终回答」 · HITL 挂起前端零表现）  
> **下游**：HG-SPEC-SIGNOFF → 拆 task（后端 B1/B2 可先 · 前端 F1/F2 专项 SPEC 另立——**维护者裁定 Q4**：合并 SPEC 先落后端仓，前端 agent 专项落盘）  
> **Open Folder（实现）**：`ops-desk-api`（后端 B1/B2）· `ops-desk-web`（前端 F1/F2 · 专项 SPEC 后补）

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **spec_slug** | `chat-history-hitl-ux` |
| **invoke_slug** | `chat-history-hitl-ux`（task 阶段） |
| **test_strategy** | `required`（后端新端点单测+集成：归属隔离/回放完整性/decide+resume 全链/OA 签名面回归；前端专项 SPEC 自填） |
| **默认分支** | `task/chat-history-hitl-ux`（后端）· 前端仓另定（**禁止 master 直改**） |
| **graph_change_layer** | `G-L1` 预期（新 REST 路由行备注义务 · 实现 task 按实判 · HG-GRAPH-MODULES 随交付签录） |
| **freeze_id** | 无（**SSE 零新事件**——`hitl.waiting`/`done{status}` 已在 lg-rag-sse-v1 freeze 内 · 仅新增 REST 查询/决策端点） |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | **approved**（2026-09-30 · 00 代录） | 维护者令原话留痕（见状态行与头部立项令 · 四裁定已答）· R1 审查文在 `docs/harness/reviews/spec_chat_history_hitl_ux_audit_R1_20260930.md`；00 可拆后端 task（B1/B2 · invoke_slug=chat-history-hitl-ux），前端 F1/F2 依 Q4 专项 SPEC 另立 |

---

## 1. 背景与目标

D2 观察期本地冒烟（2026-09-29/30 实战）暴露观测面三缺口：用户 run 挂起等审批，前端却「没有最终回答」也无任何待审批表现；刷新后中断对话消失；无历史会话可看。

### 现状实证（本帽真读 · file:line 锚点）

| 缺口 | 真态 |
|---|---|
| 无历史 API | chat 面仅 3 端点：`POST /stream` · `GET /models` · `GET /sessions/latest`（`app/ops/chat/router.py:33/49/60`）——无列表 · 无 thread 回放 |
| 中断不可见 | lg-rag run 事件已落 `ops_lg_rag_run_events`（replay 端点在 · `router.py:332`），但前端无「按 thread 找未完结 run → 续看」入口 |
| 审批面浏览器不可达 | `GET /api/ops/hitl/requests` 走 `_require_signed` HMAC 签名头（`hitl/router.py:73-83` · OA 系统面）——浏览器永远拿不到待审批列表 |
| 前端双漏 | `stores/chat.ts:524` switch 无 `hitl.waiting` 分支（落 default 忽略）· `done` 处理器（:621）不看 `status`——`waiting_approval` 被当正常完成清场 |
| 协议面其实完备 | 后端已发 `hitl.waiting`（含 reason/requests）+ `done{status:"waiting_approval"}` —— 缺的是渲染与浏览器可达的决策面 |

### 一句话目标

以**事件表为历史真源**（用户裁定 Q1）补齐「历史会话 + 中断续看 + HITL 审批」观测闭环：后端加只读历史 API 与 cookie 化审批决策面，前端渲染既有 SSE 帧并给审批醒目形态——**SSE 契约零改动**（用户裁定 Q3）。

### 设计纪律（签收时锁死）

1. **freeze 零动**：不改 lg-rag-sse-v1 · 零新 SSE 事件类型（`hitl.waiting`/`done{status}` 复用既有帧）。
2. **OA 面零触碰**：HMAC 签名 callback 契约不动；浏览器面走新增 cookie-maintainer 端点（爆炸半径隔离）。
3. **归属隔离**：历史/审批列表按 `user_id` 过滤（承 `event_store.run_owner` 语义）· 跨用户 404。
4. **记动作不记内容**：审批台账只记动作锚点。

---

## 2. 范围

### B1 · 会话历史 API（后端 · 事件表真源 · 用户裁定 Q1）

| 端点 | 语义 |
|---|---|
| `GET /api/ops/chat/threads` | 当前用户会话列表：thread_id · 首条 query 摘要（标题）· 末活动时间 · run 数 · **最新 run 状态**（含 waiting_approval 可识别）· 分页 cursor |
| `GET /api/ops/chat/threads/{thread_id}/history` | **完整对话历史**（用户裁定「完整加载」）：按 run 序重建——每 run = 用户 query（`run.start` 帧）+ 答案（`answer` 帧聚合）+ 子任务进度摘要（`subtask.progress`）+ 终态（`done.status`）+ HITL 等待信息（`hitl.waiting` 帧 requests） |

- **真源**：`ops_lg_rag_run_events`（每帧独立 commit · 回放真值）；**不**从 checkpoint 重建（checkpoint 是状态真值不是回放真值）。
- 服务端聚合为**消息视图**返回（前端不背原始帧重建 · Q6 裁定）。
- 归属：thread 下所有 run 的 `user_id` 须等于当前用户，否则 404（承 `assert_run_owned` 语义）。

### B2 · HITL 浏览器决策面（后端 · 复用 resume · 用户裁定 Q2）

| 端点 | 语义 |
|---|---|
| `GET /api/ops/hitl/pending` | **新增**（cookie maintainer · Q5 裁定新端点不动 OA 面）：当前用户可见的 pending 审批申请（id · run_id · thread_id · reason · blocked_by · created_at） |
| `POST /api/ops/hitl/requests/{id}/decide` | **新增**（cookie maintainer）：body `{decision: approved\|rejected}` → 服务端内部置申请已决（与 callback 同语义 · **密钥不出服务器**）· 台账记动作 |
| 恢复 | **复用既有** `POST /requests/{id}/resume`（cookie maintainer 已实证可行 · 零改动） |

- `GET /runtime` / `GET /requests`（签名面）保持原样——OA 契约不动。

### F1 · 前端历史与续看（概要 · 专项 SPEC 另立）

- 历史侧栏：会话列表（B1 threads）· 点击加载完整历史（B1 history）。
- 中断 run 可识别：列表态 `waiting_approval` 醒目徽标 · 点击进入该 thread 并续看（断连 replay 机制已有 T4 基础 · `clearActiveRun`/replay 在仓）。

### F2 · 前端 HITL 审批形态（概要 · 专项 SPEC 另立）

- `hitl.waiting` 帧 → **醒目审批卡片**（reason + 申请 id + 批准/驳回按钮 → B2 decide → resume）。
- `done` 按 `status` 分支：`waiting_approval` ≠ 完成态（保持待审批视觉 · 不清场）；`completed`/`failed` 维持现行。

---

## 3. 非范围

- ❌ SSE 新事件类型 / freeze 契约任何改动（Q3 裁定：协议面已完备）
- ❌ OA callback 签名面改动（`_require_signed` 契约不动）
- ❌ 前端实现细节（组件/样式/状态机）——前端专项 SPEC 另立（Q4 裁定）
- ❌ chat legacy 面（`POST /api/ops/chat/stream` WS/旧面不动 · 本 SPEC 服务 lg-rag 面）
- ❌ 审批实时推送（轮询/进入即拉取即可 · 不引入 WS 推送）
- ❌ 历史删除/编辑/重命名（只读面先行）

---

## 4. 开放裁定（全部作答 · Q1-Q4 用户已裁）

### Q1 · 历史真源（用户裁定）

| 方案 | 裁决 |
|---|---|
| **S1 · 事件表（`ops_lg_rag_run_events`）** | **裁定（用户原话：「历史真源选事件，完整加载对话历史」）**：事件表是回放真值（每帧独立 commit · run.start 携 query · answer 携内容 · done 携终态）· 完整加载=按 run 序全量重建 |
| S2 · checkpoint 表 | 弃选：checkpoint 是状态真值非回放真值 · 中间帧（subtask 进度/审批等待）不在其中 |

### Q2 · 审批恢复路径（用户裁定）

| 方案 | 裁决 |
|---|---|
| **S1 · 复用 resume** | **裁定（用户原话：「复用 resume」）**：既有 `POST /requests/{id}/resume` 已支持 cookie maintainer（2026-09-29 本地实证批准+恢复全链）· 只新增 decide 置位端点 |
| S2 · 新开恢复端点 | 弃选：重复语义 · resume 的「批准真恢复/驳回收工出结论」设计已完备 |

### Q3 · SSE 面（用户确认）

| 方案 | 裁决 |
|---|---|
| **S1 · 零契约变更 · 仅前端渲染既有帧** | **裁定（用户原话：「SSE应该只需要前端更改吗？」→ 是）**：`hitl.waiting` 与 `done{status}` 已在 lg-rag-sse-v1 freeze 内 · 后端新增仅 REST（查询/决策） |
| S2 · 新增 SSE 审批事件 | 弃选：freeze 零动纪律 · 无必要 |

### Q4 · 分仓与 SPEC 策略（用户裁定）

| 方案 | 裁决 |
|---|---|
| **S1 · 合并 SPEC 先落后端仓 · 前端专项 SPEC 另立** | **裁定（用户原话：「先在后端落盘合并的spec，实际spec后续交给前端agent再专项落盘」）**：本 SPEC 钉契约面与后端范围；前端 F1/F2 只写概要 · 前端 agent 据此专项落盘 |
| S2 · 双仓各写各的 | 弃选：契约面（端点/帧语义）须单源 · 分写易漂移 |

### Q5 · 审批列表端点形态（本帽裁定）

| 方案 | 裁决 |
|---|---|
| **S1 · 新增 cookie 端点（`GET /hitl/pending` + `POST /requests/{id}/decide`）** | **推荐（裁定）**：OA 签名面零触碰（爆炸半径隔离）· 鉴权语义清晰（签名=外部系统 · cookie=浏览器 maintainer） |
| S2 · 既有 `GET /requests` 加 cookie 回退 | 弃选：改 OA 面既有端点的鉴权链 · 回归风险面大 |

### Q6 · 历史返回形态（本帽裁定）

| 方案 | 裁决 |
|---|---|
| **S1 · 服务端聚合消息视图** | **推荐（裁定）**：前端拿「消息」（query/answer/步骤摘要/终态）而非原始帧流 · 帧格式演进不泄漏到前端 · 分页在聚合层做 |
| S2 · 原始帧流透传前端重建 | 弃选：前端背 freeze 帧语义 · 大 thread 传输浪费 |

---

## 5. failure_paths

| # | 路径 | 处置 |
|---|---|---|
| FP-1 | 历史越权（读他人 thread） | 归属校验：thread 全 run user_id 对拍当前用户 · 不符 404（不 403 · 不泄露存在性） |
| FP-2 | 大 thread 回放慢/超大 | 聚合层分页（cursor by run 序）· 单 run answer 截断上限 · 超时如实 504 |
| FP-3 | decide 误批/越权 | 仅 cookie maintainer · 台账记动作（decision/by/at · 不记内容）· 驳回语义=「不解锁收工出结论」（承 resume 设计） |
| FP-4 | 老 run 缺 `run.start` query 帧（历史数据不全） | 标题降级为 run_id 前缀+时间 · 不阻塞列表 |
| FP-5 | 前端把 waiting_approval 当完成态（现状 bug） | F2 专项 SPEC 验收钉死：`done` 按 status 分支 · waiting_approval 保持待审批视觉 |
| FP-6 | decide 后 resume 之间进程重启（HITL null store 丢申请） | 文档面提示 `OPS_HITL_PERSISTENCE=db`（承 RUNBOOK §10 已登记）· 本 SPEC 不改默认值 |

---

## 6. 验收标准

### B1（后端 · 可机断）

- [ ] `GET /api/ops/chat/threads`：造 2 run 同 thread + 1 run 异 thread → 列表两 thread · 字段族齐（标题/末活动时间/run 数/最新状态含 waiting_approval 可识别）
- [ ] `GET .../history`：完整重建（query + answer 聚合 + subtask 摘要 + done.status + hitl.waiting requests）· 帧序正确
- [ ] 跨用户访问 → 404（FP-1）
- [ ] 缺 `run.start` query 的老 run 降级显示不阻塞（FP-4）

### B2（后端 · 可机断）

- [ ] `GET /api/ops/hitl/pending`：cookie maintainer 可拿 pending 列表 · 非 maintainer 403 · 未登录 401
- [ ] `POST .../decide` approved → 申请置已决 → 复用 `POST .../resume` → run 恢复推进（集成测：挂起 run → decide → resume → 终帧 done{completed}）
- [ ] decide rejected → resume → 收工出结论（带「没批」语义 · 承 resume 既有设计）
- [ ] OA 签名面回归：`POST /callback` HMAC 校验与既有行为零 diff（既有测试全绿）

### 契约 / 图谱

- [ ] SSE 零新事件类型（`grep` 事件词表 diff 为空 · freeze 不动）
- [ ] 新 REST 路由图谱 G-L1 行备注 + HG-GRAPH-MODULES 签录（实现 task 随交付）
- [ ] `pytest tests` 全绿 · `lint-imports` 绿

### 前端（F1/F2）

- [ ] 以前端专项 SPEC 为准（本 SPEC 不钉前端验收 · Q4 裁定）

---

## 7. 思考轮回填（R0–R5）

- **R0（读人聊/目标）**：维护者四问（历史/中断/审批表现/构建分离）+ 四裁定原话；D2 冒烟实战事件链（run 09b639f7 waiting_approval）全真读。
- **R1（范围/非范围）**：B1/B2 后端 + F1/F2 前端概要；SSE/QA 签名面/前端细节/legacy 面显式排除。
- **R2（方案对比）**：Q1-Q4 用户裁定 + Q5/Q6 本帽 ≥2 案对比裁定。
- **R3（边界/失败路径）**：FP-1~FP-6；最锋利边界=归属隔离（404 不泄露存在性）与 freeze 零动。
- **R4（验收/可测性）**：B1/B2 全可集成测断言（造 run → 列表/回放/decide/resume 全链）；契约面 diff 断言。
- **R5（签收就绪）**：开放裁定无遗留；后端可立即拆 task；前端专项 SPEC 另立（Q4）。

### 思考轮控制

| 轮 | 状态 | 说明 |
|---|---|---|
| R0 | done | 用户四问四裁定 + 实战事件链 + 代码锚点真读 |
| R1 | done | 范围 B1/B2/F1/F2 · 非范围锁死 |
| R2 | done | Q1-Q6 全部作答（≥2 案对比 · 裁定留痕） |
| R3 | done | FP-1~FP-6 裁定 |
| R4 | done | 验收全可机断（后端）· 前端归专项 |
| R5 | done | 签收就绪 → 20-spec-audit → HG-SPEC-SIGNOFF |
| early_stop | no | — |

---

## 8. 关联

- 实证源：D2 RUNBOOK `docs/guides/RUNBOOK_delegation_token_observe_local_v1_zh.md`（§10 HITL 批准链）· 本窗冒烟事件链
- 码面锚点：`app/ops/chat/router.py`（3 端点现状）· `app/ops/lg_rag/router.py:332`（replay）· `app/ops/lg_rag/event_store.py`（归属语义）· `app/ops/hitl/router.py`（callback/resume/签名面）· `ops-desk-web/src/stores/chat.ts:524-650`（前端双漏现场）
- 前端专项 SPEC（待立）：`ops-desk-web` 仓 · 依据本 SPEC §2 F1/F2 概要 + 契约面

## 修订记录

| 日期 | 版本 | 内容 |
|---|---|---|
| 2026-09-30 | v0 | 10-spec 初稿：维护者四裁定（事件真源/复用 resume/SSE 零动/合并 SPEC 先落后端仓）+ Q5/Q6 本帽裁定 · FP-1~FP-6 · R0–R5 回填 |
| 2026-09-30 | v0 | 20-spec-audit R1 **PASS-WITH-NITS**（14/14 · 零阻塞 · nit 4：N1 锚点行号已勘 · N2-N4 移交 task 阶段）· **00 代录 HG-SPEC-SIGNOFF=approved**（维护者令原话留痕见状态行）· 下一棒：00 起草后端 task（B1/B2） |