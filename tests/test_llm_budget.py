"""host-v1-llm-factory-closure D1/D2/D4/D5：预算检查点 + 耗尽降级链 + 链声明 + 指标口径。

断言面（task 验收映射）：
- D1：两级声明解析（默认 0 不限 · 非法回退 0）· 预估保守下限 · 调用后真实记账
  覆盖 · 三档（off 零行为 / observe would_block 不拦 / enforce 超限下一次调用前
  拦截不截进行中流）· 白名单默认空=全观测。
- D2（防假降级 U3 · **变异检验①锚点**：摘除 degraded 标记 → 本文件标记断言
  必挂）：耗尽→小模型档带 degraded=true+degrade_reason+degrade_chain（ok=True
  也可能降级）· 链末端 ok=False+degraded 不伪造成功 · 无声明档明确失败。
- D4：resolve_fallback_chain 链解析（非法档过滤+warning · 去环 · 链长≤3）。
- D5：Cost per Successful Task 聚合口径 · 缺单价 unknown 不伪造 0。
- **变异检验③锚点**：检查点恒放行 → enforce 拦截断言必挂。
"""

from __future__ import annotations

import logging

import pytest

from app.llm import budget as llm_budget
from app.llm import model_catalog
from app.llm.budget import (
    BudgetVerdict,
    UsageCostRow,
    check_budget,
    cost_per_successful_task,
    estimate_tokens,
)
from app.llm.model_catalog import estimate_cost, resolve_fallback_chain
from app.llm.providers.base import BaseProviderImpl
from app.llm.schema import LlmChunk, LlmProviderError
from app.llm.usage import LlmRunContext, use_run_context

_BUDGET_ENVS = [
    "OPS_LLM_BUDGET_SESSION_TOKENS",
    "OPS_LLM_BUDGET_TASK_TOKENS",
    "OPS_LLM_BUDGET_MODE",
    "OPS_LLM_BUDGET_ENFORCE_TASKS",
]


@pytest.fixture(autouse=True)
def _clean_budget_state(monkeypatch):
    for name in _BUDGET_ENVS:
        monkeypatch.delenv(name, raising=False)
    llm_budget.reset()
    yield
    llm_budget.reset()


class _FakeProvider(BaseProviderImpl):
    """记录每次真实出网调用的 model；末帧带 usage（走真记账钩点）。"""

    PROVIDER_NAME = "fake-budget"

    def __init__(self) -> None:
        self.calls: list[str | None] = []

    async def complete_stream(self, messages, model=None):
        self.calls.append(model)
        yield LlmChunk(content=f"ok:{model}")
        yield LlmChunk(content="", meta={"usage": {"prompt_tokens": 10, "completion_tokens": 5}})


class _FlashFailsProvider(BaseProviderImpl):
    """小模型档首 chunk 前失败（retryable=False 免退避）→ walker 应走下一档。"""

    PROVIDER_NAME = "fake-flaky"

    async def complete_stream(self, messages, model=None):
        if model == "deepseek-ai/DeepSeek-V4-Flash":
            raise LlmProviderError("flash down", retryable=False)
        yield LlmChunk(content=f"ok:{model}")


async def _collect(provider, messages, *, model=None):
    chunks = []
    async for chunk in provider.complete_stream(messages, model=model):
        chunks.append(chunk)
    return chunks


def _degraded_chunks(chunks):
    return [c for c in chunks if (c.meta or {}).get("degraded") is True]


