param(
  [Parameter(Mandatory=$true)][string]$Workspace,
  [Parameter(Mandatory=$true)][string]$ProjectId,
  [Parameter(Mandatory=$true)][int]$ApiPort,
  [Parameter(Mandatory=$true)][int]$DbPort,
  [Parameter(Mandatory=$true)][int]$ShadowPort,
  [switch]$AllowProductionStaging
)
$ErrorActionPreference='Stop'
$repo=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$manifestPath=Join-Path $repo 'deploy/fresh-production/migration-stream.json'
$manifest=Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json

if($AllowProductionStaging){
  if($ProjectId -notmatch '^[a-z0-9]{20}$'){throw 'Production project ref format is invalid'}
} elseif($ProjectId -notmatch '^profit-radar-fresh-proof-[0-9a-f]{12}$'){
  throw 'Fresh project id must use the disposable proof prefix'
}
if(Test-Path -LiteralPath $Workspace){throw 'Fresh workspace must not already exist'}
if($manifest.target -ne 'new-supabase-project-only' -or $manifest.region -ne 'ap-northeast-1'){
  throw 'Fresh migration manifest target mismatch'
}

$sourceDir=Join-Path $repo 'supabase/migrations'
$repoFiles=@(Get-ChildItem -LiteralPath $sourceDir -Filter '*.sql' | Sort-Object Name)
$declared=@($manifest.migrations.source)+@($manifest.excluded_remote_supplements.source)
if(@($declared | Sort-Object -Unique).Count -ne $declared.Count){throw 'Duplicate source migration in fresh manifest'}
$unaccounted=@($repoFiles.Name | Where-Object {$_ -notin $declared})
$missing=@($declared | Where-Object {$_ -notin $repoFiles.Name})
if($unaccounted.Count -or $missing.Count){
  throw "Fresh manifest does not exactly account for root migrations; unaccounted=$($unaccounted -join ','); missing=$($missing -join ',')"
}

foreach($entry in @($manifest.migrations)+@($manifest.excluded_remote_supplements)){
  $path=Join-Path $sourceDir $entry.source
  $actual=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
  if($actual -ne $entry.sha256){throw "Migration hash drift: $($entry.source)"}
}
$guard=Join-Path $repo $manifest.guard.source
if((Get-FileHash -LiteralPath $guard -Algorithm SHA256).Hash -ne $manifest.guard.sha256){
  throw 'Fresh-project guard hash drift'
}
$completion=Join-Path $repo $manifest.completion.source
if((Get-FileHash -LiteralPath $completion -Algorithm SHA256).Hash -ne $manifest.completion.sha256){
  throw 'Fresh-project contract completion hash drift'
}

$migrations=Join-Path $Workspace 'supabase/migrations'
New-Item -ItemType Directory -Path $migrations -Force | Out-Null
Copy-Item -LiteralPath $guard -Destination (Join-Path $migrations $manifest.guard.staged_file)
foreach($entry in $manifest.migrations){
  Copy-Item -LiteralPath (Join-Path $sourceDir $entry.source) -Destination (Join-Path $migrations $entry.staged_file)
}
Copy-Item -LiteralPath $completion -Destination (Join-Path $migrations $manifest.completion.staged_file)

$config=Get-Content -LiteralPath (Join-Path $repo 'supabase/config.toml') -Raw
$replacements=@{
  'project_id = "profit-radar-local"'="project_id = `"$ProjectId`""
  'port = 54420'="port = $ShadowPort"
  'port = 54421'="port = $ApiPort"
  'port = 54422'="port = $DbPort"
  'port = 54423'="port = $($ApiPort+2)"
  'port = 54424'="port = $($ApiPort+3)"
  'port = 54427'="port = $($ApiPort+6)"
  'port = 54329'="port = $($ApiPort+8)"
}
foreach($old in $replacements.Keys){
  if(-not $config.Contains($old)){throw "Supabase config contract changed: $old"}
  $config=$config.Replace($old,$replacements[$old])
}
Set-Content -LiteralPath (Join-Path $Workspace 'supabase/config.toml') -Value $config -Encoding utf8NoBOM

[pscustomobject]@{
  status='READY'
  project_id=$ProjectId
  migration_count=2+$manifest.migrations.Count
  excluded_remote_supplements=$manifest.excluded_remote_supplements.Count
  production_connections=0
} | ConvertTo-Json -Compress
