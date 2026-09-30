# Profit Radar 公開・復旧・運営手順

## 2026-09-30 通常ローカル起動

1. Docker Desktop / Engineを通常起動する。prune、volume削除、Supabase resetは不要。
2. repository rootから `./scripts/start-profit-radar.ps1` を実行する。固定CLIが通常migrationを `.local-runtime` へbyte-for-byte stagingし、remote専用V1/V2だけを除外する。Production URL、Production-like `APP_ENV`、Stripe LIVE keyは起動前に拒否される。
3. READY URLはSupabase `127.0.0.1:54421`、Backend `127.0.0.1:8031`、Frontend `127.0.0.1:3101`。`/health`、`/ready`、`/login`、`/register`、`/onboarding`を確認する。CLI keyは表示しない。
4. 停止は `./scripts/stop-profit-radar.ps1`。PID command lineを照合し、`profit-radar-local`だけを停止する。volumeは保持され、`profit-radar-disposable`等の別projectは操作しない。
5. clean-build ordering fixは `202609060001_reply_logs_gmail_bridge.sql`。remote専用V1/V2をfresh chainへ混ぜたり、既存migrationを編集したりしない。詳細Evidenceは `docs/evidence/LOCAL_STARTUP_REPAIR_20260930.md`。

## 2026-09-28 P0 remediation運用（最新）

- Production環境契約は `PRODUCTION_ENVIRONMENT.md` と `deploy/production-env.schema.json`。BackendはProduction TEST billing/localhost/HTTP/origin不一致を拒否し、readinessはDB billing modeも確認する。Frontendは`APP_ENV=production`時に法務/販売情報をfail-closedにする。
- clean reviewed commitからのみ `scripts/build_release_artifact.py --repo <repo> --output-dir <repo外>` を実行し、commit/hash manifestをchange ticketへ保存する。現在のdirty tree自体はartifactではない。
- services: `profit-radar-api`, `profit-radar-frontend`, `profit-radar-sync`, `profit-radar-maintenance`, `profit-radar-runtime-probe`; repositoryのunitはtemplateであり未install。workerはloopback `/health` `/ready`、batch transport backoff、SIGTERM停止を持つ。DB running lockは時間だけで解除しない。
- Monitoring契約: `MONITORING_INCIDENT_RUNBOOK.md` と `deploy/monitoring-alerts.yaml`。receiver未設定ならnotify jobは失敗させ、external missed-heartbeatを必須とする。
- Backup: `BACKUP_RECOVERY_RUNBOOK.md`。`scheduled_backup.py`はpg_dump→age→catalog verification→atomic artifact、retentionは自身のartifact名だけ。`profit-radar-backup.timer`はstorage/key/retention承認前にenableしない。
- Legal/Google/Stripe: `commercial-disclosure`, `privacy`, `terms`, `GOOGLE_OAUTH_RELEASE_PACKAGE.md`, `STRIPE_LIVE_RELEASE_PACKAGE.md`。owner値、審査、LIVE objectは外部Gateであり今回未実施。
- Current local proof: integration 32/0, Backend 318/0, frontend 8/0 + type/lint/22-route build, dependency audits, restore drill and candidate secret scan 380/0 PASS. Production contact/deploy/provider action 0。詳細は`RELEASE_STATUS.md`先頭とP0 evidence。

## 2026-09-28 Production readiness hold point

The current authoritative decision is `BLOCKED / NOT READY`; see `docs/evidence/PRODUCTION_DEPLOYMENT_READINESS_AUDIT_20260928.md` and the first section of `RELEASE_STATUS.md`. AI isolated generation and Stripe TEST E2E are PASS, but Production deployment is not authorized.

Do not deploy until all current P0 owner actions are evidenced: immutable reviewed release artifact; selected public frontend/API hosting with DNS/TLS/CORS/secret store; current Production Auth A/B proof; Google Restricted-scope approval/security-assessment decision; Stripe LIVE objects/webhook and approved one-way billing promotion; enabled worker/maintenance/alert heartbeat; finalized legal/contact/retention/refund disclosures; and recurring backup/restore operations. V2 is already owner-reported as applied and must not be replayed.

