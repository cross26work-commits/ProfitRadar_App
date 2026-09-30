from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials
from app.core.auth import get_current_user
from app.core.company_context import get_current_company_id
from app.core.supabase_client import get_supabase_client
from app.services.billing import require_use


def lifecycle_path(path):
    # Lifecycle/recovery must remain available after expiry. Each retains its own auth.
    return (path in {"/onboarding","/account","/gmail/disconnect","/gmail/scheduled-sync","/auth/login","/auth/register","/auth/logout",
                    "/billing/checkout","/billing/webhook","/billing/cancel","/support/contact"}
            or path.startswith("/admin/support")
            or (path.startswith("/reply/") and path.endswith("/reconcile")))


async def enforce_entitlements(request:Request):
    if request.method not in {"POST","PUT","PATCH","DELETE"}:return
    path=request.url.path.rstrip("/")
    if lifecycle_path(path):return
    header=request.headers.get("authorization", "")
    scheme,_,token=header.partition(" ")
    credentials=HTTPAuthorizationCredentials(scheme=scheme,credentials=token) if scheme.lower()=="bearer" and token else None
    user=get_current_user(credentials)
    company=get_current_company_id(user)
    require_use(get_supabase_client(),company)
