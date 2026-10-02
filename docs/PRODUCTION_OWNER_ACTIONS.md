# Production owner actions

Only these external actions remain; none is authorized by this document.

1. Approve Railway billing, connect the reviewed GitHub commit/artifact and create the three services from `deploy/railway/service-plan.json` with automatic deploy disabled.
2. Create the new Tokyo (`ap-northeast-1`) Supabase Production project and record its 20-character project ref. The historical pinned project is not the selected target; do not reuse its credentials or migration history.
3. Enter the environment matrix in Railway/provider secret stores and run the redacted preflight; never paste secrets into chat or commit them.
4. Obtain counsel/owner approval for seller, privacy, terms, retention, cancellation/refund and publication values.
5. Complete Google domain/brand/Restricted-scope verification and any required independent security assessment.
6. Complete Stripe LIVE account/business/bank setup, create the reviewed ¥19,800 monthly price and webhook, then request the separate LIVE promotion approval. Do not charge during setup.
7. Configure alert receiver/on-call ownership plus encrypted off-host backup/key custody, retention, RPO/RTO and a restore drill.
8. Approve the exact database migration, Railway deployment and final お名前.com DNS changes after preflight is `READY`.

Next single owner action: **create the new Tokyo (`ap-northeast-1`) Supabase Production project and record its 20-character project ref in the release ticket, without sharing keys.**
