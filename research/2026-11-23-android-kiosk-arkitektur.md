# Android kiosk-arkitektur for Safestart

Mål: test-app `no.safestart.kiosk`, minSdk 23 (Android 6.0, samme minstekrav som Skyss), arm64-emulator, plain Java, ingen eksterne biblioteker.

Status: **alt i dette notatet er prøvd på emulator (Android 6.0, API 23, arm64) 23.11.2026.** Det som står som «verifisert» er sett i `adb`-output eller på skjermdump. Det som står som «ikke testet» er merket.

## Kort oppsummering

- En vanlig launcher-erstatning (app med `HOME`-kategori) gir barnet en egen hjem-skjerm, men **den kan alltid forlates** med HOME-knappen, og innstillinger/system-UI er åpne.
- **Lock Task mode** (pinning) låser skjermen til en liste apper. Uten Device Owner kan barnet i praksis låse seg ut med en snarvei; med Device Owner kan verken HOME, RECENTS eller statuslinje brukes.
- **Device Owner** er den eneste rollen som gir full kontroll uten root. Den settes én gang på en telefon uten konto og uten andre brukere: `adb shell dpm set-device-owner <pkg>/.AdminReceiver`.
- Verifisert på emulator: HOME, BACK og RECENTS holdt barnet inne i appen (`mLockTaskModeState=LOCKED`), Telefon-tilen åpnet den ekte dialeren (`com.android.dialer/.DialtactsActivity`), og tilbake-knappen fra dialeren førte tilbake til Safestart-hjemmet.
- Det vi **ikke** kan love: at telefonen er «100 % sikker». Device Owner kan fjernes med fabrikknullstilling, og enkelte system-apper (nødtelefon, varsler) oppfører seg ulikt fra produsent til produsent.

## 1. Lock Task mode

Lock Task (API 21+) er Androids egen «screen pinning»-mekanisme. Appen kaller `startLockTask()`, og systemet fjerner HOME, RECENTS og varselpanel så lenge modusen varer.

To nivåer:

| Nivå | Hvem kan starte | Hva barnet kan gjøre |
|---|---|---|
| `startLockTask()` uten Device Owner | appen selv | Holde seg i appen, men kan låse seg ut med «lås opp»-gesten hvis systemet tillater pinning |
| `startLockTask()` med Device Owner + `setLockTaskPackages()` | bare whitelistede pakker | Ingen utgang via HOME/RECENTS/statuslinje |

Verifisert i `adb shell dumpsys activity`:

```
mLockTaskModeState=LOCKED
mLockTaskModeTasks[TaskRecord{... A=no.safestart.kiosk ...}]
```

og `mResumedActivity` forble `no.safestart.kiosk/.HomeActivity` etter at jeg sendte `input keyevent 3` (HOME), `4` (BACK) og `187` (RECENTS). Det er denne testen som beviser at barnet faktisk ikke kommer ut.

Viktig detalj: lock task låser **oppgaven**, ikke bare appen. Derfor må alle apper barnet skal kunne bruke ligge i whitelisten (`setLockTaskPackages`), ellers blir de avvist når de startes fra kiosken.

## 2. Device Owner-provisionering på emulator via adb

Forutsetning: telefonen er **uten Google-konto**, har ingen andre brukere, og appen er ikke allerede admin.

```bash
adb install -r Safestart-test.apk
adb shell dpm set-device-owner no.safestart.kiosk/.AdminReceiver
adb shell am start -n no.safestart.kiosk/.HomeActivity
```

Verifisert output på API 23:

```
Success: Device owner set to package no.safestart.kiosk
Active admin set to component {no.safestart.kiosk/no.safestart.kiosk.AdminReceiver}
```

Merknader fra testingen:

- `adb shell dpm list-owners` og `dpm remove-active-admin` **finnes ikke** på API 23 (`Error: unknown command`). Vil man fjerne Device Owner på Android 6, må man fabrikknullstille.
- Device Owner blokkerer `pm uninstall` (`DELETE_FAILED_DEVICE_POLICY_MANAGER`), men **ikke** oppdatering: `adb install -r` virker helt fint så lenge APK-en er signert med samme nøkkel (verifisert 23.11.2026: `Success` på en telefon som allerede var Device Owner). Vil man bytte signatur eller avinstallere, må data-partisjonen nullstilles.
- På en ekte telefon gjøres det samme ved første oppstart via NFC/QR-provisjonering, eller manuelt med `dpm` fra en PC. For en UB er adb-versjonen helt grei til test.

## 3. DevicePolicyManager-kallene

Kallene appen faktisk bruker (`Kiosk.java`):

