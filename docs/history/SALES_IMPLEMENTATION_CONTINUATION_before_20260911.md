# 販売完成へ向けた継続チェックポイント

## 最新作業位置（2026-09-10、138 passed / 22 skipped）

この節を以下の履歴より優先する。HEADは変更なし、既存dirty変更をすべて保持。
AI事前予算予約・削除job・UNKNOWN復元は実装済み。今回、分割入金007、provider復旧008、復旧CLI、Gmail同期状態UI、Next16.3.4と依存脆弱性修正（npm audit 0）を追加。SQLは本番・隔離DBとも未適用。
次は隔離UI fixtureのPC/390px検証、全route entitlementテスト、保持/監視入口、Gmail送信済み起点と処理量上限、最終回帰と文書統合。
`frontend/tests/ui/serve.mjs`はloopback3190で実client componentを架空APIで表示する。CSP connect-src none、実認証迂回を製品へ追加していない。実Auth/DB合格ではない。
現時点は **CODE INCOMPLETE**。以下の「AI予算・削除未着手」「113件」等は過去記録であり現在の状態ではない。

> **2026-09-10再開更新:** 最新状態は [SALES_RELEASE_FINAL.md](SALES_RELEASE_FINAL.md)。112 passed / 19 skipped。販売不可・CODE COMPLETEではない。下記の古い件数と未着手一覧は履歴。Gmail大historyページのchunk保存、解除0件検査、financial/operator実DB用テスト、not_target救済・legacy再利用を追加。次は同期thread補完の処理量制御、AI budget、削除jobへ継続する。新RPCは実DB未検証。

> 最新の実装・検証・再開位置は [20260909追加チェックポイント](SALES_COMPLETION_CHECKPOINT_20260909.md) を優先する。以下は今回再開前の記録であり、未着手表示と44/14件は最新値ではない。

2026-09-09 JST / `arc/profit-radar-release-readiness`
HEAD `3c9a83ad2264899187bd67d1ec9ccac7b8100f70`。販売完成でもP0完了でもない。
本番DB・実Gmail・課金・deploy・commit/pushは未実行。

## 今回の差分

- `backend/tests/integration/test_p0_supabase_isolation.py`: 旧2テストを置換。明示許可・URL完全一致・loopback54321限定、架空Authユーザー作成→通常login JWT、A/B自己profile・Customers・Leadsの正例、他社詳細/更新/送信拒否、DB変化なし、provider禁止spy、直接DB42501、profile昇格拒否、onboarding再実行/初回並行、draft復元。他社DELETEは実API未実装の405確認であり削除認可の実証とは別。
- `backend/app/core/auth.py`, `backend/app/api/onboarding.py`: JWT issuer/audience/exp/sub/role、provider障害503、エラー一般化、client user_id/company_id/roleを422拒否。
- `supabase/migrations/202609090001_p0_tenant_rls_onboarding.sql`: index列/unique/valid/ready/partial検査、対象table/column ACL限定、継承権限残存時停止、profile/companies restrictive境界、正規company表示維持、onboard引数/戻り値競合停止、pg_catalog search_path、auth.users存在確認。未適用・SQL実行未検証。
- `supabase/release_readonly_tenant_audit.sql`: PUBLIC pseudo-role誤用・NULL件数修正、実効table/column権限・role membership・index validity追加。
- `backend/app/services/reply_drafts.py`, `reply.py`, `frontend/src/components/business/ReplyDraftForm.tsx`: tenant/event検査、subject改行拒否、upsert、保存済み優先復元、保存ボタン。復元時AIなし。
- `supabase/migrations/202609090002_saved_reply_drafts.sql`: service SELECT/INSERT/UPDATE限定・RLS。同名table存在時は停止して差分レビュー。未適用。
- `backend/app/core/token_vault.py`, `gmail.py`, `reply.py`: Fernet envelope、会社IDバインド、旧キー読取りrotation、plaintext/missing key拒否。
- `backend/scripts/migrate_local_gmail_tokens.py`: ローカル専用移行リハーサル、既定dry run、writer停止前提。本番移行ツールではない。
- `backend/app/services/gmail_revocation.py`: revoke→削除、失敗はpendingで再試行。200だけ成功。失効後DB削除失敗/既失効400の復旧と並行lockは残る。
- `backend/app/services/gmail_credentials.py`: 3経路の復号/refresh共通化、期限判定、client/token_uri照合、暗号化更新結果保存、旧envelope比較でOAuth再接続の上書きを防止。provider代替テストのみで実Google/DB CAS未検証。
- `backend/app/core/runtime_settings.py`, `main.py`, `.env.example`: dotenv上書き禁止、本番必須設定/HTTPS/CORS検査、固定LAN除去、鍵設定例。
- OAuth callback全体の例外一般化、APP_ENV未設定時send-test閉鎖。
- 新unit tests: auth_safety / token_vault / reply_drafts / runtime_settings / gmail_boundary_errors / gmail_revocation。SQL文字列テストはDB合格に数えない。

