"""Intent 节点（S2-a · LLM + SO Host 校验）。

失败写保守 fallback intent，不拒图。
"""

from __future__ import annotations

import logging

from app.ops.lg_rag.schemas.intent import IntentV1
from app.ops.lg_rag.state import LgRagState
from app.ops.prompts import render
from app.ops.structured_output import StructuredFailure, acomplete_structured
from app.ops.tracing import trace_span, tracing_enabled, update_current_span_metadata

logger = logging.getLogger(__name__)

INTENT_SYSTEM_TEMPLATE = "lg_rag.intent.system"


def fallback_intent_dict() -> dict:
    """保守 fallback：unknown / 全 False / low / 空摘要。"""
    return IntentV1().model_dump()


def _last_user_text(messages: list) -> str:
    for m in reversed(messages):
        if getattr(m, "type", None) == "human" or m.__class__.__name__ == "HumanMessage":
            content = getattr(m, "content", "")
            return content if isinstance(content, str) else str(content)
    return ""


def _record_intent_span(metadata: dict) -> None:
    if not tracing_enabled():
        return
    try:
        from langfuse import get_client

        get_client().update_current_span(metadata=metadata)
    except Exception:
        pass
    update_current_span_metadata(metadata)


def _query_from_state(state: LgRagState) -> str:
    messages = state.get("messages") or []
    return _last_user_text(messages)


async def intent_node(state: LgRagState) -> dict:
    """写 ``state.intent``；SO 失败走 fallback + span，不拒图。"""
    with trace_span("intent", run_type="chain"):
        query = _query_from_state(state)
        system = render(INTENT_SYSTEM_TEMPLATE)
        fallback = False
        parsed: IntentV1 | None = None
        try:
            result = await acomplete_structured(
                system=system,
                user=query or "",
                schema=IntentV1,
                max_retries=1,
                raise_on_failure=False,
            )
            if isinstance(result, IntentV1):
                parsed = result
            else:
                fallback = True
                err = (
                    result.error
                    if isinstance(result, StructuredFailure)
                    else "structured output failed"
                )
                logger.warning("lg_rag intent SO 失败，fallback intent err=%r", err)
        except Exception as exc:
            fallback = True
            logger.warning("lg_rag intent LLM/SO 异常，fallback intent err=%r", exc)

        intent = parsed.model_dump() if parsed is not None else fallback_intent_dict()
        _record_intent_span(
            {
                "module": "intent",
                "intent_fallback": fallback,
                "structured_output_fallback": fallback,
                "intent_domain": intent.get("domain"),
                "intent_needs_tool": intent.get("needs_tool"),
            }
        )
        return {"intent": intent}
