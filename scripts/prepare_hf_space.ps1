# Sync store-intelligence -> Hugging Face Space clone (Docker SDK, port 7860)
# Usage:
#   git clone https://huggingface.co/spaces/SandeepChakka/store-intelligence C:\path\to\hf-store-intelligence
#   .\scripts\prepare_hf_space.ps1 -TargetDir C:\path\to\hf-store-intelligence

param(
    [Parameter(Mandatory = $true)]
    [string]$TargetDir
)

$ErrorActionPreference = "Stop"
$Src = Split-Path $PSScriptRoot -Parent
if (-not (Test-Path (Join-Path $Src "backend"))) {
    throw "Expected store-intelligence at $Src"
}

$Target = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($TargetDir)
New-Item -ItemType Directory -Force -Path $Target | Out-Null

$dirs = @("backend", "pipeline", "scripts", "configs", "tests", "docs", "dashboard", "docker")
foreach ($d in $dirs) {
    $from = Join-Path $Src $d
    if (Test-Path $from) {
        $xd = @("node_modules", "__pycache__", ".pytest_cache", "dist", "_extracted")
        robocopy $from (Join-Path $Target $d) /E /XD $xd /NFL /NDL /NJH /NJS /nc /ns /np
    }
}

# Events only (no discovery screenshots / layout PNG — HF rejects binaries)
# Copy event jsonl files recursively (no discovery screenshots / layout PNG — HF rejects binaries)
$eventsSrc = Join-Path $Src "data\events"
$eventsDst = Join-Path $Target "data\events"
New-Item -ItemType Directory -Force -Path $eventsDst | Out-Null
if (Test-Path (Join-Path $eventsSrc "output.jsonl")) {
    Copy-Item (Join-Path $eventsSrc "output.jsonl") $eventsDst -Force
}
Get-ChildItem -Path $eventsSrc -Filter "*.jsonl" -Recurse | ForEach-Object {
    $relative = $_.FullName.Substring($eventsSrc.Length + 1)
    $destFile = Join-Path $eventsDst $relative
    $destDir = Split-Path $destFile -Parent
    New-Item -ItemType Directory -Force -Path $destDir | Out-Null
    Copy-Item $_.FullName $destFile -Force
}

Copy-Item (Join-Path $Src "requirements-docker.txt") $Target -Force
Copy-Item (Join-Path $Src "DESIGN.md") $Target -Force
Copy-Item (Join-Path $Src "CHOICES.md") $Target -Force
Copy-Item (Join-Path $Src "EVALUATION_ALIGNMENT.md") $Target -Force
Copy-Item (Join-Path $Src "pytest.ini") $Target -Force
Copy-Item (Join-Path $Src "deploy\hf\Dockerfile") $Target -Force
Copy-Item (Join-Path $Src "deploy\hf\README.md") $Target -Force
Copy-Item (Join-Path $Src "deploy\hf\.gitignore") $Target -Force

# Remove HF template stub if present
Remove-Item (Join-Path $Target "app.py") -ErrorAction SilentlyContinue
Remove-Item (Join-Path $Target "requirements.txt") -ErrorAction SilentlyContinue

Write-Host "HF Space folder ready: $Target"
Write-Host "Next: cd `"$Target`" ; git add -A ; git commit -m `"Deploy Store Intelligence API + dashboard`" ; git push"