The final controlled deployment must use the exact reviewed artifact, inject secrets only from the server-side store, check `/health` and `/ready`, start the worker/maintenance supervision, verify alert delivery, and run only the approved non-customer smoke. Roll back the application artifact on health/readiness failure; do not reverse the committed v2 schema or delete Production rows. Production deploy, LIVE charge and Gmail send still require their own explicit approvals.

## 2026-09-28 AI isolated real-generation Gate（最新）

- Evidenceは `docs/evidence/AI_ISOLATED_REAL_GENERATION_20260928.md`。隔離Supabaseのラベル/loopbackを確認してから `backend/scripts/run_isolated_ai_restart.py` を使用する。
- ランナーは正規JWTでBackend `/ai-judge/judge` を通し、実Provider応答、application validation、usage/cost/budget、cleanupとpre/post countを検証する。Production URL・Live Stripe・非loopbackは起動前拒否。Gmail/Stripe/migration/deployを呼ばない。
- 実Provider生成は費用を伴うため、既存PASSを理由なく再実行しない。失敗時は自動再試行せず、結果不明の予約を保持し、隔離fixtureだけをoperator review後に回収する。
- 2026-09-28実績: final generation PASS、failure/guard 34、integration 32/0、Backend 288/0。後続のStripe TEST E2Eも同日にPASSしたため、次はProduction Deployment Readiness Audit。AI gateのPASSを理由なく再生成しない。

## 2026-09-27 P0 Stripe/AI隔離手順（現行）

1. Dockerは`desktop-linux`、既存projectは`profit-radar-disposable`、APIは`http://127.0.0.1:54321`、DBは`127.0.0.1:54322`であることを確認する。prune、`down -v`、volume削除、`.local-isolated`再作成、Production link/db pushは禁止。
2. AI isolated restartはrepo rootから `backend/venv/Scripts/python.exe backend/scripts/run_isolated_ai_restart.py`。ランナーは非loopback Supabase、Production URL、Live Stripe、非`sk_test_` keyを事前拒否し、repo `.env`全体をchildへ読み込まない。`.local-isolated/ai-e2e.env`はgitignore対象かつlocal ACL制限対象。secret、prompt、生成本文は標準出力へ出さない。
3. 合格条件は既存Backend停止→新規isolated process→`/health`→`/ready`→provider-backed reply 1回→`ai_usage_runs` token/cost→`ai_budget_reservations` actual token/company cap→generation limitの順にすべてPASSし、検証後processが停止すること。2026-09-27実績はPASS、generation_calls=1、Production contact=0。
4. Stripe TESTは `STRIPE_SECRET_KEY=sk_test_*`、`STRIPE_WEBHOOK_SECRET=whsec_*`、`STRIPE_PRICE_ID=price_*` を隔離secret storeからのみ注入する。`STRIPE_MODE=test`を固定。Price API応答がJPY 19,800、month、interval_count=1、tax_behavior=inclusiveでなければ停止する。現在の契約はカード登録時0円、Stripe subscriptionの7日trial、終了時自動課金、月次自動更新である。Checkout直前の5確認と保存済み同意証跡を確認する。

## Legal/support Production gate (2026-09-29)

