# Profit Radar release status

## 2026-10-01 Post Financial Information Architecture checkpoint（最新）

- Phase: **Financial information architecture frozen locally / external Production gates remain**. `/results` is the Financial analysis/detail source of truth, `/financials` is a recording-only workspace, Dashboard uses a shared compact current-month summary, and Customers is customer-first. Production connection, side effects, push and deployment: **0**.
- Semantics: Dashboard and Results share `/financials/summary` and the same metric/null renderer. Normal values and `未記録・不明` states matched exactly; Financial calculation/API/JST behavior was not changed.
- Empty/mobile behavior: zero reply/risk data produces matching advice and refresh CTA without an empty Danger card. Desktop browser checks passed; the 390px isolated actual-component fixture passed eight route/state checks with horizontal overflow 0 and BottomNav overlap 0.
- Regression: Frontend Node tests **21 passed / 0 failed / 0 skipped**; TypeScript, ESLint, 27-route production build and `git diff --check` PASS.
- Reproducibility: `docs/evidence/POST_FINANCIAL_IA_CHECKPOINT_20261001.md` is included in this checkpoint. The exact commit and artifact SHA-256 are pinned by the repository-external manifest produced from the clean commit with `scripts/build_release_artifact.py`.
- Remaining owner/external gates are unchanged: legal/publication approval; hosting/domain/DNS/TLS/CORS/secret store; Google verification; Stripe LIVE preparation; worker/monitoring and recurring backups; separately approved Production deployment/smoke.

## 2026-10-01 Final local release checkpoint（最新）

- Phase: **local release checkpoint frozen / external Production gates remain**. Local startup, authenticated onboarding, Legal + Support and visible UI cleanup are included in one reviewed source boundary. Push, deploy, Production connection, Google Production OAuth, Gmail send and Stripe LIVE activity: **0**.
- Regression: disposable Auth/PostgREST integration **33 passed / 0 skipped**; Backend **344 passed / 0 skipped**; Frontend Node tests **16 passed / 0 skipped**; Python compileall, pip check/audit, TypeScript, ESLint, 27-route production build, npm audit 0 and `git diff --check` PASS.
- Commit boundary review: **463** tracked/candidate text files scanned; strong secret findings **0**; non-example env files **0**; local runtime/build/log/database/archive artifacts **0**. Ignored `.local-isolated*`, `.local-runtime/`, real env files, dependency/build directories and logs remain outside the commit.
- Reproducibility: this status and `docs/evidence/FINAL_LOCAL_RELEASE_CHECKPOINT_20261001.md` are included in the checkpoint itself. The exact commit and artifact SHA-256 are pinned by the repository-external content-addressed manifest created from the clean commit with `scripts/build_release_artifact.py`.
- Remaining owner/external gates: final legal/publication values and review; public domain/DNS/TLS/CORS/secret store; Google verification/security assessment; Stripe LIVE preparation and approved promotion; worker/monitoring installation; recurring encrypted backup operations; Production Auth evidence resolution; separately approved deployment/smoke.

## 2026-09-30 Visible UI cleanup（最新）

- Phase: **local visible UI cleanup PASS / Production side effects 0**. Existing LEGAL + SUPPORT and onboarding changes were preserved; no commit, push, deploy, Production Supabase access, Gmail send, Google OAuth consent, or Stripe action occurred.
- Plan: removed section-level faded presentation; contract/price/renewal/refund copy and all five confirmations use explicit dark text on white backgrounds. Only unavailable controls use disabled styling, and checkout/cancel each shows its concrete disabled reason. Browser-computed opacity is 1 and horizontal overflow is absent at 1280px and 390px.
- Branding/placeholders: customer-facing fixture text is `COROS WORK`; repository UI search found no `CROSS WORK`/`cross work`. Results and the legacy chart component no longer contain `グラフ表示エリア`, `表示予定`, `Chart Placeholder`, or `API接続済み`; zero-data charts show the formal financial-data empty state.
- Google UX: `/gmail/auth-url` classifies missing development/test OAuth configuration as 501, missing production configuration as 424, and provider construction failure as a redacted 502. Frontend renders distinct safe guidance for each without emitting expected failures to the Next.js issue overlay. Focused error/redaction tests **9 passed**. The running local fixture currently has OAuth values configured, so its real browser click correctly reached the independent expired-trial 402 gate instead of being misreported as missing OAuth.
- Browser proof: authenticated local pages Dashboard, Reply, Customers, Results, Settings, Plan and Mail, plus Contact and all legal/data pages were checked at 1280px and 390px. All checked routes had no horizontal overflow and no forbidden brand/development strings. Results formal empty state and Mail/Plan readable states were observed in the real browser.
- Regression: disposable real Auth/PostgREST integration **33 passed / 0 skipped**; Backend **344 passed / 0 skipped**; focused Backend **9 passed**; Frontend Node tests **16 passed / 0 skipped**; Python compileall, pip check/audit, TypeScript, ESLint, 27-route production build, npm audit 0, and `git diff --check` PASS. The build used `https://api.example.invalid` only and is not a deploy artifact.
- Changed in this cleanup: `backend/app/api/gmail.py`, `backend/tests/test_gmail_oauth_errors.py`, Plan and Mail settings pages, Results chart/summary/mapper components, `frontend/src/data/mock.ts`, `frontend/tests/visible-ui.test.mjs`, and this status record.

## 2026-09-30 Local onboarding blocker remediation（最新）

