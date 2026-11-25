#!/bin/bash
# Builds one of the QA helper APKs (qa/helper-apps/<name>).
#
#   qa/harness/build-helper.sh qadialer  -> qa/artifacts/qadialer.apk
#   qa/harness/build-helper.sh qaskyss   -> qa/artifacts/qaskyss.apk
#
# The helpers are signed with the SAME keystore as the app so `adb install -r`
# can replace them without signature conflicts. They exist because the AOSP
# "default" emulator images ship no dialer, no messaging app and obviously no
# Skyss, which makes the allowlist / package-visibility path untestable.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/env.sh"

NAME="${1:?usage: build-helper.sh qadialer|qaskyss}"
SRC="$ROOT/qa/helper-apps/$NAME"
[ -d "$SRC" ] || { echo "no such helper: $SRC"; exit 1; }

BT="$SDK/build-tools/36.0.0"
AJAR="$SDK/platforms/android-34/android.jar"
[ -f "$AJAR" ] || AJAR="$ROOT/app/lib/android.jar"
OUT="$SRC/build"
KEYSTORE="$ROOT/app/.signing/safestart.jks"
mkdir -p "$ROOT/qa/artifacts"

rm -rf "$OUT"
mkdir -p "$OUT/gen" "$OUT/classes" "$OUT/dex"

echo "== link $NAME"
# no res/ in the helpers -> link the manifest alone
"$BT/aapt2" link \
  -o "$OUT/base.apk" \
  -I "$AJAR" \
  --manifest "$SRC/AndroidManifest.xml" \
  --java "$OUT/gen" \
  --min-sdk-version 23 \
  --target-sdk-version 34 \
  --version-code 1 \
  --version-name 1.0

echo "== javac"
javac -source 11 -target 11 -nowarn -classpath "$AJAR" -d "$OUT/classes" \
  $(find "$SRC/src" "$OUT/gen" -name '*.java')

echo "== d8"
"$BT/d8" --lib "$AJAR" --min-api 23 --output "$OUT/dex" \
  $(find "$OUT/classes" -name '*.class')

echo "== package + align + sign"
cd "$OUT/dex" && zip -q -X "$OUT/base.apk" classes.dex && cd "$ROOT"
"$BT/zipalign" -f -p 4 "$OUT/base.apk" "$OUT/aligned.apk"
"$BT/apksigner" sign --ks "$KEYSTORE" --ks-pass pass:android \
  --ks-key-alias safestart --key-pass pass:android \
  --out "$ROOT/qa/artifacts/$NAME.apk" "$OUT/aligned.apk"

"$BT/apksigner" verify "$ROOT/qa/artifacts/$NAME.apk" >/dev/null && echo "signed ok"
"$BT/aapt2" dump badging "$ROOT/qa/artifacts/$NAME.apk" | head -2
ls -lh "$ROOT/qa/artifacts/$NAME.apk"
