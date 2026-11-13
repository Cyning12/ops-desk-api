"""llm-layer-hardening D3：任务类型分层路由（TASK_TIER_MODELS + env 覆盖）。

解析序钉死：显式 model= > OPS_LLM_TIER_<TASK>_MODEL > 档默认 > settings.ops_llm_model
（grader 档并入 RAG_GRADER_MODEL 覆盖链）；非法档/未知 task 回退默认 + warning；
不显式分档的调用点 = 现网逐字节一致。
"""

from __future__ import annotations

import logging

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
