#!/bin/bash
# Finish the compatibility matrix after an interrupted sweep.
#
# API 30 already has a baseline result but no fixed result, so run just that
# label (same image, same AVD), then drop the environment and let run-all.sh
# walk the remaining versions from scratch.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
. "$HERE/env.sh"
cd "$ROOT"
FIXED=qa/artifacts/Safestart-v1-fixed.apk

if [ ! -f qa/results/api30-fixed/summary.json ]; then
  echo "=== api30: fixed build only"
  rm -f "$ANDROID_AVD_HOME/api30.avd/userdata-qemu.img"
  bash "$HERE/boot.sh" 30 && python3 "$HERE/suite.py" 30 fixed "$FIXED" --reboot
fi

echo "=== dropping api30 environment"
bash "$HERE/teardown.sh" 30 --drop-image
df -h / | tail -1

echo "=== remaining versions"
bash "$HERE/run-all.sh" 31 33 34 35
echo "=== finish-sweep done"
df -h / | tail -1
