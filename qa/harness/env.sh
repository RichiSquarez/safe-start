# Shared environment for the ub-mobil Android version matrix harness.
export ROOT=/Users/panygolf/Documents/ub-mobil
export SDK=$ROOT/.androidsdk
export ANDROID_SDK_ROOT=$SDK
export ANDROID_HOME=$SDK
export ANDROID_AVD_HOME=$ROOT/.avd
export ADB=$SDK/platform-tools/adb
export EMULATOR=$SDK/emulator/emulator
export IMAGES_TSV=/tmp/sw/images.tsv
mkdir -p /tmp/sw
