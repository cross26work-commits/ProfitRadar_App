# Railway Production deployment preflight

- Completed: `2026-10-03T08:22:36+09:00`
- Scope: preflight only; no deployment authorization
- Release commit: `9099d9a4667670eb505157acd66f0c5841f2534a`
- Release artifact: `profit-radar-9099d9a4667670eb505157acd66f0c5841f2534a.tar.gz`
- Artifact SHA-256: `61C7CF281E5920B445C2E8FADA17EC93C7FDB6EB5610E3740BA86548FDB57C0A`
- Supabase Production: `runxnxvwjqblyzdcegay`, `ap-northeast-1`, READY
- Production deployment performed: **NO**
- Production/DNS/Stripe LIVE/Google OAuth/Supabase changes: **0**

## Decision

**BLOCKED for deployment.** The Railway account and intended empty Production project are now confirmed read-only. No services or repository connection exist, and no Railway variable state is configured. Production environment values, reviewed runtime pins, Google Production OAuth approval, Stripe LIVE configuration/database promotion, alert receiver/on-call, and recurring encrypted backup operation remain owner actions.

This result does not invalidate the READY Production Supabase gate and does not authorize a deploy.

## Release integrity

- HEAD exactly matches the approved release commit.
- Working tree contains only the expected release-status update and Production Supabase evidence before this preflight; this preflight adds only this evidence file and a status update.
- Artifact manifest and content hash: PASS.
- Fresh migration safety/evidence: PASS; 23 migrations, 3 disposable runs, canonical schema SHA-256 `55629B9C3C435AFA74DE08FAD7FD32D18B4EABBE1117E83EB575DB24BC3B835D`.
- Repository secret scan: 506 files, 0 findings.

## Railway account and project

- Railway CLI: unavailable on this host.
- Authenticated workspace: `cross26work-commits's Projects` (safe workspace ID `5587a553-31ff-4a1b-8b27-9bb9574a36c1`).
- Confirmed project: `Profit Radar Production`, project ID `812c77be-b93b-4db6-9338-1bc43f415707`.
- Confirmed environment: `production`, environment ID `8bcf3a8c-ba91-421c-ad11-e9c0d27c6889`.
- Project list and architecture both show **No services**. GitHub/repository connection, frontend, backend and worker do not exist; there is no partial service configuration to preserve.
- Workspace displays a Trial allowance (`29 days or $5.00`) and warns that a plan upgrade is required to keep services online. Production billing capacity is therefore an owner gate.
- Result: account **READY**, project identity **READY**, project topology **OWNER ACTION**. No project/service was created and no build was triggered.

### Actual project delta from `deploy/railway/service-plan.json`

| Required object | Actual Railway state | Delta |
|---|---|---|
| GitHub/release source | absent | connect the reviewed release source later, with automatic deploy disabled |
| `frontend` | absent | create later with reviewed root/build/start/health/domain settings |
| `backend` | absent | create later with reviewed root/build/start/readiness/domain settings |
| `worker` | absent | create later as private-only, without a public domain |
| Production variables | no service exists | populate only after services are separately approved |
| Custom domains | no service exists | defer until services are healthy and DNS change is separately approved |

This is a clean empty target, not a conflicting or partially configured deployment.

## Service topology and repository contract

Source: `deploy/railway/service-plan.json`.

| Service | Repository contract | Static result | Deployment result |
|---|---|---|---|
| frontend | root `/frontend`; `npm ci && npm run build`; `npm run start -- --hostname 0.0.0.0 --port $PORT`; health `/`; public `profitradar.jp` | PASS | BLOCKED: project/env/runtime setting not confirmed |
| backend | root `/backend`; install pinned requirements; Uvicorn on `0.0.0.0:$PORT`; health `/ready`; public `api.profitradar.jp` | PASS | BLOCKED: project/env and LIVE billing gate not ready |
| worker | root `/backend`; same pinned requirements; `python -m scripts.sync_worker`; private health `/health`; no public domain | PASS | BLOCKED: private service/env/monitoring not configured |

