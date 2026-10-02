param()
$ErrorActionPreference='Stop'
$repo=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$files=@(Get-ChildItem -LiteralPath (Join-Path $repo 'supabase/migrations') -Filter '*.sql' | Sort-Object Name)
$approved=(Get-Content -LiteralPath (Join-Path $repo 'deploy/migration-reviewed-delete-bodies.json') -Raw | ConvertFrom-Json).files
if(-not $files.Count){throw 'No migrations found'}
$duplicates=$files | Group-Object Name | Where-Object Count -gt 1
if($duplicates){throw 'Duplicate migration filename'}
foreach($file in $files){
  $sql=Get-Content -LiteralPath $file.FullName -Raw
  if($sql -match '(?im)^\s*TRUNCATE\b' -or $sql -match '(?im)^\s*DROP\s+TABLE\b'){throw "Destructive migration statement: $($file.Name)"}
  if($sql -match '(?im)^\s*DELETE\s+FROM\b'){
    $property=$approved.PSObject.Properties[$file.Name]
    $hash=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    if($null -eq $property -or $property.Value -ne $hash){throw "Unreviewed DELETE-bearing migration: $($file.Name)"}
  }
}
$v2=Join-Path $repo 'supabase/migrations/202609150001_remote_schema_forward_v2.sql'
if(-not (Test-Path -LiteralPath $v2)){throw 'Pinned forward migration missing'}
$digest=(Get-FileHash -LiteralPath $v2 -Algorithm SHA256).Hash
$fresh=Get-Content -LiteralPath (Join-Path $repo 'deploy/fresh-production/migration-stream.json') -Raw | ConvertFrom-Json
$declared=@($fresh.migrations.source)+@($fresh.excluded_remote_supplements.source)
if((@($declared | Sort-Object -Unique) -join "`n") -ne (@($files.Name | Sort-Object) -join "`n")){
  throw 'Fresh production stream does not exactly account for root migrations'
}
foreach($entry in @($fresh.migrations)+@($fresh.excluded_remote_supplements)){
  if((Get-FileHash -LiteralPath (Join-Path $repo ('supabase/migrations/'+$entry.source)) -Algorithm SHA256).Hash -ne $entry.sha256){
    throw "Fresh production migration hash drift: $($entry.source)"
  }
}
foreach($entry in @($fresh.guard,$fresh.completion)){
  if((Get-FileHash -LiteralPath (Join-Path $repo $entry.source) -Algorithm SHA256).Hash -ne $entry.sha256){
    throw "Fresh production control migration hash drift: $($entry.source)"
  }
}
[pscustomobject]@{status='PASS';migration_count=$files.Count;fresh_stream_migration_count=2+$fresh.migrations.Count;v2_sha256=$digest;remote_contact=0} | ConvertTo-Json -Compress
