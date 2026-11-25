#!/bin/bash
# Run ONE label (baseline|fixed) of one API level, retrying while the disk keeps
# flapping. usage: bash fix-label.sh API LABEL APK
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
. "$HERE/env.sh"
API=${1:?API}; LABEL=${2:?LABEL}; APK=${3:?APK}
for try in $(seq 1 30); do
  FREE=$(df -m / | awk 'NR==2{print $4}')
  echo "[$(date '+%H:%M:%S')] $LABEL api$API try $try, free ${FREE} MB"
  if [ "$FREE" -lt 2600 ]; then
    echo "  waiting for disk"
    sleep 45
    continue
  fi
  bash "$HERE/boot.sh" "$API" || { sleep 45; continue; }
  python3 "$HERE/suite.py" "$API" "$LABEL" "$APK" --reboot && exit 0
  sleep 45
done
exit 1
