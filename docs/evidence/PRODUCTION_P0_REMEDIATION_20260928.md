# Production P0 remediation evidence — 2026-09-28

## Identity and isolation

- Branch: `arc/profit-radar-release-readiness`
- HEAD at start: `435bb0ac368c32e50dda918863213b3cdbf69543`
- Validation target includes the pre-existing uncommitted release tree; no change was discarded.
- Production Supabase/API, Stripe LIVE, Google Console/OAuth, Gmail send, deploy, commit and push: **0**.
- v2 SHA-256 remained `B5152C99E1368989FB35203686DB3D29CB395362C1E8282D6F1F9BBB8EDC86F0`; preflight remained `EDE597B72EE224447FFC8D6DE835C3AF90BFC8F439374CF2BDB34920D730D8D5`.

## Implemented evidence

- Production backend validation: separate HTTPS frontend/backend, exact CORS, callback/scheduler origin binding, no loopback, LIVE-only billing, key prefix, provider/AI caps; readiness includes database billing-mode match.
- Frontend Production publication validation: seller/contact/refund/cancel/delete/retention/international transfer/jurisdiction/effective date and approval gates. A local build may only display the explicit preparation state.
- Production Auth runner: real A/B fixture IDs, own read, foreign list/detail denial, browser table denial, foreign direct update/delete 42501 with service-role unchanged proof, service-only RPC denial, canonical owner link, unauthorized/invalid JWT and exact cleanup/count delta. It was exercised only against fixed disposable loopback Supabase.
- Worker/monitoring: scheduler-secret HTTP path, company DB lock/retry system, transport exponential backoff, structured redacted state, heartbeat/readiness, SIGTERM shutdown, systemd restart, runtime probes and maintenance counters.
- Backup: provider-independent pg_dump→age implementation and systemd timer template. Existing isolated restore drill created a fresh DB and matched schema/ACL/RLS/function/index/row-count fingerprint for 54 tables; source remained unchanged.
- Legal/OAuth/Stripe packages and deploy environment/service templates were added. External values and approvals remain intentionally absent.

## Commands and results

- `python scripts/run_local_regression.py --allow-disposable-fixtures`: integration **32 passed / 0 skipped**; complete Backend **318 passed / 0 skipped**. Twelve warnings are Supabase SDK timeout/verify deprecations.
- `python -m scripts.restore_isolated --allow-disposable-fixtures --workers-stopped`: **PASS**, source unchanged, 54 tables, fresh retained target `pr_restore_e09da14aacd94cd4b19fdf2fcffba112`.
- Isolated worker smoke: local API `/health` and `/ready`, scheduler-secret path and worker heartbeat PASS. The persistent synthetic DB had 100 connected test rows; company executions failed and are preserved as `degraded`, not real Google evidence. Gmail send calls 0.
- Python compileall, pip check, pip-audit: PASS / no broken requirements / no known vulnerabilities.
- Frontend Node tests **8/0**, TypeScript, ESLint, Next production build **22 routes**, npm audit **0**: PASS. The build used an explicit non-routable HTTPS build origin because `next build` correctly rejects the local `.env.local` Backend destination in production mode.
- `git diff --check`: PASS (line-ending notices only).
- candidate working-tree scan: **380 text files, 0 actual-looking Stripe/OpenAI/Google/private-key/JWT patterns**.

## Remaining external gates

Clean reviewed commit/artifact, public domain/TLS/secret store, final legal values/review, Google verification/security assessment, Stripe LIVE objects and DB promotion, deployed worker/monitor receiver/on-call, encrypted off-host backup/key custody and Production A/B/deploy evidence. None is treated as locally PASS.
