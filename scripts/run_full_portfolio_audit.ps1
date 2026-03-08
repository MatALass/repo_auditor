param(
    [string]$OutputRoot = ".\reports",
    [string[]]$Orgs,
    [string[]]$Users,
    [switch]$TimestampedOutput,
    [switch]$SkipReviewAnalysis
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BatchScript = Join-Path $ProjectRoot "scripts\audit_all_targets.ps1"
$ExportReviewQueueScript = Join-Path $ProjectRoot "scripts\export_review_queue.py"
$AnalyzeReviewQueueScript = Join-Path $ProjectRoot "scripts\analyze_review_queue.py"
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$SrcDir = Join-Path $ProjectRoot "src"

function Get-PythonCommand {
    if (Test-Path $VenvPython) {
        Write-Host "[full-audit] Using venv Python: $VenvPython"
        return $VenvPython
    }

    try {
        & py -c "import sys" *> $null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[full-audit] Using launcher: py"
            return "py"
        }
    } catch {}

    try {
        & python -c "import sys" *> $null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[full-audit] Using launcher: python"
            return "python"
        }
    } catch {}

    throw "No usable Python interpreter found."
}

function Get-ExpectedBatchOutputDirectory {
    param(
        [string]$Root,
        [bool]$UseTimestamp
    )

    $resolvedRoot = [System.IO.Path]::GetFullPath($Root)

    if ($UseTimestamp) {
        $candidates = @()
        if (Test-Path $resolvedRoot) {
            $candidates = Get-ChildItem -Path $resolvedRoot -Directory -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -like "github_targets_audit_*" } |
                Sort-Object LastWriteTimeUtc -Descending
        }

        if ($candidates.Count -gt 0) {
            return $candidates[0].FullName
        }

        return $resolvedRoot
    }

    return $resolvedRoot
}

function Test-ReviewQueueHasReviewedRows {
    param(
        [string]$CsvPath
    )

    if (-not (Test-Path $CsvPath)) {
        return $false
    }

    $validStatuses = @("validated", "adjust_policy", "adjust_detection", "needs_context")

    foreach ($row in Import-Csv -Path $CsvPath) {
        $status = ($row.review_status | ForEach-Object { $_.ToString().Trim().ToLower() })
        if ($validStatuses -contains $status) {
            return $true
        }
    }

    return $false
}

try {
    Write-Host "[full-audit] Starting full portfolio audit..."
    Write-Host "[full-audit] Requested output root: $OutputRoot"

    $PythonCmd = Get-PythonCommand

    if (-not (Test-Path $BatchScript)) {
        throw "Batch script not found: $BatchScript"
    }

    if ($TimestampedOutput.IsPresent) {
        Write-Host "[full-audit] Running batch audit with timestamped output..."
    } else {
        Write-Host "[full-audit] Running batch audit with direct reports output..."
    }

    if ($Orgs -and $Users) {
        & $BatchScript -OutputRoot $OutputRoot -Orgs $Orgs -Users $Users @(
            if ($TimestampedOutput.IsPresent) { "-TimestampedOutput" }
        )
    }
    elseif ($Orgs) {
        & $BatchScript -OutputRoot $OutputRoot -Orgs $Orgs @(
            if ($TimestampedOutput.IsPresent) { "-TimestampedOutput" }
        )
    }
    elseif ($Users) {
        & $BatchScript -OutputRoot $OutputRoot -Users $Users @(
            if ($TimestampedOutput.IsPresent) { "-TimestampedOutput" }
        )
    }
    else {
        & $BatchScript -OutputRoot $OutputRoot @(
            if ($TimestampedOutput.IsPresent) { "-TimestampedOutput" }
        )
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Batch GitHub audit failed."
    }

    $BatchOutputRoot = Get-ExpectedBatchOutputDirectory -Root $OutputRoot -UseTimestamp $TimestampedOutput.IsPresent
    Write-Host "[full-audit] Resolved batch output directory: $BatchOutputRoot"

    $SummaryJson = Join-Path $BatchOutputRoot "batch-summary.json"
    $ReviewQueueCsv = Join-Path $BatchOutputRoot "review-queue.csv"
    $ReviewAnalysisJson = Join-Path $BatchOutputRoot "review-analysis.json"
    $ReviewAnalysisMd = Join-Path $BatchOutputRoot "review-analysis.md"

    if (-not (Test-Path $SummaryJson)) {
        throw "batch-summary.json not found after batch audit: $SummaryJson"
    }

    $PreviousPythonPath = $env:PYTHONPATH
    try {
        if ([string]::IsNullOrWhiteSpace($PreviousPythonPath)) {
            $env:PYTHONPATH = $SrcDir
        } else {
            $env:PYTHONPATH = "$SrcDir;$PreviousPythonPath"
        }

        Write-Host "[full-audit] Exporting review queue..."
        & $PythonCmd $ExportReviewQueueScript $SummaryJson --output $ReviewQueueCsv
        if ($LASTEXITCODE -ne 0) {
            throw "Review queue export failed."
        }

        if (-not $SkipReviewAnalysis.IsPresent) {
            if (Test-ReviewQueueHasReviewedRows -CsvPath $ReviewQueueCsv) {
                Write-Host "[full-audit] Analyzing review queue..."
                & $PythonCmd $AnalyzeReviewQueueScript $ReviewQueueCsv --json-output $ReviewAnalysisJson --md-output $ReviewAnalysisMd
                if ($LASTEXITCODE -ne 0) {
                    throw "Review queue analysis failed."
                }
            }
            else {
                Write-Host "[full-audit] Review queue exported, but no reviewed rows were found yet. Skipping review analysis."
            }
        }
    }
    finally {
        $env:PYTHONPATH = $PreviousPythonPath
    }

    Write-Host ""
    Write-Host "[full-audit] Done."
    Write-Host "Artifacts:"
    Write-Host " - $SummaryJson"
    Write-Host " - $ReviewQueueCsv"
    if (Test-Path $ReviewAnalysisMd) {
        Write-Host " - $ReviewAnalysisMd"
    }
    if (Test-Path $ReviewAnalysisJson) {
        Write-Host " - $ReviewAnalysisJson"
    }

    exit 0
}
catch {
    Write-Error "[full-audit] Execution failed: $($_.Exception.Message)"
    exit 1
}