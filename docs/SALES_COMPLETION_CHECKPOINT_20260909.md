# 2026-09-09 販売完成作業・最新チェックポイント

対象: `arc/profit-radar-release-readiness` / HEAD `3c9a83ad2264899187bd67d1ec9ccac7b8100f70`。既存未コミット変更を保持。販売不可、P0未完了。本番DB・Google・Stripe実操作・公開・commit/pushなし。

## 実装済み／実環境検証待ち

- 返信GETは保存draft→保存snapshot→空の順。AIは明示POST生成のみ。月次生成予約、会社ロック、30,000文字入力制限、処理時間記録。会話AIは30秒timeout・自動retryなし・出力2048token。実生成品質・費用は未計測。
- 送信operation永続claim、結果不明時再送禁止、固定Message-IDによるSENT照合、reply_logs/timeline/event確定RPC。UIに結果不明・照合・確認本文。会社ロックで送信/照合/解除/OAuthを排他。
- scheduler専用secret入口、会社ごとのロック・失敗分離・実行記録、300秒間隔の独立worker。**差分cursor/初回pagingは未実装**。現行は既知eventの返信検知である。
- 会社作成時刻基準14日試用、明示Checkout、Stripe test keyのみ、署名・時刻検査、現在subscription再取得で古いevent snapshotを不採用。Checkout試行ID永続化、期間末解約、send/sync/AIのサーバー利用制限。
- 販売ページ、利用ガイド、試用/契約UI。未公開・検証用表示。販売主体未入力時に公開済みと表示しない。
- 隔離起動script/config/baseline、通常Auth loginによるA/B JWT生成fixture。CLI 2.117.0利用可。Docker未導入で起動scriptはDB作成前に停止。

## 検証証拠

直近: Backend 83 passed / 15 skipped（実Supabase未提供）。11件はpglast SQL構文のみでDB/PLpgSQL合格ではない。compile、TypeScript、ESLint、production build（20routes）、diff check成功。pytestをrootから実行した一度の収集失敗（app import）はbackend作業directoryで再実行して解消。

### 後半で追加した修正

- OpenAI Docs仕様確認に基づき30秒timeout・implicit retry無効・出力2048、request-local usage集計。取得できたinput/output tokenのみ記録し、費用はunknownのまま。SDK制限のunit test追加。
- price_basisの人単位と期間単位の両方を要求。日額だけで人日と推定しない。円/人数/日数のliteral単位照合、全角/万円対応。数値の意味関係や矛盾・日付との区別まで実証したものではない。
- 旧subscription eventは保存Checkoutの会社・subscription一致を要求し、新契約上書きを防止。JPY税込月額Priceのactive/interval_countも検査。代替provider testのみ。
- Gmail解除後にrevoked markerとtoken消去を保存し、DB削除失敗後はlocal deleteだけ再試行。**provider成功とmarker保存の間の障害・既失効400は残件**。
- reconnectでrefresh tokenが省略された場合、同じ接続中email/clientのみ旧暗号化refreshを再利用。別アカウント・失効pending・client不一致は拒否。新規offline credentialなしも拒否。

ブラウザ: 販売ページPC/390px、登録390pxを目視。`docs/screenshots/`に3画像。登録送信・実Auth・認証後画面は未確認。モックprovider成功をGoogle/Stripe実証としない。

## コード残件（外部待ちに振り替えない）

1. Gmail初回取得/paging/history cursor/失効復旧、原子的な受信確定、50event制限による取りこぼし防止、最終同期UI。
2. Token revoke成功とmarker保存間のDB失敗/既失効の復旧、暗号化移行演習。marker後delete retry/同一account refresh継承はunit検証済み。
3. AI実token/cost計測・金額/単位/根拠照合・停止希望/injection検証・全経路利用制限。2回AIとlegacy分析の統合は未完。
4. 旧新契約のCheckout照合は追加済みだが、実Stripe逆順/作成結果不明復旧とlive有効化の安全な設定gateは未完。現状test-onlyなので有料提供不可。
5. 削除APIは503。再開可能削除・保持・外部解除・監視通知・復元演習未実装。
6. 見込/受注/入金/原価/粗利の区別・手動確定履歴、認証後PC/mobile UI E2E。
7. SET ROLE等実DB検証、既存schema互換、rollback/commit後復旧演習、販売者/規約最終化。

## 注意すべき設計限界

- work lockは自動失効なし。worker crash時は止まる安全側設計。処理停止確認なしにTTLで解除しない。運営復旧手順が必要。
- 同じevent/宛先/件名/本文hashは送信済みでも再送不可。意図的な同文追客の仕様は残件。
- Gmail受付後DB失敗はunknown。検索未反映/一致不足では再送しない。
- Stripe Checkout結果不明が23時間超なら管理者照合。重複課金を避けるため新規sessionを自動生成しない。
- 新migrationは全て本番未適用。SQLparse成功だけで適用承認を出さない。

## 再開場所

最新差分はworking tree。バックアップ `_backups/sales-completion-20260909`。次はAI SDK上限の回帰→Token解除復旧→差分同期。全体を単一項目で完了としない。
