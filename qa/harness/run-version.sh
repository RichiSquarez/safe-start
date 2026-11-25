#!/bin/bash
# Full one-version run: baseline APK then fixed APK, each on a clean device.
# usage: bash run-version.sh API [--reboot]
#
# Deletes the AVD data between the two runs so the second install starts from a
# phone with no Device Owner, exactly like a fresh setup.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
. "$HERE/env.sh"
API=${1:?usage: run-version.sh API [--reboot]}
REBOOT=${2:-}
BASE="$ROOT/qa/artifacts/Safestart-v0-baseline.apk"
FIXED="$ROOT/qa/artifacts/Safestart-v1-fixed.apk"
AVD="$ANDROID_AVD_HOME/api$API.avd"

[ -f "$BASE" ] || { echo "missing $BASE"; exit 1; }
[ -f "$FIXED" ] || { echo "missing $FIXED"; exit 1; }

if [ ! -f "$SDK/system-images/android-$API/default/arm64-v8a/system.img" ]; then
  bash "$HERE/fetch-image.sh" "$API"; rc=$?; [ $rc -eq 0 ] || exit $rc
fi
bash "$HERE/make-avd.sh" "$API" || exit 1

for label in baseline fixed; do
  case "$label" in
    baseline) APK="$BASE" ;;
    fixed)    APK="$FIXED" ;;
  esac
  rm -f "$AVD/userdata-qemu.img"
  echo "########## api $API / $label"
  bash "$HERE/boot.sh" "$API" || { echo "boot failed for api $API"; exit 1; }
  python3 "$HERE/suite.py" "$API" "$label" "$APK" $REBOOT
done

echo "########## api $API done"
