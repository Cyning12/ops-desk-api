"""确定性评估器单测：枚举 / 集合 / schema / 缺 expect 键。"""

from __future__ import annotations

import pytest

from tests.eval.eval_agent_graders import (
    eval_allowlist_match,
    eval_plan_schema,
    eval_route_match,
    eval_subtask_types,
    eval_tool_ids_in_allowlist,
    require_expect,
)


def test_eval_agent_require_expect_missing_key():
    with pytest.raises(AssertionError, match="缺 expect"):
        require_expect({"id": "x"}, "route")
    with pytest.raises(AssertionError, match="缺"):
        require_expect({"id": "x", "expect": {}}, "route")


def test_eval_agent_route_match_enum_eq():
    assert eval_route_match("rag", "rag") == 1
    assert eval_route_match("direct", "refuse") == 0


def test_eval_agent_route_match_illegal_expect_raises():
    with pytest.raises(ValueError, match="expect.route 非法"):
        eval_route_match("rag", "bogus")


def test_eval_agent_allowlist_set_eq():
    assert eval_allowlist_match(["utc_now_iso"], ["utc_now_iso"]) == 1
    assert eval_allowlist_match(["b", "a"], ["a", "b"]) == 1
    assert eval_allowlist_match(["utc_now_iso"], ["utc_now_iso", "bogus"]) == 0


def test_eval_agent_tool_id_not_in_allowlist_fails():
    plan = [{"id": "t1", "type": "tool", "input": "q", "tool": "bogus_tool"}]
    assert eval_tool_ids_in_allowlist(plan, ["utc_now_iso"]) == 0


def test_eval_agent_tool_id_in_allowlist_ok():
    plan = [{"id": "t1", "type": "tool", "input": "q", "tool": "utc_now_iso"}]
    assert eval_tool_ids_in_allowlist(plan, ["utc_now_iso"]) == 1
    rag_only = [{"id": "t1", "type": "rag", "input": "q"}]
    assert eval_tool_ids_in_allowlist(rag_only, ["utc_now_iso"]) == 1


def test_eval_agent_plan_schema():
    ok = [{"id": "t1", "type": "rag", "input": "查部署"}]
    assert eval_plan_schema(ok) == 1
    assert eval_plan_schema([]) == 0
    assert eval_plan_schema([{"id": "t1", "type": "bogus", "input": "q"}]) == 0
    assert eval_plan_schema([{"id": "t1", "type": "tool", "input": "q"}]) == 0
    tool_ok = [{"id": "t1", "type": "tool", "input": "q", "tool": "utc_now_iso"}]
    assert eval_plan_schema(tool_ok) == 1


def test_eval_agent_subtask_types():
    subtasks = [
        {"id": "t1", "type": "rag", "input": "a"},
        {"id": "t2", "type": "extract", "input": "b"},
    ]
    assert eval_subtask_types(subtasks, ["rag", "extract"]) == 1
    assert eval_subtask_types(subtasks, ["rag"]) == 0
