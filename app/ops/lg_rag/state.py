"""lg_rag 图状态定义（Phase 1）。

说明书：docs/guides/IMPL_langgraph-lg-rag-phase1_v1.md S2/S3。

Phase 1 采用 langgraph 内建 MessagesState：
- messages 走 add_messages reducer，node 返回「增量」列表即可，
  禁止手写全量覆盖；
- 输入为 HumanMessage(query)，输出为末条 AIMessage(answer)。

Router / rewrite / evaluate 等扩展字段留待 Phase 2/3 再引入，
届时在 LgRagState 上增补（保持向后兼容，新增字段须有默认值）。
"""

from __future__ import annotations

from langgraph.graph import MessagesState


class LgRagState(MessagesState):
    """lg_rag 图状态。

    messages：内建 add_messages reducer（HumanMessage in → AIMessage out）。
    route（Phase 2）：router_node 写入的意图分流，取值
        "rag" | "direct" | "refuse"；无 reducer，节点写回即覆盖。
        老 checkpoint 无此键：条件边 route_by_route 缺省 "rag"。

    Phase 3 的 retry_count / evaluate 字段届时再扩（须保持向后兼容）。
    """

    route: str
