# Local startup repair evidence — 2026-09-30 JST

## Scope and isolation

- Branch: `arc/profit-radar-release-readiness`; base HEAD: `31573c4da79b218022e7e4c40ac53fcba61bc5bc`; the existing dirty Legal/Support worktree was preserved.
- Execution targets were limited to loopback Supabase projects `profit-radar-local` (API 54421 / DB 54422) and the pre-existing test project `profit-radar-disposable` (API 54321 / DB 54322).
- Production Supabase, Gmail, Stripe LIVE, deployment, commit and push operations: **0**.

## Root cause and repair

`202607020001_profit_radar_core.sql` created `reply_logs` without `gmail_message_id` and `gmail_thread_id`. `202609070001_release_candidate_safety.sql` referenced `gmail_message_id` in a unique index before the columns were introduced by `202609100001_repair_runtime_schema.sql`. Existing remote databases already had the legacy columns, and the older isolated baseline manually supplied them, so neither path exposed the clean-build ordering defect.

`202609060001_reply_logs_gmail_bridge.sql` is an additive, transaction-wrapped bridge ordered between core and the first consumer. It adds only the two nullable text columns if absent and then verifies their exact type/null/default contract. Re-applying it against the completed local schema was a no-op and the unique index remained present exactly once. Its rollback intentionally refuses a destructive column drop because a post-commit rollback cannot distinguish legacy columns from bridge-created columns; failed application is transactionally rolled back, and committed recovery uses backup restore or a reviewed forward fix.

The local launcher stages the ordinary migration chain byte-for-byte and excludes only the historical remote-only V1/V2 schema-forward repairs. Those two migrations are pinned to a captured remote baseline and are not valid members of a fresh schema chain. The staged clean local project applied versions `202607020001`, `202609060001`, `202609070001` through `202609110001`, and `20260928153027` successfully.

## Launcher verification

- `scripts/start-profit-radar.ps1 -NoBrowser`: PASS; output contains only the three loopback READY URLs and no Supabase keys.
- Repeated start: PASS/idempotent.
- Production-like `APP_ENV`: rejected before Docker/database work.
- `scripts/stop-profit-radar.ps1`: PASS; Backend, Frontend and only `profit-radar-local` stopped. The project volume count was 1 before and 1 after. No volume/container prune, reset or unrelated project stop occurred.
- Restart after stop: PASS. `/health`, `/ready`, `/login`, `/register` and `/onboarding` returned HTTP 200.

## Final verification

- Local migration history and `reply_logs` column/index contract: PASS.
- Six Legal/Support tables: RLS enabled; browser-denial Auth/PostgREST integration included below.
- Disposable real Auth/PostgREST integration: **33 passed / 0 skipped**.
- Backend: **339 passed / 0 skipped**; only 12 Supabase SDK deprecation warnings.
- Frontend: **8 passed / 0 skipped**; TypeScript, ESLint and 27-route production build PASS. The build used `https://api.example.invalid` only as a non-network configuration sentinel and is not a deploy artifact.
- Python compileall and `pip check`: PASS. `pip-audit`: 0 known vulnerabilities after minimum safe upgrades to `oauthlib 4.0.0` and `PyJWT 2.14.0`.
- `npm audit`: 0 vulnerabilities after lock-only transitive remediation to `brace-expansion 1.1.21` and `5.0.12`.
- Candidate secret scan: 460 repository files, 0 findings.
- `git diff --check`: PASS.
- Legal/Support disposable rollback drill remains PASS: six created tables to zero; rollback refuses any legal/support evidence-bearing database.

## External gates

Local startup and code regression are complete. Public sale remains dependent on the owner/external actions in `OWNER_ACTIONS.md`: final legal review and seller/support values, Production domain/TLS/secret store, Google approval, Stripe LIVE preparation, recurring backup, monitoring/worker installation, and a separately approved controlled deployment.
