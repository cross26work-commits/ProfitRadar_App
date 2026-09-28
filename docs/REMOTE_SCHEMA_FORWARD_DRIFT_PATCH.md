# v2 drift patch — owner contract修正 / local full validator PASS

## 最新 2026-09-15: owner_user_id exact guard

Docker復旧後、今回の最新版でv2 full validatorがexit 0。fresh apply rollback、legacy forward commit、旧行保持、unrelated ACL保持、replay無差分、conflict rollback 27/27、identity rollback 10/10、内蔵real local JWT検証成功。billing_mode=test、remote_access=false。DB: pr_forward_e54d47d5e8f948798fbf8198c6179735。
SQL/static tests 37 passed、git diff --check PASS。別途integration/full backend/frontend全回帰はこの変更後未実行。以下のDocker停止・194/27は過去時点の記録で現在のfull gate証拠ではない。remote適用は禁止継続。

原因: 既存の型検査はあったが、NULL/default/identity/generatedのexact契約が不足。報告されたRuntimeErrorは通過と想定外エラーを区別しない。実際のuuid→text mutationはpolicy依存によってmigration到達前に拒否されていた。
修正: migrationのowner_contractがSHARE lock下で存在/uuid/nullable/auth.uid() default/非identity/非generatedを検査し、不一致は指定エラーでabort。自動修復なし。型変更テストは保持し、隔離transaction内だけで依存2policyを外す準備を追加。rollback後schema/row fingerprintを検査する。追加ケースはDROP DEFAULT、gen_random_uuid() default、SET NOT NULL（架空行のNULLだけtransaction内で補完）。
canonical、legacy本文、historical migration、policy oracle、global sync契約は変更していない。

最新版SHA256:
- v2: B5152C99E1368989FB35203686DB3D29CB395362C1E8282D6F1F9BBB8EDC86F0
- validator: 6AD2E68D067E40F4FB59A0F03D05A5E514E53AD2CEE3EC3FF29BE80930FDD1A7

## 以下はglobal aggregate patch時点の履歴

今回の対象はv2・preflight・validator/tests/docsのみ。remote接続/WRITE、db push、history repair、commit/push、Gmail送信、Stripe chargeは未実施。既存差分・履歴migration・canonical raw oracle・onboard_user本文は保持。

## 8列の判断

| 列 | 判断・今回の処理 | コード上の根拠 |
|---|---|---|
| companies.updated_at | B: prerequisiteから除外 | core schemaにあるがruntimeで会社の更新日時を指定するSELECT/order/writeなし。DashboardRepositoryのupdated_atはcustomers/profit_eventsに対するもの |
| gmail_sync_runs.company_id | 追加しない・prerequisiteから除外 | authoritative remoteは会社列なしのglobal aggregate。v2 tenant purgeから除外 |
| gmail_sync_runs.error_code | B: prerequisiteから除外 | gmail.py / gmail_work.pyの状態取得・更新対象はgmail_company_sync_runsであり旧テーブルではない |
| gmail_sync_runs.detected_count | B: prerequisiteから除外 | 同上。mailService.tsのlast_runは上記Backend経由 |
| profiles.updated_at | B: prerequisiteから除外 | profileService.ts/getCurrentAppProfile、company_context、onboardingはこの列を要求しない。historical core列を過剰に列挙していた |
| profit_events.description | A: nullable text、defaultなしで追加 | api/leads.pyの案件本文、engines/event_conversation.pyの保存event本文fallback |
| profit_events.neglected_days | A: nullable int4、defaultなしで追加 | api/leads.py delay_days、engines/action_engine.pyの判断根拠・スコア |
| profit_events.recoverable_profit | A: nullable int8、defaultなしで追加 | api/leads.py、engines/action_engine.py、home_brief_service.pyが参照 |

nullable追加は既存行の値を更新しない。数値を捏造/backfillしない。現在のUI側fallbackがNULLを0扱いする点はこのmigrationでは変更しない。
旧gmail_sync_runsへの列追加・削除RPC内のglobal blocking guardは撤回。適用transaction内だけでSHARE lockを取り、既知9列の型/NULL/default/identity/generated、余分な列なし（company_id禁止）、0行を再確認する。1行でもあればabort・再レビュー。既存テーブルのACL、行、列を変更しない。

## Legacy ACL

### companies/profiles再検索の証拠（現在のrepo runtimeに限定）

