param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $repo '.local-runtime'
$stage = Join-Path $runtime 'supabase'
$migrationStage = Join-Path $stage 'migrations'
$supabase = @('npx','--yes','supabase@2.117.0')

function Invoke-NativeChecked([scriptblock]$Command,[string]$FailureMessage) {
  $previousErrorAction = $ErrorActionPreference
  $hasNativePreference = Test-Path variable:PSNativeCommandUseErrorActionPreference
  if($hasNativePreference){ $previousNativePreference = $PSNativeCommandUseErrorActionPreference }
  try {
    # Native tools commonly write warnings (including CLI update notices) to
    # stderr even when they succeed. Their process exit code is authoritative.
    $ErrorActionPreference = 'Continue'
    if($hasNativePreference){ $PSNativeCommandUseErrorActionPreference = $false }
    $output = & $Command
    $nativeExitCode = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $previousErrorAction
    if($hasNativePreference){ $PSNativeCommandUseErrorActionPreference = $previousNativePreference }
  }
  if($nativeExitCode -ne 0){ throw "$FailureMessage (exit code $nativeExitCode)" }
  return $output
}

function Assert-LocalSafety {
  if ($Env:APP_ENV -in @('staging','production')) { throw 'Production-like APP_ENV is not allowed.' }
  if ($Env:STRIPE_SECRET_KEY -like 'sk_live_*' -or $Env:STRIPE_SECRET_KEY -like 'rk_live_*') { throw 'Stripe LIVE credentials are not allowed.' }
  if ($Env:SUPABASE_URL) {
    $uri = [Uri]$Env:SUPABASE_URL
    if ($uri.Scheme -ne 'http' -or $uri.Host -notin @('127.0.0.1','localhost')) { throw 'Non-loopback Supabase is not allowed.' }
  }
}
function Assert-PortFree([int]$Port) {
  if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) { throw "Local port $Port is already in use." }
}
function Wait-Http([string]$Url,[int]$Attempts=60) {
  foreach($i in 1..$Attempts) {
    try { $response=Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2; if($response.StatusCode -ge 200 -and $response.StatusCode -lt 500){ return } } catch {}
    Start-Sleep -Seconds 1
  }
  throw "Local service did not become ready: $Url"
}

Assert-LocalSafety
Invoke-NativeChecked { docker info *> $null } 'Docker Engine is not ready. Start Docker Desktop and retry.' | Out-Null
Invoke-NativeChecked { & $supabase[0] $supabase[1] $supabase[2] --version *> $null } 'Pinned Supabase CLI is unavailable.' | Out-Null

$isolated = Invoke-NativeChecked { docker ps --filter 'label=com.supabase.cli.project=profit-radar-disposable' --format '{{.Names}}' } 'Docker container inventory failed.'
if($isolated){ Write-Host 'Existing profit-radar-disposable is running on separate ports and will not be changed.' }

New-Item -ItemType Directory -Force -Path $migrationStage | Out-Null
Copy-Item -LiteralPath (Join-Path $repo 'supabase/config.toml') -Destination (Join-Path $stage 'config.toml') -Force
$sourceMigrations = Get-ChildItem (Join-Path $repo 'supabase/migrations') -File -Filter '*.sql' |
  Where-Object { $_.Name -notmatch '^2026091[45]0001_remote_schema_forward' }
$expected = @($sourceMigrations.Name)
$unexpected = Get-ChildItem $migrationStage -File -Filter '*.sql' -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -notin $expected }
if($unexpected){ throw 'Unexpected staged migration found; review .local-runtime without deleting it.' }
foreach($source in $sourceMigrations){
  $destination=Join-Path $migrationStage $source.Name
  if(Test-Path $destination){
    if((Get-FileHash $source.FullName -Algorithm SHA256).Hash -ne (Get-FileHash $destination -Algorithm SHA256).Hash){
      throw "Previously staged migration changed: $($source.Name)"
    }
  } else { Copy-Item -LiteralPath $source.FullName -Destination $destination }
}

Invoke-NativeChecked { & $supabase[0] $supabase[1] $supabase[2] start --workdir $runtime --exclude studio,mailpit,imgproxy,storage-api,realtime,edge-runtime,logflare,vector,supavisor *> $null } 'Local Supabase failed to start or migrate.' | Out-Null
$statusText=Invoke-NativeChecked { & $supabase[0] $supabase[1] $supabase[2] status --workdir $runtime --output json } 'Local Supabase status is unavailable.'
$status=$statusText | ConvertFrom-Json
$api=[Uri]$status.API_URL
if($api.Scheme -ne 'http' -or $api.Host -notin @('127.0.0.1','localhost') -or $api.Port -ne 54421){ throw 'Unexpected local Supabase target.' }

