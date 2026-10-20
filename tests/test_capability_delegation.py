"""Host V1-A · 委派令牌模型与验签纯函数（D1 令牌模型 / D3 验签门面）。

覆盖（task 验收 D1/D3 映射）：
- DelegationToken frozen dataclass + canonical JSON + HMAC-SHA256 签名/验签；
- 六类拒绝 R-a~R-f（全 ok=False 不抛异常）+ 篡改必拒（改字段 → 签名失效）；
- 参数约束三态（enum / max_len / pattern）+ 未知约束类型拒绝签发；
- 序列化 round-trip（checkpoint 形态 · 纯 JSON）；
- supersede（同 subtask 重签发 = 旧 nonce 作废）+ 签发序号单调；
- env 纪律（mode/ttl 非法回退 · 缺密钥拒签发+告警）；
- 计时 smoke（注记级 · SPEC FP-3 · 不设硬 CI 阈值）。
"""

from __future__ import annotations

import dataclasses
import json
import logging
import time
from types import SimpleNamespace

import pytest

from app.ops.capability import delegation as dl

SECRET = "test-delegation-secret-0001"

SUBJECT = {
    "tenant_id": "ops-desk-pilot",
    "user_id": "u-1",
    "run_id": "run-1",
    "subtask_id": "run-1:1",
}


@pytest.fixture(autouse=True)
def _reset_delegation():
    dl.reset_delegation_state()
    yield
    dl.reset_delegation_state()


def _issue(**kw):
    base = {
        "capability_set": {"cap.read"},
        "subject_binding": dict(SUBJECT),
        "secret": SECRET,
        "issuer": dl.DelegationIssuer(),
        "now": 1000.0,
        "ttl_seconds": 600,
    }
    base.update(kw)
    return dl.issue_token(**base)


def _verify(token, **kw):
    base = {
        "secret": SECRET,
        "capability_id": "cap.read",
        "args": {},
        "subject": dict(SUBJECT),
        "now": 1000.0,
    }
    base.update(kw)
    return dl.verify_token(token, **base)


# ---------------------------------------------------------------------------
# 令牌模型 / 签名 / 序列化
# ---------------------------------------------------------------------------


def test_issue_and_verify_ok(caplog):
    with caplog.at_level(logging.INFO, logger="app.ops.capability.delegation"):
        token = _issue()
    assert token is not None
    assert token.token_id.startswith("dt-1-")
    assert token.version == dl.TOKEN_VERSION
    assert token.one_shot is True
    assert token.expires_at == 1000.0 + 600
    assert _verify(token).ok is True
    # D4：签发台账（token_issued）——变异检验③的靶断言
    assert "token_issued" in caplog.text


def test_token_is_frozen():
    token = _issue()
    with pytest.raises(dataclasses.FrozenInstanceError):
        token.expires_at = 9999.0  # type: ignore[misc]


def test_serialization_round_trip():
    token = _issue(param_constraints={"cap.read": {"mode": {"enum": ["a"]}}})
    raw = dl.token_to_dict(token)
    # checkpoint 形态：必须纯 JSON 可序列化
    restored = dl.token_from_dict(json.loads(json.dumps(raw, ensure_ascii=False)))
    assert restored == token
    assert dl.canonical_payload(restored) == dl.canonical_payload(token)
    assert _verify(restored, args={"mode": "a"}).ok is True


def test_signature_is_hmac_sha256_hex():
    token = _issue()
    assert len(token.signature) == 64
    int(token.signature, 16)
    assert token.kid == dl._kid_of(SECRET)


# ---------------------------------------------------------------------------
# 篡改必拒（缺这组断言则「验签通过」是假通过）
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field,value",
    [
        ("capability_set", frozenset({"cap.evil"})),
        ("expires_at", 999999.0),
        ("subject_binding", {**SUBJECT, "tenant_id": "evil-tenant"}),
    ],
)
def test_tamper_any_field_rejected(field, value):
    token = _issue()
    tampered = dataclasses.replace(token, **{field: value})
    verdict = _verify(tampered)
    assert verdict.ok is False
    assert verdict.reject_class == dl.REJECT_SIGNATURE_INVALID


def test_wrong_secret_rejected():
    token = _issue()
    verdict = _verify(token, secret="another-secret")
    assert verdict.ok is False
    assert verdict.reject_class == dl.REJECT_SIGNATURE_INVALID


# ---------------------------------------------------------------------------
# 六类拒绝（R-a~R-f）
# ---------------------------------------------------------------------------


def test_reject_a_no_token():
    verdict = _verify(None)
    assert verdict.ok is False
    assert verdict.reject_class == dl.REJECT_NO_TOKEN
    # 反序列化失败同归 R-a
    assert (
        dl.verify_serialized(
            "junk", secret=SECRET, capability_id="cap.read", args={}, subject=SUBJECT
        ).reject_class
        == dl.REJECT_NO_TOKEN
    )
    assert (
        dl.verify_serialized(
            {"bad": 1}, secret=SECRET, capability_id="cap.read", args={}, subject=SUBJECT
        ).reject_class
        == dl.REJECT_NO_TOKEN
    )