1. `20260928153027_legal_support_admin.sql` は既存migrationを改変せず適用する。事前backup、writer停止、transaction適用、6テーブル/RLS/ACL/RPC、7日billing関数、既存件数不変を確認する。未適用のままアプリをdeployしない。
2. Frontend publicationは seller legal name、公開support address、terms date/court/processor disclosures、30/90日、address/phone request disclosureと3 approval flagが揃うまでfail closed。
3. Backend startupは admin UUID allowlist、contact HMAC secret、support retention、approved sender/domain、SMTP secretがないProductionを拒否する。値はserver secret storeだけへ置く。
4. `/admin/support` は通常tenant roleでは認可されない。専用adminで一覧/開示請求/notes/audit/replyをsmoke testし、通常userのUI直打ちとAPIが403であることを確認する。
5. Maintenanceで未対応件数とunknown/sending replyを監視し、明示承認されたretention runだけが完了済みsupport recordを削除する。provider outcome unknownを自動再送しない。
5. Webhookは`/billing/webhook`、successは`<FRONTEND_URL>/settings/plan?checkout=complete`、cancelは`<FRONTEND_URL>/settings/plan?checkout=cancelled`。credential投入後にcheckout→TEST payment→署名Webhook→DB subscription→entitlement→duplicate webhook→cancel→cancellation webhookを実施する。Live key / Live charge / Production接続は禁止。
6. 回帰は`backend/venv/Scripts/python.exe backend/scripts/run_local_regression.py --allow-disposable-fixtures`。2026-09-28 Stripe E2E後の実績はintegration 32/0 skipped、全Backend 288 passed。
7. Vector loggingのDocker endpoint `Network unreachable`はDB/Auth/API E2Eへ影響しない非P0。Stripe/AI gate後に別途調査し、P0合格を偽装するため設定を緩めない。
8. Stripe TEST E2Eは `start_isolated_stripe_backend.py`、`prepare_isolated_stripe_e2e.py`、`verify_isolated_stripe_e2e.py`、`verify_isolated_stripe_failure.py` を使う。CLI 1.52.0のlistenerは `--events customer.subscription.created,customer.subscription.updated,customer.subscription.deleted` を指定する。listener停止中に発生済みのTESTイベントは決済を繰り返さず、Stripe TESTから取得した実イベントを同じ署名検証endpointへ一度だけ復旧投入する。
9. 完了後はTEST subscription/customerを削除し、未払いSessionをexpireし、account-deletion RPCでlocal fixtureを削除する。tracked table countsをpre-runへ戻す。listener signing secretとSession URLは `.local-isolated` 外へ出さず、deploymentへ転用しない。

## 2026-09-18 Release Candidate handoff（現行）

- 本人報告ではv2本番適用、post-apply、既存件数、backup復元、Authenticated A/B E2E、Gmailのテスト用E2Eが成功済み。V1/V2再適用・既存E2E案件への追加送信はしない。記録は `RELEASE_STATUS.md` を優先。
- AIはhost/secret storeで `OPENAI_API_KEY`、3つの `OPENAI_MODEL_*`、`AI_MODEL_MAX_RATES_JSON`、`AI_COMPANY_MONTHLY_TOKENS`、`AI_COMPANY_MONTHLY_USD`、`AI_MONTHLY_GENERATION_LIMIT` を永続設定する。値はFrontendに置かない。本番起動は欠落・未知model・不正範囲を拒否する。再起動後の実生成を未実施の間、AI本番GateをPASSにしない。
- 2026-09-18に確認したOpenAI公式価格は[Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra)入力2/出力12 USD、[Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol)入力4/出力20 USD（各100万token）。Sol価格は期間限定と明記されている。`AI_MODEL_MAX_RATES_JSON` は請求価格そのものではなく保守的な最大予約単価で、運営者が最新単価以上を再確認して設定する。会社別月token/USD/生成回数の上限は契約・採算判断後に承認する。空欄のまま本番起動しない。
- `scripts.maintenance` は直近15分の会社別Gmail同期失敗と15分超のrunningも件数で確認する。`--notify` は承認されたHTTPS通知先だけ。API `/health` と `/ready`、workerプロセス、maintenance timer、通知先の到達性と独立heartbeatを公開前に確認する。worker自身のログだけではホスト停止を検知できない。
- 定期同期は接続中の会社ごとに前回の連続失敗を参照し、5分から最大60分まで指数的に再試行を遅らせる。他社は継続し、レスポンスの `deferred` 件数で確認する。`running` のままの会社は時間だけで解錠・再実行しない。15分超はmaintenance通知から運営者が `OPERATOR_RECOVERY.md` に従って状態確認する。
- Stripe TEST E2Eは2026-09-28に隔離環境でPASS。Checkout→TEST payment→署名Webhook→subscription/entitlement→重複/順序逆転/invalid/unknown/provider error→解約、および別Checkoutの実declineとcleanupを確認した。Evidenceは `docs/evidence/STRIPE_TEST_E2E_20260928.md`。Live設定・実課金は別承認まで禁止。
- 2026-09-28: dependency security gateで `anyio` を4.14.1から4.14.2へ最小更新。更新後は `pip check`、`pip-audit`（既知脆弱性0）、compileall、隔離integration 32件、全Backend 286件、Stripe/AI safety 58件を確認。再現時も4.15.x等へ無関係なjumpをせず、`backend/requirements.txt` のpinとvenvを同時に更新して全回帰する。
- UIの架空fixture PC/390px確認は実Auth/DB/Google/Stripeの合格証拠ではない。スクリーンショットは `docs/screenshots/release-20260918-*`。本番URL/DNS/HTTPS、法務最終確認、Google公開審査とmonitoring当番が確定するまで販売ページの準備中表示を維持する。

