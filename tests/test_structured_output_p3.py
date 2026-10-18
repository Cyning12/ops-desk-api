"""Structured Output Gateway · P3：ensure_keys / validate / no_retry（mock，无真 LLM）。"""

from __future__ import annotations

import pytest
from pydantic import BaseModel, Field

from app.llm.schema import LlmMessage
from app.ops.structured_output import (
    StructuredFailure,
    StructuredOutputError,
    acomplete_structured,
    parse_only,
)


class _SampleSchema(BaseModel):
    name: str
    count: int = Field(ge=0)


class _Meta(BaseModel):
    score: int | None = None


class _NestedSchema(BaseModel):
    name: str
    meta: _Meta | None = None


# 故意显眼的敏感规则文案：no_retry 时不得出现在 OUTPUT CORRECTION / messages
_SECRET_RULE = "SECRET_RULE_do_not_leak_into_correction_xyz"


class _MockProvider:
    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.call_count = 0
        self.captured_messages: list[list[LlmMessage]] = []

    async def complete(self, messages, model: str | None = None) -> str:
        self.captured_messages.append(
            [LlmMessage(role=m.role, content=m.content) for m in messages]
        )
        if self.call_count >= len(self._responses):
            raise AssertionError("mock provider exhausted responses")
        out = self._responses[self.call_count]
        self.call_count += 1
        return out


def test_parse_only_ensure_keys_missing_path():
    """父路径为 None 时子路径按 missing 失败；Host 权威无半成功 data。"""
    outcome = parse_only(
        '{"name": "x"}',
        schema=_NestedSchema,
        ensure_keys=["meta.score"],
    )
    assert outcome.ok is False
    assert outcome.data is None
    assert outcome.error is not None
    assert "meta.score" in outcome.error
    assert "missing" in outcome.error


def test_parse_only_ensure_keys_null_path():
    """显式 null，或空对象经 model_dump 填成 None → not_null 失败。"""
    outcome = parse_only(
        '{"name": "x", "meta": {"score": null}}',
        schema=_NestedSchema,
        ensure_keys=["meta.score"],
    )
    assert outcome.ok is False
    assert outcome.data is None
    assert outcome.error is not None
    assert "null" in outcome.error

    empty_meta = parse_only(
        '{"name": "x", "meta": {}}',
        schema=_NestedSchema,
        ensure_keys=["meta.score"],
    )
    assert empty_meta.ok is False
    assert empty_meta.data is None
    assert empty_meta.error is not None
    assert "null" in empty_meta.error


def test_parse_only_ensure_keys_ok():
    outcome = parse_only(
        '{"name": "x", "meta": {"score": 7}}',
        schema=_NestedSchema,
        ensure_keys=["meta.score"],
    )
    assert outcome.ok is True
    assert outcome.data is not None
    assert outcome.data.meta is not None
    assert outcome.data.meta.score == 7


def test_parse_only_custom_validate_fails():
    def _too_small(m: _SampleSchema) -> str | None:
        if m.count < 5:
            return "count must be >= 5"
        return None

    outcome = parse_only(
        '{"name": "x", "count": 2}',
        schema=_SampleSchema,
        validate=_too_small,
    )
    assert outcome.ok is False
    assert outcome.data is None
    assert outcome.error == "count must be >= 5"


def test_parse_only_custom_validate_passes():
    def _ok(m: _SampleSchema) -> str | None:
        return None if m.count >= 0 else "bad"

    outcome = parse_only(
        '{"name": "x", "count": 1}',
        schema=_SampleSchema,
        validate=_ok,
    )
    assert outcome.ok is True
    assert outcome.data is not None


@pytest.mark.asyncio
async def test_complete_ensure_keys_fails_then_retry_succeeds():
    """ensure_keys 失败 reason 进入 correction；预算内重试可成功。"""
    provider = _MockProvider(
        [
            '{"name": "a", "meta": {}}',
            '{"name": "a", "meta": {"score": 3}}',
        ]
    )
    result = await acomplete_structured(
        system="s",
        user="u",
        schema=_NestedSchema,
        ensure_keys=["meta.score"],
        max_retries=2,
        _provider=provider,
    )
    assert isinstance(result, _NestedSchema)
    assert result.meta is not None
    assert result.meta.score == 3
    assert provider.call_count == 2
    joined = "\n".join(m.content for m in provider.captured_messages[1])
    assert "OUTPUT CORRECTION" in joined
    assert "meta.score" in joined


@pytest.mark.asyncio
async def test_complete_validate_fails_enters_correction():
    def _need_high(m: _SampleSchema) -> str | None:
        if m.count < 10:
            return "biz: count must be >= 10"
        return None

    provider = _MockProvider(
        [
            '{"name": "a", "count": 1}',
            '{"name": "a", "count": 10}',
        ]
    )
    result = await acomplete_structured(
        system="s",
        user="u",
        schema=_SampleSchema,
        validate=_need_high,
        max_retries=2,
        _provider=provider,
    )
    assert result.count == 10
    joined = "\n".join(m.content for m in provider.captured_messages[1])
    assert "OUTPUT CORRECTION" in joined
    assert "count must be >= 10" in joined


@pytest.mark.asyncio
async def test_no_retry_does_not_leak_sensitive_rule_into_correction():
    """no_retry：失败不注入 OUTPUT CORRECTION，敏感规则文案不得出现在 messages。"""

    def _sensitive(m: _SampleSchema) -> str | None:
        if m.count < 99:
            return _SECRET_RULE
        return None

    provider = _MockProvider(
        [
            '{"name": "a", "count": 1}',
            '{"name": "a", "count": 99}',  # 不应被调用
        ]
    )
    with pytest.raises(StructuredOutputError) as exc_info:
        await acomplete_structured(
            system="s",
            user="u",
            schema=_SampleSchema,
            validate=_sensitive,
            max_retries=3,
            no_retry=True,
            raise_on_failure=True,
            _provider=provider,
        )
    assert provider.call_count == 1
    failure = exc_info.value.failure
    assert isinstance(failure, StructuredFailure)
    assert failure.no_retry is True
    assert failure.error == _SECRET_RULE

    # 全部已发送 messages 不得含 OUTPUT CORRECTION，亦不得含敏感规则文案
    all_text = "\n".join(m.content for batch in provider.captured_messages for m in batch)
    assert "OUTPUT CORRECTION" not in all_text
    assert _SECRET_RULE not in all_text
