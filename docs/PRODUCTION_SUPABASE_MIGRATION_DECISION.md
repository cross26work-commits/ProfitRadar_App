# Production Supabase migration decision gate

Status: **FRESH MIGRATION REPAIR PASS / owner creation and apply approval pending.**

Target decision: **a new Supabase Production project in Tokyo (`ap-northeast-1`)**. No Production project was created or contacted by this repair.

## Root cause and repair

The repository migration directory contains two remote-only supplements, `202609140001_remote_schema_forward.sql` and `202609150001_remote_schema_forward_v2.sql`. They pin a historical remote baseline and cannot run after the canonical fresh migrations: v1 correctly aborts because fresh `profiles` has `full_name` and does not have the historical `name` column. A migration appended after v1 cannot repair an earlier transactional abort.

Historical migration files remain byte-for-byte unchanged. The approved fresh-project stream is built from `deploy/fresh-production/migration-stream.json` and consists of:

1. a fresh-only empty-project/history guard;
2. the hash-pinned normal application migrations, excluding only the two remote-only supplements;
3. the additive fresh current-contract completion migration.

The completion adds the five current nullable `profit_events` fields required by the application and narrows direct `service_role` writes to internal tables. It does not copy v2, create legacy `profiles.name`, create `companies.owner_user_id`, patch rows, or depend on the historical remote database.

## Local proof (2026-10-02)

- Three independent zero-state Supabase projects: **PASS**.
- Fresh migration stream: **23 migrations**, identical history in every run.
- Deterministic schema: **37 public tables**, schema SHA-256 `55629B9C3C435AFA74DE08FAD7FD32D18B4EABBE1117E83EB575DB24BC3B835D` in all runs.
- Real local Auth/PostgREST application integration: **35 passed / 0 skipped** in every run.
- RLS, policies, RPCs, triggers, browser grants and narrowed service-role permissions: **PASS**.
- Guard replay against a non-empty history: rejected with `FRESH_PROJECT_ONLY` in every run.
- Manual SQL patch: **0**. Historical migrations modified: **0**.
- Evidence: `docs/evidence/FRESH_PRODUCTION_MIGRATION_20261002.json` and `.md`.

## Production boundary

Do not run the root migration directory directly and do not use blind `supabase db push`. After the owner creates the new Tokyo project, stage the exact file-only stream with `Stage-FreshProductionMigrations.ps1`, review its hashes, obtain a separate explicit apply approval, and then use the controlled runbook. Production Auth A/B E2E and post-apply verification remain separate approved operations.

This document is migration readiness evidence, not authorization to create a project, link a CLI, apply SQL, deploy, send Gmail, or charge Stripe.
