from dotenv import load_dotenv

load_dotenv(override=False)
from app.core.log_safety import configure as configure_safe_logging
configure_safe_logging()
from app.core.runtime_settings import cors_origins, validate_production
validate_production()
from app.api import account
from app.api.billing import router as billing_router
from app.api.financials import router as financials_router
from app.api.support import public_router as support_router, admin_router as admin_support_router

from app.api import reply, self_evaluation, sales_forecast, profit_events, actions, home_brief, dashboard_home, onboarding
from fastapi import FastAPI, Depends
from app.core.entitlements import enforce_entitlements
from fastapi.middleware.cors import CORSMiddleware

from app.api.ai import router as ai_router
from app.api.auth import router as auth_router
from app.api.gmail import router as gmail_router
from app.api.leads import router as leads_router
from app.api.results import router as results_router
from app.api.settings import router as settings_router
from app.api.sms import router as sms_router
from app.routers import customers as customers_v2
from app.routers import ai_judge, dashboard, learning, revenue, timeline

app = FastAPI(
    dependencies=[Depends(enforce_entitlements)],
    title="Profit Radar API",
    version="0.1.0",
    description="Backend API for Profit Radar App",
)
from app.core.error_boundary import install as install_error_boundary
install_error_boundary(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "profit-radar-api",
    }


# Legacy / current API routers
@app.get("/ready")
def readiness():
    import os
    from fastapi import HTTPException
    from app.core.billing_mode import require_database_mode
    from app.core.supabase_client import get_supabase_client
    try:
        db=get_supabase_client()
        for table,key in (("gmail_send_operations","operation_id"),("company_billing","company_id"),("gmail_work_locks","company_id"),("reply_drafts","profit_event_id"),("ai_usage_runs","id"),
                          ("ai_budget_reservations","id"),("account_deletion_jobs","id"),("account_deletion_audit","id"),
                          ("gmail_sync_cursors","company_id"),("gmail_company_sync_runs","id"),("financial_records","profit_event_id"),("financial_payments","id"),
                          ("company_business_consents","company_id"),("billing_checkout_consents","company_id"),("support_requests","id"),
                          ("support_messages","id"),("support_internal_notes","id"),("support_audit_logs","id")):
            db.table(table).select(key).limit(1).execute()
        if os.getenv("APP_ENV") not in {"development", "test"}:
            require_database_mode(db)
    except Exception:
        raise HTTPException(503,"Service not ready") from None
    return {"status":"ready"}


app.include_router(leads_router)
app.include_router(results_router)
app.include_router(gmail_router)
app.include_router(sms_router)
app.include_router(ai_router)
app.include_router(settings_router)
app.include_router(auth_router)

# Phase4+ real-data routers
app.include_router(ai_judge.router)
app.include_router(dashboard.router)
app.include_router(revenue.router)
app.include_router(timeline.router)
app.include_router(learning.router)
app.include_router(customers_v2.router)
app.include_router(actions.router)
app.include_router(home_brief.router)
app.include_router(dashboard_home.router)
app.include_router(profit_events.router)
app.include_router(sales_forecast.router)
app.include_router(self_evaluation.router)
app.include_router(reply.router)
app.include_router(onboarding.router)
app.include_router(account.router)
app.include_router(billing_router)
app.include_router(financials_router)
app.include_router(support_router)
app.include_router(admin_support_router)
