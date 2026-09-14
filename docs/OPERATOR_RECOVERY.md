# Operator recovery / retention — 2026-09-11

未デプロイ・未登録。本番操作は別承認。秘密値はEnvironmentFile等に注入し、コマンド引数・ログ・チャットへ出さない。以下のコマンドはbackendディレクトリで実行する。

## 原則

- API・workerの全writer停止と、provider処理が継続していないことを人間が確認する。経過時間だけでlockを解除しない。
- `python -m scripts.recover_company_work --company <UUID> --expected-url <対象URL>` は状態確認のみ。ownerが一致し、全worker停止後だけ、operator/ticket/ownerと`--workers-stopped --apply`を指定する。
- 復旧RPCはsendingをunknownへ移す。送信はしない。UI「送信済み照合」で確認し、不明メールは再送しない。

## AI結果不明

`python -m scripts.resolve_provider_uncertainty --kind ai --company <UUID> --expected-id <reservation UUID> --expected-url <対象URL>`

既定はid/statusの読取りだけ。providerダッシュボード・処理終了・請求可能性を確認し、全worker停止後に`--apply --workers-stopped --provider-reviewed --operator <担当参照> --ticket <障害参照>`。reservedをreviewed_unknownへ変更し監査記録を追加する。予約token/費用は返却しない。RPCはservice_roleのみ、既存company lockがあれば拒否。

`AI_MODEL_MAX_RATES_JSON`のinput/outputはモデルごとのUSD/百万token上限単価。公式単価以上を運営者が設定し、モデルを固定する。`AI_COMPANY_MONTHLY_TOKENS`と`AI_COMPANY_MONTHLY_USD`の両方を設定。未設定・未知model・DB予約失敗は503。超過・未解決予約は429。予約は実請求額ではなく保守的上限で、月内上限引上げはRPCが拒否する。input token count後、最大出力2048を予約し、provider retryは0。請求上限は設定単価の正しさが前提。

## Gmail revoke後のDB障害

Googleの400を成功扱いしない。Googleアカウントの第三者アクセスから対象OAuth許可が削除済みであることを本人が確認する。全writer停止後、上記CLIを`--kind gmail-revoke --expected-id <接続UUID>`で使用。`revocation_pending`かつ同じ接続IDだけ削除し、監査する。再接続済み・id変更は拒否。providerへ送信・revoke再実行はしない。

## Account deletion

request→providers→DB一括削除→Auth削除→completed。契約未終了・未解決send/AI予約は停止。Gmail失効・DB削除・Auth削除のどこで失敗しても完了扱いにしない。

`python -m scripts.resume_account_deletion --job <job UUID> --expected-url <対象URL>`で確認し、削除の既存申込・対象を確認した後だけ`--apply`。他社データを対象にしない。Auth失敗後はDB削除を再実行しない。保存する監査はuser/company UUID・段階・請求参照・時刻で、メール本文/tokenは含めない。

保持日数は`ACCOUNT_AUDIT_RETENTION_DAYS`で本人確定。監査保持は完了時から当初指定の日数。未完jobは期限で削除しない。DBバックアップやGoogle/Stripe側の保存はアプリ削除と別で、本人確定の規約・バックアップ期限が必要。

## Monitoring / retention execution

`python -m scripts.maintenance --expected-url <対象URL>`は4種類の件数のみ出力する。unresolved_sends/pending_deletions/reserved_ai/old_company_locksの非0を運営者確認対象とする。古いlockも自動解除しない。query失敗はexit1、本文・credentialを出さない。

期限到来したcompleted監査のみの削除は、保持規約確定後に`RETENTION_SWEEP_APPROVED=true`と`--apply-retention`の両方が必要。本作業では実行していない。顧客行・未完job・Gmail送信を変更しない。

`deploy/`のsystemdサンプルは配布ファイルのみ。パス・OSユーザー・秘密設定ファイル所有権を環境に合わせてレビューする。登録/enable/startは別承認。監視サービスは読取りのみ。運営者通知先への連携・異常通知到達・ホスト再起動後の継続稼働は本番前Gateで未検証。

## Migration

002のpending_ids/pending_pageと送信済み取込、005〜008が必要。これらのSQLは本番未適用。既存002適用環境がある場合、ファイル再実行で更新されると仮定せず差分forward migrationを作ること。隔離baselineへ全migration適用→22以上の実DB/JWTテスト→復元演習を先に完了する。
