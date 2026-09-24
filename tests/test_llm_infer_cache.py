"""host-v1-llm-factory-closure D3/D4：推理缓存 + 声明式降级集中守护。

断言面（task 验收映射）：
- D3（Q2 只缓存 plan·参数 · 终答 answer 不缓存 · 默认关零 diff）：
  命中跳过 LLM（mock 计数）· 失效三触发（模型档变更 / prompt 版本 bump /
  catalog 版本·可见集哈希变）· 终答不缓存 · off 零 diff。
  **变异检验②锚点**：摘除 prompt 版本入键（make_key 的 prompt_version
  字段）→ test_prompt_version_bump_invalidates 必挂。
- D4 集中性守护：调用点零硬编码降级模型（grep 守护 · 降级链唯一声明面
  在 model_catalog · 唯一消费面在 providers/base.py 检查点 walker）。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.llm import infer_cache, model_catalog
from app.llm.infer_cache import make_key, use_infer_cache_context
from app.llm.providers.base import BaseProviderImpl
from app.llm.schema import LlmChunk
from app.llm.usage import use_run_context

_CACHE_ENVS = [
    "OPS_LLM_INFER_CACHE_ENABLED",
    "OPS_LLM_INFER_CACHE_MAX_ENTRIES",
    "OPS_LLM_INFER_CACHE_TTL_SECONDS",
]
_BUDGET_ENVS = [
    "OPS_LLM_BUDGET_SESSION_TOKENS",
    "OPS_LLM_BUDGET_TASK_TOKENS",
    "OPS_LLM_BUDGET_MODE",
    "OPS_LLM_BUDGET_ENFORCE_TASKS",
]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_APP_DIR = _REPO_ROOT / "app"


@pytest.fixture(autouse=True)
def _clean_cache_state(monkeypatch):
    for name in [*_CACHE_ENVS, *_BUDGET_ENVS]:
        monkeypatch.delenv(name, raising=False)
    infer_cache.reset()
    yield
    infer_cache.reset()


class _CountingProvider(BaseProviderImpl):
    """complete 走真 _complete_from_stream 缓存接线；llm_calls 记真实出网次数。"""

    PROVIDER_NAME = "fake-cache"

    def __init__(self, text: str = "{\"plan\": []}") -> None:
        self.llm_calls = 0
        self._text = text

    async def complete(self, messages, model=None):
        return await self._complete_from_stream(messages, model=model)

    async def complete_stream(self, messages, model=None):
        self.llm_calls += 1
        yield LlmChunk(content=self._text)


def _msgs(text: str = "same input"):
    from app.llm.schema import LlmMessage

    return [LlmMessage(role="user", content=text)]

class TestCacheHitSkipsLlm:
    """D3 · 命中跳过 LLM（mock 计数断言）。"""

    async def test_hit_skips_second_llm_call(self, monkeypatch):
        monkeypatch.setenv("OPS_LLM_INFER_CACHE_ENABLED", "true")
        provider = _CountingProvider()
        with use_run_context(run_id="r1", task_type="structured"):
            first = await provider.complete(_msgs(), model="m/structured")
            second = await provider.complete(_msgs(), model="m/structured")
        assert first == second == "{\"plan\": []}"
        assert provider.llm_calls == 1, "第二次同键调用应命中缓存 · 零出网"
        snap = infer_cache.snapshot()
        assert snap["hits"] == 1
        assert snap["misses"] == 1

    async def test_default_off_zero_diff(self):
        """默认关：每次调用都出网（零 diff）· 缓存面零条目。"""
        provider = _CountingProvider()
        with use_run_context(run_id="r1", task_type="structured"):
            await provider.complete(_msgs(), model="m/structured")
            await provider.complete(_msgs(), model="m/structured")
        assert provider.llm_calls == 2
        assert infer_cache.snapshot()["size"] == 0

    async def test_answer_tier_never_cached(self, monkeypatch):
        """Q2 锁死：终答 answer 不缓存（时效性证据 · 缓存=静默陈旧）。"""
        monkeypatch.setenv("OPS_LLM_INFER_CACHE_ENABLED", "true")
        provider = _CountingProvider(text="final answer")
        with use_run_context(run_id="r1", surface="chat", task_type="answer"):
            await provider.complete(_msgs(), model="m/answer")
            await provider.complete(_msgs(), model="m/answer")
        assert provider.llm_calls == 2, "answer 档永远直连 LLM · 不入缓存"
        assert infer_cache.snapshot()["size"] == 0

    async def test_different_input_misses(self, monkeypatch):
        monkeypatch.setenv("OPS_LLM_INFER_CACHE_ENABLED", "true")
        provider = _CountingProvider()
        with use_run_context(run_id="r1", task_type="structured"):
            await provider.complete(_msgs("input A"), model="m/structured")
            await provider.complete(_msgs("input B"), model="m/structured")
        assert provider.llm_calls == 2

class TestCacheInvalidation:
    """D3 · 失效三触发（版本入键 · 旧条目自然 miss）。"""

    async def test_prompt_version_bump_invalidates(self, monkeypatch):
        """变异检验②锚点：prompt 版本入键 —— bump → 自然 miss · 回退旧版本 → 命中。"""
        monkeypatch.setenv("OPS_LLM_INFER_CACHE_ENABLED", "true")
        provider = _CountingProvider()
        with use_run_context(run_id="r1", task_type="structured"):
            with use_infer_cache_context(prompt_version="plan-v1"):
                await provider.complete(_msgs(), model="m/structured")
                assert provider.llm_calls == 1
                await provider.complete(_msgs(), model="m/structured")
                assert provider.llm_calls == 1, "同版本同输入应命中"
            with use_infer_cache_context(prompt_version="plan-v2"):
                await provider.complete(_msgs(), model="m/structured")
                assert provider.llm_calls == 2, "prompt 版本 bump 后旧键自然 miss"
            with use_infer_cache_context(prompt_version="plan-v1"):
                await provider.complete(_msgs(), model="m/structured")
                assert provider.llm_calls == 2, "回到旧版本键仍在（版本即键）"

    async def test_catalog_fingerprint_change_invalidates(self, monkeypatch):
        """FP-2：plan 类键含 catalog 版本/可见集哈希 —— 目录变 → 自然 miss。"""
        monkeypatch.setenv("OPS_LLM_INFER_CACHE_ENABLED", "true")
        provider = _CountingProvider()
        with use_run_context(run_id="r1", task_type="structured"):
            with use_infer_cache_context(catalog_fingerprint="catalog@a1"):
                await provider.complete(_msgs(), model="m/structured")
                assert provider.llm_calls == 1
            with use_infer_cache_context(catalog_fingerprint="catalog@b2"):
                await provider.complete(_msgs(), model="m/structured")
                assert provider.llm_calls == 2, "能力目录指纹变 → 旧 plan 自然失效"

    async def test_model_tier_change_invalidates(self, monkeypatch):
        monkeypatch.setenv("OPS_LLM_INFER_CACHE_ENABLED", "true")
        provider = _CountingProvider()
        with use_run_context(run_id="r1", task_type="structured"):
            await provider.complete(_msgs(), model="m/structured-a")
            await provider.complete(_msgs(), model="m/structured-b")
        assert provider.llm_calls == 2, "模型档 id 入键 · 换档自然 miss"

    async def test_declared_prompt_version_default_in_key(self, monkeypatch):
        """未注入版本时用 PROMPT_VERSIONS 集中声明默认（bump 声明 = 全键失效）。"""
        monkeypatch.setenv("OPS_LLM_INFER_CACHE_ENABLED", "true")
        provider = _CountingProvider()
        with use_run_context(run_id="r1", task_type="structured"):
            await provider.complete(_msgs(), model="m/structured")
            assert provider.llm_calls == 1
            await provider.complete(_msgs(), model="m/structured")
            assert provider.llm_calls == 1
            monkeypatch.setitem(infer_cache.PROMPT_VERSIONS, "structured", "v2")
            await provider.complete(_msgs(), model="m/structured")
            assert provider.llm_calls == 2, "集中声明 bump → 全键自然 miss"

class TestCacheMechanics:
    """D3 · TTL / LRU / 键形态（不记内容）。"""

    def test_ttl_expiry(self, monkeypatch):
        monkeypatch.setenv("OPS_LLM_INFER_CACHE_TTL_SECONDS", "60")
        key = make_key("structured", "m/x", input_parts=["in"])
        infer_cache.put(key, "value", now=1000.0)
        assert infer_cache.get(key, now=1059.0) == "value"
        assert infer_cache.get(key, now=1061.0) is None, "TTL 到期自然 miss"

    def test_invalid_ttl_falls_back_to_default(self, monkeypatch):
        monkeypatch.setenv("OPS_LLM_INFER_CACHE_TTL_SECONDS", "abc")
        assert infer_cache.cache_ttl_seconds() == 3600
        monkeypatch.setenv("OPS_LLM_INFER_CACHE_MAX_ENTRIES", "-3")
        assert infer_cache.cache_max_entries() == 256

    def test_lru_eviction(self, monkeypatch):
        monkeypatch.setenv("OPS_LLM_INFER_CACHE_MAX_ENTRIES", "2")
        k1 = make_key("structured", "m/x", input_parts=["a"])
        k2 = make_key("structured", "m/x", input_parts=["b"])
        k3 = make_key("structured", "m/x", input_parts=["c"])
        infer_cache.put(k1, "1", now=0.0)
        infer_cache.put(k2, "2", now=0.0)
        infer_cache.put(k3, "3", now=0.0)
        assert infer_cache.get(k1, now=1.0) is None, "最老条目应被 LRU 淘汰"
        assert infer_cache.get(k3, now=1.0) == "3"
        assert infer_cache.snapshot()["evicted"] == 1

    def test_key_is_hash_no_plaintext(self):
        key = make_key(
            "structured", "m/x", input_parts=["敏感原文"], prompt_version="v1"
        )
        assert "敏感原文" not in key
        assert len(key) == 64  # sha256 hex

    def test_snapshot_marks_process_local_scope(self):
        snap = infer_cache.snapshot()
        assert snap["scope"] == "process-local"
        assert snap["enabled"] is False

class TestDeclarativeDegradeGuard:
    """D4 · 集中性守护：调用点零硬编码降级模型（grep 守护断言）。

    降级链唯一声明面 = app/llm/model_catalog.py（TASK_TIER_FALLBACKS）；
    唯一消费面 = app/llm/providers/base.py（预算检查点 walker）。
    任何调用点写死降级模型 / 私接 resolve_fallback_chain → 本类断言必挂。
    """

    @staticmethod
    def _app_sources():
        return sorted(_APP_DIR.rglob("*.py"))

    def test_no_hardcoded_degrade_models_outside_catalog(self):
        chain_models = {
            entry
            for chain in model_catalog.TASK_TIER_FALLBACKS.values()
            for entry in chain
            if not entry.startswith(model_catalog.RULE_TIER_PREFIX)
        }
        assert chain_models, "守护前提：catalog 至少声明一个模型档降级目标"
        offenders = []
        for path in self._app_sources():
            if path.name == "model_catalog.py":
                continue  # 唯一声明面豁免
            text = path.read_text(encoding="utf-8")
            for model in chain_models:
                if model in text:
                    offenders.append(f"{path.relative_to(_REPO_ROOT)}: {model}")
        assert not offenders, (
            "调用点硬编码降级模型（降级目标只能由 catalog 声明）：" + "; ".join(offenders)
        )

    def test_resolve_fallback_chain_single_consumer(self):
        consumers = []
        for path in self._app_sources():
            if path.name == "model_catalog.py":
                continue
            if "resolve_fallback_chain" in path.read_text(encoding="utf-8"):
                consumers.append(str(path.relative_to(_REPO_ROOT)))
        assert consumers == ["app/llm/providers/base.py"], (
            f"降级链解析只能由统一入口检查点消费，散落消费面：{consumers}"
        )
