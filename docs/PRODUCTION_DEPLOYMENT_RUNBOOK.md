# Production deployment runbook

This is a gated procedure, not deployment approval. Current deployment status is **NO**.

2026-10-11 checkpoint: target Supabase `runxnxvwjqblyzdcegay` already has separately evidenced 23/23 fresh migrations. **Do not repeat section 2's initial migration steps** on this project. The single Railway STAGED frontend draft was discarded with owner approval; STAGED changes and applied services are both zero. IaC is still unapplied. See `PRODUCTION_RELEASE_GATE.md` for the active sequence.

## 0. Immutable input

- Use a clean, reviewed commit and the external `git archive` artifact/manifest created by `scripts/build_release_artifact.py`.
- Record the final Supabase project ref, Railway project ID and provider approval ticket without secret values.
- Run `scripts/production/Invoke-ProductionPreflight.ps1`; only `READY` permits an owner approval request.

## 1. Owner gates

Confirm Railway billing/GitHub access and the already-created Tokyo Supabase Production target, enter secrets, complete legal approval, prepare Google verification and Stripe LIVE objects, configure off-host encrypted backup, alert receiver and DNS targets. Do not copy TEST credentials.

## 2. Historical initial database gate (already completed for selected target)

1. Confirm exact target identity and a restorable encrypted backup with a restore drill.
2. For the selected new Tokyo project, use only the hash-pinned stream in `deploy/fresh-production/migration-stream.json`. Stage it with `Stage-FreshProductionMigrations.ps1`; never run the root migration directory or replay the remote-only v1/v2 supplements.
3. Owner approves the exact migration set/hash. Apply in a transaction where supported; stop on any error.
4. Verify schema, RLS/policies/ACL/RPC/indexes, billing mode, row counts and `/ready` prerequisites.
5. Run the separately approved Production Auth A/B runner only against its pinned target. Never run `test_p0_supabase_isolation.py` against Production.

## 3. Railway services

The STAGED frontend collision is resolved; `docs/RAILWAY_STAGED_RECONCILIATION.md` records the scoped discard. Current read-only IaC plan proposes 3 additions (frontend, backend, worker), zero changes and zero destroys, but still pins the old immutable SHA. Do not apply until the new release SHA is reviewed and pinned, variables are inventoried by **name only**, and the plan is re-run. IaC reports `variables: managed (default)`; before every future apply, reject any plan that would remove/replace a manually stored secret or other unexpected variable. Railway's `preserve()` can retain an existing value, but it must be reviewed against the actual post-creation variable inventory, not guessed now. After separate approval, create services without automatic deploy, set variables from the matrix, then deploy the reviewed **new** artifact/commit in order: backend, frontend, worker. Backend must pass `/health` and `/ready` before frontend; worker is last. Do not attach a public worker domain. Railway IaC cannot create custom domains; add them separately after exact provider values are known.

Pre-Apply variable safety gate (read-only; no secret values):

1. Confirm exact Railway project/environment, STAGED patch `{}`, applied-service list `[]`, reviewed GitHub branch and newly pinned immutable source SHA. In the initial zero-service state, there can be no existing service-secret variable to delete. Do not place secrets into IaC.
2. Run `railway config plan --file .railway/railway.ts --environment production --json` **without** `--decrypt-variables` or `--show-values`; inspect `variablePolicy.managed`, `currentGraph.resources` count, and `changeSet.changes` kinds/summaries. For the first Apply, require zero existing resources and exactly three safe `resource.create` changes named frontend, backend, worker; reject variable removal/replacement, any destroy or unexpected change. A human must review the ordinary redacted plan too. This is inspection, not Apply approval.
3. Only after a separate cost-capped owner approval may the initial IaC Apply be considered. Populate approved service-specific sealed variables afterwards, then stop IaC automation. For every **later** Apply, first obtain a variable-**name-only** inventory from Railway settings, reconcile each name with IaC `preserve()`/references, run a new read-only plan and reject any variable deletion/replacement or unknown change. If this protection cannot be proven, do not Apply. Never print/decrypt values or run the plan against another environment.

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

Fresh migration repair proof is PASS in three independent zero-state projects; see `PRODUCTION_SUPABASE_MIGRATION_DECISION.md` and `docs/evidence/FRESH_PRODUCTION_MIGRATION_20261002.md`. The selected Tokyo project already received and verified the 23/23 staged stream; see `docs/evidence/PRODUCTION_SUPABASE_INITIAL_APPLY_20261003.md`. **Do not replay it.** Remaining database work is controlled application E2E after separate approval, not initial schema apply. Static SQL PASS alone is never apply authorization.
