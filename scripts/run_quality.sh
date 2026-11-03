#!/usr/bin/env bash
set -euo pipefail
python -m pytest
python -m black --check .
python -m ruff check .
python -m mypy src/tpfi
python -m pyright --pythonpath "$(python -c 'import sys; print(sys.executable)')" src/tpfi
python -m bandit -r src/tpfi
python -m pdoc -o docs/html tpfi