対象: frontend/src全.ts/.tsx、frontendのclient/helper/test設定、backend/app全.pyとrepositories、backend/scripts、supabase SQL。vendor/.next/venvや保存HTMLはruntime証拠から除外。
実行した検索: `rg -n 'supabase|createClient|\.rpc\(|\.insert\(|\.update\(|\.upsert\(|\.delete\(' frontend`（非コードのmd/lock/bak等除外）、`rg -n 'companies|profiles|gmail_sync_runs|createCompanyAndProfile' backend/app frontend/src backend/scripts`、`rg -n 'get_table\(|gmail_sync_runs' backend`、`rg -n 'gmail_sync_runs' supabase/migrations`。複数行チェーンは一致ファイル全文で確認した。

| runtime path | 操作・結論 |
|---|---|
| frontend/src/services/profile/profileService.ts:13 createCompanyAndProfile | companies INSERT + profiles INSERTを行う旧export。参照検索は宣言のみ。AuthProviderはgetCurrentAppProfileだけをnamed importし、このhelperをimport/実行しない。namespace export/動的呼出経路も対象src内にない |
| register/page.tsx:98、onboarding/page.tsx:84 → completeOnboarding | onboardingService.tsのapiPost('/onboarding') → backend/app/api/onboarding.py:65 → service-role onboard_user。会社/profile INSERTはRPC内部で行われbrowser table grant不要 |
| AuthProvider.tsx:39 → getCurrentAppProfile | profiles SELECT(user_id/name/role/company_id) + companies(name/plan)埋込み。両SELECTを維持 |
| settings/page.tsx | profile/company情報は表示のみ。操作はlogoutとaccountService経由の削除。profile/company editのsubmit/update/upsertなし |
| authService.ts:71 | supabase.auth.updateUserはパスワード更新。public.profiles UPDATEではない |
| backend company_context.py:29 / api/account.py:49 | profiles SELECT。会社・profile削除はservice-role purge RPC。Service Roleの権限は変更しない |
| backend/app/core/supabase_client.py:get_table | generic helperは定義のみ。repositoriesのtable指定は顧客等の固定名で、profiles/companies書込みの生成clientや別名経路なし |

最終判断: **現在の受審コードではcompanies INSERT / profiles UPDATEのbrowser grantは不要**。SELECTのみ維持。remote policyの存在は機能が呼ばれる証拠とは区別し、4policyは変更しない。特にprofiles UPDATEを全列許可すると自己role/company_id変更を許し得るため、使われない権限は残さない。
古い公開Frontend・repo外の独自clientが旧helperを利用していないことはコード検索だけでは証明しない。適用時は稼働版とこの受審コードの一致確認が必要。

### gmail_sync_runs再判定

2026-09-15ユーザー提供SELECT-only証拠: id uuid NOT NULL default gen_random_uuid(); status text NOT NULL; started_at timestamptz NOT NULL default now(); finished_at timestamptz NULL; company_count/success_count/failure_count/detected_reply_count integer NOT NULL default 0; error_summary jsonb NOT NULL default '[]'::jsonb。全9列、company_idなし。total/unfinished/null_status rowsはすべて0。
PK(id)、status CHECK running/completed/failed/skipped、indexはgmail_sync_runs_pkeyのみ。incoming FK / dependent view / user trigger / public function refsなし（提供時点の証拠）。
global operational aggregateとしてtenant purgeから除外する。tenant ownership sourceは存在せず、推測/backfillしない。tenant run削除は既存gmail_company_sync_runsで維持。現appに旧table writer/readなしだが、repo外writer不存在とは断定せずservice_role ACLは変更しない。
帰属問題はこのreleaseの「既存0行・global schema」条件で解消。適用時のschema差異/1行以上は再レビュー必須。削除RPCの完了条件にこのglobal tableを含めない。

対象: companies, profiles, customers, messages, profit_events, timeline, reply_logs, ai_judgements, learning_logs, calendar_events, gmail_connections。
PUBLIC/anonは直接table・column操作なし。authenticatedはcompanies/profilesのSELECTだけ維持。他9tableはBackend経由。
profileService.tsのgetCurrentAppProfileはprofilesとcompanies(name,plan)を読むためSELECTを残す。旧createCompanyAndProfile直接INSERT helperは定義のみで呼出なし。現在の登録はBackend/onboard_user経由。
INSERT/UPDATE/DELETE/TRUNCATE/TRIGGER/REFERENCES/MAINTAIN等の不要なtable権限、およびcolumn INSERT/UPDATE/REFERENCESを対象限定で剥奪。service_role権限は変更せずCRUDの必要権限を検証する。
RLS enabled、owner、authoritative remote4 policyのqual/roles/cmd/permissive/with_check/nameと対象11table全体のpolicy集合、未知grantee・viewを検査する。未知policyは削除せずabort。INSERT/UPDATE policyもそのまま残し、table privilegeの最小化だけを行う。
継承/PUBLICによる残存実効権限も変更後に確認し、残れば全体rollback。

