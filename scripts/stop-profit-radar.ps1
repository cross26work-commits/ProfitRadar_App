$ErrorActionPreference='Stop'
$repo=Split-Path -Parent $PSScriptRoot
$runtime=Join-Path $repo '.local-runtime'
foreach($name in @('frontend','backend')){
  $pidFile=Join-Path $runtime "$name.pid"
  if(!(Test-Path $pidFile)){continue}
  $processId=[int](Get-Content $pidFile -Raw)
  $process=Get-CimInstance Win32_Process -Filter "ProcessId=$processId" -ErrorAction SilentlyContinue
  if($process -and (($process.CommandLine -like "*$repo*") -or ($name -eq 'frontend' -and $process.CommandLine -like '*127.0.0.1*3101*'))){
    taskkill.exe /PID $processId /T /F *> $null
  } elseif($process){ throw "Refusing to stop unverified process $processId" }
}
npx --yes supabase@2.117.0 stop --workdir $runtime
if($LASTEXITCODE -ne 0){throw 'Local Supabase did not stop cleanly.'}
Write-Host 'Profit Radar local processes stopped. Docker volumes were not deleted.'
