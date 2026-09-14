from datetime import date
import pytest
from pydantic import ValidationError
from app.api.financials import aggregate,FinancialInput
from app.api.financials import with_payment_entries, PaymentInput


def test_jst_midnight_and_unknown_cost():
    rows=[{"ordered_revenue":100,"paid_amount":80,"cost":None,"confirmed_at":"2026-09-09T15:00:00Z","paid_at":"2026-09-09T14:59:59Z"}]
    day=date(2026,9,10)
    result=aggregate(rows,day,day)
    assert result["ordered_revenue"]==100 and result["paid_amount"] is None and result["gross_profit"] is None
    rows[0]["cost"]=30
    assert aggregate(rows,day,day)["gross_profit"]==70
    assert aggregate([],day,day)["ordered_revenue"] is None


def test_financial_input_forbids_spoofed_actor_and_undated_revenue():
    base={"expected_version":0,"occurred_at":"2026-09-10T00:00:00+09:00"}
    for extra in ({"company_id":"b"},{"ordered_revenue":100},{"paid_amount":0},{"cost":1.5},{"cost":True}):
        with pytest.raises(ValidationError):FinancialInput(**base,**extra)


def test_period_aggregation_keeps_payment_date_and_unknown_distinct():
    rows=[{"ordered_revenue":100,"paid_amount":0,"cost":30,"confirmed_at":"2026-09-10T00:00:00+09:00","paid_at":"2026-09-12T00:00:00+09:00"},
          {"ordered_revenue":200,"paid_amount":200,"cost":None,"confirmed_at":"2026-09-11T00:00:00+09:00","paid_at":"2026-09-12T00:00:00+09:00"}]
    totals=aggregate(rows,date(2026,9,10),date(2026,9,12))
    assert totals["ordered_revenue"]==300 and totals["paid_amount"]==200
    assert totals["cost"] is None and totals["gross_profit"] is None
    paid_only=aggregate(rows,date(2026,9,12),date(2026,9,12))
    assert paid_only["ordered_revenue"] is None and paid_only["paid_amount"]==200


def test_split_payments_preserve_legacy_and_ignore_voided_entries():
    records=[{"customer_id":"a","ordered_revenue":1000,"cost":400,"confirmed_at":"2026-09-10T00:00:00+09:00","paid_amount":100,"paid_at":"2026-09-10T00:00:00+09:00"}]
    payments=[{"customer_id":"a","amount":200,"paid_at":"2026-09-11T00:00:00+09:00"},
              {"customer_id":"a","amount":300,"paid_at":"2026-09-12T00:00:00+09:00"},
              {"customer_id":"a","amount":999,"paid_at":"2026-09-12T00:00:00+09:00","voided_at":"2026-09-12T01:00:00Z"},
              {"customer_id":"b","amount":50,"paid_at":"2026-09-12T00:00:00+09:00"}]
    rows=with_payment_entries(records,payments)
    total=aggregate(rows,date(2026,9,10),date(2026,9,12))
    assert total=={"ordered_revenue":1000,"paid_amount":650,"cost":400,"gross_profit":600,"confirmed_count":1}
    assert aggregate([r for r in rows if r["customer_id"]=="a"],date(2026,9,12),date(2026,9,12))["paid_amount"]==300
    assert sum(aggregate(rows,date(2026,9,d),date(2026,9,d))["paid_amount"] for d in (10,11,12))==650


@pytest.mark.parametrize("change",[{"amount":True},{"amount":0},{"amount":1.5},{"paid_at":"2026-09-10"},{"company_id":"b"}])
def test_payment_input_requires_positive_exact_amount_dated_and_no_tenant_override(change):
    with pytest.raises(ValidationError):
        PaymentInput(**({"operation_id":"00000000-0000-4000-8000-000000000001","amount":10,"paid_at":"2026-09-10T00:00:00+09:00"}|change))
