#!/usr/bin/env bash
set -euo pipefail

git init
find . -type d -name __pycache__ -prune -exec rm -rf {} +
rm -rf .pytest_cache outputs
PYTHONPATH=apps/sistema_industrial pytest -q
git add .
git commit -m "Initial SistemaIndustrial Nextango seed"

echo "Repo initialized. Add remote and push when ready."