## STOP理由（前回のPASSを今回の証拠に流用しない）

1. policy未提供問題は解消。docs/remote_policy_snapshot_20260915.jsonを1016 bytes / SHA256 DF734F55B6379D0C2983D658AA15E6D93A667EFE5200A13B6B4199CB9905DCC2として検証済み。4件をSQLへpinし、fixtureもこのoracleから作成する。JSON原本は変更していない。
2. Docker Desktop起動を要求したがEngineのnamed pipeに接続できない。v2 validatorとreal Auth runnerはDB操作前のtarget検査で停止した。
3. replay/rollback matrix/今回追加のJWT確認はコード追加済みだが未実行。exact observed remote baseline全体を再現したとは判定しない。
4. 旧syncはglobal/0行として扱いを確定。apply直前のschema/0行再確認は必須。今回のDB gateは未実行。

## 今回の検証

- SQL関連: 36 passed（構文/静的検査。PL/pgSQLの実DB成功証拠ではない）
- Backend全体: 194 passed / 27 skipped
- 上記194/27にはDB非接続target-guardを含む。27 skipは合格に含めない。
- Docker Engine named pipeなしを今回再確認。v2 full validator/正規Auth/実DBは未実行。
- Frontendの以前のPASSは今回の検証として流用しない。Docker復旧後、下記全gateと合わせ再実行。
- canonical3箇所のLF SHA256は12A8812B782D2D2FD1D41A9199F12199D0C3767E76D4CFBE649CCDB15D1B08D2を保持。

## 再開

policy snapshotとglobal aggregate証拠統合済み。Docker Engineと既存profit-radar-disposable復旧後、backend/scripts/validate_forward_local.py --allow-disposable-fixtures とscripts/run_local_regression.py --allow-disposable-fixturesをLOCAL ONLYで実行。
exact observed baselineは新規DB内でglobal9列/status CHECKを再現。first apply/replay/full rollback matrix/JWT real Auth/integration/full backend/frontend tsc・lint・build/npm audit/diff checkを最新版で再実行する。
旧行projectionから除外する追加列はprofit_eventsの3列だけ。global company_id追加・型/default drift・非空テーブルの拒否ケースも追加したがDB実行未済。既存identity/whitespace/overload等も再実行必須。

**APPLY READYではない。remote適用・commitは禁止のまま。**

## 対象ファイルとhash

今回変更: v2 migration、remote_schema_forward_preflight.sql、backend/scripts/validate_forward_local.py、backend/scripts/validate_v2_jwt.py、backend/tests/test_remote_forward.py、本書、REMOTE_SCHEMA_FORWARD_REVIEW.md。
先行作業の未コミットcapture関連差分も保持。historical migration/V1/runtime/frontendコードは今回未変更。

```text
v2 SHA256 14A88C8801EF912916C537E8EB3A5D69C2C450FFCD79489431D02B5C74F59BA5
preflight SHA256 EDE597B72EE224447FFC8D6DE835C3AF90BFC8F439374CF2BDB34920D730D8D5
validator SHA256 F1005C374357116C984308004487CF3D14A3FB6B335B40868267735D893AB11B
policy oracle SHA256 DF734F55B6379D0C2983D658AA15E6D93A667EFE5200A13B6B4199CB9905DCC2
```

git diff --check PASS（CRLF変換予告はwarning）。git status --short:

```text
 M backend/scripts/validate_forward_local.py
 M backend/scripts/validate_v2_jwt.py
 M backend/tests/test_remote_forward.py
 M docs/REMOTE_SCHEMA_FORWARD_REVIEW.md
 M docs/remote_onboarding_functiondefs_20260915_exact.txt
 M supabase/migrations/202609150001_remote_schema_forward_v2.sql
 M supabase/remote_schema_forward_preflight.sql
?? .local-isolated-failed-20260914-125625/
?? .local-isolated-old-20260914-125339/
?? docs/REMOTE_SCHEMA_FORWARD_DRIFT_PATCH.md
?? docs/SHA256確認ファイル.html
?? docs/SHA256確認ファイル_files/
?? docs/create_company_and_profile_remote_capture.json
?? "docs/raw prosrcファイル.html"
?? "docs/raw prosrcファイル_files/"
?? docs/remote_onboarding_functiondefs_20260915.sql/
?? docs/remote_onboarding_functiondefs_20260915_exact.txt.html
?? docs/remote_onboarding_functiondefs_20260915_exact_folder_backup/
```
