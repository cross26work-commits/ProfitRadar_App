# Profit Radar production deployment readiness audit

Audited: 2026-09-28T16:26:59+09:00
Repository: `C:\Users\closs\ProfitRadar_App`
Branch: `arc/profit-radar-release-readiness`
HEAD: `435bb0ac368c32e50dda918863213b3cdbf69543`
Verdict: **BLOCKED / NOT READY**
Production deployment, Production database writes, Gmail sends and Stripe LIVE calls in this audit: **0**

## Scope and evidence rules

This audit uses the current dirty working tree, not HEAD alone. Existing changes were preserved. Local disposable Supabase, Stripe TEST and isolated OpenAI evidence are distinguished from Production facts. A code path, a mock and a successful build are not treated as proof that Production is configured or running.

The owner-reported Production v2 COMMIT, post-apply `FINAL=PASS`, unchanged 20-table counts and backup restore proof remain recorded. The current repository contains conflicting historical statements about whether the separately gated Production Authenticated A/B runner was ever executed, and no attached safe output resolves that conflict. Therefore current Production Auth/RLS tenant behaviour is **UNVERIFIED** in this audit even though local real-Auth isolation passes.

## Release baseline

| Item | Result | Evidence |
|---|---|---|
| Branch / HEAD | PASS | Values above |
| Working tree | BLOCKED for release | Extensive tracked and untracked release changes are not in a reviewable release commit; no commit/push was performed |
| Disposable Supabase | PASS for local testing | Fixed `profit-radar-disposable`; DB/Auth/Kong healthy on loopback. Vector logging container was restarting and is not counted as Production monitoring |
| Isolated integration | PASS | 32 passed, 0 skipped |
| Backend | PASS | 290 passed, 0 skipped; 12 Supabase SDK deprecation warnings |
| Python compile / dependencies | PASS | compileall; pip check; pip-audit: no known vulnerabilities |
| Frontend | PASS | TypeScript, ESLint, 21-route production build; npm audit 0 |
| Stripe TEST E2E | PASS (isolated only) | `docs/evidence/STRIPE_TEST_E2E_20260928.md` |
| Real AI generation | PASS (isolated only) | `docs/evidence/AI_ISOLATED_REAL_GENERATION_20260928.md` |
| Diff whitespace | PASS | `git -c core.safecrlf=false diff --check` |
| Candidate-file secret patterns | PASS after repository hygiene fix | 404 tracked/non-ignored candidate files, 0 actual-looking Stripe/Google/private-key/JWT patterns. Old isolated/browser-save artifacts were excluded without deletion |

The frontend build used `https://api.example.invalid` only to exercise the production fail-closed build contract. It is not a deployable artifact and made no network request.

## Production environment configuration

No values are recorded. Presence checks of local ignored files do not prove a Production host secret store.

| Configuration | State | Reason / required proof |
|---|---|---|
| `APP_ENV=production` | OWNER_ACTION_REQUIRED | Local owner-gate configuration exists; deployed process does not |
| Public frontend URL / DNS / TLS | MISSING | No approved domain, certificate or hosting target is recorded |
| Backend origin / HTTPS / CORS | MISSING | Code fails closed in production, but no approved public API origin and exact CORS allowlist are provisioned |
| Supabase URL / anon / service role | OWNER_ACTION_REQUIRED | Backend separation and fail-closed code pass; inject server-side on the deployment and expose only the browser key to the frontend |
| Supabase JWT validation | READY in code | Backend verifies HS256 only when explicitly configured, otherwise calls Supabase Auth `/user`; missing/invalid JWT tests pass |
| OpenAI key / models / rates / company limits | OWNER_ACTION_REQUIRED | Production startup validates all fields; isolated real-provider proof passed, persistent Production values are not provisioned |
| Google client / redirect / OAuth state | OWNER_ACTION_REQUIRED | Code requires an HTTPS `/gmail/callback`; approved Production client/domain/consent status is not evidenced |
| Gmail token encryption / rotation | OWNER_ACTION_REQUIRED | Versioned tenant-bound MultiFernet and reconnect/migration paths exist; key custody and Production rotation procedure need an approved secret store |
| Stripe LIVE key / Price / webhook | OWNER_ACTION_REQUIRED | TEST E2E passed. LIVE objects, webhook destination/secret and approval reference do not exist in evidence and were not invoked |
| Billing database mode | OWNER_ACTION_REQUIRED | Database is intentionally `test`; one-way `promote_billing_live` requires stopped workers and an approval reference |
| Worker / scheduler secret / backend URL | MISSING | Code and systemd template exist; no deployed/enabled five-minute worker is proven |
| Retention days / sweep approval | OWNER_ACTION_REQUIRED | Delete path fails closed without the day count; owner/legal policy is not fixed |
| Logging sink | MISSING | Application redaction passes, but no deployed durable log sink/retention/access policy is proven |
| Monitoring receiver / independent heartbeat | MISSING | Counter/notification code exists; no receiver, on-call owner or missed-heartbeat monitor is configured |

