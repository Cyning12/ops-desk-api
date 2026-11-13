"""SSE 侧的 HITL：挂起要**说出来**，而且挂起点必须已经落盘。

两件事，缺任何一件"等待授权"都会变成一个假状态：

1. ``observe_node`` 里 ``interrupt()`` 挂起后，astream 会吐一个
   ``{"__interrupt__": [...]}`` 块。不翻译的话前端收到一个
   ``node "__interrupt__"`` 的进度帧然后流静默结束 —— 看起来就是后端崩了，
   而真相是"在等人批"。
2. 挂起那一刻进程内什么都不推进了，下一次 HTTP 请求（人点批准）要能
   找回来，全靠 checkpoint 已落盘。SSE 默认每请求新建内存 saver ⇒
   **跨请求恢复根本不可能**。所以 PG saver 必须在**整个流期间持有**。
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import patch

import pytest
from langgraph.types import Interrupt

from app.ops.lg_rag.sse_stream import extract_interrupt, iter_lg_rag_sse


@pytest.fixture(autouse=True)
def _no_pg_checkpointer_by_default(monkeypatch):
    """测试**不该**从 `.env` 继承「生产式」配置。

    ``LG_RAG_HTTP_CHECKPOINTER=postgres`` 会让 supervisor 模式的 SSE 真去开
    PG saver ⇒ "没给 checkpointer 就不该往下传"这类**对照断言**会被环境翻掉
    （实测过：外部 `.env` 一开，本模块那条反向对照直接红）。

    要验 PG 路径的用例自己 ``monkeypatch.setenv`` 覆盖 —— 它在本 fixture
    之后执行，所以能生效。
    P0' T3 后必须显式置空值（delenv 会吃到「unset=默认开」）。
    """
    monkeypatch.setenv("LG_RAG_HTTP_CHECKPOINTER", "")


_INTERRUPT_PAYLOAD = {
    "reason": "hitl_waiting",
    "run_id": "run-1",
    "thread_id": "th-1",
    "checkpoint_id": None,
    "round": 1,
    "unpersisted": False,
    "requests": [
        {
            "id": "hitl_abc",
            "subtask_id": "run-1:2",
            "unlock_subtask_id": "run-1:1",
            "blocked_by": "prefix_touch_required",
            "reason": "需要重跑已执行步骤",
        }
    ],
}


async def _frames(raw_iter: AsyncIterator[str]) -> list[dict]:
    """收集 SSE 帧（pytest asyncio_mode=auto，直接 await 即可）。"""
    out: list[dict] = []
    async for raw in raw_iter:
        for block in raw.split("\n\n"):
            block = block.strip()
            if not block.startswith("event:"):
                continue
            for line in block.split("\n"):
                if line.startswith("data: "):
                    out.append(json.loads(line[len("data: ") :]))
    return out


def _one_of(frames: list[dict], event_type: str) -> dict | None:
    for f in frames:
        if f.get("event_type") == event_type:
            return f
    return None


# ---------------------------------------------------------------------------
# 1 · __interrupt__ 块 → hitl.waiting 帧
# ---------------------------------------------------------------------------


def test_extract_interrupt_reads_value_off_interrupt_objects():
    """langgraph 给的是 Interrupt 对象，业务载荷在 ``.value`` 里。"""
    chunk = {"__interrupt__": (Interrupt(value=_INTERRUPT_PAYLOAD),)}
    payload = extract_interrupt(chunk)
    assert payload is not None
    assert payload["reason"] == "hitl_waiting"
    assert payload["requests"][0]["blocked_by"] == "prefix_touch_required"


def test_extract_interrupt_returns_none_for_normal_update_control():
    """反向对照：普通节点 update 不许被当成挂起 —— 否则"一律等待授权"
    也能通过上一条。"""
    assert extract_interrupt({"rag_subtask": {"subtask_results": []}}) is None


async def _astream_with_interrupt(
    _query: str, *, thread_id: str = "t", **_kw
) -> AsyncIterator[dict[str, Any]]:
    yield {"rag_subtask": {"subtask_results": [{"subtask_id": "run-1:1"}]}}
    yield {"__interrupt__": (Interrupt(value=_INTERRUPT_PAYLOAD),)}


async def test_interrupt_emits_waiting_frame_then_done():
    """正向：挂起 ⇒ hitl.waiting 帧 + done(status=waiting_approval)，**不是** error。"""
    frames = await _frames(
        iter_lg_rag_sse(
            query="复合问题",
            mode="supervisor",
            thread_id="th-wait",
            astream_fn=_astream_with_interrupt,
        )
    )
    types = [f.get("event_type") for f in frames]
    assert "hitl.waiting" in types, f"挂起了却没有等待帧：{types}"
    assert "error" not in types, "把'在等人批'报成了错误"

    waiting = _one_of(frames, "hitl.waiting")
    assert waiting["payload"]["requests"][0]["subtask_id"] == "run-1:2"
    assert waiting["payload"]["run_id"] == "run-1"
    assert waiting["payload"]["unpersisted"] is False

    done = _one_of(frames, "done")
    assert done is not None
    assert done["payload"]["status"] == "waiting_approval"


async def _astream_plain(_query: str, *, thread_id: str = "t", **_kw):
    yield {"aggregator": {"messages": []}}


async def test_no_interrupt_has_no_waiting_frame_control():
    """反向对照：正常跑完不许发等待帧（否则"一律等待授权"也绿）。"""
    frames = await _frames(
        iter_lg_rag_sse(
            query="简单问题",
            mode="supervisor",
            thread_id="th-plain",
            astream_fn=_astream_plain,
        )
    )
    assert _one_of(frames, "hitl.waiting") is None
    done = _one_of(frames, "done")
    assert done is not None
    assert done["payload"].get("status") != "waiting_approval"


async def test_unpersisted_flag_is_carried_to_the_waiting_frame():
    """未落库必须带出来：人在等一个**不存在的**审批，
    界面上却跟"正在审批中"长得一模一样。"""
    payload = {**_INTERRUPT_PAYLOAD, "unpersisted": True}

    async def _astream(_query: str, *, thread_id: str = "t", **_kw):
        yield {"__interrupt__": (Interrupt(value=payload),)}

    frames = await _frames(
        iter_lg_rag_sse(
            query="复合问题",
            mode="supervisor",
            thread_id="th-unpersisted",
            astream_fn=_astream,
        )
    )
    waiting = _one_of(frames, "hitl.waiting")
    assert waiting is not None
    assert waiting["payload"]["unpersisted"] is True


# ---------------------------------------------------------------------------
# 2 · checkpointer 必须真的传进 astream（且在流期间持有）
# ---------------------------------------------------------------------------


class _Sentinel:
    pass


async def test_checkpointer_is_forwarded_to_astream():
    """正向：调用方给了 checkpointer ⇒ 必须传下去。

    不传的话图照样跑，但 checkpoint 落在**另一个** saver 里 ——
    下一次请求找不到挂起点，恢复静默失败。这类 bug 单测跑图永远抓不到。
    """
    seen: dict[str, Any] = {}
    sentinel = _Sentinel()

    async def _astream(_query: str, *, thread_id: str = "t", **kw):
        seen.update(kw)
        yield {"aggregator": {"messages": []}}

    await _frames(
        iter_lg_rag_sse(
            query="q",
            mode="supervisor",
            thread_id="th-cp",
            astream_fn=_astream,
            checkpointer=sentinel,
        )
    )
    assert seen.get("checkpointer") is sentinel, f"checkpointer 没传下去：{seen}"


async def test_no_checkpointer_is_not_forwarded_control():
    """反向对照：没给就不传（测试替身是 ``**kw`` 形态，不传才是对的）。"""
    seen: dict[str, Any] = {}

    async def _astream(_query: str, *, thread_id: str = "t", **kw):
        seen.update(kw)
        yield {"aggregator": {"messages": []}}

    await _frames(
        iter_lg_rag_sse(
            query="q",
            mode="supervisor",
            thread_id="th-nocp",
            astream_fn=_astream,
        )
    )
    assert "checkpointer" not in seen


async def test_sse_holds_pg_saver_for_the_whole_stream(monkeypatch):
    """开了开关 ⇒ SSE 自己打开 PG saver 并交给 astream。

    这条守的是"invoke 落盘了、stream 没落盘" —— 两边读不同开关的话，
    人从 SSE 入口触发的挂起永远恢复不了，而从 invoke 入口的能恢复。
    """
    monkeypatch.setenv("LG_RAG_HTTP_CHECKPOINTER", "postgres")
    sentinel = _Sentinel()
    entered = {"setup": None}

    @asynccontextmanager
    async def _fake_saver(*, setup: bool = False):
        entered["setup"] = setup
        yield sentinel

    seen: dict[str, Any] = {}

    async def _astream(_query: str, *, thread_id: str = "t", **kw):
        seen.update(kw)
        yield {"aggregator": {"messages": []}}

    # Wave B：PG saver 由 run_worker 持有（原 sse_stream 已迁）
    with patch("app.ops.lg_rag.run_worker.apostgres_saver", new=_fake_saver):
        await _frames(
            iter_lg_rag_sse(
                query="q",
                mode="supervisor",
                thread_id="th-pg",
                astream_fn=_astream,
            )
        )
    assert entered["setup"] is True
    assert seen.get("checkpointer") is sentinel


async def test_sse_does_not_open_pg_saver_when_explicitly_off(monkeypatch):
    """反向对照：显式关（空值回退口）⇒ 不开 PG saver。

    P0' T3 起默认开（unset=postgres），此用例验的是**回退口有效**：
    空值明确落回内存 saver。"""
    monkeypatch.setenv("LG_RAG_HTTP_CHECKPOINTER", "")
    opened = {"n": 0}

    @asynccontextmanager
    async def _fake_saver(*, setup: bool = False):
        opened["n"] += 1
        yield _Sentinel()

    async def _astream(_query: str, *, thread_id: str = "t", **kw):
        yield {"aggregator": {"messages": []}}

    with patch("app.ops.lg_rag.run_worker.apostgres_saver", new=_fake_saver):
        await _frames(
            iter_lg_rag_sse(
                query="q",
                mode="supervisor",
                thread_id="th-nopg",
                astream_fn=_astream,
            )
        )
    assert opened["n"] == 0


async def test_basic_mode_never_opens_pg_saver(monkeypatch):
    """反向对照：basic/router 图没有 observe ⇒ 不会挂起 ⇒ 不需要 PG saver。"""
    monkeypatch.setenv("LG_RAG_HTTP_CHECKPOINTER", "postgres")
    opened = {"n": 0}

    @asynccontextmanager
    async def _fake_saver(*, setup: bool = False):
        opened["n"] += 1
        yield _Sentinel()

    async def _astream(_query: str, *, thread_id: str = "t", **kw):
        yield {"rag": {"messages": []}}

    with patch("app.ops.lg_rag.run_worker.apostgres_saver", new=_fake_saver):
        await _frames(
            iter_lg_rag_sse(
                query="q",
                mode="basic",
                thread_id="th-basic",
                astream_fn=_astream,
            )
        )
    assert opened["n"] == 0
