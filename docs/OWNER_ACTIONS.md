# 本人操作と外部環境

## 2026-09-28 P0 remediation後のOWNER actions（最新・順序固定）

1. **法務・公開情報**: `frontend/.env.example` の販売者名/住所/電話/問い合わせ、返金、解約、削除、保持、国外移転、管轄、発効日を専門家と確定し、3つのapprovalをtrueにする。placeholderのまま`APP_ENV=production`は起動しない。
2. **domain/hosting/secret store**: 公開Frontend/API domain、DNS/TLS、reverse proxy、CORSを決め、`deploy/production-env.schema.json`どおりにBackend/Frontend/Backupの分離secretを登録する。値をchat/Git/unit fileへ置かない。
3. **Google**: `GOOGLE_OAUTH_RELEASE_PACKAGE.md`に従いProduction専用project/domain/branding/2 scopesを登録し、Restricted verificationとsecurity assessmentの結果を保存する。Codexは申請しない。
4. **Stripe LIVE**: `STRIPE_LIVE_RELEASE_PACKAGE.md`に従いLIVE Price/key/webhook/tax/invoice/refundを準備する。実chargeなしのreadiness確認と、writer停止後のDB live promotionはそれぞれ別承認。
5. **監視/worker**: HTTPS alert receiverと当番を決め、worker/maintenance/runtime-probe unitをinstall後、通知到達と外部missed-heartbeatを確認する。repositoryからは未登録。
6. **backup**: encrypted off-host保存先、age key custody、保持/RPO/RTOを承認し、backup timerをenableする。最初のProduction artifact restoreはdisposable環境で証拠化する。
7. **release artifact — DONE 2026-09-28**: checkpoint `c0af7d5a19a001ff3cbba0e8ca8d5fe50282f5e7`からrepository外artifactを生成し、SHA-256とmanifestを`RELEASE_STATUS.md`および`docs/evidence/RELEASE_CHECKPOINT_20260928.md`へ記録済み。push/deployは未実施。
8. **Production Auth A/B**: 上記基盤後に`run_production_auth_e2e.py`の別承認を出す。runnerはproject ref固定、実在A/B foreign IDs、直接UPDATE/DELETE、危険RPC、owner、API、cleanup/count deltaを検証する。本節は実行承認ではない。
9. **Deploy**: 前8項目とrollback windowを確認した後だけ別途承認する。v2は再適用しない。LIVE charge/Gmail sendはさらに別承認。

## 2026-09-28 Production deployment readiness — current owner actions

Current verdict: **BLOCKED / NOT READY**. AI isolated real-generation and Stripe TEST E2E are PASS, but they do not authorize Production deploy or LIVE billing. Full evidence: `docs/evidence/PRODUCTION_DEPLOYMENT_READINESS_AUDIT_20260928.md`.

1. **Production platform and release artifact** — choose frontend/API hosting, public domains, DNS/TLS, exact CORS and server secret store; create a reviewed immutable release commit/artifact from the current dirty tree. Required before deploy and first customer.
2. **Production Auth/RLS evidence** — the handoff documents conflict about whether the separately gated A/B runner ran. Attach its safe PASS/cleanup/count-delta output or separately approve one controlled run against the pinned project. Never reapply v2. Required before public API access.
3. **Google production approval** — in Google Cloud, verify domain/branding/support/home/privacy URLs and obtain the applicable Sensitive/Restricted scope approval. Because `gmail.readonly` data is processed on a server, confirm and complete the required independent security assessment unless Google records an applicable exception. Required before external Gmail users.
4. **Stripe LIVE** — create/verify the JPY 19,800 monthly tax-inclusive LIVE Price, restricted/secret key, webhook destination and subscription events; decide tax, invoice/receipt and refund operations. Record an approval reference and follow the stopped-writer one-way database promotion. Do not paste keys or perform a real charge during preparation. Required before paid signup.
5. **Worker and monitoring** — install/enable the five-minute sync worker and maintenance timer on the selected host; test the HTTPS alert receiver, independent missed-heartbeat monitor and responder escalation. Required before public signup.
6. **Legal/publication** — obtain independent review and provide the actual seller legal name, governing court/effective date, public domain and support address. Address and telephone use the approved “disclose without delay on request” flow; do not hard-code personal details. Confirm actual processors/international transfers. Keep all three publication approvals false until complete. Product terms are seven-day card-on-file trial, JPY 19,800 tax-inclusive monthly auto-renewal, cancellation any time, no customer-convenience/prorated refund, normal data deletion/anonymization within 30 days and backup rotation within 90 days.
7. **Support operations** — create a dedicated Supabase Auth administrator, place only its UUID in backend-only `SUPPORT_ADMIN_USER_IDS`, generate `CONTACT_RATE_LIMIT_SECRET`, choose the public `SUPPORT_EMAIL`, verify its production domain/sender and provision the SMTP provider secrets. Confirm `SUPPORT_RETENTION_DAYS` with counsel. Never grant admin through `profiles.role`.
7. **Backup/recovery** — the reported one-time logical restore proof is retained, but Free-plan Supabase has no scheduled project backup. Approve a recurring encrypted logical backup destination/schedule, retention, credential rotation, recovery objectives and disposable restore cadence. Required before public signup.
8. **Controlled deployment/smoke** — after 1–7, approve deployment and non-customer Production smoke covering registration, Gmail, AI, controlled mail, finance, LIVE billing, cancellation and deletion. This is a later consequential gate, not authorized now.

