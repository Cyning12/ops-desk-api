"""Structured Output Gateway · P0：parse_only / extract / deterministic repair（mock，无 LLM/库）。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.ops.structured_output import (
    deterministic_repair,
    extract_json_object,
    parse_only,
)


class _SampleSchema(BaseModel):
    name: str
    count: int = Field(ge=0)


def test_extract_valid_json_object():
    assert extract_json_object('{"a": 1, "b": "x"}') == {"a": 1, "b": "x"}


def test_extract_json_fence():
    raw = '```json\n{"route": "rag"}\n```'
    assert extract_json_object(raw) == {"route": "rag"}


def test_extract_with_surrounding_noise():
    raw = '好的，结果如下：\n{"ok": true}\n以上。'
    assert extract_json_object(raw) == {"ok": True}


def test_extract_invalid_returns_none():
    assert extract_json_object("不是 JSON") is None
    assert extract_json_object("") is None
    assert extract_json_object("[1, 2]") is None  # 仅对象，非数组


def test_deterministic_repair_curly_quotes():
    # “ ” → " ；可被 json.loads
    broken = "{“name”: “alice”, “count”: 1}"
    fixed = deterministic_repair(broken)
    assert extract_json_object(fixed) == {"name": "alice", "count": 1}


def test_deterministic_repair_preserves_string_semantics():
    """已合法 JSON：字符串内中文引号「」保持原样，不得被改写。"""
    raw = '{"msg": "他说：「你好」", "count": 0}'
    assert extract_json_object(raw) == {"msg": "他说：「你好」", "count": 0}
    # repair 也不应改动该合法字面量内的「」
    repaired = deterministic_repair(raw)
    assert "「你好」" in repaired
    assert extract_json_object(repaired) == {"msg": "他说：「你好」", "count": 0}


def test_parse_only_success():
    outcome = parse_only('{"name": "x", "count": 2}', schema=_SampleSchema)
    assert outcome.ok is True
    assert outcome.success is True
    assert outcome.data is not None
    assert outcome.data.name == "x"
    assert outcome.data.count == 2
    assert outcome.error is None


def test_parse_only_fence_and_noise():
    raw = '前缀废话\n```json\n{"name": "y", "count": 0}\n```\n后缀'
    outcome = parse_only(raw, schema=_SampleSchema)
    assert outcome.ok is True
    assert outcome.data is not None
    assert outcome.data.name == "y"


def test_parse_only_repair_curly_quotes_then_success():
    raw = "{“name”: “z”, “count”: 3}"
    outcome = parse_only(raw, schema=_SampleSchema)
    assert outcome.ok is True
    assert outcome.repaired is True
    assert outcome.data is not None
    assert outcome.data.name == "z"
    assert outcome.data.count == 3


def test_parse_only_schema_missing_field_not_success():
    outcome = parse_only('{"count": 1}', schema=_SampleSchema)
    assert outcome.ok is False
    assert outcome.data is None  # Host 权威：无半成功业务 dict
    assert outcome.error


def test_parse_only_schema_type_error_not_success():
    outcome = parse_only('{"name": "x", "count": "nope"}', schema=_SampleSchema)
    assert outcome.ok is False
    assert outcome.data is None
    assert outcome.error


def test_parse_only_unextractable_fails():
    outcome = parse_only("纯文本无对象", schema=_SampleSchema)
    assert outcome.ok is False
    assert outcome.data is None
    assert "unable to extract" in (outcome.error or "")
