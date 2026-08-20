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
    """lg_rag Phase 1 图状态。

    当前与 MessagesState 等价（仅 messages 字段）；
    定义为薄子类是为了给 Phase 2/3 的扩展字段留锚点，
    并让 graph/nodes 的注解语义明确（不直接依赖内建名）。
    """
