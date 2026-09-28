# Profit Radar AI isolated real-generation evidence

- Timestamp (UTC): `2026-09-28T03:41:38+00:00`
- Commit SHA: `435bb0ac368c32e50dda918863213b3cdbf69543`
- Working tree: dirty release-candidate tree; existing changes preserved
- Environment: `isolated-test`
- Supabase target: loopback `127.0.0.1:54321`, Docker project `profit-radar-disposable`
- Provider: OpenAI
- Model: `gpt-5.6-sol`
- Scenario: authenticated JWT -> Profit Radar `POST /ai-judge/judge` -> prompt construction -> budget reservation -> provider response -> JSON/application validation -> usage/cost persistence
- Final request: PASS
- Non-empty validated response: PASS
- HTTP latency: 6,541 ms
- Recorded provider-processing elapsed time: 6,356 ms
- Automatic retry count: 0
- Usage input/output tokens recorded: PASS
- Cost recorded from actual usage and operator maximum rates: PASS
- Company budget reservation finalized: PASS
- Generation count/cap: 1 / 100
- Fixture cleanup and pre/post tracked-table counts: PASS
- Remaining `AI restart %` fixture companies: 0
- Isolated backend stopped after verification: PASS
- Gmail send calls: 0
- Stripe calls: 0
- Production contacts/side effects: 0
- Known-secret/JWT scan of backend log and result evidence: 0 findings
- Result: **PASS**

## Isolation controls

The runner accepts only `APP_ENV=test`, loopback HTTP Supabase/frontend URLs, Stripe TEST mode, and an optional `sk_test_` key. The child process receives local Supabase credentials discovered from the existing labeled disposable project; it does not inherit the repository environment. Production Supabase URLs, non-loopback URLs, Live Stripe mode/keys, multiline values, and missing AI limits/models are rejected before backend startup. No Gmail, billing, scheduler, migration, deploy, or production route is invoked.

## Failure handling

Focused fault-injection/guard suite: **34 passed**. It verifies provider timeout and provider error produce a generic 503, make one provider attempt only, retain the conservative reservation, and do not persist provider exception text. A malformed provider judgement produces an explicitly marked safe fallback (`AI_PROVIDER_INVALID_RESPONSE`) without returning malformed text. Missing context/config, budget exhaustion, invalid generation limit, Production URL, and Live Stripe settings fail closed before paid generation or external side effects.

## Regression

- Disposable Supabase integration: **32 passed / 0 skipped**
- Full Backend: **288 passed / 0 skipped**
- Python compileall: PASS
- `git diff --check`: PASS
- Third-party Supabase SDK deprecation warnings: 12; no test failure

## Execution note

The first attempt reached and validated a real provider response but the evidence harness then failed on an undefined local variable and attempted a direct internal-table cleanup that the intentionally least-privileged `service_role` rejected. It was not counted as PASS. The harness was corrected to use the resumable account-deletion RPCs, all marked isolated fixtures were removed, and the final run above completed end-to-end. Thus this work session may have incurred two small TEST AI provider calls; only the final successful run is represented by the one-generation counters above. No secret, prompt body, response body, email, JWT, API key, or customer row is stored in this evidence.

Provider request ID is not exposed by the current application result and was not added merely for evidence.
