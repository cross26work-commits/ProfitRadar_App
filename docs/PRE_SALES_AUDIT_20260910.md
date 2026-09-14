# Profit Radar 販売前監査 — 2026-09-10 JST

## 1. 結論

**販売不可。** サポート付き3社でも、初回メール取得と「今日の収益」の成立にコード上の欠落がある。顧客分離の実DB証拠、Google外部提供条件、実決済、復旧運用も未確認。公開済みβとして安全とも判定しない。外部接続なしの画面評価は可能。

最新依頼は監査。アプリコード・migrationは変更せず、実送信・実課金・本番DB変更・公開・commit/pushなし。旧チェックポイントの完成扱いは継承しない。

### 対象と検証版

- Repository: `C:/Users/closs/ProfitRadar_App`
- Branch: `arc/profit-radar-release-readiness`
- HEAD: `3c9a83ad2264899187bd67d1ec9ccac7b8100f70`
- 既存tracked/untracked差分を含む。HEAD単体の監査ではない。
- backend/app, tests, scripts, supabase, frontend/src, package/lock, requirements, scriptsの229ファイルをパス順でSHA256化し、`path + space + hash`をLF連結してSHA256:
  `55BAE41392D324D55AA6FE04A3F13A70E3BC2D142A45E58BF6ECC7DE9F741577`
- .env、.bak、cacheは上記から除外。秘密値は出力せず、実環境の有効設定は未確認。
- 前回83件に対し今回84件成功。最新差分に `require_ai_preview` とsnapshot欠落互換処理が存在。前回コードと同一とは扱わない。
- 適用指示: frontend/AGENTS.mdを確認。今回frontendコード編集なし。

## 2. 完成度の定義

○=対象機能全体を必要環境まで実証、△=部分実装と局所検証はあるが販売条件未充足、×=必須経路の欠落確認、？=必要動作証拠なし。

下表18領域: **○0 / △13 / ×2 / ？3**。

要求された0〜100%値は、明示した機械的な監査指数として **36.1% = (○×1 + △×0.5) / 18 ×100**。未確認は0点だが未実装という意味ではない。0.5は採点上の規則であり、開発工数・販売成功率・実環境完成率を表さない。実環境まで完成の確認割合は0/18。旧65%等は使用しない。

## 3. 必須機能一覧

パスはrepo相対。証拠は実コード、下記回帰、明記したブラウザ確認。△の実DB/外部部分は未確認。

