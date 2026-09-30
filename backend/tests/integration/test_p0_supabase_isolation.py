"""Real local Auth/PostgREST. Apply migrations first; synthetic fixtures retained.

No manually supplied JWTs. Never enable against shared or production databases.
"""
import os
import secrets
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit
from uuid import uuid4
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from postgrest.exceptions import APIError
from supabase import create_client


def validate_target(url, expected, permission):
    p = urlsplit(url)
    if (permission != "CREATE_DISPOSABLE_FIXTURES" or url != expected
            or p.scheme != "http" or p.hostname not in {"127.0.0.1", "localhost"}
            or p.port != 54321 or p.username or p.password
            or p.path not in {"", "/"} or p.query or p.fragment):
        raise ValueError("Explicit matching disposable loopback target required")


@pytest.mark.parametrize("url,expected,permission", [
    ("https://shared.supabase.co", "https://shared.supabase.co", "CREATE_DISPOSABLE_FIXTURES"),
    ("http://localhost:54321", "http://localhost:54322", "CREATE_DISPOSABLE_FIXTURES"),
    ("http://localhost:54321", "http://localhost:54321", ""),
    ("http://user@localhost:54321", "http://user@localhost:54321", "CREATE_DISPOSABLE_FIXTURES"),
])
def test_target_guard_rejects_unsafe_configuration(url, expected, permission):
    with pytest.raises(ValueError, match="disposable loopback"):
        validate_target(url, expected, permission)


@pytest.fixture(scope="module")
def environment():
    url = os.getenv("P0_SUPABASE_TEST_URL", "")
    if not url:
        pytest.skip("Disposable local Supabase absent; real Auth/DB NOT verified")
    validate_target(url, os.getenv("P0_SUPABASE_EXPECTED_URL"), os.getenv("P0_ALLOW_FIXTURE_WRITES"))
    anon = os.environ["P0_SUPABASE_TEST_ANON_KEY"]
    service = create_client(url, os.environ["P0_SUPABASE_TEST_SERVICE_KEY"])
    from app.core import auth, company_context
    from app.api import onboarding, leads, profit_events, reply, financials, account
    from app.routers import customers
    patch = pytest.MonkeyPatch()
    patch.setattr(auth, "SUPABASE_URL", url)
    patch.setattr(auth, "SUPABASE_JWT_SECRET", "")
    patch.setenv("SUPABASE_ANON_KEY", anon)
    patch.setenv("SUPABASE_URL", url)
    patch.setenv("ACCOUNT_AUDIT_RETENTION_DAYS", "7")
    patch.setattr(onboarding, "get_supabase_client", lambda: service)
    for module in (company_context, leads, profit_events, reply, customers, financials, account):
        patch.setattr(module, "get_supabase_client", lambda: service)
    def forbidden_provider(*args, **kwargs):
        raise AssertionError("External provider must not be called in isolation tests")
    patch.setattr(reply, "build", forbidden_provider)
    app = FastAPI()
    app.include_router(onboarding.router)
    for module in (leads, profit_events, reply, customers, financials, account):
        app.include_router(module.router)
    api = TestClient(app)
    actors = []
    for _ in range(2):
        email, password = f"p0-{uuid4().hex}@example.invalid", secrets.token_urlsafe(32)
        user = service.auth.admin.create_user({"email": email, "password": password, "email_confirm": True}).user
        browser = create_client(url, anon)
        session = browser.auth.sign_in_with_password({"email": email, "password": password}).session
        browser.postgrest.auth(session.access_token)
        headers = {"Authorization": f"Bearer {session.access_token}"}
        response = api.post("/onboarding", headers=headers, json={"company_name": f"P0-{user.id}", "name": "Isolated fixture", "business_use_confirmed": True})
        assert response.status_code == 200
        profile = service.table("profiles").select("id,user_id,company_id,role").eq("user_id", user.id).single().execute().data
        assert profile["role"] == "owner"
        # This disposable fixture represents a card-authorized Stripe trial.
        service.rpc("ensure_company_billing", {"p_company_id":profile["company_id"]}).execute()
        service.table("company_billing").update({"status":"trialing","trial_ends_at":(datetime.now(timezone.utc)+timedelta(days=7)).isoformat()}).eq("company_id",profile["company_id"]).execute()
        actors.append((browser, headers, profile))
        customer = service.table("customers").insert({"company_id": profile["company_id"], "name": "P0 fixture", "email": email}).execute().data[0]
        service.table("profit_events").insert({"id": profile["id"], "company_id": profile["company_id"], "customer_id": customer["id"], "title": "P0 isolation fixture", "status": "open"}).execute()
    yield api, service, actors
    patch.undo()


