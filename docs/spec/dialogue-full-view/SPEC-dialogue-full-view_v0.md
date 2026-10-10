# SPEC：dialogue-full-view（B 面 · 对话过程全量展示 + SSE 导出 + mermaid 拓扑）v0

> **状态**：`draft`（10-spec 初稿 · 待 20-spec-audit → HG-SPEC-SIGNOFF 人签）
> **立项**：2026-10-11 维护者三令（统筹第一+第二梯队）· handoff 第三棒序 2（`docs/harness/invokes/by-task/_prompts/PROMPT_00_hitl-consumption-loop-handoff_20261009.md` :41）
> **上游**：`docs/guides/DESIGN_agent_contribution_endgame_v0_zh.md`（终局路线 v0 · PR #211）——并入裁定点 **#15**（全量渲染折叠/展开层级 · 默认折叠 node.progress 类技术帧）与 **#16**（mermaid 中间档：静态拓扑 + 当次 run 经过节点高亮）
> **分仓纪律**：承 A 面/chat-history-hitl-ux 先例——本 SPEC 钉需求面+后端面；前端专项 SPEC 另立 `ops-desk-web` 仓（Q4 待维护者确认）

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **spec_slug** | `dialogue-full-view` |
| **implement_repo** | `ops-desk-api`（后端面）+ `ops-desk-web`（前端专项 SPEC 另立） |
| **graph_change_layer** | 按拆 task 实判（若开后端导出端点 → G-L1 路由行回写义务） |
| **freeze_id** | 无（只读面 · 零写路径 · 零迁移预期） |
| **review_hat** | `20-spec-audit` |
| **orchestration** | 10-spec → 20-spec-audit → HG-SPEC-SIGNOFF → 拆 task（后端视 D1 裁定 · 前端 F 专项 SPEC）→ 全链 CLOSE |

### 人工闸（SPEC 阶段）

| human_gate_id | status | 说明 |
|---|---|---|
| **HG-SPEC-SIGNOFF** | pending | 20-spec-audit 落盘后维护者签（00 代录 · 授权 m01606） |

---

## 1. 背景与目标

### 1.1 背景

- 现状对话 UI（chat-history-hitl-ux 链已交付）：SSE 流式回答 + HITL 审批交互可见，但**过程帧不全量展示**——`node.progress` 类技术帧（图节点执行轨迹）对终端用户不可见，运维/审计/调试场景须翻服务端日志。
- SSE 帧已全量落盘（event_store · `POST /api/ops/lg-rag/replay` :332 可重放 `seq > after_seq`）——**数据面已备，展示/导出面缺失**。
- 终局 #16：mermaid 拓扑不做动态图，直接中间档——静态拓扑 + 当次 run 经过节点高亮，node.progress 帧数据已在（`sse_stream.py:201` 载荷=节点名+输出摘要）。

### 1.2 目标

1. **全量展示**：对话过程帧（含 node.progress 技术帧）在 UI 可见，配 #15 折叠/展开层级防信息过载。
2. **SSE 导出**：一次 run 的完整帧序列可导出留存（审计/复现/issue 附件）。
3. **mermaid 拓扑**：multi 图静态拓扑可视化 + 当次 run 经过节点高亮。

## 2. 现状锚点（逐一亲读核真 · base master `cae745e`）

| 锚点 | 实证 |
|---|---|
| `app/ops/lg_rag/router.py:222/:289/:332` | 端点 `POST /invoke` · `POST /stream` · `POST /replay`（replay 须登录 · 未知/跨用户 run_id → 404 · 游标非法 → 422） |
| `app/ops/lg_rag/sse_stream.py:201` | `node.progress` 帧生成点 · 载荷=role+节点输出摘要（`_summarize_payload`） |
| 帧型清单 | `node.progress` · `hitl.waiting` · `error` · `done` · `query` · `answer`（lg_rag 面 grep 实证 · 全量枚举 30 复核） |
| `app/ops/lg_rag/multi/graph.py:86-96` | 图节点 10 枚：intent_node · strategy_builder · supervisor · rag_subtask · info_extract · tool_exec · aggregator · critic_node · subtask_join · observe（START→intent_node :96 · critic 条件边 pass/end→END :69-74） |
| event_store | 帧全量落盘（replay 数据源 · run_id+seq 序） |
| 终局 :93-94 | #15/#16 裁定点原文（§修订记录承并入） |

## 3. 设计纪律（签收时锁死）

1. **只读面**：B 面零写路径——展示/导出/拓扑均不改动图执行与帧生成语义（帧字面零 diff）。
2. **权限口径**：导出/拓扑沿用 replay 同口径（须登录 · 仅本人 run · 跨用户 404）。
3. **分仓纪律**：前端实现不本仓——ops-desk-web 专项 SPEC 另立，本 SPEC 只钉契约面（帧字段/端点/拓扑数据）。
4. **帧契约回兼容**：既有前端消费面（chat-history-hitl-ux）零 diff——新增帧类型可，改既有帧字面禁。
5. **信息过载防线**：#15 折叠层级为默认态（技术帧默认折叠），全量可见≠全量铺开。