class TestBudgetDeclaration:
    """D1 · 两级声明解析。"""

    def test_default_zero_unlimited(self):
        assert llm_budget.limits() == {"session_tokens": 0, "task_tokens": 0}

    def test_invalid_and_negative_fall_back_to_zero(self, monkeypatch):
        monkeypatch.setenv("OPS_LLM_BUDGET_SESSION_TOKENS", "abc")
        monkeypatch.setenv("OPS_LLM_BUDGET_TASK_TOKENS", "-50")
        assert llm_budget.limits() == {"session_tokens": 0, "task_tokens": 0}

    def test_valid_values(self, monkeypatch):
        monkeypatch.setenv("OPS_LLM_BUDGET_SESSION_TOKENS", "100000")
        monkeypatch.setenv("OPS_LLM_BUDGET_TASK_TOKENS", "20000")
        assert llm_budget.limits() == {"session_tokens": 100000, "task_tokens": 20000}

    def test_mode_default_off_and_invalid_falls_back(self, monkeypatch):
        assert llm_budget.budget_mode() == "off"
        monkeypatch.setenv("OPS_LLM_BUDGET_MODE", "BANANA")
        assert llm_budget.budget_mode() == "off"

    def test_enforce_whitelist_default_empty_means_all_observe(self, monkeypatch):
        monkeypatch.setenv("OPS_LLM_BUDGET_MODE", "enforce")
        assert llm_budget.effective_mode("answer") == "observe"
        monkeypatch.setenv("OPS_LLM_BUDGET_ENFORCE_TASKS", "answer, grader")
        assert llm_budget.effective_mode("answer") == "enforce"
        assert llm_budget.effective_mode("grader") == "enforce"
        assert llm_budget.effective_mode("summary") == "observe"


class TestCheckpoint:
    """D1 · 检查点三档 + 预估下限 + 记账覆盖（变异检验③锚点：
    检查点恒放行 → test_enforce_blocks_next_call_before_invocation 必挂）。"""

    def test_off_zero_behavior(self, monkeypatch):
        monkeypatch.setenv("OPS_LLM_BUDGET_SESSION_TOKENS", "1")
        ctx = LlmRunContext(run_id="r1", task_type="answer")
        verdict = check_budget("answer", ctx=ctx)
        assert verdict.allowed is True
        assert verdict.mode == "off"
        assert verdict.would_block is False
        llm_budget.record_actual("answer", 9999, ctx=ctx)
        assert llm_budget.snapshot()["sessions"] == {}

    def test_observe_would_block_but_allows(self, monkeypatch):
        monkeypatch.setenv("OPS_LLM_BUDGET_MODE", "observe")
        monkeypatch.setenv("OPS_LLM_BUDGET_SESSION_TOKENS", "100")
        ctx = LlmRunContext(run_id="r1", task_type="answer")
        llm_budget.record_actual("answer", 100, ctx=ctx)
        verdict = check_budget("answer", ctx=ctx)
        assert verdict.allowed is True
        assert verdict.would_block is True
        assert verdict.reason == "budget_exhausted"
        assert llm_budget.snapshot()["would_block"] == 1

    def test_enforce_blocks_next_call_before_invocation(self, monkeypatch):
        """超限在下一次调用前拦截（预估已记账+下限 > 声明即拦 · 不截进行中流）。"""
        monkeypatch.setenv("OPS_LLM_BUDGET_MODE", "enforce")
        monkeypatch.setenv("OPS_LLM_BUDGET_ENFORCE_TASKS", "answer")
        monkeypatch.setenv("OPS_LLM_BUDGET_SESSION_TOKENS", "100")
        ctx = LlmRunContext(run_id="r1", task_type="answer")
        llm_budget.record_actual("answer", 100, ctx=ctx)
        verdict = check_budget("answer", ctx=ctx)
        assert verdict.allowed is False
        assert verdict.would_block is True
        assert verdict.reason == "budget_exhausted"
        assert verdict.session_used == 100
        assert llm_budget.snapshot()["blocked"] == 1

    def test_enforce_whitelist_task_isolation(self, monkeypatch):
        """白名单外 task 只观测不拦（FP-4 灰度防误伤）。"""
        monkeypatch.setenv("OPS_LLM_BUDGET_MODE", "enforce")
        monkeypatch.setenv("OPS_LLM_BUDGET_ENFORCE_TASKS", "grader")
        monkeypatch.setenv("OPS_LLM_BUDGET_SESSION_TOKENS", "100")
        ctx = LlmRunContext(run_id="r1", task_type="answer")
        llm_budget.record_actual("answer", 100, ctx=ctx)
        verdict = check_budget("answer", ctx=ctx)
        assert verdict.allowed is True
        assert verdict.would_block is True

    def test_task_level_budget_uses_five_tier_keys(self, monkeypatch):
        monkeypatch.setenv("OPS_LLM_BUDGET_MODE", "enforce")
        monkeypatch.setenv("OPS_LLM_BUDGET_ENFORCE_TASKS", "extract")
        monkeypatch.setenv("OPS_LLM_BUDGET_TASK_TOKENS", "100")
        ctx = LlmRunContext(run_id="r1", task_type="extract")
        llm_budget.record_actual("extract", 100, ctx=ctx)
        verdict = check_budget("extract", ctx=ctx)
        assert verdict.allowed is False
        assert verdict.task_used == 100
        # 未声明 task_type 的调用不受任务级约束（任务级键=五档）
        other = check_budget("not-a-tier", ctx=LlmRunContext(run_id="r9"))
        assert other.allowed is True
        assert other.task_limit == 0

    def test_estimate_is_conservative_lower_bound(self, monkeypatch):
        """预估 ≤ 实际（保守下限不拦截正常调用）；无样本用档级固定下限。"""
        monkeypatch.setenv("OPS_LLM_BUDGET_MODE", "observe")
        assert estimate_tokens("answer") == llm_budget.TIER_TOKEN_FLOOR["answer"]
        ctx = LlmRunContext(run_id="r1", task_type="answer")
        llm_budget.record_actual("answer", 10000, ctx=ctx)
        estimated = estimate_tokens("answer")
        assert estimated <= 10000
        assert estimated >= llm_budget.TIER_TOKEN_FLOOR["answer"]

    def test_record_actual_overrides_estimate(self, monkeypatch):
        """调用后真实记账为准：session/task 计数按 usage 真值累计。"""
        monkeypatch.setenv("OPS_LLM_BUDGET_MODE", "observe")
        ctx = LlmRunContext(run_id="r1", task_type="grader")
        llm_budget.record_actual("grader", 777, ctx=ctx)
        llm_budget.record_actual("grader", 223, ctx=ctx)
        snap = llm_budget.snapshot()
        assert snap["sessions"]["r1"] == 1000
        assert snap["tasks"]["grader"] == 1000


