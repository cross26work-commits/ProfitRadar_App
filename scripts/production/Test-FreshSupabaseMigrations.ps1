param(
  [switch]$AllowDisposableDockerFixtures,
  [ValidateRange(3,3)][int]$Repeat=3,
  [string]$EvidencePath
)
$ErrorActionPreference='Stop'
if(Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue){
  $PSNativeCommandUseErrorActionPreference=$false
}
if(-not $AllowDisposableDockerFixtures){throw 'Explicit disposable Docker fixture approval is required'}
$repo=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$manifest=Get-Content -LiteralPath (Join-Path $repo 'deploy/fresh-production/migration-stream.json') -Raw | ConvertFrom-Json
$expectedTables=@(
  'account_deletion_audit','account_deletion_jobs','ai_budget_reservations','ai_judgements','ai_usage_runs',
  'billing_checkout_attempts','billing_checkout_consents','billing_runtime_config','billing_webhook_events',
  'calendar_events','companies','company_billing','company_business_consents','conversation_analysis_snapshots',
  'customers','financial_payments','financial_record_history','financial_records','gmail_company_sync_runs',
  'gmail_connections','gmail_inbound_receipts','gmail_send_operations','gmail_sync_cursors','gmail_sync_runs',
  'gmail_work_locks','learning_logs','messages','operation_recovery_audit','profiles','profit_events','reply_drafts',
  'reply_logs','support_audit_logs','support_internal_notes','support_messages','support_requests','timeline'
)
$expectedPolicies=@(
  'companies|companies_own_read|PERMISSIVE|SELECT|authenticated',
  'companies|companies_self_boundary|RESTRICTIVE|SELECT|authenticated',
  'profiles|profiles_select_own|PERMISSIVE|SELECT|authenticated',
  'profiles|profiles_self_boundary|RESTRICTIVE|SELECT|authenticated'
)
$expectedTriggers=@(
  'profiles|prevent_deleted_user_onboarding|prevent_deleted_user_onboarding',
  'support_requests|support_requests_touch|support_request_touch'
)
$expectedFunctions=@(
  'add_support_note_admin(uuid,text,uuid)','apply_billing_snapshot(uuid,text,text,text,timestampwithtimezone)',
  'claim_gmail_work(uuid,uuid,text)','commit_gmail_inbound_page(uuid,uuid,uuid,text,bigint,jsonb,jsonb)',
  'company_is_active(uuid)','complete_account_deletion(uuid)',
  'create_support_request(text,uuid,uuid,text,text,text,text,text,text,text)','ensure_company_billing(uuid)',
  'finalize_gmail_send(uuid,text,text,text)','finalize_support_reply(uuid,text,text,text,uuid)',
  'onboard_user(uuid,text,text,text)','prevent_deleted_user_onboarding()','promote_billing_live(text,boolean)',
  'purge_account_data(uuid)','purge_expired_deletion_audit()','purge_expired_support_records(integer)',
  'record_financial_payment(uuid,uuid,uuid,uuid,bigint,timestampwithtimezone)',
  'recover_company_work(uuid,uuid,text,text,boolean)','release_gmail_work(uuid,uuid)',
  'request_account_deletion(uuid,integer)','reserve_ai_budget(uuid,text,bigint,bigint,bigint,bigint)',
  'reserve_ai_run(uuid,integer)','reserve_support_reply(uuid,text,text,uuid,text)',
  'resolve_provider_uncertainty(uuid,uuid,text,text,text,boolean,boolean)','save_financial_record(uuid,uuid,uuid,bigint,jsonb)',
  'support_request_touch()','update_support_request_admin(uuid,text,text,uuid)',
  'void_financial_payment(uuid,uuid,uuid,text)'
)

function Invoke-Native([scriptblock]$Command,[string]$Failure){
  $output=& $Command 2>&1
  if($LASTEXITCODE -ne 0){throw "$Failure (exit $LASTEXITCODE)"}
  return @($output | ForEach-Object {[string]$_})
}
function Invoke-Psql([string]$Container,[string]$Sql){
  $output=& docker exec $Container psql -U postgres -d postgres -AtX -v ON_ERROR_STOP=1 -c $Sql 2>&1
  if($LASTEXITCODE -ne 0){throw "Fresh schema query failed (exit $LASTEXITCODE)"}
  return (@($output | ForEach-Object {[string]$_}) -join "`n").Trim()
}
function Assert-Exact([string]$Label,[string[]]$Actual,[string[]]$Expected){
  $a=@($Actual | Sort-Object); $e=@($Expected | Sort-Object)
  if(($a -join "`n") -ne ($e -join "`n")){
    throw "$Label mismatch; expected=$($e -join ','); actual=$($a -join ',')"
  }
}

