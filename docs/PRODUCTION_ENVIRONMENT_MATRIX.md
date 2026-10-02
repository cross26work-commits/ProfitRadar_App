# Production environment matrix

Values belong in Railway/Supabase/provider secret stores, never this repository. `deploy/production-env.schema.json` is the machine-readable required-name contract and `scripts/production/Test-ProductionEnvironment.ps1` validates redacted local env files without printing values.

## Frontend

| Variable | Required | Secret | Source / exact contract |
|---|---:|---:|---|
| `APP_ENV` | yes | no | `production` |
| `BACKEND_ORIGIN` | yes | no | `https://api.profitradar.jp` (server build/rewrite) |
| `NEXT_PUBLIC_API_BASE_URL` | yes | no | `https://api.profitradar.jp` |
| `NEXT_PUBLIC_SUPABASE_URL` | yes | no | final Production Supabase URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | yes | public | final Production anon/publishable key only |
| `SALES_PUBLICATION_APPROVED`, `LEGAL_REVIEW_APPROVED`, `COMMERCIAL_DISCLOSURE_APPROVED` | yes | no | all `true` only after owner/legal approval |
| `SELLER_NAME`, `SUPPORT_EMAIL`, `PRIVACY_CONTACT`, `GOVERNING_COURT` | yes | no | owner/legal-approved publication values |
| `SELLER_ADDRESS_DISCLOSURE_MODE`, `SELLER_PHONE_DISCLOSURE_MODE` | yes | no | current contract requires `request` |
| `REFUND_POLICY`, `CANCELLATION_POLICY`, `INTERNATIONAL_TRANSFER_DISCLOSURE`, `DATA_DELETION_POLICY` | yes | no | counsel-approved text |
| `TERMS_EFFECTIVE_DATE` | yes | no | `YYYY-MM-DD` |
| `DATA_RETENTION_DAYS`, `BACKUP_RETENTION_DAYS` | yes | no | current publication contract: `30`, `90` |

Never add any name from `server_secret_only` to the frontend service.

## Backend

| Category | Required variables | Secret/source | Validation |
|---|---|---|---|
| Runtime/origins | `APP_ENV`, `FRONTEND_URL`, `BACKEND_URL`, `CORS_ORIGINS` | non-secret; exact public HTTPS origins | startup fail-closed |
| Supabase | `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` | project settings; service role secret | HTTPS/non-loopback, readiness tables |
| OAuth/Gmail | `OAUTH_STATE_SECRET`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `GMAIL_TOKEN_ENCRYPTION_KEYS` | Production Google client and key custody | exact callback, encrypted tokens |
| Scheduler | `GMAIL_SCHEDULER_SECRET`, `SCHEDULER_BACKEND_URL` | secret + exact backend URL | constant-time endpoint auth |
| Stripe | `STRIPE_MODE`, `BILLING_LIVE_APPROVED`, `BILLING_LIVE_APPROVAL_REF`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID` | Stripe LIVE dashboard/release ticket | LIVE prefixes + DB gate |
| AI | `OPENAI_API_KEY`, `OPENAI_MODEL_PRIMARY`, `OPENAI_MODEL_ESCALATION`, `OPENAI_MODEL_STANDARD`, `AI_MODEL_MAX_RATES_JSON`, `AI_COMPANY_MONTHLY_TOKENS`, `AI_COMPANY_MONTHLY_USD`, `AI_MONTHLY_GENERATION_LIMIT` | owner pricing/budget approval | bounded model/rates/limits |
| Worker observability | `WORKER_HEALTH_HOST`, `WORKER_HEALTH_PORT`, `WORKER_HEALTH_URL`, `WORKER_HEALTH_EXPOSURE`, `GMAIL_SYNC_INTERVAL_SECONDS`, `WORKER_MAX_BACKOFF_SECONDS`, `MONITORING_WEBHOOK_URL` | Railway private DNS + alert receiver | startup validation |
| Retention/admin | `ACCOUNT_AUDIT_RETENTION_DAYS`, `SUPPORT_ADMIN_USER_IDS`, `SUPPORT_RETENTION_DAYS`, `TERMS_VERSION` | approved UUID allowlist/policy | ranges and UUID syntax |
| Contact mail | `CONTACT_RATE_LIMIT_SECRET`, `SUPPORT_EMAIL_PROVIDER`, `SUPPORT_EMAIL_FROM`, `SUPPORT_EMAIL_VERIFIED_DOMAIN`, `SUPPORT_EMAIL_SENDER_APPROVED`, `SUPPORT_EMAIL_SMTP_HOST`, `SUPPORT_EMAIL_SMTP_PORT`, `SUPPORT_EMAIL_SMTP_USERNAME`, `SUPPORT_EMAIL_SMTP_PASSWORD` | approved SMTP provider | verified domain/465 or 587 |

Exact public values: `FRONTEND_URL=https://profitradar.jp`, `BACKEND_URL=https://api.profitradar.jp`, `CORS_ORIGINS=https://profitradar.jp`, `GOOGLE_REDIRECT_URI=https://api.profitradar.jp/gmail/callback`, `SCHEDULER_BACKEND_URL=https://api.profitradar.jp`.

## Worker

`APP_ENV=production`, `SCHEDULER_BACKEND_URL=https://api.profitradar.jp`, `GMAIL_SCHEDULER_SECRET`, `GMAIL_SYNC_INTERVAL_SECONDS=300`, bounded `WORKER_MAX_BACKOFF_SECONDS`, `WORKER_HEALTH_HOST=0.0.0.0`, `WORKER_HEALTH_PORT=${PORT}`, `WORKER_HEALTH_URL=http://worker.railway.internal:${PORT}`, `WORKER_HEALTH_EXPOSURE=railway-private`, and `MONITORING_WEBHOOK_URL`. Railway supplies `PORT`; its value must be copied through `WORKER_HEALTH_PORT` using a Railway variable reference. Do not give the worker database/provider secrets.

## Backup job / controlled operator environment

`APP_ENV=production`, `PGHOST`, `PGPORT`, `PGUSER`, `PGDATABASE`, `PGPASSWORD`, `PGSSLMODE=verify-full`, `BACKUP_DIR`, `BACKUP_AGE_RECIPIENT`, `BACKUP_AGE_IDENTITY_FILE`, `BACKUP_RETENTION_DAYS`. The age private identity is never stored on the same platform as every backup copy.

## Variables intentionally not required

`SUPABASE_JWT_SECRET` is optional and should be omitted so backend authentication resolves the user through Supabase Auth. Twilio variables are legacy configuration and not part of the initial Gmail-only sale.