class TestStreamingNotCutMidFlight:
    """D1 · 进行中流不截断：调用中超限不截流，超限在下一次调用前拦截。"""

    async def test_in_flight_stream_completes_then_next_call_degrades(self, monkeypatch):
        monkeypatch.setenv("OPS_LLM_BUDGET_MODE", "enforce")
        monkeypatch.setenv("OPS_LLM_BUDGET_ENFORCE_TASKS", "answer")
        # 首次预估 512 放行；真实记账 15 后 15+512 > 520 → 下一次调用前拦截
        monkeypatch.setenv("OPS_LLM_BUDGET_SESSION_TOKENS", "520")
        provider = _FakeProvider()
        with use_run_context(run_id="r1", surface="chat", task_type="answer"):
            first = await _collect(provider, [], model="big/model")
            # 进行中流完整吐完（正文 + usage 末帧齐全 · 不截断）
            assert any(c.content == "ok:big/model" for c in first)
            assert any((c.meta or {}).get("usage") for c in first)
            second = await _collect(provider, [], model="big/model")
        degraded = _degraded_chunks(second)
        assert degraded, "第二次调用应走降级链（ok=True 也可能降级）"
        assert provider.calls == ["big/model", "deepseek-ai/DeepSeek-V4-Flash"]


class TestDegradeChain:
    """D2 · 耗尽降级链（防假降级 U3 · 变异检验①锚点：
    摘除 degraded_meta 标记 → 本类标记断言必挂）。"""

    def _enforce_answer(self, monkeypatch, *, session_tokens="100"):
        monkeypatch.setenv("OPS_LLM_BUDGET_MODE", "enforce")
        monkeypatch.setenv("OPS_LLM_BUDGET_ENFORCE_TASKS", "answer,grader")
        monkeypatch.setenv("OPS_LLM_BUDGET_SESSION_TOKENS", session_tokens)

    async def test_exhaustion_degrades_to_smaller_model_with_marks(self, monkeypatch):
        """耗尽 → 小模型档：ok=True 且带 degraded+reason+chain（标记跟数据走）。"""
        self._enforce_answer(monkeypatch)
        ctx = LlmRunContext(run_id="r1", task_type="answer")
        llm_budget.record_actual("answer", 100, ctx=ctx)  # 100+512 > 100 → 拦截
        provider = _FakeProvider()
        with use_run_context(run_id="r1", surface="chat", task_type="answer"):
            chunks = await _collect(provider, [], model="big/model")
        degraded = _degraded_chunks(chunks)
        assert len(degraded) == 1
        meta = degraded[0].meta
        assert meta["degraded"] is True
        assert meta["degrade_reason"] == "budget_exhausted"
        assert meta["degrade_chain"] == ["answer", "deepseek-ai/DeepSeek-V4-Flash"]
        # ok=True：正文照常产出（降级不吞答）
        assert degraded[0].content == "ok:deepseek-ai/DeepSeek-V4-Flash"

    async def test_degrade_walks_to_rule_tier_when_model_fails(self, monkeypatch):
        """小模型档首 chunk 前失败 → 走规则/缓存档；链记录每一跳。"""
        self._enforce_answer(monkeypatch)
        ctx = LlmRunContext(run_id="r1", task_type="answer")
        llm_budget.record_actual("answer", 100, ctx=ctx)
        provider = _FlashFailsProvider()
        with use_run_context(run_id="r1", surface="chat", task_type="answer"):
            chunks = await _collect(provider, [], model="big/model")
        degraded = _degraded_chunks(chunks)
        assert len(degraded) == 1
        meta = degraded[0].meta
        assert meta["degrade_chain"] == [
            "answer",
            "deepseek-ai/DeepSeek-V4-Flash",
            "rule:static_refusal",
        ]
        assert meta["degrade_reason"] == "budget_exhausted"
        assert degraded[0].content == model_catalog.RULE_TIER_TEMPLATES["static_refusal"]

    async def test_chain_end_fails_closed_with_degraded_marks(self, monkeypatch):
        """链末端（规则档也无效/链为空）→ ok=False + degraded 不伪造成功。"""
        self._enforce_answer(monkeypatch)
        monkeypatch.setitem(
            model_catalog.TASK_TIER_FALLBACKS, "answer", ("rule:ghost-not-in-vocab",)
        )
        ctx = LlmRunContext(run_id="r1", task_type="answer")
        llm_budget.record_actual("answer", 100, ctx=ctx)
        provider = _FakeProvider()
        with (
            use_run_context(run_id="r1", surface="chat", task_type="answer"),
            pytest.raises(LlmProviderError) as exc_info,
        ):
            await _collect(provider, [], model="big/model")
        assert exc_info.value.retryable is False
        assert "budget_exhausted" in str(exc_info.value)
        assert "degraded=true" in str(exc_info.value)
        # 链末端不得有任何 LLM 出网调用（不伪造成功）
        assert provider.calls == []

    async def test_undeclared_tier_fails_explicitly(self, monkeypatch):
        """无声明档 = 明确失败（承 ACTION_NONE 默认 · 框架不猜降级目标）。"""
        self._enforce_answer(monkeypatch)
        ctx = LlmRunContext(run_id="r1", task_type="grader")
        llm_budget.record_actual("grader", 100, ctx=ctx)
        provider = _FakeProvider()
        with (
            use_run_context(run_id="r1", surface="background", task_type="grader"),
            pytest.raises(LlmProviderError) as exc_info,
        ):
            await _collect(provider, [], model="grader/model")
        assert exc_info.value.retryable is False
        assert "budget_exhausted" in str(exc_info.value)
        assert provider.calls == []

    async def test_off_mode_zero_diff_passthrough(self):
        """默认 off：预算面零行为（不拦截不计数 · 流逐字节直通）。"""
        provider = _FakeProvider()
        with use_run_context(run_id="r1", surface="chat", task_type="answer"):
            chunks = await _collect(provider, [], model="big/model")
        assert [c.content for c in chunks if c.content] == ["ok:big/model"]
        assert not _degraded_chunks(chunks)
        assert llm_budget.snapshot()["sessions"] == {}