## 2026-09-17 最新

現在の唯一の再開位置は `RELEASE_STATUS.md`。2026-09-17に本人は project `zszmetqhksthduoxfvac` へのv2 COMMIT成功、post-apply FINAL=PASS、既存20テーブル件数一致、本番backup復元PASSを報告した。v2を再適用しない。次の境界は production Authenticated A/B E2E の別承認であり、`backend/scripts/run_production_auth_e2e.py` は承認前に実行しない。以下の旧pre-apply/Docker不足/skip数/v1記述は履歴であって現行操作指示ではない。

適用後は `supabase/remote_schema_forward_post_apply.sql` と同じ `supabase/remote_schema_forward_row_counts.sql` の適用前後結果を確認。Post-apply metadata PASSだけで実AuthやGoogle/Stripe E2Eを合格にしない。

## 以下は過去時点の記録
## 2026-09-15 更新（以下の旧環境記述より優先）

remoteは未接続・未適用。現在は適用禁止。承認、preflight、backup、適用後確認をREMOTE_SCHEMA_FORWARD_REVIEW.mdで管理する。
最新Backend212 passed/0 skipped、integration31 passed/0 skipped。Docker/WSLは導入済みで旧「環境不足」記述は履歴。
新規forward一本のみを対象とし、過去migration編集/再適用/db push/履歴repairを行わない。
Forward validator 10 conflict rollbacks、billing=test。restore演習54 public/auth tables PASS、ただし本番DR全体の証明ではない。

Frontend production設定:
- BACKEND_ORIGIN: rewrite用HTTPS origin。URLにuserinfo/secret/queryを含めない。
- NEXT_PUBLIC_API_BASE_URL: BrowserとServer API双方のHTTPS絶対origin。相対/backend-apiやloopbackは本番で使用不可。
- developmentのみBackend既定127.0.0.1:8000。本番は未設定/不正URLならbuildを停止する。
- 両値を本番build時と起動時に一致させ、CORSを確認。NEXT_PUBLIC値はbundleへ固定される。
- 検証ではapi.example.invalidを使用し実通信していない。生成.nextをそのまま本番公開しない。

新規forwardのcommit候補と除外はREMOTE_SCHEMA_FORWARD_REVIEW.md。commit/pushは今回実行禁止。

## 従来手順（矛盾時は上記最新記録を優先）

2026-09-14。**未公開 / CODE COMPLETE・EXTERNAL REQUIRED**。適用承認ではない。
最新Gate: SALES_RELEASE_FINAL.md。再開位置: SALES_IMPLEMENTATION_CONTINUATION.md。
旧版はhistory/RELEASE_RUNBOOK_before_20260911.mdへ退避した。

## 1. ローカル回帰
backendから:
- venv/Scripts/python.exe -m pytest -q
- venv/Scripts/python.exe -m compileall -q app tests scripts
- venv/Scripts/python.exe -m pip check
- venv/Scripts/python.exe -m pip_audit --progress-spinner off
frontendから:
- npx tsc --noEmit
- npm run lint
- npm run build
- npm audit
repo rootから:
- git -c core.safecrlf=false diff --check

178 passed /25 skipped。全件分類はRELEASE_SKIP_CLASSIFICATION.md。外部処理代替、SQL構文検査は実DB/Google/Stripe合格ではない。収集失敗・通信障害・skipを成功にしない。

