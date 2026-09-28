from datetime import date,datetime,timedelta,timezone
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,ConfigDict,Field,AwareDatetime,model_validator
from postgrest.exceptions import APIError
from app.core.auth import get_current_user
from app.core.company_context import get_current_company_id,_extract_user_id
from app.core.supabase_client import get_supabase_client
from app.services.billing import require_use

router=APIRouter(prefix="/financials",tags=["financials"])
JPY=Annotated[int,Field(strict=True,ge=0,le=10**12)]
JST=timezone(timedelta(hours=9))


class FinancialInput(BaseModel):
    model_config=ConfigDict(extra="forbid")
    expected_version:Annotated[int,Field(strict=True,ge=0)]
    expected_revenue:JPY|None=None
    ordered_revenue:JPY|None=None
    paid_amount:JPY|None=None
    cost:JPY|None=None
    occurred_at:AwareDatetime
    confirmed_at:AwareDatetime|None=None
    paid_at:AwareDatetime|None=None
    @model_validator(mode="after")
    def dates_required(self):
        if self.ordered_revenue is not None and self.confirmed_at is None:raise ValueError("Confirmed date required")
        if self.paid_amount is not None and self.paid_at is None:raise ValueError("Payment date required")
        return self


@router.put("/{event_id}")
def save(event_id:str,payload:FinancialInput,user:dict=Depends(get_current_user),company_id:str=Depends(get_current_company_id)):
    db=get_supabase_client()
    if not db.table("profit_events").select("id").eq("company_id",company_id).eq("id",event_id).execute().data:raise HTTPException(404,"Event not found")
    require_use(db,company_id)
    try:
        return db.rpc("save_financial_record",{"p_company_id":company_id,"p_user_id":_extract_user_id(user),"p_event_id":event_id,"p_expected_version":payload.expected_version,"p_record":payload.model_dump(mode="json",exclude={"expected_version"})}).execute().data
    except APIError as exc:
        raise HTTPException(409 if exc.code=="40001" else 503,"Financial record could not be saved") from None


def aggregate(rows,start,end):
    def inside(value):
        return value is not None and start<=datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(JST).date()<=end
    confirmed=[r for r in rows if inside(r.get("confirmed_at"))]
    payments=[r for r in rows if inside(r.get("paid_at"))]
    def total(items,key):
        return sum(r[key] for r in items) if items and all(r.get(key) is not None for r in items) else None
    revenue=total(confirmed,"ordered_revenue");cost=total(confirmed,"cost")
    return {"ordered_revenue":revenue,"paid_amount":total(payments,"paid_amount"),"cost":cost,
            "gross_profit":revenue-cost if revenue is not None and cost is not None else None,"confirmed_count":len(confirmed)}


def all_company_rows(db,table,company_id,order):
    rows=[];offset=0
    while True:
        batch=db.table(table).select("*").eq("company_id",company_id).order(order).range(offset,offset+499).execute().data or []
        rows.extend(batch)
        if len(batch)<500:return rows
        offset+=500


def with_payment_entries(records,payments):
    # Old paid_amount remains a separately confirmed historical payment. New
    # entries are additional receipts, never another copy of that old amount.
    return [*records,*[{"customer_id":p["customer_id"],"paid_amount":p["amount"],"paid_at":p["paid_at"]}
                      for p in payments if p.get("voided_at") is None]]


def period_bounds(start:date|None,end:date|None,now:datetime|None=None):
    """Default summary is current month-to-date in Japan, not only today."""
    today=(now or datetime.now(JST)).astimezone(JST).date()
    return start or today.replace(day=1), end or today


@router.get("/summary")
def summary(start:date|None=None,end:date|None=None,company_id:str=Depends(get_current_company_id)):
    start,end=period_bounds(start,end)
    if end<start or (end-start).days>366:raise HTTPException(422,"Period must be within 367 days")
    db=get_supabase_client()
    rows=with_payment_entries(all_company_rows(db,"financial_records",company_id,"profit_event_id"),all_company_rows(db,"financial_payments",company_id,"id"))
    names={c["id"]:c.get("name") or "顧客" for c in all_company_rows(db,"customers",company_id,"id")}
    return {"timezone":"Asia/Tokyo","start":start,"end":end,"totals":aggregate(rows,start,end),
            "customers":[{"customer_id":cid,"customer_name":names.get(cid,"顧客"),**aggregate([r for r in rows if r["customer_id"]==cid],start,end)} for cid in sorted({r["customer_id"] for r in rows})],
            "definition":"売上は手動受注確定日、入金は入金日。粗利＝受注売上−原価。不明はnull。旧actual_profitは含めません。"}


@router.get("/{event_id}")
def read(event_id:str,company_id:str=Depends(get_current_company_id)):
    db=get_supabase_client()
    if not db.table("profit_events").select("id").eq("id",event_id).eq("company_id",company_id).execute().data:raise HTTPException(404,"Event not found")
    rows=db.table("financial_records").select("*").eq("profit_event_id",event_id).eq("company_id",company_id).execute().data or []
    payments=db.table("financial_payments").select("id,amount,paid_at,voided_at").eq("profit_event_id",event_id).eq("company_id",company_id).order("paid_at").execute().data or []
    return {**(rows[0] if rows else {"version":0}),"payments":payments}


class PaymentInput(BaseModel):
    model_config=ConfigDict(extra="forbid")
    operation_id:UUID
    amount:Annotated[int,Field(strict=True,gt=0,le=10**12)]
    paid_at:AwareDatetime


@router.post("/{event_id}/payments")
def record_payment(event_id:str,payload:PaymentInput,user:dict=Depends(get_current_user),company_id:str=Depends(get_current_company_id)):
    db=get_supabase_client()
    if not db.table("profit_events").select("id").eq("id",event_id).eq("company_id",company_id).execute().data:raise HTTPException(404,"Event not found")
    require_use(db,company_id)
    try:
        return db.rpc("record_financial_payment",{"p_company_id":company_id,"p_user_id":_extract_user_id(user),"p_event_id":event_id,
            "p_operation_id":str(payload.operation_id),"p_amount":payload.amount,"p_paid_at":payload.paid_at.isoformat()}).execute().data
    except APIError as exc:raise HTTPException(409 if exc.code in {"40001","23505"} else 503,"Payment record unavailable") from None


class VoidInput(BaseModel):
    model_config=ConfigDict(extra="forbid")
    reason:str=Field(min_length=1,max_length=200)


@router.post("/payments/{payment_id}/void")
def void_payment(payment_id:UUID,payload:VoidInput,user:dict=Depends(get_current_user),company_id:str=Depends(get_current_company_id)):
    db=get_supabase_client()
    if not db.table("financial_payments").select("id").eq("id",str(payment_id)).eq("company_id",company_id).execute().data:raise HTTPException(404,"Payment not found")
    require_use(db,company_id)
    return db.rpc("void_financial_payment",{"p_company_id":company_id,"p_user_id":_extract_user_id(user),"p_payment_id":str(payment_id),"p_reason":payload.reason.strip()}).execute().data
