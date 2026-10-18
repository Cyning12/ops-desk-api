"""llm-layer-hardening D3：任务类型分层路由（TASK_TIER_MODELS + env 覆盖）。

解析序钉死：显式 model= > OPS_LLM_TIER_<TASK>_MODEL > 档默认 > settings.ops_llm_model
（grader 档并入 RAG_GRADER_MODEL 覆盖链）；非法档/未知 task 回退默认 + warning；
不显式分档的调用点 = 现网逐字节一致。
"""

from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from app.llm.model_catalog import resolve_task_model

_TIER_ENVS = [
    "OPS_LLM_TIER_ANSWER_MODEL",
    "OPS_LLM_TIER_GRADER_MODEL",
    "OPS_LLM_TIER_EXTRACT_MODEL",
    "OPS_LLM_TIER_STRUCTURED_MODEL",
    "RAG_GRADER_MODEL",
]


@pytest.fixture(autouse=True)
def _clean_tier_envs(monkeypatch):
    for name in _TIER_ENVS:
        monkeypatch.delenv(name, raising=False)


class TestResolveTaskModel:
    def test_grader_tier_default_matches_legacy(self):
        """无 env：grader 档默认 = 现网 RAG_GRADER_MODEL 默认值（逐字节一致）。"""
        model, source = resolve_task_model("grader")
        assert model == "Qwen/Qwen3.6-27B"
        assert source == "tier_default"

    def test_env_tier_override(self, monkeypatch):
        """OPS_LLM_TIER_GRADER_MODEL 覆盖生效且优先于 RAG_GRADER_MODEL。"""
        monkeypatch.setenv("RAG_GRADER_MODEL", "legacy/grader-x")
        monkeypatch.setenv("OPS_LLM_TIER_GRADER_MODEL", "deepseek-ai/DeepSeek-V4-Pro")
        model, source = resolve_task_model("grader")
        assert model == "deepseek-ai/DeepSeek-V4-Pro"
        assert source == "env_tier"

    def test_legacy_rag_grader_model_still_works(self, monkeypatch):
        """RAG_GRADER_MODEL 并入 grader 档覆盖链（现网配置不破坏；直读不校验目录）。"""
        monkeypatch.setenv("RAG_GRADER_MODEL", "legacy/grader-x")
        model, source = resolve_task_model("grader")
        assert model == "legacy/grader-x"
        assert source == "rag_grader_model"

    def test_explicit_model_wins(self, monkeypatch):
        monkeypatch.setenv("OPS_LLM_TIER_GRADER_MODEL", "deepseek-ai/DeepSeek-V4-Pro")
        model, source = resolve_task_model("grader", "caller/explicit-m")
        assert model == "caller/explicit-m"
        assert source == "explicit"

    def test_invalid_tier_env_falls_back_with_warning(self, monkeypatch, caplog):
        """档指向不存在模型 → 回退档默认 + warning，不炸请求。"""
        monkeypatch.setenv("OPS_LLM_TIER_GRADER_MODEL", "no/such-model-anywhere")
        with caplog.at_level(logging.WARNING, logger="app.llm.model_catalog"):
            model, source = resolve_task_model("grader")
        assert model == "Qwen/Qwen3.6-27B"  # 回退档默认
        assert source == "tier_default"
        assert any("OPS_LLM_TIER_GRADER_MODEL" in r.message for r in caplog.records)

    def test_unknown_task_falls_back_with_warning(self, caplog):
        with caplog.at_level(logging.WARNING, logger="app.llm.model_catalog"):
            model, source = resolve_task_model("summarize")
        assert model is None
        assert source == "unknown_task"
        assert any("unknown llm task_type" in r.message for r in caplog.records)

    @pytest.mark.parametrize("task", ["answer", "extract", "structured"])
    def test_other_tiers_default_none(self, task):
        """answer/extract/structured 档默认 None = 本层无意见（调用方沿用现网默认）。"""
        model, source = resolve_task_model(task)
        assert model is None
        assert source == "default"

    @pytest.mark.parametrize(
        "task, env_name",
        [
            ("answer", "OPS_LLM_TIER_ANSWER_MODEL"),
            ("extract", "OPS_LLM_TIER_EXTRACT_MODEL"),
            ("structured", "OPS_LLM_TIER_STRUCTURED_MODEL"),
        ],
    )
    def test_each_tier_env_independent(self, monkeypatch, task, env_name):
        monkeypatch.setenv(env_name, "deepseek-ai/DeepSeek-V4-Flash")
        model, source = resolve_task_model(task)
        assert model == "deepseek-ai/DeepSeek-V4-Flash"
        assert source == "env_tier"
        # 其它档不受影响
        assert resolve_task_model("grader")[0] == "Qwen/Qwen3.6-27B"


