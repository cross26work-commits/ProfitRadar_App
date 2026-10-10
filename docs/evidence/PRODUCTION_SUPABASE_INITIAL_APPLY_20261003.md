# Production Supabase initial apply — content reconciliation and post-apply verification

- Completed: `2026-10-03T08:07:11+09:00`
- Release commit: `9099d9a4667670eb505157acd66f0c5841f2534a`
- Project: `Profit Radar Production`
- Project ref: `runxnxvwjqblyzdcegay`
- Region: `ap-northeast-1`
- Project status: `ACTIVE_HEALTHY`
- Authorized Production DB changes: **YES**
- Migration replay during reconciliation: **0**
- Migration-history mutations: **0**
- Unexpected Production side effects: **0**

## Final result

**PASS. Production Supabase is READY.** Railway deployment remains unapproved and was not started.

## Original apply mechanism and version rebasing

The original Codex session record shows that the staged manifest was read in order, each migration file was read verbatim with PowerShell `Get-Content -Raw`, and each migration was sent through the Supabase migration API as `apply_migration(project_id, name, query)`. That interface does not accept a caller-selected migration version. Production therefore generated apply-time version IDs; their difference from the staged filename timestamps is expected and is not content drift.

The reconciliation did not replay a migration and did not edit `supabase_migrations.schema_migrations`.

The command-output transport supplied one terminal CRLF to each query. Exact comparison therefore used the exact submitted query bytes, including that CRLF. No permissive whitespace normalization or semantic comparison was used.

## Exact migration content reconciliation

Names and order: **23/23 PASS**. Exact submitted-query SHA-256 equals the Production stored statement SHA-256 for **23/23** migrations.

