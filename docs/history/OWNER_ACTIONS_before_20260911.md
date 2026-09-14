# 外部操作と開発残件の分離（2026-09-09）

## 最新追記

- Supabase CLI 2.117.0は実行確認済み。DockerだけがローカルAuth/DB起動の環境阻害。`scripts/start-isolated-tests.ps1 -RunTests`はDocker不在を検出しDB作成前に停止した。
- Docker準備後は同scriptでfixture/通常login JWTを自動用意する。JWTを手作業で取得・共有する必要はない。
- StripeテストPriceはJPY 19,800/月・税込設定。key/webhook secret/Price IDはローカルsecret環境で設定しチャットへ貼らない。実課金は現コードで禁止。
- 販売主体/問い合わせ、保持期間、返金条件、Google審査状態は本人確認待ち。未確定契約条件を公開しない。
- 差分同期・削除・AI根拠/費用・契約競合は**コード残件**であり本人操作待ちではない。最新状態は `SALES_COMPLETION_CHECKPOINT_20260909.md`。

本番変更・メール送信・課金・公開は実施していない。販売開始不可の判断を維持する。

## 本人操作が必要

1. 隔離ローカルSupabaseを起動できるDocker環境を用意する。このWindows環境ではDockerエンジン/psqlを検出できなかった。Supabase CLI 2.117.0は実行確認済み。Docker Desktop/仮想化の有効化は管理者権限・再起動等の確認が必要なため勝手に行わない。CLIのみではAuth/DB実証にならない。
2. 本番を複製する場合は**schemaのみ**を安全に提供する。顧客行・トークンをコピーしない。最新監査SQLは読み取り専用だが関数定義/default等に埋込み機密がある場合は共有前に伏せる。
3. Backend専用暗号化キーをsecret storeで生成・保管・バックアップする。値をチャット、ログ、Gitへ出さない。既存平文tokenは新コードでは503で停止する。移行・鍵ローテーション・再接続を隔離環境で実証するまで本番反映しない。
4. Google審査状態、販売主体・問合せ・保持期間、決済事業者・契約条件を確定する。これらは未完のコード作業の代替ではない。

## 隔離Auth/API統合テスト

専用ローカルSupabaseを初期化し、実schemaとの互換性をレビューしたmigrationをその環境だけに適用する。現在のリポジトリは完全なローカルbootstrapが未完成であり、CLI init/startだけで準備完了とはみなさない。

環境変数（値は記録しない）:

- `P0_SUPABASE_TEST_URL=http://127.0.0.1:54321`
- `P0_SUPABASE_EXPECTED_URL=http://127.0.0.1:54321`
- `P0_ALLOW_FIXTURE_WRITES=CREATE_DISPOSABLE_FIXTURES`
- `P0_SUPABASE_TEST_ANON_KEY` / `P0_SUPABASE_TEST_SERVICE_KEY`: 当該ローカル環境の値だけをプロセスへ設定。

backendディレクトリから `venv/Scripts/python.exe -m pytest tests/integration -q -rs --tb=short`。
`--showlocals`、HTTP debug logging、JUnitの秘密値収録は禁止。テストは管理APIで架空のexample.invalidユーザーを生成し通常ログインする。実際の認証依存は無効化しない。Gmail providerは呼ばれたら失敗する代替関数。テスト用行は隔離DBに残す。終了後は使い捨て環境単位の廃棄を本人が確認する。共有DBで実行しない。

DB SET ROLEテスト、migration自動適用、baseline schema構築は別の**開発残件**。現テスト成功だけでこの範囲を合格にしない。

## Token移行リハーサル

同じローカル接続許可とBackend暗号化キーを設定し、backendで `venv/Scripts/python.exe -m scripts.migrate_local_gmail_tokens`。既定は件数のみで書込みなし。`--apply`はローカル限定で暗号化。OAuthなどのwriterを停止して実行する。これは本番移行承認・本番用完全復旧手順ではない。

## 適用と復旧

新規migrationはすべて未適用。既存onboard_user引数/戻り値、index定義不一致、同名reply_draftsは停止条件。監査結果を照合し明示的な互換移行を先に完成させる。
transaction途中の失敗はROLLBACKで当該transactionの変更を破棄できる。commit後の復旧とは異なる。後者には変更前schema/関数/全ACL（列・継承含む）/policy/RLS/所有者の記録、検証済みバックアップ、変更後データの扱いが必要。監査SQL出力だけで完全復元可能とはしない。
公開時にはreverse proxyとuvicornのcallback query/access loggingを無効化または確実に除去する。生のOAuth URLを監視へ送らない。
# 2026-09-10最新追記

最新Gateは `SALES_RELEASE_FINAL.md`。Docker/WSL未導入を再確認し、Supabase CLI2.117.0単独では起動不可。Docker engineと必要なWSL/仮想化を本人が準備後、`scripts/start-isolated-tests.ps1 -RunTests`を実行する。秘密値/JWTをチャットへ貼らない。19件skipは実証未完。AI予算・削除・同期の残件等は開発作業であり、本人操作待ちではない。本番・実Google・実課金・公開は今回未実行。