Automatic migration on deploy is disabled. No service start command runs a migration. Backend `/health` is liveness; `/ready` checks required tables and the database billing mode. Worker non-loopback health exposure is permitted only for `APP_ENV=production`, `WORKER_HEALTH_EXPOSURE=railway-private`, `WORKER_HEALTH_HOST=0.0.0.0`, and a health port equal to Railway `PORT`.

The verified local toolchain was Node `24.18.0`, npm `11.16.0`, and Python `3.13.14`. The repository has no explicit Node/Python runtime pin in the Railway plan, `.node-version`, `.python-version`, or Dockerfile. Pinning the selected Railway runtime to a reviewed version is required before deployment to avoid an unreviewed platform default.

## Frontend preflight

- Package-lock consistency (`npm ci --dry-run --ignore-scripts`): PASS.
- Production build without an explicit backend origin: correctly failed closed.
- Production build with only the intended non-secret origins (`https://api.profitradar.jp`): PASS, 27 routes.
- TypeScript, ESLint, frontend tests: PASS; 26 passed / 0 skipped.
- Browser-visible values are limited to `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_SUPABASE_URL`, and the Supabase publishable/anon key. Server secrets are forbidden by the environment validator.
- `NEXT_PUBLIC_API_BASE_URL` and `BACKEND_ORIGIN` must both be `https://api.profitradar.jp`; HTTPS is required in a production build.
- Status: code/config contract READY; Railway deployment **BLOCKED** pending project, runtime pin and complete values.

## Backend preflight

- Start command correctly binds Uvicorn to `0.0.0.0:$PORT`.
- `/health` and table/billing-aware `/ready` exist.
- Production startup fails closed on missing settings, unsafe/loopback origins, non-exact CORS, TEST Stripe credentials, incomplete AI budget settings, invalid support SMTP/admin settings, or worker-monitoring mismatch.
- Exact origins: frontend `https://profitradar.jp`; backend/scheduler `https://api.profitradar.jp`; CORS only `https://profitradar.jp`.
- Supabase service-role and all Google/Stripe/OpenAI/SMTP/encryption/scheduler credentials remain server-only.
- Production database billing mode is currently `test`; code requires approved LIVE mode and matching approval reference in both environment and database before `/ready` can pass.
- Status: code/config contract READY; Railway deployment **BLOCKED** pending environment, Stripe LIVE gate and runtime pin.

## Worker preflight

- Five-minute interval contract: `GMAIL_SYNC_INTERVAL_SECONDS=300`.
- Scheduler calls only `POST https://api.profitradar.jp/gmail/scheduled-sync` with its dedicated secret.
- Retry/backoff, fixed-field safe logs, health/readiness, and SIGTERM/SIGINT graceful shutdown are implemented and tested.
- Worker must have no public domain. Railway private DNS must be derived from the actual service name; `worker.railway.internal` is valid only if that service is actually named `worker`.
- Worker does not require Supabase, Google, Stripe, OpenAI, token-encryption, or SMTP credentials.
- Status: code/config contract READY; deployment **BLOCKED** pending Railway private service, variables and monitoring.

## Production environment matrix

No Railway environment was readable, so no variable is classified as already configured. Exact value names are recorded below without values.

### Frontend

| Classification | Variables | State |
|---|---|---|
| PUBLIC / shared config | `APP_ENV`, `BACKEND_ORIGIN`, `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` | contract known; MISSING/unconfirmed in Railway |
| PUBLIC / owner legal action | `SALES_PUBLICATION_APPROVED`, `LEGAL_REVIEW_APPROVED`, `COMMERCIAL_DISCLOSURE_APPROVED`, `SELLER_NAME`, `SELLER_ADDRESS_DISCLOSURE_MODE`, `SUPPORT_EMAIL`, `SELLER_PHONE_DISCLOSURE_MODE`, `REFUND_POLICY`, `CANCELLATION_POLICY`, `PRIVACY_CONTACT`, `INTERNATIONAL_TRANSFER_DISCLOSURE`, `DATA_DELETION_POLICY`, `GOVERNING_COURT`, `TERMS_EFFECTIVE_DATE`, `DATA_RETENTION_DAYS`, `BACKUP_RETENTION_DAYS` | OWNER ACTION / MISSING |