| Staged version | Production version | Migration | Staged raw SHA-256 | Exact submitted/stored SHA-256 |
|---|---|---|---|---|
| 20261002094539 | 20261002152003 | fresh_project_empty_guard | `CC8F3177D147BD94ADB8D12423FE0F376D6DC87DC45C021B9E59A3BEF1291631` | `81256800D57DBB61FFBC9EAEC32E8318BF6FAAEB22A0F67A1A058B1F534105BC` |
| 20261002094601 | 20261002152006 | profit_radar_core | `FC4E55F54F7582724D7D6898A4FD454903808FE6426E2AF71C4B3793B8552BBE` | `45B1E341336CC6BD61B48D0F19FA06238EEA2CE8EB1C4F6C1719148BA118417F` |
| 20261002094602 | 20261002152009 | reply_logs_gmail_bridge | `BB6CA1C7007068FD287ABCC12B1FE2268FB987634771E5A950DE888B28BE55FD` | `715754F1519D0CC7F9B31117E4675E9FBCD26A77F81ADEF913C1C66E38DB4B12` |
| 20261002094603 | 20261002152012 | release_candidate_safety | `A754C397D9FDEC01E59500670818F948C2B1EC9D02BAD68FBDDE040853CFFD8E` | `BF4F2EE087F709DFF3F8970D06AE4342ED20AF53A3B38741F25B727F34AEB8FD` |
| 20261002094604 | 20261002152015 | p0_tenant_rls_onboarding | `775E749A248EA1C76C5DD60C3491AAD8724F88E61C706C99BA204ADEBE14766E` | `1E17BBD390CB70024EAA291559906FEA7EA6063B8118BD0DE3AE5C3A67386060` |
| 20261002094605 | 20261002152019 | saved_reply_drafts | `2CA794AA0767C9BE479A9C6A44FA07DEB879F94842F17EB0F826CEF302EC396C` | `87D83E097B55F0ABE6F0BD6FAC6FF00679ED539C4F803B65B2521E3C93F908D1` |
| 20261002094606 | 20261002152022 | send_operations | `BBF58497A694815886F3AEE3380A4BCDD994975E29C4ED2BF54AEF1E45186E94` | `11D588443B7F2C3D15C9689F66B1A0EAFFC70F7115DC4C287CB0A547EA2BC126` |
| 20261002094607 | 20261002152025 | gmail_sync_runtime | `03C5318F80BF8BEBE7D62DF8DDF1E5376A7EA81D0A1E8CF02C678BD2411CCF6F` | `6C88E39BC1305242DCD506D201A835C3C644DA340C31536ADD4FF45D301DDBDC` |
| 20261002094608 | 20261002152028 | trial_billing | `2092C9B4273632A37A6D28584E986D1B7043D6985E42C6E78C39B6698BE1850A` | `8E78F0F8D0DC6D88EB7194F2C7B2B547685473B34D4E06291CE252157AC73C73` |
| 20261002094609 | 20261002152031 | ai_usage | `860B4C641A4F6CD56D0DC5402CCE6F207BEC35F3B896FE6AF6CD87B8DEAD0E55` | `5E42CB0F32042D467EE68BCF1DD3F0AD3C686D699F6E4A868488E8CFED024540` |
| 20261002094610 | 20261002152034 | checkout_attempts | `CE98F463532E4E1A6D280B98493822677E852F5FB85C4BA7FA662242E76BE3C2` | `E4292E9BCDB956C9EB9F0D1409FB348D3F51E2B013B589DEF143E0332CF64669` |
| 20261002094611 | 20261002152039 | repair_runtime_schema | `B29CC59B872DBAB1951277CCBA7750F07AAE86D70325AB53897786D0458EDD09` | `A264E8268340191E042DF3D3088A158FCCC30A078BE34D3EB8CE79EE4F0D32EE` |
| 20261002094612 | 20261002152042 | atomic_gmail_sync | `142DA72E2F6D102FCBE7D15DD68025D4B94E4A7774BE0425E935934B4ECB3689` | `7A92FA3DCD6AB9A854D766E080408F51E03966CF189614F8320272DDE47003B0` |
| 20261002094613 | 20261002152047 | operator_recovery | `A3FA9A0066D0BC3D320F5E9091BDEFC13BACE26541D610399F972B428686F708` | `5503F781CA6C7CAC51B2DFFA5B4D69B6B1E08620CA0FF8246932BE577E535625` |
| 20261002094614 | 20261002152050 | financial_records | `B6BA95C20977F4C1F8BEB61687EAC49A489EC0260D612D755275F7EDBD20B186` | `E1D919120974DB7E90850E28CAF35C7D5AC9A0974EE406AD2336D3A294AAFE7C` |
| 20261002094615 | 20261002152053 | ai_hard_budget | `52A33BDB49522403E111FDBE66E3EE31546F891EEA386838E5118595A1509A4D` | `6A964775AE591F8363856F9B86AA2AA51BB7F4A922B1BCC0FE0558A268C6AD31` |
| 20261002094616 | 20261002152056 | account_deletion | `02DCEC31839A812DEDCEB5BD30E496C026056C8C45043A65E17F7DF29769655B` | `00E81AE0EA3F7DD23636459E91C0373FA56E7B3B022FB6694503109140AF3A91` |
| 20261002094617 | 20261002152100 | payment_entries | `F0DDA54AD7D9148E421C764B4100781C035D2AAE6BB539871AEECCD1F7167CE2` | `50C263C78C455354AC9465F1E7E146F3CAF884915FEEFEF1D545C3A8A6ED1A84` |
| 20261002094618 | 20261002152103 | provider_recovery | `C9A5BD612118A20A60712511F595C324C54B4A65C3B8AC5C76A5534AB4CF2A0B` | `B6960818EF831046ECC3D49CA02D1C574BB0797C423EB4618577BD4B6DEEFB57` |
| 20261002094619 | 20261002152106 | billing_production_gate | `C94E573F047BAACAADDBC3FFB2BB9AA53F87C37A85CF6DDF98795F240770EA54` | `D5EE0F3FE6560D54E2915C7AAAD463C7AB54D808716B0483F62745C7D50F6605` |
| 20261002094620 | 20261002152109 | legal_support_admin | `1E6F0552AF813768679895DECD7100C226EB8605462AB0EC4A5311A1B859D23E` | `D6B63CEC93A58486B3098A11E7BCFFEE060FA6FF06BA4C84C3DB07CEF82F4F85` |
| 20261002094621 | 20261002152113 | fix_support_request_ambiguity | `F729828BDA4B1EF6AD52D88AF567FF1686ECAF9255EAA434F8CE6F33A453C7B0` | `2E6137A7BB2E2F3C8CDF80756EED87408215EF3A5928B281DFC565974998EE6A` |
| 20261002094622 | 20261002152116 | fresh_current_contract_completion | `78282E4A44F01494E44B3F8003F8B4959915B657855B49D788325EF01E9FAE70` | `47CFB3A754258D9735E826FAEB2468522DF64E50DA35E29491E4848E96921AB4` |

