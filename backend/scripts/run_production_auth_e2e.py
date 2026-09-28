"""Production Auth/tenant E2E. Requires a separate owner approval to execute.

Never import or invoke test_p0_supabase_isolation.py against production. This
runner has no Gmail, Stripe, scheduler, or deploy calls. It creates two temporary
Auth users and tenant fixtures, verifies real JWT-backed reads and isolation,
then deletes only IDs it created. Unexpected failure stops checks and enters
best-effort fixture cleanup; cleanup failure is reported as BLOCKED.
"""

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import secrets
import sys
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from postgrest.exceptions import APIError
from supabase import create_client
from supabase_auth.errors import AuthApiError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


PROJECT_REF = "zszmetqhksthduoxfvac"
URL = f"https://{PROJECT_REF}.supabase.co"
CONFIRMATION = "I_HAVE_SEPARATE_OWNER_APPROVAL_FOR_PRODUCTION_E2E"
COUNT_TABLES = ("companies", "profiles", "customers", "profit_events")
RELEASE_STATUS = Path(__file__).resolve().parents[2] / "docs" / "RELEASE_STATUS.md"


class GateError(RuntimeError):
    pass


def validate_gate(project_ref, confirmation, configured_url):
    if project_ref != PROJECT_REF or confirmation != CONFIRMATION or configured_url != URL:
        raise GateError("Production E2E gate not satisfied")


def require(condition, label):
    if not condition:
        raise GateError(label)


def require_permission_denied(operation, label):
    try:
        operation()
    except APIError as exc:
        require(exc.code == "42501", "Unexpected browser authorization error")
    else:
        raise GateError(label)


def exact_count(service, table):
    result = service.table(table).select("id", count="exact", head=True).execute()
    require(isinstance(result.count, int), "Count unavailable")
    return result.count


def counts(service):
    return {table: exact_count(service, table) for table in COUNT_TABLES}


def no_op_delete_preflight(service):
    # A nonexistent, freshly generated UUID is checked first. This validates
    # cleanup privileges without deleting any row in any customer tenant.
    for table in ("profit_events", "customers", "profiles", "companies"):
        probe = str(uuid4())
        require(not service.table(table).select("id").eq("id", probe).execute().data,
                "Cleanup probe collision")
        service.table(table).delete().eq("id", probe).execute()


def api_client(service, anon, monkeypatch):
    from app.core import auth, company_context
    from app.routers import customers
    from app.api import leads

    # Authenticate every request through production GoTrue /auth/v1/user with
    # the user's real JWT. Disabling the local HMAC path is not an auth bypass.
    monkeypatch.setattr(auth, "SUPABASE_URL", URL)
    monkeypatch.setattr(auth, "SUPABASE_JWT_SECRET", "")
    monkeypatch.setenv("SUPABASE_ANON_KEY", anon)
    monkeypatch.setattr(company_context, "get_supabase_client", lambda: service)
    monkeypatch.setattr(customers, "get_supabase_client", lambda: service)
    monkeypatch.setattr(leads, "get_supabase_client", lambda: service)
    app = FastAPI()
    app.include_router(customers.router)
    app.include_router(leads.router)
    return TestClient(app)


def one_row(service, table, row_id, fields, expected):
    rows = service.table(table).select(fields).eq("id", row_id).execute().data or []
    require(len(rows) == 1 and all(rows[0].get(k) == v for k, v in expected.items()),
            "Fixture identity changed; cleanup stopped")


