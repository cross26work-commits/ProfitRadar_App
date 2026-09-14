-- LOCAL FIXTURE OVERLAY ONLY, after repository 202607020001 core migration.
-- Never apply this fixture file to shared/production databases.
-- Keep core constraints intact rather than replacing tables with permissive mocks.
alter table public.profiles add column name text not null default '';
alter table public.profit_events add column gmail_thread_id text;
alter table public.profit_events add column last_gmail_message_id text;
alter table public.profit_events add column recoverable_profit bigint;
alter table public.profit_events add column neglected_days integer;
alter table public.profit_events add column description text;
alter table public.reply_logs add column gmail_message_id text;
alter table public.reply_logs add column gmail_thread_id text;
alter table public.gmail_connections add constraint fixture_one_gmail_per_company unique(company_id);
-- Deliberately broad legacy profile policy must be intersected by hardening.
alter table public.profiles enable row level security;
create policy legacy_broad_profiles on public.profiles for select to authenticated using(true);