```java
DevicePolicyManager dpm = (DevicePolicyManager) getSystemService(DEVICE_POLICY_SERVICE);
ComponentName admin = new ComponentName(this, AdminReceiver.class);

dpm.setLockTaskPackages(admin, packages);   // hvilke pakker som får kjøre i lock task
dpm.setStatusBarDisabled(admin, true);      // fjerner varselpanel/snarveier
startLockTask();                            // gå inn i låst modus
stopLockTask();                             // kun fra foreldre-skjermen
dpm.isDeviceOwnerApp(getPackageName());     // sjekk før vi lover noe
```

`setLockTaskPackages` må få **pakkenavn**, ikke komponentnavn. Derfor slår appen opp hvilken pakke hver tile faktisk peker på (`Catalog.resolvePackage`) før listen settes — ellers ville f.eks. Kart blitt avvist selv om den er installert.

`setStatusBarDisabled(true)` krever Device Owner. Uten den rollen får barnet dratt ned varselpanelet og kan skru på wifi, flymodus og lignende.

## 4. Launcher-erstatning uten Device Owner

Uten Device Owner kan appen fortsatt registrere seg som hjem-skjerm:

```xml
<intent-filter>
  <action android:name="android.intent.action.MAIN" />
  <category android:name="android.intent.category.HOME" />
  <category android:name="android.intent.category.DEFAULT" />
  <category android:name="android.intent.category.LAUNCHER" />
</intent-filter>
```

Dette er verifisert å fungere: etter `am start` ble `HomeActivity` resumed, og den tegnet eget hjem med fliser.

Men uten Device Owner:

- HOME-knappen går tilbake til **systemets** hjem hvis brukeren velger det, og barnet kan bytte hjem-app i Innstillinger.
- Innstillinger, Play-butikk og varselpanel er åpne.
- Lock task kan avsluttes med systemgesten for pinning.

Konklusjon: launcher-erstatning alene er en **UI-løsning**, ikke en sikkerhetsløsning. Den er grei som demo og som «trygg førstemobil» for et barn som ikke prøver å omgå den, men den tåler ikke et nysgjerrig barn.

## 5. Telefoni

Kravet «telefonen må alltid kunne ringe» er oppfylt slik:

- Telefon-tilen er **alltid på** og kan ikke skrus av i foreldre-skjermen (`Prefs` tvinger `phone = true`).
- Tilen starter `ACTION_DIAL` med `tel:` — altså den vanlige dialeren, ikke en egen app. Verifisert: `mResumedActivity: com.android.dialer/.DialtactsActivity`.
- Dialeren ligger i lock task-whitelisten, ellers ville den blitt blokkert.
- Nødtelefon (112/113) er en del av systemets dialer og krever ikke SIM; den er upåvirket av kiosken.

Verifisert på emulator at HOME-knappen **ikke** tok barnet ut av dialeren, og at BACK fra dialeren førte tilbake til Safestart-hjemmet (to trykk, fordi dialeren lukker eget panel først).

Ikke testet: faktisk anrop (emulatoren har ingen SIM), og hvordan Samsung/Huawei/Xiaomi-dialere oppfører seg — de er egne apper med egne pakkenavn og må legges i whitelisten per merke.

## 6. Hva som ikke kan blokkeres uten Device Owner

| Ting | Uten Device Owner | Med Device Owner |
|---|---|---|
| Bytte hjem-app | nei | ja (`setLockTaskPackages` + lock task) |
| Varselpanel / hurtiginnstillinger | nei | ja (`setStatusBarDisabled`) |
| Legge til ny app fra Play | nei | ja (`setUserRestriction(DISALLOW_INSTALL_APPS)`) |
| Avinstallere apper | nei | ja |
| Fabrikknullstilling | nei | kan sperres, men ikke garantert på alle merker |
| Sette opp ny konto | nei | ja (`DISALLOW_ADD_USER`) |
| Skru av/på flymodus | nei | ja |

Det som **aldri** kan blokkeres helt: en telefon med fysisk tilgang kan alltid fabrikknullstilles (eller flashes), og da forsvinner både app og Device Owner. Kiosken er et hinder, ikke en kryptografisk garanti.

## 7. Minimal DeviceAdminReceiver

`AdminReceiver.java` er bare en markør — all logikk ligger i `Kiosk.java`:

```java
public class AdminReceiver extends DeviceAdminReceiver {
    @Override public void onEnabled(Context c, Intent i) { }
    @Override public void onDisabled(Context c, Intent i) { }
}
```

`res/xml/device_admin.xml` beskriver hvilke rettigheter vi ber om:

```xml
<device-admin>
  <uses-policies>
    <limit-password />
    <force-lock />
    <wipe-data />
  </uses-policies>
</device-admin>
```

Manifest:

