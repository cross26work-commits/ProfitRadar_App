-- UNAPPLIED: review actual schema first. Existing same-name table intentionally
-- raises an error rather than silently assuming compatible columns or grants.
begin;
create table public.reply_drafts (
  company_id uuid not null references public.companies(id),
  profit_event_id uuid not null references public.profit_events(id),
  body text not null check (length(body) <= 50000),
  subject text not null check (length(subject) <= 998 and subject !~ E'[\r\n]'),
  updated_at timestamptz not null default now(),
  primary key (company_id, profit_event_id)
);
alter table public.reply_drafts enable row level security;
revoke all on table public.reply_drafts from public, anon, authenticated;
grant select, insert, update on table public.reply_drafts to service_role;
commit;
