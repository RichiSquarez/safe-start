#!/bin/bash
set -euo pipefail
SDK=/Users/panygolf/Documents/ub-mobil/.androidsdk
BT="$SDK/build-tools/36.0.0"
AJAR="$SDK/platforms/android-34/android.jar"
# platforms/ was deleted to save disk; a copy of android.jar lives in app/lib/
if [ ! -f "$AJAR" ]; then
  AJAR="/Users/panygolf/Documents/ub-mobil/app/lib/android.jar"
fi
APP=/Users/panygolf/Documents/ub-mobil/app
OUT="$APP/build"
PY=/Users/panygolf/Documents/ub-mobil/.venv/bin/python

test -x "$BT/aapt2" || { echo "aapt2 missing"; exit 1; }
test -f "$AJAR" || { echo "android.jar missing"; exit 1; }

rm -rf "$OUT"
mkdir -p "$OUT/gen" "$OUT/classes" "$OUT/dex" "$APP/res/mipmap-xxhdpi"

# --- launcher icon from the Safestart brand symbol -------------------------
"$PY" - <<'PY'
import pymupdf
src = pymupdf.open("/Users/panygolf/Documents/ub-mobil/brand/safestart-symbol.png")
page = src[0]
zoom = 192.0 / page.rect.width
pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=True)
out = "/Users/panygolf/Documents/ub-mobil/app/res/mipmap-xxhdpi/ic_launcher.png"
pix.save(out)
print("icon", pix.width, "x", pix.height, "->", out)
PY

# --- tile icons: SVG -> PNG so the app ships plain bitmaps ------------------
mkdir -p "$APP/res/drawable-xxhdpi"
"$PY" - <<'PYICON'
import pymupdf, glob, os
APP = "/Users/panygolf/Documents/ub-mobil/app"
out = os.path.join(APP, "res", "drawable-xxhdpi")
for f in sorted(glob.glob(os.path.join(APP, "icons", "*.svg"))):
    doc = pymupdf.open(f)
    page = doc[0]
    zoom = 144.0 / max(page.rect.width, page.rect.height)
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=True)
    name = "ic_" + os.path.basename(f).replace(".svg", ".png")
    pix.save(os.path.join(out, name))
    print("icon", name)
PYICON

echo "== aapt2 compile"
"$BT/aapt2" compile --dir "$APP/res" -o "$OUT/res.zip"

echo "== aapt2 link"
"$BT/aapt2" link \
  -o "$OUT/base.apk" \
  -I "$AJAR" \
  --manifest "$APP/AndroidManifest.xml" \
  --java "$OUT/gen" \
  --min-sdk-version 23 \
  --target-sdk-version 34 \
  --version-code 1 \
  --version-name 0.1-test \
  "$OUT/res.zip"

echo "== javac"
javac -source 11 -target 11 -nowarn \
  -classpath "$AJAR" \
  -d "$OUT/classes" \
  $(find "$APP/src" "$OUT/gen" -name '*.java')

echo "== d8"
"$BT/d8" --lib "$AJAR" --min-api 23 --output "$OUT/dex" \
  $(find "$OUT/classes" -name '*.class')

echo "== package"
cd "$OUT/dex" && zip -q -X "$OUT/base.apk" classes.dex && cd "$APP"

echo "== zipalign"
"$BT/zipalign" -f -p 4 "$OUT/base.apk" "$OUT/aligned.apk"

echo "== sign"
# The keystore must survive `rm -rf $OUT`, otherwise every build gets a new
# signature and `adb install -r` fails with INSTALL_FAILED_UPDATE_INCOMPATIBLE.
KEYSTORE="$APP/.signing/safestart.jks"
mkdir -p "$APP/.signing"
if [ ! -f "$KEYSTORE" ]; then
  keytool -genkeypair -keystore "$KEYSTORE" -storepass android \
    -alias safestart -keypass android -keyalg RSA -keysize 2048 \
    -validity 10950 -dname "CN=Safestart Test,O=Safestart UB,C=NO" >/dev/null 2>&1
fi
"$BT/apksigner" sign --ks "$KEYSTORE" --ks-pass pass:android \
  --ks-key-alias safestart --key-pass pass:android \
  --out "$APP/Safestart-test.apk" "$OUT/aligned.apk"

echo "== verify"
"$BT/apksigner" verify --print-certs "$APP/Safestart-test.apk" | head -5
ls -lh "$APP/Safestart-test.apk"
"$BT/aapt2" dump badging "$APP/Safestart-test.apk" | head -8
