from fastapi import APIRouter, Query

from app.services.home_brief_service import build_home_brief

router = APIRouter(prefix="/home-brief", tags=["home-brief"])


@router.get("")
def home_brief(company_id: str = Query(...)):
    return build_home_brief(company_id=company_id)
