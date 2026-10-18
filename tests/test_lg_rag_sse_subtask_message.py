"""task lg-rag-sse-subtask-message：subtask.progress 可读 message（mock，不连真 LLM）。"""

from __future__ import annotations

import logging
from typing import Any

import pytest

from app.ops.lg_rag import progress_stream, sse_stream
from app.ops.lg_rag.subtask_message import (
    SUBTASK_MESSAGE_MAX_LEN,
    build_subtask_done_message,
    build_subtask_running_message,
    build_subtask_step_message,
)

# ---------- 纯模板函数 ----------


def test_running_message_type_and_input() -> None:
    msg = build_subtask_running_message(type="rag", input_preview="查一下本周工单")
    assert msg
    assert "检索" in msg
    assert "查一下本周工单" in msg


def test_running_message_unknown_type_fallback() -> None:
    msg = build_subtask_running_message(type="weird", input_preview="")
    assert msg
    assert "weird" in msg


def test_step_retrieve_start() -> None:
    assert build_subtask_step_message(step="retrieve", detail={"phase": "start"}) == ("开始检索…")


def test_step_retrieve_done_hit_count() -> None:
    msg = build_subtask_step_message(step="retrieve", detail={"phase": "done", "hit_count": 5})
    assert "5" in msg
    assert "命中" in msg


def test_step_grade_done_gate_action_semantics() -> None:
    msg = build_subtask_step_message(
        step="grade",
        detail={"phase": "done", "kept_count": 3, "gate_action": "answer_partial"},
    )
    assert "3" in msg
    assert "部分作答" in msg
    msg_refuse = build_subtask_step_message(
        step="grade", detail={"phase": "done", "gate_action": "refuse"}
    )
    assert "拒答" in msg_refuse


def test_step_rewrite_current_query() -> None:
    msg = build_subtask_step_message(
        step="rewrite", detail={"current_query": "Ops Desk 周报怎么导出"}
    )
    assert msg.startswith("改写查询：")
    assert "周报" in msg


def test_step_answer_done_chars() -> None:
    msg = build_subtask_step_message(step="answer", detail={"phase": "done", "answer_chars": 42})
    assert "42" in msg


def test_step_unknown_fallback_contains_step_name() -> None:
    msg = build_subtask_step_message(step="mystery_node", detail=None)
    assert msg
    assert "mystery_node" in msg


def test_step_empty_step_fallback_non_empty() -> None:
    assert build_subtask_step_message(step="", detail=None) == "子任务进行中"


def test_done_message_from_subtask_result_output() -> None:
    msg = build_subtask_done_message(
        subtask_result={"id": "t1", "type": "rag", "output": "命中 3 条证据"}
    )
    assert msg
    assert "命中 3 条证据" in msg


def test_done_message_error() -> None:
    msg = build_subtask_done_message(subtask_result={"id": "t1", "error": "LLM timeout"})
    assert "失败" in msg
    assert "LLM timeout" in msg


def test_done_message_extract_dict_output() -> None:
    msg = build_subtask_done_message(
        subtask_result={
            "type": "extract",
            "output": {"dates": ["2026-09-08"], "versions": [], "people": []},
        }
    )
    assert "1" in msg
    assert "信息抽取" in msg


def test_done_message_bare_fallback_non_empty() -> None:
    assert build_subtask_done_message(subtask_result=None) == "子任务完成"


def test_message_truncated_at_max_len() -> None:
    long_query = "问" * 500
    msg = build_subtask_step_message(step="rewrite", detail={"current_query": long_query})
    assert len(msg) <= SUBTASK_MESSAGE_MAX_LEN
    msg_running = build_subtask_running_message(type="rag", input_preview=long_query)
    assert len(msg_running) <= SUBTASK_MESSAGE_MAX_LEN
    msg_done = build_subtask_done_message(subtask_result={"output": long_query})
    assert len(msg_done) <= SUBTASK_MESSAGE_MAX_LEN


# ---------- emit 挂载（fake sink） ----------


class _Sink:
    def __init__(self) -> None:
        self.frames: list[tuple[str, dict[str, Any]]] = []

    async def __call__(self, role: str, payload: dict[str, Any]) -> None:
        self.frames.append((role, payload))


@pytest.fixture()
def sink() -> Any:
    s = _Sink()
    handle = progress_stream.set_subtask_progress_sink(s)
    yield s
    progress_stream.reset_subtask_progress_sink(handle)


async def test_emit_running_frame_has_message(sink: _Sink) -> None:
    await progress_stream.emit_subtask_running(
        agent_role="rag_subtask",
        subtask_id="t1",
        type="rag",
        input_preview="查工单",
    )
    _, payload = sink.frames[0]
    assert payload["status"] == "running"
    assert payload["message"]
    assert "检索" in payload["message"]


async def test_emit_step_frame_message_matches_detail(sink: _Sink) -> None:
    await progress_stream.emit_subtask_step(
        agent_role="rag_subtask",
        subtask_id="t1",
        type="rag",
        step="retrieve",
        detail={"phase": "done", "hit_count": 2},
    )
    _, payload = sink.frames[0]
    assert payload["status"] == "step"
    assert payload["message"] == "检索完成，命中 2 条"


async def test_emit_step_message_failure_degrades(
    sink: _Sink, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def _boom(**_kwargs: Any) -> str:
        raise RuntimeError("template boom")

    monkeypatch.setattr(progress_stream, "build_subtask_step_message", _boom)
    with caplog.at_level(logging.WARNING):
        await progress_stream.emit_subtask_step(
            agent_role="rag_subtask",
            subtask_id="t1",
            type="rag",
            step="retrieve",
            detail={"phase": "start"},
        )
    _, payload = sink.frames[0]  # 帧仍发
    assert payload["status"] == "step"
    assert "message" not in payload
    assert any("message 生成失败" in r.getMessage() for r in caplog.records)


# ---------- done 映射（map_node_update 纯同步） ----------


def test_map_node_update_done_has_message() -> None:
    et, _, payload = sse_stream.map_node_update(
        "rag_subtask",
        {"subtask_results": [{"id": "t1", "type": "rag", "output": "答：3 条"}]},
    )
    assert et == "subtask.progress"
    assert payload["status"] == "done"
    assert payload["message"]
    assert "答：3 条" in payload["message"]


def test_map_node_update_done_fallback_message() -> None:
    _, _, payload = sse_stream.map_node_update("tool_exec", {"ok": True})
    assert payload["status"] == "done"
    assert payload["message"]  # 缺 subtask_result 仍有非空兜底


def test_map_node_update_done_message_failure_degrades(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def _boom(**_kwargs: Any) -> str:
        raise RuntimeError("boom")

    monkeypatch.setattr(sse_stream, "build_subtask_done_message", _boom)
    with caplog.at_level(logging.WARNING):
        et, _, payload = sse_stream.map_node_update(
            "rag_subtask", {"subtask_results": [{"id": "t1", "output": "x"}]}
        )
    assert et == "subtask.progress"
    assert payload["status"] == "done"
    assert "message" not in payload
    assert any("message 生成失败" in r.getMessage() for r in caplog.records)
