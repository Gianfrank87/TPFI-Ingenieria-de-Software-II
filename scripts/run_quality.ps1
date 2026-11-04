$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    Write-Error "No existe el Python del proyecto: $pythonPath. No se instalo nada."
    exit 1
}
$PSNativeCommandUseErrorActionPreference = $false
$checks = @(
    @{ Name = 'Pytest + coverage'; Args = @('pytest', '--cov=src/tpfi', '--cov-report=term-missing', '--cov-fail-under=85') },
    @{ Name = 'Black'; Args = @('black', '--check', '.') },
    @{ Name = 'Ruff'; Args = @('ruff', 'check', '.') },
    @{ Name = 'Mypy'; Args = @('mypy', 'src/tpfi') },
    @{ Name = 'Pyright'; Args = @('pyright', '--pythonpath', $pythonPath, 'src/tpfi') },
    @{ Name = 'Bandit'; Args = @('bandit', '-r', 'src/tpfi') },
    @{ Name = 'pdoc'; Args = @('pdoc', '-o', 'docs/html', 'tpfi') }
)
$failed = $false
$results = @()
Push-Location -LiteralPath $projectRoot
try {
    foreach ($check in $checks) {
        Write-Host "`n>>> $($check.Name)"
        $code = 1
        try {
            $toolArgs = $check.Args
            & $pythonPath -m @toolArgs
            $code = $LASTEXITCODE
        } catch {
            Write-Host $_.Exception.Message
        }
        $status = 'PASS'
        if ($code -ne 0) { $status = 'FAIL'; $failed = $true }
        $results += "$status - $($check.Name) (exit $code)"
    }
} finally {
    Pop-Location
}
Write-Host "`nResumen de controles"
$results | ForEach-Object { Write-Host $_ }
if ($failed) { exit 1 }
exit 0
