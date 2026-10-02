# Production deployment preparation evidence — 2026-10-02

> Historical checkpoint: its fresh-database blocker was resolved later on 2026-10-02. Current database evidence is `FRESH_PRODUCTION_MIGRATION_20261002.md`; Production operations still require owner approval.

- Baseline: branch `arc/profit-radar-release-readiness`, commit `4de25c344b1816aa1cfb33d46c8e9aecf3fe9820`, clean at start.
- External mutations: Railway deploy 0, Supabase write 0, DNS change 0, Stripe/Google/Gmail action 0, push/commit 0.
- Architecture: Railway frontend/backend/private worker service contract, exact domains/origins, env ownership, DNS template, monitoring, backup/restore, rollback and smoke procedures prepared.
- Worker: explicit Railway-private health mode added; non-loopback remains rejected outside `APP_ENV=production` plus `WORKER_HEALTH_EXPOSURE=railway-private`; platform `PORT` must equal configured port.
- Database: static migration safety PASS (22 files, pinned v2 hash unchanged). Brand-new local Supabase applied through `202609110001`; remote-only v1 then aborted transactionally on `profiles.name`. New-project migration readiness is BLOCKED by the target decision documented in `PRODUCTION_SUPABASE_MIGRATION_DECISION.md`. Established disposable JWT/RLS integration remains PASS.
- Dependency remediation: urllib3 `2.7.0→2.8.0`, PyJWT `2.14.0→2.15.1`, Next.js/eslint-config-next/bundle-analyzer `16.3.4→16.3.8`; pip-audit and npm audit report zero known vulnerabilities.
- Regression: disposable Integration **33 passed / 0 skipped**; Backend **356 passed / 0 skipped**; Frontend Node **26 passed / 0 skipped**; TypeScript, ESLint, 27-route production build, compileall, pip check, pip-audit, npm audit, migration static check, candidate secret scan and `git diff --check` PASS.
- Worker isolated proof: backend health/readiness, scheduler tick and worker heartbeat PASS; the long-lived synthetic fixture reported 100 expected disconnected-company failures, Gmail sends 0.
- Test isolation remediation: an ignored developer `.env` caused one invalid-token unit test to attempt a read-only Auth GET to the historical Supabase URL; it returned 503 and made no write. A pre-import pytest isolation fixture now forces loopback/synthetic auth. All subsequent full regression traffic was local. Production side effects remain 0, but the preparation turn did contain that one failed external read attempt and it is not represented as “connection 0”.

Final preparation verdict: **BLOCKED** until the final Supabase target/migration stream is decided and external owner inputs (project, secrets, legal, Google, Stripe, monitoring, backup, DNS, deployment approval) are completed. No deployment was performed.
