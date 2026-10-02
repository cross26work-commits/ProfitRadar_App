-- Fresh-project-only guard. This file must be the first migration in the
-- staged production stream. It intentionally refuses historical databases.
begin;

do $$
declare
  existing_app_objects text[];
begin
  select array_agg(c.relname order by c.relname)
    into existing_app_objects
  from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relkind in ('r', 'p', 'v', 'm')
    and c.relname = any(array[
      'companies','profiles','customers','messages','profit_events','timeline',
      'reply_logs','ai_judgements','learning_logs','calendar_events',
      'gmail_connections','conversation_analysis_snapshots','reply_drafts',
      'gmail_send_operations','gmail_sync_runs','gmail_sync_locks',
      'gmail_company_sync_runs','gmail_work_locks','company_billing',
      'billing_webhook_events','ai_usage_runs','billing_checkout_attempts',
      'gmail_sync_cursors','gmail_inbound_receipts','operation_recovery_audit',
      'financial_records','financial_record_history','ai_budget_reservations',
      'account_deletion_jobs','account_deletion_audit','financial_payments',
      'billing_runtime_config','company_business_consents',
      'billing_checkout_consents','support_requests','support_messages',
      'support_internal_notes','support_audit_logs'
    ]::text[]);

  if existing_app_objects is not null then
    raise exception 'FRESH_PROJECT_ONLY: existing Profit Radar objects: %',
      array_to_string(existing_app_objects, ',');
  end if;

  if exists (
    select 1
    from supabase_migrations.schema_migrations
  ) then
    raise exception 'FRESH_PROJECT_ONLY: migration history is not empty';
  end if;
end
$$;

commit;