## 2. 隔離DB/Auth
本人がDocker/WSL/仮想化を準備後、repo rootで powershell -File scripts/start-isolated-tests.ps1 -RunTests。
baseline/migrationのbootstrapコードは存在するが未実行。既存.local-isolatedを無断削除しない。production link/db pushは禁止。
loopback54321・URL一致・P0_ALLOW_FIXTURE_WRITES=CREATE_DISPOSABLE_FIXTURESを確認。秘密値はプロセス内のみ。
fixtureは管理APIで架空ユーザー作成→通常loginJWT。A/B正規と越境を両方確認。外部メール/AIは代替。
SET ROLEと正規JWTは別の検証。restore演習はまだ実証していない。

## 3. UI
frontendで node tests/ui/serve.mjs → http://127.0.0.1:3190。
これは実client componentの架空API fixture。CSP connect-src none、実Auth迂回を本番へ追加しない。
PC/390pxの11画面と主要fixture操作はdocs/screenshots。全状態組合せの目視と実Auth E2Eは別途確認。
実環境では登録→接続→初回/差分→案件→Draft保存/復元→確認送信→UNKNOWN照合→成果→申込/解約を別E2Eで検証。

## 4. 同期・運用
初回30日、page100、history差分、pending IDs/page、500 detail/run。既知eventだけでなく新着/SENT起点も対象。
内部worker: backend/scripts/sync_worker.py、約300秒、専用scheduler secret、Browser JWT不要。
deploy/profit-radar-sync.serviceとmaintenance service/timerはテンプレート。まだ登録・起動しない。
実行記録はgmail_company_sync_runs。gmail_sync_runs旧tableと混同しない。安全なstatus APIだけをFrontendへ返す。
会社ごとの失敗分離、ロック、backoffはコードと代替テスト。実稼働・通知・復元の証明は未完。

## 5. UNKNOWN/復旧/削除
OPERATOR_RECOVERY.mdを操作仕様として使用する。
- 送信UNKNOWNは自動再送しない。固定Message-ID/SENT/From/To/件名を照合し、未一致なら維持。
- lockは単純な時間経過で解除しない。全writer停止、owner/目的/処理状態を確認し、operator/ticketを記録。
- provider復旧RPCはservice-only。AIはレビュー済みにしても予約予算を返さない。Gmail revokeは本人によるGoogle側解除確認とconnection ID/status一致が必要。
- account deletionはprovider→DB→Auth。pendingを完了表示しない。再開は既存job経由。
- audit保持期間は完了日起算。readonly maintenanceと期限到来後の承認済みretentionを区別する。
- CLIは--expected-url一致・既定dry-run。勝手な外部処理や本番cleanupをしない。

## 6. 設定/外部Gate
.env.exampleは例のみ。APP_ENV/HTTPS/CORS/Service Role/鍵はfail closed。
旧平文token移行リハーサル前に新コードを本番反映しない。
AI最大単価・月token/USD上限は空欄のまま生成不可。usageは取得応答分、unknown予約は保持する。
Stripeはtest既定。production切替gateは実装済み、無効のまま。下記の別承認と実test E2Eが必要。試用終了自動課金なし。
Google外部審査、ドメイン、法務/販売者/連絡先/保持/返金条件はOWNER_ACTIONS.md。

## 7. Migration/公開
1. 対象環境を特定、readonly auditでschema/ACL/関数/index/RLSを照合。顧客行は取り込まない。
2. 202609100002は未適用想定で編集済み。既適用環境では新forward migrationを用意する。新005〜008も今回未適用。
3. 未知object/同名不一致では停止。変更前schema・全ACL・RLS・関数ownerと検証済みbackupを用意。
4. 隔離適用・復元演習PASS後、本人承認してから本番transaction適用。失敗時rollbackを確認。
5. commit後復旧は別操作。audit SQLだけで完全復元とはしない。新しい証跡を消すDROP禁止。
6. A/BJWT、RPC、件数、health/ready、Google/Stripe testを確認。監視通知を試験し、本番切替承認後のみ公開。
7. 初期3社は設定支援担当が毎日同期失敗/UNKNOWN/契約/削除pendingを確認する。手動担当の存在を未完コードの代わりにしない。