def test_both_users_read_own_profile_only(environment):
    actors = environment[2]
    assert actors[0][2]["company_id"] != actors[1][2]["company_id"]
    for index in range(2):
        browser, _, own = actors[index]
        other = actors[1-index][2]
        assert browser.table("profiles").select("id").eq("id", own["id"]).single().execute().data == {"id": own["id"]}
        assert browser.table("profiles").select("id").eq("id", other["id"]).execute().data == []


@pytest.mark.parametrize("table", ["customers", "messages", "profit_events", "gmail_connections"])
def test_business_select_permission_denied(environment, table):
    for browser, _, _ in environment[2]:
        with pytest.raises(APIError) as error:
            browser.table(table).select("id").limit(1).execute()
        assert error.value.code == "42501"


def test_profile_escalation_denied_without_changes(environment):
    _, service, actors = environment
    for index in range(2):
        browser, _, own = actors[index]
        with pytest.raises(APIError) as error:
            browser.table("profiles").update({"company_id": actors[1-index][2]["company_id"], "role": "admin"}).eq("id", own["id"]).execute()
        assert error.value.code == "42501"
        assert service.table("profiles").select("id,user_id,company_id,role").eq("id", own["id"]).single().execute().data == own


def test_onboarding_replay_concurrency_and_untrusted_fields(environment):
    api, service, actors = environment
    _, headers, own = actors[0]
    def replay(_):
        response = api.post("/onboarding", headers=headers, json={"company_name": "Must not create", "name": "Replay", "business_use_confirmed": True})
        assert response.status_code == 200
        assert response.json()["result"][0]["created"] is False
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(replay, range(8)))
    assert len(service.table("profiles").select("id").eq("user_id", own["user_id"]).execute().data) == 1
    assert service.table("companies").select("id").eq("name", "Must not create").execute().data == []
    assert api.post("/onboarding", headers=headers, json={"company_name": "x", "name": "x", "user_id": actors[1][2]["user_id"]}).status_code == 422


def test_missing_and_invalid_token(environment):
    api = environment[0]
    body = {"company_name": "Forbidden", "name": "Forbidden", "business_use_confirmed": True}
    assert api.post("/onboarding", json=body).status_code == 401
    assert api.post("/onboarding", json=body, headers={"Authorization": "Bearer invalid"}).status_code == 401


def test_real_jwt_api_positive_and_cross_tenant_denial(environment):
    api, service, actors = environment
    for index in range(2):
        _, headers, own = actors[index]
        other = actors[1-index][2]
        own_id, other_id = own["id"], other["id"]
        before = service.table("profit_events").select("*").eq("id", other_id).single().execute().data
        own_event = service.table("profit_events").select("customer_id").eq("id", own_id).single().execute().data
        customers = api.get("/customers", headers=headers)
        assert customers.status_code == 200
        customer_ids = {row["id"] for row in customers.json()["items"]}
        assert own_event["customer_id"] in customer_ids and before["customer_id"] not in customer_ids
        assert api.get(f"/customers/{own_event['customer_id']}", headers=headers).status_code == 200
        assert api.get(f"/customers/{before['customer_id']}", headers=headers).status_code == 404
        response = api.get("/leads", headers=headers)
        assert response.status_code == 200
        ids = {row["id"] for row in response.json()["items"]}
        assert own_id in ids and other_id not in ids
        assert api.get(f"/leads/{own_id}", headers=headers).status_code == 200
        denied = api.get(f"/leads/{other_id}?company_id={other['company_id']}", headers=headers)
        assert denied.status_code == 404 and denied.json() == {"detail": "lead not found"}
        assert api.patch(f"/profit-events/{other_id}/actual-profit", headers=headers, json={"actual_profit": 999, "company_id": other["company_id"]}).status_code == 404
        assert api.post(f"/reply/{other_id}/send", headers=headers, json={"body": "Never send", "company_id": other["company_id"]}).status_code == 404
        # This resource has no DELETE API; verify it remains unavailable, not claim RLS proof.
        assert api.delete(f"/leads/{other_id}", headers=headers).status_code == 405
        assert service.table("profit_events").select("*").eq("id", other_id).single().execute().data == before


