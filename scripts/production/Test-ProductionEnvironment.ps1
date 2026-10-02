param(
  [Parameter(Mandatory=$true)][ValidateSet('frontend','backend','worker','backup')][string]$Service,
  [Parameter(Mandatory=$true)][string]$EnvironmentFile
)
$ErrorActionPreference='Stop'
$repo=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$schema=Get-Content -LiteralPath (Join-Path $repo 'deploy/production-env.schema.json') -Raw | ConvertFrom-Json
if(-not (Test-Path -LiteralPath $EnvironmentFile -PathType Leaf)){throw 'Environment file not found'}
$values=@{}
foreach($line in Get-Content -LiteralPath $EnvironmentFile){
  $trimmed=$line.Trim()
  if(-not $trimmed -or $trimmed.StartsWith('#')){continue}
  if($trimmed -notmatch '^([A-Z][A-Z0-9_]*)=(.*)$'){throw 'Invalid environment file format'}
  if($values.ContainsKey($Matches[1])){throw 'Duplicate environment variable'}
  $values[$Matches[1]]=$Matches[2]
}
$required=$schema."${Service}_required"
$missing=@($required | Where-Object {-not $values.ContainsKey($_) -or [string]::IsNullOrWhiteSpace($values[$_])})
if($missing.Count){throw "Required $Service settings are missing: $($missing -join ', ')"}
foreach($entry in $schema.production_constants.PSObject.Properties){
  if($required -contains $entry.Name -and $values[$entry.Name] -ne [string]$entry.Value){throw 'Production constant mismatch'}
}
foreach($name in $schema.server_secret_only){
  if($Service -eq 'frontend' -and $values.ContainsKey($name)){throw 'Server secret is forbidden in frontend environment'}
}
foreach($entry in $values.GetEnumerator()){
  if($entry.Value -match '(?i)(localhost|127\.0\.0\.1|example\.(com|invalid)|<[^>]+>|TODO|TBD)'){throw 'Placeholder or local production value detected'}
}
if($Service -eq 'frontend'){
  if($values.APP_ENV -ne 'production' -or $values.BACKEND_ORIGIN -ne 'https://api.profitradar.jp' -or $values.NEXT_PUBLIC_API_BASE_URL -ne 'https://api.profitradar.jp'){throw 'Frontend origin contract mismatch'}
  if($values.NEXT_PUBLIC_SUPABASE_URL -notmatch '^https://[a-z0-9]+\.supabase\.co$'){throw 'Frontend Supabase URL invalid'}
}
if($Service -eq 'backend'){
  if($values.FRONTEND_URL -ne 'https://profitradar.jp' -or $values.BACKEND_URL -ne 'https://api.profitradar.jp' -or $values.CORS_ORIGINS -ne 'https://profitradar.jp'){throw 'Backend origin contract mismatch'}
  if($values.GOOGLE_REDIRECT_URI -ne 'https://api.profitradar.jp/gmail/callback' -or $values.SCHEDULER_BACKEND_URL -ne 'https://api.profitradar.jp'){throw 'Provider endpoint contract mismatch'}
  if($values.STRIPE_SECRET_KEY -notmatch '^(sk|rk)_live_' -or $values.STRIPE_PRICE_ID -notmatch '^price_' -or $values.STRIPE_WEBHOOK_SECRET -notmatch '^whsec_'){throw 'Stripe LIVE contract mismatch'}
}
if($Service -eq 'worker'){
  if($values.SCHEDULER_BACKEND_URL -ne 'https://api.profitradar.jp' -or $values.WORKER_HEALTH_EXPOSURE -ne 'railway-private' -or $values.WORKER_HEALTH_HOST -ne '0.0.0.0' -or $values.WORKER_HEALTH_URL -notmatch '^http://[a-z0-9-]+\.railway\.internal:[0-9]+$'){throw 'Worker Railway-private contract mismatch'}
}
[pscustomobject]@{service=$Service;status='PASS';required_count=$required.Count;secret_values_printed=0} | ConvertTo-Json -Compress