## 8. Stripe production gate（今回有効化禁止）
実装: app/core/billing_mode.py、202609110001_billing_production_gate.sql。
1. 実Stripe test E2E、契約表示/法務、バックアップを完了し、live切替の別承認を記録する。
2. 読み取りでbilling_runtime_config、Checkout/Webhook履歴、契約参照を確認する。test履歴があるDBの自動昇格は拒否される。履歴を削除して通過させず、分離した本番DBの構築/移行を別途レビューする。
3. 全旧新API/workerを停止。DB migration適用を別承認後、service-only promote_billing_live(p_approval_ref, p_workers_stopped=true)を対象DBで実行する。一般ユーザーから実行不可。approval refは非秘密の変更管理番号。
4. APP_ENV=production、STRIPE_MODE=live、BILLING_LIVE_APPROVED=true、BILLING_LIVE_APPROVAL_REFをDBと一致させ、FRONTEND_URLはHTTPSのoriginとする。key/Price/webhookはsecret storeから注入し、出力しない。
5. DB mode・key prefix・provider livemode・画面expected_mode一致を確認。不一致はfail closed。test画面の古い申込要求をlive処理へ転用しない。
6. 復旧時はまず停止。live履歴ができた後のtestへ単純巻戻しは禁止。providerの契約とDBを照合して承認済み復旧を行う。DB昇格は一方向であり汎用rollback RPCは提供しない。
今回使用したのは合成値/代替providerのみ。実live key取得・live request・課金なし。
公式根拠（2026-09-11確認）: https://docs.stripe.com/keys 、 https://docs.stripe.com/testing 、 https://docs.stripe.com/webhooks

## 9. 専用Docker restore演習
対象はsupabase_db_profit-radar-disposableのみ。実顧客データを入れない。Docker context overrideを解除し、ローカルcontext/label/54322が一致することを確認する。
隔離baseline/migration/fixture準備後、API/worker等すべてのwriterを停止し、backendから:

```powershell
venv/Scripts/python.exe -m scripts.restore_isolated --allow-disposable-fixtures --workers-stopped
```

新しいランダムpr_restore_* DBだけにrestoreする。sourceをDROPしない。public/auth/extensionsのdump、schema/ACL/RLS/関数/制約/列権限とtable件数、source不変を照合する。内容行の一致・Storage・global role・全Supabase災害復旧は証明しない。
source不変/restore一致が崩れたらFAILとして停止。新DBとcontainer内archiveをレビュー用に保持する。出力された正確な対象を確認し、不要になったfixture DB/archiveだけを別承認で片付ける。一括DROPや広いパス削除をしない。
今回Docker不足でrestore_verified=false、安全に停止。単体testのcommand代替成功を実演習PASSにしない。

## 10. Monitoring通知/停止検知
scripts/maintenance.pyは既定読み取り。--notifyはMONITORING_WEBHOOK_URLへのopt-in HTTPS通知。deploy/profit-radar-maintenance-notify.conf.exampleをテンプレートとする。登録/送信は未実施。
通知payloadは固定eventと4つの件数のみ。メール、token、例外本文、顧客行を含めない。redirect拒否、timeout/非2xxは失敗終了。
本人が通知先と当番を確定後、隔離で到達確認・失敗時exit・欠落時の独立heartbeat監視を検証する。worker自身だけではホスト停止を通知できないため外部の死活監視が必須。
通知失敗・UNKNOWN・削除pendingの運用はOPERATOR_RECOVERY.md。単純な時間切れでlockを解放しない。
## 履歴: 2026-09-15 remote forward v2 — exact定義未提供時（現在は失効）

**追加read-only確認必要 / v2 CODE INCOMPLETE / remote適用禁止。**
HEAD 0ecc42c9c95ecc9a6af9c6f8d2bc5852c8c543e3 と今回の未コミット差分を検証対象とする。
過去migrationは変更していない。v1を先に適用しない。

