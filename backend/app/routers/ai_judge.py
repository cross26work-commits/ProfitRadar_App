from fastapi import APIRouter, Header, HTTPException
from postgrest.exceptions import APIError

from app.core.supabase_client import SupabaseConfigError, get_supabase_client
from app.repositories.ai_judgement_repository import AIJudgementRepository
from app.services.ai_judge_service import AIJudgeService

router = APIRouter(prefix="/ai-judge", tags=["ai-judge"])


@router.post("/judge")
def judge(
    payload: dict,
    x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a"),
):
    service = AIJudgeService()
    return service.judge(company_id=x_company_id, payload=payload)


@router.post("/judge-and-save")
def judge_and_save(
    payload: dict,
    x_company_id: str = Header(default="517a5d5a-3488-4ece-91be-99034929143a"),
):
    try:
        service = AIJudgeService(
            repository=AIJudgementRepository(db=get_supabase_client())
        )
        return service.judge_and_save(company_id=x_company_id, payload=payload)
    except SupabaseConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except APIError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
