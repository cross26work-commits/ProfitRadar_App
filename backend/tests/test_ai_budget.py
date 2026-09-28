"""In-memory provider/DB substitutes; integration coverage lives separately."""
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from fastapi import HTTPException
from app.services.ai_budget import create_response,budget_context
from app.services.ai_usage import generation_limit
from app.services.ai_metrics import cost_records


@pytest.fixture
def budget(monkeypatch):
    monkeypatch.setenv("AI_MODEL_MAX_RATES_JSON",'{"fixture":{"input":2,"output":8}}')
    monkeypatch.setenv("AI_COMPANY_MONTHLY_TOKENS","100000")
    monkeypatch.setenv("AI_COMPANY_MONTHLY_USD","10")
    db=Mock();db.rpc.return_value.execute.return_value=SimpleNamespace(data="reservation")
    db.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value=SimpleNamespace(data=[{}])
    client=Mock();client.responses.input_tokens.count.return_value=SimpleNamespace(input_tokens=100)
    client.responses.create.return_value=SimpleNamespace(usage=SimpleNamespace(input_tokens=100,output_tokens=20))
    token=budget_context.set((db,"a"))
    yield db,client
    budget_context.reset(token)


def test_reserves_worst_case_before_call_and_keeps_it(budget):
    db,client=budget
    create_response(client,model="fixture",instructions="rules",input="mail")
    args=db.rpc.call_args.args[1]
    assert args["p_company_id"]=="a" and args["p_tokens"]==100+256+2048
    assert args["p_cost_micro_usd"]==(100+256)*2+2048*8
    assert client.responses.create.call_args.kwargs["store"] is False
    assert db.rpc.call_count==1  # No refund even after success.


def test_success_records_actual_token_cost_from_operator_rates(budget):
    db,client=budget
    costs=[]
    token=cost_records.set(costs)
    try:
        create_response(client,model="fixture",instructions="rules",input="mail")
    finally:
        cost_records.reset(token)
    assert str(costs[0]) == "0.00036"


def test_limit_refuses_before_paid_generation(budget):
    db,client=budget;db.rpc.return_value.execute.return_value=SimpleNamespace(data=None)
    with pytest.raises(HTTPException) as error:create_response(client,model="fixture",instructions="rules",input="mail")
    assert error.value.status_code==429
    client.responses.create.assert_not_called()


@pytest.mark.parametrize("fault",["config","count","database","context"])
def test_missing_config_or_uncertain_count_fails_closed(budget,monkeypatch,fault):
    db,client=budget
    token=None
    if fault=="config":monkeypatch.delenv("AI_MODEL_MAX_RATES_JSON")
    if fault=="count":client.responses.input_tokens.count.side_effect=RuntimeError("private")
    if fault=="database":db.rpc.side_effect=RuntimeError("private")
    if fault=="context":token=budget_context.set(None)
    try:
        with pytest.raises(HTTPException) as error:create_response(client,model="fixture",instructions="rules",input="mail")
        assert error.value.status_code==503 and "private" not in error.value.detail
        client.responses.create.assert_not_called()
    finally:
        if token is not None:budget_context.reset(token)


@pytest.mark.parametrize("failure", [TimeoutError("private"), RuntimeError("private")])
def test_provider_failure_has_no_automatic_retry_or_reservation_release(budget, failure):
    db,client=budget;client.responses.create.side_effect=failure
    with pytest.raises(HTTPException) as error:create_response(client,model="fixture",instructions="rules",input="mail")
    assert error.value.status_code==503
    assert client.responses.create.call_count==1
    db.table.assert_not_called()


@pytest.mark.parametrize("value", [None, "0", "10001", "invalid"])
def test_generation_limit_fails_closed_in_production(monkeypatch, value):
    monkeypatch.setenv("APP_ENV", "production")
    if value is None:
        monkeypatch.delenv("AI_MONTHLY_GENERATION_LIMIT", raising=False)
    else:
        monkeypatch.setenv("AI_MONTHLY_GENERATION_LIMIT", value)
    with pytest.raises(HTTPException) as error:
        generation_limit()
    assert error.value.status_code == 503


def test_generation_limit_uses_configured_value(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AI_MONTHLY_GENERATION_LIMIT", "53")
    assert generation_limit() == 53