### Backend

| Classification | Variables | State |
|---|---|---|
| SHARED SERVER CONFIG | `APP_ENV`, `FRONTEND_URL`, `BACKEND_URL`, `CORS_ORIGINS`, `GOOGLE_REDIRECT_URI`, `SCHEDULER_BACKEND_URL`, `STRIPE_MODE`, `BILLING_LIVE_APPROVED`, `BILLING_LIVE_APPROVAL_REF`, `OPENAI_MODEL_PRIMARY`, `OPENAI_MODEL_ESCALATION`, `OPENAI_MODEL_STANDARD`, `AI_MODEL_MAX_RATES_JSON`, `AI_COMPANY_MONTHLY_TOKENS`, `AI_COMPANY_MONTHLY_USD`, `AI_MONTHLY_GENERATION_LIMIT`, `ACCOUNT_AUDIT_RETENTION_DAYS`, `SUPPORT_ADMIN_USER_IDS`, `SUPPORT_RETENTION_DAYS`, `SUPPORT_EMAIL_PROVIDER`, `SUPPORT_EMAIL_FROM`, `SUPPORT_EMAIL_VERIFIED_DOMAIN`, `SUPPORT_EMAIL_SENDER_APPROVED`, `SUPPORT_EMAIL_SMTP_HOST`, `SUPPORT_EMAIL_SMTP_PORT`, `TERMS_VERSION`, `WORKER_HEALTH_HOST`, `WORKER_HEALTH_PORT`, `WORKER_HEALTH_URL`, `WORKER_HEALTH_EXPOSURE`, `GMAIL_SYNC_INTERVAL_SECONDS`, `WORKER_MAX_BACKOFF_SECONDS`, `MONITORING_WEBHOOK_URL` | contract known; OWNER ACTION / MISSING |
| PUBLIC provider config | `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `GOOGLE_CLIENT_ID`, `STRIPE_PRICE_ID` | OWNER ACTION / MISSING |
| SERVER SECRET | `SUPABASE_SERVICE_ROLE_KEY`, `OAUTH_STATE_SECRET`, `GOOGLE_CLIENT_SECRET`, `GMAIL_TOKEN_ENCRYPTION_KEYS`, `GMAIL_SCHEDULER_SECRET`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `OPENAI_API_KEY`, `CONTACT_RATE_LIMIT_SECRET`, `SUPPORT_EMAIL_SMTP_USERNAME`, `SUPPORT_EMAIL_SMTP_PASSWORD` | OWNER ACTION / MISSING |

### Worker

| Classification | Variables | State |
|---|---|---|
| SHARED SERVER CONFIG | `APP_ENV`, `SCHEDULER_BACKEND_URL`, `GMAIL_SYNC_INTERVAL_SECONDS`, `WORKER_MAX_BACKOFF_SECONDS`, `WORKER_HEALTH_HOST`, `WORKER_HEALTH_PORT`, `WORKER_HEALTH_URL`, `WORKER_HEALTH_EXPOSURE`, `MONITORING_WEBHOOK_URL` | contract known; OWNER ACTION / MISSING |
| SERVER SECRET | `GMAIL_SCHEDULER_SECRET` | OWNER ACTION / MISSING |

Railway supplies `PORT`; `WORKER_HEALTH_PORT` must use a Railway variable reference to it. No local `.env` or TEST credential may be promoted.

## Supabase connection boundary

- Production project identity and schema are READY from the separate Production Supabase gate.
- Frontend may receive only Production URL and publishable/anon key.
- Backend receives URL, anon key and service-role key.
- Worker receives no Supabase credential.
- No `NEXT_PUBLIC_*` variable may contain service-role/provider/server secrets.
- Production configuration must point only to project ref `runxnxvwjqblyzdcegay`; this preflight did not retrieve or store keys.

## Google OAuth

- Exact callback: `https://api.profitradar.jp/gmail/callback`.
- Homepage: `https://profitradar.jp`.
- Code requests only `gmail.send` and `gmail.readonly`; no Calendar scope is present.
- Google classifies `gmail.send` as Sensitive and `gmail.readonly` as Restricted. Because restricted Gmail data is processed/stored server-side, verification and the applicable independent security assessment must be confirmed before external customers.
- Production client ID/secret, authorized redirect URI, domain ownership, branding/consent publication, scope verification and assessment evidence are not available in this preflight.
- Status: **OWNER ACTION / BLOCKING for Gmail launch**.

