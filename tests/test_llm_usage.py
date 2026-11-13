"""llm-layer-hardening D4：usage 按 run_id 聚合落表（ops_llm_usage）。

纪律对拍（task 钉死契约）：
- 一次 chat run（answer+grader 两次调用、fake usage 末帧）→ 两行同 run_id，
  task_type 分别 answer/grader；按 run_id 聚合查询返回合计
- lg_rag run（hex run_id）落行 surface=lg_rag，与 chat 行可区分查询
- provider 无 usage 末帧 → 无行（不写 0 假账）
- 落表路径抛错 → answer 正常返回 + log/计数断言（不挡主答）
- run 上下文缺失 → run_id=NULL · surface=background
"""

from __future__ import annotations

import logging
import uuid

import httpx
import pytest
from sqlalchemy import delete, func, select

from app.db.models import OpsLlmUsage
from app.db.session import AsyncSessionLocal
from app.llm import usage as llm_usage
from app.llm.providers.siliconflow import SiliconFlowProvider
from app.llm.schema import LlmMessage
from tests.conftest import DB_AVAILABLE

_DB_SKIP = pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL unavailable")


def _usage_lines(prompt: int, completion: int, cached: int = 0) -> list[str]:
    usage = (
        f'{{"prompt_tokens": {prompt}, "completion_tokens": {completion}, '
        f'"prompt_cache_hit_tokens": {cached}}}'
    )
    return [
        'data: {"choices":[{"delta":{"content":"Answer"}}]}',
        f'data: {{"choices":[],"usage":{usage}}}',
        "data: [DONE]",
    ]


class _FakeResp:
    def __init__(self, lines: list[str]) -> None:
        self.status_code = 200
        self._lines = lines

    async def aread(self):
        return b""

    async def aiter_lines(self):
        for line in self._lines:
            yield line

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class _FakeClient:
    def __init__(self, lines: list[str]) -> None:
        self._lines = lines

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def stream(self, *args, **kwargs):
        return _FakeResp(self._lines)


@pytest.fixture
async def _clean_usage():
    async with AsyncSessionLocal() as db:
        await db.execute(delete(OpsLlmUsage))
        await db.commit()
    yield
    async with AsyncSessionLocal() as db:
        await db.execute(delete(OpsLlmUsage))
        await db.commit()


async def _rows_for(run_id: str) -> list[OpsLlmUsage]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(OpsLlmUsage).where(OpsLlmUsage.run_id == run_id))
        return list(result.scalars().all())


@_DB_SKIP
class TestUsagePersist:
    async def test_chat_run_two_calls_same_run_id(self, monkeypatch, _clean_usage):
        """answer+grader 两次调用同 run_id；tokens 与 fake 一致；聚合可查。"""
        run_id = str(uuid.uuid4())
        provider = SiliconFlowProvider(api_key="test-key")

        monkeypatch.setattr(
            httpx, "AsyncClient", lambda *a, **k: _FakeClient(_usage_lines(11, 7, 3))
        )
        with llm_usage.use_run_context(run_id=run_id, surface="chat", task_type="answer"):
            answer = await provider.complete([LlmMessage(role="user", content="hi")])
        assert answer == "Answer"

        monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _FakeClient(_usage_lines(5, 2)))
        with llm_usage.use_run_context(run_id=run_id, surface="chat", task_type="grader"):
            await provider.complete([LlmMessage(role="user", content="grade")])

        rows = await _rows_for(run_id)
        assert len(rows) == 2
        by_task = {r.task_type: r for r in rows}
        assert set(by_task) == {"answer", "grader"}
        assert by_task["answer"].prompt_tokens == 11
        assert by_task["answer"].completion_tokens == 7
        assert by_task["answer"].cached_input_tokens == 3
        assert by_task["answer"].provider == "siliconflow"
        assert by_task["answer"].surface == "chat"
        assert by_task["answer"].attempts == 1
        assert by_task["grader"].prompt_tokens == 5

        # 按 run_id 聚合查询返回合计
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(
                    func.sum(OpsLlmUsage.prompt_tokens),
                    func.sum(OpsLlmUsage.completion_tokens),
                ).where(OpsLlmUsage.run_id == run_id)
            )
            total_prompt, total_completion = result.one()
        assert (total_prompt, total_completion) == (16, 9)

    async def test_lg_rag_surface_distinguishable(self, monkeypatch, _clean_usage):
        """lg_rag run（hex run_id）落行 surface=lg_rag，与 chat 行可区分查询。"""
        hex_run_id = uuid.uuid4().hex
        monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _FakeClient(_usage_lines(3, 1)))
        provider = SiliconFlowProvider(api_key="test-key")
        with llm_usage.use_run_context(run_id=hex_run_id, surface="lg_rag"):
            await provider.complete([LlmMessage(role="user", content="hi")])

        rows = await _rows_for(hex_run_id)
        assert len(rows) == 1
        assert rows[0].surface == "lg_rag"
        assert rows[0].run_id == hex_run_id

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(func.count()).select_from(OpsLlmUsage).where(OpsLlmUsage.surface == "lg_rag")
            )
            assert result.scalar_one() == 1

    async def test_no_usage_frame_no_row(self, monkeypatch, _clean_usage):
        """provider 未回 usage 末帧 → 无行（非 0 假账）。"""
        run_id = str(uuid.uuid4())
        lines = ['data: {"choices":[{"delta":{"content":"x"}}]}', "data: [DONE]"]
        monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _FakeClient(lines))
        provider = SiliconFlowProvider(api_key="test-key")
        with llm_usage.use_run_context(run_id=run_id, surface="chat", task_type="answer"):
            answer = await provider.complete([LlmMessage(role="user", content="hi")])
        assert answer == "x"
        assert await _rows_for(run_id) == []

    async def test_persist_failure_does_not_block_answer(self, monkeypatch, _clean_usage, caplog):
        """落表路径抛错（fake session 故障）→ answer 正常返回 + log/计数断言。"""
        run_id = str(uuid.uuid4())

        class _BrokenSession:
            async def __aenter__(self):
                raise RuntimeError("db down")

            async def __aexit__(self, *args):
                pass

        monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _FakeClient(_usage_lines(2, 1)))
        monkeypatch.setattr("app.db.session.AsyncSessionLocal", lambda: _BrokenSession())
        provider = SiliconFlowProvider(api_key="test-key")
        with (
            caplog.at_level(logging.WARNING, logger="app.llm.usage"),
            llm_usage.use_run_context(run_id=run_id, surface="chat", task_type="answer"),
        ):
            answer = await provider.complete([LlmMessage(role="user", content="hi")])
        # 不挡主答
        assert answer == "Answer"
        # 不静默声称已记账：log + 计数可见
        assert llm_usage.persist_failure_count() >= 1
        assert any("ops_llm_usage persist failed" in r.message for r in caplog.records)
        assert await _rows_for(run_id) == []

    async def test_missing_context_background_surface(self, monkeypatch, _clean_usage):
        """无 ContextVar 的调用点：run_id=NULL · surface=background，不阻断记账。"""
        monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _FakeClient(_usage_lines(4, 2)))
        provider = SiliconFlowProvider(api_key="test-key")
        await provider.complete([LlmMessage(role="user", content="hi")])

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OpsLlmUsage).where(OpsLlmUsage.surface == "background")
            )
            rows = list(result.scalars().all())
        assert len(rows) == 1
        assert rows[0].run_id is None
        assert rows[0].prompt_tokens == 4

