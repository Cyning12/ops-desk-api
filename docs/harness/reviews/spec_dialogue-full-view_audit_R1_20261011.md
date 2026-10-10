# SPEC 书面审查：dialogue-full-view · R1（20-spec-audit · 2026-10-11）

## 结论
**PASS-WITH-NITS（通过 · NIT 照登不阻签收 · 无 BLOCKER）**：锚点核真 6 项实质全过（帧型清单行字面失实降 N1）· D1 倾 C / D3 倾 B 理由成立 · 设计纪律五条闭环 · Q1-Q5 无漏关键裁定 · 验收四条可机断。建议维护者签 HG-SPEC-SIGNOFF（本帽不代签）。

**元信息**：对象 `docs/spec/dialogue-full-view/SPEC-dialogue-full-view_v0.md` @4094009（draft · HG-SPEC-SIGNOFF=pending）。实证：终局 :80-105 · handoff :30-49 · lg_rag/router.py:215-373 · sse_stream.py:83-201,340-350 · sse_replay.py:36-80 · multi/graph.py:60-104 · history.py:28-33 · lg_rag 面帧型 grep。

## 锚点核真
| 锚点 | 结果 | 实证 |
|---|---|---|
| 终局 :93-94 #15/#16 | ✅ | 原文逐字在仓（:93 折叠层级默认折叠 node.progress · :94 mermaid 中间档）；SPEC 头部+D2/D3 语义并入完整（非逐字引用 · 要素零丢失）|
| handoff :41 | ✅ | 第三棒序 2=B 面 · 「起草时并入 #15/#16」令逐字一致 |
| router.py:222/:289/:332 | ✅ | /invoke·/stream·/replay 三端点逐行对拍；跨用户 404(:350-356) · 游标非法 422(:344-348) 实证 |
| sse_stream.py:201 | ✅ | `return "node.progress", role, _summarize_payload(node_output)` 逐字 |
| multi/graph.py:86-96 十节点 | ✅ | add_node :86-95 十枚与 SPEC 清单 1:1 · START→intent_node :96 · _CRITIC_MAP pass/end→END :69-74 |
| 帧型六枚 | ⚠️→N1 | 实 grep 得 **7 型**：run.start(:344) · answer · subtask.progress(:191/:373) · node.progress · hitl.waiting(:441) · done(:466/:483) · error(:516)，history.py:28-33 常量互证；`query` 非 event_type（系 run.start payload 可选键 · :346-348 A1 裁定注释），run.start/subtask.progress 漏列。**D4 兜住**（明写 subtask 系 30 复核+枚举归前端附录）→ 降 NIT 不阻签收，§2 行字面须修 |

## 裁定评估
D1 倾 C ✅（B 服务端权威导出 replay 同口径、可逐帧对拍机断 + A 流式即时导出体验面，分工不重叠）；D3 倾 B ✅（topology 端点单源防双仓漂移 · 与 §7「拓扑节点集 1:1 add_node」机断自洽 · 高亮数据源成立：帧顶层 agent_role 载节点名，`_agent_role` :136/:177）。纪律五条 ✅（只读/权限同口径/分仓/帧契约回兼容——与 :346-348 A1 先例一致/#15 默认折叠）；Q1-Q5 覆盖格式/导出形态/拓扑源/分仓/管理面，无漏关键裁定；验收四条均机断形态 ✅。

## NIT（照登 · 00 拆 task 顺手吸收）
- **N1**：§2 帧型清单行字面失实（query 非帧型 · run.start/subtask.progress 漏列）——改标「示例 · 全量枚举见 D4」或修字面。
- **N2**：§7 高亮验收「= node.progress 帧节点名去重集」漏 subtask 三节点（rag_subtask/info_extract/tool_exec 走 subtask.progress · :178-191）——宜改「node.progress ∪ subtask.progress 节点名去重集」。
- **N3**：SPEC :33「载荷=节点名+输出摘要」不精确——节点名在帧顶层 agent_role 非 payload（payload 仅 _summarize_payload 摘要）；高亮可行性不受影响，修字面即可。
- **N4**：D1=B/C 时进行中 run 的导出快照语义未定（导至当前 seq vs 拒绝）——拆 B-E1 task 钉或补 Q6。
