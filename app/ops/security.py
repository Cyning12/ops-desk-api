"""Auth/security helpers."""

from __future__ import annotations

import hmac
import secrets
from hashlib import sha256

from app.config import settings


def generate_session_token() -> str:
    """Generate a new opaque session token."""
    return secrets.token_urlsafe(32)


def generate_invite_token() -> str:
    """Generate a new opaque invite token."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Return a deterministic hash of a token using the app secret.

    The hash is used for database lookups so plaintext tokens never need to be
    persisted.
    """
    return hmac.new(
        settings.ops_desk_secret.encode("utf-8"),
        token.encode("utf-8"),
        sha256,
    ).hexdigest()
