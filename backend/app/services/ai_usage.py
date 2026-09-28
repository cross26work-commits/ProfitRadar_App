import os,time
from fastapi import HTTPException
from app.services.ai_metrics import usage_records, cost_records
from app.services.ai_budget import budget_context


def generation_limit():
    raw = os.getenv("AI_MONTHLY_GENERATION_LIMIT")
    if raw is None and os.getenv("APP_ENV") in {"development", "test"}:
        raw = "100"
    try:
        cap = int(raw or "")
        if not 1 <= cap <= 10000:
            raise ValueError()
        return cap
    except ValueError:
        raise HTTPException(503, "AI generation limit configuration unavailable") from None


def measured_generation(db,company_id,work):
    cap=generation_limit()
    run_id=db.rpc("reserve_ai_run",{"p_company_id":company_id,"p_monthly_limit":cap}).execute().data
    if not run_id: raise HTTPException(429,"AI generation limit reached")
    started=time.monotonic()
    state="failed"
    records=[]
    costs=[]
    context_token=usage_records.set(records)
    cost_token=cost_records.set(costs)
    budget_token=budget_context.set((db,company_id))
    try:
        result=work()
        state="succeeded" if not result.get("conversation_ai_error") else "fallback"
        return result
    finally:
        usage_records.reset(context_token)
        cost_records.reset(cost_token)
        budget_context.reset(budget_token)
        record={"status":state,"elapsed_ms":int((time.monotonic()-started)*1000)}
        # Received provider counters, not estimated billing. Timeout cost remains unknown.
        if records:
            record.update(input_tokens=sum(item[0] for item in records),output_tokens=sum(item[1] for item in records))
        if costs:
            record["cost_usd"] = str(sum(costs))
        db.table("ai_usage_runs").update(record).eq("company_id",company_id).eq("id",run_id).execute()
