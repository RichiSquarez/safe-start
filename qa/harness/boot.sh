#!/bin/bash
# Boot the AVD for one API level headless and wait until it is usable.
# usage: bash boot.sh 24
#
# Death detection is deliberately slack: the "emulator" binary is a launcher
# that only re-execs qemu-system-aarch64 once it has parsed the AVD, so an
# immediate pgrep misses it and a tight threshold aborts a healthy boot.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
. "$HERE/env.sh"
API=${1:?usage: boot.sh API}
NAME=api$API
LOG=/tmp/sw/emu-$API.log
"$ADB" emu kill >/dev/null 2>&1 || true
pkill -f "qemu-system-aarch64.*-avd $NAME" >/dev/null 2>&1 || true
sleep 2
"$ADB" start-server >/dev/null 2>&1
# Seed the data partition from a valid ext4 template. Two things matter here:
#  * without the file the emulator tries to *create* a 6 GiB partition and dies
#    on this full disk ("Not enough space to create userdata partition");
#  * newer images ship a 1 MB "empty" userdata.img, which the emulator does NOT
#    grow, so /data ends up 1 MB and zygote hangs forever (Android 9 never
#    reaches sys.boot_completed). Seeding a real 550 MB ext4 makes the emulator
#    resize it to disk.dataPartition.size, which is what we want.
AVD="$ANDROID_AVD_HOME/$NAME.avd"
TEMPLATE="$SDK/system-images/android-$API/default/arm64-v8a/userdata.img"
if [ -f "$TEMPLATE" ]; then
  TSIZE=$(stat -f %z "$TEMPLATE")
else
  TSIZE=0
fi
if [ "$TSIZE" -lt 67108864 ]; then
  echo "image template is only $TSIZE bytes - using the large ext4 seed"
  bash "$HERE/large-userdata.sh" || exit 1
  TEMPLATE=/tmp/sw/userdata-large.img
fi
if [ ! -f "$AVD/userdata-qemu.img" ]; then
  cp "$TEMPLATE" "$AVD/userdata-qemu.img"
  echo "seeded userdata-qemu.img from $(basename "$TEMPLATE")"
fi
# The emulator writes its gRPC jwk material into $TMPDIR/running/...; when that
# fails it aborts with "FATAL | Failed to create jwk directory". Keep it inside
# the project so the path always exists and is writable.
# macOS TCC denies writes under ~/Library/Caches/TemporaryItems, and the
# emulator builds its gRPC jwk material there - it aborts with
# "FATAL | Failed to create jwk directory". Pointing HOME into the project
# moves that path somewhere writable.
export HOME="$ROOT/.avd/home"
export ANDROID_USER_HOME="$ROOT/.avd/home/.android"
mkdir -p "$HOME/Library/Caches"
TMPD="$ROOT/.avd/tmp"
mkdir -p "$TMPD"
export TMPDIR="$TMPD"
echo "booting $NAME (log: $LOG)"
nohup "$EMULATOR" -avd "$NAME" -no-audio -no-boot-anim -no-snapshot -no-metrics \
  -gpu swiftshader_indirect -no-window > "$LOG" 2>&1 &
DEAD=0
for i in $(seq 1 400); do
  if ! pgrep -f "qemu-system-aarch64.*-avd $NAME" >/dev/null 2>&1; then
    DEAD=$((DEAD + 1))
    if [ $DEAD -ge 25 ]; then echo "EMULATOR DIED"; tail -30 "$LOG"; exit 1; fi
  else
    DEAD=0
  fi
  B=$("$ADB" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')
  if [ "$B" = "1" ]; then
    echo "boot completed after ~$((i*2))s"
    "$ADB" shell settings put global window_animation_scale 0 >/dev/null 2>&1
    "$ADB" shell settings put global transition_animation_scale 0 >/dev/null 2>&1
    "$ADB" shell settings put global animator_duration_scale 0 >/dev/null 2>&1
    "$ADB" shell input keyevent 82 >/dev/null 2>&1
    "$ADB" shell wm dismiss-keyguard >/dev/null 2>&1
    sleep 3
    echo "release: $("$ADB" shell getprop ro.build.version.release | tr -d '\r')  sdk: $("$ADB" shell getprop ro.build.version.sdk | tr -d '\r')"
    exit 0
  fi
  sleep 2
done
echo "BOOT TIMEOUT"; tail -30 "$LOG"; exit 1
