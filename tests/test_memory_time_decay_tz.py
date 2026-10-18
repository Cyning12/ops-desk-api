"""memory-fuse-tz-fix · _time_decay tz 归一回归（纯函数 · 无需 DB）。

背景（live 裁决记录发现 1）：migration 建 timestamptz → 真库读回 **aware**；
`now_utc()=datetime.utcnow()` 为 **naive**；修复前 `(now - fact.updated_at)`
直接抛 `TypeError: can't subtract offset-naive and offset-aware datetimes`。
测试库由 ORM create_all 建 naive 列，双侧同 naive 所以 P1 测试没抓到
（schema 漂移注记见 app/ops/memory/README.md）。

钉死语义：**naive 一律视为 UTC**（不转本地时区、不把 aware 转 naive）。

四象限：aware now×naive fact / naive now×aware fact / 双 aware / 双 naive
均不抛 + 衰减值正确（0 天=1.0 · 半衰期 30 天≈0.5 · 未来时间戳按 0 天）。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.db.models import OpsMemoryFact
from app.ops.memory.service import HALF_LIFE_DAYS, _time_decay

_NAIVE_BASE = datetime(2026, 9, 1, 12, 0, 0)
_AWARE_BASE = _NAIVE_BASE.replace(tzinfo=UTC)


def _fact(updated_at: datetime) -> OpsMemoryFact:
    fact = OpsMemoryFact(
        tenant_id="tz-test-tenant",
        user_id="u-tz",
        key="project.primary_repo",
        value="cyning/ops-desk",
    )
    fact.updated_at = updated_at
    return fact


# now × fact.updated_at 四象限：(now, fact) 各取 naive/aware（同一时刻）
_QUADRANTS = [
    pytest.param(_AWARE_BASE, _NAIVE_BASE, id="aware-now_naive-fact"),
    pytest.param(_NAIVE_BASE, _AWARE_BASE, id="naive-now_aware-fact"),
    pytest.param(_AWARE_BASE, _AWARE_BASE, id="aware-now_aware-fact"),
    pytest.param(_NAIVE_BASE, _NAIVE_BASE, id="naive-now_naive-fact"),
]


@pytest.mark.parametrize(("now", "fact_ts"), _QUADRANTS)
def test_time_decay_zero_age_is_one(now: datetime, fact_ts: datetime) -> None:
    """四象限：同一时刻 → age=0 天 → decay=1.0，不抛 TypeError。"""
    assert _time_decay(_fact(fact_ts), now) == 1.0


@pytest.mark.parametrize(("now", "fact_ts"), _QUADRANTS)
def test_time_decay_half_life(now: datetime, fact_ts: datetime) -> None:
    """四象限：age=半衰期（HALF_LIFE_DAYS 天 · 定稿 90 · 调参 task memory-fusion-weight-tuning）→ decay≈0.5。"""
    age = timedelta(days=HALF_LIFE_DAYS)
    assert _time_decay(_fact(fact_ts - age), now) == pytest.approx(0.5)


@pytest.mark.parametrize(("now", "fact_ts"), _QUADRANTS)
def test_time_decay_future_timestamp_clamps_to_zero(now: datetime, fact_ts: datetime) -> None:
    """四象限：未来时间戳按 0 天 → decay=1.0。"""
    future = fact_ts + timedelta(days=1)
    assert _time_decay(_fact(future), now) == 1.0


@pytest.mark.parametrize(("now", "fact_ts"), _QUADRANTS)
def test_time_decay_arbitrary_age(now: datetime, fact_ts: datetime) -> None:
    """四象限：任意 age 与公式一致（期望值动态取 0.5 ** (15/HALF_LIFE_DAYS) · 半衰期定稿 90 天）。"""
    age = timedelta(days=15)
    expected = 0.5 ** (15.0 / HALF_LIFE_DAYS)
    assert _time_decay(_fact(fact_ts - age), now) == pytest.approx(expected)


def test_time_decay_naive_equals_aware_same_instant() -> None:
    """归一语义：naive 视为 UTC —— 同一时刻 naive/aware 衰减值逐位相等。"""
    age = timedelta(days=7, hours=3)
    naive = _time_decay(_fact(_NAIVE_BASE - age), _NAIVE_BASE)
    aware = _time_decay(_fact(_AWARE_BASE - age), _AWARE_BASE)
    assert naive == aware == pytest.approx(0.5 ** ((7 * 24 + 3) / 24 / HALF_LIFE_DAYS))


def test_time_decay_aware_fact_in_non_utc_offset() -> None:
    """aware 非 UTC 偏移（如 +08:00）与 UTC 同一时刻 → 衰减值一致（不转本地）。

    注记：age 字面量 30 天 → HALF_LIFE_DAYS 动态引用（task
    memory-fusion-weight-tuning 2026-09-21 定稿半衰期 30→90 天，硬编码
    30 天不再等于半衰期）；检验意图（+08:00 不转本地）不变。
    """
    plus8 = timezone(timedelta(hours=8))
    now_utc = _AWARE_BASE
    fact_plus8 = (_AWARE_BASE - timedelta(days=HALF_LIFE_DAYS)).astimezone(plus8)
    assert _time_decay(_fact(fact_plus8), now_utc) == pytest.approx(0.5)