- 新規 `202609150001_remote_schema_forward_v2.sql` は未完成のfail-closed草案。checkoutを含む11内部テーブルを扱うが、最初のidentity gateで必ず例外になる。適用用完成品ではない。
- ユーザー提供のlegacy/canonicalは本文要約のみ。正確なpg_get_functiondef、引数名、戻り型が未提供であり、完全一致allowlistを捏造しない。
- Backendは認証済み本人IDを使い `/onboarding → onboard_user` を呼ぶ。FrontendはこのBackend API経由。canonical RPCの正規利用を勝手に置換しない。
- checkoutは既存migrationどおり4列、company PK/FK、RLS、service_role SELECT/INSERT/UPDATEのみ。未知列/policy/browser列grant/追加indexは拒否。
- rls_auto_enable/ensure_rlsは変更しない。イベントトリガー関数と公開業務RPCを区別する。
- preflightはSELECTのみ。checkoutの構造とACLを別評価し、onboardingはexact identity未確定と表示する。

### 今回の実行証拠
- checkout-only v2: disposable DB `pr_forward_f85212d946c147028de02110ed9ea83d` で作成、再適用、service INSERT、schema/行不変、4不整合rollback PASS。**v2全体の適用成功ではない。**
- Backend全体188 passed /27 skipped。integration内訳4 target guard passed /27 real Auth/DB skipped。
- skipは今回の実行プロセスにP0_SUPABASE_TEST_URL等を設定していないため。Docker自体の不存在を意味しない。過去の31/0や212/0を今回v2の証拠に流用しない。
- SQL構文/UTF-8とv2 default validatorのDB未接続拒否をテスト追加。compileall / pip check PASS。
- Frontend Node5 tests、tsc、lint、production build PASS、npm audit 0。buildは仮HTTPS originのローカル検証用で公開不可。
- 正規JWTでのlegacy拒否/canonical成功、既知remote相当v2 commit/replay、関数競合ケースは**未実装・未検証**。exact definitions確定後のコード残件であり、外部待ちだけとして完了扱いしない。

### 再開と適用前後チェック
1. 保存済みの両onboarding関数全文・引数名・戻り型・owner/config/ACLを受領する。秘密鍵/JWT/顧客行は不要。エージェントによるremote接続は禁止のまま。
2. 完全一致の旧状態と修正後状態をpinし、未知body/overload/owner/security/canonical差分を拒否する。既知legacyだけALTER/最小ACL修正し、canonicalは保持する。
3. 今の無条件停止gateを正式identity検査へ置き換え、remote相当fixtureで成功/再実行/既存行維持、拒否ケースと正規JWTを全検証する。
4. v2フルvalidator/integrationをskipなしで実行し、backup/復元根拠・対象DB・適用承認を人間が確認する。現在実行可能なremote適用コマンドは提示しない。
5. 将来COMMIT成功後は11table/14追加RPC/既存onboarding ACL/canonical不変/trigger/index/RLS/旧件数/billing=testを確認。失敗したtransaction rollbackとcommit後backup復旧を区別する。

今回remote接続・SQL Editor・db push・commit/push・メール送信・Stripe課金は実施していない。
.local-isolated-*は変更せずcommit対象外。checkout検証用新規DBは証跡として保持する。
## 2026-09-15 exact evidence受領後 v2完了（最新・過去の未提供判定を上書き）

今回のforwardコード準備: **最終checkpoint候補 / remote適用可能（技術的事前判定）**。2026-09-15にユーザーから追加read-only証跡を受領: public.companies.owner_user_id は data_type=uuid、udt_name=uuid、is_nullable=YES、column_default=auth.uid()、is_identity=NO、is_generated=NEVER。owner_user_id prerequisite確認待ちは解消。エージェントはremoteを再照会していない。migrationと既存列は変更せず、preflightはdefault/identity/generatedも表示するよう補完した。
**実行権限は別: remote適用・commit/pushは禁止のまま。** checkpoint commitは対象を限定すれば技術的に可だが、明示承認後のみ。適用直前の差分再確認・backup/復元手段・作業窓・適用承認、および適用後検証はexternal gateとして残る。販売全体のGoogle/Stripe/法務/本番公開Gateは今回解除しない。
直前のローカル証拠はBackend216/0 skipped、integration31/0 skipped、v2 conflict rollback13+9件、正規JWT検証とFrontend各Gate PASS。今回migration/runtimeコードは未変更のため、これらは前回実行結果として保持する。
remote接続/適用、SQL Editor、db push、commit/push、Gmail送信、Stripe chargeは一切実行していない。販売全体の実環境Gateとは別判定。

