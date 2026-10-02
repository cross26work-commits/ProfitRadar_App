# Production smoke test

Requires separate Production approval. Never include customer data, tokens, message bodies or provider secrets in evidence.

## Automated read-only checks

Run `scripts/production/Invoke-ProductionSmokeTest.ps1 -RequireExplicitProductionApproval I_APPROVE_READ_ONLY_PRODUCTION_SMOKE_TEST`. It sends GET only to frontend `/`, backend `/health` and `/ready`.

## Controlled functional checks

1. Create dedicated Production E2E users A/B only after the Production Auth runner approval. Verify each can read its own profile and neither can read/write/delete the other tenant. Confirm cleanup/count delta.
2. Register a separate controlled trial user through UI; confirm onboarding, `/auth/me`, Dashboard, Customers, Leads, Results, draft save/reload and logout/login.
3. Connect an owner-controlled Gmail only after Google approval. Confirm status response has no token, sync pagination/idempotency, recipient binding and draft. Real send requires a separate visible From/To/body approval.
4. Validate Stripe LIVE configuration read-only. A real Checkout/charge/cancel is not a smoke action and requires its own explicit approval.
5. Confirm worker `/health`, first completed batch `/ready`, company lock/run record, alert delivery, backup completion and restore evidence.

Stop immediately for cross-tenant data, raw exception/secret output, incorrect recipient, TEST/LIVE mismatch, readiness failure, unknown external side effect or cleanup/count mismatch.
