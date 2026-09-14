# Sales Release Gate
更新: 2026-09-15 JST

## 判定
コード準備: **CODE COMPLETE / EXTERNAL REQUIRED**。
remote適用: **適用禁止（現在の承認範囲・remote事前確認未完了）**。
ローカル検証は販売開始やremote適用成功を意味しない。詳細/適用前後チェックリスト/commit候補は REMOTE_SCHEMA_FORWARD_REVIEW.md。

## 検証対象と変更
Repo C:\Users\closs\ProfitRadar_App
Branch arc/profit-radar-release-readiness
HEAD 27d6ec0777e7019a3319cbd273999d84b18b2a5f
既存working treeを保持。新規forward一本を追加、過去migration変更なし。
前段でSupabase default privilege由来のService Role全権限残存を検出し、一時CODE COMPLETEを撤回した。対象10内部tableの権限を必要範囲に限定するforwardと実DB拒否テストで修正・再検証。
最新checkpointのrestore手順へテストを追従。新規DB以外を初期化しないことを追加検査。
Frontend rewriteのlocalhost固定は本番で不適切なため環境変数化・production fail closedを実装。

## 最新結果
| 検証 | 結果/範囲 |
|---|---|
| Backend全pytest（隔離Auth設定あり） | **212 passed /0 skipped**、SDK DeprecationWarning 6件 |
| integration | **31 passed /0 skipped**（全回帰にも含む）。27 DB/Authケース＋4接続先guard |
| UTF-8/forward grammar/restore関連 | 31 passed（全回帰の部分集合） |
| compileall | PASS |
| pip check / pip-audit | 前段PASS、既知脆弱性なし。依存変更なし |
| Frontend Node tests | 5 passed（origin設定3＋Server API2） |
| TypeScript / ESLint / production build | PASS、21 routes |
| npm audit | 0 vulnerabilities |
| Forward validator | fresh baseline/legacy forward/replay PASS、conflict rollback 10/10、billing_mode=test、remote_access=false |
| Isolated restore | 前段実行PASS。54 public/auth tables、schema/ACL/件数一致、source unchanged |
| git diff --check | PASS |

buildには検証用HTTPS originをプロセス内指定。実Backend疎通は証明しない。.envは変更なし。本番URLで再buildが必要。
restoreはStorage/global roles/本番DR全体を保証しない。外部メール/AI/決済は代替で、実Supabase Auth発行JWTとDBはローカルで実行した。

## SQL安全性
forward SHA256: 0027F2B1740804DB72242F8511F13445C6118E8AB22ED72D6D191B999F7C049F
UTF-8正常、日本語133文字、置換文字なし、参照元literal一致。
既存関数置換0。未知定義・policy/view/trigger・ACL・index・overloadは停止。新規billing configはtestのみ。
既存顧客行のUPDATE/DELETE/TRUNCATE/DROPなし。内部削除/昇格RPCは定義のみで実行しない。
remoteは未接続・未適用。SQL Editor/db push/履歴repairなし。

## 残る外部Gate
- REMOTE SUPABASE: 実schema/ACL/RPC・backup・writer停止・適用承認・適用後検証。
- REAL GOOGLE: OAuth、token移行/rotation/revoke、同期、管理下送受信、UNKNOWN照合。実送信は別承認。
- STRIPE TEST: 実test-mode E2E未実施。今回test/live chargeなし。
- GOOGLE VERIFICATION / DOMAIN / LEGAL REVIEW: 本人確認・審査・契約情報確定。
- PRODUCTION DEPLOY: 本番設定、監視到達、DR、別承認。未公開を維持。

未解消の既知コードP0/販売阻害P1は今回確認範囲で0。実remoteの安全性は未認定。
以前の「Docker未導入、25 skipped」は履歴。現在の実行結果は本書を優先する。
commit/push、本番変更、Gmail送信、Stripe chargeは未実施。
