#!/bin/bash
# Drive the remaining Android versions while the host disk free space keeps
# flapping (macOS/iCloud fills and purges several GB every few minutes).
#
# For each API level: wait until there is enough free space, run the version,
# and if it died for lack of space just wait and try again. Deletes the version
# environment after a successful run, exactly as the task asks.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
. "$HERE/env.sh"

NEED_MB=${NEED_MB:-6600}      # unpacked image + AVD + emulator headroom
WAIT_S=${WAIT_S:-60}
MAX_TRIES=${MAX_TRIES:-40}    # ~40 min of waiting per version
APIS="${*:-31 33 34 35}"

for API in $APIS; do
  if [ -f "$ROOT/qa/results/api$API-baseline/summary.json" ] &&
     [ -f "$ROOT/qa/results/api$API-fixed/summary.json" ]; then
    echo "########## api $API already done, skipping"
    continue
  fi
  attempt=0
  while [ "$attempt" -lt "$MAX_TRIES" ]; do
    attempt=$((attempt + 1))
    free=$(df -m "$ROOT" | awk 'NR==2{print $4}')
    if [ "$free" -lt "$NEED_MB" ]; then
      echo "[$(date '+%H:%M:%S')] api $API try $attempt: free ${free} MB < ${NEED_MB} MB, waiting"
      sleep "$WAIT_S"
      continue
    fi
    echo "[$(date '+%H:%M:%S')] api $API try $attempt: free ${free} MB — running"
    bash "$HERE/run-version.sh" "$API" --reboot
    rc=$?
    if [ $rc -eq 0 ]; then
      echo "[$(date '+%H:%M:%S')] api $API OK"
      bash "$HERE/teardown.sh" "$API" --drop-image
      df -h "$ROOT" | tail -1
      break
    fi
    echo "[$(date '+%H:%M:%S')] api $API try $attempt FAILED rc=$rc"
    # A dead emulator may still hold the AVD; clear it before retrying.
    bash "$HERE/teardown.sh" "$API" >/dev/null 2>&1
    sleep "$WAIT_S"
  done
done
echo "########## autosweep finished"