| ID | 機能 | 状態 | 根拠 | 問題 / 再検証 | 優先 |
|---|---|---|---|---|---|
| 01 | 登録/login/logout/初期設定 | △ | frontend authService・register/login・backend/api/onboarding.py、認証unit | UI登録入口は表示。実Auth→会社/profile→logout/期限切れは未実証 | P0 |
| 02 | 会社分離/RLS/RPC | ？ | core/auth.py,company_context.py、090001 migration、integration tests | JWT由来本人→profile会社を解決。SQL未適用、15実DBテストskip。分離できるとは断言不可 | P0 |
| 03 | Gmail OAuth/token | △ | api/gmail.py、token_vault、gmail_credentials/reconnection/revocation、unit | 暗号化/refresh/CAS/解除markerあり。実Google、旧平文移行、revoke成功→marker失敗復旧未実証/未完 | P0 |
| 04 | 新着/初回/差分メール取得 | × | api/gmail.py `_check_replies` | 既存profit_eventsのthreadのみ、既定50件・最大100・page/cursorなし。新規問い合わせが自動で案件になる入口なし | P0 |
| 05 | AI返信案/下書き | △ | reply.py GET/POST generate/draft、ReplyDraftForm、ai_usage | 保存表示と明示生成を分離、timeout・出力token・月次回数予約あり。金額予算/意味的根拠/実品質未完。保存DB E2E未確認 | P0 |
| 06 | メール送信/不明/照合 | △ | send_operations.py、090003、送信timeout/DB失敗unit | 宛先はown event/customer、送信ledger、unknown再送禁止。実Gmail受付・照合・DB確定・二重クリックE2E未確認 | P0 |
| 07 | 顧客管理 | △ | routers/customers.py、customer_resolver_service.py | own一覧/詳細/履歴あり。一覧100件制限、検索/編集/削除の一連UI未実証、find-or-create競合検証不足 | P1 |
| 08 | Timeline/履歴 | △ | gmail.py reply_log→timeline、090003送信確定RPC | 送信側transaction設計、受信側複数write。reply_log後失敗すると次回existsでskipし履歴欠損が残る | P0 |
| 09 | Leads/次の行動 | △ | api/leads.py、action_service、frontend/leads | DB一覧/優先/次actionあり。新規取込不足、正規JWTで実在A/Bを使う実行証拠なし | P1 |
| 10 | 今日の売上・利益/期間・顧客収益 | × | api/results.py、profit_events.py、core schema | 全期間actual_profit合計。売上/入金/原価/粗利を分ける台帳・日付根拠なし。不明を0へ寄せる | P0 |
| 11 | Dashboard | △ | dashboard_home_service.py→home_brief、top_actions/reply_queue | 次actionがあるだけでreply_queueに含める。要返信の意味/収益日付/根拠と表示の実証不足 | P1 |
| 12 | Stripe/試用/契約 | △ | billing service/API、090005/007、署名/逆順/旧新契約unit | test-only、実Checkout/Webhook再送/課金失敗未実証。live設定不可。全更新経路の権限制限は未完 | P0 |
| 13 | 契約/販売導線 | △ | page/guide/terms/privacy/settings/plan | 準備中表示あり。販売者/窓口未入力。削除可能と規約記載するがAPI503。保持/利用上限/委託先未確定 | P0 |
| 14 | Security | △ | service client failclosed、JWT、暗号化、CORS、unit | raw APIError経路、proxy callbackログ、全route認可/CSRF/XSS/rate limitの実環境試験なし | P0 |
| 15 | Reliability/削除/監視 | △ | gmail_work、sync_worker、/health,/ready | worker停止時lock残存、監査付き解除ツールなし。削除常時503、監視通知/復元演習なし | P0 |
| 16 | 本番構成 | ？ | runtime_settings、.env.example、RELEASE_RUNBOOK | domain/HTTPS/Google Console/Stripe live/Supabase適用/worker稼働を管理画面で未確認 | P0 |
| 17 | PC/mobile UI | △ | production build20routes、販売/login/registerのブラウザ表示 | 390pxで「を、」独立を再確認。Dashboard/Reply/Customers/Leads/Results/Settingsの認証後操作は未確認 | P1 |
| 18 | 販売E2E | ？ | integration fixture/testコード | 実Auth/DB15件skip。訪問→料金理解→登録入口まで表示確認。以後の実サービス連携なし | P0 |

## 4. P0 — 販売を止める最小タスク

| タスク | 対象ID | 必要な修正/証拠 | 完了条件 |
|---|---|---|---|
| P0-1 会社分離Gate | 01/02/14 | scoped ACL/RLS/RPCを実schema照合し隔離適用。A/B正規JWT・profile改変・再登録/並行・送信前拒否 | 正規アクセス成功、越境の情報/DB変化/外部呼出なし。unknown view/RPCを残して安全としない |
| P0-2 取得と原子保存 | 04/08 | 初回範囲を明示、pagination・永続history cursor・404復旧、message IDと会社で原子受信確定 | 51件超、新規対象商談、途中DB失敗、同頁再試行で欠落/重複なし |
| P0-3 接続/送信復旧 | 03/06/15 | plaintext移行、revoke不明、owner照合lock復旧の監査、送信SENT照合 | worker停止後に運営者復旧、unknownは再送しない。管理下Google実E2E |
| P0-4 安全境界/利用制限 | 05/12/14 | raw provider/DB error一般化、callback/proxyログredaction、会社別AI金額予算、全副作用routeの契約制限 | 外部処理前に拒否、上限超過/設定欠落/期限切れ/再試行試験 |
| P0-5 収益モデル | 10 | 見込売上・受注・入金・原価・粗利、不明null、確定日/JST、手動確認履歴を統一 | 既知fixtureの今日/期間/顧客別値がDB/API/UI一致。AI増分利益と呼ばない |
| P0-6 課金確定 | 12 | Stripe test E2E、Checkout結果不明、duplicate/逆順/契約替え、live切替failclosed設定 | 明示申込のみ課金、試用終了で自動課金なし、外部承認前はlive無効 |
| P0-7 削除・運営 | 13/15/16 | 再開可能削除、保持・外部解除・通知、backup/復元、HTTPS/CORS | 削除未完を完了表示せず、障害検知と隔離復元演習成功 |
| P0-8 外部提供/契約 | 03/13/16/18 | Google審査/ドメイン/販売者/委託先/保持/解約表示、本番設定監査 | 本人・必要専門家確認、承認済み設定で実E2E後に提供 |

## 5. P1 — 最初の3社導入前