## 2026-09-28 Stripe TEST E2E final gate（最新）

Status: **PASS**. TEST Checkout/payment, signed webhook, subscription/entitlement, duplicate delivery, cancellation, real decline, invalid signature, out-of-order/unknown events, provider error and cleanup were verified against the disposable local Supabase. Evidence: `docs/evidence/STRIPE_TEST_E2E_20260928.md`.

No additional Stripe TEST credential action is required for this gate. Do not promote the ignored local TEST values to deployment, do not enable LIVE, and do not reuse the listener signing secret as a deployed webhook secret. The next owner approval boundary is production deployment preparation and its external domain/legal/Google/monitoring checks; deployment and Stripe LIVE remain separately prohibited.

## 2026-09-28 Stripe TEST E2E credential gate（履歴）

Status: **BLOCKED_BY_STRIPE_TEST_CREDENTIALS**。Stripe API呼出、Checkout、TEST決済、Webhook、解約はまだ0件。Evidence: `docs/evidence/STRIPE_TEST_E2E_20260928.md`。

1. Stripe DashboardをTEST modeにし、Developers / API keysから`sk_test_`で始まるTEST secret keyを取得する。既存または新規TEST Productに、JPY 19,800・monthly・interval count 1・tax inclusiveのPriceを用意し、その`price_` IDを確認する。
2. 値をchatやGitへ貼らず、backend専用の隔離secret storeまたはgitignore済み `.local-isolated/stripe-test.env` に `STRIPE_SECRET_KEY` と `STRIPE_PRICE_ID` として設定する。`STRIPE_MODE=test`を維持し、frontend変数へ入れない。
3. Stripe CLIをTEST accountへloginし、隔離backendの `http://127.0.0.1:<port>/billing/webhook` へforwardするlistenerを起動する。表示された`whsec_`を同じsecret sourceの `STRIPE_WEBHOOK_SECRET` に設定し、値を送らず「設定完了」とだけ連絡する。

再開時はPrice APIの`livemode=false`と契約条件を最初に検証する。条件不一致、LIVE key/Price、非loopback DB/backend、Production webhookを検出したら外部副作用前に停止する。

## 2026-09-28 AI isolated real-generation final gate

DONE: real OpenAI generation through authenticated Profit Radar `/ai-judge/judge`, application validation, usage/token/cost/company budget persistence, retry=0, failure handling, secret scan, cleanup, integration 32/0 and Backend 288/0. Evidence: `docs/evidence/AI_ISOLATED_REAL_GENERATION_20260928.md`.

ACTION REQUIRED: AI gateにはなし。次の唯一のP0 external blockerはStripe TESTの `STRIPE_SECRET_KEY` (`sk_test_`)、`STRIPE_WEBHOOK_SECRET` (`whsec_`)、承認済み `STRIPE_PRICE_ID` (`price_`)。値をchat/Git/Frontendへ出さない。

NEXT GATE: Stripe TEST E2E。今回開始していない。

## 2026-09-27 P0再開に必要なOWNER操作（最新）

### DONE

