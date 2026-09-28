# Remote schema forward 最終監査

## 2026-09-17 最新: production v2適用・post-apply PASS（本人報告）

対象project `zszmetqhksthduoxfvac` でv2 COMMIT成功、post-apply `FINAL=PASS`、既存20テーブルのpre/post件数一致、本番backup復元PASSとの報告を受けた。エージェントはremoteを再照会していない。以下の「v2未適用」「適用禁止」はpre-apply当時の履歴としてのみ残す。v2を再適用しない。次は別承認を要するproduction Authenticated A/B E2E。実行状態・再開地点は `docs/RELEASE_STATUS.md`。

### 履歴: 2026-09-17 remote pre-apply PASS / v2未適用

ユーザー提供のRemote Final Gate結果はFINAL=PASS。ACLとlegacy onboard_userはKNOWN_REMEDIABLEで、v2適用後の再検証が必要。以下の「STOP」や旧v1手順は当時の履歴であり現在の操作指示ではない。適用前にbackup/復元可能性、writer停止、対象project、v2 SHA256と直前のread-only gateを確認し、適用の明示承認を得る。現行の作業・結果・再開位置はRELEASE_STATUS.mdを参照。

## 履歴: legacy列・ACL drift patchはSTOP

最新の列とlegacy ACL対応は実DB未検証。remote4 policyのauthoritative snapshotは1016 bytes・指定SHA256で照合/統合済み。旧gmail_sync_runsは追加SELECT-only証拠によりglobal aggregate・0行と確定しtenant purgeから除外。company_idは追加せず、適用transactionで既知schema/0行を再確認する。Docker Engine利用不可によりAPPLY READYではない。
最新の根拠・列別判断・194 passed/27 skippedと再開手順はREMOTE_SCHEMA_FORWARD_DRIFT_PATCH.mdを参照。以下のraw capture修正時のPASSは履歴であり今回のpatch合格を意味しない。

## Raw capture受領・canonical exact hash確認（最新）

ユーザー提示のCRLF→LFのみ正規化したSHA256は
`12A8812B782D2D2FD1D41A9199F12199D0C3767E76D4CFBE649CCDB15D1B08D2`。
ユーザー提供の847 bytesのraw captureを受領。Raw SHA256は
`E426BDEA084DFD662E3C766EEEC3853588AE03AFFC16F7D7F885A576EC9F48AC`で確認済み。
現在のdocs / preflight / v2 canonical本文はいずれも上記LF SHA256に一致。
過去の`57C80FAF...`不一致はraw captureからexpected側だけ修正して解消。
原本は変更せず、docs/create_company_and_profile_remote_capture.jsonにBase64で損失なく保持する。
validatorは固定したraw長/raw hash/LF hashを先に検証する。synthetic fixtureから承認hashを生成しない。
独立hash検査をvalidatorのDB作成前に追加。fixtureとexpectedの相互一致だけをremote exact証拠にはしない。
v2 full validator PASS、identity rollback10件（空白1文字変更を含む）/その他rollback13件 PASS。
推測による再インデントや比較緩和はしない。legacy・remote関数は変更せず、remote操作・commit/pushも未実施。
今回のローカル検証DB: pr_forward_9eb22d19b2494f77be86cbee7e491286。過去の検証結果と区別する。
今回再実行: SQL関連33 passed、local integration31 passed/0 skipped、Backend全体218 passed/0 skipped（SDK非推奨警告6件）、git diff --check PASS。

2026-09-15 JST / Repo C:\Users\closs\ProfitRadar_App
Branch arc/profit-radar-release-readiness / 現在HEAD 435bb0ac368c32e50dda918863213b3cdbf69543
検証対象は上記HEADに未コミットのv2差分を含む。checkpoint commitは未実行。

## 最新v2サマリー

**最終checkpoint候補 / remote適用可能（技術的事前判定）**。
exact onboarding定義とcompanies.owner_user_idの追加read-only証跡を受領済み。
一方、**実行はbackup・停止手順の直前確認および人間の適用承認前なので禁止**。
技術的準備完了とremote適用の実行許可は別であり、commit/pushも未承認・未実行。

対象SQL: `supabase/migrations/202609150001_remote_schema_forward_v2.sql`