- Phase: **local browser E2E PASS / Production side effects 0**. Existing LEGAL + SUPPORT working-tree changes were preserved; no commit, push, deploy, Production Supabase access, Gmail send, or Stripe action occurred.
- Root cause: `getCurrentAppProfile()` selected the nonexistent legacy `profiles.name` column while the deployed/local canonical schema exposes `profiles.full_name`. The onboarding API and RPC committed successfully, but the failed profile refresh produced an empty `companyId`; `OnboardingGuard` then redirected `/settings/plan` back to `/onboarding`, creating a silent loop.
- Fix: load and map `full_name`; make `refreshProfile()` return the loaded profile; require the saved profile to be readable before redirecting directly to `/dashboard`; align the onboarding response type; send and persist the explicit B2B consent; add safe `/auth/me` completion state; show a user-facing failure instead of silently returning; improve the consent/disabled-submit contrast and accessibility.
- Real local browser proof: Browser -> Backend -> local Supabase on `127.0.0.1` completed twice (desktop and 390px). POST payload contained trimmed company/name and `business_use_confirmed=true`; Dashboard navigation and reload remained stable. Local DB showed exactly one matching profile and one accepted consent, authenticated direct RLS read returned one own profile, and `/auth/me` returned `onboarding_completed=true` with a company context.
- Regression: disposable real Auth/PostgREST integration **33 passed / 0 skipped**; Backend **341 passed / 0 skipped**; Frontend Node tests **12 passed / 0 skipped**; Python compileall, TypeScript, ESLint, 27-route production build, npm audit 0, and `git diff --check` PASS. Build used `https://api.example.invalid` only and is not a deploy artifact.
- Restart point: local services remain available at Frontend `http://127.0.0.1:3101`, Backend `http://127.0.0.1:8031`, Supabase `http://127.0.0.1:54421`. The synthetic onboarding fixture remains local-only for reproducibility.

## 2026-09-28 Release checkpoint freeze（最新）

- Checkpoint commit: `c0af7d5a19a001ff3cbba0e8ca8d5fe50282f5e7` (`release: freeze Profit Radar P0 remediation checkpoint`).
- Immutable source artifact: `C:\Users\closs\Documents\Codex\release-artifacts\profit-radar\profit-radar-c0af7d5a19a001ff3cbba0e8ca8d5fe50282f5e7.tar.gz`; SHA-256 `2AEC336E9582ADD1EF877F0EA6A2CE357465ED6D8AA1625A7D37B4D53BAE4537`.
- Manifest SHA-256: `118DA4F3D860EDADAB9F1D86B4C80EEA079F25F486B026FEC7C0CBECE9863A9E`; source tree was clean, archive entries 511, forbidden local/build/secret artifacts 0.
- Freeze verification: integration 32/0, Backend 318/0, frontend 8/0, TypeScript/ESLint/22-route build, Python compile/dependency audits, npm audit, staged secret scan 123/0 and diff checks PASS. Production side effects 0.
- This checkpoint is not deployment approval. Remaining external P0 starts with finalized legal/publication information, then domain/TLS/secret store and the gated provider/Production checks in `OWNER_ACTIONS.md`.

## 2026-09-28 Production P0 remediation（最新）

- Phase: **P0 code/config remediation complete; OWNER/external production actions blocked**. Production deploy, LIVE Stripe, Google submission, Gmail send and Production Supabase contact/write remain 0. Evidence: `docs/evidence/PRODUCTION_P0_REMEDIATION_20260928.md`.
- PASS: production startup rejects TEST billing, loopback/HTTP/mismatched origins and incomplete AI/provider settings; frontend publication gate rejects incomplete legal/commercial settings; clean-commit immutable artifact builder; hardened Production A/B runner; supervised worker heartbeat/backoff/shutdown; independent runtime/maintenance monitoring; encrypted scheduled backup design; isolated restore proof.
- PASS: disposable integration **32/0**, Backend **318/0** (including the separately gated loopback Production-runner exercise), compileall, pip check/audit, frontend Node tests **8/0**, TypeScript, ESLint, 22-route build, npm audit 0, diff check and candidate secret scan **380 text files / 0 findings**. The final build used an explicit non-routable HTTPS build origin; no deploy or network contact occurred.
- PARTIAL: isolated worker reached the real local API scheduler and heartbeat, but the long-lived disposable DB contained 100 synthetic connected-Gmail fixtures; those company jobs failed and are reported as `degraded`, not promoted to real Google success. Gmail send calls were 0. Existing Gmail sync/retry/lock regression remains PASS.
- BLOCKED/OWNER: public domain/TLS/secret store; Production Auth A/B runner separate approval; Google Restricted-scope verification/security assessment; Stripe LIVE objects and one-way DB promotion; external alert receiver/on-call and worker installation; final seller/legal values; encrypted off-host backup destination/key custody/retention; production deployment approval.
- Restore drill: fixed disposable source unchanged, encrypted-production-independent local logical restore PASS, 54 tables, fresh retained DB `pr_restore_e09da14aacd94cd4b19fdf2fcffba112`; no source/Production deletion.
- Next: complete the remaining OWNER actions in `OWNER_ACTIONS.md` in order, beginning with final legal/publication values. Do not replay v2.

## 2026-09-28 Production deployment readiness audit（最新）