## Canonical schema and critical contracts

- Canonical metadata SHA-256: `55629B9C3C435AFA74DE08FAD7FD32D18B4EABBE1117E83EB575DB24BC3B835D` — **PASS**.
- Public tables: 37; tables with RLS disabled: 0.
- Public functions: 28; browser-executable `SECURITY DEFINER` functions: 0.
- Browser table grants: only `authenticated` SELECT on `companies` and `profiles`.
- Billing runtime mode: `test`; billing tables: 5.
- Gmail persistence tables: 7; canonical `profit_events` contract fields: 5.
- Profile contract: `full_name` present and legacy `name` absent.
- Internal RPC-managed tables have no broad non-SELECT service-role table grants.

The canonical schema hash also confirms the approved policies, constraints, indexes, triggers, functions and grants. No manual patch was used.

## Production Auth/RLS A/B verification

The production-only guarded runner used temporary A/B Auth users and application onboarding with real Supabase JWTs. It verified:

- both users could authenticate and read their own profile/company context;
- service-role setup writes were limited to the temporary tenant fixtures;
- own Customer and Lead list/detail paths succeeded;
- cross-tenant resource IDs returned no data/404 and did not mutate data;
- unauthenticated and invalid-JWT calls returned 401;
- direct browser access to business tables and financial records was denied;
- legacy onboarding/deletion RPC paths were denied;
- all temporary Auth and tenant fixtures were removed.

Final cleanup result: **PASS**. Pre/post deltas for companies, profiles, customers and profit events were all zero. Final marker counts for temporary Auth users, companies, customers, profit events and financial records were all zero. Gmail OAuth/send, Stripe charge, Cron and deployment calls: **0**.

One supplemental read initially referenced a nonexistent financial-record column and produced `42703`; it created no row, cleanup passed, and the corrected real-JWT check produced the expected `42501` denial. This diagnostic error is resolved and is not a schema or cleanup failure.

## Advisors

- Security Advisor: **PASS**. Only expected INFO findings for backend-only tables with RLS enabled and no browser policy were present. No critical/high issue, disabled RLS, exposed table, or browser-executable definer was found.
- Performance Advisor: **WARN, non-blocking for the initial three customers**. Findings comprise unindexed foreign keys, RLS init-plan suggestions, unused indexes and one duplicate profile index. No schema change was made during reconciliation.

## Production log review

Reviewed Auth, Edge, PostgREST, Postgres and pooler logs across the apply and verification window.

- Edge HTTP 5xx: 0.
- Auth errors/fatals or HTTP 5xx: 0.
- Unresolved PostgREST error messages: 0.
- Expected authorization denials (`42501`) were generated by the boundary tests.
- Two pre-apply missing-object messages occurred while the project was still empty.
- One transaction-wrapped direct Auth fixture attempt failed and rolled back before the final real-Auth runner.
- One SQL Editor syntax error and the resolved financial-column diagnostic were verification-query errors, not application or migration failures.

No unresolved migration abort, tenant bypass, Auth failure, or Production HTTP 5xx remains.

## Release decision

Production Supabase initial apply and post-apply verification: **PASS / READY**. The next gate is Railway production deployment readiness and explicit deployment approval; no deployment was performed here.
