#!/bin/bash
# Starter Android 6.0-emulatoren (API 23, arm64) med Safestart-testappen.
# Bruk:  bash start-emulator.sh
set -uo pipefail

SDK=/Users/panygolf/Documents/ub-mobil/.androidsdk
export ANDROID_SDK_ROOT=$SDK ANDROID_HOME=$SDK
export ANDROID_AVD_HOME=/Users/panygolf/Documents/ub-mobil/.avd
ADB="$SDK/platform-tools/adb"

echo "Stopper eventuell gammel emulator ..."
"$ADB" emu kill >/dev/null 2>&1
pkill -f qemu-system-aarch64 >/dev/null 2>&1
sleep 2

echo "Starter emulatoren (vindu åpnes om noen sekunder) ..."
nohup "$SDK/emulator/emulator" -avd api23 \
  -no-audio -no-boot-anim -no-snapshot -gpu host -no-metrics \
  > /tmp/emu.log 2>&1 &
disown

for i in $(seq 1 60); do
  if [ "$("$ADB" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ]; then
    echo "Klar: Android 6.0 (API 23), 720x1280."
    # åpne kiosk-hjemmet hvis appen er installert
    "$ADB" shell am start -n no.safestart.kiosk/.HomeActivity >/dev/null 2>&1 \
      && echo "Safestart-appen er åpnet."
    exit 0
  fi
  sleep 2
done

echo "Emulatoren svarte ikke. Se /tmp/emu.log"
exit 1