### 安全化とidentity
入力: docs/remote_onboarding_functiondefs_20260915_exact.txt（ユーザー取得のexact定義）。
onboard_userはprosrc本文と引数名/型/戻り型/owner/postgres・PLpgSQL・SECURITY DEFINER・config・ACL・overload数を検査する。
CRLF/LFだけ正規化し、本文の空白等は許容拡張しない。旧config+NULL ACL、または再実行用の既知hardening後config+限定ACLのみ許可。
一致したlegacyにのみALTER search_path=pg_catalog,pg_temp、PUBLIC/anon/authenticated EXECUTE REVOKE、service_role EXECUTE GRANT。
本文/戻り値は置換しない。Backend /onboardingは検証済みJWT本人IDをp_user_idへ導出し、FrontendはBackend経由。
canonical create_company_and_profileはexact本文・引数・uuid戻り型・owner・security・config・ACLを検査するだけで変更しない。
継承込み実効EXECUTEを変更後に再検査する。不明な差分はtransaction全体をrollback。
legacyの並行登録を新規ロック実装へ置換する作業ではない。既存一意制約とtransactionは保持され、競合時の安全なDB拒否は引き続き必要。

### 検証
- v2 full validator: fresh rollback、remote相当旧schema→commit、replay、既存行/無関係ACL/ canonical定義・ACL不変 PASS。
- 構造/権限conflict rollback13件（owner_user_id型違いを含む）、onboarding identity conflict rollback9件 PASS。
- v2専用PostgREST + 実ローカルGoTrue発行JWT: anon/auth legacy 42501拒否・行不変、canonical登録/owner profile作成、再登録拒否・行不変、service既存登録取得と新規登録、内部table直接SELECT拒否 PASS。
- 既存ローカルSupabaseでintegration31 passed/0 skipped（4対象ガード+27実Auth/DB）。Backend216 passed/0 skipped。6 SDK非推奨警告あり。
- 上記既存DB全回帰とv2専用DBの追加JWT検証は別の証拠。外部Gmail/Stripeはテスト代替であり実provider合格ではない。
- Frontend Node5 tests、tsc、lint、production build PASS、npm audit 0。compileall/pip check PASS。
- 厳密UTF-8、元日本語literal、提供された両prosrc一致のunit検査あり。SQL文字列検査だけをDB証拠にはしない。
- .local-isolated-*には触らず、新規pr_forward_* DBとpr-forward-rest-* loopback containerを証跡として保持。既存Authには架空example.invalidテストユーザーのみ追加。
- v1 migrationの内容・過去migrationは未変更。v1をremoteへ先行適用しない。

### 再実行コマンド（ローカルのみ、backendから）
Docker DesktopのbinをPATHへ追加したうえで:
```powershell
.\venv\Scripts\python.exe scripts/validate_forward_local.py --allow-disposable-fixtures
.\venv\Scripts\python.exe scripts/run_local_regression.py --allow-disposable-fixtures
```
runnerはDocker project/loopbackを照合し、local gateway credentialをメモリだけで取得。JWT手作業貼付不要。
v2 validatorは新規DBのみ対象。既存DB reset、remote URL option、provider呼出なし。

### Remote適用前後（まだ実行しない）
適用前: exact証跡の対象project/時刻、現在preflightとの差分、schema/ACL/functionのbackupと復元手段、writer停止・作業窓を人間が確認し、別途適用承認する。
未知overload/本文/owner/config/ACL/policy/index/columnは停止。rls_auto_enable/ensure_rlsやcanonical、既存一意indexは変更しない。
適用後: transaction COMMIT、11内部table/14追加RPC/必要indexとtrigger、checkout最小権限、legacy browser拒否/service許可、canonical不変、既存件数/billing=test、Backend正常経路を確認する。
transaction失敗はrollbackを確認。COMMIT後の復旧は保存した完全schema/ACL/backupと承認済みforward修正に基づく。監査SQLだけで完全復元できるとはしない。
本番送信/課金/公開をこのGate成功から自動承認しない。