class TestAnswerNodeRouting:
    async def test_answer_node_default_byte_identical(self, monkeypatch):
        """未配置档：answer 模型解析 = 现网（state.model or settings.ops_llm_model）。"""
        from app.llm.providers.base import BaseProviderImpl
        from app.llm.schema import LlmChunk
        from app.ops.chat import nodes as chat_nodes
        from app.ops.chat.state import ChatState

        seen = {}

        class _Capture(BaseProviderImpl):
            async def complete_stream(self, messages, model=None):
                seen["model"] = model
                yield LlmChunk(content="ok")

        monkeypatch.setattr(chat_nodes, "get_llm_provider", lambda: _Capture())
        monkeypatch.setattr(chat_nodes.settings, "ops_llm_model", "global/default-m")

        state = ChatState(
            query="hi",
            session_id=None,
            run_id="r1",
            model=None,
            issue_context=[],
            pr_context=[],
            graph_context=None,
            intent="",
            answer="",
            history_turns=[],
            events=[],
        )
        await chat_nodes.answer_node(state)
        assert seen["model"] == "global/default-m"

        # 显式 model（请求级）优先于一切
        state2 = ChatState(
            query="hi",
            session_id=None,
            run_id="r2",
            model="req/explicit-m",
            issue_context=[],
            pr_context=[],
            graph_context=None,
            intent="",
            answer="",
            history_turns=[],
            events=[],
        )
        await chat_nodes.answer_node(state2)
        assert seen["model"] == "req/explicit-m"

    async def test_answer_node_tier_env_override(self, monkeypatch):
        """OPS_LLM_TIER_ANSWER_MODEL 覆盖全局默认；显式 model 仍优先。"""
        from app.llm.providers.base import BaseProviderImpl
        from app.llm.schema import LlmChunk
        from app.ops.chat import nodes as chat_nodes
        from app.ops.chat.state import ChatState

        seen = {}

        class _Capture(BaseProviderImpl):
            async def complete_stream(self, messages, model=None):
                seen["model"] = model
                yield LlmChunk(content="ok")

        monkeypatch.setattr(chat_nodes, "get_llm_provider", lambda: _Capture())
        monkeypatch.setattr(chat_nodes.settings, "ops_llm_model", "global/default-m")
        monkeypatch.setenv("OPS_LLM_TIER_ANSWER_MODEL", "deepseek-ai/DeepSeek-V4-Pro")

        state = ChatState(
            query="hi",
            session_id=None,
            run_id="r3",
            model=None,
            issue_context=[],
            pr_context=[],
            graph_context=None,
            intent="",
            answer="",
            history_turns=[],
            events=[],
        )
        await chat_nodes.answer_node(state)
        assert seen["model"] == "deepseek-ai/DeepSeek-V4-Pro"

    async def test_answer_node_route_span_metadata(self, monkeypatch):
        """span metadata 含 task → model 决策与档来源。"""
        from app.llm.providers.base import BaseProviderImpl
        from app.llm.schema import LlmChunk
        from app.ops.chat import nodes as chat_nodes
        from app.ops.chat.state import ChatState

        captured = []

        class _Capture(BaseProviderImpl):
            async def complete_stream(self, messages, model=None):
                yield LlmChunk(content="ok")

        monkeypatch.setattr(chat_nodes, "get_llm_provider", lambda: _Capture())
        monkeypatch.setattr(chat_nodes.settings, "ops_llm_model", "global/default-m")
        monkeypatch.setattr(
            chat_nodes, "update_current_span_metadata", lambda m: captured.append(m)
        )

        state = ChatState(
            query="hi",
            session_id=None,
            run_id="r4",
            model=None,
            issue_context=[],
            pr_context=[],
            graph_context=None,
            intent="",
            answer="",
            history_turns=[],
            events=[],
        )
        await chat_nodes.answer_node(state)
        route = next(m["llm_route"] for m in captured if "llm_route" in m)
        assert route == {
            "task_type": "answer",
            "model": "global/default-m",
            "source": "default",
        }


