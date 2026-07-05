from fastapi import APIRouter, Depends, HTTPException
from postgrest.exceptions import APIError

from app.core.supabase_client import SupabaseConfigError, get_supabase_client
from app.core.company_context import get_current_company_id
from app.repositories.ai_judgement_repository import AIJudgementRepository
from app.services.ai_judge_service import AIJudgeService

router = APIRouter(prefix="/ai-judge", tags=["ai-judge"])


@router.post("/judge")
def judge(
    payload: dict,
    company_id: str = Depends(get_current_company_id),
):
    service = AIJudgeService()
    return service.judge(company_id=company_id, payload=payload)


@router.post("/judge-and-save")
def judge_and_save(
    payload: dict,
    company_id: str = Depends(get_current_company_id),
):
    try:
        service = AIJudgeService(
            repository=AIJudgementRepository(db=get_supabase_client())
        )
        return service.judge_and_save(company_id=company_id, payload=payload)
    except SupabaseConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except APIError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
