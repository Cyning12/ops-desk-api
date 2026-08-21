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
    retry_count（Phase 3）：rewrite_node 递增的重试计数；缺省 0。
    current_query（Phase 3）：rewrite 后的查询；rag_node 优先取用，
        缺失时回退末条 HumanMessage。rewrite 熔断时置空以终止回环。
    chain_meta（Phase 3）：rag_node 写回的 ChainResult.meta 质量信号
        子集（gate_action/hit_count/kept_count/best_relevance/grade_count），
        evaluate_node 的数据源；evidence 本体不进 state（黑盒原则）。
        缺失时 evaluate 视为 high（安全默认，防意外回环）。
    """

    route: str
    retry_count: int
    current_query: str
    chain_meta: dict