class TestFallbackChainDeclaration:
    """D4 · catalog 链声明解析（非法档过滤+warning · 去环 · 链长≤3）。"""

    def test_default_chains(self):
        assert resolve_fallback_chain("answer") == (
            "deepseek-ai/DeepSeek-V4-Flash",
            "rule:static_refusal",
        )
        # 无声明档 = 空链 = 明确失败（承 ACTION_NONE）
        for task in ("grader", "extract", "structured", "summary"):
            assert resolve_fallback_chain(task) == ()

    def test_unknown_task_empty_chain_with_warning(self, caplog):
        with caplog.at_level(logging.WARNING, logger="app.llm.model_catalog"):
            assert resolve_fallback_chain("banana") == ()
        assert any("unknown llm task_type" in r.message for r in caplog.records)

    def test_invalid_entries_filtered_with_warning(self, monkeypatch, caplog):
        monkeypatch.setitem(
            model_catalog.TASK_TIER_FALLBACKS,
            "answer",
            ("no/such-model-anywhere", "rule:ghost", "rule:static_refusal"),
        )
        with caplog.at_level(logging.WARNING, logger="app.llm.model_catalog"):
            chain = resolve_fallback_chain("answer")
        assert chain == ("rule:static_refusal",)
        messages = [r.message for r in caplog.records]
        assert any("不在已知模型目录" in m for m in messages)
        assert any("RULE_TIER_TEMPLATES" in m for m in messages)

    def test_cycle_deduplicated_with_warning(self, monkeypatch, caplog):
        monkeypatch.setitem(
            model_catalog.TASK_TIER_FALLBACKS,
            "answer",
            ("deepseek-ai/DeepSeek-V4-Flash", "deepseek-ai/DeepSeek-V4-Flash"),
        )
        with caplog.at_level(logging.WARNING, logger="app.llm.model_catalog"):
            chain = resolve_fallback_chain("answer")
        assert chain == ("deepseek-ai/DeepSeek-V4-Flash",)
        assert any("重复元素" in r.message for r in caplog.records)

    def test_chain_length_capped_at_three(self, monkeypatch, caplog):
        monkeypatch.setitem(
            model_catalog.TASK_TIER_FALLBACKS,
            "answer",
            (
                "deepseek-ai/DeepSeek-V4-Flash",
                "deepseek-ai/DeepSeek-V4-Pro",
                "Qwen/Qwen3.6-27B",
                "rule:static_refusal",
            ),
        )
        with caplog.at_level(logging.WARNING, logger="app.llm.model_catalog"):
            chain = resolve_fallback_chain("answer")
        assert len(chain) == 3
        assert any("链长上限" in r.message for r in caplog.records)


