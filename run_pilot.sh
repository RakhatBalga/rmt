#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
read -r -p 'Operator name (who actually starts this run): ' operator
[ -n "$operator" ] || { echo 'Operator name is required'; exit 1; }
python3 lab.py doctor
python3 lab.py build
log="evidence/pilot-console-$(date -u +%Y%m%dT%H%M%SZ).log"
python3 lab.py collect --phase pilot --rounds 2 --operator "$operator" | tee "$log"
run=$(grep '^RUN DIRECTORY: ' "$log" | tail -1 | sed 's/^RUN DIRECTORY: //')
python3 lab.py analyze "$run"
echo "Finished. Results: $run/processed/RESULTS.md"
