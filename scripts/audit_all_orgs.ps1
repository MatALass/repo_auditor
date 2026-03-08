param(
    [string]$OutputRoot = ".\reports",
    [string[]]$Orgs,
    [switch]$TimestampedOutput
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RunScript = Join-Path $ProjectRoot "scripts\run_repo_auditor.ps1"
$SummaryScript = Join-Path $ProjectRoot "scripts\build_batch_summary.py"
$EnvFile = Join-Path $ProjectRoot ".env"
$SrcDir = Join-Path $ProjectRoot "src"
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

function Import-DotEnvFile {
    param(
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        Write-Host "[batch] No .env file found at: $Path"
        return
    }

    Write-Host "[batch] Loading .env from: $Path"

    foreach ($line in Get-Content $Path) {
        $trimmed = $line.Trim()

        if ([string]::IsNullOrWhiteSpace($trimmed)) {
            continue
        }

        if ($trimmed.StartsWith("#")) {
            continue
        }

        $parts = $trimmed -split "=", 2
        if ($parts.Count -ne 2) {
            continue
        }

        $key = $parts[0].Trim()
        $value = $parts[1].Trim()

        if (
            ($value.StartsWith('"') -and $value.EndsWith('"')) -or
            ($value.StartsWith("'") -and $value.EndsWith("'"))
        ) {
            $value = $value.Substring(1, $value.Length - 2)
        }

        [Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}

function Get-OrgList {
    param(
        [string[]]$ExplicitOrgs
    )

    if ($ExplicitOrgs -and $ExplicitOrgs.Count -gt 0) {
        return $ExplicitOrgs
    }

    $raw = $env:GITHUB_ORGS
    if ([string]::IsNullOrWhiteSpace($raw)) {
        throw "No organizations provided. Pass -Orgs or define GITHUB_ORGS in .env."
    }

    $orgs = $raw `
        -split "[,; ]+" `
        | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } `
        | Select-Object -Unique

    if (-not $orgs -or $orgs.Count -eq 0) {
        throw "GITHUB_ORGS is defined but no valid organization names were parsed."
    }

    return $orgs
}

function Get-PythonCommand {
    if (Test-Path $VenvPython) {
        Write-Host "[batch] Using venv Python: $VenvPython"
        return $VenvPython
    }

    try {
        & py -c "import sys" *> $null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[batch] Using launcher: py"
            return "py"
        }
    } catch {}

    try {
        & python -c "import sys" *> $null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[batch] Using launcher: python"
            return "python"
        }
    } catch {}

    throw "No usable Python interpreter found."
}

function Get-BatchOutputDirectory {
    param(
        [string]$Root,
        [bool]$UseTimestamp
    )

    $resolvedRoot = [System.IO.Path]::GetFullPath($Root)

    if ($UseTimestamp) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        return (Join-Path $resolvedRoot "github_orgs_audit_$timestamp")
    }

    return $resolvedRoot
}

function Reset-OrgOutputDirectory {
    param(
        [string]$DirectoryPath
    )

    if (Test-Path $DirectoryPath) {
        Remove-Item -Recurse -Force $DirectoryPath
    }

    New-Item -ItemType Directory -Force -Path $DirectoryPath | Out-Null
}

function Remove-PreviousBatchSummaryFiles {
    param(
        [string]$BatchOutputRoot
    )

    $summaryJson = Join-Path $BatchOutputRoot "batch-summary.json"
    $summaryMd = Join-Path $BatchOutputRoot "batch-summary.md"

    if (Test-Path $summaryJson) {
        Remove-Item -Force $summaryJson
    }

    if (Test-Path $summaryMd) {
        Remove-Item -Force $summaryMd
    }
}

try {
    Write-Host "[batch] Project root: $ProjectRoot"
    Write-Host "[batch] Requested output root: $OutputRoot"

    Import-DotEnvFile -Path $EnvFile
    $OrgList = Get-OrgList -ExplicitOrgs $Orgs
    $PythonCmd = Get-PythonCommand

    Write-Host "[batch] Organizations to audit: $($OrgList -join ', ')"

    $BatchOutputRoot = Get-BatchOutputDirectory -Root $OutputRoot -UseTimestamp $TimestampedOutput.IsPresent
    New-Item -ItemType Directory -Force -Path $BatchOutputRoot | Out-Null
    Remove-PreviousBatchSummaryFiles -BatchOutputRoot $BatchOutputRoot

    Write-Host "[batch] Batch output directory: $BatchOutputRoot"

    $Failures = @()

    foreach ($org in $OrgList) {
        Write-Host ""
        Write-Host "=== Auditing GitHub org: $org ==="

        $orgOutput = Join-Path $BatchOutputRoot $org
        Reset-OrgOutputDirectory -DirectoryPath $orgOutput

        & $RunScript --github-org $org --output $orgOutput

        if ($LASTEXITCODE -ne 0) {
            $Failures += $org
            Write-Warning "Audit failed for org: $org"
        }
    }

    $PreviousPythonPath = $env:PYTHONPATH
    try {
        if ([string]::IsNullOrWhiteSpace($PreviousPythonPath)) {
            $env:PYTHONPATH = $SrcDir
        } else {
            $env:PYTHONPATH = "$SrcDir;$PreviousPythonPath"
        }

        Write-Host "[batch] Building consolidated summary..."
        & $PythonCmd $SummaryScript $BatchOutputRoot

        if ($LASTEXITCODE -ne 0) {
            throw "Batch summary generation failed."
        }
    }
    finally {
        $env:PYTHONPATH = $PreviousPythonPath
    }

    Write-Host ""
    Write-Host "Batch output directory: $BatchOutputRoot"
    Write-Host "Combined summary files:"
    Write-Host " - $([System.IO.Path]::Combine($BatchOutputRoot, 'batch-summary.md'))"
    Write-Host " - $([System.IO.Path]::Combine($BatchOutputRoot, 'batch-summary.json'))"

    if ($Failures.Count -gt 0) {
        Write-Host "Failed orgs: $($Failures -join ', ')"
        exit 1
    }

    Write-Host "All organization audits completed successfully."
    exit 0
}
catch {
    Write-Error "[batch] Execution failed: $($_.Exception.Message)"
    exit 1
}