"""Provider/storage substitutes: NOT real Gmail or PostgreSQL evidence."""
import base64
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from googleapiclient.errors import HttpError
from app.services.gmail_sync import synchronize,normalize
from app.services.gmail_sync import normalize_sent_inquiry


def test_sent_proposal_is_outgoing_not_a_detected_reply():
    row=detail('sent',labels=['SENT'])
    row['payload']['headers']=[{'name':'From','value':'me@example.invalid'},{'name':'To','value':'Peer <peer@example.invalid>'},{'name':'Subject','value':'お見積のご提案'}]
    assert normalize(row,'me@example.invalid') is None
    record=normalize_sent_inquiry(row,'me@example.invalid')
    assert record['direction']=='outgoing' and record['sender']=='peer@example.invalid'
    row['payload']['headers'].append({'name':'Cc','value':'other@example.invalid'})
    assert normalize_sent_inquiry(row,'me@example.invalid') is None


def detail(i,labels=None,body="見積もりをお願いします"):
    return {"id":str(i),"threadId":"thread"+str(i),"internalDate":"1800000000000","labelIds":labels or ["INBOX"],
        "payload":{"mimeType":"text/plain","headers":[{"name":"From","value":"Fixture <client@example.invalid>"},{"name":"Subject","value":"問い合わせ"}],"body":{"data":base64.urlsafe_b64encode(body.encode()).decode()}}}


class MemoryStore:
    def __init__(self):
        self.state={"version":0};self.records={};self.fail=False
    def load(self):return deepcopy(self.state)
    def commit(self,previous,state,records):
        if self.fail and records:raise RuntimeError("simulated transaction failure")
        assert previous["version"]==self.state["version"]
        inserted=0
        for r in records:
            if r["message_id"] not in self.records:inserted+=1
            self.records[r["message_id"]]=r
        self.state={**deepcopy(state),"version":previous["version"]+1,"mailbox":"me@example.invalid"}
        return {"version":self.state["version"],"inserted":inserted}


def provider(pages):
    api=Mock();api.users.return_value=api;api.messages.return_value=api;api.history.return_value=api
    api.getProfile.return_value.execute.return_value={"historyId":"10"}
    def listing(**kw):
        q=Mock();q.execute.return_value=pages[kw.get("pageToken")];return q
    api.list.side_effect=listing
    api.get.side_effect=lambda **kw:SimpleNamespace(execute=lambda:detail(kw["id"]))
    api.threads.return_value.get.return_value.execute.return_value={"messages":[]}
    return api


def test_more_than_100_resume_persistent_page_and_dedupe():
    pages={None:{"messages":[{"id":str(i)} for i in range(100)],"nextPageToken":"p2"},"p2":{"messages":[{"id":str(i)} for i in range(100,151)]}}
    api=provider(pages);store=MemoryStore()
    assert synchronize(api,store,"me@example.invalid",max_pages=1)["has_more"]
    assert len(store.records)==100 and store.state["page_token"]=="p2"
    synchronize(api,store,"me@example.invalid",max_pages=1)
    assert len(store.records)==151 and store.state["history_id"]=="10"
    api.list.side_effect=lambda **kw:SimpleNamespace(execute=lambda:{"historyId":"12","history":[{"messagesAdded":[{"message":{"id":"150"}},{"message":{"id":"151"}}]}]})
    result=synchronize(api,store,"me@example.invalid")
    assert result["count"]==1 and len(store.records)==152
    assert store.state["caught_up"] and store.state["history_id"]=="12"


def test_page_db_failure_does_not_advance_then_retries_same_page():
    store=MemoryStore();store.fail=True;api=provider({None:{"messages":[{"id":"1"}]}})
    with pytest.raises(RuntimeError,match="simulated transaction failure"):synchronize(api,store,"me@example.invalid",max_pages=1)
    assert store.state["mode"]=="full" and store.state["page_token"] is None and not store.records
    store.fail=False;synchronize(api,store,"me@example.invalid",max_pages=1)
    assert len(store.records)==1


def test_expired_history_restarts_full_with_original_window():
    store=MemoryStore();store.state={"version":2,"mode":"delta","mailbox":"me@example.invalid","history_id":"old","initial_since":123,"page_token":None}
    api=provider({});api.list.side_effect=HttpError(SimpleNamespace(status=404,reason="gone"),b'{}')
    synchronize(api,store,"me@example.invalid",max_pages=1)
    assert store.state["mode"]=="full" and store.state["initial_since"]==123
    assert store.state["history_id"]=="10"


@pytest.mark.parametrize("status",[401,429,500])
def test_provider_failure_never_advances_page(status):
    from fastapi import HTTPException
    store=MemoryStore();api=provider({})
    api.list.side_effect=HttpError(SimpleNamespace(status=status,reason="provider"),b'{}')
    with pytest.raises(HTTPException) as exc:synchronize(api,store,"me@example.invalid")
    assert exc.value.status_code==503 and store.state["version"]==1


