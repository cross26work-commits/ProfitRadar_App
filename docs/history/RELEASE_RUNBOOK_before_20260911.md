# Profit Radar 公開・検証・復旧・運営手順

2026-09-09。**未公開、販売Gate BLOCKED**。これは適用承認ではない。コード残件は `SALES_COMPLETION_CHECKPOINT_20260909.md`。本番に新migrationを適用しない。

## 1. ローカル回帰

PowerShell、repo rootから:

```powershell
Set-Location backend
venv/Scripts/python.exe -m pytest -q
venv/Scripts/python.exe -m compileall -q app tests scripts
Set-Location ../frontend
npx tsc --noEmit
npm run lint
npm run build
Set-Location ..
git -c core.safecrlf=false diff --check
```

pytestはbackendから実行する。rootから直接実行するとapp importに失敗する。通信/収集失敗は合格に数えない。pglast v8.4でSQL grammarを検査したがPL/pgSQL・権限動作を証明しない。実行可能なtest requirementsに含めて再現する。

## 2. 隔離DB/Auth

本人がDockerエンジン/仮想化を準備した後、repo rootで:

```powershell
./scripts/start-isolated-tests.ps1 -RunTests
```

- CLI 2.117.0、`.local-isolated`専用、loopback54321のみ。既存directoryがある場合は停止し、内容確認なしに削除しない。
- baseline overlayと全migrationを空のローカル環境へ適用する設計。まだDocker不在で実行未証明。
- fixtureは架空A/B、通常Auth password loginでJWTをメモリ取得。メール/AIは代替処理。秘密値を出力・保存しない。
- A/Bの正例、実在BへのA越境、DB42501、profile改変、onboard再実行/並行、send claim並行/確定再実行を確認。skipは合格外。
- SET ROLE追加とbackup restore演習はコード/検証残件。productionへのlink/db pushは禁止。

## 3. 外部テスト前提

暗号鍵、Supabase service key、Google OAuth secret、Stripe test key/webhook secretを安全な環境設定で渡す。Frontendにはpublic URL/anon用途以外の秘密値を渡さない。設定例はbackend/.env.example。

Google Consoleのscope/redirect/審査は本人確認。未審査テスト設定を有料顧客へ流用しない。Gmail readonlyはRestricted、sendはSensitive。旧平文tokenは新コードが拒否するため、隔離移行/rotation/reconnect/refresh/解除演習前に本番更新しない。

Stripeは現コードtest-only。JPY 19,800、monthly、税込Priceを用意。14日試用はアプリ内、終了時自動課金なし。本人がCheckoutを選択した場合のみtest session作成。test webhook署名/重複/逆順/旧新契約競合/解約/支払失敗を確認してからlive gateを別途実装・承認する。

## 4. Scheduler構成（まだ登録しない）

独立workerとして `backend/scripts/sync_worker.py` をBackendと同じ信頼境界内でプロセス管理する。`SCHEDULER_BACKEND_URL`と`GMAIL_SCHEDULER_SECRET`を設定し、専用secretをbackendとworkerに同じ値で注入する。Browser JWTは不要。約300秒周期、timeoutあり、redirect禁止。

実装されているのは既知案件のbatch返信検知。初回取得/paging/history cursor/失効回復が未完なので、worker起動だけで同期完成としない。1会社の失敗は他社へ波及しない。`gmail_sync_runs`とsafe summaryで監視する。

## 5. 不明送信とロックの復旧

- Gmail受付後のtimeout/DB失敗はunknown。同じ内容を自動再送しない。
- UI「送信済み照合」で固定Message-ID、From/To/件名/SENTを照合。一致不足ではunknownを維持。
- Gmail実画面/テスト宛先受信とDB証跡を本人が確認するまでは手動再送もしない。
- company work lockは自動期限解除しない。停止/再起動後は全worker/APIの対象処理停止を確認し、owner ID・purpose・取得時刻・send operationを安全な管理経路で照合する。単に古いという理由で解除しない。
- 停止確認後のservice-only release RPC操作は監査記録を残し、既存送信operationは削除しない。自動運営ツールは未実装。
- Checkout作成結果不明は同一attempt IDで再試行。23時間超は停止しStripe test側で照合する。新sessionによる二重契約を作らない。

## 6. Migration適用と復旧Gate

1. 対象環境を特定し、顧客行を取得しないaudit SQLでschema/ACL/RLS/functions/index/重複件数を確認。
2. table名や既存objectが不一致なら停止。隔離overlayは本番用migrationではない。
3. 復元可能backupとschema/ACL（列grants、role inheritance、RLS、関数所有者/EXECUTE、view/trigger依存含む）を安全に退避。復元演習が成功していなければ適用禁止。
4. 本人承認後だけtransaction適用。失敗時はrollbackを確認。途中で別SQLを継ぎ足さない。
5. commit後の問題はforward fix優先。監査出力だけで完全復旧できると断定しない。新規証跡を壊すDROP禁止。
6. A/B JWT正規・越境、RPC、service/table、件数、/health、/readyを確認してからアプリ切替。

## 7. 公開前と初期3社運営

- コード残件を完成し隔離DBと管理下Google/Stripe test E2Eを通す。
- 販売者・問い合わせ・保持/返金・利用条件/プライバシーを本人確定。未入力情報を捏造しない。
- HTTPS/CORS/本番secret/Google外部提供条件を確認、監視通知と復元演習を実装・実施。
- 本人承認後だけ本番migration/公開。試用→明示契約→解約まで各社設定支援を行う。
- 毎日担当者が同期失敗/滞留lock/unknown送信/課金失敗を確認する案。通知・削除・保持が未完成のため、この手動案だけで販売要件充足としない。

## 参考（2026-09-09確認）

- [Gmail message list / rfc822msgid検索](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/list)
- [Stripe Checkout session](https://docs.stripe.com/api/checkout/sessions/create)
- [Stripe Webhookの順序・再送](https://docs.stripe.com/webhooks)
- [OpenAI Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create)

SDKのtimeout/出力上限・usageを確認して実装した。記録tokenは取得済み応答分のみ。費用や5秒以内を保証しない。
# 2026-09-10優先する検証状況

`SALES_RELEASE_FINAL.md`を最新Gateとする。112 local pass / 19 real DB skip。`202609100002`〜`004`は隔離適用未検証で本番適用禁止。CLI2.117.0確認済み、Docker/WSLなし。隔離起動は`powershell -File scripts/start-isolated-tests.ps1 -RunTests`。operator復旧は全writer停止・owner照合・監査参照を必須にし、UNKNOWNを自動再送しない。transaction内失敗のrollbackとcommit後復旧を混同しない。販売準備中表示を維持する。
# 最新検証結果の補正

最新は **113 passed / 19 skipped**（2026-09-10）。FinancialSummary期間指定・原価表示追加後もTypeScript / ESLint / production build成功。以下の112件は直前チェックポイントの履歴。実DB・認証後UIは未実証。販売不可。詳細はSALES_RELEASE_FINAL.md。
