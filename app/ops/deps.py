"""Ops Desk auth dependencies."""
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OpsSession, OpsUser
from app.db.session import get_db


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> OpsUser:
    """Resolve current user from session cookie."""
    session_cookie = request.cookies.get("ops_session")
    if not session_cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # TODO: hash cookie and compare token_hash
    result = await db.execute(select(OpsSession).where(OpsSession.token_hash == session_cookie))
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    result = await db.execute(select(OpsUser).where(OpsUser.id == session.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


async def require_maintainer(user: OpsUser = Depends(get_current_user)) -> OpsUser:
    """Require maintainer role."""
    if user.role != "maintainer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Maintainer role required",
        )
    return user


CurrentUser = Depends(get_current_user)
MaintainerUser = Depends(require_maintainer)
