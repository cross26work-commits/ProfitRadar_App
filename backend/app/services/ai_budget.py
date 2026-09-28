"""Pre-authorize each paid call. Never refund uncertain or worst-case reservations.

Limits and maximum model rates are operator configuration, not vendor prices.
No prompts, keys, or provider exception text are persisted here.
"""
import json
import os
from contextvars import ContextVar
from decimal import Decimal, ROUND_CEILING
from fastapi import HTTPException
from app.services.ai_metrics import cost_records

budget_context = ContextVar("ai_budget_context", default=None)


def settings(model):
    try:
        rates = json.loads(os.environ["AI_MODEL_MAX_RATES_JSON"])[model]
        incoming, outgoing = Decimal(str(rates["input"])), Decimal(str(rates["output"]))
        tokens = int(os.environ["AI_COMPANY_MONTHLY_TOKENS"])
        cost = Decimal(os.environ["AI_COMPANY_MONTHLY_USD"])
        if not all(x.is_finite() and x > 0 for x in (incoming, outgoing, cost)) or not 1 <= tokens <= 100000000:
            raise ValueError()
        return incoming, outgoing, tokens, int((cost * 1000000).to_integral_value(rounding=ROUND_CEILING))
    except (KeyError, ValueError, TypeError, ArithmeticError):
        raise HTTPException(503, "AI budget configuration unavailable") from None


def create_response(client, *, model, instructions, input, store=False, max_output_tokens=2048):
    context = budget_context.get()
    if context is None:
        raise HTTPException(503, "Verified AI company context required")
    db, company = context
    rates_in, rates_out, token_limit, cost_limit = settings(model)
    if (not isinstance(input,str) or not isinstance(instructions,str)
            or len(input.encode("utf-8"))+len(instructions.encode("utf-8")) > 160000
            or type(max_output_tokens) is not int or not 1 <= max_output_tokens <= 2048):
        raise HTTPException(413, "AI input or output limit exceeded")
    try:
        counted = client.responses.input_tokens.count(model=model, instructions=instructions, input=input).input_tokens
        if type(counted) is not int or counted < 0 or counted > 100000:
            raise ValueError()
        # Framing margin; untrusted tools/images/history references aren't accepted.
        incoming = counted + 256
        maximum = int((incoming*rates_in + max_output_tokens*rates_out).to_integral_value(rounding=ROUND_CEILING))
        reservation = db.rpc("reserve_ai_budget", {"p_company_id":company,"p_model":model,
            "p_tokens":incoming+max_output_tokens,"p_cost_micro_usd":maximum,
            "p_token_limit":token_limit,"p_cost_limit_micro_usd":cost_limit}).execute().data
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(503,"AI budget reservation unavailable") from None
    if not reservation:
        raise HTTPException(429,"AI usage limit reached")
    try:
        response = client.responses.create(model=model,instructions=instructions,input=input,
            store=False,max_output_tokens=max_output_tokens)
    except Exception:
        # Keep reservation, including after a timeout or worker death. Never retry.
        raise HTTPException(503,"AI result unknown; reserved budget retained") from None
    usage = getattr(response,"usage",None)
    actual_in = getattr(usage,"input_tokens",None)
    actual_out = getattr(usage,"output_tokens",None)
    if type(actual_in) is not int or type(actual_out) is not int or not 0 <= actual_in <= incoming or not 0 <= actual_out <= max_output_tokens:
        raise HTTPException(503,"AI usage could not be verified; reserved budget retained")
    try:
        changed = db.table("ai_budget_reservations").update({"status":"succeeded",
            "actual_input_tokens":actual_in,"actual_output_tokens":actual_out}).eq("id",reservation).eq("company_id",company).execute().data
        if not changed: raise ValueError()
    except Exception:
        raise HTTPException(503,"AI usage recording unavailable; reserved budget retained") from None
    costs = cost_records.get()
    if costs is not None:
        costs.append((Decimal(actual_in) * rates_in + Decimal(actual_out) * rates_out) / Decimal(1000000))
    return response
