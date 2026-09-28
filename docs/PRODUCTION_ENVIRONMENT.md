# Production environment contract

This document is a deployment contract, not an environment file. Secret values belong in a server-side secret store and must never be committed, copied into frontend variables, printed, or placed in unit files. The machine-readable inventory is `deploy/production-env.schema.json`.

## Separation and startup gate

- Backend: `APP_ENV=production`, a public HTTPS `BACKEND_URL`, an independent HTTPS `FRONTEND_URL`, and `CORS_ORIGINS` containing exactly `FRONTEND_URL`.
- Google callback must be exactly `<BACKEND_URL>/gmail/callback`; `SCHEDULER_BACKEND_URL` must use the same backend origin.
- Production rejects loopback endpoints, HTTP, missing provider settings, `STRIPE_MODE=test`, `sk_test_`, model budgets without prices/caps, and an unapproved LIVE billing switch.
- Frontend: `APP_ENV=production` activates publication validation at build/start configuration time. Final legal and commercial fields and all three publication approvals must be present. Local regression builds omit `APP_ENV=production` and deliberately render “準備中”.
- `BACKEND_ORIGIN` is server-only for the Next rewrite. `NEXT_PUBLIC_API_BASE_URL`, the Supabase URL and publishable/anon key are browser-visible. No server secret may use a `NEXT_PUBLIC_` name.

## Secret-store injection

Create separate restricted files or equivalent managed secret-store bindings:

- `/etc/profit-radar/backend.env` (mode 0600): backend/provider/database secrets and approved origins.
- `/etc/profit-radar/frontend.env` (mode 0600): public browser configuration plus finalized publication text. Do not place service-role/provider secrets here.
- `/etc/profit-radar/backup.env` (mode 0600): PostgreSQL credentials and age recipient/identity paths.

Development, Stripe TEST and Production use separate Google Cloud projects, Stripe modes/objects, environment files and Supabase projects. Copying a TEST file into Production is prohibited.

## Immutable release and rollback

1. Review and commit the candidate. `scripts/build_release_artifact.py` refuses a dirty tree and writes a commit-addressed tarball plus SHA-256 manifest outside the repository.
2. Record the commit and manifest hash in the change ticket. Deploy only that archive; do not rsync a working tree.
3. Before traffic, run backend startup, frontend configuration/build, `/health`, `/ready`, worker `/health` and `/ready`, and the alert-delivery smoke.
4. On a rollback trigger, stop public traffic and worker, deploy the previous verified application artifact, re-inject its matching config, then recheck health/readiness. Do not reverse the already committed v2 schema or delete rows. Any schema forward fix requires a new reviewed migration and backup proof.
