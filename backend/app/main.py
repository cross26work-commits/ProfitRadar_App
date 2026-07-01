from fastapi import FastAPI

app = FastAPI(
    title="Profit Radar API",
    version="0.1.0",
    description="Backend API for Profit Radar App"
)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "profit-radar-api"
    }


from app.api.leads import router as leads_router
from app.api.customers import router as customers_router
from app.api.results import router as results_router
from app.api.gmail import router as gmail_router
from app.api.sms import router as sms_router
from app.api.ai import router as ai_router
from app.api.settings import router as settings_router

app.include_router(leads_router)
app.include_router(customers_router)
app.include_router(results_router)
app.include_router(gmail_router)
app.include_router(sms_router)
app.include_router(ai_router)
app.include_router(settings_router)
