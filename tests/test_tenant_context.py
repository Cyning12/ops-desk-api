"""阶段 T 租户解析 + RAG metadata 负样本；含切 B → sessions/latest 回归。"""

import pytest
from httpx import AsyncClient

from app.ops.rag.retrieve import RetrievedChunk, _filter_by_request_tenant
from app.ops.tenant_context import (
    TENANT_A,
    TENANT_B,
    TENANT_HEADER,
    current_tenant_or_default,
    reset_current_tenant,
    resolve_header_against_session,
    set_current_tenant,
)
from tests.conftest import DB_AVAILABLE


def _chunk(cid: int, tenant: str | None) -> RetrievedChunk:
    meta = {} if tenant is None else {"tenant_id": tenant}
    return RetrievedChunk(
        id=cid,
        repo="acme/demo",
        source_type="issue",
        source_id=f"issue-{cid}",
        chunk_index=0,
        content=f"chunk-{cid}",
        metadata=meta,
    )


def test_header_absent_uses_session():
    assert resolve_header_against_session(TENANT_A, None) == TENANT_A
    assert resolve_header_against_session(None, "") == TENANT_A


def test_header_must_match_session():
    assert resolve_header_against_session(TENANT_B, TENANT_B) == TENANT_B
    with pytest.raises(ValueError, match="tenant_header_mismatch"):
        resolve_header_against_session(TENANT_A, TENANT_B)


def test_unknown_tenant_rejected():
    with pytest.raises(ValueError, match="unknown_tenant"):
        resolve_header_against_session(TENANT_A, "other-tenant")


def test_contextvar_roundtrip():
    assert current_tenant_or_default() == TENANT_A
    token = set_current_tenant(TENANT_B)
    try:
        assert current_tenant_or_default() == TENANT_B
    finally:
        reset_current_tenant(token)
    assert current_tenant_or_default() == TENANT_A


def test_rag_filter_cross_tenant_negative():
    """T3：A 会话不得见到 B metadata；无 tenant_id 存量视为 A。"""
    semantic = [_chunk(1, TENANT_A), _chunk(2, TENANT_B), _chunk(3, None)]
    keyword = [_chunk(10, TENANT_B), _chunk(11, TENANT_A)]

    # 无请求租户 → 不过滤
    s0, k0 = _filter_by_request_tenant(semantic, keyword)
    assert len(s0) == 3 and len(k0) == 2

    token = set_current_tenant(TENANT_A)
    try:
        s_a, k_a = _filter_by_request_tenant(semantic, keyword)
        assert {c.id for c in s_a} == {1, 3}
        assert {c.id for c in k_a} == {11}
    finally:
        reset_current_tenant(token)

    token = set_current_tenant(TENANT_B)
    try:
        s_b, k_b = _filter_by_request_tenant(semantic, keyword)
        assert {c.id for c in s_b} == {2}
        assert {c.id for c in k_b} == {10}
    finally:
        reset_current_tenant(token)


@pytest.mark.skipif(not DB_AVAILABLE, reason="PostgreSQL not available")
async def test_sessions_latest_ok_after_switch_to_tenant_b(
    client: AsyncClient, seeded_maintainer
) -> None:
    """登录 → 切 B → GET sessions/latest（带 X-Ops-Tenant-Id:B）须 200 且有 session id。"""
    login = await client.post(
        "/api/ops/auth/login",
        json={
            "username": seeded_maintainer["user"].username,
            "invite_token": seeded_maintainer["plaintext_invite"],
        },
    )
    assert login.status_code == 200

    switch = await client.post(
        "/api/ops/auth/tenant",
        json={"tenant_id": TENANT_B},
    )
    assert switch.status_code == 200
    assert switch.json()["tenant_id"] == TENANT_B

    latest = await client.get(
        "/api/ops/chat/sessions/latest",
        headers={TENANT_HEADER: TENANT_B},
    )
    assert latest.status_code == 200
    body = latest.json()
    assert body.get("id")
    assert body["user_id"] == str(seeded_maintainer["user"].id)
