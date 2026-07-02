import os
from dotenv import load_dotenv
from typing import Any

import requests
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt

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
                options={"verify_aud": False},
            )
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

        return response.json()

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=401, detail=f"Auth failed: {error}")
