# 販売実装 継続チェックポイント
2026-09-15 JST

Repo C:\Users\closs\ProfitRadar_App
Branch arc/profit-radar-release-readiness
HEAD 27d6ec0777e7019a3319cbd273999d84b18b2a5f
既存未コミット変更を保持。commit/pushなし。過去migrationを変更しない。

## 現在地
新規 202609140001_remote_schema_forward.sql 完成、ローカル検証済み、remote未接続。
SHA256とobjects/ACL/依存・適用前後チェックリストは REMOTE_SCHEMA_FORWARD_REVIEW.md。
現在のremote適用判定は「適用禁止」：ユーザーがまだ適用を承認しておらず、実remote定義との最終照合も未実施。
コード準備と外部GateはSALES_RELEASE_FINAL.mdで区別。

## 最新実行
Backend212 passed/0 skipped、integration31 passed/0 skipped。
Frontend Node5、tsc/lint/build/npm audit PASS。
Forward validator fresh/旧schema相当/再実行PASS、conflict rollback10/10、billing=test。
restore演習54 tablesのschema/ACL/件数一致とsource不変PASS。
実Google/Stripeは未実施。SDKの非推奨警告6件はFAILではないが今後対応対象。

## 今回修正
- Service Roleのdefault由来ALLを対象10内部tableだけ最小権限へ限定。
- NULL/[] pending_ids契約、RPC迂回拒否を実DBテスト追加。
- restore unitを最新checkpointに追従。
- SQLの厳密UTF-8・元日本語literal一致テスト追加。
- next.configの固定BackendをBACKEND_ORIGINへ変更。developmentのみ127.0.0.1:8000既定。
- productionではBACKEND_ORIGIN/NEXT_PUBLIC_API_BASE_URLに明示HTTPS originが必要。既存.envは未編集。

## 次の再開
1. remote接続/metadata確認の明示承認を得る。現時点でSQL Editor、db pushは禁止。
2. preflightの個別SELECT、schema/関数全文/ACL backup、復元手段、作業窓を人間が確認。
3. 差異があればforwardを修正してローカル全回帰。過去SQL再適用や不明policy削除は禁止。
4. 別途適用承認後、新SQL一本を新しいsessionでtransaction適用。エラーなら停止/rollback確認。
5. 適用後チェックリストを実施。Gmail/課金/Cron/公開へ勝手に進まない。

## 隔離環境
Dockerはユーザーインストール:
C:\Users\closs\AppData\Local\Programs\DockerDesktop\resources\bin
固定project/container profit-radar-disposable、loopback54321/54322。
validate_forward_localは新規pr_forward_* DBのみ作成し保持。既存DBをresetしない。
restoreは新規pr_restore_* DBに限定。証跡は保持、無断削除しない。
.local-isolated-failed-* / .local-isolated-old-* はcommit対象外。git add .を使わない。
検証buildの.nextは仮URL入りなので公開不可。本番設定を確定して再buildする。
