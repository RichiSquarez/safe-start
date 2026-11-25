# Android uten Android Studio: CLI-verktøykjede, Gradle-fri APK-bygging og emulator på Apple Silicon

**Dato:** 2026-11-23
**Mål:** bygge og kjøre en vanlig Java-Android-app (`no.safestart.kiosk`, launcher/kiosk, `minSdkVersion 23`, `targetSdkVersion 34`) med kommandolinjeverktøy alene, uten Gradle og uten Android Studio, på en maskin med ca. 3,7 GB ledig disk.
**Metode:** primærkilder (developer.android.com, source.android.com, AOSP-kildekode, Googles repository-XML) + byte-presise målinger av pakkearkivene + faktiske målinger på denne maskinen.

Maskinen som er målt på (verifisert lokalt):

| Faktum | Verdi |
|---|---|
| OS / arkitektur | macOS 27.2 (build 26B123), arm64 |
| Ledig disk ved oppgavestart | 3,7 GB (volum 228 GiB, 99 % fullt) |
| JDK | Temurin OpenJDK 25.0.1 (`/Library/Java/JavaVirtualMachines/temurin-25.jdk/Contents/Home`) |
| Installert på forhånd | ingen Android Studio, ingen Android SDK, ingen Gradle, ingen `adb` på PATH |
| Homebrew | `/opt/homebrew/bin/brew` |
| Nettverk | `dl.google.com` fungerer |

Alle nedlastingsstørrelser under er hentet fra Googles repository-XML (`<size>`-feltene). Installasjonsstørrelser er **ikke dokumentert av Google**; de er målt her ved å lese zip-arkivenes central directory og summere ukomprimerte oppføringer — og der det er mulig er de krysset mot faktisk `du` på denne maskinen. Der jeg ikke har tall, står det eksplisitt.

---

## Kort oppsummering

- **Du trenger ikke Android Studio og ikke Gradle.** Fire SDK-pakker holder: `cmdline-tools;latest`, `platform-tools`, `platforms;android-34`, `build-tools;34.0.0` — til sammen ca. **312 MB nedlasting / ca. 516 MB installert**.
- **JDK 25 fungerer fint som `javac`, men bruk `--release 11`.** d8 i build-tools 34 spiser klassefiler opp til Java 17 (major 61); `--release 21+` (major 65) blir avvist av eldre D8/R8 med `Unsupported class file major version 65`. Merk fella: d8 sin egen `--release`-flagg betyr «fjern debug-info», ikke Java-versjon.
- **Byggerekka er fem kommandoer:** `aapt2 compile` → `aapt2 link` → `javac` → `d8` → `zipalign` → `apksigner`. Ingen XML-oppskrift, ingen Gradle-demon, ingen `~/.gradle`-cache.
- **Emulatoren er den dyre delen, ikke verktøyene.** `emulator`-pakken er ca. **421 MB nedlasting / ca. 1,32 GB installert** (stock 37.4.1), og hver arm64-systemavbildning legger på **1,5–3,2 GiB** fordi `system.img` er en nesten full ext4-partisjon.
- **Minst mulig arm64-avbildning som tilfredsstiller `minSdk 23` er `system-images;android-23;default;arm64-v8a`** (253,8 MB nedlasting, **1,5 GiB på disk**). arm64-avbildninger finnes helt fra API 21 — påstanden om at arm64 starter senere er feil.
- **ATD-avbildningene («automated test device») sparer bare nedlasting, ikke disk.** `aosp_atd` er ca. 100 MB mindre å laste ned, men like stor installert som `default` — og ATD **skrur av hardware-rendering**, så skjermbildetester av en kiosk-UI er en dårlig idé der.
- **Diskbudsjettet sprekker hvis du vil ha emulator på denne maskinen.** Verktøy + emulator + API 23-avbildning ≈ 1,7–3,0 GB installert, og emulatoren krever i tillegg flere GB ledig for å starte. Her stoppet den faktisk med `FATAL | Your device does not have enough disk space to run avd: api23`. Bygg-og-installer på fysisk enhet krever bare ca. 0,5 GB.
- **Manifestet må ha `android:exported="true"`** på launcher-aktiviteten (krav fra API 31 når appen har intent-filter), og på device-admin-receiveren. `minSdk 23` + `targetSdk 34` installerer normalt på API 30/33/34 — Android 14-gulvet gjelder `targetSdkVersion`, ikke `minSdkVersion`.

---

## 1. Minimal SDK-installasjon for kommandolinjebygging

### 1.1 Hvilke pakker er strengt nødvendige

| Pakke | Repository-revisjon | Nedlasting (dokumentert) | Installert (målt) | Hvorfor |
|---|---|---|---|---|
| `cmdline-tools;latest` | 23.0 | 155,4 MB | 180,5 MB | `sdkmanager`, `avdmanager`, `apkanalyzer` |
| `platform-tools` | 37.0.3 | 16,6 MB | 40,2 MB | `adb` (og `fastboot`) |
| `platforms;android-34` | `platform-34-ext7_r03` | 63,2 MB | 99,1 MB | `android.jar` — kompilering og `aapt2 -I` |
| `build-tools;34.0.0` | 34.0.0 | 76,6 MB | 196,2 MB | `aapt2`, `d8`, `zipalign`, `apksigner` |
| **Sum** | | **311,8 MB** | **516,0 MB** | |

Kilder: <https://dl.google.com/android/repository/repository2-3.xml> (autoritativ pakkeliste med størrelser), <https://developer.android.com/tools/sdkmanager>, <https://developer.android.com/tools/releases/build-tools>, <https://developer.android.com/tools/releases/platform-tools>.

Ikke nødvendig: `sources;android-34`, `ndk`, `cmake`, `docs`, `extras;google;m2repository`, eldre `build-tools`, `platforms;android-23`, Play-Store-avbildninger, Gradle, Android Studio.

### 1.2 Riktig URL og riktig layout på disk

**Viktig korreksjon:** mønsteret `commandlinetools-mac-*-latest.zip` gjelder ikke lenger. Fra og med cmdline-tools 22.0 er arkivet splittet per arkitektur, så filnavnet er `commandlinetools-mac_arm64-<buildid>_latest.zip`. Siste arkiv som matcher det gamle mønsteret er cmdline-tools 19.0 (`commandlinetools-mac-13114758_latest.zip`, 143,3 MB).

Gjeldende arkiv for Apple Silicon (cmdline-tools 23.0):

```
https://dl.google.com/android/repository/commandlinetools-mac_arm64-16111833_latest.zip
```

Layoutkravet er dokumentert i <https://developer.android.com/tools/sdkmanager>, med denne ordlyden: *«In the unzipped cmdline-tools directory, create a sub-directory called latest … Move the original cmdline-tools directory contents, including the lib directory, bin directory, NOTICE.txt file, and source.properties file, into the newly created latest directory.»*