1. 認証後PC/390pxの主要画面と送信confirm/unknown/reload/draft復元の操作検証。fixture画面と実Authを別証拠にする。
2. Leads/Customers検索・件数上限・空/error/loading・次action/元メール/分析日時を一貫表示。
3. 同期失敗/未接続/接続切れ/試用終了/支払失敗の状態をSettingsから対処可能にする。
4. 商品画面に基づく利用案内、初期3社の設定・日次運営チェック、390px見出し修正。

手動支援はオンボーディングの代替にはなるが、分離・誤送信防止・収益の正確性・定期同期の代替とはしない。

## 6. Google販売準備

コードはgmail.readonly **Restricted**、gmail.send **Sensitive**。Calendar scopeなし。[公式scope一覧](https://developers.google.com/workspace/gmail/api/auth/scopes)を2026-09-10確認。

必要なのは、公開domain/所有確認、HTTPS callback、同意画面のブランド/サポート/ホーム/同一domainのprivacy、scope用途・デモ・取得データの流れ、適切なテスト/本番project分離。Restrictedデータをサーバーで保存する現構成は追加審査・セキュリティ評価の対象になり得るため、例外を自己判断しない。[Google Restricted verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification)、[Production policy](https://developers.google.com/identity/protocols/oauth2/production-readiness/policy-compliance)（同日確認）。

Console審査結果は未確認。「未確認アプリ」警告の解消はコード修正だけで完了しない。Testingを一般販売の運用として仮定しない。ドメイン等の準備と審査資料作成はコード修正と並行可能、提出は本人承認後。

## 7. 課金販売準備

company.created_at+14日、trial終了は利用不可判定、Checkoutは明示操作。sk_test_以外拒否、live event拒否、署名/timestamp検査、同一イベントDB重複制御、最新subscription取得と保存Checkoutによる旧新契約照合を確認した。**Stripe実通信は今回なし**。

paid_until/statusはsend/sync/AIで利用するが、draft保存/actual-profit更新等に共通制限がない。継続閲覧/更新をどこまで許すかの仕様と実装を揃える。最新のDEV_ALLOW_UNMIGRATED_AI_PREVIEWは「APP_ENVがproduction以外＋missing RPC文字列」で例外許可する。さらに生成内部のrequire_useが残っており、互換入口だけで生成成功とは判断不可。staging/未設定でもdev扱いになる構成を販売環境へ持ち込まない。

実Stripeではtestmodeで、二重クリック、session作成後DB失敗、23時間超結果不明、Webhook再送/逆順/別契約、支払失敗、期間末解約、再契約を検証する。単なるモック署名成功を決済合格にしない。

## 8. Security監査（危険順）

1. **顧客間分離は実証待ち**。Service Role成功はRLS証拠ではない。migrationの11対象限定・列ACL・継承・restrictive profile境界は実装あり、実DB未知。
2. **APIエラー露出経路**。routers/dashboard.py,revenue.pyのAPIError→detail=str(exc)。engines/ai_judge.pyにraw exception格納経路。実秘密値の漏洩を確認したのではないが、例外内容に依存する危険経路が残る。
3. **OAuth/Token復旧とログ**。callback一般化・暗号化・tenant bindingは改善。provider codeを含むcallback queryをproxy/access logで落とす運用は未実証。revoke成功→DB marker失敗、旧平文移行はGate。
4. **副作用と費用制限**。送信recipientをbackendで解決する設計はある。送信test endpointはdevelopment/testなら任意宛先可能で、本番設定誤り時の防御を検証する。AI回数予約はあるが金額予算ではない。
5. **UI/リクエスト防御**。React描画に対するdangerouslySetInnerHTML検索では該当を検出しなかったがXSS合格とはしない。Bearer認証でもCSRF/OAuth state replay/CORS実ブラウザ試験は必要。SQL構造・PostgREST filter経由も実証待ち。
6. **設定境界**。service role未設定はclient生成失敗、anon client分離。productionチェックはAPP_ENVの正確な値に依存。secret値の全Git履歴検査や本番ログの監査は今回未実施。漏洩なしを保証しない。

## 9. 実行検証とE2E

| 検証 | 実行結果 | 合格対象外 |
|---|---|---|
| backend `venv/Scripts/python.exe -m pytest -q` | 84 passed / 15 skipped、2.08秒 | skipは実Supabase。SQL parser/文字列検査はDB動作ではない |
| Python compileall app/tests/scripts | exit0 | 実行時schema/外部設定 |
| frontend `npx tsc --noEmit` | 成功 | 外部API/実Auth |
| ESLint | 成功 | セキュリティ侵入試験 |
| production build | 成功、20routes | 本番起動・DB接続 |
| git diff --check | 成功 | 既存変更の正しさ保証 |
| Browser localhost3100 | server起動後に販売ページ表示、390px再確認、Login/Signup表示、未認証/dashboard→/login | 登録送信なし。認証後主要画面/実DB/Google/Stripe E2E未実施 |
| Docker/psql availability | コマンド未検出 | 隔離DB起動・復元は未確認 |

異常系の実行済み範囲はprovider代替: 送信timeout、Gmail受付後DB失敗→unknown、lock競合/例外release、batch失敗分離、AI失敗/予約上限、revoke/network failure、署名/古いWebhook現在状態/旧契約無視、refresh/reconnect。worker強制終了・OS再起動、実二重クリック/reload、Google refresh失効・実ネット切断、Stripe実重複イベントは未実証。

Browser初回はserver未起動でconnection refused。起動後新tabで表示成功。認証バイパスや本番顧客データによる確認は行っていない。Computer Useスキルに従い閲覧のみ。390pxの「を、」独立を再確認したが今回監査のため修正しない。

各画面: Sales/Login/Signupは表示確認。Dashboardは未認証リダイレクトのみ。Reply/Customers/Leads/Results/Settingsはコードとbuildのみ、認証後PC/mobile/loading/error操作は？。以前のスクリーンショットを今回の認証E2E証拠へ流用しない。

## 10. 顧客価値との照合

| 顧客の期待 | 現機能 | 評価 |
|---|---|---|
| 誰に今返すか | top_actions/Leads/reply_queue | 選別のUI入口はあるが新着取込がなく日常の網羅性不足 |
| 返信漏れ/追客忘れ防止 | 既知thread検知、worker | 50件上限/差分なしで価値を保証できない |
| 対応時間削減 | 編集/保存/明示AI生成 | 時間削減の可能性はある。利用者実測・品質比較は未確認 |
| 売上につながる行動 | next_action/reason/score | 保存分析の混在・根拠の一貫性と営業的有用性は未証明 |
| 今日の収益 | Results/actual_profit | 全期間合計と利益用語混在で要件不成立 |
| Gmail接続が怖くない | 最小scope/暗号化/確認送信 | 委託先・保管期間・解除復旧・審査説明不足 |
| 月額19,800円を払う理由 | 一連の業務支援という提案 | 価格自体は確定案だがROI/需要は未検証。回収漏れ1件・削減分数・継続利用を3社で測る |

技術的にも商品としても未完成。AI文案が出ることだけでは「利益回収OS」の価値証明にならない。

## 11. 今は作らない

LINE/電話/SMS拡張、営業先の自動探索、大量送信、無確認自動送信、多人数RBAC、会計連携、海外/英語、ネイティブアプリ、他製品統合、装飾的な分析グラフ。P2は高度な分析/支援効率化、P3は海外等。現存の未接続readyスタブ（api/ai.py等）を新機能扱いして拡張しない。

## 12. 最短販売ロードマップ

1. 検証対象working treeを固定・隔離baseline/migrationと会社分離を実証。Docker待ちの間も以下のコードを進める。
2. 初回/paging/cursorと原子受信、送信/解除/lock復旧を一本の安全な業務フローにする。
3. 今日の売上/利益の定義と台帳、全経路entitlement/AI予算、削除/監視を完成。
4. Stripe test・認証後PC/mobile UIと異常系E2E。販売文言と実装を一致させる。
5. 並行してGoogle domain/privacy/審査資料・契約表示を準備。必要な専門家に国内販売表示、特商法適用、委託/国外処理/返金条件を確認。法的結論は本監査で断定しない。
6. 外部提供条件・本番設定・backup復元が確認され、本人承認後に支援付きβ3社。未審査や越境未証明のまま有料βへ飛ばない。
7. 致命的不具合ゼロと実運営/収益照合を確認して正式販売。実績は測定値だけ公開。

## 13. 一言

**Profit Radarを販売するために残る本質的な仕事は、メールの取り込みから安全な対応・正しい収益記録までを、会社分離と障害復旧を含めて一つの実運用として成立させること。**

今回の文書変更はこの監査文書の新規作成と、SALES_READINESS_AUDIT.mdへの最新監査リンク追加のみ。既存アプリ差分は保持。ローカルNextを監査用に起動したが外部公開はしていない。