v2はcheckout補完、既知legacy onboard_userの最小権限化、canonicalのexact identity検査・不変維持を含む。
ローカル証拠はv2 full validator PASS（構造等13件・identity9件のrollback）、正規JWT検証PASS、integration31 passed/0 skipped、Backend216 passed/0 skipped。
これらは後半のv2検証記録に対応し、remote適用成功を意味しない。
現在のcommit候補と適用前後Gateは後半の最新v2記録を参照する。旧v1 SQLは適用対象ではなく、先行再実行しない。

## 履歴：旧v1最終監査（以下は当時の記録）

以下の旧HEAD・判定・SQL・検証値は履歴として保持する。現在の判定には上記最新v2サマリーを優先する。
Branch arc/profit-radar-release-readiness / HEAD 27d6ec0777e7019a3319cbd273999d84b18b2a5f

### 旧v1判定
**適用禁止（現時点）**。ローカル技術検証はPASSだが、remote定義との最終照合・backup・停止手順・人間の適用承認は未完。
コードの追加修正を要求する判定ではない。remoteへ接続せず、SQL Editor/db push/履歴repair/commit/push/メール/Stripe chargeを行っていない。

### 旧v1対象SQL
supabase/migrations/202609140001_remote_schema_forward.sql
SHA256: 0027F2B1740804DB72242F8511F13445C6118E8AB22ED72D6D191B999F7C049F
UTF-8 strict decode正常、U+FFFDなし、日本語文字133、参照元SQLの日本語literalとの一致テストPASS。
過去migrationの変更なし。DMLを含む関数は定義するだけで呼び出さない。適用時の永続データ追加は新規billing_runtime_configのtest行のみ。
既存行DELETE/UPDATE/TRUNCATE/DROP、live昇格、過去migration再実行を行わない。

## 作成objects（存在時は厳密な互換性確認）
| Table | 役割 / Service Role |
|---|---|
| gmail_sync_cursors | cursor/version/pending / SELECT |
| gmail_inbound_receipts | company/mailbox/message冪等性 / SELECT |
| operation_recovery_audit | 運営復旧の証跡 / SELECT |
| financial_records | 売上/入金/原価/確認日/version / SELECT |
| financial_record_history | 金額変更履歴 / SELECT |
| ai_budget_reservations | token/cost予約 / SELECT + status/actual_input_tokens/actual_output_tokensのみUPDATE |
| account_deletion_jobs | 削除段階/保持 / SELECT + gmail_done/billing_done/billing_reference/last_error_codeのみUPDATE |
| account_deletion_audit | 削除証跡 / SELECT |
| financial_payments | 分割入金/取消 / SELECT |
| billing_runtime_config | test既定のmode gate / SELECT |

全10tableはRLS有効・browser policy追加なし。anon/authenticated/PUBLIC/継承・列権限によるアクセスを検査。
既存互換tableのService Role権限も上記へ正規化。過去のdefault privilege由来ALLが残る欠陥をここで修正した。対象外tableは変更しない。
FK/PK/unique/check/null/default/型をtemplateと比較。関連view、不明policy/trigger、無効index、未知grantee、関数overload/本体差異は停止条件。

新規RPC/関数14:
- commit_gmail_inbound_page
- recover_company_work
- save_financial_record
- reserve_ai_budget
- company_is_active
- request_account_deletion
- purge_account_data
- complete_account_deletion
- purge_expired_deletion_audit
- prevent_deleted_user_onboarding（trigger専用）
- record_financial_payment
- void_financial_payment
- resolve_provider_uncertainty
- promote_billing_live（定義のみ、実行禁止）

SECURITY DEFINER、search_path=pg_catalog,pg_temp。service_roleのみEXECUTE、trigger関数にはservice_roleへの追加EXECUTEなし。
明示index: ai_budget_company_month / financial_payments_company_date。PK/uniqueのindexも定義に付随する。
profilesへBEFORE INSERT trigger prevent_deleted_user_onboardingを追加（既存ならidentity/type/enabled条件を照合）。