def test_first_onboarding_concurrently_creates_exactly_one_company(environment):
    api, service, _ = environment
    email, password = f"p0-race-{uuid4().hex}@example.invalid", secrets.token_urlsafe(32)
    user = service.auth.admin.create_user({"email": email, "password": password, "email_confirm": True}).user
    browser = create_client(os.environ["P0_SUPABASE_TEST_URL"], os.environ["P0_SUPABASE_TEST_ANON_KEY"])
    session = browser.auth.sign_in_with_password({"email": email, "password": password}).session
    name = f"P0-race-{user.id}"
    def register(_):
        response = api.post("/onboarding", headers={"Authorization": f"Bearer {session.access_token}"}, json={"name": "Concurrent fixture", "company_name": name, "business_use_confirmed": True})
        assert response.status_code == 200
        return response.json()["result"][0]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(register, range(4)))
    assert sum(result["created"] for result in results) == 1
    assert len({result["company_id"] for result in results}) == 1
    assert len(service.table("profiles").select("id").eq("user_id", user.id).execute().data) == 1
    assert len(service.table("companies").select("id").eq("name", name).execute().data) == 1


def test_saved_draft_real_db_roundtrip_and_other_tenant_denial(environment):
    api, service, actors = environment
    _, a_headers, own = actors[0]
    _, b_headers, other = actors[1]
    body = {"body": "Synthetic saved draft", "subject": "Isolated test"}
    assert api.post(f"/reply/{own['id']}/draft", headers=a_headers, json=body).status_code == 200
    stored = service.table("reply_drafts").select("body,subject").eq("company_id", own["company_id"]).eq("profit_event_id", own["id"]).single().execute().data
    assert stored == body
    restored = api.get(f"/reply/{own['id']}/draft", headers=a_headers)
    assert restored.status_code == 200
    assert restored.json()["draft"] == body["body"] and restored.json()["draft_provider"] == "saved"
    assert api.get(f"/reply/{own['id']}/draft", headers=b_headers).status_code == 404
    assert api.post(f"/reply/{own['id']}/draft", headers=b_headers, json={**body, "body": "Forbidden"}).status_code == 404
    assert service.table("reply_drafts").select("body,subject").eq("company_id", own["company_id"]).eq("profit_event_id", own["id"]).single().execute().data == stored


@pytest.mark.parametrize("operation", ["insert", "update", "delete"])
def test_direct_customer_writes_explicitly_denied(environment, operation):
    _, service, actors = environment
    for browser, _, own in actors:
        row = service.table("customers").select("id,name,company_id").eq("company_id", own["company_id"]).single().execute().data
        query = browser.table("customers")
        if operation == "insert":
            query = query.insert({"company_id": own["company_id"], "name": "Forbidden"})
        elif operation == "update":
            query = query.update({"name": "Forbidden"}).eq("id", row["id"])
        else:
            query = query.delete().eq("id", row["id"])
        with pytest.raises(APIError) as error:
            query.execute()
        assert error.value.code == "42501"
        assert service.table("customers").select("id,name,company_id").eq("id", row["id"]).single().execute().data == row


def test_concurrent_send_claim_and_transactional_finalize(environment):
    from app.services.send_operations import claim,finalize
    _,service,actors=environment
    own=actors[0][2]
    event=service.table("profit_events").select("customer_id").eq("company_id",own["company_id"]).eq("id",own["id"]).single().execute().data
    def reserve(_):
        return claim(service,own["company_id"],own["id"],"fixture@example.invalid","Synthetic send","No email is sent",event["customer_id"])
    with ThreadPoolExecutor(max_workers=4) as pool: results=list(pool.map(reserve,range(4)))
    assert sum(result[1] for result in results)==1
    key=results[0][0]
    synthetic={"id":"synthetic-"+uuid4().hex,"threadId":"synthetic-thread"}
    finalize(service,own["company_id"],key,synthetic)
    finalize(service,own["company_id"],key,synthetic)
    logs=service.table("reply_logs").select("id").eq("company_id",own["company_id"]).eq("gmail_message_id",synthetic["id"]).execute().data
    assert len(logs)==1
    op=service.table("gmail_send_operations").select("status").eq("company_id",own["company_id"]).eq("operation_id",key).single().execute().data
    assert op["status"]=="sent"


