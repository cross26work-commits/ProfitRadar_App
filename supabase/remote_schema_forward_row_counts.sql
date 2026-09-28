-- READ ONLY. Run before and after v2; compare exact aggregate counts by table.
-- No row values, identifiers, email, tokens or customer content are returned.
SELECT 'ai_judgements'::text AS table_name, count(*)::bigint AS row_count FROM public.ai_judgements
UNION ALL
SELECT 'ai_usage_runs'::text AS table_name, count(*)::bigint AS row_count FROM public.ai_usage_runs
UNION ALL
SELECT 'billing_webhook_events'::text AS table_name, count(*)::bigint AS row_count FROM public.billing_webhook_events
UNION ALL
SELECT 'calendar_events'::text AS table_name, count(*)::bigint AS row_count FROM public.calendar_events
UNION ALL
SELECT 'companies'::text AS table_name, count(*)::bigint AS row_count FROM public.companies
UNION ALL
SELECT 'company_billing'::text AS table_name, count(*)::bigint AS row_count FROM public.company_billing
UNION ALL
SELECT 'conversation_analysis_snapshots'::text AS table_name, count(*)::bigint AS row_count FROM public.conversation_analysis_snapshots
UNION ALL
SELECT 'customers'::text AS table_name, count(*)::bigint AS row_count FROM public.customers
UNION ALL
SELECT 'gmail_company_sync_runs'::text AS table_name, count(*)::bigint AS row_count FROM public.gmail_company_sync_runs
UNION ALL
SELECT 'gmail_connections'::text AS table_name, count(*)::bigint AS row_count FROM public.gmail_connections
UNION ALL
SELECT 'gmail_send_operations'::text AS table_name, count(*)::bigint AS row_count FROM public.gmail_send_operations
UNION ALL
SELECT 'gmail_sync_runs'::text AS table_name, count(*)::bigint AS row_count FROM public.gmail_sync_runs
UNION ALL
SELECT 'gmail_work_locks'::text AS table_name, count(*)::bigint AS row_count FROM public.gmail_work_locks
UNION ALL
SELECT 'learning_logs'::text AS table_name, count(*)::bigint AS row_count FROM public.learning_logs
UNION ALL
SELECT 'messages'::text AS table_name, count(*)::bigint AS row_count FROM public.messages
UNION ALL
SELECT 'profiles'::text AS table_name, count(*)::bigint AS row_count FROM public.profiles
UNION ALL
SELECT 'profit_events'::text AS table_name, count(*)::bigint AS row_count FROM public.profit_events
UNION ALL
SELECT 'reply_drafts'::text AS table_name, count(*)::bigint AS row_count FROM public.reply_drafts
UNION ALL
SELECT 'reply_logs'::text AS table_name, count(*)::bigint AS row_count FROM public.reply_logs
UNION ALL
SELECT 'timeline'::text AS table_name, count(*)::bigint AS row_count FROM public.timeline
ORDER BY table_name;