## CREATE OR REPLACE / 触らないobjects
永続既存functionのCREATE OR REPLACEは **0件**。同名互換functionは保持、本体の空白差を含め一致しない場合も停止。
acquire_gmail_sync_lock / release_gmail_sync_lock / apply_billing_snapshot / claim_gmail_work / release_gmail_work /
create_company_and_profile / ensure_company_billing / finalize_gmail_send / onboard_user / reserve_ai_run / rls_auto_enable を置換しない。
既存companies/profiles/customers/messages/profit_events/reply_logs/timeline等の行・column・policyを変更しない（profilesへの上記trigger追加を除く）。
migration historyには触らない。補助objectsはpg_temp内のみで別sessionへ公開しない。再実行は新しい接続sessionで行う。

## pending_ids契約
columnはnullable JSONB。直接RPCのJSON nullはSQL NULLへ変換、[]は[]のまま。
現在SyncStore.commitはNone/欠落を[]に変換。pending_pageはNULL可。既存NULLのbackfillやNOT NULL化はしない。
空配列/NULL・cursor version増加・受信行追加なしを実DBで検証。原子rollback/途中page再開/重複も既存統合テストで確認。

## 実行証拠
- 指定checkpointを含む前段: integration 31 passed /0 skipped、全Backend 211 passed /0 skipped。
- 最終監査でUTF-8回帰1件を追加。最新全Backend結果は SALES_RELEASE_FINAL.md。
- SQL grammar/UTF-8/restore unitをまとめて31 passed。
- Forward validator: 新規DBに旧schema前提を構築→空データ適用とrollback→架空既存データを入れてcommit→再実行、PASS。
- conflict rollback 10/10: table差異、policy、column grant、index、overload、search_path、public CREATE、view、trigger、billing approval不整合。
- 旧行のDB内hash、対象外sentinel ACL、再実行schema/row不変を検査。実remote schemaと同一である証拠ではない。
- 隔離restore（前段実行）: restore_verified=true、source_unchanged=true、54 tables。public/authのschema/ACL/件数。全Supabase/Storage/role/内容行のDRを証明しない。
- 新しいpr_forward_* DBとpr_restore_* DB/archiveは証跡として保持。削除なし。無断で再利用/一括削除しない。
- 外部Google/AI/Stripeは代替。実Auth/DBとprovider代替を区別。

## Frontend本番構成
旧127.0.0.1:8000固定は別ホスト構成で不正。next.config.tsをBACKEND_ORIGINへ変更。
開発時のみ127.0.0.1:8000を既定にする。本番はBACKEND_ORIGINとNEXT_PUBLIC_API_BASE_URLの両方を明示し、HTTPS origin・userinfo/query/fragmentなし・loopback不可を検証。
現在のServer API helperは絶対URL前提なので、本番NEXT_PUBLIC_API_BASE_URLに/backend-apiのような相対値は使わない。既存.envは変更していない。
NEXT_PUBLIC値とrewriteはbuildに反映されるため、本番URLで再buildし同じ設定で起動する。Backend CORSと公開URLも合わせる。
検証buildは https://api.example.invalid をプロセス内だけで指定。実疎通なし。この.nextを本番配布しない。
5 Node tests（設定3/Server API2）、tsc/lint/build/npm audit PASS。

## Remote適用前チェックリスト（人間、別承認後のread-only確認）
- [ ] project/環境/DB/担当者/作業窓を確定。今回の接続禁止を解除する明示承認を得る。
- [ ] remote_schema_forward_preflight.sqlの各SELECTをレビューし、実行承認後にmetadataを安全に保存する。現在は未実行。
- [ ] 198既存列の型、profiles.user_id unique/NULL/重複、全prerequisite RPC署名/owner/search_path/ACLを照合。
- [ ] 10table/14functionの存在状況と未知overload/extra constraint/view/trigger/列ACL/継承roleを確認。不一致を無理に緩めない。
- [ ] 旧公開RPC/SECURITY DEFINERの本文・view依存・RLSを人間が確認。forwardの検査だけで全旧RPCの安全性を保証しない。
- [ ] billing_runtime_config既存ならtest/承認NULL、未存在ならtest行のみ作成することを確認。live昇格しない。
- [ ] 検証済みbackup、schema・全ACL・RLS・関数定義/owner・triggerの退避、件数基準を確保。
- [ ] worker/API writerを停止し、Service Roleの対象外直接書込み依存がないことを確認。
- [ ] SQL SHA256、client/server encoding=UTF8、lock timeout 5秒/statement timeout120秒、接続ownerpostgres/supabase_adminを確認。
- [ ] 新規SQL一本だけの適用を明示承認。db push、過去SQL、履歴repairを併用しない。