Altså: zipen pakker ut til én mappe `cmdline-tools/` med `bin/`, `lib/`, `NOTICE.txt`, `source.properties`. Den mappen skal **flyttes/omdøpes** til `<sdk>/cmdline-tools/latest/` — ikke legges inni den. Resultatet må være:

```
<sdk>/cmdline-tools/latest/bin/sdkmanager
<sdk>/cmdline-tools/latest/lib/...
<sdk>/cmdline-tools/latest/source.properties
```

`sdkmanager` finner SDK-roten ved `--sdk_root=` eller via `ANDROID_HOME` / `ANDROID_SDK_ROOT`; uten `latest`-nivå feiler den med en «could not determine SDK root»-melding fordi den leter etter `cmdline-tools/<versjon>/`.

```bash
export ANDROID_HOME="$PWD/.androidsdk"          # eller $HOME/Library/Android/sdk
mkdir -p "$ANDROID_HOME/cmdline-tools"
curl -fL -o /tmp/clt.zip \
  https://dl.google.com/android/repository/commandlinetools-mac_arm64-16111833_latest.zip
rm -rf /tmp/clt && mkdir -p /tmp/clt
unzip -q /tmp/clt.zip -d /tmp/clt
mv /tmp/clt/cmdline-tools "$ANDROID_HOME/cmdline-tools/latest"
"$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" --version
```

### 1.3 Lisenser og installasjon

```bash
export SDKM="$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager"
yes | "$SDKM" --sdk_root="$ANDROID_HOME" --licenses
"$SDKM" --sdk_root="$ANDROID_HOME" \
  "platform-tools" "platforms;android-34" "build-tools;34.0.0"
"$SDKM" --sdk_root="$ANDROID_HOME" --list_installed
```

Merknader:
- `--licenses` må kjøres først, ellers avbrytes installasjonen med «license not accepted».
- Installer **én pakke om gangen** når disken er stram: `sdkmanager` laster ned arkivet til `<sdk>/.temp` / `~/.android/cache` **før** det pakkes ut, så toppforbruket er `installert + arkiv`. Slett `<sdk>/.temp` og `~/.android/cache` etterpå.
- cmdline-tools 23.0 krever Java 17+; JDK 25 er ikke dokumentert som testet, men fungerte her. Hvis `sdkmanager` skulle feile på JDK 25: installer en JDK 17 ved siden av og pek `JAVA_HOME` dit bare for SDK-kommandoene.

### 1.4 Disk-sparetriks som faktisk virker: bare `android.jar`

`platforms;android-34` er 63,2 MB nedlasting / 99,1 MB installert, men det eneste bygget trenger er `android.jar`. På denne maskinen er `platforms/` droppet helt og kun jaret beholdt:

```
app/lib/android.jar        # 25 MiB målt (du -h)
```

Det sparer ca. **74 MB** og gjør `aapt2`- og `javac`-kommandoene flyttbare (`-I app/lib/android.jar`). Fungerer fordi `android.jar` er selvstendig — men du mister `sdkmanager`s eierskap til filen, så ved oppgradering må jaret hentes på nytt. APK-en blir identisk: `compileSdkVersion` kommer fra manifestet/`aapt2`-flaggene.

---

## 2. Bygge APK uten Gradle, steg for steg

Forutsetning: kildetre som under (`app/` = modulrot):

```
app/AndroidManifest.xml
app/res/values/strings.xml
app/res/xml/device_admin.xml
app/res/mipmap-xxhdpi/ic_launcher.png
app/src/no/safestart/kiosk/*.java
app/lib/android.jar          # eller $ANDROID_HOME/platforms/android-34/android.jar
```

```bash
export ANDROID_HOME="$PWD/.androidsdk"
BT="$ANDROID_HOME/build-tools/34.0.0"
AJ="$PWD/app/lib/android.jar"          # alternativt: $ANDROID_HOME/platforms/android-34/android.jar
rm -rf app/build && mkdir -p app/build/{compiled,gen,classes,dex}
```

### 2.1 `aapt2 compile` — ressurser til `.flat`

```bash
"$BT/aapt2" compile --dir app/res -o app/build/compiled
```

- `--dir` kompilerer hele katalogen rekursivt. Dokumentert i <https://developer.android.com/tools/aapt2>: syntaksen er `aapt2 compile path-to-input-files [options] -o output-directory/`, og `--dir` tar en hel mappe (ingen inkrementell fordel — den kompilerer alt hver gang).
- Utdata er `.flat`-filer. Bruk `find` når du sender dem videre, fordi underkatalogstrukturen bevares:

```bash
find app/build/compiled -name '*.flat'
```

### 2.2 `aapt2 link` — manifest + R.java + `base.apk`

```bash
"$BT/aapt2" link \
  -o app/build/base.apk \
  -I "$AJ" \
  --manifest app/AndroidManifest.xml \
  --java app/build/gen \
  --min-sdk-version 23 \
  --target-sdk-version 34 \
  --auto-add-overlay \
  $(find app/build/compiled -name '*.flat')
```

| Flagg | Betydning (jf. aapt2-dokumentasjonen) |
|---|---|
| `-I <android.jar>` | basis-API-et som ressursene lenkes mot |
| `--manifest` | manifestet som skal inn i APK-en |
| `--java <dir>` | genererer `R.java` (pakke utledes fra manifestets `package`) |
| `--min-sdk-version` / `--target-sdk-version` | injiseres i manifestet når appen ikke selv har `uses-sdk` |
| `--auto-add-overlay` | tillater at ressurser legges til uten å være deklarert i en overlay |
| `-o base.apk` | ualignert, usignert APK med `resources.arsc` + manifest |

`aapt2 link` produserer **ikke** dex — APK-en er på dette punktet ressurser + manifest bare.

### 2.3 `javac --release` — hvilken verdi er trygg for d8 i build-tools 34?

Verifisert på denne maskinen med Temurin 25.0.1: `javac --release 8|11|17|21|25` gir klassefil-major 52/55/61/65/69, og `--release 8` skriver ut ``source value 8 is obsolete and will be removed in a future release``. javac 25 kan også lese Java-17-klassefiler (major 61) fra classpath mens den kompilerer med `--release 11`.

```bash
javac --release 11 -classpath "$AJ" -d app/build/classes \
  $(find app/src app/build/gen -name '*.java')
```

Anbefaling og begrunnelse:

| `--release` | Klassefil-major | Egnethet med d8 i build-tools 34 |
|---|---|---|
| 8 | 52 | virker, men «obsolete»-advarsel; unødvendig lavt |
| **11** | **55** | **anbefalt** — god margin, ingen advarsler, dekker alt enkel Java trenger |
| 17 | 61 | praktisk tak for denne build-tools-æraen; virker, men gir ingen gevinst uten språkfunksjoner du ikke trenger |
| 21 / 25 | 65 / 69 | **ikke bruk** — eldre D8/R8 avviser med `Unsupported class file major version 65` |

