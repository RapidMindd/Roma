#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd "$(dirname "$0")" && pwd)"
if [[ ! -x "$project_dir/.venv/bin/python" || ! -f "$project_dir/build/libgaussian_blur.so" ]]; then
    "$project_dir/setup.sh"
fi
if [[ $# -eq 0 || "${1:-}" == demo ]]; then
    exec "$project_dir/.venv/bin/python" "$project_dir/demo.py"
fi
exec "$project_dir/.venv/bin/python" "$project_dir/main.py" "$@"