def cleanup(service, actors, *, owner_filter=True):
    # No broad company_id-only DELETE and no cascade-as-proof. Verify every
    # identity before each exact-ID delete. Do not touch unrelated production rows.
    for actor in reversed(actors):
        actor["cleanup_stage"] = "identity-recovery"
        if not actor.get("user_id"):
            raise GateError("Auth creation outcome unknown; manual fixture review required")
        if not actor.get("company_id"):
            # A successful RPC response may have been lost. The newly created
            # Auth UUID plus the run marker are both required for recovery.
            profiles = service.table("profiles").select("id,company_id").eq("user_id", actor["user_id"]).execute().data or []
            require(len(profiles) <= 1, "Ambiguous test profile; cleanup stopped")
            if profiles:
                actor["company_id"] = profiles[0]["company_id"]
                actor["profile_id"] = profiles[0]["id"]
                one_row(service, "companies", actor["company_id"], "id,name,owner_user_id",
                        {"name": actor["marker"], "owner_user_id": actor["user_id"]})
        if actor.get("company_id"):
            for table, field, key in (("customers", "name", "customer_id"),
                                      ("profit_events", "title", "event_id")):
                rows = service.table(table).select("id").eq("company_id", actor["company_id"]).eq(field, actor["marker"]).execute().data or []
                require(len(rows) <= 1, "Ambiguous fixture row; cleanup stopped")
                if rows:
                    require(key not in actor or actor[key] == rows[0]["id"],
                            "Fixture ID changed; cleanup stopped")
                    actor[key] = rows[0]["id"]
        for table, field, row_id in (
            ("profit_events", "title", actor.get("event_id")),
            ("customers", "name", actor.get("customer_id")),
        ):
            if row_id:
                actor["cleanup_stage"] = "delete-" + table
                one_row(service, table, row_id, f"id,company_id,{field}",
                        {"company_id": actor["company_id"], field: actor["marker"]})
                service.table(table).delete().eq("id", row_id).eq("company_id", actor["company_id"]).execute()
                require(not service.table(table).select("id").eq("id", row_id).execute().data,
                        "Fixture row cleanup incomplete")
        if actor.get("profile_id"):
            actor["cleanup_stage"] = "delete-profile"
            one_row(service, "profiles", actor["profile_id"], "id,user_id,company_id",
                    {"user_id": actor["user_id"], "company_id": actor["company_id"]})
            service.table("profiles").delete().eq("id", actor["profile_id"]).eq("user_id", actor["user_id"]).execute()
            require(not service.table("profiles").select("id").eq("id", actor["profile_id"]).execute().data,
                    "Profile cleanup incomplete")
        if actor.get("company_id"):
            actor["cleanup_stage"] = "delete-company"
            one_row(service, "companies", actor["company_id"], "id,name,owner_user_id",
                    {"name": actor["marker"], "owner_user_id": actor["user_id"]})
            deletion = service.table("companies").delete().eq("id", actor["company_id"])
            if owner_filter:
                deletion = deletion.eq("owner_user_id", actor["user_id"])
            deletion.execute()
            require(not service.table("companies").select("id").eq("id", actor["company_id"]).execute().data,
                    "Company cleanup incomplete")
        actor["cleanup_stage"] = "delete-auth"
        service.auth.admin.delete_user(actor["user_id"])
        try:
            service.auth.admin.get_user_by_id(actor["user_id"])
        except AuthApiError as error:
            require(error.status == 404 and error.code == "user_not_found",
                    "Auth deletion verification failed")
        else:
            raise GateError("Auth user still exists after deletion")
        actor["auth_deleted"] = True


def register_actor(service, anon, run_marker, index, actors):
    marker = f"PR-PROD-E2E-{run_marker}-{index}"
    email = f"pr-e2e-{run_marker}-{index}@example.invalid"
    password = secrets.token_urlsafe(40)
    actor = {"marker": marker, "auth_outcome_unknown": True}
    actors.append(actor)
    actor["stage"] = "auth-create"
    created = service.auth.admin.create_user(
        {"email": email, "password": password, "email_confirm": True}
    ).user
    require(created is not None and created.id is not None, "Auth user creation failed")
    actor["user_id"] = str(created.id)
    actor["auth_outcome_unknown"] = False
    actor["stage"] = "auth-login"
    browser = create_client(URL, anon)
    session = browser.auth.sign_in_with_password({"email": email, "password": password}).session
    require(session is not None and session.access_token, "Real Auth login failed")
    browser.postgrest.auth(session.access_token)
    actor["stage"] = "canonical-rpc"
    company = browser.rpc("create_company_and_profile", {"company_name": marker,
                                                          "owner_name": marker}).execute().data
    require(company is not None, "Canonical registration failed")
    actor["company_id"] = str(company)
    actor["stage"] = "profile-linkage"
    profiles = service.table("profiles").select("id,user_id,company_id,role").eq("user_id", actor["user_id"]).execute().data or []
    require(len(profiles) == 1 and profiles[0]["company_id"] == actor["company_id"]
            and profiles[0]["role"] == "owner", "Profile/company linkage invalid")
    actor["profile_id"] = profiles[0]["id"]
    actor["browser"] = browser
    actor["headers"] = {"Authorization": "Bearer " + session.access_token}
    return actor


