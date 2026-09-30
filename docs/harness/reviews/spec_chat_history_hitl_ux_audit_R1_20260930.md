# SPEC 书面审查：chat-history-hitl-ux · R1（20-spec-audit）

## 元信息

| 字段 | 值 |
|---|---|
| **帽** | 20-spec-audit（SPEC 书面审 · 不实现代码 · 不改 SPEC 实质内容） |
| **日期** | 2026-09-30 |
| **对象 SPEC** | `docs/spec/chat-history-hitl-ux/SPEC-chat-history-hitl-ux_v0.md`（v0 · draft · HG-SPEC-SIGNOFF=pending） |
| **轮次** | R1（轻量路径：10-spec 思考轮 R0–R5 已回填充分，单轮书面审） |
| **实证抽查范围** | `app/ops/chat/router.py` · `app/ops/hitl/router.py` · `app/ops/lg_rag/router.py`(:280-373) · `app/ops/lg_rag/event_store.py` · `app/ops/deps.py` · `app/ops/lg_rag/sse_stream.py` |

## 核对项表

| # | 核对项 | 结果 | 证据 / 说明 |
|---|---|---|---|
| C1 | 范围可界：B1（历史 API · 事件表真源） | ✅ | §2 B1 两端点语义表齐全（threads 列表字段族 + history 按 run 序重建）· 真源锁 `ops_lg_rag_run_events` 显式排除 checkpoint 重建 |
| C2 | 范围可界：B2（HITL 浏览器面：pending + decide · 复用 resume） | ✅ | §2 B2 三行：新增 pending/decide（cookie maintainer）+ resume 复用零改动；OA 签名面（runtime/requests/callback）显式保持原样 |
| C3 | 范围可界：F1/F2 仅概要 · 前端专项 SPEC 另立 | ✅ | §2 F1/F2 只写形态概要 + §6「前端验收以专项 SPEC 为准」· 与 Q4 裁定一致 |
| C4 | 非范围锁死：SSE 零新事件 / OA 签名面不动 / 前端细节归专项 | ✅ | §3 六条非范围含 legacy chat 面、审批推送、历史写操作均显式排除；freeze_id=「无 · SSE 零新事件」 |
| C5 | Q1-Q4 用户裁定原话留痕 · 与头部立项令一致 | ✅ | 头部立项令行（:5）四裁定原话与 §4 Q1「历史真源选事件，完整加载对话历史」/Q2「复用 resume」/Q3「SSE应该只需要前端更改吗？」/Q4「先在后端落盘合并的spec…」逐字一致 |
| C6 | Q5/Q6 作者裁定 ≥2 案对比 · 裁决理由成立 | ✅ | Q5（新增 cookie 端点 vs 既有端点加 cookie 回退）：爆炸半径隔离 + 鉴权语义分层理由成立；Q6（服务端聚合消息视图 vs 原始帧透传）：freeze 帧语义不泄漏前端理由成立 |
| C7 | FP-1~FP-6：归属隔离 404 不泄露存在性 · freeze 零动 = 最锋利边界且可执行 | ✅ | FP-1 明确「不 403」承 `assert_run_owned` 语义（event_store.py:87-95 存在即 404 语义在仓）；FP-3 驳回语义承 resume 设计（hitl/router.py:240-255 docstring 实证）|
| C8 | 验收 B1/B2 全可集成测断言 | ✅ | §6 B1 四条（造 run 造 thread 断言字段族/帧序/404/降级）· B2 四条（pending 401/403 · decide→resume 全链 · 驳回收工 · OA 面零 diff 回归）均可在 pytest 集成测机断 |
| C9 | 契约面（SSE 零新事件）可 diff 断言 | ✅ | §6「grep 事件词表 diff 为空」机断可行 |
| C10 | R0–R5 控制表齐全 · early_stop=no 合理 | ✅ | §7 控制表六轮全 done + early_stop=no；六裁定全作答、无遗留开放项，无提前停止理由 |
| C11 | 实证锚点①：chat 面仅 3 端点 `router.py:33/49/60` | ✅ | 实测：`@router.post("/stream")` :33（T6 后恒 410 · 与 SPEC 非范围「legacy 面不动」兼容）· `/models` :49 · `/sessions/latest` :60，无其他路由 |
| C12 | 实证锚点②：`GET /hitl/requests` 走 `_require_signed` 签名面（:73-82） | ✅（nit 见 N1） | `@router.get("/requests")` :73 · `_require_signed(request, b"")` 调用实位于 **:83**（引用区间 73-82 覆盖装饰器/签名/docstring 未含调用行，见 N1） |
| C13 | 实证锚点③：replay 端点 `lg_rag/router.py:332` · 归属语义 `event_store.run_owner` | ✅ | `@router.post("/replay")` :332 · `run_owner` event_store.py:50 · `assert_run_owned` :87 · replay 跨用户 404 路径 :350-356 实证在仓 |
| C14 | 实证锚点④：resume cookie maintainer 可用（deps.require_admin_sync） | ✅ | resume 用 `AdminSyncAuth`（hitl/router.py:240-242）→ deps.py:86-111 `require_admin_sync` 无 Bearer 时走 cookie + role==maintainer（:105-110）；另 `hitl.waiting`/`done{waiting_approval}` 帧在 sse_stream.py:438/469 实证「协议面已完备」（Q3 前提成立） |

