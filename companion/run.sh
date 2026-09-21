#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
cache=${PG_CACHE:-"$HOME/.cache/shop-pg16"}
export PG_BIN=${PG_BIN:-"$cache/root/usr/lib/postgresql/16/bin"}
export LD_LIBRARY_PATH="$cache/root/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
uv=${UV:-"$HOME/.hermes/bin/uv"}
exec "$uv" run --frozen python run_tests.py "$@"