## Database, authentication and tenant security

- Local Auth/DB proof: A and B both have real local Auth JWTs and existing rows; own access succeeds, cross-tenant list/detail/write/delete and direct browser table access are denied; unauthenticated/invalid JWT is denied; service-role APIs derive company from the verified user profile.
- Production database: owner-reported v2 post-apply metadata and counts are favorable, but this audit did not connect to Production. Current Production A/B runner evidence is inconsistent across handoff documents. Classification: **UNVERIFIED** until the pinned runner output and cleanup/count delta are attached or a separately approved rerun succeeds.
- Service role is backend-only and fails closed when missing. Browser code references only the public Supabase key. Internal tables and privileged RPCs are tested as browser-denied in the disposable environment.
- The forward migration pins function bodies/ACL/search paths and local SQL tests cover unknown drift and rollback. It must not be replayed; the owner reports it is already committed in Production.
- Signup/onboarding derives `p_user_id` from a verified JWT. Duplicate and concurrent registration safety is covered locally.
- One response-redaction defect in `/auth/me` and two browser console paths that logged raw SDK error objects were fixed in this audit; regression passed.

## Gmail readiness

**Code/local: PASS. Production sale: BLOCKED.**

- Requested scopes are exactly `gmail.send` and `gmail.readonly`; Calendar is absent. `gmail.readonly` is Restricted and `gmail.send` is Sensitive.
- Tokens use tenant-bound encrypted envelopes, no plaintext fallback, refresh compare-and-set, reconnect account checks, explicit revoke states and resumable recovery.
- Initial 30-day import, pagination, history cursor, invalid-cursor recovery, atomic page commit, receipts/idempotency, company lock, retry/backoff, run records and manual/scheduled entry points are covered by local tests including more than 1,200 messages.
- Production send derives the recipient from the authorized event/customer and rejects a supplied mismatch. `/gmail/send-test` is 404 outside development/test. UNKNOWN sends are not automatically resent.
- External blocker: Google says public apps requesting sensitive/restricted consumer scopes require verification unless an exception applies; storing/transmitting Restricted data server-side can require an annual approved security assessment. Production branding, domain ownership, consent-screen URLs, scope approval and any assessment are not evidenced. Testing-mode success is not public-sale approval.
- Operational blocker: the scheduler template has not been installed/enabled and there is no external heartbeat/alert receiver.

Official references checked 2026-09-28: Google OAuth restricted-scope readiness, Gmail scope catalogue, OAuth policies and verification requirements.

## Stripe readiness

**TEST: PASS. LIVE: OWNER ACTION REQUIRED.**

- Real TEST Checkout, payment, signed webhook, provider-state reconciliation, DB subscription, entitlement, paid route, duplicate delivery, period-end cancellation, deletion, declined card and failure paths passed in an isolated database.
- Code validates JPY 19,800/month, interval 1 and tax-inclusive Price, verifies signed webhook timestamps/HMAC, fetches current provider state to defeat stale events, links only the persisted user-requested Checkout, and uses provider/idempotency keys and a DB event ledger.
- Production startup and requests fail closed on mode/key/DB mismatch. The DB promotion is service-only and one-way.
- LIVE Product/Price, key, webhook endpoint/events, tax/business registration decision, invoice/receipt email configuration, refund policy/process and approval reference are not configured or evidenced. No LIVE request occurred.
- The current code intentionally ignores non-subscription webhook event types. The owner must configure at least `customer.subscription.created`, `.updated`, and `.deleted`; renewal payment-failure behaviour must be confirmed against the final Stripe retry/dunning settings before launch. Refunds may be an operator Dashboard procedure for three customers only if the legal/support runbook states the owner, SLA and entitlement reconciliation steps.

