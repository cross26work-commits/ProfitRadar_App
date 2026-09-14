# Profit Radar 公開・復旧・運営手順
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
