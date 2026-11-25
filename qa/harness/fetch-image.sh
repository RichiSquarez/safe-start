#!/bin/bash
# Download and unpack one AOSP arm64 system image into the project SDK.
# usage: bash fetch-image.sh 24
#
# The disk on this Mac is nearly full, so this unpacks *inside* the SDK tree
# and then renames the directory into place: an extract-then-copy would need
# twice the space and filled the volume up on the first attempt.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
. "$HERE/env.sh"
API=${1:?usage: fetch-image.sh API}
DEST="$SDK/system-images/android-$API/default/arm64-v8a"
if [ -f "$DEST/system.img" ]; then
  echo "image android-$API already installed"
  exit 0
fi
ROW=$(awk -F'\t' -v a="$API" '$1==a{print; exit}' "$IMAGES_TSV")
[ -n "$ROW" ] || { echo "no download row for API $API"; exit 1; }
FILE=$(printf '%s' "$ROW" | cut -f2)
BASE=https://dl.google.com/android/repository/sys-img/android
URL=$BASE/$FILE
SHA=$(printf '%s' "$ROW" | cut -f4)

# An unpacked arm64 image is roughly ten times its zip, plus 2 GiB of headroom
# for the emulator's own userdata. Bail out before half-filling the volume.
FREE_MB=$(df -m "$SDK" | awk 'NR==2{print $4}')
NEED_MB=$(printf '%s' "$ROW" | cut -f3 | awk '{printf "%d", ($1*8)/1048576+512}')
echo "free ${FREE_MB} MB, estimated need ${NEED_MB} MB"
if [ "$FREE_MB" -lt "$NEED_MB" ]; then
  echo "!! not enough space for android-$API: free ${FREE_MB} MB < need ${NEED_MB} MB"
  echo "!! delete the previous version's environment first (teardown.sh API --drop-image)"
  exit 3
fi

ZIP=/tmp/sw/android-$API.zip
# Reuse a download from an earlier attempt: this disk only gives us a few GB
# for a few minutes at a time, and re-downloading 600 MB each retry throws the
# window away.
if [ -s "$ZIP" ] && [ -n "$SHA" ] &&
   printf '%s  %s\n' "$SHA" "$ZIP" | shasum -a 1 -c - >/dev/null 2>&1; then
  echo "reusing downloaded $(basename "$ZIP")"
else
  echo "downloading android-$API ..."
  curl -L --fail --retry 3 --retry-delay 2 -o "$ZIP" "$URL"
  if [ -n "$SHA" ]; then
    printf '%s  %s\n' "$SHA" "$ZIP" | shasum -a 1 -c - >/dev/null || { echo "sha1 mismatch"; rm -f "$ZIP"; exit 1; }
    echo "sha1 ok"
  fi
fi

STAGE="$SDK/system-images/.stage-$API"
rm -rf "$STAGE"
mkdir -p "$STAGE"
unzip -q "$ZIP" -d "$STAGE"
SYS=$(find "$STAGE" -name system.img -print -quit)
[ -n "$SYS" ] || { echo "system.img not found in zip"; rm -rf "$STAGE" "$ZIP"; exit 1; }
rm -rf "$SDK/system-images/android-$API"
mkdir -p "$(dirname "$DEST")"
mv "$(dirname "$SYS")" "$DEST"
rm -rf "$STAGE" "$ZIP"
echo "installed: $DEST"
du -sh "$DEST"
