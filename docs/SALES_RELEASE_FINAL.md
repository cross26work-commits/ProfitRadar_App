# Sales Release Gate
更新: 2026-09-14 JST

## 判定
**CODE COMPLETE / EXTERNAL REQUIRED**（今回確認したコード上の販売阻害について）。販売開始の許可ではない。
- 確認済み未解消 P0 CODE DEFECTS: 0
- 確認済み未解消 P1 SALES-BLOCKING CODE DEFECTS: 0
- LOCAL TEST FAILURES: 0
- LOCAL UNJUSTIFIED SKIPS: 0
この判定は欠陥が存在しない保証ではない。実DB適用・正規Auth・外部provider・本番運用の合格とは別で、下記外部Gateは未合格。

## 検証対象
Repository: C:\Users\closs\ProfitRadar_App
Branch: arc/profit-radar-release-readiness
HEAD: 3c9a83ad2264899187bd67d1ec9ccac7b8100f70
HEADだけでなく既存未コミット・未追跡の実装を含むworking treeを検証。既存変更は保持。
commit/push、本番DB変更、実メール、実課金、Cron登録、deployは未実施。

## 今回閉じたコード残件
- 詳細画面の旧利益フォーム、固定SMS案内、生のServer APIエラーを除去。認証JWT、404/401誘導、安全なerror boundaryをテスト。
- 返信編集→保存→reload→確認ダイアログ→fixture送信→成果入力を接続。送信UNKNOWNは保持して再照合、自動再送しない。
- Stripe test/live切替は設定・DBモード・明示承認reference・HTTPS・provider livemode・画面expected_modeでfail closed。既定test。実live有効化なし。
- Gmail解除復旧と再接続の競合、および課金モード切替拒否の実DBテストを追加（未実行）。
- monitoringは件数のみのopt-in通知、restoreは専用ローカルDockerの新規DB限定。単体検証と実演習を分離。
- build中Google Fonts取得失敗を確認し、ビルド時フォントダウンロードを除去。OS標準日本語/欧文フォントへ変更して再build成功。
- 未認証/不正Bearer/Basicのonboarding HTTP拒否3件をローカルで実行。DB/provider未呼出も検査。

## 最終ローカル実行（2026-09-14）
| コマンド（各ディレクトリから） | 結果 |
|---|---|
| backend: venv/Scripts/python.exe -m pytest -q -rs | **178 passed / 25 skipped** |
| backend: venv/Scripts/python.exe -m compileall -q app tests scripts | PASS |
| backend: venv/Scripts/python.exe -m pip check | PASS |
| backend: venv/Scripts/python.exe -m pip_audit --progress-spinner off | 既知脆弱性なし |
| frontend: node --test tests/server-api.test.mjs | 2 passed / 0 skipped |
| frontend: npx tsc --noEmit | PASS |
| frontend: npm run lint | PASS |
| frontend: npm run build | PASS、21 routes |
| frontend: npm audit | 0 vulnerabilities |
| root: git -c core.safecrlf=false diff --check | PASS |

25件全件分類: [RELEASE_SKIP_CLASSIFICATION.md](RELEASE_SKIP_CLASSIFICATION.md)。
依存監査は確認時点の既知advisoryのみ。SQL構文テスト、provider/storage代替成功をDB/Gmail/Stripe E2E成功へ加算しない。

## UI証拠と限界
実component＋架空API、CSP connect-src noneのfixture。本番の認証bypassは追加していない。
Dashboard / Reply / Customers / Leads / Results / Financials / Settings / Plan / Mail / Lead詳細 / Customer詳細をPC・390pxで読み込み、主要見出しを確認して画像保存。
編集保存・reload復元・確認表示・fixture送信・Financials保存、UNKNOWN復元、同期失敗、未接続、支払失敗時の申込拒否を操作確認。
docs/screenshots/gate-*.png、fixture-*.png。画像の一括保存と個別目視は区別し、全画像・全状態組合せの目視合格とはしない。
本番のログインから課金までの通しE2E、実データ/ネットワーク障害時の表示は未検証。販売ページの準備中は維持。

## 外部Release Gate
| Gate | 状態・解除条件 |
|---|---|
| REAL SUPABASE REQUIRED | 25 skipped。Docker/WSL準備後、隔離baseline・全migration・正規JWT・RLS/RPC/atomicity/競合を実行。実schemaとの差分確認も必要 |
| DOCKER RESTORE REQUIRED | 演習コードあり。Docker不足で実dump/restore未実施。単体成功は復元証拠ではない |
| REAL GOOGLE REQUIRED | 管理下OAuth・移行/rotation/refresh/revoke・同期・送受信・UNKNOWN照合。別承認なしに送信しない |
| STRIPE TEST REQUIRED | 代替処理のみ。実test-modeでWebhook再送/順序逆転/失敗/解約/再契約/UNKNOWNを実施 |
| GOOGLE VERIFICATION REQUIRED | 本人の審査状態と外部提供条件の確認 |
| STRIPE LIVE REQUIRED | 本番設定gateは実装済み・無効。実test E2Eと別承認後にのみ移行 |
| DOMAIN REQUIRED | URL、HTTPS、OAuth redirect、CORSの実環境整合 |
| LEGAL REVIEW REQUIRED | 販売者情報、問い合わせ、保持/返金/解約の確定 |
| PRODUCTION DEPLOY REQUIRED | 全Gate確認、backup、通知到達、独立死活監視、適用・公開承認 |

## P1/P2と再開条件
既知の販売阻害コード残件はない。実DBやproviderで欠陥が発覚した場合はコード課題へ戻し、この判定を更新する。
UI全状態の網羅・全画像目視は追加QAであり実施済みとしない。実環境E2Eで主要操作に問題が出れば販売阻害として扱う。
運用・適用: RELEASE_RUNBOOK.md。本人操作: OWNER_ACTIONS.md。
新SQLを本番適用していない。202609100002が既適用の環境にはforward差分が必要。commit後復旧をtransaction失敗時rollbackと混同しない。
