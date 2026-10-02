param([Parameter(Mandatory=$true)][string]$RequireExplicitProductionApproval)
$ErrorActionPreference='Stop'
if($RequireExplicitProductionApproval -ne 'I_APPROVE_READ_ONLY_PRODUCTION_SMOKE_TEST'){throw 'Explicit Production smoke approval is required'}
$targets=@('https://profitradar.jp/','https://api.profitradar.jp/health','https://api.profitradar.jp/ready')
foreach($target in $targets){
  $response=Invoke-WebRequest -Uri $target -Method Get -MaximumRedirection 0 -TimeoutSec 10 -SkipHttpErrorCheck
  if($response.StatusCode -lt 200 -or $response.StatusCode -ge 300){throw 'Production smoke endpoint failed'}
}
[pscustomobject]@{status='PASS';checks=$targets.Count;write_requests=0} | ConvertTo-Json -Compress