def verify(service, anon, monkeypatch, actors, *, require_company_owner=True):
    api = api_client(service, anon, monkeypatch)
    require(actors[0]["company_id"] != actors[1]["company_id"], "Companies were not isolated")
    for actor in actors:
        customer = service.table("customers").insert({"company_id": actor["company_id"],
            "name": actor["marker"]}).execute().data
        require(len(customer or []) == 1, "Service-role customer write failed")
        actor["customer_id"] = customer[0]["id"]
        event = service.table("profit_events").insert({"company_id": actor["company_id"],
            "customer_id": actor["customer_id"], "title": actor["marker"], "status": "open"}).execute().data
        require(len(event or []) == 1, "Service-role event write failed")
        actor["event_id"] = event[0]["id"]

    for actor in actors:
        other = actors[1] if actor is actors[0] else actors[0]
        browser = actor["browser"]
        own = browser.table("profiles").select("id,company_id").eq("id", actor["profile_id"]).execute().data or []
        foreign = browser.table("profiles").select("id").eq("id", other["profile_id"]).execute().data or []
        require(len(own) == 1 and own[0]["company_id"] == actor["company_id"] and not foreign,
                "Authenticated profile isolation failed")
        for table in ("customers", "profit_events", "gmail_connections"):
            require_permission_denied(
                lambda table=table: browser.table(table).select("id").limit(1).execute(),
                "Browser business-table access unexpectedly allowed")
        # Do not infer isolation from an empty result. Exercise real foreign IDs,
        # require the expected permission failure, then prove the rows unchanged
        # through the service role.
        require_permission_denied(
            lambda: browser.table("customers").update({"name": actor["marker"]})
                .eq("id", other["customer_id"]).execute(),
            "Cross-tenant browser update unexpectedly allowed")
        require_permission_denied(
            lambda: browser.table("profit_events").delete()
                .eq("id", other["event_id"]).execute(),
            "Cross-tenant browser delete unexpectedly allowed")
        one_row(service, "customers", other["customer_id"], "id,company_id,name",
                {"company_id": other["company_id"], "name": other["marker"]})
        one_row(service, "profit_events", other["event_id"], "id,company_id,title",
                {"company_id": other["company_id"], "title": other["marker"]})
        require_permission_denied(
            lambda: browser.rpc("onboard_user", {
                "p_user_id": actor["user_id"], "p_company_name": actor["marker"],
                "p_name": actor["marker"], "p_email": "blocked@example.invalid",
            }).execute(),
            "Legacy service-only onboarding RPC unexpectedly allowed")
        require_permission_denied(
            lambda: browser.rpc("request_account_deletion", {
                "p_user_id": actor["user_id"], "p_retention_days": 1,
            }).execute(),
            "Service-only deletion RPC unexpectedly allowed")
        customer_list = api.get("/customers", headers=actor["headers"])
        lead_list = api.get("/leads", headers=actor["headers"])
        require(customer_list.status_code == 200 and lead_list.status_code == 200,
                "Authenticated normal read failed")
        own_customers = {x["id"] for x in customer_list.json()["items"]}
        own_events = {x["id"] for x in lead_list.json()["items"]}
        require(actor["customer_id"] in own_customers and other["customer_id"] not in own_customers
                and actor["event_id"] in own_events and other["event_id"] not in own_events,
                "Authenticated list isolation failed")
        require(api.get(f"/customers/{actor['customer_id']}", headers=actor["headers"]).status_code == 200
                and api.get(f"/leads/{actor['event_id']}", headers=actor["headers"]).status_code == 200,
                "Authenticated own detail failed")
        require(api.get(f"/customers/{other['customer_id']}", headers=actor["headers"]).status_code == 404
                and api.get(f"/leads/{other['event_id']}", headers=actor["headers"]).status_code == 404,
                "Cross-tenant detail access not denied")
        if require_company_owner:
            ownership = service.table("companies").select("id,owner_user_id").eq(
                "id", actor["company_id"]).execute().data or []
            require(len(ownership) == 1 and ownership[0]["owner_user_id"] == actor["user_id"],
                    "Canonical onboarding company ownership invalid")
    require(api.get("/customers").status_code == 401 and
            api.get("/customers", headers={"Authorization": "Bearer invalid"}).status_code == 401,
            "Missing/invalid JWT not denied")


