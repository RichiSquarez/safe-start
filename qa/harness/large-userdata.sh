#!/bin/bash
# Provide /tmp/sw/userdata-large.img: a real ~550 MB ext4 userdata template.
#
# The Android 9+ AOSP images ship a 1 MB userdata.img that the emulator refuses
# to grow, so the guest ends up with a 1 MB /data and zygote hangs. The Android 7
# image ships a proper 550 MB ext4 that the emulator happily resizes to
# disk.dataPartition.size. Fetch it once and cache it, extracting only
# userdata.img from the zip (no need to unpack a whole system image).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
. "$HERE/env.sh"
OUT=/tmp/sw/userdata-large.img
if [ -s "$OUT" ]; then
  echo "large userdata seed already cached ($(du -h "$OUT" | cut -f1))"
  exit 0
fi
# arm64-v8a API 24 image: 305 MB zip, contains a 550 MB ext4 userdata.img.
FILE=arm64-v8a-24_r09.zip
SHA=e88ebdf4533efa0370603ee4ab0e7834e0cc364f
URL=https://dl.google.com/android/repository/sys-img/android/$FILE
ZIP=/tmp/sw/$FILE
mkdir -p /tmp/sw
if [ ! -s "$ZIP" ] || ! printf '%s  %s\n' "$SHA" "$ZIP" | shasum -a 1 -c - >/dev/null 2>&1; then
  echo "downloading $FILE ..."
  curl -sL --fail --retry 3 -o "$ZIP" "$URL"
  printf '%s  %s\n' "$SHA" "$ZIP" | shasum -a 1 -c -
fi
TMP=$(mktemp -d /tmp/sw/ud-XXXX)
unzip -o -j -q "$ZIP" "*/userdata.img" -d "$TMP"
mv "$TMP/userdata.img" "$OUT"
rm -rf "$TMP" "$ZIP"
echo "cached $OUT ($(du -h "$OUT" | cut -f1))"
