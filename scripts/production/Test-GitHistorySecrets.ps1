param()
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$objects = @(git -C $repo rev-list --objects --all)
if ($LASTEXITCODE -ne 0) { throw 'Git history inventory failed' }
$seen = [System.Collections.Generic.HashSet[string]]::new()
$findings = [System.Collections.Generic.List[string]]::new()
$scanned = 0
$largeSkipped = 0
foreach ($line in $objects) {
  $parts = $line -split ' ', 2
  $oid = $parts[0]
  if (-not $seen.Add($oid)) { continue }
  $kind = git -C $repo cat-file -t $oid
  if ($LASTEXITCODE -ne 0) { throw 'Git object inspection failed' }
  if ($kind -ne 'blob') { continue }
  $path = if ($parts.Count -gt 1) { $parts[1] } else { '(unnamed blob)' }
  $scanned++
  if ($path -match '(^|/)(\.env($|\.(?!example$))|.*\.(pem|p12|pfx|key)$)' -or
      $path -match '(^|/)(\.local-isolated|release-artifacts|backups?)(/|$)') {
    $findings.Add("path:$path")
    continue
  }
  $size = [int64](git -C $repo cat-file -s $oid)
  if ($LASTEXITCODE -ne 0) { throw 'Git object size inspection failed' }
  if ($size -gt 5MB) { $largeSkipped++; continue }
  $content = (git -C $repo cat-file blob $oid) -join "`n"
  if ($LASTEXITCODE -ne 0) { throw 'Git blob inspection failed' }
  if ($content -match '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----' -or
      $content -match '(?<![A-Za-z0-9_])(sk|rk)_(live|test)_[A-Za-z0-9]{24,}' -or
      $content -match '(?<![A-Za-z0-9_])whsec_[A-Za-z0-9]{24,}' -or
      $content -match 'AIza[0-9A-Za-z_-]{30,}') {
    $findings.Add("pattern:$path")
  }
}
$result = [pscustomobject]@{
  status = if ($findings.Count) { 'BLOCKED' } else { 'PASS' }
  blobs_scanned = $scanned
  oversized_blobs_not_content_scanned = $largeSkipped
  findings = $findings.Count
  finding_paths = @($findings | Sort-Object -Unique)
}
$result | ConvertTo-Json -Compress -Depth 3
if ($findings.Count) { exit 1 }
