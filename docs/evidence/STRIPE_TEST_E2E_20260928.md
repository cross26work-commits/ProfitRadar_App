# Profit Radar Stripe TEST E2E evidence

- Completed (UTC): `2026-09-28T06:45:06Z` (success/cancel), followed by decline/failure and regression verification
- Commit SHA: `435bb0ac368c32e50dda918863213b3cdbf69543`
- Working tree: dirty release-candidate tree; existing changes preserved
- Environment: disposable local Supabase `127.0.0.1` and isolated Backend `127.0.0.1:8021`
- Stripe mode: **TEST** (`livemode=false` responses; credential prefixes checked without output)
- Production contacts/side effects: **0**
- Secret/token/customer-row values in this evidence: **0**
- Result: **PASS**

## Real application path

1. A temporary local Auth user and company were created through the Profit Radar onboarding route.
2. The local trial was expired and a paid feature returned HTTP 402 before checkout.
3. Authenticated `POST /billing/checkout` created a real Stripe TEST hosted Checkout Session. The configured TEST Price was verified as active, JPY 19,800/month, interval count 1, tax inclusive.
4. The hosted TEST Checkout completed with Stripe's success test card. The Session became complete/paid and had a TEST subscription.
5. A real Stripe TEST `customer.subscription.created` event passed Profit Radar's HMAC/timestamp verification and current-provider reconciliation. The initial CLI listener had stopped before the payment, so that already-created event was recovered once through the same signed webhook endpoint after the listener was restarted; no payment was repeated.
6. `company_billing` persisted the subscription and paid-through timestamp. `/billing/status` returned allowed and the paid `/self-evaluation/run` path returned HTTP 200.
7. Replaying the same real event twice returned 200 and did not increase `billing_webhook_events`.
8. Authenticated `POST /billing/cancel` set `cancel_at_period_end=true` at Stripe. Entitlement remained available for the paid period. Immediate TEST cleanup then deleted the subscription; the running Stripe CLI listener delivered the deletion and local billing became canceled.

## Failure and ordering checks

- Invalid webhook signature: HTTP 400; no state change.
- Out-of-order subscription snapshot: the handler fetched current Stripe provider state under the company lock; stale `past_due` input did not overwrite the current active state.
- Unknown event: a real Stripe TEST `checkout.session.completed` event was signed for the isolated endpoint, returned `ignored=true`, and changed no tracked table counts.
- Provider API error: an initially mismatched TEST Price produced a real Stripe resource-missing response. Profit Radar returned 503 before Customer/Subscription creation; the local fixture was cleaned. The Price reference was then corrected. Only the single TEST sandbox Price's `tax_behavior` was changed from unspecified to inclusive; no LIVE object was touched.
- Payment failure: a second authenticated application Checkout used Stripe's decline test card. The hosted page displayed the rejection, Session remained open/unpaid, no subscription ID was created or persisted, billing remained disallowed, and the paid feature remained HTTP 402. The Session was expired and the local fixture was cleaned.

## Cleanup and regression

- Both temporary users/companies were removed through the resumable account-deletion RPC path.
- Tracked local table counts matched each scenario's pre-run counts after cleanup.
- Stripe TEST subscriptions/customers created by the success scenario were deleted; the declined Session was expired.
- Disposable integration: **32 passed / 0 skipped**.
- Full Backend: **288 passed / 0 skipped** (12 Supabase SDK deprecation warnings).
- Stripe/AI/entitlement focused regression: **59 passed**.
- Python compileall, `pip check`, `pip-audit`: PASS; known vulnerabilities 0.
- Frontend TypeScript, ESLint, production build (21 routes): PASS with explicit dummy HTTPS build origins; npm audit 0.
- `git diff --check`: PASS.

No Stripe LIVE key/Price, Production webhook, Production database, Gmail send, migration, deploy, or real charge was used.