Viktige forbehold:

- **d8 sin egen `--release`-flagg er ikke en Java-versjon.** Dokumentert i <https://developer.android.com/tools/d8>: den betyr «compiler DEX uten debug-informasjon». Java-nivået bestemmes av `javac` + `--min-api` i d8.
- **Google dokumenterer ikke klassefil-taket per build-tools-versjon.** Påstanden «build-tools 34 tar maks major 61» er derfor empirisk, ikke dokumentert — verifiser lokalt med en enklasses røyktest og `"$BT/d8" --version`.
- **JDK 9+ fjernet `-bootclasspath`**, så `java.*` løses fra JDK 25 sitt `ct.sym`, ikke fra `android.jar`. Konsekvens: desktop-only-API-er (f.eks. `java.nio.file`, `Objects.requireNonNullElse`) kompilerer men krasjer på enheten med `NoSuchMethodError`. Hold deg til API-er som finnes i API 23 og test på enhet/emulator. `--release 11` hjelper mot *språk*-nivået, ikke mot Android-API-tilgjengelighet.
- Ikke bruk records/text blocks (Java 15/16) — de krever `--release 17` og desugaring som er dårlig dekket i denne build-tools-generasjonen.

### 2.4 `d8` — klassefiler til `classes.dex`

```bash
"$BT/d8" --lib "$AJ" --min-api 23 --output app/build/dex \
  $(find app/build/classes -name '*.class')
```

- Plassering og bruk er dokumentert i <https://developer.android.com/tools/d8>: d8 ligger i `android_sdk/build-tools/<versjon>/` (tilgjengelig siden build-tools 28.0.1), syntaks `d8 path-to-input-files [options]`.
- `--lib <android.jar>` er **påkrevd** når bytekoden bruker Java 8-språkfunksjoner (lambda, standardmetoder), fordi desugaringen trenger bibliotekklassene.
- `--min-api 23` setter laveste API for den produserte dexen; med lambda/desugaring bestemmer dette hvilke runtime-hjelpeklasser som brukes.
- **Inndata:** både `*.class`-filer og JAR/ZIP/APK går. **Utdata:** `--output <katalog>` gir `classes.dex` inne i katalogen; gir du et `.zip`/`.jar`-navn i stedet, får du et arkiv som inneholder dexen.
- Har du en `classes/`-mappe (typisk fra `javac -d`), send inn `find ... -name '*.class'` slik over. Har du en `classes.jar`, send jaret direkte: `d8 --lib "$AJ" --min-api 23 --output app/build/dex app/build/classes.jar`.
- `--no-desugaring` slår av desugaring (bare hvis du vet at du ikke trenger den); `--classpath` brukes for bibliotek som *ikke* skal inn i dexen.

### 2.5 Legge dexen inn i APK-en

`aapt2 link` lagde `base.apk` uten `classes.dex`. Dexen må ligge i **APK-roten**:

```bash
( cd app/build/dex && zip -q -j ../base.apk classes.dex )
```

`-j` = «junk paths», altså `classes.dex` legges i roten uansett hvor kommandoen kjøres fra. Sjekk:

```bash
unzip -l app/build/base.apk | grep -E 'classes.dex|resources.arsc|AndroidManifest'
```

### 2.6 `zipalign` — før signering, alltid

```bash
"$BT/zipalign" -P 16 -f -v 4 app/build/base.apk app/build/aligned.apk
```

Dokumentert i <https://developer.android.com/tools/zipalign>:

- `4` = 4-byte justering for alle ukomprimerte oppføringer.
- `-P 16` = sidejuster ukomprimerte `.so`-filer til 16 KiB. **`-p` (4 KiB) er deprecated** — dokumentasjonen sier eksplisitt «`-P 16` instead». Har du ingen native biblioteker, er `-P 16` likevel riktig valg for framtiden.
- `-f` overskriver utdata, `-v` er verbos, `-c` er bare sjekk (`zipalign -c -v 4 app.apk`).
- **Rekkefølge:** zipalign **må** kjøres **før** `apksigner`. `apksigner` bevarer justeringen; gjør du det motsatt, ødelegger zipalign signaturen. (Unntaket er den deprecated `jarsigner`-flyten, der zipalign kjøres etterpå.)

### 2.7 Debug-keystore med `keytool`

```bash
mkdir -p "$HOME/.android"
keytool -genkeypair -v \
  -keystore "$HOME/.android/debug.keystore" \
  -storetype PKCS12 \
  -storepass android -keypass android \
  -alias androiddebugkey \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -dname "CN=Android Debug,O=Android,C=US"
```

- `androiddebugkey` / `android` er **konvensjonen** Android-verktøyene bruker, ikke noe Google dokumenterer som konstant. Dokumentert i <https://developer.android.com/studio/publish/app-signing> er at SDK-verktøyene lager `$HOME/.android/debug.keystore` ved første debug-kjøring, at passordene settes for både keystore og nøkkel, at sertifikatet er selvsignert med 30 års gyldighet, og at filen regenereres hvis den slettes.
- Bruk `-storetype PKCS12`: JDK 25 advarer mot JKS, og PKCS12 krever at `-keypass` er lik `-storepass` (her: `android`). `apksigner` leser begge formater.
- `-validity 10000` dager ≈ 27 år (Android-verktøyene bruker 30 år / 10950 dager).

### 2.8 `apksigner` — signer og verifiser

```bash
"$BT/apksigner" sign \
  --ks "$HOME/.android/debug.keystore" \
  --ks-pass pass:android \
  --ks-key-alias androiddebugkey \
  --min-sdk-version 23 \
  --out app/build/app-debug.apk \
  app/build/aligned.apk

"$BT/apksigner" verify --print-certs --min-sdk-version 23 app/build/app-debug.apk
```

Dokumentert i <https://developer.android.com/tools/apksigner>:

- Syntaks: `apksigner sign --ks keystore.jks [signer_options] app.apk`.
- `--out <fil>` — uten den signeres APK-en **på stedet**.
- `--ks-pass <format>` godtar `pass:<passord>`, `env:<variabel>`, `file:<fil>`, `stdin`. Samme formater gjelder `--key-pass`.
- `--min-sdk-version` defaulter til manifestets `minSdkVersion`; med `minSdk 23` signeres det med v1+v2 (v2 kreves fra API 24, v1 trengs for 23).
- Enhver endring av APK-en etter signering ugyldiggjør signaturen — derfor zipalign først, aldri `zip` etterpå.
- `apksigner verify --print-certs` viser sertifikatkjeden; `--min-sdk-version 23` gjør at verifiseringen matcher signeringsforutsetningene.

### 2.9 Hvilke verktøy ligger hvor

