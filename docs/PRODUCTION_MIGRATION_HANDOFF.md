# v2 production migration: execution boundary

Prepared 2026-09-17. **Historical execution handoff; migration stage is complete per owner report.** Owner reports production project `zszmetqhksthduoxfvac`: v2 COMMIT succeeded, post-apply `FINAL=PASS`, pre/post counts of the existing 20 tables matched exactly, and production backup restore proof passed. This agent has not independently accessed production to reproduce those results. Backup artifact timestamp/path/SHA256 and the post-apply output have not been attached in this turn. Current next stage is separately approved production Authenticated A/B E2E, not migration replay; see `docs/RELEASE_STATUS.md`.

## Exact artifact

- Apply only `supabase/migrations/202609150001_remote_schema_forward_v2.sql`, SHA256 `B5152C99E1368989FB35203686DB3D29CB395362C1E8282D6F1F9BBB8EDC86F0`.
- Historical v1 SQL and past migrations are not part of this operation. Do not use `supabase db push`, migration-history repair, or a shell that substitutes interpolated SQL text.
- The SQL contains BEGIN/COMMIT, 5-second lock timeout, 120-second statement timeout, exact prerequisites, no customer-row backfill, and billing test mode only.
- Read-only pre-apply comparison: `supabase/remote_schema_forward_final_gate.sql`, SHA256 `BB10D080796F4792F31D48843E60E934355848332FE51BBFD114BF28780893C6`. Owner reports FINAL=PASS, with known ACL/onboarding remediation.

## Before approval

1. Confirm the remote project ID/environment and that the captured oracle belongs to that exact project. Preserve the remote Final Gate output and a fresh read-only `supabase/remote_schema_forward_row_counts.sql` count table. Any difference from the approved schema or nonzero legacy global sync rows stops the application; the v2 transaction independently rechecks the prerequisites.
2. Confirm a completed, restorable backup and its restore method. Preserve schema, RLS/policies, grants including column/sequence ACL, function signatures/bodies/owners/config, triggers, indexes, and existing business-row counts. The local `pr_restore_*` drill proves only the disposable local DB path, not production restore capability.
3. Stop API/worker/cron writers, confirm their process state and a maintenance window, identify the DB operator and recovery contact. Keep them stopped until immediate post-apply checks pass. The owner must expressly approve applying the exact v2 artifact after reviewing these concrete facts.

Do not copy passwords, tokens, customer rows, or Gmail message bodies into chat or audit reports. Use a protected database service alias if executing with `psql`; use a fresh session, UTF-8 encoding, and `ON_ERROR_STOP=1`. The repo does not contain production credentials.

## Immediately after an approved execution

1. Record transaction success/COMMIT or precise failure state. If any SQL error occurred, do not continue; verify rollback and compare the saved object inventory and counts. Do not retry with altered guards or a historical migration.
2. Run read-only `supabase/remote_schema_forward_post_apply.sql` and the exact same `supabase/remote_schema_forward_row_counts.sql`. The post-apply SQL checks 11 internal tables, 14 new functions, RLS, effective table SELECT grants, hardened legacy onboarding, canonical registration ACL, global sync, and billing test mode. `FINAL=PASS` is necessary but not sufficient: compare old business counts exactly, canonical body/ACL and four-policy oracle against the saved captures, and check column/inherited privileges.
3. With a dedicated test tenant and authorized operator, check Backend health, login/profile, A/B tenant isolation, normal read paths and service-role writes. Keep Gmail OAuth/send, Stripe charge, cron registration and deployment outside this migration operation. Record test identity, time, result and any error code without secrets.

After COMMIT, rollback is **not** a replay of the inverse SQL. Keep writers stopped and choose a reviewed forward fix or backup restore with its own approval. Never delete new evidence just to make a gate pass.

## Next gate: production Authenticated E2E (not yet approved or run)

The separate `backend/scripts/run_production_auth_e2e.py` pins project `zszmetqhksthduoxfvac`, requires exact `SUPABASE_URL` plus a production-specific confirmation flag, and reads anon/service credentials only from the process environment. It creates two temporary Auth/tenant fixtures, checks JWT login/profile, own and cross-tenant API reads, service-role fixture writes, direct business-table denial, and exact-ID cleanup with pre/post counts. It does not run the older disposable-only `test_p0_supabase_isolation.py`, Gmail, Stripe, Cron, or Deploy. Do not invoke until the owner separately authorizes this write-bearing production E2E; a failure requires operator review, not automatic rerun.

## Remaining sale blockers after migration

Real Google consent/verification, controlled test Gmail E2E, Stripe test-mode E2E, finalized seller/contact/domain/terms/retention, monitoring destination, production environment values and deploy approval. These cannot be inferred from local test results.
