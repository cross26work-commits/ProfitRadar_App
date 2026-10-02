# Production rollback plan

## Before any change

Record the immutable app artifact hash, current Railway deployments, target DB identity, schema fingerprint, non-sensitive row counts, DNS records, provider object IDs and a successfully restored encrypted backup. Stop writers for database changes.

## Application failure

Disable public signup and worker first. Roll back Railway backend/frontend/worker to the previous immutable deployment. Do not change database rows merely to match old code. Require `/health`, `/ready`, authentication and tenant smoke checks before reopening.

## Migration failure

- Before COMMIT: confirm transaction rollback and re-run read-only verification. Do not continue with later statements.
- After COMMIT: stop writers, preserve logs/fingerprints, and use a reviewed forward fix. If recovery cannot preserve correctness, restore the complete verified backup to a controlled replacement project/database and separately approve traffic switching.
- Never replay historical forward v2, run blind `db push`, delete/backfill unknown rows or weaken RLS to recover availability.

## Provider failure

Google: stop worker/send, leave encrypted token evidence intact, correct callback/client configuration, never auto-resend. Stripe: disable checkout, keep webhook processing fail-closed, reconcile provider state, never reverse the one-way DB LIVE promotion or mix TEST/LIVE. Unknown send/payment outcomes require provider reconciliation before retry.

## DNS failure

Restore the exact prior DNS records recorded before change. DNS rollback does not roll back application/database state. Maintain the Railway generated domain for operator-only verification where approved.
