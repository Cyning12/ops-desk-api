"""memory-facts-p0 · M1 写入闸纯函数（无 DB）：三判据 + 长度上限 + 拒绝原因码枚举。"""
from __future__ import annotations

import pytest

from app.ops.memory.gate import (
    ALLOWED_KINDS,
    DEFAULT_MAX_VALUE_CHARS,
    KIND_FACT,
    REJECT_REASONS,
    Decision,
    FactCandidate,
    max_value_chars,
    should_write,
)


def _candidate(**over) -> FactCandidate:
    base = {
        "tenant_id": "ops-desk-pilot",
        "user_id": "u-1",
        "key": "project.primary_repo",
        "value": "cyning/ops-desk",
    }
    base.update(over)
    return FactCandidate(**base)


def test_valid_fact_allowed():
    d = should_write(_candidate())
    assert d == Decision(allowed=True, reason_code="")


@pytest.mark.parametrize("value", ["x", 1, 1.5, True, False])
def test_scalar_values_allowed(value):
    assert should_write(_candidate(value=value)).allowed is True


@pytest.mark.parametrize("kind", ["profile", "PREFERENCE", "prefs", ""])
def test_kind_not_allowed(kind):
    """kind 集合外 → kind_not_allowed（memory-preference-profile：preference
    已放开入集合，本用例改用集合外值钉死「集合外仍拒」）。"""
    d = should_write(_candidate(kind=kind))
    assert d.allowed is False
    assert d.reason_code == "kind_not_allowed"


def test_allowed_kinds_set():
    """闸放开集合钉死：恰为 {fact, preference}（不多不少）。"""
    assert sorted(ALLOWED_KINDS) == ["fact", "preference"]


def test_preference_with_pref_key_allowed():
    """preference + pref.* key → 放行（双向绑定的放行面）。"""
    d = should_write(_candidate(key="pref.answer_lang", value="中文", kind="preference"))
    assert d == Decision(allowed=True, reason_code="")


@pytest.mark.parametrize(
    "key,kind",
    [
        ("project.answer_lang", "preference"),  # preference + 非 pref. key
        ("pref.display_tz", "fact"),  # fact + pref. key
        ("pref.display_tz", KIND_FACT),  # 显式 fact 同上（双向）
    ],
)
def test_key_kind_mismatch_bidirectional(key, kind):
    """双向 key 域绑定：kind=preference ⟺ key 首段 == pref；违反 → key_kind_mismatch。"""
    d = should_write(_candidate(key=key, kind=kind))
    assert d.allowed is False
    assert d.reason_code == "key_kind_mismatch"


@pytest.mark.parametrize("tenant_id,user_id", [("", "u-1"), ("t", ""), ("  ", "u-1"), ("t", "  ")])
def test_missing_subject(tenant_id, user_id):
    d = should_write(_candidate(tenant_id=tenant_id, user_id=user_id))
    assert d.allowed is False
    assert d.reason_code == "missing_subject"


@pytest.mark.parametrize(
    "key",
    ["", "Project.Primary_Repo", "primaryrepo", "project.", ".project", "project.primary-repo", "a.b c"],
)
def test_invalid_key(key):
    d = should_write(_candidate(key=key))
    assert d.allowed is False
    assert d.reason_code == "invalid_key"


@pytest.mark.parametrize("key", ["tmp.note", "session.turn", "ephemeral.ctx", "draft.idea"])
def test_volatile_key(key):
    d = should_write(_candidate(key=key))
    assert d.allowed is False
    assert d.reason_code == "volatile_key"


@pytest.mark.parametrize("value", [None, {"a": 1}, ["x"], (1, 2)])
def test_value_not_scalar(value):
    d = should_write(_candidate(value=value))
    assert d.allowed is False
    assert d.reason_code == "value_not_scalar"


@pytest.mark.parametrize("value", ["", "   "])
def test_empty_value(value):
    d = should_write(_candidate(value=value))
    assert d.allowed is False
    assert d.reason_code == "empty_value"


def test_value_too_large():
    d = should_write(_candidate(value="x" * DEFAULT_MAX_VALUE_CHARS))
    assert d.allowed is False
    assert d.reason_code == "value_too_large"


def test_value_limit_env_override(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MEMORY_FACTS_MAX_VALUE_CHARS", "16")
    assert should_write(_candidate(value="short")).allowed is True
    d = should_write(_candidate(value="x" * 32))
    assert d.allowed is False and d.reason_code == "value_too_large"


def test_value_limit_env_invalid_falls_back(monkeypatch: pytest.MonkeyPatch, caplog):
    monkeypatch.setenv("MEMORY_FACTS_MAX_VALUE_CHARS", "abc")
    with caplog.at_level("WARNING", logger="app.ops.memory.gate"):
        assert max_value_chars() == DEFAULT_MAX_VALUE_CHARS
    assert "MEMORY_FACTS_MAX_VALUE_CHARS" in caplog.text
    monkeypatch.setenv("MEMORY_FACTS_MAX_VALUE_CHARS", "-5")
    assert max_value_chars() == DEFAULT_MAX_VALUE_CHARS


def test_reject_reasons_enumerable_and_cover_all_rejections():
    """原因码稳定可枚举：每条拒绝路径的码都必须注册在 REJECT_REASONS。

    memory-preference-profile：集合放开后改用集合外 kind 触发
    kind_not_allowed；新增 key_kind_mismatch 双向两态显式入覆盖清单。
    """
    bad_candidates = [
        _candidate(kind="profile"),  # kind_not_allowed（集合外）
        _candidate(kind="preference"),  # key_kind_mismatch（preference + 非 pref. key）
        _candidate(key="pref.answer_lang"),  # key_kind_mismatch（缺省 fact + pref. key）
        _candidate(tenant_id=""),
        _candidate(key="BAD KEY"),
        _candidate(key="tmp.x"),
        _candidate(value=None),
        _candidate(value=""),
        _candidate(value="x" * (DEFAULT_MAX_VALUE_CHARS + 1)),
    ]
    for c in bad_candidates:
        d = should_write(c)
        assert d.allowed is False
        assert d.reason_code in REJECT_REASONS
    # 9 条拒径 → 8 个原因码（key_kind_mismatch 双向两态同一码），集合钉死
    assert sorted(REJECT_REASONS) == [
        "empty_value",
        "invalid_key",
        "key_kind_mismatch",
        "kind_not_allowed",
        "missing_subject",
        "value_not_scalar",
        "value_too_large",
        "volatile_key",
    ]
