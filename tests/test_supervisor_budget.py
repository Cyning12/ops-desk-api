"""H-β · supervisor 总步预算：主闸 aggregate / 辅闸禁 retry / env 回退 / 墙钟。"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.ops.lg_rag.multi.budget import (
    DEFAULT_MAX_SUPERVISOR_STEPS,
    bump_supervisor_step,
    get_max_supervisor_steps,
    get_max_wall_seconds,
    is_supervisor_budget_exhausted,
)
from app.ops.lg_rag.multi.nodes import route_next_subtask
from app.ops.strategy.critic import (
    decide_critic_verdict,
    route_after_critic,
)


def _pending_rag_state(**extra) -> dict:
    base = {
        "subtasks": [
            {"id": "t1", "type": "rag", "input": "q1"},
            {"id": "t2", "type": "extract", "input": "q2"},
        ],
        "subtask_results": [],
    }
    base.update(extra)
    return base


def test_get_max_supervisor_steps_default_and_fallback(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("LG_RAG_SUPERVISOR_MAX_STEPS", raising=False)
    assert get_max_supervisor_steps() == DEFAULT_MAX_SUPERVISOR_STEPS
    monkeypatch.setenv("LG_RAG_SUPERVISOR_MAX_STEPS", "8")
    assert get_max_supervisor_steps() == 8
    monkeypatch.setenv("LG_RAG_SUPERVISOR_MAX_STEPS", "0")
    assert get_max_supervisor_steps() == DEFAULT_MAX_SUPERVISOR_STEPS
    monkeypatch.setenv("LG_RAG_SUPERVISOR_MAX_STEPS", "-3")
    assert get_max_supervisor_steps() == DEFAULT_MAX_SUPERVISOR_STEPS
    monkeypatch.setenv("LG_RAG_SUPERVISOR_MAX_STEPS", "abc")
    assert get_max_supervisor_steps() == DEFAULT_MAX_SUPERVISOR_STEPS


def test_get_max_wall_seconds_default_off(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("LG_RAG_SUPERVISOR_MAX_WALL_SECONDS", raising=False)
    assert get_max_wall_seconds() == 0.0
    monkeypatch.setenv("LG_RAG_SUPERVISOR_MAX_WALL_SECONDS", "1.5")
    assert get_max_wall_seconds() == 1.5
    monkeypatch.setenv("LG_RAG_SUPERVISOR_MAX_WALL_SECONDS", "0")
    assert get_max_wall_seconds() == 0.0


def test_bump_increments_and_sets_started_at():
    out = bump_supervisor_step({}, now=100.0)
    assert out["supervisor_step_count"] == 1
    assert out["supervisor_started_at"] == 100.0
    assert "supervisor_budget_exhausted" not in out

    out2 = bump_supervisor_step(
        {"supervisor_step_count": 1, "supervisor_started_at": 100.0},
        now=101.0,
    )
    assert out2["supervisor_step_count"] == 2
    assert "supervisor_started_at" not in out2


def test_bump_marks_exhausted_at_max(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LG_RAG_SUPERVISOR_MAX_STEPS", "3")
    out = bump_supervisor_step({"supervisor_step_count": 2}, now=1.0)
    assert out["supervisor_step_count"] == 3
    assert out["supervisor_budget_exhausted"] is True


def test_route_next_subtask_budget_exhausted_goes_aggregate_even_with_pending(
    monkeypatch: pytest.MonkeyPatch,
):
    """主闸：总步耗尽 → aggregate（即使仍有 pending）。"""
    monkeypatch.setenv("LG_RAG_SUPERVISOR_MAX_STEPS", "5")
    state = _pending_rag_state(supervisor_step_count=5)
    assert route_next_subtask(state) == "observe"

    flagged = _pending_rag_state(
        supervisor_step_count=1,
        supervisor_budget_exhausted=True,
    )
    assert route_next_subtask(flagged) == "observe"


def test_route_next_subtask_not_exhausted_dispatches():
    """未耗尽：同批两个无依赖工人同时在飞，且不共享下标。"""
    state = _pending_rag_state(supervisor_step_count=2)
    for row in state["subtasks"]:
        row["subtask_id"] = row["id"]
        row["depends_on"] = []
    state["inflight_subtask_ids"] = ["t1", "t2"]
    routed = route_next_subtask(state)
    assert isinstance(routed, list)
    assert len(routed) == 2
    bound = [item.arg["assigned_subtask"]["subtask_id"] for item in routed]
    assert bound == ["t1", "t2"]
    assert {item.node for item in routed} == {"rag_subtask", "info_extract"}


def test_route_wall_clock_exhausted_goes_aggregate(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LG_RAG_SUPERVISOR_MAX_WALL_SECONDS", "10")
    state = _pending_rag_state(
        supervisor_step_count=1,
        supervisor_started_at=0.0,
    )
    with patch(
        "app.ops.lg_rag.multi.budget.time.monotonic",
        return_value=20.0,
    ):
        assert is_supervisor_budget_exhausted(state) is True
        assert route_next_subtask(state) == "observe"


def test_decide_critic_global_exhausted_forbids_retry_rebind():
    error = {"id": "t1", "type": "rag", "input": "q", "error": "boom"}
    retry_state = {
        "subtask_results": [error],
        "allowed_capability_ids": ["utc_now_iso"],
        "inner_retry_count": 0,
        "supervisor_budget_exhausted": True,
    }
    assert decide_critic_verdict(retry_state) == "end"
    rebind_state = {
        "subtask_results": [error],
        "allowed_capability_ids": [],
        "rebinding_count": 0,
        "supervisor_step_count": 99,
    }
    assert decide_critic_verdict(rebind_state) == "end"


def test_route_after_critic_blocks_retry_when_exhausted():
    state = {
        "critic_verdict": {"outcome": "retry_planner"},
        "supervisor_budget_exhausted": True,
    }
    assert route_after_critic(state) == "end"
    state2 = {
        "critic_verdict": {"outcome": "rebind"},
        "supervisor_step_count": 40,
    }
    assert route_after_critic(state2) == "end"


def test_decide_no_error_still_pass_when_exhausted():
    """无 error 仍 pass；辅闸只挡 retry/rebind。"""
    assert (
        decide_critic_verdict(
            {
                "subtask_results": [{"output": "ok"}],
                "supervisor_budget_exhausted": True,
            }
        )
        == "pass"
    )