def test_read_mail_included_sent_and_optout_suppressed():
    assert normalize(detail(1,labels=["INBOX"]),"me@example.invalid")["candidate"]
    assert normalize(detail(2,labels=["SENT"]),"me@example.invalid") is None
    row=normalize(detail(3,body="配信停止してください"),"me@example.invalid")
    assert row["suppressed"] and not row["candidate"]


def test_large_history_page_partial_commit_failure_replays_without_loss():
    store = MemoryStore()
    store.state = {"version": 1, "mode": "delta", "mailbox": "me@example.invalid",
                   "history_id": "10", "initial_since": 123, "page_token": None}
    api = provider({None: {"historyId": "20", "history": [{"messagesAdded": [
        {"message": {"id": str(i)}} for i in range(1201)]}]}})
    original = store.commit
    calls = 0
    def fail_second(previous, state, records):
        nonlocal calls
        calls += bool(records)
        if calls == 2:
            raise RuntimeError("simulated transaction failure")
        assert len(records) <= 500
        return original(previous, state, records)
    store.commit = fail_second
    with pytest.raises(RuntimeError, match="simulated transaction failure"):
        synchronize(api, store, "me@example.invalid",max_details=2000)
    assert len(store.records) == 500 and store.state["history_id"] == "10"
    assert not store.state["caught_up"]
    store.commit = original
    total=0
    for _ in range(3):total+=synchronize(api, store, "me@example.invalid")["count"]
    assert total == 701 and len(store.records) == 1201
    assert store.state["history_id"] == "20" and store.state["caught_up"]
    assert synchronize(api, store, "me@example.invalid")["count"] == 0


def test_pending_ids_resume_without_relisting_a_changed_provider_page():
    api=provider({None:{"messages":[{"id":str(i)} for i in range(51)]}})
    store=MemoryStore()
    result=synchronize(api,store,"me@example.invalid",max_details=20)
    assert result['has_more'] and len(store.records)==20 and len(store.state['pending_ids'])==31
    api.list.side_effect=AssertionError('Must use persisted IDs, not a changed listing')
    synchronize(api,store,"me@example.invalid",max_details=20)
    synchronize(api,store,"me@example.invalid",max_details=20,max_pages=1)
    assert len(store.records)==51 and not store.state.get('pending_ids') and store.state['mode']=='delta'


def test_detail_failure_on_second_page_preserves_resume_cursor():
    from fastapi import HTTPException
    api = provider({None: {"messages": [{"id": "1"}], "nextPageToken": "p2"},
                    "p2": {"messages": [{"id": "2"}, {"id": "3"}]}})
    store = MemoryStore()
    synchronize(api, store, "me@example.invalid", max_pages=1)
    api.get.side_effect = HttpError(SimpleNamespace(status=429, reason="limited"), b'{}')
    with pytest.raises(HTTPException) as error:
        synchronize(api, store, "me@example.invalid", max_pages=1)
    assert error.value.status_code == 503
    assert store.state["page_token"] == "p2" and len(store.records) == 1
    api.get.side_effect = lambda **kw: SimpleNamespace(execute=lambda: detail(kw["id"]))
    synchronize(api, store, "me@example.invalid", max_pages=1)
    assert len(store.records) == 3 and store.state["mode"] == "delta"


def test_candidate_thread_recovers_nonkeyword_reply_without_other_sender_or_sent():
    from app.services.gmail_sync import expand_candidate_threads
    candidate = detail("inquiry")
    candidate["threadId"] = "same"
    reply = detail("reply", body="ありがとうございます")
    reply["threadId"] = "same"
    reply["payload"]["headers"][1]["value"] = "Re: ご連絡"
    other = deepcopy(reply); other["id"]="other"
    other["payload"]["headers"][0]["value"]="other@example.invalid"
    sent=deepcopy(reply);sent["id"]="sent";sent["labelIds"]=["SENT"]
    api=provider({})
    api.threads.return_value.get.return_value.execute.return_value={"messages":[candidate,reply,other,sent]}
    result=expand_candidate_threads(api,[normalize(candidate,"me@example.invalid")],"me@example.invalid",1)
    assert {r["message_id"] for r in result}=={"inquiry","reply"}
    assert all(r["candidate"] for r in result)


def test_html_mail_is_text_only_and_alternative_not_duplicated():
    from app.services.gmail_sync import plain_text
    html={"mimeType":"text/html","body":{"data":base64.urlsafe_b64encode(b'<style>hidden</style><p>Inquiry &amp; quote</p><script>private()</script>').decode()}}
    assert plain_text(html).strip()=="Inquiry & quote"
    plain={"mimeType":"text/plain","body":{"data":base64.urlsafe_b64encode(b'Plain inquiry').decode()}}
    assert plain_text({"mimeType":"multipart/alternative","parts":[plain,html]})=="Plain inquiry"
