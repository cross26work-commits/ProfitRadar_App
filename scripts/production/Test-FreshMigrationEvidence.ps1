param(
  [Parameter(Mandatory=$true)][string]$EvidencePath
)
$ErrorActionPreference='Stop'
$repo=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$resolved=[System.IO.Path]::GetFullPath($EvidencePath,$repo)
$evidenceRoot=[System.IO.Path]::GetFullPath((Join-Path $repo 'docs/evidence'))
if(-not $resolved.StartsWith($evidenceRoot,[System.StringComparison]::OrdinalIgnoreCase)){
  throw 'Fresh migration evidence must be under docs/evidence'
}
if(-not (Test-Path -LiteralPath $resolved -PathType Leaf)){throw 'Fresh migration evidence is missing'}
$evidence=Get-Content -LiteralPath $resolved -Raw | ConvertFrom-Json
$manifest=Get-Content -LiteralPath (Join-Path $repo 'deploy/fresh-production/migration-stream.json') -Raw | ConvertFrom-Json
$runs=@($evidence.runs)
if($evidence.status -ne 'PASS'){throw 'Fresh migration evidence summary is not approved'}
if($evidence.target -ne 'NEW TOKYO PROJECT'){throw 'Fresh migration evidence summary is not approved'}
if($evidence.repeat -ne 3 -or $runs.Count -ne 3){throw 'Fresh migration evidence summary is not approved'}
if($evidence.manual_db_patch_required -ne $false){throw 'Fresh migration evidence summary is not approved'}
if($evidence.historical_migrations_modified -ne 0){throw 'Fresh migration evidence summary is not approved'}
if($evidence.canonical_schema_parity -ne 'PASS'){throw 'Fresh migration evidence summary is not approved'}
if($evidence.rls -ne 'PASS' -or $evidence.rls_runner -ne 'READY'){throw 'Fresh migration evidence summary is not approved'}
if($evidence.application_integration -ne 'PASS'){throw 'Fresh migration evidence summary is not approved'}
if($evidence.no_historical_db_dependency -ne 'PASS'){throw 'Fresh migration evidence summary is not approved'}
if($evidence.production_connections -ne 0 -or $evidence.production_side_effects -ne 0){throw 'Fresh migration evidence summary is not approved'}
$expectedRunNumbers=1,2,3
$actualRunNumbers=@($runs.run | Sort-Object)
if(($actualRunNumbers -join ',') -ne ($expectedRunNumbers -join ',')){
  throw 'Fresh migration evidence run numbers are not exactly 1,2,3'
}
$hashes=@($runs.schema_sha256 | Select-Object -Unique)
if($hashes.Count -ne 1 -or $hashes[0] -notmatch '^[0-9A-F]{64}$' -or $evidence.schema_sha256 -ne $hashes[0]){
  throw 'Fresh migration schema hash evidence is invalid or nondeterministic'
}
if($evidence.schema_sha256 -ne $manifest.canonical_schema_sha256){
  throw 'Fresh migration schema hash evidence is invalid or nondeterministic'
}
foreach($run in $runs){
  if($run.status -ne 'PASS'){throw "Fresh migration run $($run.run) is not approved"}
  if($run.migrations -ne $evidence.fresh_stream_migrations -or $run.tables -ne 37){throw "Fresh migration run $($run.run) is not approved"}
  if($run.integration -notmatch '^35 passed,' -or $run.integration -match 'skipped'){throw "Fresh migration run $($run.run) is not approved"}
  if($run.production_connections -ne 0 -or $run.production_side_effects -ne 0){throw "Fresh migration run $($run.run) is not approved"}
}
[pscustomobject]@{
  status='PASS'
  target=$evidence.target
  runs=$runs.Count
  migrations=$evidence.fresh_stream_migrations
  schema_sha256=$evidence.schema_sha256
  canonical_schema_parity=$evidence.canonical_schema_parity
  rls_runner=$evidence.rls_runner
  manual_db_patch_required=$evidence.manual_db_patch_required
  production_connections=0
  production_side_effects=0
} | ConvertTo-Json -Compress