**核对计数**：14 项 · 通过 14 · 部分通过（含 nit）0 · 不通过 0（C12 判 ✅ 附非阻塞 nit N1）

## 阻塞清单

无。范围/非范围边界清晰可执行，六裁定全部作答且用户四裁定原话与立项令逐字一致，FP 与验收均可机断，实证锚点与代码真值一致。未发现需退回 10-spec 的实质缺口。

## 非阻塞清单（nits · 不阻签收 · 建议 00 拆 task 时顺手处理）

| # | 级别 | 内容 | 建议 |
|---|---|---|---|
| N1 | 文献 nit | SPEC §1 锚点 `hitl/router.py:73-82` 未含 `_require_signed` 实际调用行（:83） | 实现 task 引用时改为 `:73-83`（或 `:73-85`）；SPEC 本体无需为此升版 |
| N2 | 交付提示 | FP-6 仅文档面提示 `OPS_HITL_PERSISTENCE=db`，本 SPEC 不改默认值 | B2 task 的 test_strategy 宜显式覆盖「db 持久化下 decide→重启→resume」路径，避免 null store 丢申请在验收外裸奔 |
| N3 | 交付提示 | FP-2「单 run answer 截断上限」未给数值阈值 | 阈值留给实现 task 钉（建议随 task 验收补具体上限与断言），SPEC 层面「有界 + 超时如实 504」已足够 |
| N4 | 观察 | chat `/stream` 已是 410 亡端点（T6），SPEC §1 称「仅 3 端点」字面上含亡端点 | 非问题（非范围已锁 legacy 面不动）；仅提示拆 task 时勿误将 410 端点计入「可用面」 |

## HG-SPEC-SIGNOFF 建议

建议签收（pass）。本帽不代签 human_gate；维护者签录后可由 00 起草后端 task（B1/B2 可先并行拆 · invoke_slug=`chat-history-hitl-ux`），前端 F1/F2 依 Q4 由前端 agent 专项 SPEC 另立。拆 task 时携带 N1-N3 回填。

## 结论：R1 PASS-WITH-NITS

R1 书面审 **PASS-WITH-NITS**：14 项核对全数通过，四条实证锚点与代码真值一致，Q1-Q6 裁定闭合且用户原话留痕无误，failure_paths 与验收标准均可机断执行；四条非阻塞 nits（锚点行号微偏 / 持久化测试覆盖 / 截断阈值 / 亡端点字面计数）移交 task 阶段处理，不影响 HG-SPEC-SIGNOFF 进入人签。