- Verdict: **BLOCKED / NOT READY**. Production deploy/LIVE billing/Gmail send/Production DB writeは0。Evidence: `docs/evidence/PRODUCTION_DEPLOYMENT_READINESS_AUDIT_20260928.md`。
- Current local tree: branch `arc/profit-radar-release-readiness`, HEAD `435bb0ac368c32e50dda918863213b3cdbf69543`, extensive uncommitted release work. This dirty tree is not a reproducible release artifact; preserve it and do not deploy or commit without a reviewed file set.
- Fresh local gate: disposable integration **32 passed / 0 skipped**; Backend **290 passed / 0 skipped**; compileall, pip check/audit, TypeScript, ESLint, 21-route production build, npm audit 0 and diff check PASS. Build used `api.example.invalid` only and is not a deployable artifact.
- Security hygiene fix: `/auth/me` no longer has a raw exception response path; AuthProvider no longer logs raw SDK errors. Explicitly non-release old isolated/browser-save artifacts are now ignored without deletion. Candidate secret-pattern scan: **404 files / 0 findings**.
- Owner-reported Production v2/post-apply/count/restore evidence remains recorded and v2 must not be replayed. Production Auth A/B status is contradictory across existing handoffs and no attached safe execution result resolves it; current Production tenant isolation is therefore **UNVERIFIED**, while local real-Auth A/B isolation passes.
- P0 blockers: public hosting/domain/TLS/exact CORS/secret store/release artifact; Google Restricted-scope verification/security-assessment decision; Stripe LIVE configuration and DB promotion; deployed five-minute worker; external monitoring/heartbeat; final seller/legal/retention/refund disclosures; recurring backup strategy; current Production Auth/RLS evidence.
- Restart point: complete OWNER ACTIONS in the new top section, then perform a separately approved controlled deployment. **Do not start Production deploy from this checkpoint.** Next gate: `BLOCKED_BY_PRODUCTION_CONFIGURATION_AND_EXTERNAL_APPROVALS`.

## 2026-09-28 Stripe TEST E2E final gate（最新）

- Status: **PASS**. Disposable Supabase and isolated Backend only; Stripe responses were TEST (`livemode=false`). Profit Radar onboarding -> expired trial/402 -> authenticated Checkout -> hosted TEST payment -> signed webhook -> subscription persistence -> entitlement -> paid feature -> cancel-at-period-end -> listener-delivered deletion was verified.
- Duplicate real event delivery did not add a second webhook record. Invalid signature returned 400. A stale subscription event could not overwrite current provider state. A real unknown TEST event was ignored without DB change. A real provider resource error mapped to 503 before subscription creation.
- A separate hosted Checkout with Stripe's decline test card remained open/unpaid, created no subscription, granted no entitlement, and left the paid route at 402. Both success and failure fixtures were cleaned; tracked local table counts returned to their pre-run values.
- Regression: disposable integration **32 passed / 0 skipped**; full Backend **288 passed / 0 skipped**; Stripe/AI/entitlement focused **59 passed**; compileall, pip check/audit, frontend TypeScript/lint/build, npm audit 0 and diff check PASS.
- Production contacts, LIVE charge, Gmail send, migration and deploy: 0. Evidence: `docs/evidence/STRIPE_TEST_E2E_20260928.md`. Next gate: **PRODUCTION DEPLOYMENT READINESS AUDIT**; deploy itself remains prohibited without separate approval.

## 2026-09-28 Stripe TEST E2E credential gate（履歴）

- Status: **BLOCKED_BY_STRIPE_TEST_CREDENTIALS**. Read-only preflight found `STRIPE_MODE=test` and a loopback frontend origin, but `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and `STRIPE_PRICE_ID` are all absent.
- Existing application flow and guards were reviewed; no Stripe API, Checkout, webhook, charge, Gmail, migration, deploy, or Production endpoint was invoked. Production side effects: 0.
- Mock/synthetic tests were not promoted to real Stripe E2E evidence. Checkout, TEST payment, Stripe-signed webhook, provider subscription persistence, entitlement, duplicate delivery, cancellation, and provider failures remain unexecuted.
- Blocked evidence: `docs/evidence/STRIPE_TEST_E2E_20260928.md`. Resume only after the three TEST-only values are injected into an isolated backend secret source; never paste them into chat or commit them.
- 2026-09-28T05:46:52Z再確認でも3値は未設定。既存disposable Supabaseは稼働中だが、通常のBackend環境には非loopback Supabase設定があるため起動せず停止した。再開時は継承環境を使わない隔離processへloopback SupabaseとTEST Stripe値だけを注入する。
- Listener preparation checkpoint: isolated Backend is running on `http://127.0.0.1:8021`, with health/ready PASS and fixed disposable Supabase `http://127.0.0.1:54321`. The launcher clears application/provider environment, disables dotenv loading, and injects only local Supabase credentials; Stripe calls remain 0. `.local-isolated/stripe-test.env` exists with empty secret fields. Stripe CLI authentication to the owner-selected sandbox was confirmed, but listener/E2E is not started and `whsec_` is not configured.
- Stripe TEST E2E resumed: all three credentials passed presence/prefix validation without value output. The configured Price referred to a different TEST context, while the selected sandbox contained exactly one JPY 19,800 monthly Price with `tax_behavior=unspecified`; Checkout safely returned 503 before Customer/Subscription creation. That unique TEST Price was changed to `inclusive`, the ignored local Price reference was aligned, and the isolated Backend was restarted. Profit Radar onboarding, forced local trial expiry, pre-subscription paid-feature denial (402), and real application Checkout Session creation passed. Hosted Checkout is filled with Stripe TEST data and paused immediately before the consequential submit action for required operator confirmation. Production contacts remain 0.

## 2026-09-28 AI isolated real-generation final gate（最新）