| Verktøy | Pakke | Sti |
|---|---|---|
| `aapt2`, `d8`, `zipalign`, `apksigner` (+ `aidl`, `renderscript`) | `build-tools;<ver>` | `<sdk>/build-tools/<ver>/` |
| `adb`, `fastboot` | `platform-tools` | `<sdk>/platform-tools/` |
| `sdkmanager`, `avdmanager`, `apkanalyzer` | `cmdline-tools;<ver>` | `<sdk>/cmdline-tools/latest/bin/` |
| `emulator`, qemu, `mksdcard`, `qemu-img` | `emulator` | `<sdk>/emulator/` |

Kilder: <https://developer.android.com/tools/releases/build-tools>, <https://developer.android.com/tools/releases/platform-tools> («primarily adb and fastboot»), <https://developer.android.com/studio/command-line/apkanalyzer>.

### 2.10 Inspeksjon av den ferdige APK-en

```bash
"$BT/aapt2" dump badging app/build/app-debug.apk
"$BT/aapt2" dump permissions app/build/app-debug.apk
"$BT/aapt2" dump xmltree app/build/app-debug.apk --file AndroidManifest.xml
"$ANDROID_HOME/cmdline-tools/latest/bin/apkanalyzer" manifest print app/build/app-debug.apk
"$ANDROID_HOME/cmdline-tools/latest/bin/apkanalyzer" apk file-size app/build/app-debug.apk
```

`aapt2 dump badging` er dokumentert som «Prints information extracted from the APK's manifest». Reell utdata fra APK-en bygget på denne maskinen:

```
package: name='no.safestart.kiosk' versionCode='1' versionName='0.1-test'
         platformBuildVersionName='14' platformBuildVersionCode='34'
         compileSdkVersion='34' compileSdkVersionCodename='14'
minSdkVersion:'23'
targetSdkVersion:'34'
application-label:'Safestart'
launchable-activity: name='no.safestart.kiosk.HomeActivity'
```

