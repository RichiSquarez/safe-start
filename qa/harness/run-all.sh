#!/bin/bash
# Walks the whole Android 7..15 compatibility matrix, one version at a time.
#
#   bash qa/harness/run-all.sh            # all versions, skipping finished ones
#   bash qa/harness/run-all.sh 30 31      # only the given API levels
#
# The disk on this machine is nearly full, so after each version the system
# image AND the AVD are deleted again (this is exactly what the task asks for:
# "delete the previous version's environment, install the new one, continue").
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
. "$HERE/env.sh"

# Android 7, 8, 9, 10, 11, 12, 13, 14, 15 - the major releases only.
ALL_APIS="24 26 28 29 30 31 33 34 35"
APIS="${*:-$ALL_APIS}"

for API in $APIS; do
  if [ -f "$ROOT/qa/results/api$API-baseline/summary.json" ] &&
     [ -f "$ROOT/qa/results/api$API-fixed/summary.json" ]; then
    echo "########## api $API already done, skipping"
    continue
  fi
  echo "########## api $API starting ($(date '+%H:%M:%S'))"
  bash "$HERE/run-version.sh" "$API" --reboot
  rc=$?
  if [ $rc -eq 3 ]; then
    echo "!!!!!!!!!! api $API skipped: not enough disk space — stopping the sweep"
    break
  fi
  if [ $rc -ne 0 ]; then
    echo "!!!!!!!!!! api $API FAILED rc=$rc — keeping environment for inspection"
    continue
  fi
  bash "$HERE/teardown.sh" "$API" --drop-image
  df -h / | tail -1
done

echo "########## matrix pass finished"
