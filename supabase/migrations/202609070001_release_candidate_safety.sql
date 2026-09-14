-- REVIEW BEFORE APPLYING: additive release-candidate safety objects only.
-- Do not apply until production schema, duplicate Gmail IDs, RLS and grants are audited.

create table if not exists public.conversation_analysis_snapshots (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies(id) on delete cascade,
  profit_event_id uuid not null references public.profit_events(id) on delete cascade,
  analysis_version text not null default 'conversation-v1',
  payload jsonb not null default '{}'::jsonb,
  provider text,
  model text,
  created_at timestamptz not null default now()
);

create index if not exists idx_conversation_analysis_snapshots_company_event_created
  on public.conversation_analysis_snapshots(company_id, profit_event_id, created_at desc);

-- Pre-apply audit required. This index intentionally excludes null IDs.
create unique index if not exists uq_reply_logs_company_gmail_message
  on public.reply_logs(company_id, gmail_message_id)
  where gmail_message_id is not null;

-- RLS/policies are deliberately not changed here. They require a production policy audit.
