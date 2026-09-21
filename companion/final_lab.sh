#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
log="${FINAL_LAB_LOG:-$(mktemp /tmp/shop-final-lab-XXXXXX.log)}"
set +e
bash run.sh "$@" 2>&1 | tee "$log"
status=${PIPESTATUS[0]}
set -e
printf '\nFINAL_LAB_LOG=%s\nFINAL_LAB_EXIT_CODE=%s\n' "$log" "$status"
if [ "$status" -ne 0 ]; then
  exit "$status"
fi
printf 'FINAL_LAB_RESULT=passed\n'