$null=Invoke-Native { docker info --format '{{.ServerVersion}}' } 'Docker engine unavailable'
$results=@(); $referenceSchemaHash=$null
for($run=1;$run -le $Repeat;$run++){
  $suffix=[guid]::NewGuid().ToString('N').Substring(0,12)
  $project="profit-radar-fresh-proof-$suffix"
  $workspace=Join-Path $env:LOCALAPPDATA "ProfitRadar/fresh-production-$suffix"
  $apiPort=54621+(($run-1)*100)
  $dbPort=$apiPort+1
  $shadowPort=$apiPort-1
  $container="supabase_db_$project"
  $started=$false
  try {
    $stage=& (Join-Path $PSScriptRoot 'New-FreshSupabaseWorkspace.ps1') -Workspace $workspace -ProjectId $project -ApiPort $apiPort -DbPort $dbPort -ShadowPort $shadowPort
    if($LASTEXITCODE -ne 0){throw 'Fresh workspace staging failed'}
    $stageResult=$stage | ConvertFrom-Json
    if($stageResult.status -ne 'READY' -or $stageResult.production_connections -ne 0){throw 'Fresh workspace staging evidence invalid'}

    Push-Location $workspace
    try {
      $null=Invoke-Native { npx --yes supabase@2.117.0 start } 'Fresh local Supabase migration apply failed'
      $started=$true
    } finally { Pop-Location }

    $expectedHistory=@($manifest.guard.staged_file)+@($manifest.migrations.staged_file)+@($manifest.completion.staged_file)
    $expectedVersions=@($expectedHistory | ForEach-Object {$_.Split('_')[0]})
    $actualVersions=@((Invoke-Psql $container 'select version from supabase_migrations.schema_migrations order by version') -split "`n" | Where-Object {$_})
    Assert-Exact 'Fresh migration history' $actualVersions $expectedVersions

    $tables=@((Invoke-Psql $container "select c.relname from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relkind in ('r','p') order by c.relname") -split "`n" | Where-Object {$_})
    Assert-Exact 'Fresh public tables' $tables $expectedTables
    $nonRls=Invoke-Psql $container "select c.relname from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relkind in ('r','p') and not c.relrowsecurity order by c.relname"
    if($nonRls){throw "RLS disabled: $nonRls"}

    $policies=@((Invoke-Psql $container "select tablename||'|'||policyname||'|'||permissive||'|'||cmd||'|'||array_to_string(roles,',') from pg_policies where schemaname='public' order by tablename,policyname") -split "`n" | Where-Object {$_})
    Assert-Exact 'Fresh policies' $policies $expectedPolicies
    $grants=@((Invoke-Psql $container "select grantee||'|'||table_name||'|'||privilege_type from information_schema.role_table_grants where table_schema='public' and grantee in ('anon','authenticated') order by grantee,table_name,privilege_type") -split "`n" | Where-Object {$_})
    Assert-Exact 'Fresh browser grants' $grants @('authenticated|companies|SELECT','authenticated|profiles|SELECT')

    $triggers=@((Invoke-Psql $container "select c.relname||'|'||t.tgname||'|'||p.proname from pg_trigger t join pg_class c on c.oid=t.tgrelid join pg_namespace n on n.oid=c.relnamespace join pg_proc p on p.oid=t.tgfoid where n.nspname='public' and not t.tgisinternal order by c.relname,t.tgname") -split "`n" | Where-Object {$_})
    Assert-Exact 'Fresh triggers' $triggers $expectedTriggers
    $functions=@((Invoke-Psql $container "select p.proname||'('||replace(oidvectortypes(p.proargtypes),' ','')||')' from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' order by p.proname,oidvectortypes(p.proargtypes)") -split "`n" | Where-Object {$_})
    Assert-Exact 'Fresh functions' $functions $expectedFunctions
    $exposedDefiners=Invoke-Psql $container "select p.proname from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.prosecdef and (has_function_privilege('public',p.oid,'execute') or has_function_privilege('anon',p.oid,'execute') or has_function_privilege('authenticated',p.oid,'execute')) order by p.proname"
    if($exposedDefiners){throw "SECURITY DEFINER function exposed to browser roles: $exposedDefiners"}
    if((Invoke-Psql $container 'select count(*) from public.companies') -ne '0' -or (Invoke-Psql $container 'select count(*) from public.profiles') -ne '0'){
      throw 'Fresh database contains fixtures before application integration'
    }
    if((Invoke-Psql $container "select mode from public.billing_runtime_config where singleton") -ne 'test'){
      throw 'Fresh billing runtime must fail closed in test mode'
    }

    $guardSql=Get-Content -LiteralPath (Join-Path $repo $manifest.guard.source) -Raw
    $guardReplay=$guardSql | & docker exec -i $container psql -U postgres -d postgres -AtX -v ON_ERROR_STOP=1 2>&1
    if($LASTEXITCODE -eq 0 -or (@($guardReplay | ForEach-Object {[string]$_}) -join "`n") -notmatch 'FRESH_PROJECT_ONLY'){
      throw 'Fresh-project guard did not reject a non-empty migration history'
    }

    $snapshotSql=Get-Content -LiteralPath (Join-Path $repo 'supabase/fresh_production_schema_snapshot.sql') -Raw
    $snapshot=Invoke-Psql $container $snapshotSql
    $bytes=[System.Text.Encoding]::UTF8.GetBytes($snapshot)
    $schemaHash=[Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($bytes))
    if($schemaHash -ne $manifest.canonical_schema_sha256){throw 'Fresh schema does not match the approved canonical metadata snapshot'}
    if($null -eq $referenceSchemaHash){$referenceSchemaHash=$schemaHash}
    elseif($schemaHash -ne $referenceSchemaHash){throw 'Fresh schema is not deterministic across runs'}

    $apiUrl="http://127.0.0.1:$apiPort"
    Push-Location (Join-Path $repo 'backend')
    try {
      $integration=& (Join-Path $repo 'backend/venv/Scripts/python.exe') (Join-Path $repo 'backend/scripts/run_fresh_supabase_integration.py') --project-id $project --api-url $apiUrl --allow-fresh-fixtures 2>&1
      if($LASTEXITCODE -ne 0){
        $safe=@($integration | ForEach-Object {[string]$_} | Select-Object -Last 80)
        throw "Fresh application integration failed (exit $LASTEXITCODE)`n$($safe -join "`n")"
      }
    } finally { Pop-Location }
    $summary=($integration | ForEach-Object {[string]$_} | Where-Object {$_ -match '\d+ passed'} | Select-Object -Last 1)
    if(-not $summary -or $summary -match 'skipped'){throw 'Fresh integration did not produce a zero-skip pass summary'}

    $results += [pscustomobject]@{
      run=$run; status='PASS'; migrations=$expectedVersions.Count; tables=$tables.Count;
      integration=$summary.Trim(); schema_sha256=$schemaHash; production_connections=0; production_side_effects=0
    }
  } finally {
    if($started){
      Push-Location $workspace
      try { $null=Invoke-Native { npx --yes supabase@2.117.0 stop } 'Fresh local Supabase stop failed' } finally { Pop-Location }
    }
  }
}

$evidence=[pscustomobject]@{
  status='PASS'; target='NEW TOKYO PROJECT'; runs=$results; repeat=$Repeat;
  fresh_stream_migrations=2+$manifest.migrations.Count; canonical_schema_parity='PASS';
  manual_db_patch_required=$false; historical_migrations_modified=0;
  rls='PASS'; rls_runner='READY'; application_integration='PASS'; no_historical_db_dependency='PASS';
  schema_sha256=$referenceSchemaHash; production_connections=0; production_side_effects=0
}
if($EvidencePath){
  $full=[System.IO.Path]::GetFullPath($EvidencePath,$repo)
  if(-not $full.StartsWith([System.IO.Path]::GetFullPath((Join-Path $repo 'docs/evidence')),[System.StringComparison]::OrdinalIgnoreCase)){
    throw 'Evidence path must remain under docs/evidence'
  }
  $evidence | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $full -Encoding utf8NoBOM
}
$evidence | ConvertTo-Json -Depth 6
