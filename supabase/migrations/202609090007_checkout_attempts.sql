begin;
create table public.billing_checkout_attempts (
 company_id uuid primary key references public.companies(id),attempt_id uuid not null,
 session_id text,created_at timestamptz not null default now()
);
alter table public.billing_checkout_attempts enable row level security;
revoke all on public.billing_checkout_attempts from public,anon,authenticated;
grant select,insert,update on public.billing_checkout_attempts to service_role;
commit;
