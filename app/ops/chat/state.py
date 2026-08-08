"""ChatState：LangGraph 共享状态定义。"""
from operator import add
from typing import Annotated, TypedDict


class ChatState(TypedDict):
    """单次 Chat 运行的状态；节点返回的 dict 会按字段 merge 回本结构。

    多数字段默认「后写覆盖」；`events` 例外，见下方 Annotated 说明。
    """

    query: str
    session_id: str | None
    run_id: str
    model: str | None
    issue_context: list[dict]
    pr_context: list[dict]
    graph_context: dict | None
    intent: str
    answer: str
    # Annotated[..., add]：声明 reducer = operator.add
    # 多个节点各自 return {"events": [...]} 时，列表会拼接而非互相覆盖，
    # 这样 intent / load_context / answer 产生的 SSE 事件能完整保留到 service 侧消费。
    # 若写成普通 list[dict]，后一节点的 events 会盖掉前一节点的。
    events: Annotated[list[dict], add]
