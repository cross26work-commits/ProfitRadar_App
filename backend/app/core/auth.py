import os
from dotenv import load_dotenv
from typing import Any

import requests
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

load_dotenv()

security = HTTPBearer(auto_error=False)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credentials.credentials

    try:
        if SUPABASE_JWT_SECRET:
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
                issuer=f"{SUPABASE_URL.rstrip('/')}/auth/v1",
                options={"require": ["exp", "sub", "iss", "aud"]},
            )
            if payload.get("role") != "authenticated" or not payload.get("sub"):
                raise HTTPException(status_code=401, detail="Invalid token")
            return payload

        if not SUPABASE_URL:
            raise HTTPException(status_code=500, detail="SUPABASE_URL is not configured")

        response = requests.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": os.getenv("SUPABASE_ANON_KEY", ""),
            },
            timeout=10,
        )

        if response.status_code >= 400:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = response.json()
        if not isinstance(user, dict) or not user.get("id"):
            raise HTTPException(status_code=401, detail="Invalid token")
        return user

    except HTTPException:
        raise
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Authentication temporarily unavailable") from None
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token") from None
