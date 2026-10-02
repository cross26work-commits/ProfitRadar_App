param(
  [Parameter(Mandatory=$true)][string]$Manifest,
  [Parameter(Mandatory=$true)][string]$ExpectedCommit
)
$ErrorActionPreference='Stop'
if($ExpectedCommit -notmatch '^[0-9a-f]{40}$'){throw 'Expected commit must be a full SHA'}
$data=Get-Content -LiteralPath $Manifest -Raw | ConvertFrom-Json
$artifact=Join-Path (Split-Path -Parent $Manifest) $data.artifact
if($data.commit -ne $ExpectedCommit -or $data.source_tree -ne 'clean' -or -not (Test-Path -LiteralPath $artifact)){throw 'Release artifact manifest mismatch'}
$actual=(Get-FileHash -LiteralPath $artifact -Algorithm SHA256).Hash
if($actual -ne $data.sha256){throw 'Release artifact SHA256 mismatch'}
[pscustomobject]@{status='PASS';commit=$ExpectedCommit;sha256=$actual} | ConvertTo-Json -Compress