```xml
<receiver android:name=".AdminReceiver"
    android:permission="android.permission.BIND_DEVICE_ADMIN"
    android:exported="true">
  <meta-data android:name="android.app.device_admin" android:resource="@xml/device_admin" />
  <intent-filter>
    <action android:name="android.app.action.DEVICE_ADMIN_ENABLED" />
  </intent-filter>
</receiver>
```

Merk: `android:exported="true"` er **påkrevd** for komponenter med intent-filter fra API 31, ellers nekter systemet å installere appen. Det gjelder også på API 23-telefoner når `targetSdkVersion` er 31+.

## 8. Eksisterende kiosk-apper

Det finnes ferdige løsninger, og de er verdt å nevne i presentasjonen fordi de viser at markedet finnes:

- **Fully Kiosk Browser** — mest brukt, web-fokusert, krever betalt lisens for låsefunksjoner.
- **Scalefusion / Hexnode / Miradore** — MDM-løsninger for bedrifter, overkill og dyrt for en UB.
- **Google Lock Task / «Pinned mode»** — innebygd i Android, gratis, men uten sentral styring.

Forskjellen vår: vi selger **ikke** en app. Vi selger en ferdig konfigurert telefon, med PIN-kode og en guide på ett ark. Det er tjenesten, ikke programvaren, som er produktet.

## 9. Utviklingsflyt som faktisk fungerer (testet)

Bygg uten Gradle, med build-tools 36.0.0:

```bash
bash app/build.sh          # aapt2 -> javac -> d8 -> zipalign -> apksigner
adb install app/Safestart-test.apk
adb shell dpm set-device-owner no.safestart.kiosk/.AdminReceiver
adb shell am start -n no.safestart.kiosk/.HomeActivity
adb exec-out screencap -p > proof/skjerm.png
```

Det som **faktisk** pleide å ødelegge oppdateringen var ikke Device Owner, men at keystore-filen lå inne i `build/` — som `build.sh` sletter hver gang. Da fikk hver build en ny signatur, og `adb install -r` svarte `INSTALL_FAILED_UPDATE_INCOMPATIBLE`. Etter at keystoren ble flyttet til `app/.signing/safestart.jks` oppdaterer `adb install -r` appen på plass, også når den er Device Owner.

Ren data-partisjon trengs bare når man vil begynne helt på nytt (eller har byttet signeringsnøkkel). På emulator:

```bash
adb emu kill
rm -f .avd/api23.avd/userdata-qemu.img*
.emulator/bin64/mkfs.ext4 -F -L userdata -b 4096 .avd/api23.avd/userdata-qemu.img 262144
# start emulatoren igjen
```

Kald oppstart tok ca. 24 sekunder på denne maskinen med 1 GB data-partisjon. Med 64 MB data-partisjon krasjet `system_server` i boot-løkke (`ClassNotFoundException: com.android.server.SystemServer`, `No original dex files found for dex location /system/framework/services.jar`) — det er ikke et bilde-problem, det er for lite `/data` til dexopt.

## Anbefalt teknisk løsning

1. **Device Owner + Lock Task** er kjernen. Uten Device Owner er ikke produktet en «trygg førstemobil», bare et pent hjem.
2. **Egen hjem-app** (`HomeActivity`) med fliser for Telefon, Meldinger, Kamera, Kart, Skyss. Telefon kan ikke slås av.
3. **PIN bak foreldre-knappen** (standard `1234`, lagres som saltet SHA-256, 5 feil forsøk gir 30 sekunders sperre). PIN-en er det eneste barnet ikke har.
4. **Whitelist bygges dynamisk** fra hvilke fliser som er på og hvilke pakker som faktisk finnes på telefonen.
5. **Foreldre-skjermen** viser status: «Device Owner: aktiv — telefonen er låst til Safestart». Det er den setningen som gjør at foreldrene forstår hva de har kjøpt.

## Hva vi ikke kan love

- **«100 % sikker»** — nei. Fabrikknullstilling fjerner alt, og vi kan ikke hindre det på alle merker.
- **«Fungerer på alle Android-telefoner»** — nei. Vi har testet API 23 arm64 på emulator. Ulike produsenter har egne dialere, kamera-apper og egne tolkninger av Device Owner.
- **«Skyss fungerer uten internett»** — nei. Skyss krever nett for søk, kjøp og visning, og barn under 15 kan ikke ha egen Skyss-profil.
- **«Vi har målt klimagevinst»** — nei. Vi har ingen målinger; vi vet bare at gjenbruk forlenger levetiden, og at det bare hjelper hvis det erstatter et nykjøp (EEA).
- **«Foreldrekontroll gir full beskyttelse»** — nei. Medietilsynet sier eksplisitt at foreldrekontroll ikke er full beskyttelse. Kiosken er et supplement, ikke en erstatning for samtale.
