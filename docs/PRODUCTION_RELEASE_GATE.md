# Profit Radar production release gate

2026-10-11 update: the exact STAGED frontend draft was discarded under owner approval. Patch `{}`, 0 staged changes and 0 applied services. The STAGED collision stop condition below is historical; the current stop conditions are uncommitted release fixes, stale IaC SHA, production variables/managed-variable review, external provider/legal/monitoring/backup gates, and separate Apply/Deploy approval. See `docs/RAILWAY_RELEASE_CANDIDATE_20261011.md`.

2026-10-10 status: **BLOCKED — no deploy/public sale authorization.** The prior 23-migration Production Supabase evidence remains valid as a historical checkpoint; do **not** reapply migrations. Each gate below requires its own timestamped result and a human approval for external changes.

## G0: immutable candidate and infrastructure plan

- Review and commit/push today's source/dependency/IaC fixes only with separate approval; record the new SHA and build a new immutable artifact. Current frozen `9099d9a...` lacks today's fixes. `Invoke-ProductionPreflight.ps1` intentionally requires a clean worktree and exact artifact.
- Reconcile the STAGED frontend ID `81d8c4c5-9c45-46eb-9f1c-11afed625c61` with `.railway/railway.ts` using `docs/RAILWAY_STAGED_RECONCILIATION.md`. Existing staged branch is unspecified. The preferred design is to supersede only the unapplied patch **after explicit approval**, then re-inventory and re-plan. Verify **one frontend**, one backend, one private worker, expected repo/branch/new immutable SHA/root/build/start/health, zero destructive actions and no unreviewed duplicate. `railway config apply` is forbidden until separately approved.
- IaC cannot register custom domains; create them through Railway only after service approval. Record provider-issued DNS validation/routing targets, never invent IPs.
- Run current full local security gate: secret/current+history scans; Backend and disposable Auth/RLS integration; frontend test/tsc/lint/build; compile/pip check/pip-audit; npm full and production-only audit; migration hash check; diff check. Mark skipped tests separately. The current full npm audit has an unpatched dev-tooling `braces` advisory, so it requires explicit security risk disposition rather than a false PASS.

## G1: environment, legal and recovery

- Enter `docs/PRODUCTION_ENVIRONMENT_MATRIX.md` values into isolated Railway service settings, not Git. Validate with redacted `Test-ProductionEnvironment.ps1`; browser service has no server secret. Confirm `APP_ENV=production`, exact HTTPS origins/CORS, Production Supabase ref, Google callback, Stripe LIVE gate and no TEST key.
- Verify approved seller/support/legal content, B2B and 7-day card-required trial, independent counsel review and publication switches. Until then, the UI remains preparation-only.
- Configure a real alert receiver/on-call, validate one redacted signal plus dedupe, and prove encrypted off-host recurring backup plus disposable restore against the final target. Record RPO/RTO, key custody and retention. Prior one-time backup proof is not proof of recurring service.
- Run `Invoke-ProductionPreflight.ps1` with the new clean SHA/artifact and validated env files. Only `READY` may lead to a consequential approval request.

## G2: controlled production apply (separate explicit approvals)

1. Approve the exact Railway plan, subscription/resource cost ceiling, services and source SHA. Apply only after the STAGED patch is reconciled. Verify service count/IDs and that worker has no public domain; never auto-run DB migrations.
2. Approve provider setup separately: Google production OAuth/Restricted-scope verification and security assessment outcome; Stripe LIVE business/Price/webhook plus separately approved `promote_billing_live` DB RPC. No LIVE customer, Checkout or charge during configuration.
3. Approve Railway custom domains and then exact お名前.com DNS records. Verify HTTPS/TLS and CORS/callback. If any value is unknown, stop; do not guess.

## G3: smoke, recovery and opening

- Backend `/health` and `/ready`, frontend publication state, worker private `/health` and completed-batch `/ready`; monitoring alerts and restore proof. `/health` alone is not a DB or billing proof.
- Controlled dedicated production Auth A/B tenant test, normal read and denied cross-tenant service-role paths with exact-ID cleanup; no existing customer data. Requires its own approval.
- Controlled Gmail connection/sync/duplicate/revoke and Stripe signed webhook/entitlement/cancel/failure cases with dedicated test identities. Any actual Gmail send or LIVE paid transaction requires an additional explicit approval; none is implied here.
- Verify rollback artifacts and the current Railway deployment IDs. Application rollback is to an immutable deployment; the LIVE DB promotion is one-way and cannot be casually rolled back to TEST. DNS rollback uses recorded prior records. See `docs/PRODUCTION_ROLLBACK_PLAN.md`.
- Only after all above PASS and final owner/legal approval: enable publication and invite the first three companies with setup support. Not before Google scope approval/security determination.

## Current stop conditions

STAGED frontend collision risk, no deployed services, no production variables/domains/TLS, Google/Stripe LIVE incomplete, monitoring/recurring restore unverified, unpatched dev-only npm advisory disposition, Docker-dependent fresh integration unavailable on this host after normal Docker Desktop start, and current fixes uncommitted/unpushed. **Current gate = BLOCKED.**
