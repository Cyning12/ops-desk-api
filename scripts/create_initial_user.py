"""Create the initial maintainer user and invite token.

Usage:
    python scripts/create_initial_user.py

Output (JSON):
    {"username": "admin", "invite_token": "xxx", "role": "maintainer"}

The script is idempotent for the same username: if the user already exists,
a new invite token is created for that user. It is **not** idempotent for the
invite token itself; each run creates a new token.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta

from sqlalchemy import select

from app.db.models import OpsInviteToken, OpsUser
from app.db.session import AsyncSessionLocal
from app.ops.security import generate_invite_token, hash_token

DEFAULT_USERNAME = "admin"
DEFAULT_ROLE = "maintainer"


async def main() -> None:
    """Create initial user and invite token."""
    async with AsyncSessionLocal() as db:
        username = DEFAULT_USERNAME
        role = DEFAULT_ROLE

        # Upsert user by username to keep the script safe to re-run.
        user = await db.scalar(
            select(OpsUser).where(OpsUser.username == username)
        )
        if user is None:
            user = OpsUser(username=username, role=role)
            db.add(user)
            await db.flush()

        plaintext_token = generate_invite_token()
        invite = OpsInviteToken(
            token=hash_token(plaintext_token),
            role=role,
            expires_at=datetime.utcnow() + timedelta(days=365),
        )
        db.add(invite)
        await db.commit()

        print(
            json.dumps(
                {
                    "username": user.username,
                    "invite_token": plaintext_token,
                    "role": user.role,
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
