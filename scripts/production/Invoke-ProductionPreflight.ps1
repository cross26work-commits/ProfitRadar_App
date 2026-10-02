param(
  [Parameter(Mandatory=$true)][string]$ExpectedCommit,
  [Parameter(Mandatory=$true)][string]$ArtifactManifest,
  [Parameter(Mandatory=$true)][string]$FrontendEnvironmentFile,
  [Parameter(Mandatory=$true)][string]$BackendEnvironmentFile,
  [Parameter(Mandatory=$true)][string]$WorkerEnvironmentFile,
  [Parameter(Mandatory=$true)][string]$BackupEnvironmentFile,
  [Parameter(Mandatory=$true)][string]$FreshMigrationEvidence
)
$ErrorActionPreference='Stop'
$repo=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$head=(git -C $repo rev-parse HEAD).Trim()
if($LASTEXITCODE -ne 0 -or $head -ne $ExpectedCommit){throw 'Release commit mismatch'}
if(git -C $repo status --porcelain --untracked-files=all){throw 'Release working tree must be clean'}
& (Join-Path $PSScriptRoot 'Test-ReleaseArtifact.ps1') -Manifest $ArtifactManifest -ExpectedCommit $ExpectedCommit | Out-Null
foreach($item in @(
  @('frontend',$FrontendEnvironmentFile), @('backend',$BackendEnvironmentFile),
  @('worker',$WorkerEnvironmentFile), @('backup',$BackupEnvironmentFile)
)){
  & (Join-Path $PSScriptRoot 'Test-ProductionEnvironment.ps1') -Service $item[0] -EnvironmentFile $item[1] | Out-Null
}
& (Join-Path $PSScriptRoot 'Test-MigrationSafety.ps1') | Out-Null
& (Join-Path $PSScriptRoot 'Test-RepositorySecrets.ps1') | Out-Null
& (Join-Path $PSScriptRoot 'Test-FreshMigrationEvidence.ps1') -EvidencePath $FreshMigrationEvidence | Out-Null
$required=@(
  'backend/scripts/run_production_auth_e2e.py','backend/scripts/scheduled_backup.py',
  'backend/scripts/runtime_probe.py','docs/PRODUCTION_SMOKE_TEST.md',
  'docs/PRODUCTION_ROLLBACK_PLAN.md','deploy/railway/service-plan.json'
)
foreach($path in $required){if(-not (Test-Path -LiteralPath (Join-Path $repo $path))){throw "Required release control missing: $path"}}
[pscustomobject]@{status='READY';commit=$ExpectedCommit;production_connections=0;production_side_effects=0} | ConvertTo-Json -Compress
