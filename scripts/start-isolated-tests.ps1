param([switch]$RunTests)
$ErrorActionPreference='Stop'
$repoRoot=Split-Path -Parent $PSScriptRoot
$isolatedRoot=Join-Path $repoRoot '.local-isolated'
# Fixed project, new directory only; never db reset, link, push or remote flags.
if(Test-Path -LiteralPath $isolatedRoot){throw 'Existing isolated workspace detected. Reuse it manually after inspection; no automatic reset.'}
if(-not (Get-Command docker -ErrorAction SilentlyContinue)){throw 'Docker engine is required; no environment was created.'}
docker info --format '{{.ServerVersion}}'
if($LASTEXITCODE -ne 0){throw 'Docker engine unavailable'}
$migrationRoot=Join-Path $isolatedRoot 'supabase/migrations'
New-Item -ItemType Directory -Path $migrationRoot -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $repoRoot 'backend/tests/isolated/config.toml') -Destination (Join-Path $isolatedRoot 'supabase/config.toml')
Copy-Item -LiteralPath (Join-Path $repoRoot 'backend/tests/isolated/baseline.sql') -Destination (Join-Path $migrationRoot '20260901000000_synthetic_baseline.sql')
Get-ChildItem -LiteralPath (Join-Path $repoRoot 'supabase/migrations') -Filter '*.sql' | Copy-Item -Destination $migrationRoot
Push-Location $isolatedRoot
try {
  $startupOutput = npx --yes supabase@2.117.0 start 2>&1
  if($LASTEXITCODE -ne 0){throw 'Local startup failed; inspect local Docker without using production credentials'}
  # Parse captured JSON in memory. Never print status output containing keys.
  $localStatusRaw = npx --yes supabase@2.117.0 status -o json 2>$null
  if($LASTEXITCODE -ne 0){throw 'Local status unavailable'}
  $localStatus = ($localStatusRaw -join "`n") | ConvertFrom-Json
  if($localStatus.API_URL -notin @('http://127.0.0.1:54321','http://localhost:54321')){throw 'Unexpected local target'}
  $env:P0_SUPABASE_TEST_URL=$localStatus.API_URL
  $env:P0_SUPABASE_EXPECTED_URL=$localStatus.API_URL
  $env:P0_ALLOW_FIXTURE_WRITES='CREATE_DISPOSABLE_FIXTURES'
  $env:P0_SUPABASE_TEST_ANON_KEY=$localStatus.ANON_KEY
  $env:P0_SUPABASE_TEST_SERVICE_KEY=$localStatus.SERVICE_ROLE_KEY
  if($RunTests){
    Push-Location (Join-Path $repoRoot 'backend')
    try { & './venv/Scripts/python.exe' -m pytest tests/integration -q -rs --tb=short; if($LASTEXITCODE -ne 0){throw 'Integration tests failed'} } finally { Pop-Location }
  }
} finally {
  Remove-Item Env:P0_SUPABASE_TEST_ANON_KEY,Env:P0_SUPABASE_TEST_SERVICE_KEY -ErrorAction SilentlyContinue
  $localStatus=$null; $localStatusRaw=$null; $startupOutput=$null
  Pop-Location
}
