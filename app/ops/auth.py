"""Authentication endpoints."""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import OpsInviteToken, OpsSession, OpsUser
from app.db.session import get_db
from app.ops.deps import CurrentUser
from app.ops.security import generate_session_token, hash_token
from app.ops.tenant_context import TENANT_A, normalize_tenant

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """Login request body."""

    username: str
    invite_token: str


class UserOut(BaseModel):
    """Public user info."""

    id: str
    username: str
    role: str


def _set_session_cookie(response: Response, token: str) -> None:
    """Set the HttpOnly session cookie."""
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=int(timedelta(hours=settings.session_ttl_hours).total_seconds()),
        path=settings.session_cookie_path,
        secure=settings.session_cookie_secure,
        httponly=settings.session_cookie_httponly,
        samesite=settings.session_cookie_samesite,
    )


def _delete_session_cookie(response: Response) -> None:
    """Delete the session cookie."""
    response.delete_cookie(
        key=settings.session_cookie_name,
        path=settings.session_cookie_path,
        samesite=settings.session_cookie_samesite,
    )


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Login with username and invite token, set session cookie."""
    token_hash = hash_token(body.invite_token)
    now = datetime.utcnow()

    invite_result = await db.execute(
        select(OpsInviteToken).where(
            OpsInviteToken.token == token_hash,
            OpsInviteToken.used_by_user_id.is_(None),
            OpsInviteToken.expires_at > now,
        )
    )
    invite = invite_result.scalar_one_or_none()
    if invite is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired invite token",
        )

    user_result = await db.execute(
        select(OpsUser).where(OpsUser.username == body.username)
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        user = OpsUser(username=body.username, role=invite.role)
        db.add(user)
        await db.flush()

    # Consume the invite token.
    invite.used_by_user_id = user.id
    invite.used_at = now

    plaintext_token = generate_session_token()
    session = OpsSession(
        user_id=user.id,
        token_hash=hash_token(plaintext_token),
        expires_at=now + timedelta(hours=settings.session_ttl_hours),
    )
    db.add(session)
    await db.commit()

    _set_session_cookie(response, plaintext_token)

    return {
        "ok": True,
        "user": UserOut(id=str(user.id), username=user.username, role=user.role).model_dump(),
    }


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Clear session cookie and invalidate the DB session."""
    cookie_token = request.cookies.get(settings.session_cookie_name)
    if cookie_token:
        token_hash = hash_token(cookie_token)
        await db.execute(
            delete(OpsSession).where(OpsSession.token_hash == token_hash)
        )
        await db.commit()

    _delete_session_cookie(response)
    return {"ok": True}


@router.get("/me")
async def me(request: Request, user: OpsUser = CurrentUser) -> dict:
    """Return current user info and session tenant."""
    tenant_id = getattr(request.state, "ops_tenant_id", TENANT_A)
    return {
        "user": UserOut(
            id=str(user.id), username=user.username, role=user.role
        ).model_dump(),
        "tenant_id": tenant_id,
    }


class SwitchTenantRequest(BaseModel):
    """切换当前 session 租户（Fixture 轨仅允许试点 A/B）。"""

    tenant_id: str


@router.post("/tenant", status_code=status.HTTP_200_OK)
async def switch_tenant(
    body: SwitchTenantRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: OpsUser = CurrentUser,
) -> dict:
    """写入 session.tenant_id。本请求不校验旧头（切换动作本身）。"""
    del user
    try:
        tenant_id = normalize_tenant(body.tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    cookie_token = request.cookies.get(settings.session_cookie_name)
    if not cookie_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token_hash = hash_token(cookie_token)
    result = await db.execute(select(OpsSession).where(OpsSession.token_hash == token_hash))
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    session.tenant_id = tenant_id
    await db.commit()
    request.state.ops_tenant_id = tenant_id
    return {"ok": True, "tenant_id": tenant_id}
