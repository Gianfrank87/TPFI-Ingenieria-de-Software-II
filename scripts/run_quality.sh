#!/usr/bin/env bash
set -uo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)" || exit 1
python_path="$project_root/.venv/bin/python"
if [[ ! -x "$python_path" ]]; then
    printf 'No existe el Python del proyecto: %s. No se instalo nada.\n' "$python_path" >&2
    exit 1
fi
cd -- "$project_root" || exit 1
failed=0
results=()
run_check() {
    local name="$1" code status
    shift
    printf '\n>>> %s\n' "$name"
    "$python_path" -m "$@"
    code=$?
    status=PASS
    if (( code != 0 )); then status=FAIL; failed=1; fi
    results+=("$status - $name (exit $code)")
}
run_check 'Pytest + coverage' pytest --cov=tpfi --cov-report=term-missing --cov-fail-under=85
run_check Black black --check .
run_check Ruff ruff check .
run_check Mypy mypy src/tpfi
run_check Pyright pyright --pythonpath "$python_path" src/tpfi
run_check Bandit bandit -r src/tpfi
run_check pdoc pdoc -o docs/html tpfi
printf '\nResumen de controles\n'
printf '%s\n' "${results[@]}"
exit "$failed"
