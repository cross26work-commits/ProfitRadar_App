# Production deployment runbook

This is a gated procedure, not deployment approval. Current deployment status is **NO**.

## 0. Immutable input

- Use a clean, reviewed commit and the external `git archive` artifact/manifest created by `scripts/build_release_artifact.py`.
- Record the final Supabase project ref, Railway project ID and provider approval ticket without secret values.
- Run `scripts/production/Invoke-ProductionPreflight.ps1`; only `READY` permits an owner approval request.

## 1. Owner gates

Confirm Railway billing/GitHub access, create the Tokyo Supabase Production project, enter secrets, complete legal approval, prepare Google verification and Stripe LIVE objects, configure off-host encrypted backup, alert receiver and DNS targets. Do not copy TEST credentials.

## 2. Database gate (writers stopped)

1. Confirm exact target identity and a restorable encrypted backup with a restore drill.
2. For the selected new Tokyo project, use only the hash-pinned stream in `deploy/fresh-production/migration-stream.json`. Stage it with `Stage-FreshProductionMigrations.ps1`; never run the root migration directory or replay the remote-only v1/v2 supplements.
3. Owner approves the exact migration set/hash. Apply in a transaction where supported; stop on any error.
4. Verify schema, RLS/policies/ACL/RPC/indexes, billing mode, row counts and `/ready` prerequisites.
5. Run the separately approved Production Auth A/B runner only against its pinned target. Never run `test_p0_supabase_isolation.py` against Production.

## 3. Railway services

Create services without automatic deploy. Apply `deploy/railway/service-plan.json`, set variables from the matrix, then deploy the reviewed artifact/commit in order: backend, frontend, worker. Backend must pass `/health` and `/ready` before frontend; worker is last. Do not attach a public worker domain.

## 4. Domains

After Railway generates exact validation/routing values, enter only those values at お名前.com:

| Purpose | Type | Host | Value | TTL |
|---|---|---|---|---|
| apex verification | TXT | `@` | `<RAILWAY_FRONTEND_VERIFICATION>` | provider default |
| apex route | ALIAS/ANAME or flattened CNAME supported by DNS UI | `@` | `<RAILWAY_FRONTEND_TARGET>` | provider default |
| API verification | TXT | `<RAILWAY_API_VERIFICATION_HOST>` | `<RAILWAY_API_VERIFICATION>` | provider default |
| API route | CNAME | `api` | `<RAILWAY_BACKEND_TARGET>` | provider default |
| optional www | CNAME | `www` | `<RAILWAY_FRONTEND_TARGET>` | provider default |

Do not invent A records: Railway does not provide a stable application IP. Confirm certificate issuance and redirect policy before publishing.

## 5. Provider gates

- Google: homepage/privacy/terms/support live, domain verified, callback exact, only `gmail.readonly` and `gmail.send`, verification/security assessment complete before external users.
- Stripe: create reviewed LIVE ¥19,800/month inclusive-tax price and webhook; run read-only LIVE configuration validation first. Database `billing_mode` promotion is separately approved and one-way. No charge in readiness checks.

## 6. Smoke and release

After deploy approval, run `Invoke-ProductionSmokeTest.ps1` with its exact approval phrase. Then execute the manual scenarios in `PRODUCTION_SMOKE_TEST.md`. Any auth, tenant, billing, Gmail recipient, readiness or secret-leak issue is a stop/rollback condition.

## Migration audit note

The repository contains historical repair/remote-forward migrations. Static safety validation rejects `DROP TABLE`, `TRUNCATE` and row `DELETE`; it is not proof that an arbitrary remote baseline matches. The disposable migration/integration suite is mandatory. Automatic deploy-time migration and blind `supabase db push` remain prohibited.

Fresh migration repair proof is PASS in three independent zero-state projects; see `PRODUCTION_SUPABASE_MIGRATION_DECISION.md` and `docs/evidence/FRESH_PRODUCTION_MIGRATION_20261002.md`. The remaining database gate is owner creation of the new Tokyo project followed by separately approved staging/apply/post-apply verification. Static SQL PASS alone is never apply authorization.