- Status: **PASS**. Existing labeled disposable Supabase only (`127.0.0.1:54321`); Production contact, Gmail send, Stripe call, migration and deploy are all 0.
- The final path used a normal local Auth JWT and the real application HTTP endpoint: `/ai-judge/judge` -> tenant/entitlement checks -> prompt -> budget reservation -> OpenAI `gpt-5.6-sol` -> JSON/application validation -> `ai_usage_runs` and `ai_budget_reservations`. Non-empty validated response, token/cost/company budget, latency 6,541 ms, retry 0 and cleanup all PASS.
- Failure/guard suite **34 passed**: provider error/timeout have no automatic retry and retain unknown-cost reservation; malformed response is a marked safe fallback; Production/Live Stripe/non-loopback configuration fails closed. Log/result known-secret and JWT scan: 0 findings.
- Regression after changes: disposable integration **32 passed / 0 skipped**; full Backend **288 passed / 0 skipped**; compileall and `git diff --check` PASS. Evidence: `docs/evidence/AI_ISOLATED_REAL_GENERATION_20260928.md`.
- Initial evidence-harness attempt was not counted as PASS: real response validation completed, then local verification/cleanup code failed. The fixture was recovered through approved deletion RPCs and final rerun passed. Current isolated AI fixture companies: 0; isolated backend stopped.
- Next Gate remains **Stripe TEST E2E**, BLOCKED only on TEST secret key, webhook signing secret and approved TEST Price ID. Do not start Stripe in the AI gate.

## 2026-09-27 Docker復旧・AI isolated restart checkpoint（最新）

- Docker Desktop 4.90.0 / Engine 29.7.2 / `desktop-linux` を復旧。原因はstaleな0-byte Windows runtime socketで、Dockerを停止してruntimeディレクトリを日時付きで退避後、残留Docker processを終了して通常起動した。prune、volume/container/network削除、factory reset、再インストール、`.local-isolated`削除は行っていない。
- 既存 `profit-radar-disposable` を維持。API `127.0.0.1:54321`、DB `127.0.0.1:54322`。隔離E2E **32 passed / 0 skipped**。
- AI isolated restart **PASS**。`backend/scripts/run_isolated_ai_restart.py` は `runtime_settings.AI_PRODUCTION_REQUIRED` を設定schemaとして使い、既存 `.env` からは `OPENAI_API_KEY` だけ、`.env.owner-gate` からは宣言済みAI設定だけを読み取る。生成する `.local-isolated/ai-e2e.env` と結果JSONはgitignore対象でACLを現在ユーザー1名に制限。Production URL、非loopback Supabase、Live Stripe、非`sk_test_` keyは起動前に拒否する。
- 既存Backend process停止と専用port空きを確認後、継承設定を使わない新規processを起動。health=PASS、ready=PASS、OpenAI reply `responses.create` 1回、provider=openai。`ai_usage_runs`へinput/output tokenとoperator設定単価によるcost、`ai_budget_reservations`へcompany budgetとactual tokenを記録し、generation count=1 / cap=100を確認。isolated backendは検証後停止。Production contact=0。
- Cost記録の欠落を修正し、保守的な予約額を変更せず、成功応答の実token×operator設定単価を `ai_usage_runs.cost_usd` に記録する。focused guard/accounting tests PASS。
- Runbook準拠Full regression: integration **32 passed / 0 skipped**、全Backend **286 passed**、12件はSupabase SDK deprecation warningのみ。`git diff --check` PASS。
- 2026-09-27継続確認: `docker version` / `docker info` のServer応答、`desktop-linux`、既存DB/Auth/Kongのhealthy、loopback 54321/54322を確認後、既存 `run_local_regression.py --allow-disposable-fixtures` を再実行。integration **32 passed / 0 skipped**、全Backend **286 passed**。prune、volume/container/network削除、Supabase再初期化、production接続は0。
- 2026-09-28 dependency security remediation: `anyio==4.14.1` を、同一系列の修正版 `4.14.2` へだけ更新（4.15.xへのjumpなし）。CVE-2026-63374 / CVE-2026-64847 / CVE-2026-63349は再監査で検出0。`pip check`、`pip-audit`、compileall PASS。更新後の隔離integration **32 passed / 0 skipped**、全Backend **286 passed**、Stripe/AI safety focused **58 passed**、frontend TypeScript/lint/build、npm audit 0、`git diff --check` PASS。実AI再生成、Stripe通信、production接続、DB migration、Docker/Supabase再初期化は0。
- Stripe TEST実E2Eは `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` / `STRIPE_PRICE_ID` が未設定のため **BLOCKED**。mock成功を実E2Eへ流用せず、Live chargeは0。必要契約はJPY 19,800、monthly、interval_count=1、tax inclusive。14日trialはアプリ管理で自動課金なし。
- Vector loggingはDocker log endpointへのNetwork unreachableでrestart中。DB/Auth/APIおよび隔離E2Eに影響しないため **NON-BLOCKING ISSUE**。
- Release decision: **BLOCKED**。次gateはOWNERによるStripe TEST credentialの隔離secret設定と、実TEST checkout/Webhook/cancel E2E。Production deploy readyではない。

## 2026-09-18 release-candidate continuation (latest)

