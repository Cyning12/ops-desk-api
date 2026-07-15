"""Authentication endpoints."""
from fastapi import APIRouter, Response, status
from pydantic import BaseModel

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


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(body: LoginRequest, response: Response) -> dict:
    """Login with username and invite token, set session cookie."""
    # TODO: validate invite token, create user/session, set cookie
    return {"ok": True, "user": {"username": body.username}}


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response) -> dict:
    """Clear session cookie."""
    response.delete_cookie("ops_session")
    return {"ok": True}


@router.get("/me")
async def me() -> dict:
    """Return current user info."""
    # TODO: use get_current_user dependency
    return {"user": None}
