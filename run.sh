#!/bin/bash

set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "=== 1. Activating virtual environment ==="
source .venv/bin/activate

echo "=== 2. Installing/updating package with uv ==="
uv pip install -e .

echo "=== 3. Running benchmark script ==="
python src/jssp/experiments/run_benchmark.py \
    "$@" \
    --config experiments/configs/final/toy_instances_benchmark.yaml # default config