def test_atomic_inbound_page_and_cursor_rollback(environment):
    from app.services.gmail_work import company_lock
    from app.services.gmail_sync import SyncStore
    _,service,actors=environment
    own=actors[0][2];company=own["company_id"]
    connection=service.table("gmail_connections").insert({"company_id":company,"email":"mailbox@example.invalid","token_json":{},"status":"connected"}).execute().data[0]
    with company_lock(service,company,"sync"):
        store=SyncStore(service,company,connection)
        state={"mode":"delta","history_id":"10","initial_since":1,"page_token":None,"caught_up":True}
        records=[{"message_id":"inbound-"+str(i),"thread_id":"new-thread-"+str(i),"sender":"new@example.invalid","sender_name":"Fixture","subject":"見積依頼","body":"見積をお願いします","received_at":"2026-09-10T00:00:00Z","candidate":True,"suppressed":False,"reason":"fixture"} for i in range(51)]
        original=store.load()
        pending={**state,"pending_ids":[row["message_id"] for row in records],
                 "pending_page":{"nextPageToken":"fixture-next"},"caught_up":False}
        store.commit(original,pending,[])
        original=store.load()
        assert original["pending_ids"]==pending["pending_ids"]
        assert original["pending_page"]==pending["pending_page"]
        invalid=[*records,{**records[0],"message_id":"bad","received_at":"not-a-date"}]
        with pytest.raises(APIError) as exc:store.commit(original,state,invalid)
        assert exc.value.code=="22007"
        assert store.load()==original
        assert not service.table("customers").select("id").eq("company_id",company).eq("email","new@example.invalid").execute().data
        result=store.commit(original,state,records)
        assert result["inserted"]==51
        assert store.load()["pending_ids"]==[]
        replay=store.commit(store.load(),state,records)
        assert replay["inserted"]==0
        assert len(service.table("customers").select("id").eq("company_id",company).eq("email","new@example.invalid").execute().data)==1
        assert len(service.table("gmail_inbound_receipts").select("gmail_message_id").eq("company_id",company).execute().data)==51
        # A newer short reply is seen before the older inquiry on another page.
        short={**records[0],"message_id":"short-first","thread_id":"late-candidate","candidate":False}
        assert store.commit(store.load(),state,[short])["inserted"]==0
        candidate={**short,"message_id":"inquiry-later","candidate":True}
        assert store.commit(store.load(),state,[candidate,{**short,"candidate":True}])["inserted"]==2
        assert store.commit(store.load(),state,[candidate,short])["inserted"]==0
        matching=service.table("messages").select("id").eq("company_id",company).eq("external_id","short-first").execute().data
        assert len(matching)==1
        sent={**records[0],"message_id":"sent-only-proposal","thread_id":"sent-only-thread","direction":"outgoing","sender":"sent-peer@example.invalid"}
        assert store.commit(store.load(),state,[sent])["inserted"]==1
        assert store.commit(store.load(),state,[sent])["inserted"]==0
        messages=service.table("messages").select("direction,sender,recipient").eq("company_id",company).eq("external_id",sent["message_id"]).execute().data
        assert messages==[{"direction":"outgoing","sender":"mailbox@example.invalid","recipient":"sent-peer@example.invalid"}]
        assert service.table("reply_logs").select("id").eq("company_id",company).eq("gmail_message_id",sent["message_id"]).execute().data==[]


def test_new_internal_tables_and_rpcs_are_not_browser_accessible(environment):
    _,_,actors=environment
    for browser,_,own in actors:
        for table in ("gmail_sync_cursors","gmail_inbound_receipts","operation_recovery_audit","financial_records","financial_payments","financial_record_history","ai_budget_reservations","account_deletion_jobs","account_deletion_audit"):
            with pytest.raises(APIError) as exc:browser.table(table).select("*").execute()
            assert exc.value.code=="42501"
        with pytest.raises(APIError) as exc:
            browser.rpc("recover_company_work",{"p_company_id":own["company_id"],"p_expected_owner":str(uuid4()),"p_operator_ref":"forbidden","p_ticket_ref":"forbidden","p_workers_stopped":True}).execute()
        assert exc.value.code=="42501"


