"""Ops Desk auth dependencies."""
from __future__ import annotations

import inspect
import secrets
from datetime import datetime

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import OpsSession, OpsUser
from app.db.session import get_db
from app.ops.security import hash_token


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> OpsUser:
    """Resolve current user from session cookie."""
    session_cookie = request.cookies.get(settings.session_cookie_name)
    if not session_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    token_hash = hash_token(session_cookie)
    now = datetime.utcnow()

    result = await db.execute(
        select(OpsSession).where(
            OpsSession.token_hash == token_hash,
            OpsSession.expires_at > now,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session"
        )

    result = await db.execute(select(OpsUser).where(OpsUser.id == session.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return user


async def require_maintainer(user: OpsUser = Depends(get_current_user)) -> OpsUser:
    """Require maintainer role."""
    if user.role != "maintainer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Maintainer role required",
        )
    return user


def _extract_bearer(request: Request) -> str | None:
    raw = request.headers.get("Authorization")
    if not raw:
        return None
    scheme, _, token = raw.partition(" ")
    if scheme.lower() != "bearer":
        return None
    return token.strip()


async def _resolve_cookie_user(request: Request, db: AsyncSession) -> OpsUser:
    """走 cookie 用户解析，并尊重 FastAPI dependency_overrides（现有单测）。"""
    override = request.app.dependency_overrides.get(get_current_user)
    target = override or get_current_user
    result = target(request, db)
    if inspect.isawaitable(result):
        return await result
    return result


async def require_admin_sync(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> OpsUser | None:
    """Admin sync：Bearer 机读 或 cookie maintainer。

    OPS_ADMIN_SYNC_TOKEN 为空则 Bearer 路径禁用（带 Bearer 一律 401）。
    禁止把 token 写入日志。
    """
    presented = _extract_bearer(request)
    if presented is not None:
        configured = (settings.ops_admin_sync_token or "").strip()
        if configured and secrets.compare_digest(presented, configured):
            return None
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user = await _resolve_cookie_user(request, db)
    if user.role != "maintainer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Maintainer role required",
        )
    return user


CurrentUser = Depends(get_current_user)
MaintainerUser = Depends(require_maintainer)
AdminSyncAuth = Depends(require_admin_sync)