try {
  $backendReady=(Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8031/ready' -TimeoutSec 2).StatusCode -eq 200
  $frontendReady=(Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:3101/login' -TimeoutSec 2).StatusCode -eq 200
} catch { $backendReady=$false; $frontendReady=$false }
if($backendReady -and $frontendReady){
  Write-Host 'Supabase READY: http://127.0.0.1:54421';Write-Host 'Backend READY: http://127.0.0.1:8031';Write-Host 'Frontend READY: http://127.0.0.1:3101'
  if(!$NoBrowser){Start-Process 'http://127.0.0.1:3101/login'}
  return
}

Assert-PortFree 8031; Assert-PortFree 3101
$saved=@{}; foreach($name in @('APP_ENV','SUPABASE_URL','SUPABASE_ANON_KEY','SUPABASE_SERVICE_ROLE_KEY','FRONTEND_URL','BACKEND_URL','CORS_ORIGINS','STRIPE_MODE','STRIPE_SECRET_KEY','NEXT_PUBLIC_API_BASE_URL','NEXT_PUBLIC_SUPABASE_URL','NEXT_PUBLIC_SUPABASE_ANON_KEY','BACKEND_ORIGIN')){$saved[$name]=[Environment]::GetEnvironmentVariable($name,'Process')}
try {
  $Env:APP_ENV='development';$Env:SUPABASE_URL=$status.API_URL;$Env:SUPABASE_ANON_KEY=$status.ANON_KEY;$Env:SUPABASE_SERVICE_ROLE_KEY=$status.SERVICE_ROLE_KEY
  $Env:FRONTEND_URL='http://127.0.0.1:3101';$Env:BACKEND_URL='http://127.0.0.1:8031';$Env:CORS_ORIGINS='http://127.0.0.1:3101';$Env:STRIPE_MODE='test';Remove-Item Env:STRIPE_SECRET_KEY -ErrorAction SilentlyContinue
  $backend=Start-Process -FilePath (Join-Path $repo 'backend/venv/Scripts/python.exe') -ArgumentList @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8031') -WorkingDirectory (Join-Path $repo 'backend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtime 'backend.stdout.log') -RedirectStandardError (Join-Path $runtime 'backend.stderr.log') -PassThru
  $backend.Id | Set-Content (Join-Path $runtime 'backend.pid')
  Wait-Http 'http://127.0.0.1:8031/health'; Wait-Http 'http://127.0.0.1:8031/ready'
  $Env:NEXT_PUBLIC_API_BASE_URL='http://127.0.0.1:8031';$Env:BACKEND_ORIGIN='http://127.0.0.1:8031';$Env:NEXT_PUBLIC_SUPABASE_URL=$status.API_URL;$Env:NEXT_PUBLIC_SUPABASE_ANON_KEY=$status.ANON_KEY
  $frontend=Start-Process -FilePath 'npm.cmd' -ArgumentList @('run','dev','--','--hostname','127.0.0.1','--port','3101') -WorkingDirectory (Join-Path $repo 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtime 'frontend.stdout.log') -RedirectStandardError (Join-Path $runtime 'frontend.stderr.log') -PassThru
  $frontend.Id | Set-Content (Join-Path $runtime 'frontend.pid')
  Wait-Http 'http://127.0.0.1:3101/login'; Wait-Http 'http://127.0.0.1:3101/register'; Wait-Http 'http://127.0.0.1:3101/onboarding'
} catch {
  if($frontend -and !$frontend.HasExited){Stop-Process -Id $frontend.Id -Force}
  if($backend -and !$backend.HasExited){Stop-Process -Id $backend.Id -Force}
  throw
} finally { foreach($name in $saved.Keys){[Environment]::SetEnvironmentVariable($name,$saved[$name],'Process')} }
Write-Host 'Supabase READY: http://127.0.0.1:54421'
Write-Host 'Backend READY: http://127.0.0.1:8031'
Write-Host 'Frontend READY: http://127.0.0.1:3101'
if(!$NoBrowser){ Start-Process 'http://127.0.0.1:3101/login' }
