# Fresh Production Migration Evidence — 2026-10-02

Generated at: `2026-10-02T21:10:33+09:00` (Asia/Tokyo).

## Scope and safety

- Target: future **NEW TOKYO PROJECT** (`ap-northeast-1`), not yet created or contacted.
- Repository baseline HEAD: `4de25c344b1816aa1cfb33d46c8e9aecf3fe9820` plus the preserved uncommitted release work listed by Git.
- Production connections: **0**. Production side effects: **0**.
- Historical migrations modified: **0**. Manual database patches: **0**.

## Root cause

The remote-only v1/v2 forward migrations require the historical remote schema. On a zero-state project, canonical migrations create `profiles.full_name` and do not create the historical `profiles.name`; remote-only v1 therefore aborts transactionally before any later migration could repair the chain. A direct root-directory `db push`, history forgery, historical edit, or copying v2 would be unsafe.

The real application integration additionally identified current contracts absent after the normal 20-migration stream: five nullable `profit_events` fields (`gmail_thread_id`, `last_gmail_message_id`, `recoverable_profit`, `neglected_days`, `description`) and narrower service-role direct-write privileges on internal tables. It also exposed an ambiguous `create_support_request` query, repaired by the additive normal migration `20261002114404_fix_support_request_ambiguity.sql`.

## Repair

- Manifest: `deploy/fresh-production/migration-stream.json`.
- Empty-project guard: `deploy/fresh-production/supabase/migrations/20261002094539_fresh_project_empty_guard.sql`.
- Normal application migrations: **21**, each exact-hash pinned.
- Fresh completion: `deploy/fresh-production/supabase/migrations/20261002095741_fresh_current_contract_completion.sql`.
- Total staged fresh stream: **23 migrations**.
- Excluded remote supplements: only `202609140001_remote_schema_forward.sql` and `202609150001_remote_schema_forward_v2.sql`, exact-hash pinned.
- Canonical profile contract remains `profiles.full_name`; legacy `profiles.name` and `companies.owner_user_id` are not introduced.
- Completion is additive and fail-closed, and only accepts the guarded empty/current prerequisite shape.

## Three zero-state runs

| Run | Migration apply | Public tables | Application integration | Schema SHA-256 | Result |
|---|---:|---:|---:|---|---|
| 1 | 23/23 | 37 | 35 passed / 0 skipped | `55629B9C3C435AFA74DE08FAD7FD32D18B4EABBE1117E83EB575DB24BC3B835D` | PASS |
| 2 | 23/23 | 37 | 35 passed / 0 skipped | `55629B9C3C435AFA74DE08FAD7FD32D18B4EABBE1117E83EB575DB24BC3B835D` | PASS |
| 3 | 23/23 | 37 | 35 passed / 0 skipped | `55629B9C3C435AFA74DE08FAD7FD32D18B4EABBE1117E83EB575DB24BC3B835D` | PASS |

Every run used a different local Supabase project ID, workspace and port set. Each began at zero state, applied only the generated stream, rejected guard replay after migration, and used actual local GoTrue JWTs and PostgREST. No manual SQL patch was used. Workspaces were stopped without deleting volumes or touching the existing isolated environment.

The file-only Production staging guard was also exercised with a synthetic 20-character project ref. It produced exactly 23 files and reported `remote_contact=0` / `remote_write=0`; no CLI link or push occurred.

## Verified application contracts

- Auth, onboarding, company/profile and B2B consent.
- `/auth/me`, normal own-tenant reads and A/B tenant isolation.
- Financial records/payments, current `profit_events` and Gmail persistence columns.
- Billing, support/admin, account deletion and provider recovery.
- Canonical profile `full_name` contract and absence of legacy `name`.
- Browser table access limited to the approved company/profile SELECT path.
- Internal service-role tables are SELECT-only except the exact column-level updates required for AI budget completion and account-deletion progress.
- RLS enabled on every public application table; exact four browser policies, exact functions/triggers, and no browser-executable SECURITY DEFINER function.

## Regression

- Existing isolated integration: **35 passed / 0 skipped**.
- Backend full: **360 passed / 0 skipped**.
- Frontend Node: **26 passed / 0 skipped**.
- Python compileall, pip check, pip-audit: PASS / no known vulnerabilities.
- TypeScript, ESLint, production build: PASS.
- npm audit: 0 vulnerabilities.
- Candidate secret scan: 0 findings.
- `git -c core.safecrlf=false diff --check`: PASS.

The first production-build attempt intentionally failed the Production origin fail-closed guard because only one of the two required origins was supplied. The final build passed with both set to the non-routable `https://api.example.invalid`; this is not a deployment artifact or network target.

## Decision

Fresh migration: **PASS**. Canonical schema parity: **PASS**. Application integration: **PASS**. No historical DB dependency: **PASS**. Manual DB patch required: **NO**. RLS runner: **READY**.

This evidence does not authorize Production project creation, CLI link, migration apply, Auth fixture creation, deployment, Gmail send or Stripe activity. The next external action is to create the new Tokyo project and record its project ref; staging/apply remains a separate approval boundary.
