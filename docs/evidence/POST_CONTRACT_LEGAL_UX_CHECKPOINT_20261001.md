# Post Contract / Legal UX checkpoint — 2026-10-01 JST

## Scope

- Branch: `arc/profit-radar-release-readiness`.
- Starting checkpoint: `becbddf2252f24fca56c98382d961aa185c45bb5`.
- This checkpoint contains only the reviewed Contract-state presentation, context-aware Legal navigation, Legal contrast remediation and their frontend/UI regression tests.
- Billing/Stripe API contracts, subscription persistence, database schema, RLS, Auth authorization, Gmail and legal-policy body text were not changed.
- Production connections, Production side effects, Gmail send, Stripe activity, Google Production OAuth, push and deployment: **0**.

## Verified behavior

- The read-only local database state was `trial_pending` for two companies, with zero Stripe subscription references, zero checkout attempts and zero checkout consents. No customer rows or secrets were displayed.
- `trial_pending`/checkout-not-started no longer renders an exact first-billing timestamp. It explains that the seven-day free period starts after card registration and that the billing timestamp is not yet confirmed.
- `trialing` renders a confirmed first-billing timestamp only when supplied; `active` renders a renewal timestamp only when supplied. Failed, incomplete, paused, canceled and unknown states are mapped separately and fail safely when a required timestamp is absent.
- Terms, Privacy and Cancellation/Refund links from Plan carry the allowlisted `/settings/plan` return target. Signup carries `/register`. External, protocol-relative, query-mutated and otherwise unknown return targets are rejected.
- Authenticated direct Legal access falls back to Settings; unauthenticated direct access falls back to Signup.
- Cancellation/Refund headings, body, contact and return links have explicit readable colors on the white card. Axe color-contrast checks reported zero violations at desktop and 390px.
- Customer-facing frontend source contains no legacy `cross work` brand text; display branding remains `COROS WORK`.

## Browser and regression evidence

- Real local authenticated browser: Plan showed `カード登録待ち`, the unconfirmed billing explanation and no exact first-billing timestamp. Terms, Privacy and Cancellation/Refund returned to Plan.
- Real local 390px browser: Plan and Cancellation/Refund had no horizontal overflow; the Legal page had no BottomNav overlap.
- Isolated actual-component fixture: desktop and 390px Plan states, all three Legal return paths, unauthenticated fallback, external-return rejection and contrast passed. It prohibited external transport and did not contact Auth, DB or Stripe.
- Frontend Node tests: **26 passed / 0 failed / 0 skipped**.
- TypeScript, ESLint, 27-route production build and `git diff --check`: **PASS**.

## Artifact identity

This evidence is included in the checkpoint commit. The exact commit and source-artifact SHA-256 are recorded by the repository-external manifest generated from the clean commit by `scripts/build_release_artifact.py`.

## External gates remaining

This UI checkpoint is not Production deployment approval. Final owner/legal publication approval, public hosting/domain/DNS/TLS/CORS/secret store, Google verification/security assessment, Stripe LIVE preparation and approved promotion, worker/monitoring installation, recurring encrypted backup operation and separately approved Production deployment/smoke remain external gates.
