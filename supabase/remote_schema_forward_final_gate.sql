-- One result set; metadata and aggregate counts only. No remote execution by tooling.
-- Authoritative source SHA256: EDE597B72EE224447FFC8D6DE835C3AF90BFC8F439374CF2BDB34920D730D8D5
-- Independent remote snapshot SHA256: 1819D3032106DF74FC7709CC0C88EE6D0C0992F941BF74A16617A65515E751E9
WITH
approved_oracle AS (SELECT $remote_oracle${"billing_runtime_config":{"present":false},"constraints":[{"conname":"ai_judgements_company_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE","table_name":"ai_judgements"},{"conname":"ai_judgements_customer_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL","table_name":"ai_judgements"},{"conname":"ai_judgements_pkey","contype":"p","convalidated":true,"definition":"PRIMARY KEY (id)","table_name":"ai_judgements"},{"conname":"ai_judgements_profit_event_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (profit_event_id) REFERENCES profit_events(id) ON DELETE SET NULL","table_name":"ai_judgements"},{"conname":"ai_usage_runs_company_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (company_id) REFERENCES companies(id)","table_name":"ai_usage_runs"},{"conname":"ai_usage_runs_pkey","contype":"p","convalidated":true,"definition":"PRIMARY KEY (id)","table_name":"ai_usage_runs"},{"conname":"billing_webhook_events_company_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (company_id) REFERENCES companies(id)","table_name":"billing_webhook_events"},{"conname":"billing_webhook_events_pkey","contype":"p","convalidated":true,"definition":"PRIMARY KEY (event_id)","table_name":"billing_webhook_events"},{"conname":"calendar_events_company_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE","table_name":"calendar_events"},{"conname":"calendar_events_customer_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL","table_name":"calendar_events"},{"conname":"calendar_events_pkey","contype":"p","convalidated":true,"definition":"PRIMARY KEY (id)","table_name":"calendar_events"},{"conname":"calendar_events_profit_event_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (profit_event_id) REFERENCES profit_events(id) ON DELETE SET NULL","table_name":"calendar_events"},{"conname":"companies_owner_user_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (owner_user_id) REFERENCES auth.users(id) ON DELETE CASCADE","table_name":"companies"},{"conname":"companies_pkey","contype":"p","convalidated":true,"definition":"PRIMARY KEY (id)","table_name":"companies"},{"conname":"company_billing_company_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (company_id) REFERENCES companies(id)","table_name":"company_billing"},{"conname":"company_billing_pkey","contype":"p","convalidated":true,"definition":"PRIMARY KEY (company_id)","table_name":"company_billing"},{"conname":"company_billing_stripe_subscription_id_key","contype":"u","convalidated":true,"definition":"UNIQUE (stripe_subscription_id)","table_name":"company_billing"},{"conname":"conversation_analysis_snapshots_company_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE","table_name":"conversation_analysis_snapshots"},{"conname":"conversation_analysis_snapshots_pkey","contype":"p","convalidated":true,"definition":"PRIMARY KEY (id)","table_name":"conversation_analysis_snapshots"},{"conname":"conversation_analysis_snapshots_profit_event_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (profit_event_id) REFERENCES profit_events(id) ON DELETE CASCADE","table_name":"conversation_analysis_snapshots"},{"conname":"customers_company_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE","table_name":"customers"},{"conname":"customers_pkey","contype":"p","convalidated":true,"definition":"PRIMARY KEY (id)","table_name":"customers"},{"conname":"gmail_company_sync_runs_company_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (company_id) REFERENCES companies(id)","table_name":"gmail_company_sync_runs"},{"conname":"gmail_company_sync_runs_pkey","contype":"p","convalidated":true,"definition":"PRIMARY KEY (id)","table_name":"gmail_company_sync_runs"},{"conname":"gmail_company_sync_runs_status_check","contype":"c","convalidated":true,"definition":"CHECK ((status = ANY (ARRAY['running'::text, 'succeeded'::text, 'failed'::text, 'busy'::text])))","table_name":"gmail_company_sync_runs"},{"conname":"gmail_connections_company_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE","table_name":"gmail_connections"},{"conname":"gmail_connections_pkey","contype":"p","convalidated":true,"definition":"PRIMARY KEY (id)","table_name":"gmail_connections"},{"conname":"gmail_connections_profile_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE","table_name":"gmail_connections"},{"conname":"gmail_send_operations_company_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (company_id) REFERENCES companies(id)","table_name":"gmail_send_operations"},{"conname":"gmail_send_operations_customer_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (customer_id) REFERENCES customers(id)","table_name":"gmail_send_operations"},{"conname":"gmail_send_operations_pkey","contype":"p","convalidated":true,"definition":"PRIMARY KEY (company_id, operation_id)","table_name":"gmail_send_operations"},{"conname":"gmail_send_operations_profit_event_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (profit_event_id) REFERENCES profit_events(id)","table_name":"gmail_send_operations"},{"conname":"gmail_send_operations_status_check","contype":"c","convalidated":true,"definition":"CHECK ((status = ANY (ARRAY['sending'::text, 'unknown'::text, 'sent'::text])))","table_name":"gmail_send_operations"},{"conname":"gmail_sync_runs_pkey","contype":"p","convalidated":true,"definition":"PRIMARY KEY (id)","table_name":"gmail_sync_runs"},{"conname":"gmail_sync_runs_status_check","contype":"c","convalidated":true,"definition":"CHECK ((status = ANY (ARRAY['running'::text, 'completed'::text, 'failed'::text, 'skipped'::text])))","table_name":"gmail_sync_runs"},{"conname":"gmail_work_locks_company_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (company_id) REFERENCES companies(id)","table_name":"gmail_work_locks"},{"conname":"gmail_work_locks_pkey","contype":"p","convalidated":true,"definition":"PRIMARY KEY (company_id)","table_name":"gmail_work_locks"},{"conname":"learning_logs_company_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE","table_name":"learning_logs"},{"conname":"learning_logs_customer_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL","table_name":"learning_logs"},{"conname":"learning_logs_pkey","contype":"p","convalidated":true,"definition":"PRIMARY KEY (id)","table_name":"learning_logs"},{"conname":"learning_logs_profit_event_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (profit_event_id) REFERENCES profit_events(id) ON DELETE SET NULL","table_name":"learning_logs"},{"conname":"messages_company_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE","table_name":"messages"},{"conname":"messages_customer_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL","table_name":"messages"},{"conname":"messages_pkey","contype":"p","convalidated":true,"definition":"PRIMARY KEY (id)","table_name":"messages"},{"conname":"profiles_company_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE","table_name":"profiles"},{"conname":"profiles_pkey","contype":"p","convalidated":true,"definition":"PRIMARY KEY (id)","table_name":"profiles"},{"conname":"profiles_user_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE","table_name":"profiles"},{"conname":"profiles_user_id_key","contype":"u","convalidated":true,"definition":"UNIQUE (user_id)","table_name":"profiles"},{"conname":"profit_events_company_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE","table_name":"profit_events"},{"conname":"profit_events_customer_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL","table_name":"profit_events"},{"conname":"profit_events_pkey","contype":"p","convalidated":true,"definition":"PRIMARY KEY (id)","table_name":"profit_events"},{"conname":"profit_events_source_message_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (source_message_id) REFERENCES messages(id) ON DELETE SET NULL","table_name":"profit_events"},{"conname":"reply_drafts_company_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE","table_name":"reply_drafts"},{"conname":"reply_drafts_company_id_profit_event_id_key","contype":"u","convalidated":true,"definition":"UNIQUE (company_id, profit_event_id)","table_name":"reply_drafts"},{"conname":"reply_drafts_customer_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL","table_name":"reply_drafts"},{"conname":"reply_drafts_pkey","contype":"p","convalidated":true,"definition":"PRIMARY KEY (id)","table_name":"reply_drafts"},{"conname":"reply_drafts_profit_event_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (profit_event_id) REFERENCES profit_events(id) ON DELETE CASCADE","table_name":"reply_drafts"},{"conname":"reply_logs_company_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE","table_name":"reply_logs"},{"conname":"reply_logs_customer_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL","table_name":"reply_logs"},{"conname":"reply_logs_message_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE SET NULL","table_name":"reply_logs"},{"conname":"reply_logs_pkey","contype":"p","convalidated":true,"definition":"PRIMARY KEY (id)","table_name":"reply_logs"},{"conname":"reply_logs_profit_event_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (profit_event_id) REFERENCES profit_events(id) ON DELETE SET NULL","table_name":"reply_logs"},{"conname":"timeline_company_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE","table_name":"timeline"},{"conname":"timeline_customer_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL","table_name":"timeline"},{"conname":"timeline_pkey","contype":"p","convalidated":true,"definition":"PRIMARY KEY (id)","table_name":"timeline"},{"conname":"timeline_profit_event_id_fkey","contype":"f","convalidated":true,"definition":"FOREIGN KEY (profit_event_id) REFERENCES profit_events(id) ON DELETE SET NULL","table_name":"timeline"}],"event_trigger":[{"anon_execute":true,"authenticated_execute":true,"evtenabled":"O","evtevent":"ddl_command_end","evtname":"ensure_rls","evttags":["CREATE TABLE","CREATE TABLE AS","SELECT INTO"],"function_owner":"postgres","function_signature":"public.rls_auto_enable()","proacl":null,"proconfig":["search_path=pg_catalog"],"prosecdef":true,"prosrc_md5":"99be20677b456ea8d3be47bdd44fb369","return_type":"event_trigger","service_execute":true,"trigger_owner":"postgres"}],"functions":[{"anon_execute":false,"authenticated_execute":false,"identity_arguments":"p_owner_token uuid, p_lease_seconds integer","name":"acquire_gmail_sync_lock","owner":"postgres","present":true,"proacl":["postgres=X/postgres","service_role=X/postgres"],"proargnames":["p_owner_token","p_lease_seconds"],"proconfig":["search_path=pg_catalog, public"],"prosecdef":true,"prosrc_md5":"3a37272567e11c5021dbf51071224750","result":"boolean","service_execute":true},{"anon_execute":false,"authenticated_execute":false,"identity_arguments":"p_company_id uuid, p_event_id text, p_subscription_id text, p_status text, p_paid_until timestamp with time zone","name":"apply_billing_snapshot","owner":"postgres","present":true,"proacl":["postgres=X/postgres","service_role=X/postgres"],"proargnames":["p_company_id","p_event_id","p_subscription_id","p_status","p_paid_until"],"proconfig":["search_path=pg_catalog, pg_temp"],"prosecdef":true,"prosrc_md5":"04ea3098e11373a521c5d142f9c1f70d","result":"void","service_execute":true},{"anon_execute":false,"authenticated_execute":false,"identity_arguments":"p_company_id uuid, p_owner_id uuid, p_purpose text","name":"claim_gmail_work","owner":"postgres","present":true,"proacl":["postgres=X/postgres","service_role=X/postgres"],"proargnames":["p_company_id","p_owner_id","p_purpose"],"proconfig":["search_path=pg_catalog, pg_temp"],"prosecdef":true,"prosrc_md5":"3d12d706c5e98fb3a4624ca275ca4dbe","result":"boolean","service_execute":true},{"anon_execute":null,"authenticated_execute":null,"identity_arguments":null,"name":"commit_gmail_inbound_page","owner":null,"present":false,"proacl":null,"proargnames":null,"proconfig":null,"prosecdef":null,"prosrc_md5":null,"result":null,"service_execute":null},{"anon_execute":null,"authenticated_execute":null,"identity_arguments":null,"name":"company_is_active","owner":null,"present":false,"proacl":null,"proargnames":null,"proconfig":null,"prosecdef":null,"prosrc_md5":null,"result":null,"service_execute":null},{"anon_execute":null,"authenticated_execute":null,"identity_arguments":null,"name":"complete_account_deletion","owner":null,"present":false,"proacl":null,"proargnames":null,"proconfig":null,"prosecdef":null,"prosrc_md5":null,"result":null,"service_execute":null},{"anon_execute":false,"authenticated_execute":true,"identity_arguments":"company_name text, owner_name text","name":"create_company_and_profile","owner":"postgres","present":true,"proacl":["postgres=X/postgres","authenticated=X/postgres"],"proargnames":["company_name","owner_name"],"proconfig":["search_path=pg_catalog, public"],"prosecdef":true,"prosrc_md5":"2cf12d00f40e7bbaeedbd24f7f41bae3","result":"uuid","service_execute":false},{"anon_execute":false,"authenticated_execute":false,"identity_arguments":"p_company_id uuid","name":"ensure_company_billing","owner":"postgres","present":true,"proacl":["postgres=X/postgres","service_role=X/postgres"],"proargnames":["p_company_id"],"proconfig":["search_path=pg_catalog, pg_temp"],"prosecdef":true,"prosrc_md5":"8e2cbc48f6ca661aec9ba1604c8349d6","result":"SETOF company_billing","service_execute":true},{"anon_execute":false,"authenticated_execute":false,"identity_arguments":"p_company_id uuid, p_operation_id text, p_message_id text, p_thread_id text","name":"finalize_gmail_send","owner":"postgres","present":true,"proacl":["postgres=X/postgres","service_role=X/postgres"],"proargnames":["p_company_id","p_operation_id","p_message_id","p_thread_id"],"proconfig":["search_path=pg_catalog, pg_temp"],"prosecdef":true,"prosrc_md5":"1035a2a49bac9bc534a1ab771157db08","result":"boolean","service_execute":true},{"anon_execute":true,"authenticated_execute":true,"identity_arguments":"p_user_id uuid, p_company_name text, p_name text, p_email text","name":"onboard_user","owner":"postgres","present":true,"proacl":null,"proargnames":["p_user_id","p_company_name","p_name","p_email"],"proconfig":["search_path=public"],"prosecdef":true,"prosrc_md5":"0c321b67f077c23f3a413abccc3e3103","result":"jsonb","service_execute":true},{"anon_execute":null,"authenticated_execute":null,"identity_arguments":null,"name":"prevent_deleted_user_onboarding","owner":null,"present":false,"proacl":null,"proargnames":null,"proconfig":null,"prosecdef":null,"prosrc_md5":null,"result":null,"service_execute":null},{"anon_execute":null,"authenticated_execute":null,"identity_arguments":null,"name":"promote_billing_live","owner":null,"present":false,"proacl":null,"proargnames":null,"proconfig":null,"prosecdef":null,"prosrc_md5":null,"result":null,"service_execute":null},{"anon_execute":null,"authenticated_execute":null,"identity_arguments":null,"name":"purge_account_data","owner":null,"present":false,"proacl":null,"proargnames":null,"proconfig":null,"prosecdef":null,"prosrc_md5":null,"result":null,"service_execute":null},{"anon_execute":null,"authenticated_execute":null,"identity_arguments":null,"name":"purge_expired_deletion_audit","owner":null,"present":false,"proacl":null,"proargnames":null,"proconfig":null,"prosecdef":null,"prosrc_md5":null,"result":null,"service_execute":null},{"anon_execute":null,"authenticated_execute":null,"identity_arguments":null,"name":"record_financial_payment","owner":null,"present":false,"proacl":null,"proargnames":null,"proconfig":null,"prosecdef":null,"prosrc_md5":null,"result":null,"service_execute":null},{"anon_execute":null,"authenticated_execute":null,"identity_arguments":null,"name":"recover_company_work","owner":null,"present":false,"proacl":null,"proargnames":null,"proconfig":null,"prosecdef":null,"prosrc_md5":null,"result":null,"service_execute":null},{"anon_execute":false,"authenticated_execute":false,"identity_arguments":"p_owner_token uuid","name":"release_gmail_sync_lock","owner":"postgres","present":true,"proacl":["postgres=X/postgres","service_role=X/postgres"],"proargnames":["p_owner_token"],"proconfig":["search_path=pg_catalog, public"],"prosecdef":true,"prosrc_md5":"c11defbde027b9a1a70df2237dd2a5f2","result":"boolean","service_execute":true},{"anon_execute":false,"authenticated_execute":false,"identity_arguments":"p_company_id uuid, p_owner_id uuid","name":"release_gmail_work","owner":"postgres","present":true,"proacl":["postgres=X/postgres","service_role=X/postgres"],"proargnames":["p_company_id","p_owner_id"],"proconfig":["search_path=pg_catalog, pg_temp"],"prosecdef":true,"prosrc_md5":"a7cc78e6582da420d54b891880370775","result":"void","service_execute":true},{"anon_execute":null,"authenticated_execute":null,"identity_arguments":null,"name":"request_account_deletion","owner":null,"present":false,"proacl":null,"proargnames":null,"proconfig":null,"prosecdef":null,"prosrc_md5":null,"result":null,"service_execute":null},{"anon_execute":null,"authenticated_execute":null,"identity_arguments":null,"name":"reserve_ai_budget","owner":null,"present":false,"proacl":null,"proargnames":null,"proconfig":null,"prosecdef":null,"prosrc_md5":null,"result":null,"service_execute":null},{"anon_execute":false,"authenticated_execute":false,"identity_arguments":"p_company_id uuid, p_monthly_limit integer","name":"reserve_ai_run","owner":"postgres","present":true,"proacl":["postgres=X/postgres","service_role=X/postgres"],"proargnames":["p_company_id","p_monthly_limit"],"proconfig":["search_path=pg_catalog, pg_temp"],"prosecdef":true,"prosrc_md5":"14299d4c1d6caadb0c7dc09b2c0839ee","result":"uuid","service_execute":true},{"anon_execute":null,"authenticated_execute":null,"identity_arguments":null,"name":"resolve_provider_uncertainty","owner":null,"present":false,"proacl":null,"proargnames":null,"proconfig":null,"prosecdef":null,"prosrc_md5":null,"result":null,"service_execute":null},{"anon_execute":true,"authenticated_execute":true,"identity_arguments":"","name":"rls_auto_enable","owner":"postgres","present":true,"proacl":null,"proargnames":null,"proconfig":["search_path=pg_catalog"],"prosecdef":true,"prosrc_md5":"99be20677b456ea8d3be47bdd44fb369","result":"event_trigger","service_execute":true},{"anon_execute":null,"authenticated_execute":null,"identity_arguments":null,"name":"save_financial_record","owner":null,"present":false,"proacl":null,"proargnames":null,"proconfig":null,"prosecdef":null,"prosrc_md5":null,"result":null,"service_execute":null},{"anon_execute":null,"authenticated_execute":null,"identity_arguments":null,"name":"void_financial_payment","owner":null,"present":false,"proacl":null,"proargnames":null,"proconfig":null,"prosecdef":null,"prosrc_md5":null,"result":null,"service_execute":null}],"gmail_sync_runs":{"columns":[{"column_default":"gen_random_uuid()","column_name":"id","data_type":"uuid","generated_kind":"","identity_kind":"","is_nullable":false,"ordinal_position":1,"udt_name":"uuid"},{"column_default":null,"column_name":"status","data_type":"text","generated_kind":"","identity_kind":"","is_nullable":false,"ordinal_position":2,"udt_name":"text"},{"column_default":"now()","column_name":"started_at","data_type":"timestamp with time zone","generated_kind":"","identity_kind":"","is_nullable":false,"ordinal_position":3,"udt_name":"timestamptz"},{"column_default":null,"column_name":"finished_at","data_type":"timestamp with time zone","generated_kind":"","identity_kind":"","is_nullable":true,"ordinal_position":4,"udt_name":"timestamptz"},{"column_default":"0","column_name":"company_count","data_type":"integer","generated_kind":"","identity_kind":"","is_nullable":false,"ordinal_position":5,"udt_name":"int4"},{"column_default":"0","column_name":"success_count","data_type":"integer","generated_kind":"","identity_kind":"","is_nullable":false,"ordinal_position":6,"udt_name":"int4"},{"column_default":"0","column_name":"failure_count","data_type":"integer","generated_kind":"","identity_kind":"","is_nullable":false,"ordinal_position":7,"udt_name":"int4"},{"column_default":"0","column_name":"detected_reply_count","data_type":"integer","generated_kind":"","identity_kind":"","is_nullable":false,"ordinal_position":8,"udt_name":"int4"},{"column_default":"'[]'::jsonb","column_name":"error_summary","data_type":"jsonb","generated_kind":"","identity_kind":"","is_nullable":false,"ordinal_position":9,"udt_name":"jsonb"}],"constraints":[{"conname":"gmail_sync_runs_pkey","contype":"p","convalidated":true,"definition":"PRIMARY KEY (id)","table_name":"gmail_sync_runs"},{"conname":"gmail_sync_runs_status_check","contype":"c","convalidated":true,"definition":"CHECK ((status = ANY (ARRAY['running'::text, 'completed'::text, 'failed'::text, 'skipped'::text])))","table_name":"gmail_sync_runs"}],"indexes":[{"definition":"CREATE UNIQUE INDEX gmail_sync_runs_pkey ON public.gmail_sync_runs USING btree (id)","index_name":"gmail_sync_runs_pkey","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"gmail_sync_runs"}],"total_rows":0},"indexes":[{"definition":"CREATE UNIQUE INDEX ai_judgements_pkey ON public.ai_judgements USING btree (id)","index_name":"ai_judgements_pkey","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"ai_judgements"},{"definition":"CREATE INDEX idx_ai_judgements_company_id ON public.ai_judgements USING btree (company_id)","index_name":"idx_ai_judgements_company_id","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"ai_judgements"},{"definition":"CREATE INDEX idx_ai_judgements_profit_event_id ON public.ai_judgements USING btree (profit_event_id)","index_name":"idx_ai_judgements_profit_event_id","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"ai_judgements"},{"definition":"CREATE UNIQUE INDEX ai_usage_runs_pkey ON public.ai_usage_runs USING btree (id)","index_name":"ai_usage_runs_pkey","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"ai_usage_runs"},{"definition":"CREATE UNIQUE INDEX billing_webhook_events_pkey ON public.billing_webhook_events USING btree (event_id)","index_name":"billing_webhook_events_pkey","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"billing_webhook_events"},{"definition":"CREATE UNIQUE INDEX calendar_events_pkey ON public.calendar_events USING btree (id)","index_name":"calendar_events_pkey","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"calendar_events"},{"definition":"CREATE INDEX idx_calendar_events_company_id ON public.calendar_events USING btree (company_id)","index_name":"idx_calendar_events_company_id","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"calendar_events"},{"definition":"CREATE UNIQUE INDEX companies_pkey ON public.companies USING btree (id)","index_name":"companies_pkey","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"companies"},{"definition":"CREATE UNIQUE INDEX company_billing_pkey ON public.company_billing USING btree (company_id)","index_name":"company_billing_pkey","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"company_billing"},{"definition":"CREATE UNIQUE INDEX company_billing_stripe_subscription_id_key ON public.company_billing USING btree (stripe_subscription_id)","index_name":"company_billing_stripe_subscription_id_key","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"company_billing"},{"definition":"CREATE UNIQUE INDEX conversation_analysis_snapshots_pkey ON public.conversation_analysis_snapshots USING btree (id)","index_name":"conversation_analysis_snapshots_pkey","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"conversation_analysis_snapshots"},{"definition":"CREATE INDEX idx_conversation_analysis_snapshots_company_event_created ON public.conversation_analysis_snapshots USING btree (company_id, profit_event_id, created_at DESC)","index_name":"idx_conversation_analysis_snapshots_company_event_created","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"conversation_analysis_snapshots"},{"definition":"CREATE UNIQUE INDEX customers_pkey ON public.customers USING btree (id)","index_name":"customers_pkey","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"customers"},{"definition":"CREATE INDEX idx_customers_company_id ON public.customers USING btree (company_id)","index_name":"idx_customers_company_id","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"customers"},{"definition":"CREATE INDEX gmail_company_sync_runs_company_time ON public.gmail_company_sync_runs USING btree (company_id, started_at DESC)","index_name":"gmail_company_sync_runs_company_time","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"gmail_company_sync_runs"},{"definition":"CREATE UNIQUE INDEX gmail_company_sync_runs_pkey ON public.gmail_company_sync_runs USING btree (id)","index_name":"gmail_company_sync_runs_pkey","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"gmail_company_sync_runs"},{"definition":"CREATE UNIQUE INDEX gmail_connections_pkey ON public.gmail_connections USING btree (id)","index_name":"gmail_connections_pkey","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"gmail_connections"},{"definition":"CREATE INDEX idx_gmail_connections_company_id ON public.gmail_connections USING btree (company_id)","index_name":"idx_gmail_connections_company_id","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"gmail_connections"},{"definition":"CREATE UNIQUE INDEX gmail_send_one_unresolved_event ON public.gmail_send_operations USING btree (company_id, profit_event_id) WHERE (status = ANY (ARRAY['sending'::text, 'unknown'::text]))","index_name":"gmail_send_one_unresolved_event","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"gmail_send_operations"},{"definition":"CREATE UNIQUE INDEX gmail_send_operations_pkey ON public.gmail_send_operations USING btree (company_id, operation_id)","index_name":"gmail_send_operations_pkey","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"gmail_send_operations"},{"definition":"CREATE UNIQUE INDEX gmail_sync_runs_pkey ON public.gmail_sync_runs USING btree (id)","index_name":"gmail_sync_runs_pkey","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"gmail_sync_runs"},{"definition":"CREATE UNIQUE INDEX gmail_work_locks_pkey ON public.gmail_work_locks USING btree (company_id)","index_name":"gmail_work_locks_pkey","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"gmail_work_locks"},{"definition":"CREATE INDEX idx_learning_logs_company_id ON public.learning_logs USING btree (company_id)","index_name":"idx_learning_logs_company_id","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"learning_logs"},{"definition":"CREATE INDEX idx_learning_logs_event_type ON public.learning_logs USING btree (event_type)","index_name":"idx_learning_logs_event_type","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"learning_logs"},{"definition":"CREATE UNIQUE INDEX learning_logs_pkey ON public.learning_logs USING btree (id)","index_name":"learning_logs_pkey","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"learning_logs"},{"definition":"CREATE INDEX idx_messages_company_id ON public.messages USING btree (company_id)","index_name":"idx_messages_company_id","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"messages"},{"definition":"CREATE INDEX idx_messages_customer_id ON public.messages USING btree (customer_id)","index_name":"idx_messages_customer_id","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"messages"},{"definition":"CREATE INDEX idx_messages_thread_id ON public.messages USING btree (thread_id)","index_name":"idx_messages_thread_id","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"messages"},{"definition":"CREATE UNIQUE INDEX messages_pkey ON public.messages USING btree (id)","index_name":"messages_pkey","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"messages"},{"definition":"CREATE INDEX idx_profiles_company ON public.profiles USING btree (company_id)","index_name":"idx_profiles_company","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"profiles"},{"definition":"CREATE INDEX idx_profiles_user ON public.profiles USING btree (user_id)","index_name":"idx_profiles_user","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"profiles"},{"definition":"CREATE UNIQUE INDEX profiles_pkey ON public.profiles USING btree (id)","index_name":"profiles_pkey","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"profiles"},{"definition":"CREATE UNIQUE INDEX profiles_user_id_key ON public.profiles USING btree (user_id)","index_name":"profiles_user_id_key","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"profiles"},{"definition":"CREATE UNIQUE INDEX profiles_user_id_unique ON public.profiles USING btree (user_id)","index_name":"profiles_user_id_unique","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"profiles"},{"definition":"CREATE INDEX idx_profit_events_company_id ON public.profit_events USING btree (company_id)","index_name":"idx_profit_events_company_id","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"profit_events"},{"definition":"CREATE INDEX idx_profit_events_customer_id ON public.profit_events USING btree (customer_id)","index_name":"idx_profit_events_customer_id","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"profit_events"},{"definition":"CREATE INDEX idx_profit_events_gmail_thread_id ON public.profit_events USING btree (company_id, gmail_thread_id)","index_name":"idx_profit_events_gmail_thread_id","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"profit_events"},{"definition":"CREATE INDEX idx_profit_events_status ON public.profit_events USING btree (status)","index_name":"idx_profit_events_status","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"profit_events"},{"definition":"CREATE UNIQUE INDEX profit_events_pkey ON public.profit_events USING btree (id)","index_name":"profit_events_pkey","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"profit_events"},{"definition":"CREATE UNIQUE INDEX reply_drafts_company_id_profit_event_id_key ON public.reply_drafts USING btree (company_id, profit_event_id)","index_name":"reply_drafts_company_id_profit_event_id_key","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"reply_drafts"},{"definition":"CREATE UNIQUE INDEX reply_drafts_pkey ON public.reply_drafts USING btree (id)","index_name":"reply_drafts_pkey","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"reply_drafts"},{"definition":"CREATE UNIQUE INDEX idx_reply_logs_company_gmail_message ON public.reply_logs USING btree (company_id, gmail_message_id) WHERE (gmail_message_id IS NOT NULL)","index_name":"idx_reply_logs_company_gmail_message","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"reply_logs"},{"definition":"CREATE INDEX idx_reply_logs_company_id ON public.reply_logs USING btree (company_id)","index_name":"idx_reply_logs_company_id","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"reply_logs"},{"definition":"CREATE INDEX idx_reply_logs_thread_id ON public.reply_logs USING btree (thread_id)","index_name":"idx_reply_logs_thread_id","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"reply_logs"},{"definition":"CREATE UNIQUE INDEX reply_logs_gmail_message_id_unique ON public.reply_logs USING btree (gmail_message_id) WHERE (gmail_message_id IS NOT NULL)","index_name":"reply_logs_gmail_message_id_unique","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"reply_logs"},{"definition":"CREATE UNIQUE INDEX reply_logs_pkey ON public.reply_logs USING btree (id)","index_name":"reply_logs_pkey","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"reply_logs"},{"definition":"CREATE UNIQUE INDEX uq_reply_logs_company_gmail_message ON public.reply_logs USING btree (company_id, gmail_message_id) WHERE (gmail_message_id IS NOT NULL)","index_name":"uq_reply_logs_company_gmail_message","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"reply_logs"},{"definition":"CREATE INDEX idx_timeline_company_id ON public.timeline USING btree (company_id)","index_name":"idx_timeline_company_id","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"timeline"},{"definition":"CREATE INDEX idx_timeline_customer_id ON public.timeline USING btree (customer_id)","index_name":"idx_timeline_customer_id","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"timeline"},{"definition":"CREATE INDEX idx_timeline_profit_event_id ON public.timeline USING btree (profit_event_id)","index_name":"idx_timeline_profit_event_id","indisready":true,"indisunique":false,"indisvalid":true,"table_name":"timeline"},{"definition":"CREATE UNIQUE INDEX timeline_pkey ON public.timeline USING btree (id)","index_name":"timeline_pkey","indisready":true,"indisunique":true,"indisvalid":true,"table_name":"timeline"}],"profiles_identity":{"duplicate_user_id_groups":0,"null_user_id_count":0},"security_definers":[{"function_signature":"public.acquire_gmail_sync_lock(p_owner_token uuid, p_lease_seconds integer)","owner":"postgres","proacl":["postgres=X/postgres","service_role=X/postgres"],"proconfig":["search_path=pg_catalog, public"],"prosrc_md5":"3a37272567e11c5021dbf51071224750"},{"function_signature":"public.apply_billing_snapshot(p_company_id uuid, p_event_id text, p_subscription_id text, p_status text, p_paid_until timestamp with time zone)","owner":"postgres","proacl":["postgres=X/postgres","service_role=X/postgres"],"proconfig":["search_path=pg_catalog, pg_temp"],"prosrc_md5":"04ea3098e11373a521c5d142f9c1f70d"},{"function_signature":"public.claim_gmail_work(p_company_id uuid, p_owner_id uuid, p_purpose text)","owner":"postgres","proacl":["postgres=X/postgres","service_role=X/postgres"],"proconfig":["search_path=pg_catalog, pg_temp"],"prosrc_md5":"3d12d706c5e98fb3a4624ca275ca4dbe"},{"function_signature":"public.create_company_and_profile(company_name text, owner_name text)","owner":"postgres","proacl":["postgres=X/postgres","authenticated=X/postgres"],"proconfig":["search_path=pg_catalog, public"],"prosrc_md5":"2cf12d00f40e7bbaeedbd24f7f41bae3"},{"function_signature":"public.ensure_company_billing(p_company_id uuid)","owner":"postgres","proacl":["postgres=X/postgres","service_role=X/postgres"],"proconfig":["search_path=pg_catalog, pg_temp"],"prosrc_md5":"8e2cbc48f6ca661aec9ba1604c8349d6"},{"function_signature":"public.finalize_gmail_send(p_company_id uuid, p_operation_id text, p_message_id text, p_thread_id text)","owner":"postgres","proacl":["postgres=X/postgres","service_role=X/postgres"],"proconfig":["search_path=pg_catalog, pg_temp"],"prosrc_md5":"1035a2a49bac9bc534a1ab771157db08"},{"function_signature":"public.onboard_user(p_user_id uuid, p_company_name text, p_name text, p_email text)","owner":"postgres","proacl":null,"proconfig":["search_path=public"],"prosrc_md5":"0c321b67f077c23f3a413abccc3e3103"},{"function_signature":"public.release_gmail_sync_lock(p_owner_token uuid)","owner":"postgres","proacl":["postgres=X/postgres","service_role=X/postgres"],"proconfig":["search_path=pg_catalog, public"],"prosrc_md5":"c11defbde027b9a1a70df2237dd2a5f2"},{"function_signature":"public.release_gmail_work(p_company_id uuid, p_owner_id uuid)","owner":"postgres","proacl":["postgres=X/postgres","service_role=X/postgres"],"proconfig":["search_path=pg_catalog, pg_temp"],"prosrc_md5":"a7cc78e6582da420d54b891880370775"},{"function_signature":"public.reserve_ai_run(p_company_id uuid, p_monthly_limit integer)","owner":"postgres","proacl":["postgres=X/postgres","service_role=X/postgres"],"proconfig":["search_path=pg_catalog, pg_temp"],"prosrc_md5":"14299d4c1d6caadb0c7dc09b2c0839ee"},{"function_signature":"public.rls_auto_enable()","owner":"postgres","proacl":null,"proconfig":["search_path=pg_catalog"],"prosrc_md5":"99be20677b456ea8d3be47bdd44fb369"}],"target_tables":[{"kind":null,"name":"account_deletion_audit","owner":null,"present":false,"relforcerowsecurity":null,"relrowsecurity":null},{"kind":null,"name":"account_deletion_jobs","owner":null,"present":false,"relforcerowsecurity":null,"relrowsecurity":null},{"kind":null,"name":"ai_budget_reservations","owner":null,"present":false,"relforcerowsecurity":null,"relrowsecurity":null},{"kind":"r","name":"ai_judgements","owner":"postgres","present":true,"relforcerowsecurity":false,"relrowsecurity":true},{"kind":"r","name":"ai_usage_runs","owner":"postgres","present":true,"relforcerowsecurity":false,"relrowsecurity":true},{"kind":null,"name":"billing_checkout_attempts","owner":null,"present":false,"relforcerowsecurity":null,"relrowsecurity":null},{"kind":null,"name":"billing_runtime_config","owner":null,"present":false,"relforcerowsecurity":null,"relrowsecurity":null},{"kind":"r","name":"billing_webhook_events","owner":"postgres","present":true,"relforcerowsecurity":false,"relrowsecurity":true},{"kind":"r","name":"calendar_events","owner":"postgres","present":true,"relforcerowsecurity":false,"relrowsecurity":true},{"kind":"r","name":"companies","owner":"postgres","present":true,"relforcerowsecurity":false,"relrowsecurity":true},{"kind":"r","name":"company_billing","owner":"postgres","present":true,"relforcerowsecurity":false,"relrowsecurity":true},{"kind":"r","name":"conversation_analysis_snapshots","owner":"postgres","present":true,"relforcerowsecurity":false,"relrowsecurity":true},{"kind":"r","name":"customers","owner":"postgres","present":true,"relforcerowsecurity":false,"relrowsecurity":true},{"kind":null,"name":"financial_payments","owner":null,"present":false,"relforcerowsecurity":null,"relrowsecurity":null},{"kind":null,"name":"financial_record_history","owner":null,"present":false,"relforcerowsecurity":null,"relrowsecurity":null},{"kind":null,"name":"financial_records","owner":null,"present":false,"relforcerowsecurity":null,"relrowsecurity":null},{"kind":"r","name":"gmail_company_sync_runs","owner":"postgres","present":true,"relforcerowsecurity":false,"relrowsecurity":true},{"kind":"r","name":"gmail_connections","owner":"postgres","present":true,"relforcerowsecurity":false,"relrowsecurity":true},{"kind":null,"name":"gmail_inbound_receipts","owner":null,"present":false,"relforcerowsecurity":null,"relrowsecurity":null},{"kind":"r","name":"gmail_send_operations","owner":"postgres","present":true,"relforcerowsecurity":false,"relrowsecurity":true},{"kind":null,"name":"gmail_sync_cursors","owner":null,"present":false,"relforcerowsecurity":null,"relrowsecurity":null},{"kind":"r","name":"gmail_sync_runs","owner":"postgres","present":true,"relforcerowsecurity":false,"relrowsecurity":true},{"kind":"r","name":"gmail_work_locks","owner":"postgres","present":true,"relforcerowsecurity":false,"relrowsecurity":true},{"kind":"r","name":"learning_logs","owner":"postgres","present":true,"relforcerowsecurity":false,"relrowsecurity":true},{"kind":"r","name":"messages","owner":"postgres","present":true,"relforcerowsecurity":false,"relrowsecurity":true},{"kind":null,"name":"operation_recovery_audit","owner":null,"present":false,"relforcerowsecurity":null,"relrowsecurity":null},{"kind":"r","name":"profiles","owner":"postgres","present":true,"relforcerowsecurity":false,"relrowsecurity":true},{"kind":"r","name":"profit_events","owner":"postgres","present":true,"relforcerowsecurity":false,"relrowsecurity":true},{"kind":"r","name":"reply_drafts","owner":"postgres","present":true,"relforcerowsecurity":false,"relrowsecurity":true},{"kind":"r","name":"reply_logs","owner":"postgres","present":true,"relforcerowsecurity":false,"relrowsecurity":true},{"kind":"r","name":"timeline","owner":"postgres","present":true,"relforcerowsecurity":false,"relrowsecurity":true}],"triggers":[],"views":[]}$remote_oracle$::jsonb AS snapshot),
observed_oracle AS (
-- Fact capture only, not an approval gate. One result set; no remote execution by Codex.
-- The two existing legacy relations profiles and gmail_sync_runs must exist.
-- No customer values or function bodies are returned. prosrc is raw md5 only.
-- Save the complete result as JSON without editing; retain this SQL with the capture.
WITH
target_tables(name) AS (VALUES
 ('account_deletion_audit'),('account_deletion_jobs'),('ai_budget_reservations'),
 ('ai_judgements'),('ai_usage_runs'),('billing_checkout_attempts'),('billing_runtime_config'),
 ('billing_webhook_events'),('calendar_events'),('companies'),('company_billing'),
 ('conversation_analysis_snapshots'),('customers'),('financial_payments'),
 ('financial_record_history'),('financial_records'),('gmail_company_sync_runs'),
 ('gmail_connections'),('gmail_inbound_receipts'),('gmail_send_operations'),
 ('gmail_sync_cursors'),('gmail_sync_runs'),('gmail_work_locks'),('learning_logs'),
 ('messages'),('operation_recovery_audit'),('profiles'),('profit_events'),
 ('reply_drafts'),('reply_logs'),('timeline')
),
expected_functions(name) AS (VALUES
 ('commit_gmail_inbound_page'),('recover_company_work'),('save_financial_record'),
 ('reserve_ai_budget'),('company_is_active'),('request_account_deletion'),
 ('purge_account_data'),('complete_account_deletion'),('purge_expired_deletion_audit'),
 ('prevent_deleted_user_onboarding'),('record_financial_payment'),('void_financial_payment'),
 ('resolve_provider_uncertainty'),('promote_billing_live'),('acquire_gmail_sync_lock'),
 ('apply_billing_snapshot'),('claim_gmail_work'),('create_company_and_profile'),
 ('ensure_company_billing'),('finalize_gmail_send'),('onboard_user'),
 ('release_gmail_sync_lock'),('release_gmail_work'),('reserve_ai_run'),('rls_auto_enable')
),
constraint_rows AS (
 SELECT c.relname AS table_name,con.conname,con.contype,con.convalidated,
 pg_catalog.pg_get_constraintdef(con.oid,false) AS definition
 FROM pg_catalog.pg_constraint con JOIN pg_catalog.pg_class c ON c.oid=con.conrelid
 JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
 JOIN target_tables t ON t.name=c.relname WHERE n.nspname='public'
),
index_rows AS (
 SELECT c.relname AS table_name,i.relname AS index_name,x.indisunique,x.indisvalid,x.indisready,
 pg_catalog.pg_get_indexdef(x.indexrelid,0,false) AS definition
 FROM pg_catalog.pg_index x JOIN pg_catalog.pg_class c ON c.oid=x.indrelid
 JOIN pg_catalog.pg_class i ON i.oid=x.indexrelid
 JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
 JOIN target_tables t ON t.name=c.relname WHERE n.nspname='public'
),
function_rows AS (
 SELECT e.name,p.oid IS NOT NULL AS present,
 pg_catalog.pg_get_function_identity_arguments(p.oid) AS identity_arguments,
 pg_catalog.pg_get_function_result(p.oid) AS result,
 pg_catalog.pg_get_userbyid(p.proowner) AS owner,p.prosecdef,p.proconfig,p.proargnames,
 pg_catalog.md5(p.prosrc) AS prosrc_md5,p.proacl,
 pg_catalog.has_function_privilege('anon',p.oid,'EXECUTE') AS anon_execute,
 pg_catalog.has_function_privilege('authenticated',p.oid,'EXECUTE') AS authenticated_execute,
 pg_catalog.has_function_privilege('service_role',p.oid,'EXECUTE') AS service_execute
 FROM expected_functions e LEFT JOIN pg_catalog.pg_proc p
 ON p.pronamespace='public'::regnamespace AND p.proname=e.name
),
event_rows AS (
 SELECT e.evtname,e.evtevent,e.evtenabled,e.evttags,
 pg_catalog.pg_get_userbyid(e.evtowner) AS trigger_owner,
 pg_catalog.format('%I.%I(%s)',n.nspname,p.proname,
 pg_catalog.pg_get_function_identity_arguments(p.oid)) AS function_signature,
 pg_catalog.format_type(p.prorettype,NULL) AS return_type,
 pg_catalog.pg_get_userbyid(p.proowner) AS function_owner,p.prosecdef,p.proconfig,p.proacl,
 pg_catalog.md5(p.prosrc) AS prosrc_md5,
 pg_catalog.has_function_privilege('anon',p.oid,'EXECUTE') AS anon_execute,
 pg_catalog.has_function_privilege('authenticated',p.oid,'EXECUTE') AS authenticated_execute,
 pg_catalog.has_function_privilege('service_role',p.oid,'EXECUTE') AS service_execute
 FROM pg_catalog.pg_event_trigger e JOIN pg_catalog.pg_proc p ON p.oid=e.evtfoid
 JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
 WHERE e.evtname='ensure_rls' OR (n.nspname='public' AND p.proname='rls_auto_enable')
),
view_rows AS (
 SELECT n.nspname AS schema,c.relname AS name,c.relkind AS kind,c.reloptions AS options,
 pg_catalog.pg_get_userbyid(c.relowner) AS owner
 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
 WHERE n.nspname='public' AND c.relkind IN ('v','m')
),
trigger_rows AS (
 SELECT c.relname AS table_name,t.tgname AS trigger_name,t.tgenabled AS enabled,
 pg_catalog.format('%I.%I(%s)',fn.nspname,p.proname,
 pg_catalog.pg_get_function_identity_arguments(p.oid)) AS function_signature,
 pg_catalog.pg_get_triggerdef(t.oid,false) AS definition
 FROM pg_catalog.pg_trigger t JOIN pg_catalog.pg_class c ON c.oid=t.tgrelid
 JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
 JOIN pg_catalog.pg_proc p ON p.oid=t.tgfoid
 JOIN pg_catalog.pg_namespace fn ON fn.oid=p.pronamespace
 WHERE n.nspname='public' AND NOT t.tgisinternal
),
definer_rows AS (
 SELECT pg_catalog.format('%I.%I(%s)',n.nspname,p.proname,
 pg_catalog.pg_get_function_identity_arguments(p.oid)) AS function_signature,
 pg_catalog.pg_get_userbyid(p.proowner) AS owner,p.proconfig,p.proacl,
 pg_catalog.md5(p.prosrc) AS prosrc_md5
 FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
 WHERE n.nspname='public' AND p.prosecdef
),
sync_columns AS (
 SELECT a.attnum AS ordinal_position,a.attname AS column_name,
 pg_catalog.format_type(a.atttypid,a.atttypmod) AS data_type,t.typname AS udt_name,
 NOT a.attnotnull AS is_nullable,pg_catalog.pg_get_expr(d.adbin,d.adrelid,false) AS column_default,
 a.attidentity AS identity_kind,a.attgenerated AS generated_kind
 FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_type t ON t.oid=a.atttypid
 LEFT JOIN pg_catalog.pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
 WHERE a.attrelid=pg_catalog.to_regclass('public.gmail_sync_runs')
 AND a.attnum>0 AND NOT a.attisdropped
),
table_rows AS (
 SELECT t.name,c.oid IS NOT NULL AS present,c.relkind AS kind,
 pg_catalog.pg_get_userbyid(c.relowner) AS owner,c.relrowsecurity,c.relforcerowsecurity
 FROM target_tables t LEFT JOIN pg_catalog.pg_class c
 ON c.oid=pg_catalog.to_regclass('public.'||t.name)
),
snapshots(oracle_name,snapshot) AS (
 SELECT 'event_trigger',coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.evtname COLLATE "C"),'[]'::jsonb) FROM event_rows r
 UNION ALL
 SELECT 'constraints',coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.table_name COLLATE "C",r.conname COLLATE "C"),'[]'::jsonb) FROM constraint_rows r
 UNION ALL
 SELECT 'indexes',coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.table_name COLLATE "C",r.index_name COLLATE "C"),'[]'::jsonb) FROM index_rows r
 UNION ALL
 SELECT 'functions',coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.name COLLATE "C",r.identity_arguments COLLATE "C" NULLS FIRST),'[]'::jsonb) FROM function_rows r
 UNION ALL
 SELECT 'views',coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.schema COLLATE "C",r.name COLLATE "C"),'[]'::jsonb) FROM view_rows r
 UNION ALL
 SELECT 'triggers',coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.table_name COLLATE "C",r.trigger_name COLLATE "C"),'[]'::jsonb) FROM trigger_rows r
 UNION ALL
 SELECT 'security_definers',coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.function_signature COLLATE "C"),'[]'::jsonb) FROM definer_rows r
 UNION ALL
 SELECT 'billing_runtime_config',pg_catalog.jsonb_build_object('present',pg_catalog.to_regclass('public.billing_runtime_config') IS NOT NULL)
 UNION ALL
 SELECT 'gmail_sync_runs',pg_catalog.jsonb_build_object(
 'columns',(SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.ordinal_position),'[]'::jsonb) FROM sync_columns r),
 'constraints',(SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.conname COLLATE "C"),'[]'::jsonb) FROM constraint_rows r WHERE r.table_name='gmail_sync_runs'),
 'indexes',(SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.index_name COLLATE "C"),'[]'::jsonb) FROM index_rows r WHERE r.table_name='gmail_sync_runs'),
 'total_rows',(SELECT pg_catalog.count(*) FROM public.gmail_sync_runs))
 UNION ALL
 SELECT 'profiles_identity',pg_catalog.jsonb_build_object(
 'null_user_id_count',(SELECT pg_catalog.count(*) FROM public.profiles WHERE user_id IS NULL),
 'duplicate_user_id_groups',(SELECT pg_catalog.count(*) FROM (SELECT user_id FROM public.profiles WHERE user_id IS NOT NULL GROUP BY user_id HAVING pg_catalog.count(*)>1) d))
 UNION ALL
 SELECT 'target_tables',coalesce(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) ORDER BY r.name COLLATE "C"),'[]'::jsonb) FROM table_rows r
)
SELECT oracle_name,snapshot FROM snapshots ORDER BY oracle_name COLLATE "C"
),
q0 AS (
SELECT 'companies.owner_user_id' AS prerequisite,
 CASE WHEN a.atttypid='uuid'::regtype THEN 'COMPATIBLE' ELSE 'MISSING_OR_INCOMPATIBLE' END AS status,
 format_type(a.atttypid,a.atttypmod) AS actual_type,a.attnotnull,
 pg_get_expr(d.adbin,d.adrelid) AS column_default,a.attidentity,a.attgenerated
 FROM (SELECT to_regclass('public.companies') oid) t
 LEFT JOIN pg_attribute a ON a.attrelid=t.oid AND a.attname='owner_user_id' AND NOT a.attisdropped
 LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
),
q1 AS (
WITH target AS (SELECT to_regclass('public.billing_checkout_attempts') AS oid),
expected(name,type_name,required,default_expr) AS (VALUES
 ('company_id','uuid',true,NULL::text),('attempt_id','uuid',true,NULL::text),
 ('session_id','text',false,NULL::text),('created_at','timestamptz',true,'now()'))
SELECT CASE WHEN t.oid IS NULL THEN 'MISSING'
 WHEN (SELECT relkind FROM pg_class WHERE oid=t.oid)<>'r'
 OR (SELECT count(*) FROM pg_attribute WHERE attrelid=t.oid AND attnum>0 AND NOT attisdropped)<>4
 OR EXISTS(SELECT 1 FROM expected e LEFT JOIN pg_attribute a ON a.attrelid=t.oid AND a.attname=e.name AND NOT a.attisdropped
   LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
   WHERE a.attnum IS NULL OR a.atttypid IS DISTINCT FROM to_regtype('pg_catalog.'||e.type_name)::oid
   OR a.attnotnull IS DISTINCT FROM e.required OR pg_get_expr(d.adbin,d.adrelid) IS DISTINCT FROM e.default_expr)
 OR (SELECT count(*) FROM pg_constraint WHERE conrelid=t.oid)<>2
 OR NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid=t.oid AND contype='p' AND convalidated
   AND conkey=ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid=t.oid AND attname='company_id')]::smallint[])
 OR NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid=t.oid AND contype='f' AND convalidated
   AND confrelid=to_regclass('public.companies') AND confdeltype='a' AND confupdtype='a'
   AND conkey=ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid=t.oid AND attname='company_id')]::smallint[]
   AND confkey=ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid=to_regclass('public.companies') AND attname='id')]::smallint[])
 OR (SELECT count(*) FROM pg_index WHERE indrelid=t.oid)<>1
 OR EXISTS(SELECT 1 FROM pg_index WHERE indrelid=t.oid AND (NOT indisvalid OR NOT indisready OR NOT indisunique OR NOT indisprimary))
 THEN 'INCOMPATIBLE' ELSE 'COMPATIBLE' END AS checkout_structure,
 (SELECT relrowsecurity FROM pg_class WHERE oid=t.oid) AS rls_enabled,
 (SELECT count(*) FROM pg_policy WHERE polrelid=t.oid) AS policy_count,
 has_any_column_privilege('anon',t.oid,'SELECT,INSERT,UPDATE,REFERENCES') AS anon_column_access,
 has_any_column_privilege('authenticated',t.oid,'SELECT,INSERT,UPDATE,REFERENCES') AS authenticated_column_access,
 has_table_privilege('service_role',t.oid,'SELECT') AS service_select,
 has_table_privilege('service_role',t.oid,'INSERT') AS service_insert,
 has_table_privilege('service_role',t.oid,'UPDATE') AS service_update,
 has_table_privilege('service_role',t.oid,'DELETE,TRUNCATE,TRIGGER,REFERENCES') AS service_extra_privileges
 FROM target t
),
q2 AS (
WITH expected(name,args,result,body,config) AS (VALUES
('onboard_user',ARRAY['p_user_id','p_company_name','p_name','p_email'],'jsonb'::regtype,convert_from(decode('0a6465636c6172650a20202020765f6578697374696e675f70726f66696c65207075626c69632e70726f66696c657325726f77747970653b0a20202020765f636f6d70616e79207075626c69632e636f6d70616e69657325726f77747970653b0a20202020765f70726f66696c65207075626c69632e70726f66696c657325726f77747970653b0a626567696e0a2020202073656c656374202a0a20202020696e746f20765f6578697374696e675f70726f66696c650a2020202066726f6d207075626c69632e70726f66696c65730a20202020776865726520757365725f6964203d20705f757365725f69640a202020206c696d697420313b0a0a20202020696620666f756e64207468656e0a202020202020202072657475726e206a736f6e625f6275696c645f6f626a656374280a2020202020202020202020202763726561746564272c2066616c73652c0a20202020202020202020202027636f6d70616e795f6964272c20765f6578697374696e675f70726f66696c652e636f6d70616e795f69642c0a2020202020202020202020202770726f66696c655f6964272c20765f6578697374696e675f70726f66696c652e69640a2020202020202020293b0a20202020656e642069663b0a0a20202020696e7365727420696e746f207075626c69632e636f6d70616e69657320280a20202020202020206e616d652c0a2020202020202020706c616e2c0a20202020202020206f776e65725f757365725f69640a20202020290a2020202076616c75657320280a20202020202020207472696d28705f636f6d70616e795f6e616d65292c0a20202020202020202766726565272c0a2020202020202020705f757365725f69640a20202020290a2020202072657475726e696e67202a0a20202020696e746f20765f636f6d70616e793b0a0a20202020696e7365727420696e746f207075626c69632e70726f66696c657320280a2020202020202020757365725f69642c0a2020202020202020636f6d70616e795f69642c0a20202020202020206e616d652c0a2020202020202020726f6c652c0a2020202020202020656d61696c0a20202020290a2020202076616c75657320280a2020202020202020705f757365725f69642c0a2020202020202020765f636f6d70616e792e69642c0a20202020202020207472696d28705f6e616d65292c0a2020202020202020276f776e6572272c0a2020202020202020705f656d61696c0a20202020290a2020202072657475726e696e67202a0a20202020696e746f20765f70726f66696c653b0a0a2020202072657475726e206a736f6e625f6275696c645f6f626a656374280a20202020202020202763726561746564272c20747275652c0a202020202020202027636f6d70616e795f6964272c20765f636f6d70616e792e69642c0a20202020202020202770726f66696c655f6964272c20765f70726f66696c652e69640a20202020293b0a656e643b0a','hex'),'UTF8'),ARRAY['search_path=public']),
('create_company_and_profile',ARRAY['company_name','owner_name'],'uuid'::regtype,convert_from(decode('0a6465636c6172650a20206e65775f636f6d70616e795f696420757569643b0a202063616c6c65725f656d61696c20746578743b0a626567696e0a2020696620617574682e7569642829206973206e756c6c207468656e0a20202020726169736520657863657074696f6e202741757468656e7469636174696f6e207265717569726564273b0a2020656e642069663b0a20206966206e756c6c6966287472696d28636f6d70616e795f6e616d65292c20272729206973206e756c6c206f72206e756c6c6966287472696d286f776e65725f6e616d65292c20272729206973206e756c6c207468656e0a20202020726169736520657863657074696f6e2027436f6d70616e79206e616d6520616e64206f776e6572206e616d6520617265207265717569726564273b0a2020656e642069663b0a2020696620657869737473202873656c65637420312066726f6d207075626c69632e70726f66696c657320776865726520757365725f6964203d20617574682e756964282929207468656e0a20202020726169736520657863657074696f6e202750726f66696c6520616c726561647920657869737473273b0a2020656e642069663b0a0a202063616c6c65725f656d61696c203a3d20636f616c6573636528617574682e6a77742829202d3e3e2027656d61696c272c202727293b0a2020696e7365727420696e746f207075626c69632e636f6d70616e696573286e616d652c20706c616e290a2020202076616c75657320287472696d28636f6d70616e795f6e616d65292c20276672656527292072657475726e696e6720696420696e746f206e65775f636f6d70616e795f69643b0a2020696e7365727420696e746f207075626c69632e70726f66696c657328757365725f69642c20636f6d70616e795f69642c206e616d652c2066756c6c5f6e616d652c20656d61696c2c20726f6c65290a2020202076616c7565732028617574682e75696428292c206e65775f636f6d70616e795f69642c207472696d286f776e65725f6e616d65292c207472696d286f776e65725f6e616d65292c2063616c6c65725f656d61696c2c20276f776e657227293b0a202072657475726e206e65775f636f6d70616e795f69643b0a656e643b0a','hex'),'UTF8'),ARRAY['search_path=pg_catalog, public']))
SELECT e.name, CASE WHEN p.oid IS NULL THEN 'MISSING'
 WHEN (SELECT count(*) FROM pg_proc WHERE pronamespace='public'::regnamespace AND proname=e.name)<>1
 OR p.proowner<>'postgres'::regrole OR NOT p.prosecdef OR p.prolang<>(SELECT oid FROM pg_language WHERE lanname='plpgsql')
 OR p.proargnames IS DISTINCT FROM e.args OR p.prorettype<>e.result OR p.proretset
 OR replace(p.prosrc,chr(13)||chr(10),chr(10))<>replace(e.body,chr(13)||chr(10),chr(10))
 OR p.proconfig IS DISTINCT FROM e.config THEN 'UNKNOWN_OR_HARDENED_REVIEW_ACL'
 ELSE 'EXACT_CAPTURED_BODY_AND_CONTRACT' END AS identity,
 p.proconfig,p.proacl,pg_get_function_identity_arguments(p.oid) AS arguments,
 has_function_privilege('anon',p.oid,'EXECUTE') AS anon_execute,
 has_function_privilege('authenticated',p.oid,'EXECUTE') AS authenticated_execute,
 has_function_privilege('service_role',p.oid,'EXECUTE') AS service_execute
FROM expected e LEFT JOIN pg_proc p ON p.pronamespace='public'::regnamespace AND p.proname=e.name
),
q4 AS (
WITH targets(name) AS (VALUES ('account_deletion_audit'),('account_deletion_jobs'),('ai_budget_reservations'),('ai_judgements'),('ai_usage_runs'),('billing_checkout_attempts'),('billing_runtime_config'),('billing_webhook_events'),('calendar_events'),('companies'),('company_billing'),('conversation_analysis_snapshots'),('customers'),('financial_payments'),('financial_record_history'),('financial_records'),('gmail_company_sync_runs'),('gmail_connections'),('gmail_inbound_receipts'),('gmail_send_operations'),('gmail_sync_cursors'),('gmail_sync_runs'),('gmail_work_locks'),('learning_logs'),('messages'),('operation_recovery_audit'),('profiles'),('profit_events'),('reply_drafts'),('reply_logs'),('timeline'))
SELECT t.name,c.relkind,pg_get_userbyid(c.relowner) AS owner,c.relrowsecurity,c.relforcerowsecurity,
 c.oid IS NOT NULL AS present FROM targets t LEFT JOIN pg_class c ON c.oid=to_regclass('public.'||t.name)
ORDER BY t.name
),
q5 AS (
WITH expected(table_name,column_name,type_name) AS (VALUES
('account_deletion_audit','id','uuid'),
('account_deletion_audit','job_id','uuid'),
('account_deletion_audit','stage','text'),
('account_deletion_audit','created_at','timestamptz'),
('account_deletion_jobs','id','uuid'),
('account_deletion_jobs','company_id','uuid'),
('account_deletion_jobs','user_id','uuid'),
('account_deletion_jobs','status','text'),
('account_deletion_jobs','gmail_done','bool'),
('account_deletion_jobs','billing_done','bool'),
('account_deletion_jobs','billing_reference','text'),
('account_deletion_jobs','last_error_code','text'),
('account_deletion_jobs','requested_at','timestamptz'),
('account_deletion_jobs','completed_at','timestamptz'),
('account_deletion_jobs','purge_after','timestamptz'),
('ai_budget_reservations','id','uuid'),
('ai_budget_reservations','company_id','uuid'),
('ai_budget_reservations','model','text'),
('ai_budget_reservations','reserved_tokens','int8'),
('ai_budget_reservations','reserved_cost_micro_usd','int8'),
('ai_budget_reservations','token_limit','int8'),
('ai_budget_reservations','cost_limit_micro_usd','int8'),
('ai_budget_reservations','status','text'),
('ai_budget_reservations','actual_input_tokens','int8'),
('ai_budget_reservations','actual_output_tokens','int8'),
('ai_budget_reservations','created_at','timestamptz'),
('ai_judgements','id','uuid'),
('ai_judgements','company_id','uuid'),
('ai_judgements','customer_id','uuid'),
('ai_judgements','profit_event_id','uuid'),
('ai_judgements','provider','text'),
('ai_judgements','score','int4'),
('ai_judgements','priority','text'),
('ai_judgements','risk','text'),
('ai_judgements','reason','text'),
('ai_judgements','next_action','text'),
('ai_judgements','raw_input','jsonb'),
('ai_judgements','raw_output','jsonb'),
('ai_judgements','created_at','timestamptz'),
('ai_usage_runs','id','uuid'),
('ai_usage_runs','company_id','uuid'),
('ai_usage_runs','status','text'),
('ai_usage_runs','created_at','timestamptz'),
('ai_usage_runs','elapsed_ms','int4'),
('ai_usage_runs','input_tokens','int4'),
('ai_usage_runs','output_tokens','int4'),
('ai_usage_runs','cost_usd','numeric'),
('billing_checkout_attempts','company_id','uuid'),
('billing_checkout_attempts','attempt_id','uuid'),
('billing_checkout_attempts','session_id','text'),
('billing_checkout_attempts','created_at','timestamptz'),
('billing_runtime_config','singleton','bool'),
('billing_runtime_config','mode','text'),
('billing_runtime_config','approval_ref','text'),
('billing_runtime_config','approved_at','timestamptz'),
('billing_webhook_events','event_id','text'),
('billing_webhook_events','company_id','uuid'),
('billing_webhook_events','processed_at','timestamptz'),
('calendar_events','id','uuid'),
('calendar_events','company_id','uuid'),
('calendar_events','customer_id','uuid'),
('calendar_events','profit_event_id','uuid'),
('calendar_events','provider','text'),
('calendar_events','title','text'),
('calendar_events','description','text'),
('calendar_events','meeting_url','text'),
('calendar_events','external_id','text'),
('calendar_events','starts_at','timestamptz'),
('calendar_events','ends_at','timestamptz'),
('calendar_events','created_at','timestamptz'),
('companies','id','uuid'),
('companies','name','text'),
('companies','plan','text'),
('companies','created_at','timestamptz'),
('company_billing','company_id','uuid'),
('company_billing','trial_ends_at','timestamptz'),
('company_billing','status','text'),
('company_billing','stripe_subscription_id','text'),
('company_billing','paid_until','timestamptz'),
('company_billing','updated_at','timestamptz'),
('conversation_analysis_snapshots','id','uuid'),
('conversation_analysis_snapshots','company_id','uuid'),
('conversation_analysis_snapshots','profit_event_id','uuid'),
('conversation_analysis_snapshots','analysis_version','text'),
('conversation_analysis_snapshots','payload','jsonb'),
('conversation_analysis_snapshots','provider','text'),
('conversation_analysis_snapshots','model','text'),
('conversation_analysis_snapshots','created_at','timestamptz'),
('customers','id','uuid'),
('customers','company_id','uuid'),
('customers','name','text'),
('customers','email','text'),
('customers','phone','text'),
('customers','company_name','text'),
('customers','status','text'),
('customers','total_estimated_profit','int8'),
('customers','total_actual_profit','int8'),
('customers','last_contact_at','timestamptz'),
('customers','created_at','timestamptz'),
('customers','updated_at','timestamptz'),
('financial_payments','id','uuid'),
('financial_payments','company_id','uuid'),
('financial_payments','profit_event_id','uuid'),
('financial_payments','customer_id','uuid'),
('financial_payments','amount','int8'),
('financial_payments','paid_at','timestamptz'),
('financial_payments','created_by','uuid'),
('financial_payments','created_at','timestamptz'),
('financial_payments','voided_at','timestamptz'),
('financial_payments','voided_by','uuid'),
('financial_payments','void_reason','text'),
('financial_record_history','id','uuid'),
('financial_record_history','company_id','uuid'),
('financial_record_history','profit_event_id','uuid'),
('financial_record_history','actor_id','uuid'),
('financial_record_history','version','int8'),
('financial_record_history','previous_record','jsonb'),
('financial_record_history','new_record','jsonb'),
('financial_record_history','created_at','timestamptz'),
('financial_records','company_id','uuid'),
('financial_records','profit_event_id','uuid'),
('financial_records','customer_id','uuid'),
('financial_records','expected_revenue','int8'),
('financial_records','ordered_revenue','int8'),
('financial_records','paid_amount','int8'),
('financial_records','cost','int8'),
('financial_records','occurred_at','timestamptz'),
('financial_records','confirmed_at','timestamptz'),
('financial_records','paid_at','timestamptz'),
('financial_records','source','text'),
('financial_records','created_by','uuid'),
('financial_records','version','int8'),
('financial_records','updated_at','timestamptz'),
('gmail_company_sync_runs','id','uuid'),
('gmail_company_sync_runs','company_id','uuid'),
('gmail_company_sync_runs','status','text'),
('gmail_company_sync_runs','started_at','timestamptz'),
('gmail_company_sync_runs','finished_at','timestamptz'),
('gmail_company_sync_runs','error_code','text'),
('gmail_company_sync_runs','detected_count','int4'),
('gmail_connections','id','uuid'),
('gmail_connections','company_id','uuid'),
('gmail_connections','profile_id','uuid'),
('gmail_connections','email','text'),
('gmail_connections','token_json','jsonb'),
('gmail_connections','status','text'),
('gmail_connections','last_synced_at','timestamptz'),
('gmail_connections','created_at','timestamptz'),
('gmail_connections','updated_at','timestamptz'),
('gmail_inbound_receipts','company_id','uuid'),
('gmail_inbound_receipts','mailbox','text'),
('gmail_inbound_receipts','gmail_message_id','text'),
('gmail_inbound_receipts','profit_event_id','uuid'),
('gmail_inbound_receipts','outcome','text'),
('gmail_inbound_receipts','created_at','timestamptz'),
('gmail_send_operations','company_id','uuid'),
('gmail_send_operations','profit_event_id','uuid'),
('gmail_send_operations','customer_id','uuid'),
('gmail_send_operations','operation_id','text'),
('gmail_send_operations','request_hash','text'),
('gmail_send_operations','status','text'),
('gmail_send_operations','recipient','text'),
('gmail_send_operations','subject','text'),
('gmail_send_operations','body','text'),
('gmail_send_operations','gmail_message_id','text'),
('gmail_send_operations','gmail_thread_id','text'),
('gmail_send_operations','created_at','timestamptz'),
('gmail_send_operations','updated_at','timestamptz'),
('gmail_sync_cursors','company_id','uuid'),
('gmail_sync_cursors','mailbox','text'),
('gmail_sync_cursors','version','int8'),
('gmail_sync_cursors','mode','text'),
('gmail_sync_cursors','history_id','text'),
('gmail_sync_cursors','page_token','text'),
('gmail_sync_cursors','initial_since','int8'),
('gmail_sync_cursors','pending_ids','jsonb'),
('gmail_sync_cursors','pending_page','jsonb'),
('gmail_sync_cursors','last_page_at','timestamptz'),
('gmail_sync_cursors','last_successful_sync','timestamptz'),
('gmail_sync_runs','id','uuid'),
('gmail_sync_runs','status','text'),
('gmail_sync_runs','started_at','timestamptz'),
('gmail_sync_runs','finished_at','timestamptz'),
('gmail_work_locks','company_id','uuid'),
('gmail_work_locks','owner_id','uuid'),
('gmail_work_locks','purpose','text'),
('gmail_work_locks','acquired_at','timestamptz'),
('learning_logs','id','uuid'),
('learning_logs','company_id','uuid'),
('learning_logs','customer_id','uuid'),
('learning_logs','profit_event_id','uuid'),
('learning_logs','event_type','text'),
('learning_logs','input_data','jsonb'),
('learning_logs','result_data','jsonb'),
('learning_logs','success','bool'),
('learning_logs','actual_profit','int8'),
('learning_logs','created_at','timestamptz'),
('messages','id','uuid'),
('messages','company_id','uuid'),
('messages','customer_id','uuid'),
('messages','channel','text'),
('messages','direction','text'),
('messages','sender','text'),
('messages','recipient','text'),
('messages','subject','text'),
('messages','body','text'),
('messages','external_id','text'),
('messages','thread_id','text'),
('messages','sent_at','timestamptz'),
('messages','received_at','timestamptz'),
('messages','created_at','timestamptz'),
('operation_recovery_audit','id','uuid'),
('operation_recovery_audit','company_id','uuid'),
('operation_recovery_audit','owner_id','uuid'),
('operation_recovery_audit','purpose','text'),
('operation_recovery_audit','operator_ref','text'),
('operation_recovery_audit','ticket_ref','text'),
('operation_recovery_audit','stopped_workers_confirmed','bool'),
('operation_recovery_audit','recovered_at','timestamptz'),
('profiles','id','uuid'),
('profiles','user_id','uuid'),
('profiles','company_id','uuid'),
('profiles','email','text'),
('profiles','full_name','text'),
('profiles','role','text'),
('profiles','created_at','timestamptz'),
('profiles','name','text'),
('profit_events','id','uuid'),
('profit_events','company_id','uuid'),
('profit_events','customer_id','uuid'),
('profit_events','source_message_id','uuid'),
('profit_events','title','text'),
('profit_events','status','text'),
('profit_events','category','text'),
('profit_events','estimated_profit','int8'),
('profit_events','actual_profit','int8'),
('profit_events','opportunity_score','int4'),
('profit_events','roi_score','int4'),
('profit_events','hot_lead','bool'),
('profit_events','risk_level','text'),
('profit_events','next_action','text'),
('profit_events','due_at','timestamptz'),
('profit_events','closed_at','timestamptz'),
('profit_events','created_at','timestamptz'),
('profit_events','updated_at','timestamptz'),
('profit_events','gmail_thread_id','text'),
('profit_events','last_gmail_message_id','text'),
('profit_events','recoverable_profit','int8'),
('profit_events','neglected_days','int4'),
('profit_events','description','text'),
('reply_drafts','company_id','uuid'),
('reply_drafts','profit_event_id','uuid'),
('reply_drafts','body','text'),
('reply_drafts','subject','text'),
('reply_drafts','updated_at','timestamptz'),
('reply_logs','id','uuid'),
('reply_logs','company_id','uuid'),
('reply_logs','customer_id','uuid'),
('reply_logs','profit_event_id','uuid'),
('reply_logs','message_id','uuid'),
('reply_logs','channel','text'),
('reply_logs','reply_body','text'),
('reply_logs','reply_at','timestamptz'),
('reply_logs','detected_at','timestamptz'),
('reply_logs','external_id','text'),
('reply_logs','thread_id','text'),
('reply_logs','created_at','timestamptz'),
('reply_logs','gmail_message_id','text'),
('reply_logs','gmail_thread_id','text'),
('timeline','id','uuid'),
('timeline','company_id','uuid'),
('timeline','customer_id','uuid'),
('timeline','profit_event_id','uuid'),
('timeline','event_type','text'),
('timeline','channel','text'),
('timeline','title','text'),
('timeline','description','text'),
('timeline','amount','int8'),
('timeline','occurred_at','timestamptz'),
('timeline','metadata','jsonb'),
('timeline','created_at','timestamptz'))
SELECT e.*,a.atttypid::regtype AS actual_type,a.attnotnull,pg_get_expr(d.adbin,d.adrelid) AS default_expression,
 a.attnum IS NOT NULL AS present FROM expected e
 LEFT JOIN pg_attribute a ON a.attrelid=to_regclass('public.'||e.table_name) AND a.attname=e.column_name AND a.attnum>0 AND NOT a.attisdropped
 LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum ORDER BY 1,2
),
q6 AS (
WITH expected(t,c,typ) AS (VALUES
 ('profit_events','description','text'),('profit_events','neglected_days','int4'),('profit_events','recoverable_profit','int8'))
SELECT e.*,CASE WHEN a.attnum IS NULL THEN 'ADD_NULLABLE'
 WHEN a.atttypid=to_regtype(e.typ) AND a.atttypmod=-1 AND NOT a.attnotnull AND d.adbin IS NULL
 AND a.attidentity='' AND a.attgenerated='' THEN 'COMPATIBLE' ELSE 'STOP_COLUMN_DRIFT' END AS decision
FROM expected e LEFT JOIN pg_attribute a ON a.attrelid=to_regclass('public.'||e.t) AND a.attname=e.c AND NOT a.attisdropped
LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
),
q9 AS (
WITH expected AS (SELECT $policy_oracle$[{"cmd":"INSERT","qual":null,"roles":["authenticated"],"tablename":"companies","permissive":"PERMISSIVE","policyname":"companies_insert_own","schemaname":"public","with_check":"(owner_user_id = auth.uid())"},{"cmd":"SELECT","qual":"((owner_user_id = auth.uid()) OR (EXISTS ( SELECT 1\n   FROM profiles\n  WHERE ((profiles.company_id = companies.id) AND (profiles.user_id = auth.uid())))))","roles":["authenticated"],"tablename":"companies","permissive":"PERMISSIVE","policyname":"companies_select_member_or_owner","schemaname":"public","with_check":null},{"cmd":"SELECT","qual":"(user_id = auth.uid())","roles":["authenticated"],"tablename":"profiles","permissive":"PERMISSIVE","policyname":"profiles_select_own","schemaname":"public","with_check":null},{"cmd":"UPDATE","qual":"(user_id = auth.uid())","roles":["authenticated"],"tablename":"profiles","permissive":"PERMISSIVE","policyname":"profiles_update_own","schemaname":"public","with_check":null}]$policy_oracle$::jsonb snapshot),
actual AS (SELECT coalesce(jsonb_agg(to_jsonb(p) ORDER BY p.tablename,p.policyname),'[]'::jsonb) snapshot
 FROM pg_policies p WHERE schemaname='public' AND tablename IN ('companies','profiles','customers','messages','profit_events','timeline','reply_logs','ai_judgements','learning_logs','calendar_events','gmail_connections'))
SELECT CASE WHEN actual.snapshot=expected.snapshot THEN 'EXACT_REMOTE_POLICY_MATCH' ELSE 'STOP_POLICY_DRIFT' END AS policy_gate,
 actual.snapshot AS observed FROM actual CROSS JOIN expected
),
q11 AS (
SELECT c.relname,a.grantee,CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END AS role_name,
 a.privilege_type,a.is_grantable FROM pg_class c CROSS JOIN LATERAL aclexplode(coalesce(c.relacl,acldefault('r',c.relowner))) a
 WHERE c.relnamespace='public'::regnamespace AND c.relkind IN ('r','v','m') ORDER BY 1,2,4
),
q12 AS (
SELECT c.relname,col.attname,a.grantee,a.privilege_type,a.is_grantable FROM pg_attribute col
 JOIN pg_class c ON c.oid=col.attrelid CROSS JOIN LATERAL aclexplode(col.attacl) a
 WHERE c.relnamespace='public'::regnamespace ORDER BY 1,2,3
),
q14 AS (
SELECT pg_get_userbyid(roleid) AS granted_role,pg_get_userbyid(member) AS member_role,admin_option
 FROM pg_auth_members ORDER BY 1,2
),
q15 AS (
SELECT r.role,has_schema_privilege(r.role,'public','USAGE') AS usage,has_schema_privilege(r.role,'public','CREATE') AS create_privilege
 FROM (VALUES('anon'),('authenticated'),('service_role')) r(role)
),
q16 AS (
WITH targets(t) AS (VALUES ('companies'),('profiles'),('customers'),('messages'),('profit_events'),('timeline'),
 ('reply_logs'),('ai_judgements'),('learning_logs'),('calendar_events'),('gmail_connections')),
desired AS (SELECT t,r,p,(r='authenticated' AND t IN ('companies','profiles') AND p='SELECT') allowed
 FROM targets CROSS JOIN (VALUES('anon'),('authenticated')) roles(r)
 CROSS JOIN (VALUES('SELECT'),('INSERT'),('UPDATE'),('DELETE'),('TRUNCATE'),('TRIGGER'),('REFERENCES')) privileges(p))
SELECT *,has_table_privilege(r,to_regclass('public.'||t),p) effective,
 CASE WHEN to_regclass('public.'||t) IS NULL THEN 'STOP_MISSING_TABLE'
 WHEN has_table_privilege(r,to_regclass('public.'||t),p)=allowed THEN 'MATCH'
 WHEN allowed THEN 'REQUIRED_SELECT_MISSING_REVIEW_RLS' ELSE 'NEEDS_REVOKE' END AS decision FROM desired ORDER BY t,r,p
),
q17 AS (
SELECT n.nspname,x.grantee,CASE WHEN x.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(x.grantee) END AS grantee_name,
 x.privilege_type,x.is_grantable FROM pg_namespace n CROSS JOIN LATERAL aclexplode(n.nspacl) x WHERE n.nspname='public'
),
q18 AS (
SELECT c.relname,p.privilege,has_table_privilege('service_role',c.oid,p.privilege) required_service_access
 FROM pg_class c CROSS JOIN (VALUES('SELECT'),('INSERT'),('UPDATE'),('DELETE')) p(privilege)
 WHERE c.relnamespace='public'::regnamespace AND c.relname IN ('companies','profiles','customers','messages','profit_events',
 'timeline','reply_logs','ai_judgements','learning_logs','calendar_events','gmail_connections') ORDER BY 1,2
),
q19 AS (
WITH expected(name) AS (VALUES ('commit_gmail_inbound_page'),('recover_company_work'),('save_financial_record'),('reserve_ai_budget'),('company_is_active'),('request_account_deletion'),('purge_account_data'),('complete_account_deletion'),('purge_expired_deletion_audit'),('prevent_deleted_user_onboarding'),('record_financial_payment'),('void_financial_payment'),('resolve_provider_uncertainty'),('promote_billing_live'),('acquire_gmail_sync_lock'),('apply_billing_snapshot'),('claim_gmail_work'),('create_company_and_profile'),('ensure_company_billing'),('finalize_gmail_send'),('onboard_user'),('release_gmail_sync_lock'),('release_gmail_work'),('reserve_ai_run'),('rls_auto_enable'))
SELECT e.name,p.oid IS NOT NULL AS present,pg_get_function_identity_arguments(p.oid) AS arguments,
 pg_get_function_result(p.oid) AS result,pg_get_userbyid(p.proowner) AS owner,p.prosecdef,p.proconfig,
 p.proargnames,md5(p.prosrc) AS body_md5,p.proacl,
 has_function_privilege('anon',p.oid,'EXECUTE') AS anon_execute,
 has_function_privilege('authenticated',p.oid,'EXECUTE') AS authenticated_execute,
 has_function_privilege('service_role',p.oid,'EXECUTE') AS service_execute
 FROM expected e LEFT JOIN pg_proc p ON p.pronamespace='public'::regnamespace AND p.proname=e.name ORDER BY 1,3
),
q24 AS (
WITH expected(name,typ,nn,def) AS (VALUES ('id','uuid',true,'gen_random_uuid()'),
 ('status','text',true,NULL),
 ('started_at','timestamptz',true,'now()'),
 ('finished_at','timestamptz',false,NULL),
 ('company_count','int4',true,'0'),
 ('success_count','int4',true,'0'),
 ('failure_count','int4',true,'0'),
 ('detected_reply_count','int4',true,'0'),
 ('error_summary','jsonb',true,'''[]''::jsonb')),
 actual AS (
 SELECT a.attname::text AS name,t.typname::text AS typ,a.attnotnull AS nn,
 pg_get_expr(d.adbin,d.adrelid) AS def,a.atttypmod,a.attidentity,a.attgenerated
 FROM pg_attribute a JOIN pg_type t ON t.oid=a.atttypid
 LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
 WHERE a.attrelid='public.gmail_sync_runs'::regclass AND a.attnum>0 AND NOT a.attisdropped)
 SELECT 1 FROM expected e FULL JOIN actual a USING(name)
 WHERE e.name IS NULL OR a.name IS NULL OR e.typ IS DISTINCT FROM a.typ
 OR e.nn IS DISTINCT FROM a.nn OR e.def IS DISTINCT FROM a.def
 OR a.atttypmod<>-1 OR a.attidentity<>'' OR a.attgenerated<>''

),
q25 AS (
SELECT count(*) AS legacy_sync_row_count,
 CASE WHEN count(*)=0 THEN 'EMPTY_AT_CAPTURE' ELSE 'STOP_GLOBAL_SYNC_ROWS_REVIEW' END AS legacy_review
 FROM public.gmail_sync_runs
),
q26 AS (
SELECT count(*) FILTER (WHERE user_id IS NULL) AS null_user_ids,
 (SELECT count(*) FROM (SELECT user_id FROM public.profiles GROUP BY user_id HAVING count(*)>1) d) AS duplicate_groups
 FROM public.profiles
),
checks(gate,ok,remediable,detail) AS (
 SELECT 'V2-0 owner_user_id',
 coalesce((SELECT status='COMPATIBLE' AND NOT attnotnull AND column_default='auth.uid()'
 AND attidentity='' AND attgenerated='' FROM q0),false),false,'exact ownership column contract'
 UNION ALL SELECT 'V2-A checkout',
 (SELECT checkout_structure IN ('MISSING','COMPATIBLE') FROM q1)
 AND NOT EXISTS(SELECT 1 FROM pg_attribute WHERE attrelid=to_regclass('public.billing_checkout_attempts')
 AND attnum>0 AND NOT attisdropped AND (attidentity<>'' OR attgenerated<>'' OR atttypmod<>-1)),
 false,'missing or approved four-column structure'
 UNION ALL SELECT 'V2-B onboarding',
 (SELECT count(*)=2 AND bool_and(identity='EXACT_CAPTURED_BODY_AND_CONTRACT') FROM q2)
 AND NOT EXISTS(SELECT 1 FROM pg_proc p WHERE p.pronamespace='public'::regnamespace
 AND p.proname IN ('onboard_user','create_company_and_profile') AND (
 p.prokind<>'f' OR p.provolatile<>'v' OR p.proisstrict OR p.proleakproof OR p.proparallel<>'u'
 OR p.pronargdefaults<>0 OR p.proargmodes IS NOT NULL OR p.proallargtypes IS NOT NULL
 OR p.proargtypes::text<>CASE p.proname WHEN 'onboard_user' THEN '2950 25 25 25' ELSE '25 25' END
 OR CASE WHEN p.proname='onboard_user' THEN p.proacl IS NOT NULL
 ELSE NOT coalesce((SELECT count(*)=2 AND bool_and(privilege_type='EXECUTE' AND NOT is_grantable
 AND grantor='postgres'::regrole AND grantee IN ('postgres'::regrole,'authenticated'::regrole))
 FROM aclexplode(p.proacl)),false) END))
 AND (SELECT bool_and(CASE name WHEN 'onboard_user' THEN anon_execute AND authenticated_execute AND service_execute
 ELSE NOT anon_execute AND authenticated_execute AND NOT service_execute END) FROM q2),
 true,'exact legacy baseline; onboard_user requires v2 remediation'
 UNION ALL SELECT 'tables',
 NOT EXISTS(SELECT 1 FROM q4 WHERE
 CASE WHEN name='billing_checkout_attempts' THEN present AND (relkind<>'r' OR owner NOT IN ('postgres','supabase_admin'))
 WHEN name=ANY(ARRAY['gmail_sync_cursors','gmail_inbound_receipts','operation_recovery_audit','financial_records','financial_record_history','ai_budget_reservations','account_deletion_jobs','account_deletion_audit','financial_payments','billing_runtime_config','billing_checkout_attempts']) THEN present
 ELSE NOT present OR relkind<>'r' OR owner NOT IN ('postgres','supabase_admin') OR NOT relrowsecurity END),
 false,'31 targets: expected 20 present / 11 absent; approved checkout may exist'
 UNION ALL SELECT 'legacy columns',
 NOT EXISTS(SELECT 1 FROM q5 WHERE NOT table_name=ANY(ARRAY['gmail_sync_cursors','gmail_inbound_receipts','operation_recovery_audit','financial_records','financial_record_history','ai_budget_reservations','account_deletion_jobs','account_deletion_audit','financial_payments','billing_runtime_config','billing_checkout_attempts'])
 AND NOT (table_name='profit_events' AND column_name IN ('description','neglected_days','recoverable_profit'))
 AND (NOT present OR actual_type IS DISTINCT FROM to_regtype('pg_catalog.'||type_name)))
 AND NOT EXISTS(SELECT 1 FROM q6 WHERE decision NOT IN ('ADD_NULLABLE','COMPATIBLE')),
 false,'required legacy types and safe nullable additions'
 UNION ALL SELECT 'policies',(SELECT policy_gate='EXACT_REMOTE_POLICY_MATCH' FROM q9)
 AND NOT EXISTS(SELECT 1 FROM pg_policies WHERE schemaname='public'
 AND tablename IN (SELECT name FROM q4) AND tablename NOT IN ('companies','profiles')),
 false,'authoritative four-policy snapshot; no extra target policies'
 UNION ALL SELECT 'ACL',
 NOT EXISTS(SELECT 1 FROM q11 WHERE role_name NOT IN ('PUBLIC','postgres','supabase_admin','anon','authenticated','service_role'))
 AND NOT EXISTS(SELECT 1 FROM q12 WHERE grantee NOT IN (0,'postgres'::regrole,'supabase_admin'::regrole,'anon'::regrole,'authenticated'::regrole,'service_role'::regrole))
 AND NOT EXISTS(SELECT 1 FROM pg_auth_members WHERE member IN ('anon'::regrole,'authenticated'::regrole,'service_role'::regrole))
 AND NOT EXISTS(SELECT 1 FROM q15 WHERE create_privilege OR NOT usage)
 AND NOT EXISTS(SELECT 1 FROM q17 WHERE privilege_type='CREATE' AND grantee_name NOT IN ('postgres','supabase_admin','pg_database_owner'))
 AND NOT EXISTS(SELECT 1 FROM q18 WHERE required_service_access IS DISTINCT FROM true)
 AND NOT EXISTS(SELECT 1 FROM q16 WHERE decision NOT IN ('MATCH','NEEDS_REVOKE')),
 EXISTS(SELECT 1 FROM q16 WHERE decision='NEEDS_REVOKE'),
 'known explicit browser excess is remediable; unknown grantees/inheritance stop'
 UNION ALL SELECT 'profiles identity',(SELECT null_user_ids=0 AND duplicate_groups=0 FROM q26),false,'aggregate null and duplicate counts must be zero'
 UNION ALL SELECT 'gmail_sync_runs columns/rows',NOT EXISTS(SELECT 1 FROM q24)
 AND (SELECT legacy_sync_row_count=0 FROM q25),false,'exact nine global columns; no company_id; zero rows'
 UNION ALL SELECT 'gmail_sync_runs constraints',
 (SELECT count(*)=2 FROM pg_constraint WHERE conrelid='public.gmail_sync_runs'::regclass)
 AND EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='public.gmail_sync_runs'::regclass AND contype='p' AND convalidated
 AND conkey=ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid='public.gmail_sync_runs'::regclass AND attname='id')]::smallint[])
 AND EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='public.gmail_sync_runs'::regclass AND contype='c' AND convalidated
 AND pg_get_expr(conbin,conrelid)=$status$(status = ANY (ARRAY['running'::text, 'completed'::text, 'failed'::text, 'skipped'::text]))$status$)
 AND (SELECT count(*)=1 AND bool_and(i.indisprimary AND i.indisunique AND i.indisvalid AND i.indisready
 AND i.indpred IS NULL AND i.indexprs IS NULL AND i.indnatts=1 AND i.indnkeyatts=1
 AND c.relname='gmail_sync_runs_pkey') FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid WHERE i.indrelid='public.gmail_sync_runs'::regclass),
 false,'known primary key/status constraint and sole primary index'
 UNION ALL SELECT 'billing_runtime_config',to_regclass('public.billing_runtime_config') IS NULL,false,
 'absent expected; existing configuration requires approved exact structure/state evidence'
),
results AS (
 SELECT gate,CASE WHEN ok IS DISTINCT FROM true THEN 'STOP' WHEN remediable THEN 'KNOWN_REMEDIABLE' ELSE 'PASS' END AS status,detail FROM checks
 UNION ALL
 SELECT 'oracle ' || e.key,
 CASE WHEN a.snapshot IS NOT DISTINCT FROM e.value THEN 'PASS' ELSE 'STOP' END,
 'exact remote metadata snapshot comparison'
 FROM approved_oracle o CROSS JOIN LATERAL pg_catalog.jsonb_each(o.snapshot) e
 LEFT JOIN observed_oracle a ON a.oracle_name=e.key
)
SELECT gate,status,detail FROM (
 SELECT 0 AS ordering,gate,status,detail FROM results
 UNION ALL SELECT 1,'FINAL',CASE WHEN EXISTS(SELECT 1 FROM results WHERE status='STOP') THEN 'STOP' ELSE 'PASS' END,
 'Exact approved pre-apply baseline; known remediation is not a hardened state'
) final_results ORDER BY ordering,gate;