既存dirty変更は破棄していない。開始時app/tests/supabase/docsを `_backups/sales-continuation-20260909` へコピー。backupをGitへ含めない。秘密値追加なし。

## 作業状態

| 項目 | 状態 | 次のコード作業・検証 |
|---|---|---|
| P0 isolation/onboard/grants | 実装中 | 完全な隔離baseline、migration自動適用、SET ROLE、匿名CRUD、views/RPC/継承迂回、復元情報充足。実DB14テストは環境待ち |
| 1 Token lifecycle | 実装中 | refresh実装済み・実検証待ち。reconnect互換、移行手順、既失効/削除失敗復旧、status制約確認、disconnect/send並行lock |
| 2 Auth/production | 実装中 | API全体エラー、service例外マッピング、proxy/uvicorn query redaction、実起動smoke |
| 3 Draft保存/復元 | 実装済み／検証待ち | 既存schema互換差分、実DB/browser reload/logout/login、送信後と複数tab競合の扱い |
| 4 定期・差分同期 | 未着手 | check-replies共通サービス化、永続cursor/page、company lease、scheduler secret、backoff/run記録 |
| 5 送信重複/結果不明 | 未着手 | operation ledger/claim RPC、SENT照合、不明時再送禁止、reply_logs/timeline確定transaction |
| 6 AI統合/金額/上限 | 未着手 | 二重AIをsnapshotへ統合、根拠金額/単位照合、injection、budget予約/usage/cost |
| 7 試用/課金/解約 | 未着手 | subscription/server entitlement、署名webhook、重複/順序逆転テスト。実課金しない |
| 8 削除/保持/監視 | 未着手 | account削除は既存503。transaction/retention/alerting実装 |
| 9 販売・登録案内 | 未着手 | terms/privacy整合、価格/14日/明示契約導線、問い合わせ/保持情報 |
| 10 E2E/公開運営手順 | 実装中 | OWNER_ACTIONS、統合fixture追加。完全bootstrap/公開runbook/実E2Eは未完 |

未着手を「外部操作待ち」に付け替えない。定期同期の販売仕様を手動同期へ縮小しない。

## 検証

- Backend pytest: 44 passed / 14 skipped。skipは実Auth/DB環境なしで合格に含めない。
- `venv/Scripts/python.exe -m compileall -q app tests scripts`: 成功。
- Frontend `npx tsc --noEmit`, `npm run lint`, `npm run build`: 成功、19 routes。DB/OAuth/E2E合格ではない。
- `git -c core.safecrlf=false diff --check`: 成功。
- migration/RLS/real JWT/Gmail/請求/本番起動は未実証。架空ユーザーも実DBには未作成。

## 再開順

1. P0隔離bootstrap/実行SQLテストを完成。実schemaとmigration互換を照合。環境なしでもテスト実装を続ける。
2. token refreshの実DB CAS検証、reconnect・disconnect復旧を完成。旧平文接続は停止するため本番反映禁止。
3. 既存Gmail syncの共通化とDB lease、次にsend ledger/結果不明復旧。別実装を並立させない。
4. AI/billing/削除/販売案内へ継続。OWNER_ACTIONSの本人操作待ちとは別管理。

## 公式資料

Google失効はPOSTでtokenを渡しHTTP200を成功扱いとする。[Google OAuth Web Server公式資料](https://developers.google.com/identity/protocols/oauth2/web-server#tokenrevoke)（2026-09-09確認）。実失効せずprovider代替テストのみ。
# 最新検証結果の補正

最新は **113 passed / 19 skipped**（2026-09-10）。FinancialSummary期間指定・原価表示追加後もTypeScript / ESLint / production build成功。以下の112件は直前チェックポイントの履歴。実DB・認証後UIは未実証。販売不可。詳細はSALES_RELEASE_FINAL.md。