- Docker Desktop / Engineと既存 `profit-radar-disposable` は非破壊で復旧。volume/container/network、Supabaseデータ、`.local-isolated` は削除・再初期化していない。
- 隔離Supabase E2Eは再実行で32 passed / 0 skipped、Backend全体は286 passed。
- AI isolated restartはloopback Supabaseだけを使う新規processでhealth/ready、OpenAI reply 1回、usage token/cost、company budget、generation limitの記録までPASS。Production接続は0。最小1生成を超える不要な再実行はしない。
- Dependency security: `anyio` は4.14.1で検出されたCVE-2026-63374 / CVE-2026-64847 / CVE-2026-63349を解消するため4.14.2へ最小更新。`pip check` / `pip-audit` / compileall、隔離E2E 32件、Backend 286件、Stripe/AI safety 58件がPASS。追加OWNER操作なし。
- 本人報告済みのProduction V2 / post-apply / Authenticated E2E / Google OAuth / Gmail read・send / AI reply generationは完了扱い。V2、Production Auth E2E、Gmail送信を再実行しない。

### ACTION REQUIRED

Stripe TEST E2Eはcredential未設定のためBLOCKED。コードで回避せず、OWNERはsecret storeまたは隔離process環境へ次のTEST値だけを設定する。値をchat、Git、Frontend、スクリーンショットへ記録しない。

- TEST secret key: `STRIPE_SECRET_KEY`（`sk_test_`のみ）
- Webhook signing secret: `STRIPE_WEBHOOK_SECRET`（`whsec_`）
- TEST Price ID: `STRIPE_PRICE_ID`（`price_`）
- Webhook endpoint: `/billing/webhook`
- Success URL: `<FRONTEND_URL>/settings/plan?checkout=complete`
- Cancel URL: `<FRONTEND_URL>/settings/plan?checkout=cancelled`

PriceはJPY 19,800、月次、interval_count=1、税込（tax_behavior=inclusive）であることをAPI応答から検証する。Checkoutはカード登録時0円、Stripe subscriptionの7日trial、終了時自動課金、月次自動更新である。既存TEST Priceの存在は再利用可否や新規作成を仮定しない。Credential投入後にcheckout→TEST payment method→署名Webhook→DB trialing subscription→entitlement→重複Webhook→cancel→cancellation webhookを隔離環境だけで実行する。Live key / Live chargeは禁止。

### EXTERNAL MANUAL

- Production secret storeへ同じ承認済みAI model/rate/budget設定とAPI keyを保存し、deploy時に値を表示せず再起動確認する。ローカル隔離PASSをproduction secret storeの証明にはしない。
- Google公開審査、公開domain/HTTPS、販売者・問い合わせ情報、利用条件・Privacyの法務レビュー、監視通知先/当番、production deployは別Gate。

### OBSOLETE

- 以下の履歴に残る「V2未適用」「Production Authenticated E2E未実施」「Gmail E2E未実施」「Docker未導入/25 skipped」「AI再起動後の新規生成未実施」は現在状態では失効。監査履歴としてのみ保持する。

Vector loggingはDocker log endpointへのNetwork unreachableでrestart中だが、DB/Auth/APIと隔離E2Eには影響しない非P0項目。Stripe TEST gateを先に完了する。

## 2026-09-18 販売直前の未実施事項（履歴・上記最新状態と矛盾する記述はOBSOLETE）

