#!/usr/bin/env bash
# Part D: spec section 9 procedure, run literally. "If timing fails, increase CLOCK_PERIOD by 0.5 ns and run again."
# HOST-side script (calls the `eda` wrapper). From the repo root:
#     source /home/dvd-a2-env/env.sh && bash docs/scripts/partD_sweep.sh <first_attempt_no> <period> [<period> ...]
# For each period: set CLOCK_PERIOD in pnr/config.json, run LibreLane with run tag attempt<N>_<P>ns,
# log to docs/logs/partD/attempt<N>_<P>ns_librelane.log, and stop at the first run that exits 0.
set -u
n=$1; shift
for P in "$@"; do
  tag="attempt${n}_${P}ns"
  python3 -I - "$P" <<'EOF'
import json, sys
c = json.load(open("pnr/config.json")); c["CLOCK_PERIOD"] = float(sys.argv[1])
open("pnr/config.json", "w").write(json.dumps(c, indent=2) + "\n")
EOF
  log=docs/logs/partD/${tag}_librelane.log
  start=$(date +%s)
  eda -c "cd pnr && librelane --run-tag $tag config.json" </dev/null > "$log" 2>&1
  rc=$?
  echo "librelane exit=$rc  wall=$(( $(date +%s) - start ))s" >> "$log"
  echo "$tag: CLOCK_PERIOD=$P exit=$rc"
  [ $rc -eq 0 ] && break
  n=$((n + 1))
done
