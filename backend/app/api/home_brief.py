from fastapi import APIRouter, Depends

from app.services.home_brief_service import build_home_brief
from app.core.company_context import get_current_company_id

router = APIRouter(prefix="/home-brief", tags=["home-brief"])


@router.get("")
def home_brief(company_id: str = Depends(get_current_company_id)):
    return build_home_brief(company_id=company_id)