- 持続する本番secret storeにAI provider key、3 model名と検証済み最大単価、会社別月token/USD/生成回数上限を設定する。OpenAI公式の[Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra)と[Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol)価格を設定直前に再確認し、上限・採算を承認する。PowerShell一時環境変数は本番設定ではない。再起動後の新規AI生成は未実施。
- Stripe TESTのbackend-only key、TEST Price、署名付きWebhookを隔離環境に設定し、trial→checkout→TEST決済→重複/順序逆転/支払失敗→解約を検証する。この作業環境にStripe credentialsは無い。Live key/実課金は別承認まで禁止。
- 公開domain、HTTPS frontend/backend、販売者・問い合わせ情報、返金/保持/解約条件、法務レビュー、監視通知先と当番を確定する。Googleの[OAuthポリシー](https://developers.google.com/identity/protocols/oauth2/policies)は検証済みdomain上の公開homepageと利用条件/Privacy導線を求める。[Gmail scope一覧](https://developers.google.com/workspace/gmail/api/auth/scopes)では `gmail.readonly` はRestricted、`gmail.send` はSensitive。Restricted scopeの[検証要件](https://support.google.com/cloud/answer/13464321?hl=en)と、サーバーで対象データを保存する場合のsecurity assessment要否をGoogle Consoleの実状態で確認する。Testingの成功を一般公開承認とみなさない。
- production API/worker/maintenance timer、監視通知と独立した死活監視を別承認後に配置する。本番 `/health`・`/ready`、5分同期、失敗通知、復旧当番の確認は未実施。v2 migrationを再適用しない。

## 2026-09-17 最新（以下の旧Docker/skip記述より優先）

最新 2026-09-17: 対象project `zszmetqhksthduoxfvac` のv2適用COMMIT、post-apply FINAL=PASS、旧20テーブル件数一致、本番backup復元PASSを本人が報告。以下の「v2未適用」は過去の記録であり、再適用しない。次の本人操作は **production Authenticated E2Eの別承認**。`backend/scripts/run_production_auth_e2e.py` は専用A/B test user/tenantを作成・削除するため、承認前に本番実行しない。最新状態は `RELEASE_STATUS.md`。

隔離Dockerは利用可能。v2 full validator、ローカルGoTrue/JWT、integration31/0、Backend261/0、restore演習を再実行済み。以下はpre-apply時点の履歴。

法務・Google/Stripeテスト・domain・本番設定と公開はmigrationとは別の後続Gate。実送信、実課金、deployは承認前に行わない。

## 以下は過去時点の記録
2026-09-14。最新Gate: SALES_RELEASE_FINAL.md。過去版はhistory/OWNER_ACTIONS_before_20260911.md。
未完コードはSALES_IMPLEMENTATION_CONTINUATION.mdで管理し、本人待ちへ付け替えない。

## 隔離DB
Docker engineとWSL/仮想化の準備が必要。CLI2.117.0だけではSupabaseは起動できない。管理者操作・再起動は本人判断。
準備後、repo rootで powershell -File scripts/start-isolated-tests.ps1 -RunTests。
専用loopback54321、明示許可とURL照合、架空Authユーザー・通常login JWTを自動準備する設計。JWT手作業取得・チャット共有不要。
現在25 tests skipped。全件分類はRELEASE_SKIP_CLASSIFICATION.md。baseline/migration/正規JWT/RPCを実行した証拠はない。通信/SQL失敗はskipへ変換して成功扱いしない。
本番や共有DBを隔離先に指定しない。既存.local-isolatedの削除を自動承認しない。

## GoogleとToken
OAuth設定・外部提供審査状態を本人が確認する。gmail.readonlyはRestricted、gmail.sendはSensitive。テスト設定を一般販売可能と仮定しない。
鍵はsecret storeで保管・backup。旧平文tokenを新コードは拒否するため、移行/rotation/reconnect/refresh/revokeの隔離演習前に反映しない。
backendから python -m scripts.migrate_local_gmail_tokens はローカルdry-run既定。--applyも専用隔離限定。
本番token移行は別承認と復旧計画が必要。secret/token/JWT/メール本文をログや報告へ出さない。
実Google E2Eでは本人管理の送受信先と内容を別途確認し、送信直前の承認を得る。

## Stripe
現設定はtest既定。production切替gateは実装済み・未有効化。月額JPY19,800、month/interval_count1、税込inclusive Priceをテスト環境に用意する。
secret/key/webhookはBackendだけへ注入。7日trialと自動更新条件はStripe TESTで検証し、Productionへは別承認で切り替える。
実Stripe testの重複/順序逆転/支払失敗/解約/再契約/UNKNOWNが未実証。
live切替はRELEASE_RUNBOOKの設定・DB approval一致と実test E2E、別承認が必要。test履歴があるDBの安易な昇格は拒否する。live呼出/実課金禁止を維持。

## 運営・契約で本人が決めること
- 販売主体、所在地、問い合わせ先、ドメイン、HTTPS、公開URL。
- 保持日数、解約後の閲覧期限、返金/削除/backup保持の条件。未確定内容を契約として公開しない。
- AI会社別月token/USD上限と許可modelの保守的最大単価。設定例の空欄はfail closed。原価の実測ではない。
- ACCOUNT_AUDIT_RETENTION_DAYSと保持削除の承認。日数は削除完了から起算、未完jobは期限削除しない。
- 障害通知の受け先、当番、backup復元演習日。maintenanceはreadonly既定で外部通知接続は未証明。
- Google外部提供条件と法務レビュー。販売準備中表示は維持。

## 承認が必要な境界
本番DB適用/削除、実メール、実課金、公開、cron登録、審査提出は未実行。別承認前に進めない。
schema/ACL（列権限・継承・関数owner/EXECUTE・RLS含む）を安全に退避し、backup復元可能性を確認する。
SQL audit出力だけではcommit後の完全復元を保証できない。新規migration002が既適用ならforward差分が必要。
手順はRELEASE_RUNBOOK.md、operator復旧はOPERATOR_RECOVERY.md。
