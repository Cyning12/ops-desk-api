"""S2-a · IntentV1 schema（合法 / extra ignore / 缺省）。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.ops.lg_rag.schemas import IntentV1
from app.ops.lg_rag.state import LgRagState


def test_lg_rag_state_has_intent_field():
    assert "intent" in LgRagState.__annotations__


def test_intent_v1_valid():
    parsed = IntentV1(
        domain="ops_kb",
        needs_tool=True,
        needs_skill=False,
        is_composite=True,
        risk_hint="medium",
        summary="查 issue 状态",
    )
    dumped = parsed.model_dump()
    assert dumped["domain"] == "ops_kb"
    assert dumped["needs_tool"] is True
    assert dumped["is_composite"] is True
    assert dumped["risk_hint"] == "medium"
    assert dumped["summary"] == "查 issue 状态"


def test_intent_v1_extra_ignore():
    parsed = IntentV1.model_validate(
        {
            "domain": "general",
            "needs_tool": False,
            "junk_field": 1,
            "route": "refuse",
        }
    )
    dumped = parsed.model_dump()
    assert "junk_field" not in dumped
    assert "route" not in dumped
    assert dumped["domain"] == "general"


def test_intent_v1_defaults_when_missing():
    parsed = IntentV1.model_validate({})
    dumped = parsed.model_dump()
    assert dumped == {
        "domain": "unknown",
        "needs_tool": False,
        "needs_skill": False,
        "is_composite": False,
        "risk_hint": "low",
        "summary": "",
    }


def test_intent_v1_invalid_domain_rejected():
    with pytest.raises(ValidationError):
        IntentV1.model_validate({"domain": "rag"})
