# Railway production service plan

This directory is a reviewed, non-secret deployment specification. It is not an executable deployment approval.

Railway's current documentation deprecates legacy Config-as-Code for new services, so this new empty project must not be bootstrapped with a speculative `railway.toml`/`railway.json`. Create the three services in the owner-controlled project and copy the exact settings from `service-plan.json`. Do not enable automatic deploys until the first controlled release is approved.

- Frontend: public `profitradar.jp`; root `/frontend`; Railway-provided `PORT` is passed to `next start`.
- Backend: public `api.profitradar.jp`; root `/backend`; `/health` is liveness and `/ready` validates required tables plus billing mode. Railway health check uses `/ready`.
- Worker: no public domain; root `/backend`; its health server binds `0.0.0.0:$PORT` only when `APP_ENV=production`, `WORKER_HEALTH_EXPOSURE=railway-private`, and `WORKER_HEALTH_PORT=$PORT`. Railway health check uses `/health`; `/ready` remains an operational batch-completion check.

The worker calls the public HTTPS backend scheduler endpoint so the backend startup guard can verify the exact production origin. The scheduler secret authenticates that call. The worker never receives Supabase, Stripe, Google, Gmail token-encryption, or AI secrets.

Railway references: [monorepos](https://docs.railway.com/guides/monorepo), [healthchecks](https://docs.railway.com/guides/healthchecks), [private networking](https://docs.railway.com/guides/private-networking), [custom domains](https://docs.railway.com/guides/public-networking#custom-domains).
