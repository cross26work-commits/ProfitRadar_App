-- Complete the current application contract on a database created only by the
-- fresh-project stream. Historical remote baselines use the pinned v1/v2 path.
begin;

do $$
declare
  required_table text;
begin
  foreach required_table in array array[
    'companies','profiles','profit_events','gmail_sync_cursors',
    'gmail_inbound_receipts','operation_recovery_audit','financial_records',
    'financial_record_history','ai_budget_reservations','account_deletion_jobs',
    'account_deletion_audit','financial_payments'
  ]::text[] loop
    if to_regclass('public.'||required_table) is null then
      raise exception 'FRESH_CONTRACT: required table public.% is missing', required_table;
    end if;
  end loop;

  if not exists (
    select 1 from information_schema.columns
    where table_schema='public' and table_name='profiles' and column_name='full_name'
      and data_type='text'
  ) or exists (
    select 1 from information_schema.columns
    where table_schema='public' and table_name='profiles' and column_name='name'
  ) then
    raise exception 'FRESH_CONTRACT: profiles.full_name canonical contract mismatch';
  end if;

  if exists (
    select 1 from information_schema.columns
    where table_schema='public' and table_name='profit_events'
      and column_name=any(array[
        'gmail_thread_id','last_gmail_message_id','recoverable_profit',
        'neglected_days','description'
      ]::text[])
  ) then
    raise exception 'FRESH_CONTRACT: additive profit_events columns already exist';
  end if;
end
$$;

alter table public.profit_events
  add column gmail_thread_id text,
  add column last_gmail_message_id text,
  add column recoverable_profit bigint,
  add column neglected_days integer,
  add column description text;

-- These internal state tables are mutated only through audited SECURITY
-- DEFINER RPCs. The service role may inspect them but cannot bypass those RPCs.
revoke all on table
  public.gmail_sync_cursors,
  public.gmail_inbound_receipts,
  public.operation_recovery_audit,
  public.financial_records,
  public.financial_record_history,
  public.ai_budget_reservations,
  public.account_deletion_jobs,
  public.account_deletion_audit,
  public.financial_payments
from service_role;

grant select on table
  public.gmail_sync_cursors,
  public.gmail_inbound_receipts,
  public.operation_recovery_audit,
  public.financial_records,
  public.financial_record_history,
  public.ai_budget_reservations,
  public.account_deletion_jobs,
  public.account_deletion_audit,
  public.financial_payments
to service_role;

-- Preserve the two narrow runtime write paths from their source migrations.
-- Broad table INSERT/UPDATE/DELETE privileges remain revoked.
grant update(status, actual_input_tokens, actual_output_tokens)
  on table public.ai_budget_reservations to service_role;
grant update(gmail_done, billing_done, billing_reference, last_error_code)
  on table public.account_deletion_jobs to service_role;

commit;
