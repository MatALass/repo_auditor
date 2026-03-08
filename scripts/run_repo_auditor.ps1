param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CliArgs
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$SrcDir = Join-Path $ProjectRoot "src"
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

function Get-PythonCommand {
    param(
        [string]$PreferredVenvPython
    )

    if (Test-Path $PreferredVenvPython) {
        Write-Host "[repo-auditor] Using venv Python: $PreferredVenvPython"
        return $PreferredVenvPython
    }

    try {
        & py -c "import sys" *> $null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[repo-auditor] Using launcher: py"
            return "py"
        }
    } catch {}

    try {
        & python -c "import sys" *> $null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[repo-auditor] Using launcher: python"
            return "python"
        }
    } catch {}

    throw "No usable Python interpreter found. Install Python or restore .venv."
}

function Test-RequiredDependencies {
    param(
        [string]$PythonCmd
    )

    & $PythonCmd -c "import requests, dotenv" *> $null
    if ($LASTEXITCODE -ne 0) {
        throw @"
Missing required dependencies for repo-auditor in the selected Python environment.

Install them once with:
  py -m pip install requests python-dotenv

Or, if you use a virtual environment:
  .\.venv\Scripts\python.exe -m pip install requests python-dotenv
"@
    }
}

Write-Host "[repo-auditor] Project root: $ProjectRoot"
Write-Host "[repo-auditor] CLI args: $($CliArgs -join ' ')"

$PythonCmd = Get-PythonCommand -PreferredVenvPython $VenvPython
Test-RequiredDependencies -PythonCmd $PythonCmd

$PreviousPythonPath = $env:PYTHONPATH
try {
    if ([string]::IsNullOrWhiteSpace($PreviousPythonPath)) {
        $env:PYTHONPATH = $SrcDir
    } else {
        $env:PYTHONPATH = "$SrcDir;$PreviousPythonPath"
    }

    Write-Host "[repo-auditor] PYTHONPATH set to include: $SrcDir"
    & $PythonCmd -m repo_auditor.cli @CliArgs
    exit $LASTEXITCODE
}
catch {
    Write-Error "[repo-auditor] Execution failed: $($_.Exception.Message)"
    exit 1
}
finally {
    $env:PYTHONPATH = $PreviousPythonPath
}