- Current local gate after financial, AI, UI, monitoring, redaction, production-config and company retry edits: target-validated disposable Supabase integration **32 passed / 0 skipped**; full Backend **280 passed / 0 skipped** (12 third-party SDK deprecation warnings). Python compileall, pip check and pip-audit PASS. Frontend TypeScript, ESLint and production build PASS (21 routes), npm audit 0; `git diff --check` PASS. The build used a dummy HTTPS origin and is not a production deploy artifact.
- UI-only Playwright fixture (CSP blocks external transport, no real Auth/DB): PC 1280px and mobile 390px dashboard, financials and error states **6/6 PASS**. Retry button was clicked and routed back to Dashboard. Screenshots: `docs/screenshots/release-20260918-{dashboard,financials,error}-{pc,390}.png`. This is not authenticated production E2E.
- Security review found older Dashboard/Results/Reply/Settings/service-layer failure paths could display or log raw exception text in the browser; those paths now use generic messages, and legacy router 503 paths no longer include raw DB exception text. The central API exception handler already redacts client responses. Focused error/maintenance tests 9 PASS and full rerun PASS. Tracked environment files include only `backend/.env.example`; scoped source/docs scan found no actual-looking Stripe/PEM credentials and no server credential variable references in frontend source. This is not a substitute for secret rotation review or a full history scan.
- Monitoring maintenance counters now include recent failed Gmail company syncs and sync runs stuck >15 minutes, with counts only in the optional HTTPS alert payload. No customer row, token, or provider exception is included. External alert destination and independent host/worker heartbeat are not configured.
- Production/staging API startup now also requires Google OAuth/scheduler and Stripe credentials, rejects HTTP OAuth callback or invalid scheduler origin, and rejects a Stripe key whose TEST/LIVE prefix conflicts with `STRIPE_MODE`. This closes the previous path where `/health` could run while core providers were unconfigured. It checks only shape/presence; actual Google/Stripe reachability and account approval remain external tests.
- Company-specific scheduled Gmail retry now uses persisted recent run states: 5→10→20→40→60-minute bounded backoff after consecutive failures, without delaying other companies or releasing `running` locks. `deferred` is reported separately from success/failure. Focused scheduler tests 7 PASS; real deployed five-minute process/restart alerting remains NOT TESTED.
- This process has no Stripe TEST credentials, OpenAI production key, Google credentials, public frontend/API URL, or monitoring receiver configured. Do not mistake local mocks or a dummy HTTPS build origin for provider E2E or a production deployment. Stripe TEST E2E, persisted production AI env, actual restart-generation, Google review, legal/domain, live billing approval and deployment remain NOT TESTED / MANUAL.
- Review 1 DATA: canonical `financial_records`/`financial_payments`, JST month boundary, version conflict, cancellation and A/B separation tested locally. Production financial write→summary replay on real customer-like rows was not performed. Review 2 SECURITY/SIDE EFFECTS: browser/raw DB exception paths redacted, backend service-role boundary and secret scan reviewed; no Gmail/Stripe/production side effect in this turn. Review 3 RELEASE: a new company tomorrow still cannot be sold to until TEST checkout/Webhook, persistent AI env/restart, public domain/HTTPS, Google verification, legal terms and monitored deployment are independently completed. Decision: **NOT READY** (no claim of zero code defects from untested external paths).
- 2026-09-18 further work: production startup now validates `OPENAI_API_KEY`, all three explicit model names, maximum USD-per-million-token rates for each, monthly token/USD and generation limits; paid generation also rejects a missing/invalid generation cap at call time. No provider key/value was written to the repository. Operator must provision persistent server-side environment values and restart-test against the approved deployment. [Official Terra pricing](https://developers.openai.com/api/docs/models/gpt-5.6-terra) was USD 2 input / 12 output per million tokens and [Sol pricing](https://developers.openai.com/api/docs/models/gpt-5.6-sol) USD 4 / 20 on 2026-09-18; Sol promotional pricing is time-limited. These are observations, not locked billing terms or operator-approved maximums. Rates/budgets remain blank in `.env.example` until owner approval; conservative maximums must be at least current provider prices and rechecked before deploy.
- Local interim checks after those edits: focused AI/runtime/financial **24 passed**, frontend TypeScript/lint/build PASS (21 routes). A plain `pytest` without disposable fixture configuration initially returned 3 failures because older AI tests relied on an implicit generation-limit default; tests now explicitly configure the test cap. Plain `pytest` also skips real local Auth/DB cases; use the target-validated disposable runner for the final 0-skip count. No production API, Stripe or Google call occurred.
- Financial deep-link now loads an authorized record even when it falls outside the first 50 `/leads` rows. Financial summary period heading distinguishes current month from user-selected dates. App-level error boundary now has explicit dark text and a keyboard-visible, clickable retry button; authenticated desktop/390px browser proof remains outstanding.
- Phase: code/UX release blockers. Preserve the dirty working tree and do not reapply v2. Owner reports production DB/Auth/Gmail E2E successes in the current mission; these are owner-provided evidence, not rerun by this agent. No Gmail send, Stripe charge, production deploy, remote migration, or commit/push in this turn.
- P0 DATA root cause confirmed in code: canonical `financial_records` are used by `/financials/summary`, but legacy `PATCH /profit-events/{id}/actual-profit` only mutated `profit_events` and ancillary logs; the two amounts could diverge. Also the summary's no-argument period defaulted to **today**, while the intended dashboard period is month-to-date. Frontend financial save already remounts `FinancialSummary` (`key={refresh}`) and API fetch uses `cache: no-store`.
- P0 DATA fix in working tree: legacy mutation now returns 409 for an authorized event and 404 across tenants, with no DB write; confirmed values remain `financial_records` via version-fenced `save_financial_record`. Backend summary defaults to JST month-to-date; UI labels match. Lead detail deep-links to its financial record; editing preserves `occurred_at`. Existing old `ActualProfitForm` now links to canonical flow instead of calling the unsafe route.
- Verification: focused Backend financial/entitlement tests 16 passed; disposable local Auth/DB integration **32 passed / 0 skipped** including 100,000→150,000 update, duplicate submit, cancellation, A/B isolation and JST month boundary; full Backend **270 passed / 0 skipped**, 12 SDK deprecation warnings. Frontend TypeScript passed at the first check; lint/build and final typecheck still pending for the latest edits. This is local proof, not a read of production financial rows.
- Next: finish production AI configuration without inventing provider prices; verify deployment/worker/monitoring/UI; run all remaining local gates; perform three review passes and update release decision. Current sale decision remains NOT READY pending external Stripe TEST E2E, production configuration, Google review/legal/domain/deploy and any code defects found in later review.

Earlier entries below are historical checkpoints.

Updated: 2026-09-17 JST. Repository: `C:\Users\closs\ProfitRadar_App`, branch `arc/profit-radar-release-readiness`, HEAD `435bb0ac368c32e50dda918863213b3cdbf69543`. The working tree already contains extensive uncommitted release work; preserve it. Do not add saved HTML, `.local-isolated-*`, or raw attachment backups to a commit.

## Latest authoritative checkpoint (supersedes historical pre-apply notes below)

- Owner reports production v2 migration on project `zszmetqhksthduoxfvac` **applied with COMMIT success**; read-only post-apply `FINAL=PASS`; all 20 existing-table row counts matched pre/post; and production logical backup restore proof `PASS`. This is owner-provided evidence in this conversation, **not independently rerun by this agent**. Backup timestamp, artifact path and SHA256 were not provided here; do not invent them.
- Current phase: production Authenticated A/B E2E preparation. `backend/scripts/run_production_auth_e2e.py` is a new project-pinned, separately approved, production-only runner. It has **not** been run on production; owner approval remains required immediately before that write-bearing E2E. It never invokes `test_p0_supabase_isolation.py`, Gmail, Stripe, Cron or Deploy.
- PASS (local only): runner guard tests and a disposable GoTrue/JWT tenant/cleanup exercise. The default local DB predates v2 canonical onboarding ACL/owner column, so the local exercise uses a clearly marked local fixture registration and relaxed local-only owner-column cleanup; the production runner keeps canonical RPC and exact owner checks. This is not production Auth proof.
- Local command `PR_AUTH_E2E_LOCAL_TEST=ALLOW_DISPOSABLE_LOCAL` with `pytest -q backend/tests/test_production_auth_e2e.py`: **5 passed / 0 skipped**. A/B real local GoTrue login, own profile and API lists/details, cross-tenant deny, service-role customer/event writes, exact-ID cleanup, and unchanged four-table counts passed. The local registration/owner-column cleanup substitutions above mean this is a partial path proof only. Separate v2 synthetic-DB canonical JWT validator remains prior evidence, not this run. Initial local trial failures exposed schema differences; their eight uniquely marked synthetic company/Auth fixtures were removed in one validated local transaction and final counts were zero. No production rows were changed.
- Full local regression after wiring the new fixture flag into the already target-validated disposable runner: integration **31 passed / 0 skipped**, all Backend **268 passed / 0 skipped** (12 Supabase SDK deprecation warnings). `compileall` and `git diff --check` passed. A deliberately wrong production confirmation flag was rejected without remote access. This session never ran the production E2E.
- PARTIAL/BLOCKED: live Auth login/profile, A/B tenant isolation, normal read, service-role fixture write, and post-cleanup count equality await separately approved production execution. Google/Stripe E2E, legal, domain, monitoring destination and deployment remain distinct sale gates.
- Next: obtain separate approval for the production Auth E2E runner, execute once against the pinned project, inspect its safe result and cleanup status, then proceed to the remaining external gates. Never rerun a failed production fixture automatically; stop for operator review.

Historical notes below describe the pre-apply period and are retained for audit only; their statements that v2/backup are pending are no longer current.

## Current phase

Remote schema forward v2: pre-apply gate passed per owner-provided live read-only result. Local validation and migration handoff are prepared. **Migration has not been applied.** Waiting for confirmation of the target project, completed restorable backup, stopped writers and explicit approval of the exact v2 SQL. Production Gmail sends, Stripe charges, OAuth confirmation and deployment require separate approval at their action boundaries.

2026-09-17 backup checkpoint: owner confirmed target project `zszmetqhksthduoxfvac`, no scheduled Free-plan backup/recovery method, and API/worker/cron writers stopped or not deployed. Owner expressly **did not approve v2 apply**. Manual production `pg_dump` plus disposable restore is now the required next gate. No production database password or PostgreSQL connection URI is available to this execution environment; the service-role key is not a PostgreSQL backup credential. Thus the production archive has **not** been created, and no production restore proof exists.

## PASS

- Owner reported Remote Final Gate `FINAL=PASS`; policy, tables, owner column, global sync runs, profile identity, billing config exact; ACL and legacy onboarding are `KNOWN_REMEDIABLE` by v2.
- Owner reported Local Final Gate `76 passed / 0 errors` at the prior checkpoint. This is prior evidence, not a new run in this session.
- `docs/remote_schema_forward_oracle_snapshot_20260916.json` SHA256 `1819D3032106DF74FC7709CC0C88EE6D0C0992F941BF74A16617A65515E751E9` was verified locally. v2/preflight/capture hashes are pinned in their tests.
- Existing v2 local validator previously completed first apply, replay, rollback matrix, and local GoTrue JWT checks; details in `docs/REMOTE_SCHEMA_FORWARD_DRIFT_PATCH.md`.

## FAIL

- None newly confirmed. Do not infer that prior test results prove production operation.

## PARTIAL

- Production backup/restore proof is pending. The disposable local restore drill passed.
- Remote post-apply verification and real Auth, Gmail, Stripe test E2E: pending. Mock/provider substitute successes do not count as real E2E.
- Legal terms, seller information, public domain, production secret store, monitoring destination: owner decisions and independent verification pending.

## BLOCKED

- Production migration application: backup completion, target/project confirmation, writer stop, and explicit final approval are required immediately before execution.
- Public sale: production migration, live configuration, external E2E, Google approval, legal review, and deploy remain unfinished.

## Next work

1. Run all local quality gates and repair any failures without discarding existing changes.
2. Prepare read-only post-apply SQL and backup/recovery checklist; verify exact SQL and hashes.
3. When all safe preparation is complete, request one concrete migration approval. Keep Gmail sends, charges and deploy on separate approval boundaries.

## Commands/results this session

- `git status --short`, `git branch --show-current`, `git rev-parse HEAD`: branch/HEAD above, substantial user working-tree changes preserved.
- Read `SALES_RELEASE_FINAL.md`, `SALES_IMPLEMENTATION_CONTINUATION.md`, `OWNER_ACTIONS.md`, `RELEASE_RUNBOOK.md`, `REMOTE_SCHEMA_FORWARD_REVIEW.md`; several old historical sections conflict with latest checkpoint, so this status and current source hashes govern the next action.
- Quality commands and results will be appended below as they complete.
- `backend/venv/Scripts/python.exe -m pytest -q -rs --tb=short`: 206 passed / 55 skipped (no local fixture env); skip is not counted as pass.
- `backend/venv/Scripts/python.exe -m compileall -q app tests scripts`: PASS.
- `backend/venv/Scripts/python.exe -m pip check`: PASS. `pip_audit --progress-spinner off`: no known vulnerabilities.
- `frontend npx tsc --noEmit`, `npm run lint`, `npm run build`: PASS, 21 routes. `npm audit --audit-level=low`: 0 vulnerabilities. Build used `https://api.example.invalid` as a temporary nonproduction origin; not a deploy artifact.
- Docker disposable project container labels/engine available. `backend/scripts/run_local_regression.py --allow-disposable-fixtures`: integration 31 passed / 0 skipped; initial full suite 233 passed / 28 skipped because runner omitted `FINAL_GATE_LOCAL_TEST`.
- Dedicated final gate suite: 76 passed / 0 skipped, local disposable DB only.
- Fixed regression runner to set `FINAL_GATE_LOCAL_TEST` only after disposable target validation. Full rerun in progress.
- Corrected full rerun: integration **31 passed / 0 skipped**; full Backend **261 passed / 0 skipped**, 6 SDK deprecation warnings. No external provider calls. The earlier 206/55 and 233/28 rows are historical interim runs.
- Current v2 validator, disposable DB `pr_forward_f068bd3af2644726a6884d6468378482`: first apply/rollback, commit/replay, row/ACL preservation, conflict rollbacks **27**, identity rollbacks **10**, local GoTrue JWT checks PASS. `billing_mode=test`, `remote_access=false`.
- Added read-only `supabase/remote_schema_forward_post_apply.sql`. Executed against that v2 disposable DB: `FINAL=PASS` for table/function/RLS/effective table and column ACL/billing/global sync checks. Existing data counts, exact canonical body/policy oracle, and full production E2E remain separate post-apply checks.
- Local restore rehearsal in progress; source/target are the fixed disposable Supabase only.
- Local restore rehearsal PASS: source unchanged, 54 public/auth tables, restored metadata/ACL/row counts matched in new `pr_restore_ae68fa599edd4fbd81fe518c4e3f3fb1`; local archive retained at `/tmp/pr_restore_ae68fa599edd4fbd81fe518c4e3f3fb1/synthetic.dump`. This is not production DR proof.
- Frontend after legal copy edits: `npx tsc --noEmit`, `npm run lint`, `npm run build` PASS; `npm audit --audit-level=low` 0 vulnerabilities. Node tests 5 passed / 0 skipped.
- Legal copy review found unsupported Microsoft/Outlook claims and an unspecified free plan. The initial Gmail-only and explicit 14-day trial wording now matches the current product. Seller identity, retention, refund/withdrawal, and full legal review remain owner tasks.
- `supabase/remote_schema_forward_row_counts.sql`: read-only exact counts for the 20 currently present remote target tables. Save its pre-apply output and compare the same query immediately post-apply. No customer row content.

## Changed files this session

- `docs/RELEASE_STATUS.md` (new). Prior dirty files were not discarded.
- `backend/scripts/run_local_regression.py`: pass explicit final-gate fixture flag to the already validated disposable local test run.
- `docs/REMOTE_SCHEMA_FORWARD_REVIEW.md`: latest pre-apply state and future command target corrected from historical v1 to v2.
- `supabase/remote_schema_forward_post_apply.sql`: new read-only post-apply metadata check; internal trigger distinguished from service RPC.
- `supabase/remote_schema_forward_row_counts.sql`: read-only aggregate data preservation check.
- `frontend/src/app/terms/page.tsx`, `frontend/src/app/privacy/page.tsx`: initial Gmail-only and trial wording corrected.
- `docs/PRODUCTION_MIGRATION_HANDOFF.md`: concrete backup, writer stop, transaction, verification, and recovery boundaries.
- `docs/OWNER_ACTIONS.md`, `docs/RELEASE_RUNBOOK.md`: current checkpoint inserted above historical Docker/v1 instructions.

## Production operations not performed

No remote migration, production data change, Gmail send, Stripe charge, OAuth completion, cron/deploy, commit or push.

## Resume point

Read this file and verify current `git status`/migration SHA256. Continue the local quality checks, then backup/recovery and post-apply preparation. Do not restart the pre-apply audit unless the schema has drifted or the captured evidence is invalidated.

### Manual backup/restore boundary (latest)

- `backend/scripts/backup_production_restore.py` is an interactive, local-only `pg_dump`/`pg_restore` helper. It pins the approved project identity, prompts for the production PostgreSQL password without echo or command-line/environment exposure on the host, uses TLS certificate and hostname verification, writes a custom-format archive outside the repository with restricted ACL, then restores into a new random database in the labeled disposable local Supabase container. It prints only completion time, artifact path, archive SHA256, and PASS/FAIL. A completed archive is retained even if restore fails; v2 remains prohibited until PASS and separate explicit apply approval.
- Local rehearsal of its restore path using an earlier **synthetic** archive: PASS into a fresh `pr_prodrestore_*` database. This is not production backup proof. Source connection and live `pg_dump` are untested because the PostgreSQL password is unavailable here.
- Offline script tests: 2 passed / 0 skipped; Python compile PASS; restricted backup directory setup PASS; `git diff --check` PASS. No remote connection, dump, or migration was attempted.
- Next step requiring the owner: run the helper on this computer in an interactive local terminal, entering the PostgreSQL database password **there only**, not in chat. If direct `db.<project>.supabase.co` is inaccessible, use the Supabase session-pooler host with user `postgres.<project>` and port 5432. Inspect its four-field result locally; provide only those four fields. Do not apply v2 until the production restore result is PASS and separate explicit approval is given.

- Production Auth E2E 2026-09-17T07:45:16+00:00: PASS; cleanup=PASS; pre/post count delta: companies=0, profiles=0, customers=0, profit_events=0. Dedicated A/B users only; no Gmail, Stripe, Cron, or Deploy.
# 2026-09-29 Legal + contact/admin implementation (current)

- Phase: **implementation complete; final regression in progress; Production remains blocked**.
- PASS: COROS WORK B2B disclosure, seven-day card-on-file trial contract, explicit renewal/refund/privacy confirmations, legal/cancellation/retention/Google-data pages, public contact intake, isolated support-admin authorization, reply idempotency/provider fail-closed design, support retention maintenance and new RLS/service-only schema.
- PASS (disposable local only): `20260928153027_legal_support_admin.sql` applied in one transaction; real Auth/PostgREST integration **33 passed / 0 skipped**, including browser denial for all six new internal tables. Production DB contact/write: 0.
- PARTIAL / external: actual seller identity, public domain/support address, verified email sender/provider, support-admin Auth UUID, independent legal review and Production migration/deploy approval are not configured. The frontend publication gate and Backend production startup fail closed until configured.
- Evidence: `docs/evidence/LEGAL_SUPPORT_IMPLEMENTATION_20260929.md`.
- Regression checkpoint: real local Auth/PostgREST integration **33 passed / 0 skipped**; Backend **329 passed / 0 skipped** before two final focused admin/email test files; frontend **8 passed / 0 skipped**, TypeScript/ESLint/27-route Production build PASS, npm audit 0, compileall/pip check/pip-audit PASS. A minimal disposable database migration+guarded rollback drill completed cleanly (6 new tables → 0). Final diff/secret scan and the updated Backend total follow in the last checkpoint below.
- Resume: run the final focused tests and diff/secret scan, then review the owner-only values above. Do not deploy or apply the migration without separate approval.

## 2026-09-30 Local startup repair + Legal/Support final regression (latest)

- Phase: **local code/migration gate PASS; next owner/external actions remain blocked**. Branch `arc/profit-radar-release-readiness`, base HEAD `31573c4da79b218022e7e4c40ac53fcba61bc5bc`; existing uncommitted work preserved. Production contact/write, Gmail send, Stripe LIVE, deploy, commit and push: 0.
- Root cause: the release-candidate unique Gmail-message index ran before the later repair migration added its columns. Existing remote/isolated baselines already contained the legacy columns and masked the clean-build defect. An additive transaction-wrapped `202609060001_reply_logs_gmail_bridge.sql` now supplies and validates the two nullable text columns before the first consumer; existing exact schemas are a no-op.
- Fresh local chain: PASS on `profit-radar-local`, versions `202607020001`, bridge `202609060001`, normal migrations through `202609110001`, and Legal/Support `20260928153027`. The two remote-only forward repairs remain unchanged and are excluded only from fresh local staging. Reapply of the bridge is idempotent; Gmail unique index count remains 1.
- Startup: `scripts/start-profit-radar.ps1` PASS/idempotent with secret-free output; Supabase 54421, Backend 8031, Frontend 3101 READY. Health/readiness/login/register/onboarding HTTP 200. Production-like APP_ENV fails closed. Stop script targeted only owned processes/project and preserved its volume (1 before/after); restart PASS.
- Regression: disposable real Auth/PostgREST integration **33 passed / 0 skipped**; Backend **339 passed / 0 skipped**; Frontend **8 passed / 0 skipped**; TypeScript, ESLint, 27-route production build, compileall and pip check PASS. `pip-audit` and `npm audit`: 0 vulnerabilities after `oauthlib 4.0.0`, `PyJWT 2.14.0`, and transitive `brace-expansion` security updates. Candidate secret scan **460 files / 0 findings**; `git diff --check` PASS.
- Legal/Support: B2B disclosure, seven-day card-required trial, checkout confirmations, contact/admin authorization, reply idempotency/provider failure handling, disclosure workflow, retention, RLS and guarded rollback are locally PASS. Seller identity/domain/support sender/admin UUID/SMTP, independent legal review and Production migration/deploy remain owner/external gates.
- Evidence: `docs/evidence/LEGAL_SUPPORT_IMPLEMENTATION_20260929.md`, `docs/evidence/LOCAL_STARTUP_REPAIR_20260930.md`. Resume at `OWNER_ACTIONS.md`; do not deploy or apply the Legal/Support migration without separate approval.
