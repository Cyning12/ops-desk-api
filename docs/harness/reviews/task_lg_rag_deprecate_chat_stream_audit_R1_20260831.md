# Task Audit R1：lg-rag-deprecate-chat-stream

> **hat_id**：20-task-audit  
> **task**：`docs/tasks/active/task_lg_rag_deprecate_chat_stream.md`（T6 · 弃用 chat stream · api 清扫）  
> **上游 SPEC**：`docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §4.1（T0 弃用通道 + 不删 chat 代码）· §9.3（T6 图谱钩子）· §10.5 · §11  
> **先例**：`docs/harness/reviews/task_lg_rag_sse_token_stream_audit_R1_20260831.md`（T5 · 同 freeze / 同 W4 豁免处理）  
> **日期**：2026-08-31 · 审查人：20-task-audit  
> **10 lint**：PASS（W4 无思考轮节 · SPEC 承载合法）· 本帽复跑 `dsh-coding-kit@1.10.0 task lint` → **PASS（exit 0）** 核实

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **pass** · 零阻塞 · 不退回 10 · **无「必须退回 00 改钉」级问题** |
| **流程闸** | `HG-AUDIT-R1` **仍 pending**（正确 · 20 不代签）· `HG-TASK-DRAFT` / `HG-GRAPH-MODULES` 已 approved |
| **30 授权** | **未签发** · pending 时禁止附 30 Prompt；真值仍在 task 人工闸表；**可交 00 代签 HG-AUDIT-R1** |

---

## 审查核对（对照 SPEC §4.1/§9.3/§10.5/§11 · 现网代码 · 先例）

| 审查点 | 结论 |
|--------|------|
| 处置 = **410**（非 404 · 非删码）与 05 §4.1/§10.5 一致性 | **一致 · 不退回 00**。§4.1 T0：chat/stream 进弃用通道 · **不删 chat 代码** · 下线日留 T6；§10.5 api 行「标记/移除 `/ops/chat/stream`（**或 410**）· 文档 · 图谱」。task 00 定夺钉 `POST /api/ops/chat/stream` → 410 Gone（JSON 迁移指针 + `Deprecation` 头 · **不** 404 避免监控「404 洪流」语义混淆——与 §10.5 联调项「监控无 404 洪流」原文对齐）；「本波仅路由 410，不删 chat 代码/图/表」延续 §4.1 非范围。选型落在 SPEC 明文选项内 |
| 下线窗口授权是否写明 | **已写明**。前置行「维护者下线窗口 = **维护者 Prompt 授权可开**（串行波次 2）」+ 修订记录 00 行「维护者 Prompt 授权下线窗口」+ HG-TASK-DRAFT「00 代签 · 维护者 Prompt 授权」——与 §10.5 前置「维护者定下线窗口」一致 |
| 保留端点清单 vs 「lg-rag 零改动」/「chat 代码零删除」互斥性 | **互斥无冲突**。保留 = `GET /chat/models`（router.py L97 ✓）· `GET /chat/sessions/latest`（L108 ✓）· WS `/chat/ws`（ws.py L79 · demo 未鉴权 ✓）**本波不动**且列入验收「行为不变」；「lg-rag 零改动」= `app/ops/lg_rag/** 零 diff`（验收条 4）；「chat 零删除」= `app/ops/chat/**` 零删除、仅 router.py stream 端点函数改 410（验收条 8）。三者正交：改动面被钉死在**单端点函数体**，无重叠解释空间 |
| 测试清理范围 | **声明成立**。现网核实：`test_chat_router.py` 四 stream 用例存在——`test_stream_success`（def L123 · URL L127）· `test_stream_requires_auth`（L143/L147 · 现断 401）· `test_stream_invalid_session`（L155/L158 · 现断 404）· `test_stream_existing_session_ok`（L166/L204 · 现断 200），task 要求全部改写为 410 断言（requires_auth 按鉴权次序定 401 或 410）；`TestListModels`（L218–226）不动绿。`test_auth.py` sessions/latest 用例在 **L158 def / L161 docstring 起**（task 称 L161+ · 属实 ✓）· `test_chat_ws.py`（六用例 · 纯 WS 协议）与 `test_chat_service.py`（service 层）均不触 `/chat/stream` 路由——「不受影响」声明经现网阅读成立 |
| failure_paths 完备性 | **完备**（五行）：旧客户端 410 + JSON 迁移指针 ✓ · iOS 未迁移仍 410（另仓 task 跟踪）✓ · 保留端点正常服务 ✓ · 未登录仍 401（鉴权前置）✓ · 监控 410 单独计数告警、非 404 洪流 ✓——四点要求全覆盖且多一行鉴权次序 |
| graph_delta 与 05 §9.3 T6 钩子一致性 | **一致**。§9.3 T6 行「文档为主；若删 lg_rag 边/节点 → 同步删 indexes 条目」；本 task 不删任何节点/边/indexes（graph_delta_note 钉死「仅备注 · 不删」），故无 indexes 同步义务，仅 `01_modules.md` chat 行（现网 L22 ✓）+ `10_flow_chat.graph.yaml`/`.md` deprecated 备注（**两文件均存在 · glob 核实** ✓，验收由「若存在」钉为明确要求——收紧非改钉）。graph_change_layer=`G-L1` 合理 |
| 形态建议是否越权 | **不越权**。验收条 1 子项明示「形态建议（**不钉死 · 30 落地时定**）」：`Deprecation: true`（RFC 8594）· body 字段名 `error/migrate_to/message` · 鉴权次序「保留 `Depends(get_current_user)` → 未登录仍 401；若改无条件 410 须自检写明理由」。00 定夺钉死项（410 · 迁移指针 · Deprecation 头）零实质改动，建议仅补形态细节——10 补全边界合规，同 T5 先例处理 |
| 行为变更类 task「旧测 grep 影响面」（K7 checklist） | **已列**。验收条 4 专项：lg-rag 五测试文件（token_stream / sse_stream / sse_resume / lg_rag_session_continuity / session_continuity）**glob 核实全部存在** ✓ 零改动绿 + `app/ops/lg_rag/**` 零 diff；验收条 5 grep 检索词三枚（`/chat/stream` · `chat/stream` · `useOpsChatSse`）+ 历史归档不改边界 |
| 可行性：文档清扫面实证 | **属实**。README.md 现网 **无** `/chat/stream` 引用（grep 核实 · 与 10 自检一致 ✓）；活引用确集中在 task 点名的 `docs/ios/api-auth-chat.md`（6 处）· `docs/deployment/rag-frontend-api-plan.md`（5 处）· `docs/deployment/qdrant-*.md` · `docs/guides/*.md`；done/ 归档与 05/旧任务史陈述属历史记录不改——边界已在验收钉明 |
| 05 §10.5 回写义务 | **已钩**。验收条 6「05 §10.5 回写实现句（410 · 日期 · 保留端点清单）」（§10.5 现网在 L338 ✓ 与自检一致）——SPEC 回写属文档维护、非改 task 实质 |
| §11 merge 纪律 | **一致**。00 定夺「本 PR **勿 auto-merge**」与 §11.1 原文一致；web 删 `useOpsChatSse` 死代码另 task（00 出 Prompt `PROMPT_web_00_t6_remove_chat_sse` · 本仓不改 Vue）；iOS 另仓与 §10.5 通过标准一致 |
| 思考轮 W4 豁免合法性 | **合法 · 不退回**。本帽复跑 lint → PASS · W4「无思考轮节（SPEC 承载合法豁免）」；弃用清扫型 task，思考轮由 05 §4.1/§10.5/§11 + T0–T5 关账链承载——与 T5 同款处理，20 不把缺节当内容阻塞 |
| 人工闸表与 invoke 留档 | **合规**。required_invoke_hats=`10,00,30`；00/10 invoke 已落盘 `docs/harness/invokes/by-task/lg-rag-deprecate-chat-stream/`（两文件核实 ✓）；HG-AUDIT-R1=pending 待本审查落盘后 00 代签；wiki_delta=`n/a` 合理（行为真值在 05 + 本 task）· `lint-wiki-delta` 验收条在（10 自检已 PASS） |

其余可执行性：验收含 ruff/pytest/graph-compile/lint-wiki-delta 全绿；freeze_id=`lg-rag-sse-v1` 不改（本波仅 chat 下线 · lg-rag 契约不动）；非范围逐条排除删 chat 代码/图/表 · WS/models/sessions.latest 下线 · iOS · 本仓改 Vue · lg-rag 主路径 · 重开 T2–T5 · C0–C4 · chat 事件兼容层/双写桥 · 改 freeze 字段——与范围互斥无重叠。

---

## 阻塞

无。

---

## 非阻塞风险（不退回 10 · 30 知情即可）

1. **行号锚点双套并存**：test_strategy_note / 验收条 3 用 **def 行**（L123/143/155/166），自检结论用 **URL 行**（L127/147/158/204）——两套经现网核实**均准确**（10 自检称「零修正」属实），仅标注口径不一；30 改写时以**用例名**为准即可。
2. **router.py 改 410 的 import 连带**：stream 函数改 410 后 `StreamingResponse`/`uuid`/`ChatEventStreamer` 等 import 可能变未用，ruff 条（验收 9）会迫使清理——属 router.py 文件内改动，与「`app/ops/chat/**` 零删除」（文件/模块级）不冲突，30 知情勿误判越界。
3. **grep 清扫的边角命中**：全仓 grep `/chat/stream` 还会命中 task 重点四类之外的 `docs/spec/agent-infra/README.md`（L110）与 `docs/spec/agent-infra/session/README.md`（L17）。task 已钉「仅改引导新用法的活引用 · 历史陈述不改」，30 自检清单须对这两条逐条分类（活引用 or 历史陈述）并写明判断；task 未点名这两文件不构成阻塞（grep 为全仓检索 · 清单列进自检已钩）。
4. **`test_stream_existing_session_ok` 回归语义消解**：该用例原为 uuid session 404 回归保护（L167–172 docstring），改 410 断言后回归保护消失——**合理**（端点整体弃用 · 回归对象不复存在），建议 30 改写时保留一行注释说明原回归意图，task 未钉死、非契约项。
5. **WS demo 未鉴权保留的安全自述**：ws.py docstring 已自述「do not expose publicly」· `OPS_CHAT_WS_ENABLED` 闸在；保留 WS 是 00 钉死项，安全暴露治理不在本 task 范围，仅提醒后续真鉴权 follow-up 勿因 T6 关账而遗忘。

---

## 回填清单

无（内容零阻塞 · 不改 task 实质 · **不改**人工闸表 status）。

---

## 签收

**内容签收 · pass**（终轮 R1）。流程闸 `HG-AUDIT-R1` 仍 **pending**（本帽不签发）——**可交 00 代签 HG-AUDIT-R1**；pending 期间禁止下发 30 Prompt。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（00 代签 · 维护者 Prompt 授权 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