def test_financials_real_jwt_roundtrip_isolation_and_version_conflict(environment):
    api, service, actors = environment
    for index in range(2):
        _, headers, own = actors[index]
        other = actors[1-index][2]
        body = {"expected_version": 0, "ordered_revenue": 1000, "paid_amount": 800,
                "cost": 400, "occurred_at": "2026-09-10T00:00:00+09:00",
                "confirmed_at": "2026-09-10T00:00:00+09:00", "paid_at": "2026-09-11T00:00:00+09:00"}
        assert api.put(f"/financials/{own['id']}", headers=headers, json=body).status_code == 200
        stored = api.get(f"/financials/{own['id']}", headers=headers)
        assert stored.status_code == 200 and stored.json()["ordered_revenue"] == 1000
        assert api.get(f"/financials/{other['id']}", headers=headers).status_code == 404
        assert api.put(f"/financials/{other['id']}", headers=headers, json=body).status_code == 404
        assert api.put(f"/financials/{own['id']}", headers=headers, json=body).status_code == 409
        assert api.get(f"/financials/{own['id']}", headers=headers).json() == stored.json()
        summary = api.get("/financials/summary?start=2026-09-10&end=2026-09-10", headers=headers)
        assert summary.status_code == 200
        assert summary.json()["totals"]["gross_profit"] == 600
        assert summary.json()["totals"]["paid_amount"] is None
        assert len(service.table("financial_record_history").select("id").eq("company_id", own["company_id"]).execute().data) == 1


def test_confirmed_gross_profit_lifecycle_jst_and_tenant_boundary(environment):
    api,service,actors=environment
    _,a_headers,a=actors[0];_,b_headers,b=actors[1]
    customer=service.table("profit_events").select("customer_id").eq("id",a["id"]).single().execute().data["customer_id"]
    def new_event():
        return service.table("profit_events").insert({"company_id":a["company_id"],"customer_id":customer,
            "title":"Synthetic financial lifecycle","status":"open"}).execute().data[0]["id"]
    def totals(headers,month):
        response=api.get(f"/financials/summary?start=2031-{month}-01&end=2031-{month}-28",headers=headers)
        assert response.status_code==200
        return response.json()["totals"]
    jan_a_before=totals(a_headers,"01");jan_b_before=totals(b_headers,"01")
    event=new_event()
    payload={"expected_version":0,"ordered_revenue":100000,"cost":0,
        "occurred_at":"2031-01-15T10:00:00+09:00","confirmed_at":"2031-01-15T10:00:00+09:00"}
    assert api.put(f"/financials/{event}",headers=a_headers,json=payload).status_code==200
    assert totals(a_headers,"01")["gross_profit"]==(jan_a_before["gross_profit"] or 0)+100000
    assert totals(b_headers,"01")==jan_b_before
    assert api.get(f"/financials/{event}",headers=b_headers).status_code==404
    assert api.put(f"/financials/{event}",headers=b_headers,json=payload).status_code==404
    # One version can be saved once. A duplicate submit cannot double count.
    assert api.put(f"/financials/{event}",headers=a_headers,json=payload).status_code==409
    assert len(service.table("financial_record_history").select("id").eq("profit_event_id",event).execute().data)==1
    changed={**payload,"expected_version":1,"ordered_revenue":150000}
    assert api.put(f"/financials/{event}",headers=a_headers,json=changed).status_code==200
    assert totals(a_headers,"01")["gross_profit"]==(jan_a_before["gross_profit"] or 0)+150000
    assert len(service.table("financial_record_history").select("id").eq("profit_event_id",event).execute().data)==2
    canceled={**payload,"expected_version":2,"ordered_revenue":None,"cost":None,"confirmed_at":None}
    assert api.put(f"/financials/{event}",headers=a_headers,json=canceled).status_code==200
    assert totals(a_headers,"01")==jan_a_before
    # Legacy endpoint must reject an own-tenant write without touching either source.
    old=service.table("profit_events").select("actual_profit,status").eq("id",event).single().execute().data
    assert api.patch(f"/profit-events/{event}/actual-profit",headers=a_headers,json={"actual_profit":999}).status_code==409
    assert service.table("profit_events").select("actual_profit,status").eq("id",event).single().execute().data==old
    first=new_event();second=new_event()
    for target,amount,confirmed in ((first,50000,"2031-01-31T23:59:00+09:00"),
                                    (second,70000,"2031-02-01T00:00:00+09:00")):
        body={**payload,"ordered_revenue":amount,"confirmed_at":confirmed}
        assert api.put(f"/financials/{target}",headers=a_headers,json=body).status_code==200
    jan=api.get("/financials/summary?start=2031-01-01&end=2031-01-31",headers=a_headers).json()["totals"]
    feb=totals(a_headers,"02")
    assert jan["gross_profit"]==(jan_a_before["gross_profit"] or 0)+50000
    assert feb["gross_profit"]==70000