def test_reject_a_secret_missing():
    token = _issue()
    verdict = _verify(token, secret=None)
    assert verdict.ok is False
    assert verdict.reject_class == dl.REJECT_SECRET_MISSING


def test_reject_b_out_of_set():
    token = _issue()
    verdict = _verify(token, capability_id="cap.other")
    assert verdict.ok is False
    assert verdict.reject_class == dl.REJECT_OUT_OF_SET


def test_reject_c_expired():
    token = _issue()
    verdict = _verify(token, now=1000.0 + 601)
    assert verdict.ok is False
    assert verdict.reject_class == dl.REJECT_EXPIRED


def test_reject_d_nonce_reused():
    token = _issue()
    assert _verify(token).ok is True
    verdict = _verify(token)
    assert verdict.ok is False
    assert verdict.reject_class == dl.REJECT_NONCE_REUSED


def test_reject_e_param_violation():
    token = _issue(param_constraints={"cap.read": {"mode": {"enum": ["a", "b"]}}})
    verdict = _verify(token, args={"mode": "c"})
    assert verdict.ok is False
    assert verdict.reject_class == dl.REJECT_PARAM_VIOLATION
    assert verdict.violated_field == "mode"


def test_reject_f_subject_mismatch():
    token = _issue()
    verdict = _verify(token, subject={**SUBJECT, "run_id": "run-other"})
    assert verdict.ok is False
    assert verdict.reject_class == dl.REJECT_SUBJECT_MISMATCH


def test_rejected_call_does_not_burn_nonce():
    """被拒（参数越约束）的调用不消费 nonce——修好参数后同一令牌仍可用。"""
    token = _issue(param_constraints={"cap.read": {"mode": {"enum": ["a"]}}})
    assert _verify(token, args={"mode": "x"}).reject_class == dl.REJECT_PARAM_VIOLATION
    assert _verify(token, args={"mode": "a"}).ok is True


# ---------------------------------------------------------------------------
# 参数约束三态 + 未知类型拒绝签发
# ---------------------------------------------------------------------------


def test_constraint_enum_pass_and_fail():
    token = _issue(param_constraints={"cap.read": {"m": {"enum": ["x", 1, None]}}})
    assert _verify(token, args={"m": "x"}).ok is True
    bad = _issue(param_constraints={"cap.read": {"m": {"enum": ["x"]}}})
    assert _verify(bad, args={"m": "y"}).reject_class == dl.REJECT_PARAM_VIOLATION


def test_constraint_max_len_pass_and_fail():
    token = _issue(param_constraints={"cap.read": {"q": {"max_len": 3}}})
    assert _verify(token, args={"q": "abc"}).ok is True
    bad = _issue(param_constraints={"cap.read": {"q": {"max_len": 3}}})
    assert _verify(bad, args={"q": "abcd"}).reject_class == dl.REJECT_PARAM_VIOLATION
    bad2 = _issue(param_constraints={"cap.read": {"q": {"max_len": 3}}})
    # 非 str / 缺字段一律违规（安全默认）
    assert _verify(bad2, args={}).reject_class == dl.REJECT_PARAM_VIOLATION


def test_constraint_pattern_pass_and_fail():
    token = _issue(param_constraints={"cap.read": {"q": {"pattern": "^[0-9]+$"}}})
    assert _verify(token, args={"q": "123"}).ok is True
    bad = _issue(param_constraints={"cap.read": {"q": {"pattern": "^[0-9]+$"}}})
    assert _verify(bad, args={"q": "12a"}).reject_class == dl.REJECT_PARAM_VIOLATION


def test_unknown_constraint_type_rejects_issue(caplog):
    with caplog.at_level(logging.WARNING, logger="app.ops.capability.delegation"):
        token = _issue(param_constraints={"cap.read": {"x": {"regex": ".*"}}})
    assert token is None
    assert "拒绝签发" in caplog.text
    assert dl.validate_param_constraints({"c": {"x": {"regex": ".*"}}}) is not None
    assert dl.validate_param_constraints({"c": {"x": {"enum": ["a"]}}}) is None
    assert dl.validate_param_constraints({"c": {"x": {"max_len": True}}}) is not None
    assert dl.validate_param_constraints({"c": {"x": {"pattern": "["}}}) is not None


def test_constraints_for_other_capability_not_applied():
    token = _issue(param_constraints={"cap.other": {"q": {"max_len": 1}}})
    assert _verify(token, args={"q": "long-value"}).ok is True


# ---------------------------------------------------------------------------
# 一次性 / supersede / 序号单调
# ---------------------------------------------------------------------------


def test_one_shot_disabled_allows_reuse():
    token = _issue(one_shot=False)
    assert _verify(token).ok is True
    assert _verify(token).ok is True