def append_status(outcome, cleanup_ok, delta):
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    safe_delta = ", ".join(f"{table}={delta.get(table, 'unknown')}" for table in COUNT_TABLES)
    with RELEASE_STATUS.open("a", encoding="utf-8") as target:
        target.write(f"\n- Production Auth E2E {stamp}: {outcome}; "
                     f"cleanup={'PASS' if cleanup_ok else 'BLOCKED'}; "
                     f"pre/post count delta: {safe_delta}. "
                     "Dedicated A/B users only; no Gmail, Stripe, Cron, or Deploy.\n")


def exercise(service, anon_key, monkeypatch, *, record=True):
    actors = []
    outcome = "BLOCKED"
    cleanup_ok = False
    before = after = None
    stage = "baseline-counts"
    failure_stage = "none"
    failure_type = "none"
    failure_local_reason = ""
    cleanup_stage = "none"
    cleanup_type = "none"
    try:
        before = counts(service)
        stage = "cleanup-privilege-preflight"
        no_op_delete_preflight(service)
        run_marker = uuid4().hex
        for index in ("A", "B"):
            stage = "register-" + index
            register_actor(service, anon_key, run_marker, index, actors)
        stage = "jwt-isolation-and-read"
        verify(service, anon_key, monkeypatch, actors)
        outcome = "PASS"
    except Exception as error:
        outcome = "BLOCKED"
        failure_stage = stage + ("/" + actors[-1].get("stage", "") if stage.startswith("register-") and actors else "")
        failure_type = type(error).__name__
        if not record and isinstance(error, AssertionError):
            failure_local_reason = str(error)[:160]
    finally:
        try:
            cleanup(service, actors)
            cleanup_ok = all(actor.get("auth_deleted") and not actor.get("auth_outcome_unknown") for actor in actors)
            after = counts(service) if before is not None else None
            if before is None or after != before:
                cleanup_ok = False
        except Exception as error:
            cleanup_ok = False
            cleanup_type = type(error).__name__
            cleanup_stage = next((a.get("cleanup_stage", "none") for a in reversed(actors)
                                  if a.get("cleanup_stage") and not a.get("auth_deleted")), "none")
        delta = {table: after[table] - before[table] for table in COUNT_TABLES} if before and after else {}
        if record:
            append_status(outcome, cleanup_ok, delta)
    if outcome != "PASS" or not cleanup_ok:
        label = "Production Auth E2E or cleanup blocked; stop for operator review"
        if not record:
            label += f" (local stage={failure_stage}, error_type={failure_type}, cleanup={cleanup_ok}, cleanup_stage={cleanup_stage}, cleanup_type={cleanup_type}, reason={failure_local_reason})"
        raise GateError(label)
    return {"result": "PASS", "cleanup": "PASS", "count_delta": delta}


def run(project_ref, confirmation, service_key, anon_key, monkeypatch):
    validate_gate(project_ref, confirmation, os.getenv("SUPABASE_URL", ""))
    require(bool(service_key and anon_key), "Production E2E credentials not configured")
    service = create_client(URL, service_key)
    return exercise(service, anon_key, monkeypatch)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-ref", required=True)
    parser.add_argument("--confirm-production-e2e", required=True)
    args = parser.parse_args()
    # No credential is read and no remote client is constructed before gate.
    validate_gate(args.project_ref, args.confirm_production_e2e, os.getenv("SUPABASE_URL", ""))
    from pytest import MonkeyPatch
    import json
    with MonkeyPatch.context() as patch:
        result = run(args.project_ref, args.confirm_production_e2e,
                     os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
                     os.getenv("SUPABASE_ANON_KEY", ""), patch)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never print provider exception bodies, test identities, JWTs or keys.
        print("Production Auth E2E blocked; see safe release status entry.", file=sys.stderr)
        raise SystemExit(1) from None