## AI safety

**PASS in code and isolated real-provider execution; Production configuration pending.**

- Per-company token/cost/generation hard limits are reserved atomically before calls. Unknown provider outcomes retain budget, automatic retries are disabled, input/output/time limits are bounded, and cost/usage are recorded.
- Provider error, timeout, malformed output and missing configuration fail safely; logs do not contain prompt, provider exception or secret text.
- Prompt instructions explicitly treat mail as untrusted data. Structured financial fields still require user confirmation; unknown values are not promoted to confirmed financial results.
- Production model names, maximum rates and budgets must be owner-approved and provisioned. External-AI data handling and international transfer disclosures remain legal/privacy actions.

## Worker, monitoring and recovery

| Area | Result | Evidence / gap |
|---|---|---|
| Scheduled Gmail worker code | PASS | Dedicated secret, HTTPS/loopback URL guard, company isolation, lock and backoff |
| Production worker process | FAIL | Only a systemd template; not installed, enabled or restart-tested on a selected host |
| Maintenance counters | PASS in code | UNKNOWN sends, deletion, AI reservation, locks and sync failures/stalls |
| Alert delivery | FAIL | No approved HTTPS receiver test, on-call owner or independent missed-heartbeat alert |
| Backend readiness | PASS in code | `/health` and DB/table-aware `/ready` |
| Frontend availability monitoring | FAIL | No public deployment or external probe |
| Backup | PARTIAL | Owner reports one logical backup restore proof; Free-plan Production has no scheduled project backup and no recurring offsite backup/restore schedule is proven |
| Recovery runbook | PARTIAL | Migration/Gmail/send/deletion/restore procedures exist; deploy rollback, deployed version identity and alert escalation cannot be exercised before a hosting target is chosen |

## Legal and customer-facing readiness

**OWNER ACTION REQUIRED / not sale-ready.**

- Pricing and tax-inclusive display, 14-day trial with no automatic conversion, human-confirmed sending, cancellation UI and non-guaranteed AI outcomes are present.
- The landing page deliberately remains “preparing for paid release”. Seller and support values are absent from the current build configuration.
- Terms and Privacy explicitly contain “finalize before release” clauses. They do not yet contain final operator identity/contact, fixed retention/backup deletion periods, actual processors/international transfers, refund rules or final jurisdiction.
- There is no dedicated Specified Commercial Transactions Act disclosure page. Applicability/content must be decided by the owner and legal reviewer; the audit does not give legal advice.
- No public domain, public support channel or incident/contact SLA is evidenced. Marketing does not contain invented testimonials or guaranteed outcomes.

## Onboarding and offboarding

- Registration, login, canonical company/profile creation, trial, Gmail UI, initial sync, leads, drafts, send confirmation, results, paid signup and cancellation paths exist and pass local/isolated tests.
- A new external customer still cannot complete the path because there is no Production deployment, approved Google public OAuth configuration, LIVE billing or running scheduler. Production onboarding classification: **FAIL**.
- Account deletion is resumable/idempotent, reauthenticates, stops active billing deletion, revokes Gmail, purges tenant data, deletes Auth last and retains minimal audit data. Production classification: **FAIL** until retention/backup policy is fixed and one controlled Production offboarding rehearsal with non-customer fixtures confirms Google/Stripe/provider recovery.

## Blockers

### P0 — required before Production deployment/public signup

