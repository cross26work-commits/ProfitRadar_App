# Sales Release Gate — 2026-09-10

## 再開中の最新チェックポイント

**CODE INCOMPLETE**。最新ローカルpytest **138 passed / 22 skipped**、compileall成功。TypeScript・lint・build・diffは利用者の最新確認ではPASS、今回追加変更後に最終回帰を再実行する。
AI hard budget、resumable deletion、分割入金、provider review復旧は実装済み／実DB検証待ち。下記の古い未実装説明は履歴として後続更新で統合する。
Next.js16.3.4へ更新、`npm audit`および`npm audit --omit=dev`は0件。根拠: [Next.js公式security advisory](https://github.com/vercel/next.js/security/advisories/GHSA-2xp9-vwfh-vxw4)（2026-09-10確認）。
残コード: Gmail送信済み商談起点・処理量制御、認証後UI fixtureの全状態検証、保持/監視実行入口、route網羅回帰。実Supabase22件はEXTERNALでありPASSではない。

## 判定

**販売不可。CODE COMPLETEではありません。** 外部承認だけを待つ段階ではなく、下記のコード残件があります。本書は現時点の検証記録であり、販売完成証明ではありません。

## 対象

- Repository: `C:\Users\closs\ProfitRadar_App`
- Branch: `arc/profit-radar-release-readiness`
- HEAD: `3c9a83ad2264899187bd67d1ec9ccac7b8100f70`
- HEADだけでなく既存の大量の未コミット変更・未追跡コードを含めて検証。既存変更を破棄していません。
- 本番DB適用・実メール・実課金・審査提出・deploy・commit/pushは未実行。

## Gateの分離

| Gate | 結果／残件 |
|---|---|
| CODE COMPLETE | NO。同期の対象判定順序、AI予算、削除・保持、運用・認証後UIなどが残る |
| LOCAL TEST PASS | 下記の実行範囲はPASS。製品全体の合格ではない |
| REAL SUPABASE REQUIRED | EXTERNAL。実Auth/DBの19テストはスキップ |
| REAL GOOGLE REQUIRED | EXTERNAL。初回・差分・送受信・失効を実Googleで未実証 |
| GOOGLE VERIFICATION REQUIRED | 外部提供の審査状態を管理画面で確認し、必要な審査を完了する |
| STRIPE TEST PASS | NOT VERIFIED。provider代替テストのみ。Stripeテスト環境のE2Eは未実施 |
| STRIPE LIVE REQUIRED | 未設定／未許可。現コードはtest keyのみ受理。実課金禁止を維持 |
| DOMAIN REQUIRED | 本番URL・HTTPS・OAuth/Stripe redirectの確定待ち |
| LEGAL REVIEW REQUIRED | 販売者情報、保持・返金・解約条件の本人確定とレビューが必要 |
| PRODUCTION DEPLOY REQUIRED | 未実施。コード残件・隔離DB・バックアップ復元・外部Gate完了後に別承認 |

## この再開での修正

1. Gmail historyの1ページが1,000件を超えても、500件ずつ同じカーソルで保存し、最後のchunkだけページを進める。途中失敗時はページを再取得し、DB receiptで重複排除する。
2. 1,201件・途中500件保存後の失敗・残り701件の再試行・再同期0件、および2ページ目の429→同じページ再開をprovider/storage代替で検証。
3. Gmail解除の状態変更・token消去・削除が0件の場合は409で停止。成功表示せず、最初の状態変更に失敗した場合はproviderも呼ばない。
4. operator recoveryのNULL監査参照を拒否。
5. Financialsの正規JWT本人読み書き・他社拒否・version競合・日付別集計、およびoperator recoveryのowner違い・再実行の隔離DBテストを追加（環境未提供でskip）。
6. Gmail API末尾空行のdiffエラーを修正。
7. 商談候補を見つけたthreadは同一送信者・初回対象期間内に限り補完。既にnot_targetになった短文返信を再評価できるRPCに変更。過去の古いメールが新しい案件状態を上書きするのを防ぎ、mailbox変更時の成功時刻をリセット。既存legacy reply_log/event/messagesを再利用する検索を追加。SQL実動作は未検証。
8. FinancialSummary共通UIに原価・集計対象期間・期間指定・今日再取得・入力検査を追加。期間集計の入金日区別とunknown原価のテストを追加。認証後の操作は未実証。

## 既存実装を維持した範囲

初回30日・ページ・history cursor、原子的受信保存RPC、会社lock、送信operation/UNKNOWN照合、token暗号化、error boundary、runtime fail-closed、entitlement、14日試用と明示的Checkout、financial records/API/Dashboard/Resultsはコードに存在します。コード存在と実環境動作は分離します。

## 実行結果

| コマンド／場所 | 結果 |
|---|---|
| backend: `venv/Scripts/python.exe -m pytest -q` | **113 passed / 19 skipped** |
| backend: `venv/Scripts/python.exe -m compileall -q app tests scripts` | PASS |
| frontend: `npx tsc --noEmit` | PASS |
| frontend: `npm run lint` | PASS |
| frontend: `npm run build` | PASS、21 routes。DB接続証明ではない |
| root: `git -c core.safecrlf=false diff --check` | PASS |
| root: `npx --yes supabase@2.117.0 --version` | 2.117.0 |

SQLテストはpglastによる構文等の検査であり、PL/pgSQL実行・RLSの証拠ではありません。スキップを成功件数に含めません。外部AI、Gmail、決済の代替処理を実サービス合格に数えません。

## 隔離環境

Dockerコマンド、Docker service、Program Files/Dockerを確認しましたが利用可能なengineはありません。`wsl --list --quiet`もWSL未導入を返しました。CLIだけではSupabaseを起動できません。Windowsの仮想化・WSL/Docker導入は本人操作として切り分けます。

起動入口は `scripts/start-isolated-tests.ps1 -RunTests`。固定loopback54321・接続先完全一致・明示fixture書込許可・Authユーザー自動作成・通常password login JWTを利用します。本番プロジェクトへlink/push/resetしません。既存 `.local-isolated` があれば自動上書きせず停止する設計です。

## UI検証

最新production buildをloopback3102で起動。販売ページPC/390pxをブラウザ確認し、「を、」だけの孤立改行がないこと、準備中・非自動課金表示を確認しました。未認証 `/financials` は認証確認後ログインへ誘導されました。

- `screenshots/release-20260910-sales-pc.png`
- `screenshots/release-20260910-sales-390.png`

認証後Dashboard/Results/Reply/Customers/Leads/Settingsの操作E2E・390px各状態は**未確認**。販売ページ画像を認証後画面の証跡に代用しません。

## コード残件（外部待ちに付け替えない）

- Gmail: not_target順序問題はコード修正・provider代替テスト済み、DB再評価は未検証。HTMLのみ本文、初回送信済み商談起点、候補判定品質、thread補完のリクエスト量上限は未完成。
- Gmail atomic RPC: legacy再利用・mailbox成功時刻リセットはコード修正済み・実DB未確認。詳細なrollback/復元演習が必要。
- Token: Google revoke成功後DB更新失敗→再試行で既失効400となる復旧は未完成。今回の0件検査だけでは解消しない。
- AI: 月生成回数上限と使用token計測はあるが、費用hard limit・全AI経路統合・未確定金額の意味的根拠・同時実行制限は残る。
- Entitlement: mutation gateは存在。GET OAuth開始/callback等の副作用経路とread-only保持期限の整合、全登録routeの回帰テストが残る。
- Financials: 単一案件の累積記録モデル。期間指定UIは追加・build済み。分割入金の日付別履歴、顧客集計UI、認証後操作、DB実証は残る。旧actual_profitは新受注額に自動変換しない。
- Account deletion: 現在503で安全停止。resumable job、Google revoke/Stripe参照/データ削除と保持、監査、途中復旧はコード未完成。
- Billing: Stripe test E2E、契約置換・結果不明復旧の実サービス検証、live切替を別承認で有効化する設定が残る。
- 監視・障害通知・保持scheduler・復元演習・認証後UI状態fixture・運営手順の整合が残る。

## マイグレーションと復旧

`202609100002_atomic_gmail_sync.sql`、`003_operator_recovery.sql`、`004_financial_records.sql`および前段の未適用migrationを隔離baselineへ順に適用して検証する必要があります。ユーザー追加の`202609100001_repair_runtime_schema.sql`は保持。

未commit transactionのエラーrollbackと、commit後の復旧は別です。commit後は新規データの保存・整合と対象ACL/RLS/関数定義等のバックアップが必要で、監査SELECTだけで完全復元できるとは保証しません。本番適用は承認前に実行しません。

## 次の再開位置

同期のthread補完による処理量上限・HTML/初回送信済み商談の不足を扱い、AI budget、削除job、financial顧客集計UI/部分入金、entitlement全route、Stripe/認証後UI、運用を継続。not_target救済・legacy再利用・operator/financial RPCは隔離DBで再検証する。Docker待ちは実DB検証だけの阻害事項です。

## 販売開始まで

コード残件→ローカル全回帰→隔離Supabase19件以上の実証と復元演習→テストGmail/Stripe E2E→Google審査・ドメイン・法務条件→本番適用/公開の明示承認→本番read-only smoke→初期3社への設定支援。現時点で有料販売開始を承認できる証拠はありません。