class TestCostPerSuccessfulTask:
    """D5 · Cost per Successful Task 聚合口径（缺单价 unknown 不伪造 0）。"""

    def test_estimate_cost_known_and_unknown_model(self):
        cost = estimate_cost("deepseek-ai/DeepSeek-V4-Flash", 1000, 1000)
        assert cost == pytest.approx(0.001 + 0.002)
        assert estimate_cost("no/such-model", 1000, 1000) is None

    def test_aggregation_over_successful_runs(self):
        rows = [
            UsageCostRow("r1", "deepseek-ai/DeepSeek-V4-Flash", 1000, 1000),
            UsageCostRow("r1", "deepseek-ai/DeepSeek-V4-Flash", 1000, 1000),
            UsageCostRow("r2", "Qwen/Qwen3.6-27B", 1000, 0),
        ]
        result = cost_per_successful_task(rows)
        # r1: 2 × 0.003 = 0.006；r2: 0.002 → 均值 (0.006+0.002)/2
        assert result["successful_tasks"] == 2
        assert result["total_cost"] == pytest.approx(0.008)
        assert result["cost_per_successful_task"] == pytest.approx(0.004)
        assert result["basis"] == "estimate_only_not_billing"

    def test_missing_price_marks_unknown_not_zero(self):
        rows = [
            UsageCostRow("r1", "deepseek-ai/DeepSeek-V4-Flash", 1000, 1000),
            UsageCostRow("r2", "no/such-model", 1000, 1000),
        ]
        result = cost_per_successful_task(rows)
        assert result["cost_per_successful_task"] == "unknown"
        assert result["total_cost"] == "unknown"

    def test_empty_rows_zero_tasks(self):
        result = cost_per_successful_task([])
        assert result["successful_tasks"] == 0
        assert result["cost_per_successful_task"] == 0.0

    def test_verdict_span_report_noop_when_tracing_off(self):
        """span 产出面：tracing 关时观测静默（不挡主流程）。"""
        verdict = BudgetVerdict(allowed=True, mode="observe", would_block=True)
        llm_budget.report_verdict(verdict)
        llm_budget.report_estimated_cost("no/such-model", 1, 1)
