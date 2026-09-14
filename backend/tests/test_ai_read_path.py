from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from fastapi import HTTPException
from app.api import reply
from app.services.ai_usage import measured_generation


def test_get_without_snapshot_never_instantiates_ai(monkeypatch):
    from app.engines import conversation_intelligence,conversation_reply
    forbidden=Mock(side_effect=AssertionError("GET must not call AI"))
    monkeypatch.setattr(conversation_intelligence,"ConversationIntelligenceEngine",forbidden)
    monkeypatch.setattr(conversation_reply,"ConversationReplyGenerator",forbidden)
    queries=[]
    def table(name):
        queries.append(name)
        q=Mock()
        q.select.return_value=q; q.eq.return_value=q; q.limit.return_value=q; q.order.return_value=q
        q.execute.return_value=SimpleNamespace(data=[{"id":"event","company_id":"a","customer_id":None}] if name=="profit_events" else [])
        return q
    db=Mock(); db.table.side_effect=table
    monkeypatch.setattr(reply,"get_supabase_client",lambda:db)
    result=reply.build_reply_draft("event","a")
    assert result["draft"]=="" and result["draft_provider"]=="none"
    assert queries==["profit_events","reply_drafts","gmail_send_operations","conversation_analysis_snapshots"]
    forbidden.assert_not_called()


def test_ai_limit_prevents_provider_call():
    db=Mock(); db.rpc.return_value.execute.return_value=SimpleNamespace(data=None)
    work=Mock()
    with pytest.raises(HTTPException) as exc: measured_generation(db,"a",work)
    assert exc.value.status_code==429
    work.assert_not_called()


def test_failed_generation_records_elapsed_time():
    db=Mock(); db.rpc.return_value.execute.return_value=SimpleNamespace(data="run")
    with pytest.raises(ValueError): measured_generation(db,"a",Mock(side_effect=ValueError()))
    record=db.table.return_value.update.call_args.args[0]
    assert record["status"]=="failed" and record["elapsed_ms"]>=0


def test_generation_records_provider_counters_and_resets_context():
    from app.services.ai_metrics import record_usage,usage_records
    db=Mock(); db.rpc.return_value.execute.return_value=SimpleNamespace(data="run")
    def work():
        record_usage(SimpleNamespace(usage=SimpleNamespace(input_tokens=100,output_tokens=20)))
        record_usage(SimpleNamespace(usage=SimpleNamespace(input_tokens=150,output_tokens=30)))
        return {}
    measured_generation(db,"a",work)
    record=db.table.return_value.update.call_args.args[0]
    assert record["input_tokens"]==250 and record["output_tokens"]==50
    assert usage_records.get() is None


def test_conversation_clients_disable_implicit_retries(monkeypatch):
    from app.engines import conversation_intelligence,conversation_reply
    monkeypatch.setenv("OPENAI_API_KEY","synthetic")
    for module,klass in [(conversation_intelligence,"ConversationIntelligenceEngine"),(conversation_reply,"ConversationReplyGenerator")]:
        client=Mock();monkeypatch.setattr(module,"OpenAI",client)
        getattr(module,klass)()
        assert client.call_args.kwargs["timeout"]==30.0
        assert client.call_args.kwargs["max_retries"]==0