## 提案のみ：将来の適用コマンド
現在実行禁止。認証情報はOSの保護されたpg_service/pgpass等に設定し、URL/passwordをコマンドやチャットへ貼らない。
新規psql sessionで、確認済みservice aliasを使用する例:
```powershell
$env:PGCLIENTENCODING = 'UTF8'
psql 'service=profit_radar_reviewed_remote' -X -v ON_ERROR_STOP=1 -f supabase/migrations/202609150001_remote_schema_forward_v2.sql
```
PowerShellのGet-Content pipeによる再エンコードを避ける。SQL内にBEGIN/COMMITがあるため別の自動transaction wrapperで包まない。
error/timeout/未知objectなら停止。connectionを閉じて未commit rollbackを確認し、原因を調査。既存制約を消して通過させない。

## 適用後チェックリスト
- [ ] COMMIT成功。10table/14function/index/triggerとschema cache reloadを確認。
- [ ] RLS、Service Role table/列権限、anon/authenticated/PUBLIC/継承の実効権限を再取得。
- [ ] 現在の承認テストユーザーで自己閲覧と越境拒否を確認。顧客データ内容を報告に載せない。
- [ ] 旧行件数/事前基準不変、billing mode=test、既存function/既存policy不変を確認。
- [ ] Backend read/health、保存・予算・同期の通常経路を別途承認されたテストで検証。メール/課金を勝手に始めない。
- [ ] 不整合ならwriter停止を維持。commit前rollbackとcommit後復旧を区別する。後者はbackup/承認済みforward fixで対応し、新規証跡を消すDROPはしない。

## 旧v1 checkpointのCommit候補（履歴・今回対象ではない）
- supabase/migrations/202609140001_remote_schema_forward.sql
- supabase/remote_schema_forward_preflight.sql
- backend/scripts/validate_forward_local.py
- backend/tests/test_remote_forward.py
- backend/tests/integration/test_p0_supabase_isolation.py
- backend/tests/test_restore_isolated.py
- frontend/next.config.ts
- frontend/config/backend-origin.ts
- frontend/tests/backend-origin.test.mjs
- docs/REMOTE_SCHEMA_FORWARD_REVIEW.md
- docs/SALES_RELEASE_FINAL.md
- docs/SALES_IMPLEMENTATION_CONTINUATION.md
- docs/RELEASE_RUNBOOK.md
- docs/RELEASE_SKIP_CLASSIFICATION.md

.local-isolated-failed-* / .local-isolated-old-* / .local-isolated / .env*実値 / .next / archiveは対象外。git add . は使わない。
既存Next設定のユーザー差分は開発既定値として保持し、本番分岐を追加した。過去migrationは編集していない。
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

### 今回のcommit候補（最終checkpoint候補・承認前なのでcommitしない）
- supabase/migrations/202609150001_remote_schema_forward_v2.sql
- supabase/remote_schema_forward_preflight.sql
- backend/scripts/validate_forward_local.py
- backend/tests/test_remote_forward.py
- backend/scripts/validate_v2_jwt.py
- backend/scripts/run_local_regression.py
- docs/remote_onboarding_functiondefs_20260915_exact.txt
- docs/REMOTE_SCHEMA_FORWARD_REVIEW.md
- docs/SALES_RELEASE_FINAL.md
- docs/SALES_IMPLEMENTATION_CONTINUATION.md
- docs/RELEASE_RUNBOOK.md
- docs/RELEASE_SKIP_CLASSIFICATION.md

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

最終v2検証DB: pr_forward_a925e1a551454a87bb421178cd372add。
最終専用REST: pr-forward-rest-06e283a6b8d14ea682cf0244cf58a81f（loopbackのみ）。
exact入力SHA256: 6B2750F6FED4812D588586F0EFF7538BED8FA189A6455D59E0778427CE208539。
既存の保存HTML、同名.sqlフォルダ、*_folder_backup、.local-isolated-*は今回commit対象外。削除・移動していない。

owner_user_id証跡反映後の今回検証: tests/test_remote_forward.py + tests/test_sql_parse.py は31 passed。git diff --check PASS。前回の全回帰を今回再実行したとは扱わない。更新対象は文書5件とread-only preflightのみ。migration/runtimeコード変更なし。