## Stripe LIVE

- Exact webhook endpoint: `https://api.profitradar.jp/billing/webhook`.
- Application verifies the LIVE Price is active, JPY 19,800, monthly, interval count 1 and tax-inclusive; Checkout requires a payment method and applies a seven-day trial.
- Startup rejects TEST mode/keys in Production and `/ready` requires the database billing mode and approval reference to match.
- LIVE Price, keys, webhook secret, signed webhook delivery and one-way database LIVE promotion are unconfirmed. No LIVE resource or charge was touched.
- Status: **OWNER ACTION / BLOCKING for paid launch**.

## Domain and DNS plan

- `profitradar.jp` routes to frontend; `api.profitradar.jp` routes to backend; worker has no public domain.
- Railway must first provide the exact route and ownership-verification values. お名前.com changes then use those values only; no fixed A record is invented and nameservers are not changed.
- Railway documentation currently requires the provided routing record plus its ownership-verification TXT record for custom domains. Apex record type depends on the DNS provider's CNAME-flattening/ALIAS/ANAME support.
- Status: **READY FOR LATER CHANGE**, but exact records are unavailable until the Railway project/services exist.

## Monitoring, backup and rollback

| Area | Result | Remaining action |
|---|---|---|
| Backend health/readiness | READY in code | configure external probe after deployment |
| Worker health/readiness/heartbeat | READY in code | configure private target and independent missed-heartbeat alert |
| Alert delivery | OWNER ACTION / BLOCKING | choose HTTPS receiver and on-call/escalation owner; verify delivery |
| Encrypted logical backup | READY in code | choose off-site storage, age-key custody, schedule and retention |
| Recurring Production backup/restore | OWNER ACTION / BLOCKING | run first encrypted backup plus disposable restore and record RPO/RTO |
| Application rollback | READY in runbook | retain previous Railway deployments; stop worker/signup before rollback |
| Database rollback | READY as forward-fix/restore policy | never destructively reverse the committed schema |
| DNS rollback | READY in runbook | capture existing records immediately before any later DNS change |

## Security and tests

- Focused Production deployment/runtime/worker/billing tests: 53 passed.
- Frontend tests: 26 passed / 0 skipped; TypeScript PASS; ESLint PASS; production build PASS after supplying only the intended public backend origins.
- Plain Backend suite: 300 passed / 60 skipped because disposable Supabase integration credentials were not supplied to this invocation. These skips are not counted as PASS; the immutable release evidence separately records 360/0 and fresh/isolated 35/0 for the approved commit.
- Python compileall PASS; pip check PASS; pip-audit 0 vulnerabilities; npm audit 0 vulnerabilities.
- Secret scan PASS, 506 files / 0 findings.
- `git diff --check` PASS before evidence update.
- No Production API, Supabase, Gmail, Stripe, DNS or Railway mutation occurred.

## Remaining blockers

1. Upgrade/approve a Railway plan suitable for persistent Production services; the workspace is currently Trial-limited.
2. Separately approve creation of the three empty services and GitHub/release-source connection with automatic deploy disabled; this preflight did not create them.
3. Pin reviewed Node/Python runtimes and populate/validate the full Railway environment matrix.
4. Complete legal/publication values and approvals.
5. Complete Google Production OAuth/domain/Restricted-scope verification and applicable security assessment.
6. Complete Stripe LIVE Price/webhook/account preparation and separately approve the one-way database LIVE promotion.
7. Configure alert receiver/on-call and recurring encrypted off-site backup with restore evidence.
8. Obtain separate deployment approval, followed later by separate DNS and Production smoke approvals.

## Next owner action

Approve/upgrade the Railway workspace plan required to keep Production services online; do not create services or deploy yet.
