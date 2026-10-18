"""会话记忆真摘要 · 保真度金样（否决面 · session-summary-fallback D4）。

**金样不是准确率。** 任一条规则被突破**整体不通过**。正反双断言缺一不可：

- **正向（F1）**：must_keep sentinel ⊆ 摘要文本（丢关键事实 = 违规）
- **反向（F2）**：must_not_add 禁忌 sentinel 逐项不在摘要（幻觉 = 违规）；
  空摘要假通过防线——空摘要必判违规且每个金样 must_keep 非空
- **结构（F3）**：装配产物零占位格式残留 · 摘要条含版本/来源/有损三标记

清单在 evals/session/summary_fidelity_v1.yaml；本文件是它的实现，
两者一一对应（F0 守这条 · preference_redline P0 同款）。
热路径零 LLM-as-judge：判定函数 evals/session/fidelity.py 是确定性 token
断言；CI 用夹具 turns + 录制摘要跑同一函数，真模型离线抽检不作 CI 否决面。
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from app.llm.schema import BaseProvider
from app.ops.lg_rag.continuity import compress_window
from app.ops.session import summary as session_summary
from evals.session.fidelity import check_summary_fidelity

pytestmark = pytest.mark.redline

_INVENTORY = Path(__file__).resolve().parents[2] / "evals" / "session" / "summary_fidelity_v1.yaml"

#: rule_id → 实现它的测试函数名（装饰器登记，F0 对照用）
IMPLEMENTED: dict[str, str] = {}


def rule(rule_id: str):
    def decorate(fn):
        IMPLEMENTED[rule_id] = fn.__name__
        fn.__doc__ = f"[{rule_id}] {fn.__doc__ or ''}"
        return fn

    return decorate


def _load_inventory() -> dict:
    with _INVENTORY.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _cases() -> list[dict]:
    cases = _load_inventory()["golden_cases"]
    assert len(cases) >= 3, "金样太少不足以称金样"
    return cases


@rule("F0")
def test_inventory_matches_implementation():
    """清单 ↔ 实现一一对应：多声明 = 假防护，少声明 = 暗改。"""
    inv = _load_inventory()
    declared = {r["id"] for r in inv["rules"]}
    assert declared == set(IMPLEMENTED), (
        f"清单与实现漂移：declared={sorted(declared)} implemented={sorted(IMPLEMENTED)}"
    )


@rule("F1")
def test_must_keep_sentinels_present():
    """正向：录制摘要含全部 must_keep sentinel；反向对照：删掉任一 sentinel
    的摘要必须被判违规（防「永不校验」式假通过）。"""
    for case in _cases():
        assert case["must_keep"], f"[{case['id']}] must_keep 为空（假通过防线）"
        violations = check_summary_fidelity(
            case["recorded_summary"],
            must_keep=case["must_keep"],
            must_not_add=case["must_not_add"],
        )
        assert violations == [], f"[{case['id']}] 录制摘要未过正向断言: {violations}"
        # 反向对照：逐个删掉 sentinel 必挂
        for token in case["must_keep"]:
            dropped = case["recorded_summary"].replace(token, "", 1)
            bad = check_summary_fidelity(
                dropped,
                must_keep=case["must_keep"],
                must_not_add=case["must_not_add"],
            )
            assert f"must_keep_missing:{token}" in bad, (
                f"[{case['id']}] 删掉 sentinel {token} 未被判违规"
            )


@rule("F2")
def test_must_not_add_sentinels_absent_and_empty_summary_rejected():
    """反向：must_not_add 逐项不在摘要；掺入任一禁忌 token 必挂；
    空摘要必判违规（空摘要假通过防线——空摘要天然满足 must_not_add）。"""
    for case in _cases():
        assert case["must_not_add"], f"[{case['id']}] must_not_add 为空"
        for token in case["must_not_add"]:
            assert token not in case["recorded_summary"], (
                f"[{case['id']}] 录制摘要本身含禁忌 token {token}（夹具错误）"
            )
            polluted = case["recorded_summary"] + f" {token}"
            bad = check_summary_fidelity(
                polluted,
                must_keep=case["must_keep"],
                must_not_add=case["must_not_add"],
            )
            assert f"must_not_add_present:{token}" in bad, (
                f"[{case['id']}] 掺入禁忌 token {token} 未被判违规"
            )
        # 空摘要假通过防线（对该金样 must_keep 集合）
        assert check_summary_fidelity(
            "", must_keep=case["must_keep"], must_not_add=case["must_not_add"]
        ) == ["empty_summary"]
        assert check_summary_fidelity(
            "   \n  ", must_keep=case["must_keep"], must_not_add=case["must_not_add"]
        ) == ["empty_summary"]


@rule("F3")
async def test_assembled_context_structure(monkeypatch: pytest.MonkeyPatch):
    """结构断言：金样 turns 走真摘要面（fake provider 回放录制摘要）后——

    零占位格式残留（无 roles= 占位条）· 每条摘要条含 v1 + 模型: + 有损三标记。
    且装配产物摘要文本过同一 fidelity 校验函数（热路径确定性）。
    """
    monkeypatch.setattr(session_summary, "update_current_span_metadata", lambda m: None)

    async def _no_read(thread_id, digest):
        return None

    async def _no_write(**kwargs):
        return None

    monkeypatch.setattr(session_summary, "_read_cached_summary", _no_read)
    monkeypatch.setattr(session_summary, "_write_cached_summary", _no_write)

    for case in _cases():
        turns = case["turns"]
        compressed = compress_window(list(turns))
        n_placeholders = sum(1 for t in compressed if t["content"].startswith("[历史摘要 · "))
        assert n_placeholders >= 1, f"[{case['id']}] 夹具 turns 未触发压缩"

        def _make_replay_provider(recorded: str) -> BaseProvider:
            """工厂绑定（B023：循环变量经参数入闭包）。"""

            class _ReplayProvider(BaseProvider):
                async def complete(self, messages, model=None):
                    return recorded

            return _ReplayProvider()

        # 默认参数绑定循环变量（B023：lambda 定义期即绑定本 case 的录制摘要）
        monkeypatch.setattr(
            session_summary,
            "get_llm_provider",
            lambda recorded=case["recorded_summary"]: _make_replay_provider(recorded),
        )
        out = await session_summary.summarize_placeholders(
            compressed, thread_id=f"gold-{case['id']}", source_turns=list(turns)
        )
        assert len(out) == len(compressed)  # 结构零改动（条数不变）
        summary_entries = [t for t in out if str(t.get("content", "")).startswith("[历史摘要 · ")]
        assert len(summary_entries) == n_placeholders
        for entry in summary_entries:
            content = entry["content"]
            assert "roles=" not in content, f"[{case['id']}] 占位格式残留"
            assert " · v1 · " in content  # 版本标记
            assert "模型:" in content  # 来源标记
            assert "有损" in content  # 有损声明
            # 摘要正文过同一 fidelity 校验函数（录制摘要即热路径候选）
            body = content.split("\n", 1)[1]
            assert (
                check_summary_fidelity(
                    body,
                    must_keep=case["must_keep"],
                    must_not_add=case["must_not_add"],
                )
                == []
            )
