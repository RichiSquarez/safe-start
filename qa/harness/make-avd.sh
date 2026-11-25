#!/bin/bash
# Create a fresh AVD for one API level (arm64, 720x1280, 2G data).
# usage: bash make-avd.sh 24
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
. "$HERE/env.sh"
API=${1:?usage: make-avd.sh API}
NAME=api$API
AVD="$ANDROID_AVD_HOME/$NAME.avd"
[ -f "$SDK/system-images/android-$API/default/arm64-v8a/system.img" ] || {
  echo "image android-$API missing (run fetch-image.sh $API first)"; exit 1; }
rm -rf "$AVD" "$ANDROID_AVD_HOME/$NAME.ini"
mkdir -p "$AVD"
printf 'avd.ini.encoding=UTF-8\npath=%s\npath.rel=avd/%s.avd\ntarget=android-%s\n' \
  "$AVD" "$NAME" "$API" > "$ANDROID_AVD_HOME/$NAME.ini"
cat > "$AVD/config.ini" <<EOF
avd.ini.encoding=UTF-8
AvdId=$NAME
avd.ini.displayname=$NAME (Android SDK $API)
abi.type=arm64-v8a
tag.id=default
tag.display=Default
image.sysdir.1=system-images/android-$API/default/arm64-v8a/
hw.cpu.arch=arm64
hw.cpu.ncore=4
hw.ramSize=2048
vm.heapSize=192
disk.dataPartition.size=1G
hw.sdCard=no
hw.keyboard=yes
hw.gpu.enabled=yes
hw.gpu.mode=swiftshader_indirect
hw.lcd.density=320
hw.lcd.width=720
hw.lcd.height=1280
hw.mainKeys=no
hw.dPad=no
hw.trackBall=no
hw.accelerometer=yes
hw.sensors.orientation=yes
hw.sensors.proximity=yes
hw.audioInput=no
hw.audioOutput=no
hw.camera.back=none
hw.camera.front=none
skin.dynamic=yes
skin.name=720x1280
skin.path=_no_skin
showDeviceFrame=no
runtime.network.latency=none
runtime.network.speed=full
EOF
echo "created AVD $NAME"
