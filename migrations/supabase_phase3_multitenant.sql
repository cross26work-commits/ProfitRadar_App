create table if not exists public.companies (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  plan text not null default 'free',
  created_at timestamptz not null default now()
);

create table if not exists public.profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  company_id uuid not null references public.companies(id) on delete cascade,
  name text not null,
  role text not null default 'owner',
  created_at timestamptz not null default now(),
  unique(user_id)
);

alter table public.companies enable row level security;
alter table public.profiles enable row level security;

drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own"
on public.profiles
for select
to authenticated
using (user_id = auth.uid());

drop policy if exists "profiles_insert_own" on public.profiles;
create policy "profiles_insert_own"
on public.profiles
for insert
to authenticated
with check (user_id = auth.uid());

drop policy if exists "companies_select_member" on public.companies;
create policy "companies_select_member"
on public.companies
for select
to authenticated
using (
  exists (
    select 1
    from public.profiles
    where profiles.company_id = companies.id
    and profiles.user_id = auth.uid()
  )
);

drop policy if exists "companies_insert_authenticated" on public.companies;
create policy "companies_insert_authenticated"
on public.companies
for insert
to authenticated
with check (true);
