param()
$ErrorActionPreference='Stop'
$repo=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$files=@(git -C $repo ls-files --cached --others --exclude-standard)
if($LASTEXITCODE -ne 0){throw 'Git file inventory failed'}
$findings=@()
foreach($relative in $files){
  if($relative -match '(^|/)(node_modules|venv|\.next)/'){continue}
  $path=Join-Path $repo $relative
  if(-not (Test-Path -LiteralPath $path -PathType Leaf)){continue}
  if($relative -match '(^|/)\.env$' -or ($relative -match '\.env\.' -and $relative -notmatch '\.env\.example$')){$findings += $relative;continue}
  $content=Get-Content -LiteralPath $path -Raw -ErrorAction SilentlyContinue
  if($null -eq $content){continue}
  if($content -match '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----' -or
     $content -match '(?<![A-Za-z0-9_])(sk|rk)_(live|test)_[A-Za-z0-9]{24,}' -or
     $content -match '(?<![A-Za-z0-9_])whsec_[A-Za-z0-9]{24,}' -or
     $content -match 'AIza[0-9A-Za-z_-]{30,}'){$findings += $relative}
}
if($findings.Count){throw "Potential committed secret material: $($findings.Count) file(s)"}
[pscustomobject]@{status='PASS';files_scanned=$files.Count;findings=0} | ConvertTo-Json -Compress