`apkanalyzer` ligger i **cmdline-tools**, ikke build-tools (<https://developer.android.com/studio/command-line/apkanalyzer>), med syntaks `apkanalyzer [global-options] subject verb [options] apk` og kommandoer som `apk summary`, `apk file-size`, `apk download-size`, `manifest print`, `manifest min-sdk`, `manifest target-sdk`, `manifest application-id`, `files list`.

---

## 3. Emulator og systemavbildninger på Apple Silicon med stram disk

### 3.1 Pakker

| Pakke | Revisjon | Nedlasting (dokumentert) | Installert (målt) |
|---|---|---|---|
| `emulator` | 37.4.1 | 420,6 MB | 1 324,5 MB (404 filer) |
| `emulator` (trimmet installasjon målt her) | 37.3.10 | — | **178 MiB** etter fjerning av Qt/WebEngine/Vulkan-assets |

De største enkeltfilene i stock-pakken: `lib64/qt/lib/libQt6WebEngineCoreAndroidEmu.6.5.3.dylib` 322,8 MB, `lib64/vulkan/libLLVM.dylib` 152,5 MB, `qemu/darwin-aarch64/qemu-system-aarch64` 60,3 MB, `qemu-system-armel` 60,0 MB, `qemu-system-aarch64-headless` 50,3 MB, `qemu-system-armel-headless` 50,0 MB, `netsimd` 25,0 MB.

### 3.2 arm64-v8a finnes fra API 21 — og hvor store er de?

Påstanden «arm64-avbildninger starter på et senere API-nivå» er **feil**. Googles sys-img-XML lister `arm64-v8a` fra og med API 21, og emulator-dokumentasjonen krever eksplisitt «arm64-v8a system images for Android 5.0 (API level 21) and higher» for ARM64-verter (<https://developer.android.com/studio/run/emulator-acceleration>).

Nedlastingsstørrelser for `system-images;android-<N>;default;arm64-v8a` (fra <https://dl.google.com/android/repository/sys-img/android/sys-img2-3.xml>):

| API | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 | 32 | 33 | 34 | 35 | 36 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MB | 211,4 | 219,1 | **253,8** | 305,9 | 308,4 | 330,0 | 332,2 | 426,8 | 498,0 | 548,4 | 635,5 | 643,3 | 672,3 | 705,1 | 769,1 | 810,7 |

Andre varianter (nedlasting, MB), samme API-utvalg:

| Variant | API 30 | API 33 | API 34 |
|---|---|---|---|
| `default` | 548,4 | 672,3 | 705,1 |
| `aosp_atd` | 449,7 | 559,3 | 599,3 |
| `google_atd` | 514,9 | 651,3 | 679,2 |
| `google_apis` | 1 244,3 | 1 761,6 | 1 610,4 |
| `google_apis_playstore` | 1 308,4 | 1 713,5 | 1 548,9 |

`aosp_atd` finnes for API 30–36 (`30:449,7 31:526,2 32:532,7 33:559,3 34:599,3 35:677,0 36:712,0`), `google_atd` for API 30–36 (`30:514,9 31:624,2 32:627,8 33:651,3 34:679,2 35:794,2 36:819,9`).

### 3.3 Den viktige nyansen: installert størrelse følger ikke nedlasting

`system.img` er en nesten full ext4-partisjon, så installert fotavtrykk er 3–6× nedlastingen. Målt på denne maskinen: `system-images;android-23;default;arm64-v8a` legger igjen

```
system.img   1 610 612 736 bytes (1,5 GiB), allokert = 1,5 GiB (ikke sparse)
kernel-ranchu 7,7 MB, kernel-qemu 6,3 MB, ramdisk.img 1,2 MB, NOTICE.txt 1,0 MB
```

— altså **1,5 GiB på disk for 253,8 MB nedlasting**. `userdata.img` følger ikke med i den utpakkede pakken; AVD-en lager sin egen `userdata-qemu.img` (her 64 MiB data-partisjon, 4,1 MiB allokert etter forsøk på oppstart).

**ATD-myten:** ATD-avbildningene er markedsført som små, men besparelsen ligger i *nedlasting*, ikke disk, fordi `system.img` har samme apparent size. `aosp_atd` (API 30) er 449,7 MB å laste ned mot 548,4 MB for `default` — ca. 100 MB — men begge legger igjen rundt 3,0 GiB utpakket. I tillegg, dokumentert i <https://developer.android.com/studio/test/gradle-managed-devices>: ATD-er «disable hardware rendering» og «Screenshot tests that depend on hardware rendering currently aren't supported when using ATDs» — dårlig match for en kiosk-UI som skal verifiseres med `screencap`.

### 3.4 Minste levedyktige arm64-avbildning

| Kandidat | Nedlasting | På disk | Vurdering |
|---|---|---|---|
| `system-images;android-23;default;arm64-v8a` | 253,8 MB | **1,5 GiB** | **anbefalt** — minste som tilfredsstiller `minSdk 23` |
| `system-images;android-24;default;arm64-v8a` | 305,9 MB | ~1,6 GiB (anslag) | neste steg opp |
| `system-images;android-30;aosp_atd;arm64-v8a` | 449,7 MB | ~3,0 GiB | bare hvis du vil ha API 30 og ikke trenger GPU-rendering |
| `system-images;android-30;default;arm64-v8a` | 548,4 MB | ~3,0 GiB | tryggest for `targetSdk 34`-testing |
| API 21/22 | 211,4 / 219,1 MB | ~1,4 GiB | **ugyldig** — under `minSdk 23`, APK-en installeres ikke |

API 23-avbildningen er det beste bytteforholdet: den er den minste som faktisk kan installere APK-en, den har `system.img` på 1,5 GiB, og den er gammel nok til at `minSdk 23`-adferd testes på ekte.

---

## 4. Headless emulator på Apple Silicon uten Android Studio

### 4.1 Virtualisering: HVF, ikke HAXM

På macOS bruker emulatoren **Hypervisor.Framework (HVF)**, som er innebygd i macOS. Dokumentert i <https://developer.android.com/studio/run/emulator-acceleration>: macOS-vert bruker HVF, og `emulator -accel-check` skriver ut en linje som

```
accel: 0 Hypervisor.Framework OS X Version 13.2
```

`accel: 0` = akselerasjon tilgjengelig (0 er suksess-koden). Apple Silicon står eksplisitt i listen over støttede CPU-er, og kravetabellen sier ARM64-vert → `arm64-v8a`-avbildning, API 21+. Ingen HAXM, ingen KVM, ingen ekstra kjørertid — HVF er grunnen til at `emulator -accel-check` er den første kommandoen du kjører.

### 4.2 Kommandoer

```bash
export SDK="$PWD/.androidsdk"
SM="$SDK/cmdline-tools/latest/bin/sdkmanager"
AVDM="$SDK/cmdline-tools/latest/bin/avdmanager"

"$SM" --sdk_root="$SDK" "emulator" "system-images;android-23;default;arm64-v8a"

echo no | "$AVDM" create avd \
  -n api23 \
  -k "system-images;android-23;default;arm64-v8a" \
  -d pixel_4 \
  --force

"$SDK/emulator/emulator" -accel-check

"$SDK/emulator/emulator" -avd api23 \
  -no-window -no-audio -no-boot-anim -no-snapshot \
  -gpu swiftshader &
```

`avdmanager`-syntaksen er dokumentert i <https://developer.android.com/tools/avdmanager>: `avdmanager create avd -n name -k "sdk_id" [-c {path|size}] [-f] [-p path]`, med eksempelet `avdmanager create avd -n test -k "system-images;android-25;google_apis;x86"`. Merk at dokumentasjonssiden nå markerer `avdmanager` som **deprecated** til fordel for Android CLI-kommandoen `android emulator [create|remove]`; `avdmanager` fungerer fortsatt og er det som er dokumentert med full flaggliste.

Vent på oppstart (headless har ingen vindu, alt går via adb):

```bash
ADB="$SDK/platform-tools/adb"
"$ADB" wait-for-device
until [ "$("$ADB" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ]; do sleep 2; done
"$ADB" shell getprop ro.build.version.sdk
```

### 4.3 `-gpu`-verdier: ikke bruk `swiftshader_indirect`

Dokumenterte verdier i <https://developer.android.com/studio/run/emulator-acceleration>: `auto`, `host`, `software`, `lavapipe`, `swiftshader`, `swangle`. Deprecated: `mesa`, `angle`, `angle_indirect`, `guest`, `swangle_indirect` og **`swiftshader_indirect` (deprecated i 36.4.9)**.

Eldre oppskrifter på nettet sier `-gpu swiftshader_indirect`. Med emulator 37.x er riktig verdi `-gpu swiftshader` (eller `-gpu software`), og `auto` er Googles anbefalte standard. `-no-window` betyr headless: ingen UI, all interaksjon via `adb`/konsoll.

Andre nyttige flagg fra <https://developer.android.com/studio/run/emulator-commandline>: `-no-snapshot` (slår av Quick Boot lasting+lagring — viktig for disk), `-noaudio`/`-no-audio`, `-no-boot-anim`, `-accel auto`, `-wipe-data`, `-partition-size <MB>` («system data partition size»), `-prop navn=verdi`.

### 4.4 Emulatoren nekter å starte på grunn av diskplass — målt her

Dette er den viktigste empiriske observasjonen i hele notatet. Med SDK installert og ca. 1,8 GB ledig disk stoppet emulatoren (37.3.10) med:

```
INFO  |      Error: Your device does not have enough disk space to run avd: `api23`
INFO  |   Checking: hasSufficientHwGpu
INFO  |      Ok: Hardware GPU requirements to run avd: `api23` are passed
INFO  |   Checking: hasSufficientSystem
INFO  |      Warning: System compatibility checks are disabled
FATAL | Your device does not have enough disk space to run avd: `api23`.
```

Strengen finnes i qemu-binæren (`qemu-system-aarch64-headless`), sammen med blant annet `could not initialize Quickboot RAM file. Please ensure enough disk space for the guest RAM size (%d MB) along with a safety factor.` og `Unable to save snapshot: Not enough disk space.` AVD-en var konfigurert med `disk.dataPartition.size=64M` og `disk.systemPartition.size=1610612736`, så kravet er ikke bare partisjonsstørrelsen — sjekken krever fri plass med sikkerhetsfaktor (forenlig med ca. 2× systemavbildningen ≈ 3,2 GB, som er mer enn de 1,8 GB som var ledige).

**Eksakt formel er ikke dokumentert — mål lokalt.** Praktisk tommelfingerregel fra målingen: regn **≥ 2× `system.img` + 1 GB** ledig disk før du starter en AVD, altså ca. **4 GB ledig** for API 23 og ca. **7 GB** for API 30. Start aldri en AVD på et volum som er >95 % fullt.

---

## 5. Kompatibilitet: `minSdkVersion 23` på moderne Android

### 5.1 Installerer APK-en normalt på API 30/33/34?

**Ja.** To forskjellige begreper blandes ofte sammen:

- `minSdkVersion` = laveste API appen kan installeres på. Din app: 23. Ingen moderne Android-versjon nekter dette.
- `targetSdkVersion` = hvilken adferdsprofil appen får. Android 14 innførte et **gulv for `targetSdkVersion`**, dokumentert i <https://developer.android.com/about/versions/14/behavior-changes-all> (avsnittet «Minimum installable target API level»): *«Starting with Android 14, apps with a targetSdkVersion lower than 23 can't be installed»*, med logcat-teksten `INSTALL_FAILED_DEPRECATED_SDK_VERSION: App package must target at least SDK version 23, but found 7`.

Med `targetSdk 34` er du langt over gulvet, og med `minSdk 23` er det ingen konflikt. APK-en bygget på denne maskinen (`minSdkVersion:'23'`, `targetSdkVersion:'34'`) er nettopp den kombinasjonen som fungerer overalt fra API 23 til API 36+.

### 5.2 Manifestkrav som faktisk kan velte appen

| Krav | Fra API | Konsekvens hvis det mangler |
|---|---|---|
| `android:exported="true"` på komponenter med `<intent-filter>` (når `targetSdk ≥ 31`) | 31 | **app kan ikke installeres**: «If an activity … uses intent filters and doesn't have an explicitly-declared value for android:exported, your app can't be installed on a device that runs Android 12 or higher» (<https://developer.android.com/about/versions/12/behavior-changes-12>) |
| `exported="true"` på launcher-aktiviteten (`CATEGORY_LAUNCHER`/`HOME`) | 31 | samme som over |
| `exported="true"` + `android:permission="android.permission.BIND_DEVICE_ADMIN"` på device-admin-receiveren | 21+ | `dpm set-device-owner` feiler; receiveren kan ikke aktiveres |
| `android:targetSdkVersion ≥ 23` | 34 (håndhevet) | `INSTALL_FAILED_DEPRECATED_SDK_VERSION` |
| `CATEGORY_HOME` + `CATEGORY_DEFAULT` for å være launcher | alle | appen kan ikke velges som hjem-app; `cmd package set-home-activity` feiler |
| Unik `android:launchMode="singleTask"` for kiosk | alle | flere instanser av kiosk-UI-en |

**Merk om `android:exported`:** attributtet er obligatorisk å deklarere eksplisitt fra API 31 når komponenten har intent-filter — også når den «naturlige» verdien ville vært `true`. Standardverdien er `true` for komponenter med minst ett intent-filter og `false` ellers, men fra 31 er det **eksplisitt deklarasjon** som kreves, ikke en implisitt standard.

### 5.3 Fungerende manifest for formålet

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="no.safestart.kiosk"
    android:versionCode="1"
    android:versionName="0.1-test">

    <uses-sdk android:minSdkVersion="23" android:targetSdkVersion="34" />

    <uses-permission android:name="android.permission.REORDER_TASKS" />

    <application
        android:label="Safestart"
        android:icon="@mipmap/ic_launcher"
        android:allowBackup="false"
        android:theme="@android:style/Theme.DeviceDefault.NoActionBar">

        <activity
            android:name=".HomeActivity"
            android:exported="true"
            android:launchMode="singleTask"
            android:excludeFromRecents="true"
            android:stateNotNeeded="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.HOME" />
                <category android:name="android.intent.category.DEFAULT" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <receiver
            android:name=".AdminReceiver"
            android:exported="true"
            android:permission="android.permission.BIND_DEVICE_ADMIN">
            <meta-data
                android:name="android.app.device_admin"
                android:resource="@xml/device_admin" />
            <intent-filter>
                <action android:name="android.app.action.DEVICE_ADMIN_ENABLED" />
            </intent-filter>
        </receiver>
    </application>
</manifest>
```

`res/xml/device_admin.xml`:

```xml
<device-admin xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-policies>
        <force-lock />
        <wipe-data />
        <disable-camera />
        <no-usb-debugging />
    </uses-policies>
</device-admin>
```

---

## 6. `adb`-kommandoer for installasjon og verifisering

Dokumentasjon: <https://developer.android.com/tools/adb> (installasjon, `exec-out screencap`) og <https://developer.android.com/tools/adb#dpm> (`dpm`).

```bash
ADB="$SDK/platform-tools/adb"

# 1. Enhet/emulator til stede
"$ADB" devices -l

# 2. Installer (erstatt eksisterende, gi alle runtime-tillatelser)
"$ADB" install -r -g app/build/app-debug.apk
#    -r = reinstall/erstatt, -g = gi alle runtime permissions, -t = tillat testOnly-APK

# 3. Start aktiviteten og vent til den er synlig
"$ADB" shell am start -W -n no.safestart.kiosk/.HomeActivity

# 4. Gjør appen til HOME (launcher/kiosk)
"$ADB" shell cmd package set-home-activity no.safestart.kiosk/.HomeActivity
#    dokumentert i PackageManagerShellCommand:
#    set-home-activity [--user USER_ID] TARGET-COMPONENT  (AOSP main)

# 5. Gjør appen til device owner (krever at enheten ikke har kontoer)
"$ADB" shell dpm set-device-owner no.safestart.kiosk/.AdminReceiver
#    syntaks: adb shell dpm set-device-owner [--user current] [--name navn] komponent

# 6. Logg: bare det relevante
"$ADB" logcat -c
"$ADB" logcat -s AndroidRuntime:E ActivityTaskManager:I ActivityManager:I PackageManager:I '*:S'
"$ADB" logcat --pid="$("$ADB" shell pidof -s no.safestart.kiosk | tr -d '\r')"

# 7. Skjermbilde (rådata, ikke shell-konvertering)
"$ADB" exec-out screencap -p > /tmp/shot.png
#    alternativ: adb shell screencap /sdcard/s.png && adb pull /sdcard/s.png

# 8. Verifiser at appen faktisk er i forgrunnen
"$ADB" shell dumpsys activity activities | grep -i mResumedActivity
"$ADB" shell dumpsys window | grep -i mCurrentFocus

# 9. Avinstaller / rens
"$ADB" uninstall no.safestart.kiosk
```

Merknader fra dokumentasjonen:
- `adb install` tar `-t` for test-APK-er og `install-multiple` for splittet APK.
- For skjermbilde anbefaler dokumentasjonen eksplisitt `exec-out` framfor `shell`, fordi `shell` kan ødelegge binærdataene med CRLF-konvertering: «use 'exec-out' instead of 'shell' to get raw data».
- `dpm`-kommandoen krever at receiveren er deklarert som device admin (meta-data `android.app.device_admin`) og at enheten ikke allerede har en device owner eller kontoer. `remove-active-admin` krever `android:testOnly="true"` på appen.
- `set-home-activity` er verifisert mot AOSP-kildekoden: <https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/services/core/java/com/android/server/pm/PackageManagerShellCommand.java> — `case "set-home-activity":` og bruksstrengen `set-home-activity [--user USER_ID] TARGET-COMPONENT`, som internt kaller `roleManager.addRoleHolderAsUser(RoleManager.ROLE_HOME, ...)`.

---

## 7. Diskbudsjett: hva du installerer, og hva du hopper over

### 7.1 Tre scenarier

| Scenario | Nedlasting | Installert | Plass til overs av 3,7 GB? |
|---|---|---|---|
| **A. Bygg + fysisk enhet** (4 SDK-pakker) | 311,8 MB | 516,0 MB | ✅ ja, ca. 3,2 GB igjen |
| **B. + emulator + API 23-avbildning** | 986,2 MB | ca. 1,7–2,7 GB | ⚠️ bare hvis emulatorens disk-sjekk passerer |
| **C. + emulator + API 30 `default`** | 1 280,8 MB | ca. 4,3–4,8 GB | ❌ nei |

Regnestykket for B, med målte tall:

```
build-tools;34.0.0        196,2 MB
platform-tools             40,2 MB
cmdline-tools;latest      180,5 MB
platforms;android-34       99,1 MB   (kan byttes mot android.jar alene: 25 MiB)
emulator                1 324,5 MB   stock 37.4.1
system-images;android-23;default;arm64-v8a  1 610,6 MB (system.img)
------------------------------------------
sum                      ca. 3,45 GB
```

Og toppforbruket under installasjon er høyere enn summen, fordi `sdkmanager` henter arkivet **før** det pakker ut:

```
sum installert (3,45 GB) + arkiv (ca. 0,99 GB) ≈ 4,4 GB
+ AVD-ens userdata/snapshot etter første oppstart  (0,1–1,5 GB)
+ emulatorens egen disk-sjekk krever ~2× system.img ledig
```

**Konklusjon: scenario B er ikke gjennomførbart på 3,7 GB ledig disk uten å frigjøre plass.** Det er ikke en teoretisk beregning — emulatoren nektet faktisk å starte (se 4.4), og på denne maskinen falt ledig disk til ca. 1,8 GB etter at SDK-verktøyene var installert.

### 7.2 Hva du kan trylle bort (og hva du ikke kan)

| Tiltak | Gevinst | Risiko |
|---|---|---|
| Dropp `platforms;android-34`, behold bare `android.jar` | ~74 MB | må hente jaret på nytt ved oppgradering |
| Slett `<sdk>/.temp` og `~/.android/cache` etter hver `sdkmanager`-kjøring | 100–700 MB | ingen |
| Installer én pakke om gangen | senker toppforbruket | ingen |
| `-no-snapshot` på alle emulator-kjøringer | hindrer 1–2 GB snapshot-vekst | ingen (langsommere oppstart) |
| Fjern `emulator/lib64/qt`, `emulator/lib64/vulkan`, `qemu/darwin-aarch64/qemu-system-armel*` | 300–500 MB (målt: stock 1 324,5 MB → 178 MiB trimmet) | **usikker** — emulatoren kan kreve Qt/Vulkan ved kjøring; kun for headless-oppsett, og du må verifisere med en faktisk oppstart |
| Konverter `system.img` til APFS-sparsefil (`dd conv=sparse`) | 1–1,5 GB hvis det er nullregioner | uoffisielt triks; her var `system.img` **ikke** sparse (allokert = apparent 1,5 GiB), så gevinsten er tvilsom |
| Velg API 23-avbildning framfor API 30 | ~1,5 GB | ingen for ditt `minSdk 23`-formål |
| Legg SDK + AVD på ekstern disk (`ANDROID_SDK_ROOT`, `avdmanager -p`) | hele behovet | krever ekstern disk |
| Bruk fysisk enhet i stedet for emulator | alt av emulator+avbildning (~3 GB) | krever en enhet |

### 7.3 Anbefalt plan for denne maskinen

1. **Nå:** bygg og installer på en fysisk Android-enhet via `adb` (scenario A, 516 MB). Bruk `adb install -r -g`, `am start -W`, `cmd package set-home-activity`, `dpm set-device-owner`, `exec-out screencap`. Alt i seksjon 6 virker uten emulator.
2. **Hvis emulator er et absolutt krav:** frigjør minst **4–5 GB** (helst 6–7 GB) først, eller flytt `.androidsdk` + `~/.android/avd` til ekstern disk. Start med `-no-window -no-snapshot -gpu swiftshader`, og sjekk `df -g` før hver oppstart.
3. **Ikke** installer `google_apis`/`google_apis_playstore`-avbildninger (1,2–1,8 GB nedlasting, 4+ GB på disk).

---

## 8. Minste oppsett — fra tom maskin til signert APK på kjørende emulator

Forutsetninger: macOS arm64, JDK 17+ (`javac`/`keytool`), `curl`, `unzip`, `zip`. Alle stier relative til prosjektroten; `ANDROID_HOME` settes til en mappe med plass.

```bash
# ---------- 0. Miljø ----------
export ANDROID_HOME="$PWD/.androidsdk"
export PATH="$ANDROID_HOME/platform-tools:$ANDROID_HOME/build-tools/34.0.0:$PATH"
mkdir -p "$ANDROID_HOME"

# ---------- 1. cmdline-tools (155,4 MB) ----------
mkdir -p "$ANDROID_HOME/cmdline-tools"
curl -fL -o /tmp/clt.zip \
  https://dl.google.com/android/repository/commandlinetools-mac_arm64-16111833_latest.zip
rm -rf /tmp/clt && mkdir -p /tmp/clt && unzip -q /tmp/clt.zip -d /tmp/clt
mv /tmp/clt/cmdline-tools "$ANDROID_HOME/cmdline-tools/latest"
SM="$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager"

# ---------- 2. Lisenser ----------
yes | "$SM" --sdk_root="$ANDROID_HOME" --licenses

# ---------- 3. Verktøy (156,4 MB: platform-tools 16,6 + platform 63,2 + build-tools 76,6) ----------
"$SM" --sdk_root="$ANDROID_HOME" "platform-tools"
"$SM" --sdk_root="$ANDROID_HOME" "platforms;android-34"
"$SM" --sdk_root="$ANDROID_HOME" "build-tools;34.0.0"
rm -rf "$ANDROID_HOME/.temp" "$HOME/.android/cache"

# ---------- 4. Debug-keystore ----------
mkdir -p "$HOME/.android"
keytool -genkeypair -v -keystore "$HOME/.android/debug.keystore" \
  -storetype PKCS12 -storepass android -keypass android \
  -alias androiddebugkey -keyalg RSA -keysize 2048 -validity 10000 \
  -dname "CN=Android Debug,O=Android,C=US"

# ---------- 5. Bygg ----------
BT="$ANDROID_HOME/build-tools/34.0.0"
AJ="$ANDROID_HOME/platforms/android-34/android.jar"
rm -rf app/build && mkdir -p app/build/{compiled,gen,classes,dex}

"$BT/aapt2" compile --dir app/res -o app/build/compiled

"$BT/aapt2" link -o app/build/base.apk -I "$AJ" \
  --manifest app/AndroidManifest.xml --java app/build/gen \
  --min-sdk-version 23 --target-sdk-version 34 --auto-add-overlay \
  $(find app/build/compiled -name '*.flat')

javac --release 11 -classpath "$AJ" -d app/build/classes \
  $(find app/src app/build/gen -name '*.java')

"$BT/d8" --lib "$AJ" --min-api 23 --output app/build/dex \
  $(find app/build/classes -name '*.class')

( cd app/build/dex && zip -q -j ../base.apk classes.dex )

"$BT/zipalign" -P 16 -f -v 4 app/build/base.apk app/build/aligned.apk

"$BT/apksigner" sign --ks "$HOME/.android/debug.keystore" \
  --ks-pass pass:android --ks-key-alias androiddebugkey \
  --min-sdk-version 23 --out app/build/app-debug.apk app/build/aligned.apk

"$BT/apksigner" verify --print-certs --min-sdk-version 23 app/build/app-debug.apk
"$BT/aapt2" dump badging app/build/app-debug.apk

# ---------- 6. Emulator (KREVER LEDIG DISK, se 4.4) ----------
"$SM" --sdk_root="$ANDROID_HOME" "emulator"                                  # 420,6 MB
"$SM" --sdk_root="$ANDROID_HOME" "system-images;android-23;default;arm64-v8a" # 253,8 MB
rm -rf "$ANDROID_HOME/.temp" "$HOME/.android/cache"

echo no | "$ANDROID_HOME/cmdline-tools/latest/bin/avdmanager" create avd \
  -n api23 -k "system-images;android-23;default;arm64-v8a" -d pixel_4 --force

"$ANDROID_HOME/emulator/emulator" -accel-check    # forvent "accel: 0 Hypervisor.Framework ..."
"$ANDROID_HOME/emulator/emulator" -avd api23 \
  -no-window -no-audio -no-boot-anim -no-snapshot -gpu swiftshader &

"$ANDROID_HOME/platform-tools/adb" wait-for-device
until [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ]; do sleep 2; done

# ---------- 7. Installer og verifiser ----------
adb install -r -g app/build/app-debug.apk
adb shell am start -W -n no.safestart.kiosk/.HomeActivity
adb shell cmd package set-home-activity no.safestart.kiosk/.HomeActivity
adb shell dpm set-device-owner no.safestart.kiosk/.AdminReceiver
adb logcat -c && adb logcat -s AndroidRuntime:E ActivityTaskManager:I ActivityManager:I '*:S' &
adb exec-out screencap -p > /tmp/shot.png
adb shell dumpsys activity activities | grep -i mResumedActivity
```

### Total nedlasting

| Scenario | Nedlasting | Installert på disk |
|---|---|---|
| A. Bygg + fysisk enhet (steg 1–5) | **311,8 MB** | **516,0 MB** |
| B. Bygg + emulator + API 23 (steg 1–7) | **986,4 MB** | ca. **1,7–2,7 GB** + AVD-vekst |
| C. Bygg + emulator + API 30 `default` | 1 280,8 MB | ca. **4,3–4,8 GB** |

**Anbefaling for denne maskinen:** kjør scenario A nå (516 MB — passer med god margin i 3,7 GB), og behandle emulatoren som en egen oppgave som krever at du først frigjør 4–5 GB eller flytter SDK/AVD til ekstern disk. Emulatoren selv nekter å starte uten nok ledig plass (FATAL-meldingen i 4.4), så dette er ikke bare et spørsmål om å «presse inn» noen megabyte.

---

## 9. Kilder (primærkilder)

- Googles SDK-repository (autoritativ pakke- og størrelsesliste): <https://dl.google.com/android/repository/repository2-3.xml>
- Systemavbildninger: <https://dl.google.com/android/repository/sys-img/android/sys-img2-3.xml> (og `sys-img/android/sys-img2-3.xml`, `sys-img/aosp_atd/sys-img2-3.xml`, `sys-img/google_atd/sys-img2-3.xml`, `sys-img/google_apis/sys-img2-3.xml`, `sys-img/google_apis_playstore/sys-img2-3.xml`)
- sdkmanager (oppsett, `latest`-layout, lisenser): <https://developer.android.com/tools/sdkmanager>
- aapt2 (`compile --dir`, `link`, `dump badging`): <https://developer.android.com/tools/aapt2>
- d8 (`--lib`, `--min-api`, `--output`, `--release`-fella): <https://developer.android.com/tools/d8>
- zipalign (`-P 16`, rekkefølge før apksigner): <https://developer.android.com/tools/zipalign>
- apksigner (`--ks-pass`, `--out`, `verify`): <https://developer.android.com/tools/apksigner>
- Debug-keystore og signering: <https://developer.android.com/studio/publish/app-signing>
- avdmanager (deprecated, syntaks): <https://developer.android.com/tools/avdmanager>
- Emulator kommandolinje (`-no-window`, `-no-snapshot`, `-gpu`): <https://developer.android.com/studio/run/emulator-commandline>
- Emulator-akselerasjon (HVF, arm64-krav, `-gpu`-verdier, deprecations): <https://developer.android.com/studio/run/emulator-acceleration>
- adb (`install`, `exec-out screencap`, `dpm`): <https://developer.android.com/tools/adb>
- Android 12 `android:exported`-kravet: <https://developer.android.com/about/versions/12/behavior-changes-12>
- Android 14 minimum `targetSdkVersion` (23): <https://developer.android.com/about/versions/14/behavior-changes-all>
- ATD-avbildninger (hardware rendering av): <https://developer.android.com/studio/test/gradle-managed-devices>
- apkanalyzer: <https://developer.android.com/studio/command-line/apkanalyzer>
- Byggeverktøy-releasenoter: <https://developer.android.com/tools/releases/build-tools>
- Plattformverktøy-releasenoter: <https://developer.android.com/tools/releases/platform-tools>
- AOSP `PackageManagerShellCommand` (`set-home-activity`): <https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/services/core/java/com/android/server/pm/PackageManagerShellCommand.java>

### Hva som er dokumentert vs. målt

| Påstand | Status |
|---|---|
| Nedlastingsstørrelser for alle SDK-pakker og systemavbildninger | **dokumentert** (repository-XML) |
| Installasjonsstørrelser (516 MB verktøy, 1,32 GB emulator, 1,5 GiB API 23-avbildning) | **målt** — Google dokumenterer dem ikke |
| `aapt2`/`d8`/`zipalign`/`apksigner`-flagg og rekkefølge | **dokumentert** |
| `javac --release 11` og klassefil-major 55 | **målt lokalt** med Temurin 25.0.1 |
| d8-grensen ved major 65 (Java 21) | **ikke dokumentert** per build-tools-versjon — empirisk; verifiser lokalt |
| Emulatorens diskplass-krav (FATAL-meldingen) | **observert lokalt**; eksakt formel ikke dokumentert |
| ATD sparer disk | **avkreftet** — sparer bare nedlasting; samme `system.img` |
| arm64-avbildninger finnes fra API 21 | **dokumentert** (emulator-akselerasjonssiden + sys-img-XML) |
