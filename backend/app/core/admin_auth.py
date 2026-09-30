"""Support administrator authorization, isolated from tenant profile roles."""
import hmac
import os
from uuid import UUID

from fastapi import Depends, HTTPException

from app.core.auth import get_current_user
from app.core.company_context import _extract_user_id


def configured_admin_ids() -> tuple[str, ...]:
    values = []
    for raw in os.getenv("SUPPORT_ADMIN_USER_IDS", "").split(","):
        candidate = raw.strip()
        if not candidate:
            continue
        try:
            values.append(str(UUID(candidate)))
        except ValueError:
            raise RuntimeError("Support administrator configuration is invalid") from None
    if not values:
        raise RuntimeError("Support administrator configuration is unavailable")
    return tuple(dict.fromkeys(values))


def require_support_admin(user: dict = Depends(get_current_user)) -> str:
    actor = _extract_user_id(user)
    try:
        allowed = configured_admin_ids()
    except RuntimeError:
        raise HTTPException(503, "Support administration unavailable") from None
    if not actor or not any(hmac.compare_digest(actor, candidate) for candidate in allowed):
        raise HTTPException(403, "Administrator access required")
    return actor