def test_operator_recovery_owner_fencing_and_idempotency(environment):
    _, service, actors = environment
    company = actors[1][2]["company_id"]
    owner = str(uuid4())
    assert service.rpc("claim_gmail_work", {"p_company_id": company, "p_owner_id": owner, "p_purpose": "sync"}).execute().data is True
    params = {"p_company_id": company, "p_expected_owner": owner, "p_operator_ref": "fixture-operator",
              "p_ticket_ref": "fixture-ticket", "p_workers_stopped": True}
    for changed in ({"p_expected_owner": str(uuid4())}, {"p_workers_stopped": False}, {"p_operator_ref": None}):
        with pytest.raises(APIError) as error:
            service.rpc("recover_company_work", {**params, **changed}).execute()
        assert error.value.code == "P0001"
        assert service.table("gmail_work_locks").select("owner_id").eq("company_id",company).single().execute().data["owner_id"] == owner
    assert service.rpc("recover_company_work", params).execute().data is True
    assert service.rpc("recover_company_work", params).execute().data is False
    assert len(service.table("operation_recovery_audit").select("id").eq("company_id",company).eq("owner_id",owner).execute().data) == 1


def test_budget_concurrent_reservation_and_monthly_hard_stop(environment):
    _,service,actors=environment
    company=actors[1][2]["company_id"]
    args={"p_company_id":company,"p_model":"fixture","p_tokens":100,"p_cost_micro_usd":100,
          "p_token_limit":100,"p_cost_limit_micro_usd":100}
    def reserve(_):return service.rpc("reserve_ai_budget",args).execute().data
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(reserve,range(4)))
    assert sum(r is not None for r in results)==1
    rid=next(r for r in results if r)
    service.table("ai_budget_reservations").update({"status":"succeeded"}).eq("id",rid).eq("company_id",company).execute()
    assert reserve(None) is None  # Finished calls still consume their conservative reservation.
    for browser,_,_ in actors:
        with pytest.raises(APIError) as exc:browser.rpc("reserve_ai_budget",args).execute()
        assert exc.value.code=="42501"


def test_account_delete_real_reauthentication_and_atomic_cleanup(environment):
    api,service,_=environment
    email,password=f"delete-{uuid4().hex}@example.invalid",secrets.token_urlsafe(32)
    user=service.auth.admin.create_user({"email":email,"password":password,"email_confirm":True}).user
    browser=create_client(os.environ["P0_SUPABASE_TEST_URL"],os.environ["P0_SUPABASE_TEST_ANON_KEY"])
    session=browser.auth.sign_in_with_password({"email":email,"password":password}).session
    headers={"Authorization":f"Bearer {session.access_token}"}
    response=api.post("/onboarding",headers=headers,json={"company_name":"Deletion fixture","name":"Fixture","business_use_confirmed":True})
    assert response.status_code==200
    company=response.json()["result"][0]["company_id"]
    customer=service.table("customers").insert({"company_id":company,"name":"Delete fixture"}).execute().data[0]
    assert api.request("DELETE","/account",headers=headers,json={"password":"wrong","confirmation":"削除"}).status_code==401
    assert service.table("customers").select("id").eq("id",customer["id"]).execute().data
    response=api.request("DELETE","/account",headers=headers,json={"password":password,"confirmation":"削除"})
    assert response.status_code==200 and response.json()["success"] is True
    for table,key,val in (("profiles","user_id",user.id),("companies","id",company),("customers","company_id",company)):
        assert service.table(table).select("*").eq(key,val).execute().data==[]
    projection="id,status,completed_at,purge_after"
    jobs=service.table("account_deletion_jobs").select(projection).eq("user_id",user.id).execute().data
    assert len(jobs)==1 and jobs[0]["status"]=="completed"
    completed=datetime.fromisoformat(jobs[0]["completed_at"].replace("Z","+00:00"))
    deadline=datetime.fromisoformat(jobs[0]["purge_after"].replace("Z","+00:00"))
    assert deadline-completed==timedelta(days=7)
    service.rpc("complete_account_deletion",{"p_job_id":jobs[0]["id"]}).execute()
    assert service.table("account_deletion_jobs").select(projection).eq("user_id",user.id).execute().data==jobs
    audit=service.table("account_deletion_audit").select("stage").eq("job_id",jobs[0]["id"]).execute().data
    assert {row["stage"] for row in audit}=={"requested","data_deleted","completed"}


def test_support_internal_tables_are_browser_denied_and_service_readable(environment):
    _, service, actors = environment
    for table in ("support_requests", "support_messages", "support_internal_notes", "support_audit_logs",
                  "company_business_consents", "billing_checkout_consents"):
        assert isinstance(service.table(table).select("*").limit(1).execute().data, list)
        for browser, _, _ in actors:
            with pytest.raises(APIError) as error:
                browser.table(table).select("*").limit(1).execute()
            assert error.value.code == "42501"


