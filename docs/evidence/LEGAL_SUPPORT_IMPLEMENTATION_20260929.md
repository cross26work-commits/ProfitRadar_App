# Legal and support implementation evidence — 2026-09-29 JST

## Scope and isolation

- Branch `arc/profit-radar-release-readiness`; starting HEAD `31573c4da79b218022e7e4c40ac53fcba61bc5bc` plus the uncommitted changes listed by Git.
- Production deploy, Production Supabase access, Gmail send, Stripe charge, commit and push: **0**.
- Database execution used only the labeled disposable Supabase containers on loopback (`profit-radar-disposable`, API 54321 / DB 54322).

## Implemented

- COROS WORK / Profit Radar B2B disclosures; seven-day card-on-file trial; JPY 19,800 tax-inclusive monthly renewal; cancellation/refund and 30/90-day retention disclosures.
- Public contact form/API with fixed category vocabulary, server validation, origin/intent guard, honeypot, elapsed-time check, HMAC rate key, atomic database rate limit and non-sensitive request ID.
- Support admin API/UI with UUID allowlist authority independent of tenant roles, list/search/filter/detail, status/priority, notes, audit history and legal-disclosure classification.
- Reply reservation/finalization RPCs provide a fixed database recipient and persistent idempotency. Development/test delivery is suppressed. Production SMTP is fail-closed unless the sender/domain and provider settings are approved.
- Six internal tables have RLS enabled, no browser policies, explicit browser revokes and minimal service-role grants. Admin mutations and audit writes use service-only, fixed-search-path RPCs.
- Checkout records authenticated-user business/renewal/terms/privacy/refund confirmations before contacting Stripe. Stripe subscription trial is seven days and collects a payment method; trial-pending tenants do not receive write entitlement.

## Verification

- Migration applied successfully to disposable PostgreSQL in one transaction.
- Disposable real Auth/PostgREST integration: 33 passed / 0 skipped, including direct browser denial for all six new internal tables.
- Full Backend regression after final admin/email/startup tests and dependency remediation: **339 passed / 0 skipped**.
- Frontend: 8 tests / 0 skipped; TypeScript, ESLint and 27-route Production build PASS; npm audit 0.
- Python compileall, pip check and pip-audit PASS (0 known vulnerabilities). Current security pins include `oauthlib 4.0.0` and `PyJWT 2.14.0`.
- Clean minimal disposable database drill: migration first apply PASS; guarded rollback PASS; six new tables before rollback and zero afterward.
- Candidate secret scan: 460 files / 0 findings. Final local startup/migration evidence is in `LOCAL_STARTUP_REPAIR_20260930.md`.

## External owner gates

- Legal professional approval, actual seller legal name, governing court/effective date and final disclosure text.
- Production domain and `SUPPORT_EMAIL`; verified sender/domain plus production SMTP credentials.
- Supabase Auth UUID(s) for the dedicated support-admin allowlist.
- Production migration/deploy approval and a post-deploy authenticated smoke test.