class TestGradeNodeRouting:
    def _state_with_chunk(self):
        from app.ops.chat.state import ChatState

        chunk = SimpleNamespace(
            id=1,
            source_type="doc",
            anchor="a1",
            content="doc-context: x\n\n证据正文",
            metadata={},
            source_id="s1",
            chunk_index=0,
        )
        return ChatState(
            query="q",
            session_id=None,
            run_id="rg1",
            model=None,
            issue_context=[],
            pr_context=[],
            graph_context=None,
            intent="",
            answer="",
            history_turns=[],
            events=[],
            retrieved=[chunk],
        )

    def _capture_provider(self, monkeypatch, seen):
        from app.llm.providers.base import BaseProviderImpl
        from app.llm.schema import LlmChunk
        from app.ops.chat import rag_nodes

        class _GraderCapture(BaseProviderImpl):
            async def complete(self, messages, model=None):
                return await self._complete_from_stream(messages, model=model)

            async def complete_stream(self, messages, model=None):
                seen["model"] = model
                yield LlmChunk(content='[{"chunk_id": 1, "relevance": "exact", "reason": "r"}]')

        monkeypatch.setattr(rag_nodes, "get_llm_provider", lambda name: _GraderCapture())

    async def test_grade_node_tier_default(self, monkeypatch):
        """grader 调用点声明 task_type=grader → 命中 grader 档默认（现网逐字节一致）。"""
        from app.ops.chat import rag_nodes

        seen = {}
        self._capture_provider(monkeypatch, seen)
        result = await rag_nodes.grade_node(self._state_with_chunk())
        assert seen["model"] == "Qwen/Qwen3.6-27B"
        assert result["gate_action"] == "answer"

    async def test_grade_node_env_tier_override(self, monkeypatch):
        from app.ops.chat import rag_nodes

        seen = {}
        self._capture_provider(monkeypatch, seen)
        monkeypatch.setenv("OPS_LLM_TIER_GRADER_MODEL", "deepseek-ai/DeepSeek-V4-Pro")
        await rag_nodes.grade_node(self._state_with_chunk())
        assert seen["model"] == "deepseek-ai/DeepSeek-V4-Pro"

    async def test_grade_node_legacy_env_compat(self, monkeypatch):
        """既有 RAG_GRADER_MODEL 配置不破坏（并入覆盖链）。"""
        from app.ops.chat import rag_nodes

        seen = {}
        self._capture_provider(monkeypatch, seen)
        monkeypatch.setenv("RAG_GRADER_MODEL", "legacy/grader-x")
        await rag_nodes.grade_node(self._state_with_chunk())
        assert seen["model"] == "legacy/grader-x"

    async def test_grade_node_route_span_metadata(self, monkeypatch):
        from app.ops.chat import rag_nodes

        seen = {}
        self._capture_provider(monkeypatch, seen)
        captured = []
        monkeypatch.setattr(rag_nodes, "update_current_span_metadata", lambda m: captured.append(m))
        await rag_nodes.grade_node(self._state_with_chunk())
        route = next(m["llm_route"] for m in captured if "llm_route" in m)
        assert route == {
            "task_type": "grader",
            "model": "Qwen/Qwen3.6-27B",
            "source": "tier_default",
        }


class TestStructuredTier:
    async def test_structured_default_byte_identical(self):
        """未配置档：acomplete_structured 模型解析 = 现网（model=None 透传）。"""
        from pydantic import BaseModel

        from app.llm.schema import BaseProvider
        from app.ops.structured_output.complete import acomplete_structured

        seen = {}

        class _P(BaseProvider):
            async def complete(self, messages, model=None):
                seen["model"] = model
                return '{"x": 1}'

        class _S(BaseModel):
            x: int

        result = await acomplete_structured(system="s", user="u", schema=_S, _provider=_P())
        assert result.x == 1
        assert seen["model"] is None  # provider 注入路径：现网语义不动

    async def test_structured_tier_env_override(self, monkeypatch):
        """OPS_LLM_TIER_STRUCTURED_MODEL 对 get_llm_provider 路径生效。"""
        from pydantic import BaseModel

        from app.llm.schema import BaseProvider
        from app.ops.structured_output import complete as so_complete

        seen = {}

        class _P(BaseProvider):
            async def complete(self, messages, model=None):
                seen["model"] = model
                return '{"x": 1}'

        class _S(BaseModel):
            x: int

        monkeypatch.setattr(so_complete, "get_llm_provider", lambda name: _P())
        monkeypatch.setenv("OPS_LLM_TIER_STRUCTURED_MODEL", "deepseek-ai/DeepSeek-V4-Flash")
        result = await so_complete.acomplete_structured(system="s", user="u", schema=_S)
        assert result.x == 1
        assert seen["model"] == "deepseek-ai/DeepSeek-V4-Flash"
