#!/bin/bash
# Kill the emulator and remove its AVD (and optionally the system image) to free disk.
# usage: bash teardown.sh 24 [--drop-image]
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
. "$HERE/env.sh"
API=${1:?usage: teardown.sh API [--drop-image]}
NAME=api$API
"$ADB" emu kill >/dev/null 2>&1 || true
pkill -f "qemu-system-aarch64.*-avd $NAME" >/dev/null 2>&1 || true
sleep 3
"$ADB" kill-server >/dev/null 2>&1 || true
rm -rf "$ANDROID_AVD_HOME/$NAME.avd" "$ANDROID_AVD_HOME/$NAME.ini"
echo "removed AVD $NAME"
if [ "${2:-}" = "--drop-image" ]; then
  rm -rf "$SDK/system-images/android-$API"
  echo "removed system image android-$API"
fi
df -h /System/Volumes/Data | tail -1
