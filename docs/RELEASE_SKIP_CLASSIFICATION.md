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