1. Select and provision the frontend/API host, public domains, DNS/TLS, exact CORS, secret store, immutable release commit/artifact and rollback target. The current dirty tree is not a deployable release.
2. Resolve Production Auth/RLS evidence conflict: attach the pinned A/B runner result with zero count delta/cleanup PASS, or separately approve one controlled run. Do not rerun v2.
3. Obtain the applicable Google brand/scope verification and security-assessment decision for `gmail.readonly`; configure the approved Production OAuth client/domain/URLs.
4. Create and approve Stripe LIVE Product/Price/webhook configuration, tax/invoice/refund decisions, then perform the documented stopped-writer DB live promotion and controlled LIVE smoke without charging a real customer.
5. Install/enable the five-minute worker and maintenance timer; configure a tested alert receiver, independent heartbeat and accountable responder.
6. Finalize and review Terms, Privacy, seller/contact information, retention/backup deletion, refund/cancellation terms and the required commercial disclosure before setting `SALES_PUBLICATION_APPROVED=true`.
7. Establish recurring Production backups despite the Free-plan limitation, protect/rotate backup credentials, and schedule a disposable restore drill with recovery objectives.

### P1 — required before the first paying customer

1. Run the deployed non-customer smoke: signup/login/company/trial, Gmail consent/import/sync, AI generation, draft/reload, controlled send/receive, financial result, LIVE Checkout/webhook/entitlement/cancel and account deletion.
2. Verify authenticated product UI at desktop and 390px on the real public origins, including disconnected/sync-failed/AI-limit/UNKNOWN/trial-expired/payment-failed states.
3. Assign the initial-three-company onboarding/support/on-call owner and daily review procedure for sync failures, UNKNOWN sends, billing failures and pending deletion.
4. Document the manual refund/invoice/support procedure if no automated customer portal is selected.

### P2 — may follow launch

- Replace deprecated Supabase SDK client timeout/verify configuration.
- Add broader automated browser coverage and a customer portal if operational load warrants it.
- Improve observability beyond the minimum receiver/heartbeat and resolve the local Vector logging container issue.

## Owner action checklist

| WHAT | WHY | WHERE | WHEN | Before deploy? | Before first customer? |
|---|---|---|---|---|---|
| Choose public frontend/API domains, host, TLS and secret store | No Production target exists | Hosting/DNS provider and deployment config | First | YES | YES |
| Create a reviewed release commit/artifact from the current tree | Dirty workspace is not reproducible | Git/release pipeline | Before build | YES | YES |
| Resolve Production Auth A/B evidence | Production tenant isolation cannot be inferred from local tests | Pinned `run_production_auth_e2e.py` evidence | Before public API | YES | YES |
| Complete Google verification/assessment decision | Restricted Gmail read data is processed server-side | Google Cloud OAuth Verification Center / approved assessor if required | Before external Gmail users | YES | YES |
| Finalize LIVE billing/tax/invoice/refund settings | TEST credentials and results cannot authorize LIVE sales | Stripe LIVE Dashboard and billing approval runbook | Before billing deployment | YES | YES |
| Configure/verify worker and monitoring | Manual-only sync and invisible failures are not production-ready | Production host/systemd or equivalent; monitoring service | Before public signup | YES | YES |
| Finalize legal identity/contact/terms/privacy/commercial disclosure | Current pages explicitly say unfinished | Public site plus legal review | Before publication approval | YES | YES |
| Choose retention and recurring backup policy | Deletion and recovery need fixed, disclosed periods | Secret/config store, backup target, Privacy/Runbook | Before public signup | YES | YES |
| Approve controlled deployment and smoke | Consequential external operations require human approval | Release runbook/change record | Last | YES | YES |

## Changes made by this audit

- Removed raw exception interpolation from `/auth/me` and raw SDK error objects from two browser console warnings.
- Added focused auth-response safety tests.
- Added ignore rules for explicitly non-release local Supabase/browser-save artifacts; no files were deleted.
- Added this evidence and updated release/owner-action handoff documents.

## Final verdict

Local code regression is green and the isolated AI/Stripe gates are strong. Profit Radar is **not ready for Production deployment or paid customer onboarding** because external production infrastructure, Google approval, LIVE billing, background operation/monitoring, legal publication data, reproducible release packaging and current Production tenant evidence are incomplete.

Next gate: **BLOCKED_BY_PRODUCTION_CONFIGURATION_AND_EXTERNAL_APPROVALS**.