def test_split_payment_idempotency_and_cross_company_rejection(environment):
    api,service,actors=environment
    _,headers,own=actors[0];_,other_headers,other=actors[1]
    body={"operation_id":str(uuid4()),"amount":123,"paid_at":"2026-09-15T00:00:00+09:00"}
    path=f"/financials/{own['id']}/payments"
    first=api.post(path,headers=headers,json=body)
    assert first.status_code==200
    assert api.post(path,headers=headers,json=body).status_code==200
    assert api.post(path,headers=headers,json={**body,"amount":124}).status_code==409
    assert api.post(path,headers=other_headers,json={**body,"operation_id":str(uuid4())}).status_code==404
    rows=service.table("financial_payments").select("id,amount").eq("id",body["operation_id"]).execute().data
    assert rows==[{"id":body["operation_id"],"amount":123}]
    cancel=f"/financials/payments/{body['operation_id']}/void"
    assert api.post(cancel,headers=other_headers,json={"reason":"forbidden"}).status_code==404
    for _ in range(2):assert api.post(cancel,headers=headers,json={"reason":"fixture correction"}).status_code==200
    saved=api.get(f"/financials/{own['id']}",headers=headers).json()["payments"]
    assert next(p for p in saved if p["id"]==body["operation_id"])["voided_at"] is not None


def test_provider_recovery_requires_review_and_preserves_budget(environment):
    _,service,actors=environment
    company=actors[0][2]["company_id"]
    budget={"p_company_id":company,"p_model":"recovery-fixture","p_tokens":1,
            "p_cost_micro_usd":1,"p_token_limit":1,"p_cost_limit_micro_usd":1}
    rid=service.rpc("reserve_ai_budget",budget).execute().data
    assert rid is not None
    args={"p_company_id":company,"p_expected_id":rid,"p_kind":"ai",
          "p_operator_ref":"fixture-operator","p_ticket_ref":"fixture-ticket",
          "p_workers_stopped":True,"p_provider_reviewed":True}
    for browser,_,_ in actors:
        with pytest.raises(APIError) as error:
            browser.rpc("resolve_provider_uncertainty",args).execute()
        assert error.value.code=="42501"
    for field in ("p_workers_stopped","p_provider_reviewed"):
        with pytest.raises(APIError) as error:
            service.rpc("resolve_provider_uncertainty",{**args,field:False}).execute()
        assert error.value.code=="P0001"
    def saved():
        return service.table("ai_budget_reservations").select("status,reserved_tokens,reserved_cost_micro_usd").eq("id",rid).single().execute().data
    assert saved()["status"]=="reserved"
    assert service.rpc("resolve_provider_uncertainty",{**args,"p_company_id":actors[1][2]["company_id"]}).execute().data is False
    assert saved()["status"]=="reserved"
    assert service.rpc("resolve_provider_uncertainty",args).execute().data is True
    assert service.rpc("resolve_provider_uncertainty",args).execute().data is False
    assert saved()=={"status":"reviewed_unknown","reserved_tokens":1,"reserved_cost_micro_usd":1}
    assert service.rpc("reserve_ai_budget",budget).execute().data is None
    assert len(service.table("operation_recovery_audit").select("id").eq("company_id",company).eq("owner_id",rid).execute().data)==1


