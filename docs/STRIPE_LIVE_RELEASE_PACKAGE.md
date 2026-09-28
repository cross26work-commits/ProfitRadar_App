# Stripe LIVE readiness package

No LIVE API call, object creation, webhook change or charge is authorized by this document. Stripe TEST E2E is separately PASS.

## OWNER setup

1. In LIVE mode create/approve a JPY 19,800 recurring monthly Price with `interval_count=1` and `tax_behavior=inclusive`. Decide Stripe Tax, invoice/receipt wording and qualified-invoice operation with the accountant/legal reviewer.
2. Store a restricted `rk_live_` or `sk_live_` key, LIVE Price ID and a new LIVE endpoint signing secret for `POST <BACKEND_URL>/billing/webhook` in the Production secret store. Subscribe only to required `customer.subscription.*` events. Never reuse TEST objects or the Stripe CLI `whsec_`.
3. Decide and publish refund/cancellation support. The current product cancels at period end through its authenticated `/billing/cancel` path; a Stripe Customer Portal is not required by the application and must not be enabled without a separate URL/return-flow/security review.

## Technical promotion gate

- Production startup requires `APP_ENV=production`, `STRIPE_MODE=live`, `BILLING_LIVE_APPROVED=true`, an approval reference, HTTPS/approved origins and a LIVE key prefix. TEST mode or `sk_test_` fails closed.
- The database remains `billing_mode=test` until the separately approved, stopped-writer `promote_billing_live` RPC confirms no TEST billing history and records the same approval reference. Do not edit the row manually.
- The first controlled LIVE readiness check may retrieve the configured Price and validate `livemode=true`, currency, amount, interval and inclusive tax, but must not create a Customer, Checkout, Subscription or charge. A real paid subscription needs its own explicit approval.
- Signed webhook processing fetches current provider state, binds it to the persisted authenticated Checkout and uses an event-idempotent database RPC. Invalid signatures and out-of-order snapshots cannot grant entitlement.

## Rollback

Before any customer charge, failure means stop public signup, disable the deployed webhook endpoint, restore the previous application artifact and keep billing unavailable. The DB live promotion is intentionally one-way; do not revert it to TEST or mix modes. Correct configuration with a reviewed forward change.
