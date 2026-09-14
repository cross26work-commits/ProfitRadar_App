# 販売実装 継続チェックポイント
更新: 2026-09-14 JST

## 保持する状態
Repository C:\Users\closs\ProfitRadar_App
Branch arc/profit-radar-release-readiness
HEAD 3c9a83ad2264899187bd67d1ec9ccac7b8100f70
全未コミット/未追跡変更が成果物。既存backup/logを保持、秘密値を読出し・転記しない。commit/push・本番変更・実送信・実課金・公開なし。

## 最新判定
CODE COMPLETE / EXTERNAL REQUIRED。根拠と限界は SALES_RELEASE_FINAL.md。
178 passed / 25 skipped、compileall/pip check/pip-audit/TS/lint/build/npm audit/diff PASS。
Server API Node tests 2 passed。25件は RELEASE_SKIP_CLASSIFICATION.md に全件掲載。skipは実Auth/DB合格に含めない。
Google Fontsのbuild時ネットワーク障害をOSフォント化で解消し再build成功。

## 実装済み
AI予算予約/hard limit、resumable deletion、Gmail初回30日/page/history/atomic cursor、SENT起点、send operation/UNKNOWN、Draft復元、分割入金/JST集計、entitlement、Checkout recovery。
加えて、詳細表示view共有と安全なServer APIエラー、Stripe production設定/DB gate、Gmail再接続競合DBtest、件数のみ監視通知、隔離restore演習コード。
Stripe gateのmigration 202609110001は未適用。test既定/live無効のまま。

## UI検証
11 routesのPC/390px fixture表示と画像保存。編集→保存→reload→確認→fixture送信→Financials保存を確認。
UNKNOWN・支払失敗・同期失敗・未接続もfixture操作確認。本物Auth/DBとは区別。
全画像の個別目視、全状態組合せは網羅していない。次の実環境E2Eで追加確認し、問題はコード課題へ戻す。
fixture: frontendで node tests/ui/serve.mjs、loopback3190。ユーザー既存8001/3001プロセスを停止しない。

## 次の作業（承認境界を維持）
1. Docker/WSLが利用可能になったら scripts/start-isolated-tests.ps1 -RunTests。fixtureがA/Bユーザーと正規JWTを自動作成。無許可共有DB接続禁止。
2. 全25実DBケースの実行と修正。SQL構文PASSだけでは適用成功を断定しない。
3. 新規隔離DB限定restore演習（RELEASE_RUNBOOK参照）。現状Docker未導入で未実行。
4. 承認された管理下Google E2EとStripe実test E2E。実送信は直前再承認、live keyや実課金は禁止のまま。
5. 法務/ドメイン/Google審査/通知先/保持条件をOWNER_ACTIONSで確定。
6. 本番schemaのreadonly照合→復元可能backup→別承認→migration/設定/公開。
新たなコード欠陥が出ればCODE COMPLETEを撤回し、修正と全回帰を行う。

## Migration/復旧
202609100002は未適用前提で編集済み。既適用先にはforward差分が必要。005〜008および202609110001等も今回本番適用していない。
監査SQLだけではcommit後の完全復元を保証しない。ACL/列権限/RLS/関数owner・定義と検証済みbackupを保管。
解除/recoveryの単純な時間経過再実行は禁止。全writer停止と証跡review、operator/ticket記録が必要。
