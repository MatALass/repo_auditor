$ErrorActionPreference = "Stop"

if (-not (Test-Path ".env")) {
    Write-Error "Missing .env file at project root."
}

Get-Content ".env" | ForEach-Object {
    $line = $_.Trim()
    if (-not $line) { return }
    if ($line.StartsWith("#")) { return }
    if ($line -notmatch "^\s*([^=]+)=(.*)$") { return }

    $name = $matches[1].Trim()
    $value = $matches[2].Trim()

    if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
        $value = $value.Substring(1, $value.Length - 2)
    }

    [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
}

if (-not $env:GITHUB_TOKEN) {
    Write-Error "GITHUB_TOKEN is missing in .env"
}

$outputRoot = if ($env:AUDIT_OUTPUT_DIR) { $env:AUDIT_OUTPUT_DIR } else { ".\reports" }
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outputDir = Join-Path $outputRoot "multi-github-$timestamp"

New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
Write-Host "Output directory: $outputDir"

if ($env:GITHUB_USER) {
    Write-Host "Auditing GitHub user: $($env:GITHUB_USER)"
    python -m repo_auditor.cli --github-user $env:GITHUB_USER --output $outputDir
}

if ($env:GITHUB_ORGS) {
    $orgs = $env:GITHUB_ORGS.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ }
    foreach ($org in $orgs) {
        Write-Host "Auditing GitHub org: $org"
        python -m repo_auditor.cli --github-org $org --output $outputDir
    }
}

Write-Host "Done. Reports written to $outputDir"