## 4. 开放裁定（D 块 · 不锁死 · 留 20 审/维护者）

### D1 · SSE 导出形态（核心裁定 · 三选一）
- **A 前端自拼**：UI 流式期间捕获帧 + 断线 replay 补齐 → 客户端生成下载文件。零后端改动，但导出完整性依赖前端实现。
- **B 后端导出端点**：`GET /api/ops/lg-rag/runs/{run_id}/export`（jsonl/sse 原文 · replay 同权限口径）→ 前端仅触发下载。完整性服务端保证，加一个只读端点。
- **C 混合（倾向）**：B 为权威导出（审计口径）+ A 为流式中即时导出（体验面）。
- 倾向 C，留 20 审裁定。

### D2 · 折叠层级定义（#15 落地 · 前端专项 SPEC 细化）
- 顶层：用户 query / AI answer / error。
- 中层：HITL 事件（hitl.waiting/decide 结果 · 既有交互在案）。
- 默认折叠：node.progress 技术帧（按节点分组 · 可展开 · 帧计数徽标）。
- 层级字面/默认态由前端专项 SPEC 钉死，本 SPEC 只钉原则。

### D3 · mermaid 拓扑数据源（#16 落地 · 二选一）
- **A 前端硬编码静态图**：10 节点拓扑写死前端——最小面，但图演进时双仓同步负担。
- **B 后端 topology 端点（倾向）**：`GET /api/ops/lg-rag/topology` 从 graph 结构生成节点/边清单（mermaid 文本或 JSON 图谱）——图演进单源，前端纯渲染。
- run 节点高亮：前端消费 node.progress 帧节点名集合 → 拓扑渲染高亮（两案同口径 · 帧数据已在）。

### D4 · 帧型枚举完备性
- 本文帧型清单系 grep 实证（6 型）；30 拆 task 时须全量复核（含 subtask 系/台账系帧），枚举落前端专项 SPEC 附录。

## 5. 维护者问答（Q 块 · 待答）

- **Q1**：导出文件格式——sse 原文（可 replay 复现）/ jsonl（机读友好）/ 美化 md（人读报告）？（倾向 jsonl+sse 双格式 · 维护者裁）
- **Q2**：D1 导出形态裁定（A/B/C）？
- **Q3**：D3 拓扑源裁定（A/B）？
- **Q4**：分仓确认——前端专项 SPEC 另立 ops-desk-web（承先例）？
- **Q5**：导出是否须管理面（管理员可导任意 run）？（倾向否 · 本期仅本人 run · 管理面另立）

## 6. 范围 / 非范围

### 范围（后端面 · 本仓）
- 视 D1/D3 裁定：导出端点 / topology 端点（均只读 · replay 同权限口径）。
- 帧契约文档化（前端专项 SPEC 的锚）。

### 非范围
- 前端实现（ops-desk-web 专项 SPEC）。
- 动态拓扑/实时执行动画（终局 #16 钉死中间档 · 不做动态图）。
- 帧生成语义改动 · 图结构改动。
- run 删除/ retention 策略（另立）。

## 7. 验收方向（拆 task 细化）

- 导出完整性：导出文件帧序列与 replay 全量逐帧对拍一致（机断）。
- 权限：跨用户 run 导出/拓扑访问 404。
- 拓扑正确性：拓扑节点集与 graph.py add_node 清单 1:1（机断 · 防漂移）。
- 高亮正确性：run 经过节点集 = node.progress 帧节点名去重集（机断）。

## 8. 下游拆 task 规划（签收后）

| 序 | task | 仓 | 依赖 |
|---|---|---|---|
| B-E1 | SSE 导出端点（若 D1=B/C） | ops-desk-api | D1 裁定 |
| B-E2 | topology 端点（若 D3=B） | ops-desk-api | D3 裁定 |
| B-F1 | 前端专项 SPEC（全量渲染+折叠+导出 UI+拓扑高亮） | ops-desk-web | 本 SPEC 签收 + Q1-Q5 |

## 修订记录

| 日期 | 版本 | 说明 |
|---|---|---|
| 2026-10-11 | v0 | 10-spec 初稿（**00 代笔** · 首棒卡滞 interrupt 留痕 · 授权 m01606）：终局 #15/#16 裁定点并入 · 锚点亲读（graph.py:86-96 十节点 · sse_stream.py:201 · router 三端点 · 帧型六枚）· D1-D4 开放 · Q1-Q5 待维护者 · 分仓纪律承先例 · HG-SPEC-SIGNOFF pending |
