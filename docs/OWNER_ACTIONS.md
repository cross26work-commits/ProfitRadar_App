# 本人操作と外部環境
2026-09-14。最新Gate: SALES_RELEASE_FINAL.md。過去版はhistory/OWNER_ACTIONS_before_20260911.md。
未完コードはSALES_IMPLEMENTATION_CONTINUATION.mdで管理し、本人待ちへ付け替えない。

## 隔離DB
Docker engineとWSL/仮想化の準備が必要。CLI2.117.0だけではSupabaseは起動できない。管理者操作・再起動は本人判断。
準備後、repo rootで powershell -File scripts/start-isolated-tests.ps1 -RunTests。
専用loopback54321、明示許可とURL照合、架空Authユーザー・通常login JWTを自動準備する設計。JWT手作業取得・チャット共有不要。
現在25 tests skipped。全件分類はRELEASE_SKIP_CLASSIFICATION.md。baseline/migration/正規JWT/RPCを実行した証拠はない。通信/SQL失敗はskipへ変換して成功扱いしない。
本番や共有DBを隔離先に指定しない。既存.local-isolatedの削除を自動承認しない。

## GoogleとToken
OAuth設定・外部提供審査状態を本人が確認する。gmail.readonlyはRestricted、gmail.sendはSensitive。テスト設定を一般販売可能と仮定しない。
鍵はsecret storeで保管・backup。旧平文tokenを新コードは拒否するため、移行/rotation/reconnect/refresh/revokeの隔離演習前に反映しない。
backendから python -m scripts.migrate_local_gmail_tokens はローカルdry-run既定。--applyも専用隔離限定。
本番token移行は別承認と復旧計画が必要。secret/token/JWT/メール本文をログや報告へ出さない。
実Google E2Eでは本人管理の送受信先と内容を別途確認し、送信直前の承認を得る。

## Stripe
現設定はtest既定。production切替gateは実装済み・未有効化。月額JPY19,800、month/interval_count1、税込inclusive Priceをテスト環境に用意する。
secret/key/webhookはBackendだけへ注入。14日試用はアプリ管理、終了時自動課金なし。
実Stripe testの重複/順序逆転/支払失敗/解約/再契約/UNKNOWNが未実証。
live切替はRELEASE_RUNBOOKの設定・DB approval一致と実test E2E、別承認が必要。test履歴があるDBの安易な昇格は拒否する。live呼出/実課金禁止を維持。

## 運営・契約で本人が決めること
- 販売主体、所在地、問い合わせ先、ドメイン、HTTPS、公開URL。
- 保持日数、解約後の閲覧期限、返金/削除/backup保持の条件。未確定内容を契約として公開しない。
- AI会社別月token/USD上限と許可modelの保守的最大単価。設定例の空欄はfail closed。原価の実測ではない。
- ACCOUNT_AUDIT_RETENTION_DAYSと保持削除の承認。日数は削除完了から起算、未完jobは期限削除しない。
- 障害通知の受け先、当番、backup復元演習日。maintenanceはreadonly既定で外部通知接続は未証明。
- Google外部提供条件と法務レビュー。販売準備中表示は維持。

## 承認が必要な境界
本番DB適用/削除、実メール、実課金、公開、cron登録、審査提出は未実行。別承認前に進めない。
schema/ACL（列権限・継承・関数owner/EXECUTE・RLS含む）を安全に退避し、backup復元可能性を確認する。
SQL audit出力だけではcommit後の完全復元を保証できない。新規migration002が既適用ならforward差分が必要。
手順はRELEASE_RUNBOOK.md、operator復旧はOPERATOR_RECOVERY.md。
