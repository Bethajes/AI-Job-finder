#!/usr/bin/env python
"""Create an admin account (Week 8 security requirement).

Admins are never created through the public API; use this CLI instead:

    python scripts/create_admin.py admin@example.com StrongPass123! Ada Lovelace

Optional flags:
    --super-admin   Also add the email to SUPER_ADMIN_EMAILS (print a hint).
"""

import argparse
import asyncio
import sys

sys.path.insert(0, ".")

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from sqlalchemy import select  # noqa: E402


async def create_admin(email: str, password: str, first_name: str, last_name: str) -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none() is not None:
            print(f"User {email} already exists; promoting to admin.")
            user = existing.scalar_one()
        else:
            user = User(
                email=email,
                phone=None,
                first_name=first_name,
                last_name=last_name,
                hashed_password=get_password_hash(password),
                role=UserRole.admin,
                is_active=True,
                is_verified=True,
                email_verified_at=user_email_verified_at(),
            )
            session.add(user)

        user.role = UserRole.admin
        user.is_active = True
        await session.commit()
        print(f"Admin ready: {user.email} (id={user.id})")


def user_email_verified_at():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or promote an admin user")
    parser.add_argument("email")
    parser.add_argument("password")
    parser.add_argument("first_name")
    parser.add_argument("last_name", nargs="?", default="Admin")
    args = parser.parse_args()

    asyncio.run(create_admin(args.email, args.password, args.first_name, args.last_name))
    print(
        "Note: add the email to SUPER_ADMIN_EMAILS in .env to enable "
        "super-admin-only operations."
    )


if __name__ == "__main__":
    main()
