# Production architecture

Status: prepared, not deployed. This document contains no credential value and authorizes no external change.

## Runtime topology

| Component | Host | Public entry | Responsibility |
|---|---|---|---|
| Frontend | Railway service `frontend` | `https://profitradar.jp` | Next.js UI, Supabase browser Auth, server-side API rewrite |
| Backend | Railway service `backend` | `https://api.profitradar.jp` | FastAPI auth/tenant enforcement, Gmail, AI, billing, support APIs |
| Worker | Railway service `worker` | none | five-minute Gmail scheduler; authenticated backend batch call only |
| Database/Auth | owner-created Supabase Production project, Tokyo `ap-northeast-1` | Supabase project URL | PostgreSQL, Auth, RLS, RPC |

`deploy/railway/service-plan.json` is the reviewed service contract. No migration is run from a service start command. Backend `/health` proves only process liveness; `/ready` proves required database objects and billing-mode agreement. Worker `/health` proves process liveness; `/ready` becomes healthy after a completed batch.

The worker has no public domain. Its health listener may bind `0.0.0.0:$PORT` only with `WORKER_HEALTH_EXPOSURE=railway-private`; all other non-loopback configurations fail closed. The only worker side effect is `POST https://api.profitradar.jp/gmail/scheduled-sync` authenticated by the scheduler secret. Database locking and idempotency remain backend/RPC responsibilities.

## Trust boundaries

- Browser receives only Supabase URL/anon key and public API URL. Service-role, provider, SMTP, scheduler, billing, encryption and AI secrets are backend-only.
- Backend derives company context from the validated user and service-role lookups; the browser cannot choose a tenant.
- CORS is exactly `https://profitradar.jp`. Google callback is exactly `https://api.profitradar.jp/gmail/callback`. Stripe webhook is `https://api.profitradar.jp/billing/webhook`.
- Supabase Production creation, migration, RLS A/B verification, LIVE provider promotion and deployment are separate owner-approved gates.

## Database identity warning

Repository history records a previously operated project (`zszmetqhksthduoxfvac`), while this preparation request states that the intended Production project has not been created. These are not silently treated as the same environment. The owner must record the final Production project ref in the release ticket before any connection. The existing production E2E runner remains pinned to the historical ref and must not be repointed or run until that decision has a separate review.

## Deployment order

1. Freeze the reviewed commit/artifact; complete off-host backup and rollback evidence.
2. Owner approves the exact Supabase target and migration plan.
3. Apply migrations manually in a stopped-writer window; execute schema/RLS verification.
4. Deploy backend and require `/health` plus `/ready`.
5. Deploy frontend and complete read-only public smoke checks.
6. Deploy worker last; confirm health, one controlled batch, locks and run record.

No automatic migration-on-deploy and no blind `supabase db push` are permitted.
