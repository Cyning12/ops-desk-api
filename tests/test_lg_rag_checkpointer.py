"""P0' T3：LG_RAG_HTTP_CHECKPOINTER 默认翻开（unset=postgres）真值表钉死。

conftest 有 autouse fixture 把该键显式置空（测试面统一压回 off），
所以「默认开」用例必须自己 delenv 才能验到 unset 语义。
"""

import pytest

from app.ops.lg_rag.checkpointer import CHECKPOINTER_ENV, use_postgres_checkpointer


def test_unset_defaults_to_postgres(monkeypatch: pytest.MonkeyPatch) -> None:
    """P0' T3 核心语义反转：未设 env ⇒ 默认开（HITL 跨请求恢复必须可用）。"""
    monkeypatch.delenv(CHECKPOINTER_ENV, raising=False)
    assert use_postgres_checkpointer() is True


@pytest.mark.parametrize("value", ["postgres", " POSTGRES ", "Postgres"])
def test_explicit_postgres_on(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv(CHECKPOINTER_ENV, value)
    assert use_postgres_checkpointer() is True


@pytest.mark.parametrize("value", ["", "off", "memory", "0", "none"])
def test_explicit_off_values(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    """回退口：postgres 以外任意值（含空串）= 关。"""
    monkeypatch.setenv(CHECKPOINTER_ENV, value)
    assert use_postgres_checkpointer() is False
