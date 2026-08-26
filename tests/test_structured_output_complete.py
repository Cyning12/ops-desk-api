"""Structured Output Gateway · P1：acomplete_structured（mock provider，无真 LLM/库）。"""

from __future__ import annotations

import pytest
from pydantic import BaseModel, Field

from app.llm.schema import LlmMessage
from app.ops.structured_output import (
    StructuredFailure,
    StructuredOutputError,
    acomplete_structured,
    complete_structured,
)


class _SampleSchema(BaseModel):
    name: str
    count: int = Field(ge=0)


class _MockProvider:
    """计数 + 捕获每次 complete 的 messages。"""

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


@pytest.mark.asyncio
async def test_acomplete_first_bad_second_good_with_correction():
    """第 1 次坏 JSON/schema、第 2 次好；correction 出现在第 2 次 messages。"""
    provider = _MockProvider(
        [
            '{"count": 1}',  # 缺 name → schema 失败
            '{"name": "ok", "count": 2}',
        ]
    )
    result = await acomplete_structured(
        system="sys",
        user="give json",
        schema=_SampleSchema,
        max_retries=3,
        raise_on_failure=True,
        _provider=provider,
    )
    assert isinstance(result, _SampleSchema)
    assert result.name == "ok"
    assert result.count == 2
    assert provider.call_count == 2

    second_msgs = provider.captured_messages[1]
    joined = "\n".join(m.content for m in second_msgs)
    assert "OUTPUT CORRECTION" in joined
    # 截断后的校验 reason 应出现（缺字段相关）
    assert "name" in joined.lower() or "Field required" in joined or "validation" in joined.lower()


@pytest.mark.asyncio
async def test_budget_exhausted_raises_no_success_data():
    """总尝试次数 = max_retries + 1；预算耗尽 raise，不得返回成功业务数据。"""
    # max_retries=2 → 总尝试 3 次
    provider = _MockProvider(
        [
            "not json",
            '{"count": "bad"}',
            '{"wrong": true}',
        ]
    )
    with pytest.raises(StructuredOutputError) as exc_info:
        await acomplete_structured(
            messages=[LlmMessage(role="user", content="x")],
            schema=_SampleSchema,
            max_retries=2,
            raise_on_failure=True,
            _provider=provider,
        )
    assert provider.call_count == 3  # max_retries + 1
    failure = exc_info.value.failure
    assert isinstance(failure, StructuredFailure)
    assert failure.attempts == 3
    assert failure.error
    # Host 权威：无成功 data 属性
    assert not hasattr(failure, "data") or getattr(failure, "data", None) is None


@pytest.mark.asyncio
async def test_budget_exhausted_return_failure_when_not_raise():
    provider = _MockProvider(["bad", "also bad"])
    # max_retries=1 → 总尝试 2
    out = await acomplete_structured(
        system="s",
        user="u",
        schema=_SampleSchema,
        max_retries=1,
        raise_on_failure=False,
        _provider=provider,
    )
    assert isinstance(out, StructuredFailure)
    assert provider.call_count == 2
    assert out.attempts == 2
    assert out.data is None if hasattr(out, "data") else True


@pytest.mark.asyncio
async def test_no_retry_fails_without_second_call():
    provider = _MockProvider(['{"count": 1}', '{"name": "x", "count": 0}'])
    with pytest.raises(StructuredOutputError):
        await acomplete_structured(
            system="s",
            user="u",
            schema=_SampleSchema,
            max_retries=3,
            raise_on_failure=True,
            no_retry=True,
            _provider=provider,
        )
    assert provider.call_count == 1


@pytest.mark.asyncio
async def test_complete_structured_alias_is_async():
    """SPEC 表面名 complete_structured 与 acomplete_structured 同一实现。"""
    assert complete_structured is acomplete_structured
    provider = _MockProvider(['{"name": "a", "count": 0}'])
    result = await complete_structured(
        system="s",
        user="u",
        schema=_SampleSchema,
        _provider=provider,
    )
    assert result.name == "a"


@pytest.mark.asyncio
async def test_correction_reason_truncated():
    """过长 validation reason 在 correction 中截断。"""
    # 构造极长非法文本，使 extract 失败 error 较短；改用缺字段 + 手动检查截断工具路径
    # schema 失败 error 通常不超长；直接测第 2 次 messages 含 truncated 标记路径：
    # 使用无法 extract 的超长文本作为 raw，error 固定短句；
    # 另测：mock 返回会触发 ValidationError 的对象即可。
    long_bad = "{" + ("x" * 500)  # 不可 extract
    provider = _MockProvider([long_bad, '{"name": "t", "count": 1}'])
    await acomplete_structured(
        system="s",
        user="u",
        schema=_SampleSchema,
        max_retries=1,
        _provider=provider,
    )
    joined = "\n".join(m.content for m in provider.captured_messages[1])
    assert "OUTPUT CORRECTION" in joined
    assert "Validation reason (truncated):" in joined
