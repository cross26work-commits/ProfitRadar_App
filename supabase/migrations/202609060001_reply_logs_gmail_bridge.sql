-- Clean-build bridge for columns that existed in the legacy remote schema before
-- the release-candidate index/function migrations. Existing installations are a no-op.
begin;

do $$
begin
  if to_regclass('public.reply_logs') is null then
    raise exception 'BRIDGE: public.reply_logs is missing';
  end if;
end $$;

alter table public.reply_logs add column if not exists gmail_message_id text;
alter table public.reply_logs add column if not exists gmail_thread_id text;

do $$
begin
  if exists (
    select 1 from information_schema.columns
    where table_schema='public' and table_name='reply_logs'
      and column_name in ('gmail_message_id','gmail_thread_id')
      and (data_type <> 'text' or is_nullable <> 'YES' or column_default is not null)
  ) or (select count(*) from information_schema.columns
        where table_schema='public' and table_name='reply_logs'
          and column_name in ('gmail_message_id','gmail_thread_id')) <> 2 then
    raise exception 'BRIDGE: reply_logs Gmail column contract mismatch';
  end if;
end $$;

commit;
