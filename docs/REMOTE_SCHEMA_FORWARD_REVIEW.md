# Remote schema forward 最終監査
2026-09-15 JST / Repo C:\Users\closs\ProfitRadar_App
Branch arc/profit-radar-release-readiness / HEAD 27d6ec0777e7019a3319cbd273999d84b18b2a5f

## 最終判定
**適用禁止（現時点）**。ローカル技術検証はPASSだが、remote定義との最終照合・backup・停止手順・人間の適用承認は未完。
コードの追加修正を要求する判定ではない。remoteへ接続せず、SQL Editor/db push/履歴repair/commit/push/メール/Stripe chargeを行っていない。

## 対象SQL
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
psql 'service=profit_radar_reviewed_remote' -X -v ON_ERROR_STOP=1 -f supabase/migrations/202609140001_remote_schema_forward.sql
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

## Commit候補（今回commitしない）
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
