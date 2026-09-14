# Sales Readiness Backlog

> 最新実装状態とコード残件は [追加チェックポイント](SALES_COMPLETION_CHECKPOINT_20260909.md)。送信ledger・scheduler worker・test billing・明示AI生成・販売UIを追加したが、販売可否/P0完了判定は変更しない。差分同期、削除、費用上限、実環境E2Eは未完。

現在: Token marker/reconnect・AI文字数/token/時間・金額単位・旧新契約照合を追加し83unit/static passed、15実DB skipped。優先再開はC04/A04初回・差分同期と受信確定の原子性。その後C03残障害復旧、D03費用予算、F02削除、E01成果区分。全てコード残件でありDocker待ちによる停止対象ではない。

2026-09-09継続更新: 販売完成/P0完了ではない。最新差分・10領域の状態・次作業は `SALES_IMPLEMENTATION_CONTINUATION.md`、本人操作は `OWNER_ACTIONS.md`。下書きは仕様判断待ちを解除し、保存/復元を実装済み・実DB検証待ち。定期同期は引き続きP1必須で、下記P2の手動案は販売要件充足ではない。

## P0: 顧客データを扱う前

| ID | 対象 | 実装・依存 | 完了条件 / 検証 | 規模・不確実性 |
|---|---|---|---|---|
| B01,G02 | Supabase RLS/RPC/migrations | 明示11 table対象のaudit SQL/migration、skip付きJWT testを追加済み。次は隔離Supabaseへ適用 | A/B JWT越境全否認、API越境、onboard再実行/並行、backup restore演習 | M / 実DB依存 |
| C02,C03 | Gmail token | encryption key/KMS、legacy移行、revoke状態 | token非露出、revoke mock、rotation手順 | L / provider依存 |
| C01 | Google公開審査 | consent screen、privacy disclosure、verification/security assessment | Google側承認または販売停止判断 | L / 外部審査 |
| B04,G01 | API/production | generic error、CORS env、HTTPS deployment runbook | production-like smoke | M |
| G03 | 法務表示 | 事業者/問合せ/保存/国外移転/料金を実運用に一致 | 法務レビュー済みページ | M / 判断依存 |

## P1: 初期有料提供まで

| ID | 対象 | 実装・依存 | 完了条件 / 検証 | 規模・不確実性 |
|---|---|---|---|---|
| F01 | Billing | provider subscription、trial、署名検証webhook、server entitlement | 試用→課金→失敗→解約の順序逆転試験 | L |
| C04,C05,A10 | Gmail運用 | cursor/pagination、company lock、operation id、retry/recovery | 同一message/sendの再試行で二重なし | L |
| D01,D04,E01 | Analysis/Results | one-call JSON snapshot、revenue/cost/profit schema、UI mapper | 金額red-teamと履歴整合E2E | L |
| F02 | Deletion | transaction RPC、sole-member guard、retention workflow | rollback/multi-member test | L / schema依存 |
| D02,D03 | AI safety | injection guard、limits、timeouts、latency/cost metrics | adversarial fixtures、cap test | M |
| G04 | Operations | alerting、structured redacted logs、backup/restore runbook | intentional failure drill | M |

## P2: 初期3社では手動運用で代替可能

| ID | 手動代替 | 担当・手順・影響 |
|---|---|---|
| A04 | 同期ボタン運用 | **P1の定期同期が未完の間だけの運用代替**。運営者が毎営業日、各社の接続/同期失敗を確認。販売仕様を恒久的に縮小するものではない。 |
| A09,C06 | Gmail thread実証 | 運営者が各社1件の管理下メールで送受信・threadを確認。実顧客への試験送信は禁止。 |
| E02 | 成果確定 | 顧客が受注/入金/原価を手動記録。AI寄与としては表示しない。 |

## P3: 販売後

- orphan返信専用キュー、複数member権限、国際化、会計連携、LINE/電話、より高度な分析。

## 最小修正順序

1. P0のRLS/Google/token/production設定を実環境で確定する。
2. P1のGmail冪等性と課金entitlementをserver側で実装する。
3. revenue/cost/profitとAI snapshotを統合する。
4. 管理下テストで全E2E、次に3社オンボーディングを手動支援する。
# 最新再開位置 2026-09-10

最新状態・コード残件は`SALES_RELEASE_FINAL.md`。同期chunk保存、not_target再評価、legacy再利用、解除0件検査、financial/operatorの実DB用テストを追加。112 local pass / 19 DB skip。AI budget・削除job・認証後UI・運用を未完了のコード作業として維持し、Docker待ちを理由に外部待ちへ変更しない。
# 最新検証結果の補正

最新は **113 passed / 19 skipped**（2026-09-10）。FinancialSummary期間指定・原価表示追加後もTypeScript / ESLint / production build成功。以下の112件は直前チェックポイントの履歴。実DB・認証後UIは未実証。販売不可。詳細はSALES_RELEASE_FINAL.md。
