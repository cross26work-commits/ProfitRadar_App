# 隔離UI表示検証
2026-09-11。実client component + 架空API。実Auth/DB/Google/Stripeではない。
loopback3190、CSP connect-src none。製品側へ認証bypassを追加していない。

| 範囲 | 観察・操作 | 限界 |
|---|---|---|
| Reply draft | 入力→保存→reload復元、UNKNOWNで送信不可 | sessionStorage fixture、実DBではない |
| Gmail settings | 未接続、最終同期、失敗表示、再試行503を一般化しbusy解除 | OAuth/同期を実行していない |
| Plan | 支払失敗、契約説明、checkbox同意後も新規Checkout disabled | 390px/1440px確認、実決済なし |
| Financials | subject付き案件選択、分割入金フォーム表示 | fixture writeは拒否、実永続化未検証 |
| Dashboard/Customers | 架空tenant表示と主要表示 | 全状態・全幅の網羅未完 |
| Leads/Results/Settings | fixtureスクリーンショット保存 | 保存だけの画像もあり全PASSとはしない |
| Lead詳細 | server component実Auth経路 | fixture未対応・未確認 |

画像: screenshots/fixture-*.png。full-page captureではsticky header/navが現在のscroll位置に写る場合がある。
今回の新しい確実な画像: fixture-mail-disconnected-390.png、fixture-plan-payment-failed-390.png、fixture-plan-payment-failed-pc.png。
次はnormal/empty/loading/error/limit/expired/UNKNOWNを各操作経路ごとに確認し、未実装fixtureを通信エラーとして誤判定しない。
