# Release skip分類
更新2026-09-15。最新: Backend **212 passed /0 skipped**、integration **31 passed /0 skipped**。
Docker/WSLは利用可能となり、下記旧25ケースを全件実行した。新規実DBケース2件（cursor NULL/[]、Service Role RPC迂回拒否）もPASS。
integration31件にはDB/Authケース27件と接続先guard4件を含む。外部Google/Stripe成功へは加算しない。
以下は2026-09-14時点の履歴分類。現在のskip理由ではない。

## 過去記録
2026-09-14当初。全25件、合格加算0。当時の全pytest: 178 passed /25 skipped。

全件 backend/tests/integration/test_p0_supabase_isolation.py の test_ 接頭辞付き。
共通分類: EXTERNAL / REAL SUPABASE REQUIRED。専用localhost54321のAuth/PostgREST/PostgreSQL、baseline/migration、正常login JWTが必要。
環境fixtureのP0_SUPABASE_TEST_URL未設定で理由付きskip。Docker engine/WSL未導入を実確認。CLIだけでは起動不可。
通信失敗やSQL例外をskipへ変換していない。共有/本番を代替にしない。

| # | test名（test_省略） | 必要な実証 |
|---|---|---|
|1|both_users_read_own_profile_only|A/B本人SELECT・他社profile非表示|
|2|business_select_permission_denied[customers]|顧客table実効ACL拒否|
|3|business_select_permission_denied[messages]|メールtable実効ACL拒否|
|4|business_select_permission_denied[profit_events]|案件table実効ACL拒否|
|5|business_select_permission_denied[gmail_connections]|credential table実効ACL拒否|
|6|profile_escalation_denied_without_changes|所属/role改変拒否・DB不変|
|7|onboarding_replay_concurrency_and_untrusted_fields|登録再実行と未信頼入力|
|8|missing_and_invalid_token|実Auth検証endpoint利用時のHTTP拒否|
|9|real_jwt_api_positive_and_cross_tenant_denial|実JWT A/B正常と越境・送信前拒否|
|10|first_onboarding_concurrently_creates_exactly_one_company|初回登録同時実行|
|11|saved_draft_real_db_roundtrip_and_other_tenant_denial|Draft実永続化・隔離|
|12|direct_customer_writes_explicitly_denied[insert]|直接INSERT拒否|
|13|direct_customer_writes_explicitly_denied[update]|直接UPDATE拒否|
|14|direct_customer_writes_explicitly_denied[delete]|直接DELETE拒否|
|15|concurrent_send_claim_and_transactional_finalize|送信claim競合/確定transaction|
|16|atomic_inbound_page_and_cursor_rollback|受信データ/cursor rollback|
|17|new_internal_tables_and_rpcs_are_not_browser_accessible|内部table/RPC実効権限|
|18|financials_real_jwt_roundtrip_isolation_and_version_conflict|金額実永続化とversion競合|
|19|operator_recovery_owner_fencing_and_idempotency|復旧owner fencing|
|20|budget_concurrent_reservation_and_monthly_hard_stop|予算同時予約・上限|
|21|account_delete_real_reauthentication_and_atomic_cleanup|再認証/削除transaction|
|22|split_payment_idempotency_and_cross_company_rejection|分割入金/他社拒否|
|23|provider_recovery_requires_review_and_preserves_budget|provider復旧review/予算保持|
|24|gmail_revoke_recovery_cannot_delete_reconnected_account|再接続競合でcredential削除防止|
|25|billing_mode_promotion_rejects_test_history_and_browser|課金mode移行の拒否条件|

## ローカルで補完した検証
8番の実provider検証は残す。別途 test_auth_safety.py にonboarding HTTP拒否3ケースを追加・実行した。
未認証/不正Bearer/Basicを本来のJWT検証関数で拒否し、DB/provider呼出ゼロ・安全な応答本文を検査。認証dependency overrideなし。
これは合成HMAC設定でのローカル検証であり、Supabase発行JWT/実provider合格ではない。
接続先安全guard4件もローカル実行済み。SQL構文・mockテストはDB動作証拠に数えない。
LOCAL UNJUSTIFIED SKIPS: 0。実DB必須の25件をモックへ置換して減らさない。

## 実行手順
Docker/WSL準備後、repo root: powershell -File scripts/start-isolated-tests.ps1 -RunTests
専用接続先一致・明示許可が必要。スクリプト/fixtureで架空A/Bと通常login JWTを準備し、秘密値の手作業共有は不要。
実Google/Stripe E2E、Docker restoreはこの25件に含まれない別のEXTERNAL Gate。
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