def test_gmail_revoke_recovery_cannot_delete_reconnected_account(environment):
    _,service,actors=environment
    company=actors[1][2]["company_id"]
    connection=service.table("gmail_connections").insert({"company_id":company,"email":"reconnect@example.invalid","token_json":{},"status":"revocation_pending"}).execute().data[0]
    rid=connection["id"];owner=str(uuid4())
    args={"p_company_id":company,"p_expected_id":rid,"p_kind":"gmail-revoke",
          "p_operator_ref":"fixture-operator","p_ticket_ref":"fixture-ticket",
          "p_workers_stopped":True,"p_provider_reviewed":True}
    assert service.rpc("claim_gmail_work",{"p_company_id":company,"p_owner_id":owner,"p_purpose":"oauth"}).execute().data is True
    # Active OAuth work fences recovery even if the operator accidentally attests.
    with pytest.raises(APIError) as error:service.rpc("resolve_provider_uncertainty",args).execute()
    assert error.value.code=="P0001"
    service.table("gmail_connections").update({"status":"connected"}).eq("id",rid).eq("company_id",company).execute()
    assert service.rpc("recover_company_work",{"p_company_id":company,"p_expected_owner":owner,"p_operator_ref":"fixture-operator","p_ticket_ref":"fixture-ticket","p_workers_stopped":True}).execute().data is True
    # Same row ID after reconnect must also be protected by its changed status.
    with pytest.raises(APIError) as error:service.rpc("resolve_provider_uncertainty",args).execute()
    assert error.value.code=="P0001"
    assert service.table("gmail_connections").select("id,status").eq("company_id",company).execute().data==[{"id":rid,"status":"connected"}]
    for browser,_,_ in actors:
        with pytest.raises(APIError) as error:browser.rpc("resolve_provider_uncertainty",args).execute()
        assert error.value.code=="42501"
    service.table("gmail_connections").update({"status":"revocation_pending"}).eq("id",rid).execute()
    assert service.rpc("resolve_provider_uncertainty",args).execute().data is True
    assert service.rpc("resolve_provider_uncertainty",args).execute().data is False
    assert service.table("gmail_connections").select("id").eq("id",rid).execute().data==[]
    assert len(service.table("operation_recovery_audit").select("id").eq("owner_id",rid).execute().data)==1


def test_billing_mode_promotion_rejects_test_history_and_browser(environment):
    _,service,actors=environment
    args={"p_approval_ref":"fixture-approval","p_workers_stopped":True}
    for browser,_,_ in actors:
        with pytest.raises(APIError) as error:browser.table("billing_runtime_config").select("*").execute()
        assert error.value.code=="42501"
        with pytest.raises(APIError) as error:browser.rpc("promote_billing_live",args).execute()
        assert error.value.code=="42501"
    company=actors[0][2]["company_id"]
    # No Stripe service is called: this is a synthetic unknown checkout fixture.
    service.table("billing_checkout_attempts").upsert({"company_id":company,"attempt_id":str(uuid4()),"session_id":None},on_conflict="company_id").execute()
    with pytest.raises(APIError) as error:service.rpc("promote_billing_live",args).execute()
    assert error.value.code=="P0001"
    assert service.table("billing_runtime_config").select("mode").eq("singleton",True).single().execute().data=={"mode":"test"}


def test_cursor_null_empty_contract_with_current_sync_store(environment):
    from app.services.gmail_sync import SyncStore
    _, service, actors = environment
    company = actors[1][2]["company_id"]
    connection = service.table("gmail_connections").insert({"company_id": company,
        "email": "cursor-contract@example.invalid", "token_json": {}, "status": "connected"}).execute().data[0]
    owner = str(uuid4())
    assert service.rpc("claim_gmail_work", {"p_company_id": company, "p_owner_id": owner, "p_purpose": "sync"}).execute().data is True
    try:
        store = SyncStore(service, company, connection)
        previous = store.load()
        state = {"mode": "delta", "history_id": "100", "initial_since": 1,
                 "page_token": None, "pending_ids": None, "pending_page": None, "caught_up": True}
        service.rpc("commit_gmail_inbound_page", {"p_company_id": company, "p_owner_id": owner,
            "p_connection_id": connection["id"], "p_mailbox": connection["email"],
            "p_expected_version": previous["version"], "p_state": state, "p_records": []}).execute()
        null_row = store.load()
        assert null_row["pending_ids"] is None and null_row["pending_page"] is None
        assert null_row["version"] == previous["version"] + 1
        store.commit(null_row, state, [])
        empty_row = store.load()
        assert empty_row["pending_ids"] == [] and empty_row["pending_page"] is None
        assert empty_row["version"] == null_row["version"] + 1
        assert service.table("gmail_inbound_receipts").select("gmail_message_id").eq("company_id",company).execute().data == []
    finally:
        service.rpc("release_gmail_work", {"p_company_id": company, "p_owner_id": owner}).execute()


def test_service_role_reservations_and_deletion_status_require_rpc(environment):
    _, service, actors = environment
    company = actors[1][2]["company_id"]
    for table in ("ai_budget_reservations", "account_deletion_jobs", "financial_records", "financial_payments"):
        before = service.table(table).select("*").eq("company_id",company).execute().data
        with pytest.raises(APIError) as error:
            service.table(table).insert({"company_id": company}).execute()
        assert error.value.code == "42501"
        with pytest.raises(APIError) as error:
            service.table(table).update({"company_id": company}).eq("company_id",company).execute()
        assert error.value.code == "42501"
        assert service.table(table).select("*").eq("company_id",company).execute().data == before
