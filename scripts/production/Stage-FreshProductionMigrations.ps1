param(
  [Parameter(Mandatory=$true)][string]$ProjectRef,
  [Parameter(Mandatory=$true)][string]$Destination,
  [Parameter(Mandatory=$true)][string]$Confirmation
)
$ErrorActionPreference='Stop'
$expected="I_CONFIRM_NEW_EMPTY_TOKYO_PROJECT_STAGING:$ProjectRef"
if($ProjectRef -notmatch '^[a-z0-9]{20}$' -or $Confirmation -ne $expected){
  throw 'Fresh Production staging confirmation mismatch'
}
if(Test-Path -LiteralPath $Destination){throw 'Production staging destination must not already exist'}

# Staging is file-only. This script never links a project and never invokes db push.
$result=& (Join-Path $PSScriptRoot 'New-FreshSupabaseWorkspace.ps1') `
  -Workspace $Destination -ProjectId $ProjectRef -ApiPort 55421 -DbPort 55422 -ShadowPort 55420 `
  -AllowProductionStaging
$parsed=$result | ConvertFrom-Json
if($parsed.status -ne 'READY' -or $parsed.project_id -ne $ProjectRef -or $parsed.production_connections -ne 0){
  throw 'Fresh Production migration staging evidence is invalid'
}
[pscustomobject]@{
  status='STAGED'
  project_ref=$ProjectRef
  workspace=[System.IO.Path]::GetFullPath($Destination)
  migration_count=$parsed.migration_count
  remote_contact=0
  remote_write=0
  next='Owner approval is required before link or db push'
} | ConvertTo-Json -Compress
