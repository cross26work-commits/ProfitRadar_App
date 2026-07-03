from dotenv import load_dotenv

load_dotenv(override=True)

from app.api import reply, self_evaluation, sales_forecast, profit_events, actions, home_brief, dashboard_home
from fastapi import FastAPI
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
    title="Profit Radar API",
    version="0.1.0",
    description="Backend API for Profit Radar App",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
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