def test_supersede_invalidates_old_nonce(caplog):
    issuer = dl.DelegationIssuer()
    first = _issue(issuer=issuer)
    with caplog.at_level(logging.INFO, logger="app.ops.capability.delegation"):
        second = _issue(issuer=issuer)
    assert first is not None and second is not None
    assert first.nonce != second.nonce
    # 旧例 nonce 作废 → R-d（从未消费也算重用，supersede 语义）
    verdict = _verify(first)
    assert verdict.ok is False
    assert verdict.reject_class == dl.REJECT_NONCE_REUSED
    assert _verify(second).ok is True
    assert "token_superseded" in caplog.text


def test_issue_seq_monotonic():
    issuer = dl.DelegationIssuer()
    t1 = _issue(issuer=issuer)
    t2 = _issue(issuer=issuer, subject_binding={**SUBJECT, "subtask_id": "run-1:2"})
    assert t1.token_id.startswith("dt-1-")
    assert t2.token_id.startswith("dt-2-")


# ---------------------------------------------------------------------------
# env 纪律（非法回退 · 缺密钥拒签发+告警）
# ---------------------------------------------------------------------------


def test_env_mode_invalid_falls_back_off(monkeypatch):
    monkeypatch.delenv(dl.ENV_MODE, raising=False)
    assert dl.delegation_mode() == dl.MODE_OFF
    monkeypatch.setenv(dl.ENV_MODE, "ENFORCE")
    assert dl.delegation_mode() == dl.MODE_ENFORCE
    monkeypatch.setenv(dl.ENV_MODE, "bogus")
    assert dl.delegation_mode() == dl.MODE_OFF


def test_env_ttl_invalid_falls_back_default(monkeypatch):
    monkeypatch.delenv(dl.ENV_TTL_SECONDS, raising=False)
    assert dl.delegation_ttl_seconds() == 600
    monkeypatch.setenv(dl.ENV_TTL_SECONDS, "abc")
    assert dl.delegation_ttl_seconds() == 600
    monkeypatch.setenv(dl.ENV_TTL_SECONDS, "0")
    assert dl.delegation_ttl_seconds() == 600
    monkeypatch.setenv(dl.ENV_TTL_SECONDS, "30")
    assert dl.delegation_ttl_seconds() == 30


def test_missing_secret_refuses_issue_with_alert(monkeypatch, caplog):
    monkeypatch.delenv(dl.ENV_SECRET, raising=False)
    with caplog.at_level(logging.WARNING, logger="app.ops.capability.delegation"):
        token = dl.issue_token(capability_set={"cap.read"}, subject_binding=dict(SUBJECT))
    assert token is None
    assert "拒绝签发" in caplog.text


def test_secret_from_env(monkeypatch):
    monkeypatch.setenv(dl.ENV_SECRET, SECRET)
    token = dl.issue_token(capability_set={"cap.read"}, subject_binding=dict(SUBJECT), now=1000.0)
    assert token is not None
    assert _verify(token).ok is True


# ---------------------------------------------------------------------------
# 审批口径（Q2：只读自动 · 其余 HITL）
# ---------------------------------------------------------------------------


def _spec(cid, *, side_effect="read", kind="local_fn"):
    return SimpleNamespace(capability_id=cid, side_effect=side_effect, kind=kind)


def test_issuance_policy_allows_readonly_in_scope():
    ok, _ = dl.issuance_policy_allows([_spec("a")], effective_scope={"a", "b"})
    assert ok is True


@pytest.mark.parametrize(
    "spec_kwargs,scope",
    [
        ({"side_effect": "write"}, {"a"}),
        ({"side_effect": "irreversible"}, {"a"}),
        ({"kind": "sandbox"}, {"a"}),
        ({"kind": "cli"}, {"a"}),
    ],
)
def test_issuance_policy_allows_denies_write_and_sandbox_cli(spec_kwargs, scope):
    ok, why = dl.issuance_policy_allows([_spec("a", **spec_kwargs)], effective_scope=scope)
    assert ok is False
    assert why


def test_issuance_policy_allows_denies_out_of_scope():
    ok, _ = dl.issuance_policy_allows([_spec("a")], effective_scope={"b"})
    assert ok is False


# ---------------------------------------------------------------------------
# 计时 smoke（注记级 · SPEC FP-3：<1ms/次量级声明 · 不设硬 CI 阈值）
# ---------------------------------------------------------------------------


def test_verify_timing_smoke():
    token = _issue(one_shot=False)
    rounds = 1000
    started = time.perf_counter()
    for _ in range(rounds):
        assert _verify(token).ok is True
    avg_ms = (time.perf_counter() - started) * 1000.0 / rounds
    # 注记：HMAC 对称验签 + 纯代码约束校验，实测微秒级（量级声明 <1ms/次，
    # 不设硬阈值防 CI 抖动；观测期异常放大由 FP-3 台账复盘）。
    print(f"delegation verify avg {avg_ms:.4f} ms/call over {rounds} calls")
