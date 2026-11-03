$ErrorActionPreference = "Stop"
$pythonPath = (Get-Command python -ErrorAction Stop).Source
$checks = @(
    @("pytest"),
    @("black", "--check", "."),
    @("ruff", "check", "."),
    @("mypy", "src/tpfi"),
    @("pyright", "--pythonpath", $pythonPath, "src/tpfi"),
    @("bandit", "-r", "src/tpfi"),
    @("pdoc", "-o", "docs/html", "tpfi")
)
foreach ($check in $checks) {
    & $pythonPath -m @check
    if ($LASTEXITCODE -ne 0) {
        throw "Falló el control: $($check -join ' ')"
    }
}
