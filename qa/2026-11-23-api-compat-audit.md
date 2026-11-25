# API-kompatibilitetsrevisjon — Safestart kiosk (Android 7.0 → 15)

**App:** `no.safestart.kiosk`, versionName `0.1-test`, minSdk 23, targetSdk 34, compileSdk 34
**Omfang:** API 24 (7.0), 26 (8.0), 28 (9), 29 (10), 30 (11), 31 (12), 33 (13), 34 (14), 35 (15)
**Metode:** kodelesing av alle kilder under `app/src/no/safestart/kiosk/` + `app/AndroidManifest.xml` + `app/build.sh`, krysset mot `aapt2 dump badging` på den bygde `app/Safestart-test.apk`, og mot plattformdokumentasjon for `DevicePolicyManager`, `PackageManager` og lock task. Ingen emulator, ingen adb, ingen endringer under `app/`.

**Forhold til `qa/2026-11-23-qa-utflukter.md`:** den revisjonen er API 23, kodetolkning, og er på flere punkter utdatert — `Kiosk.java` kaller nå `setStatusBarDisabled` (82), `setKeyguardDisabled` (87), `DISALLOW_SAFE_BOOT`/`DISALLOW_FACTORY_RESET` (94–95) og `addPersistentPreferredActivity` (102–106), og `PinDialog` teller nå hvert feil PIN-forsøk. De funnene gjentas ikke her. Denne revisjonen handler om hva som *fortsatt* bryter på nyere API-nivåer.

---

## 1. Kort oppsummering

- **Kritisk:** på Android 11+ (API 30) filtrerer package visibility `PackageManager.resolveActivity` (`Catalog.java:81`). `Kiosk.allowlist()` (`Kiosk.java:53–66`) får da `null` for telefon/SMS/kamera/kart, og `setLockTaskPackages` (`Kiosk.java:77`) sender bare `no.safestart.kiosk`. Resultat: i lock task er «Ring»-flisen *død* — barnet kan ikke ringe. Dette er appens kjernefunksjon, og den ryker på alle Android-versjoner fra 11 til 15.
- **Kritisk, andre ansikt:** samme filtrering gjør `Catalog.available()` (`Catalog.java:143`) usann, så alle eksterne fliser vises som «Ikke her» (`HomeActivity.java:323`) og grå, mens klikklytteren er registrert uansett (`HomeActivity.java:335`). Skjermen varsler altså riktig på 30+, men av helt feil grunn — og på 24–29 ser flisene like ut mens de virker.
- **Høy:** `Kiosk.lock()` kaller aldri `setLockTaskFeatures`. Fra API 28 er `LOCK_TASK_FEATURE_GLOBAL_ACTIONS` **på som standard**, så barnet får strømmenyen (Slå av / Start på nytt / Nødtelefon) i lock task på Android 9–15. «Nødtelefon» gir et tastatur utenfor allowlisten. På API 24–27 finnes ingen API for å skru dette av i det hele tatt.
- **Høy:** `setStatusBarDisabled` er dokumentert **uten virkning i lock task** — varselkurven holdes borte av lock task, ikke av kallet (`Kiosk.java:82`). Returverdien (boolean) ignoreres, så et avslag er usynlig. På API 34+ er kallet dessuten sperret bak `MANAGE_DEVICE_POLICY_STATUS_BAR`.
- **Middels:** `setKeyguardDisabled` returnerer `false` når det finnes PIN/mønster/passord, og etter reboot er det ingen boot-receiver som re-asserterer policyen. Kiosken kommer seg normalt opp igjen via persistent preferred HOME + persisterte DO-policyer, men det finnes konkrete hull (se F5/F6).
- **Lav, men må ryddes før targetSdk heves:** splash-skjerm på API 31+ (hver activity-start blinker appikonet), Force Dark på API 29+, `setSystemUiVisibility`-immersive er deprecated siden API 30, og edge-to-edge blir *påtvunget* først ved targetSdk 35 — ikke i dag.

---

## 2. Matrise per API-nivå

| API | Android | Hva som endrer seg for denne appen | Berørte filer | Alvor |
|----|---------|-----------------------------------|---------------|-------|
| **24** | 7.0 | `resizeableActivity` er **standard true** for targetSdk ≥ 24 → kiosken kan tvinges inn i split-screen/freeform, rutenettet (faste dp-mål) klippes. Lock task finnes, men uten `setLockTaskFeatures` kan strømmenyen ikke styres. Ingen bakgrunnsstart-restriksjoner ennå. | `AndroidManifest.xml:18–45`, `HomeActivity.java` (grid), `Kiosk.java:113–128` | Middels |
| **26** | 8.0 | Bakgrunnsgrenser for tjenester (app har ingen tjenester → uten virkning). Ukjent manifest-element ignoreres fortsatt. Lock task uendret. `startLockTask()` uten Device Owner gir PINNED-variant med bekreftelsesdialog. | `Kiosk.java:117–126` | Lav |
| **28** | 9 | **`setLockTaskFeatures` innføres, og `LOCK_TASK_FEATURE_GLOBAL_ACTIONS` er standard på** → strømmeny i lock task. `LOCK_TASK_FEATURE_KEYGUARD` finnes, men er av → keyguard undertrykkes i lock task. `setKeyguardDisabled(true)` avviser nå også en synlig keyguard. | `Kiosk.java:69–110` (mangler kall) | **Høy** |
| **29** | 10 | Force Dark kan invertere/fargeomlegge den lyse papir-looken (targetSdk ≥ 29, lys tema, ingen opt-out). Bakgrunnsstart av activities begrenses — appen starter aldri activities i bakgrunnen, så den er ikke berørt i dag. | `AndroidManifest.xml:15`, `Backdrop.java`, `Ui.java` | Lav |
| **30** | 11 | **Package visibility:** `resolveActivity`, `getPackageInfo`, `getLaunchIntentForPackage`, `queryIntentActivities` filtreres. → allowlisten kollapser, Skyss-flisen blir `null`, alle eksterne fliser vises «Ikke her». `setSystemUiVisibility`-flaggene depreceres (virker fortsatt). Auto-reset av `CALL_PHONE` starter. | `Catalog.java:81, 95, 110, 135`, `Kiosk.java:53–66, 77`, `HomeActivity.java:276, 323, 335, 398`, `ParentActivity.java:159–161` | **Kritisk** |
| **31** | 12 | `android:exported` **påkrevd** ved intent-filter (allerede satt: `HomeActivity` true, `AdminReceiver` true → OK). Splash-skjerm påtvunget for alle apper → blink ved hver activity-start. `PendingIntent` må være immutable — appen bruker ingen. `startLockTask` uendret. | `AndroidManifest.xml:20, 36, 42, 49`; `HomeActivity.java:485`, `ChessActivity` | Middels |
| **33** | 13 | `onBackPressed()` deprecert (virker; prediktiv tilbake er opt-in via `enableOnBackInvokedCallback`, som ikke er satt). Ingenting bryter i dag. `registerReceiver` må ha export-flagg *først* ved targetSdk 34 — appen registrerer ingen receivere. | `HomeActivity.java:117–120`, `ChessActivity.java:51` | Lav |
| **34** | 14 | Lock task-features og lock task-pakker **slås sammen til én policy**: feiler den ene, feiler begge → `setLockTaskPackages` + `setLockTaskFeatures` må settes sammen og verifiseres. `setStatusBarDisabled` krever `MANAGE_DEVICE_POLICY_STATUS_BAR`. `registerReceiver` krever eksplisitt export-flagg (ikke aktuelt). | `Kiosk.java:77, 82` | **Høy** |
| **35** | 15 | Edge-to-edge **påtvunget kun ved targetSdk 35** — appen er targetSdk 34 og beholder dagens oppførsel i dag. `SYSTEM_UI_FLAG_*` er legacy; ved targetSdk 35 må det enten migreres til `WindowInsetsController` eller opt-out via `android:windowOptOutEdgeToEdgeEnforcement` (krever compileSdk 35). | `Ui.java:40–48`, `android:theme` | Middels (ved targetSdk-heving) |

---

## 3. Funn

### F1 — Package visibility gjør lock task-allowlisten tom for alle eksterne apper (API 30+) · **kritisk**

**Sted:** `app/src/no/safestart/kiosk/Catalog.java:81`, `:95`, `:110`, `:135` → brukt i `app/src/no/safestart/kiosk/Kiosk.java:53–66` og `:77`

**Symptom på Android 11–15 (API 30+), Device Owner, lock task aktivt:**
- Barnet trykker «Ring». `Catalog.launch()` (`Catalog.java:148–161`) bygger `ACTION_DIAL`-intent og kaller `c.startActivity(i)` (`:155`). Ingenting åpnes. `startActivity` *kaster ikke* — systemet blokkerer starten fordi dialer-pakken ikke står i allowlisten som `Kiosk.lock()` pushet, viser et systemvarsel, og `launch()` returnerer `true` (appen tror det gikk bra, ingen Toast). Samme for SMS, kamera, kart og Skyss.
- Samtidig rendres alle eksterne fliser som «Ikke her» med grå chip (`HomeActivity.java:276` → `:295–297`, `:323`), fordi `Catalog.available()` er `resolvePackage(...) != null` og `resolveActivity` returnerer `null`.

**Årsak:** Appen er targetSdk 34. Fra Android 11 filtrerer systemet svar fra `PackageManager`-metoder som gir informasjon om *andre* apper: `queryIntentActivities()`, `resolveActivity()`, `getPackageInfo()`, `getLaunchIntentForPackage()`, `getInstalledApplications()`. Bare egen pakke, visse systempakker og apper som allerede har interagert med oss er automatisk synlige. Ingen dokumentert fritak for Device Owner/DPC. `intentFor()` er heller ikke påvirket — *starting* av activities via implicit intent er ikke begrenset av visibility, men den er begrenset av lock task-allowlisten, og allowlisten er nettopp det som ble feil.

Resultatkjede, eksakt:
1. `Kiosk.allowlist()` (`Kiosk.java:53`) starter med `pkgs.add(c.getPackageName())` (`:55`).
2. For hver `Catalog.Item` kalles `Catalog.resolvePackage()` (`:60`) → `pm.resolveActivity(i, MATCH_DEFAULT_ONLY)` (`Catalog.java:81`) → `null` på 30+.
3. `if (pkg != null)` (`:61–63`) hopper over → listen inneholder **kun** `no.safestart.kiosk` (CHESS-flisen er `internal` og short-circuiter i `Catalog.java:73`, så den virker).
4. `d.setLockTaskPackages(admin(c), pkgs.toArray(...))` (`Kiosk.java:77`) gir en allowlist på én pakke.
5. Lock task blokkerer dermed hver `startActivity` mot dialer/SMS/kamera/kart/Skyss.

**Rettelse — `app/AndroidManifest.xml`, legg `<queries>` som søsken av `<application>` (etter linje 10):**

```xml
<queries>
    <!-- Telefon / ACTION_DIAL -->
    <intent>
        <action android:name="android.intent.action.DIAL" />
        <data android:scheme="tel" />
    </intent>
    <!-- SMS: APP_MESSAGING-kategorien ... -->
    <intent>
        <action android:name="android.intent.action.MAIN" />
        <category android:name="android.intent.category.APP_MESSAGING" />
    </intent>
    <!-- ... og sms:-skjemaet som fallback -->
    <intent>
        <action android:name="android.intent.action.VIEW" />
        <data android:scheme="sms" />
    </intent>
    <!-- Kamera -->
    <intent>
        <action android:name="android.media.action.STILL_IMAGE_CAMERA" />
    </intent>
    <!-- Kart -->
    <intent>
        <action android:name="android.intent.action.VIEW" />
        <data android:scheme="geo" />
    </intent>
    <!-- Skyss: alle kandidatene må listes eksplisitt (se F2) -->
    <package android:name="no.skyss.billett" />
    <package android:name="no.skyss.reise" />
    <package android:name="no.skyss" />
    <package android:name="no.skyss.tickets" />
</queries>
```

- `<queries>` krever compileSdk 30+ (vi har 34) og **ignoreres stille av API 23–29**, så det er trygt med minSdk 23.
- Pragmatisk tillegg for denne appen: den distribueres med `adb install` / MDM, ikke Play. Da kan `QUERY_ALL_PACKAGES` brukes i tillegg som belte-og-seler:
  ```xml
  <uses-permission android:name="android.permission.QUERY_ALL_PACKAGES" />
  ```
  (Play krever godkjenning for denne — ikke aktuelt ved sideload, men må dokumenteres hvis appen en gang skal på Play.)
- Etter manifestendringen bør `Kiosk.lock()` logge `pkgs.size()`, slik at en tom allowlist er synlig i logcat i stedet for å feile stille.

---

### F2 — Skyss-flisen blir permanent `null` på API 30+ (visibility + `getPackageInfo`) · **kritisk**

**Sted:** `Catalog.java:133–140` (`isInstalled` → `getPackageInfo`), brukt av `skyssPackage()` `:119–131`, som brukes av `intentFor()` `:107–115`; `getLaunchIntentForPackage` på `:110`.

**Symptom:** Skyss-flisen har ingen intent i det hele tatt på Android 11+. `Catalog.available()` = false, `Catalog.launch()` returnerer `false` umiddelbart (`intentFor` er `null`) → Toast «… er ikke tilgjengelig her» (`HomeActivity.java:335–340`). Også den manuelle overstyringen i foreldre-innstillingene (`Prefs.skyssPackage()`, satt i `ParentActivity.java` rundt `:222`) blir filtrert bort, fordi `skyssPackage()` først sjekker `isInstalled(c, custom)` (`Catalog.java:121`).

**Årsak:** `getPackageInfo(pkg, 0)` kaster `NameNotFoundException` for pakker som ikke er synlige, og koden fanger `Exception` → `return false` (`Catalog.java:134–139`). Dette er *korrekt kode* som blir feil av plattformen: feilen er ikke «ikke installert», den er «ikke synlig». Samme gjelder `getLaunchIntentForPackage` (`:110`), som også returnerer `null` for usynlige pakker.

**Rettelse:** `<package>`-oppføringene i F1 dekker alle fire kandidatene. I tillegg bør `isInstalled` skille «ikke synlig» fra «ikke installert» slik at feilen ikke er usynlig:

```java
static boolean isInstalled(Context c, String pkg) {
    try {
        c.getPackageManager().getPackageInfo(pkg, 0);
        return true;
    } catch (PackageManager.NameNotFoundException e) {
        // API 30+: samme unntak betyr «ikke synlig» med mindre pakken er i <queries>
        Log.i("Safestart", "pakke ikke synlig/installert: " + pkg);
        return false;
    }
}
```
Hvis Skyss-pakkenavnet er kjent for utrulleringen, er den robuste varianten å alltid sende `setPackage(pkg)` + `ACTION_MAIN` (fallbacken på `Catalog.java:112–114`) og la `startActivity` avgjøre — den virker uavhengig av visibility, men krever at pakken er i allowlisten (altså `<queries>`/`QUERY_ALL_PACKAGES`).

---

### F3 — Strømmeny («global actions») er aktiv i lock task fra API 28 · **høy**

**Sted:** `Kiosk.java:69–110` (`lock()`), som aldri kaller `setLockTaskFeatures`.

**Symptom — hva barnet faktisk kan gjøre i lock task i dag:**

| API | Android | Strømmeny | Varselkurv | Oversikt/Recents | Home | Tillegg |
|-----|---------|-----------|------------|------------------|------|---------|
| 24–27 | 7.0–8.1 | **Alltid tilgjengelig** (kan ikke skrus av; API-et finnes ikke) | Blokkert av lock task | Blokkert | Blokkert | Langt trykk på av/på → Slå av / Start på nytt. Barnet kan slå av telefonen. |
| 28–35 | 9–15 | **Tilgjengelig som standard** (`LOCK_TASK_FEATURE_GLOBAL_ACTIONS`) → Slå av, Start på nytt, **Nødtelefon**, Skjermbilde/Lockdown på enkelte | Blokkert (`LOCK_TASK_FEATURE_NOTIFICATIONS` ikke satt) | Blokkert (`LOCK_TASK_FEATURE_OVERVIEW` ikke satt) | Blokkert (`LOCK_TASK_FEATURE_HOME` ikke satt) | «Nødtelefon» åpner nødtastaturet, som ligger utenfor allowlisten — et reelt avbrekk fra kiosken. |

**Årsak:** Fra API 28 er `setLockTaskFeatures(ComponentName, int)` den eneste måten å styre disse systemflatene. Dokumentasjonen er entydig: «Any system features not included in flags are implicitly disabled. **By default, only `LOCK_TASK_FEATURE_GLOBAL_ACTIONS` is enabled; all other features are disabled.**» Appen kaller metoden aldri, så standarden gjelder — det er derfor strømmenyen er der, mens de andre flatene er borte.

**Ekstra for API 34:** lock task-features og lock task-pakker er fra Android 14 **slått sammen til én policy** — feiler den ene, feiler begge. Kallene i `Kiosk.lock()` må derfor settes i samme `try`/rekkefølge og resultatet verifiseres, ellers kan en feil i `setLockTaskFeatures` ta med seg allowlisten.

**Rettelse — i `Kiosk.lock()` etter `setLockTaskPackages` (`Kiosk.java:77–80`):**

```java
// API 28+: skru av strømmeny/global actions. Før 28 finnes ingen mulighet.
if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
    try {
        d.setLockTaskFeatures(admin(c), DevicePolicyManager.LOCK_TASK_FEATURE_NONE);
    } catch (Throwable t) {
        Log.w(TAG, "setLockTaskFeatures failed", t);
    }
}
```
`LOCK_TASK_FEATURE_NONE` (verdi 0) slår av alt: global actions, home, overview, notifications, system info, keyguard. Husk å importere `Build` (per i dag brukes `android.os.Build` bare inline i `ParentActivity.java:159`).

For API 24–27 må gapet håndteres utenfor koden: enten akseptere at barnet kan slå av telefonen, eller sette minimum supported API til 28 for kiosk-drift. Dette bør stå i utrulleringsdokumentasjonen.

---

### F4 — `setStatusBarDisabled` er uten virkning i lock task, og returverdien ignoreres · **høy**

**Sted:** `Kiosk.java:82` (`d.setStatusBarDisabled(admin(c), true)` i `lock()`), `:141` (`setStatusBarDisabled(admin(a), false)` i `unlock()`).

**Symptom:** Ingen synlig feil — men kallet gir ikke den beskyttelsen kommentaren antyder. Varselkurven holdes borte *fordi lock task er aktivt*, ikke fordi statusbaren er deaktivert. Konsekvensene er konkrete:
- På en enhet som **ikke** er Device Owner (`isDeviceOwner()` false, `Kiosk.java:70–73`) eller der `startLockTask()` feiler, er statusbaren helt vanlig — barnet kan dra ned kurven og starte hvilken som helst app.
- Vinduet fra `HomeActivity` vises til lock task faktisk er aktivt (kaldstart, reboot, etter `stopLockTask()` i `unlock()`).
- På låseskjermen har kallet dokumentert ingen virkning i det hele tatt.

**Årsak:** Plattformdokumentasjonen for `setStatusBarDisabled` sier rett ut: «**This method has no effect for LockTask mode.** The behavior of the status bar in LockTask mode can be configured with `setLockTaskFeatures(...)`. Calls to this method when the device is in LockTask mode will be registered, but will only take effect when the device leaves LockTask mode.» I tillegg: «This policy does not have any effect while on the lock screen.» Fra API 34 er metoden sperret bak `android.permission.MANAGE_DEVICE_POLICY_STATUS_BAR` (auto-innvilget til DO/DPC, men kallet kan returnere `false`).

**Rettelse:**
1. Bruk `setLockTaskFeatures(admin, LOCK_TASK_FEATURE_NONE)` (F3) som den *faktiske* mekanismen for å holde kurven borte i kiosk-modus.
2. Behold `setStatusBarDisabled` for vinduet utenfor lock task, men **sjekk returverdien** og logg:
   ```java
   try {
       boolean ok = d.setStatusBarDisabled(admin(c), true);
       if (!ok) Log.w(TAG, "setStatusBarDisabled avslått (policy ikke anvendt)");
   } catch (Throwable t) { ... }
   ```
3. På API 34+: deklarer permissions eksplisitt i manifestet for tydelighet (og for enheter der DO-innvilgelse er forsinket):
   ```xml
   <uses-permission android:name="android.permission.MANAGE_DEVICE_POLICY_STATUS_BAR" />
   ```
   (Krever compileSdk 34 — OK. På API < 34 ignoreres ukjent permission.)
4. Vær klar over OEM-avvik: flere produsenter (Samsung, Xiaomi) har historisk hatt egne regler for statusbar i kiosk-modus. **Må verifiseres empirisk per enhetsmodell.**

---

### F5 — `setKeyguardDisabled` gir `false` når skjermlås er satt; keyguard kommer tilbake · **middels**

**Sted:** `Kiosk.java:87` (returverdi ignorert), `:84–90` (kun `Throwable` logges).

**Symptom:** Hvis telefonen har PIN/mønster/passord når Safestart blir Device Owner, returnerer `setKeyguardDisabled(true)` `false` og gjør ingenting. Etter reboot (eller når skjermen har vært av) møter barnet en låseskjerm — ikke kiosken. Fra låseskjermen er nødtelefon tilgjengelig.

**Årsak:** Dokumentert: «Setting the keyguard to disabled has the same effect as choosing 'None' as the screen lock type. However, **this call has no effect if a password, pin or pattern is currently set. If a password, pin or pattern is set after the keyguard was disabled, the keyguard stops being disabled.** As of API 28 this call also dismisses the keyguard if it is currently shown.» I lock task (API 28+) undertrykkes keyguard uansett fordi `LOCK_TASK_FEATURE_KEYGUARD` ikke er satt — men utenfor lock task (oppstart, før `Kiosk.enter`) gjelder den.

**Rettelse:**
```java
try {
    boolean ok = d.setKeyguardDisabled(admin(c), true);
    if (!ok) {
        // Det finnes skjermlås. DPC kan ikke slette enheten direkte;
        // fjern kravet og be forelderen fjerne skjermlåsen.
        d.setPasswordQuality(admin(c), DevicePolicyManager.PASSWORD_QUALITY_UNSPECIFIED);
        Log.w(TAG, "keyguard ikke deaktivert: skjermlås er satt — må fjernes");
    }
} catch (Throwable t) { ... }
```
Og i `ParentActivity`: vis statusen («Skjermlås er aktiv — kiosken kan ikke starte automatisk etter omstart»), siden dette er en miljøfeil forelderen må rette, ikke en kodefeil appen kan løse alene.

---

### F6 — Ingen boot-receiver: hva som skjer ved omstart per API-nivå · **middels**

**Sted:** `AdminReceiver.java:1–19` (kun `onEnabled`/`onDisabled`, ingen `onReceive`), `AndroidManifest.xml:47–57` (ingen `BOOT_COMPLETED`-intent-filter, ingen `RECEIVE_BOOT_COMPLETED`-permission).

**Hva som faktisk skjer ved reboot, per nivå:**

| API | Oppførsel i dag | Hull |
|-----|-----------------|------|
| 24–35 | Device Owner-status, `setLockTaskPackages`, `setStatusBarDisabled`, `setKeyguardDisabled`, user restrictions og `addPersistentPreferredActivity` er **persistert DO-policy** og overlever omstart. Systemet starter HOME-appen (Safestart, pga. persistent preferred activity) → `HomeActivity.onResume` (`:101–106`) kaller `Kiosk.enter()` → `Kiosk.lock()` re-asserterer alt og `startLockTask()`. Kiosken kommer altså tilbake **uten** boot-receiver. | (a) Har enheten skjermlås (F5), stopper den på låseskjermen. (b) Er direct-boot aktivert og brukeren ikke har låst opp, kan appen ikke kjøre i det hele tatt (ikke `directBootAware`). (c) Mistet lock task (krasj/system) uten at HOME rekjøres, blir enheten stående ulåst. |

**Årsak/plattformdetaljer det må tas høyde for hvis receiver legges til:**
- `BOOT_COMPLETED` er på API 26+ **unntatt** fra restriksjonene på implicit broadcasts — den leveres fortsatt via manifest.
- Men `LOCKED_BOOT_COMPLETED` (direct boot) krever `android:directBootAware="true"` på receiveren, og all data den leser må ligge i device-protected storage (`SharedPreferences` i `Prefs.java` ligger i credential-encrypted storage og er **utilgjengelig** før opplåsing).
- Fra API 31+ **må** manifest-receivere med intent-filter ha `android:exported` satt (denne appen har det allerede på `AdminReceiver`).
- Registrering av receiver i kjøretid må fra targetSdk 34 oppgi `RECEIVER_NOT_EXPORTED`/`RECEIVER_EXPORTED` — appen registrerer ingen i dag, så det er ikke et problem nå, men det er fellen hvis noen legger til en.
- **Ikke** start activities fra receiveren: fra API 29 er bakgrunnsstart begrenset, og det finnes **ingen dokumentert Device Owner-fritak** for «background activity starts». Systemet sørger for at HOME startes; receiveren skal bare kalle DPM-metoder. (Fritaket for DO/DPC bør likevel **verifiseres empirisk** på 10–15, siden OEM-bygg varierer.)
- Android 12+ app standby-bøtte: apper i «restricted»-bøtte får ikke `BOOT_COMPLETED`. En kiosk-enhet bruker appen konstant, men en DO-eid app kan i prinsippet bøttes på enkelte bygg.

**Rettelse:**
```xml
<uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
...
<receiver
    android:name=".BootReceiver"
    android:exported="true"
    android:directBootAware="true">
    <intent-filter>
        <action android:name="android.intent.action.BOOT_COMPLETED" />
        <action android:name="android.intent.action.LOCKED_BOOT_COMPLETED" />
    </intent-filter>
</receiver>
```
`BootReceiver.onReceive`: kall `Kiosk.lock(context, new Prefs(context))` (bare DPM-kall, ingen `startActivity`). `directBootAware` kan sløyfes hvis direct boot ikke er i bruk — da holder `BOOT_COMPLETED` alene.

---

### F7 — Splash-skjerm på hver activity-start fra API 31 · **middels**

**Sted:** `AndroidManifest.xml:15` (`android:theme="@android:style/Theme.Material.Light.NoActionBar"`); ingen `app/res/values/styles.xml` eller `values-v31/` finnes; nye activities startes i `HomeActivity.java:485` (ParentActivity) og `Catalog.java:155` (ChessActivity, eksterne apper).

**Symptom:** På Android 12+ viser systemet en splash (appikon på bakgrunn fra temaet) *hver gang* en activity startes — også ParentActivity og ChessActivity. I en kiosk oppleves det som et blink/«app-ikon midt på skjermen» hver gang forelderen åpner PIN-panelet, og barnet ser det samme ved bytte til og fra sjakk. På API 24–30 finnes ingen splash (bare `windowBackground`), så opplevelsen er ulik per Android-versjon.

**Årsak:** Android 12 (API 31) innførte `SplashScreen`-API-et og pålegger splash for alle apper. Uten `windowSplashScreenBackground`/`windowSplashScreenAnimatedIcon` brukes temaets `windowBackground` + appikon. Appen har bare et PNG-ikon i `mipmap-xxhdpi` (ingen adaptivt ikon i `mipmap-anydpi-v26`), så ikonet vises beskåret i en sirkel på API 26+.

**Rettelse:** Legg til `app/res/values/styles.xml`:
```xml
<style name="Safestart" parent="@android:style/Theme.Material.Light.NoActionBar">
    <item name="android:windowBackground">@android:color/white</item>
</style>
```
og `app/res/values-v31/styles.xml` (samme stilnavn, overstyrer bare splash-attributtene):
```xml
<style name="Safestart" parent="@android:style/Theme.Material.Light.NoActionBar">
    <item name="android:windowBackground">@android:color/white</item>
    <item name="android:windowSplashScreenBackground">@android:color/white</item>
    <item name="android:windowSplashScreenAnimatedIcon">@mipmap/ic_launcher</item>
</style>
```
Deretter `android:theme="@style/Safestart"` i manifestet (linje 15). Merk: `windowSplashScreenBackground`/`windowSplashScreenAnimatedIcon` er plattformattributter fra API 31 og hører hjemme i `values-v31`. `postSplashScreenTheme` er **ikke** et plattformattributt — det er AndroidX-biblioteket `androidx.core:core-splashscreen` sin egen attr, og det biblioteket finnes ikke i dette Gradle-frie bygget. Med ren plattformtema trengs det ikke: splash-attributtene leses fra apptemaet, og etter splash går appen rett over i samme tema.

---

### F8 — Multi-vindu er på som standard (API 24+) og kan klippe rutenettet · **middels**

**Sted:** `AndroidManifest.xml:18–45` — ingen `android:resizeableActivity`, ingen `android:screenOrientation`; `configChanges="orientation|screenSize|keyboardHidden"` (`:25`, `:44`).

**Symptom:** Fra API 24 er activities resizeable som standard når targetSdk ≥ 24. Kiosken kan havne i split-screen/freeform (OEM desktop-modus på Android 10+, eller hvis en annen app ber om multi-window). `HomeActivity` bygger rutenettet med faste dp-mål i `onResume`/`rebuildGrid`; ved en kraftig høydeendring klippes nederste rad. På Android 12+ blir ikke-resizeable activities letterboxet i stedet.

**Årsak:** `android:resizeableActivity` (API 24+) default er `true` for targetSdk ≥ 24. Lock task blokkerer riktignok split-screen så lenge kiosk-modus er aktiv, men ikke i vinduet før `startLockTask()` er aktivt, og ikke på enheter der kiosk-modus feiler.

**Rettelse:** `android:resizeableActivity="false"` på alle tre activities (`HomeActivity`, `ParentActivity`, `ChessActivity`). Attributtet ignoreres på API < 24, altså trygt. Legg gjerne også `android:screenOrientation="portrait"` hvis produktet er låst til portrett (vurder om HOME-rollen respekterer det — **må verifiseres empirisk**; enkelte launcher-implementasjoner ignorerer `resizeableActivity=false`).

---

### F9 — Immersive-flagg er deprecated (API 30) og edge-to-edge tvinges først ved targetSdk 35 · **middels**

**Sted:** `Ui.java:40–48` — `d.setSystemUiVisibility(SYSTEM_UI_FLAG_IMMERSIVE_STICKY | FULLSCREEN | HIDE_NAVIGATION | LAYOUT_*)`.

**Symptom:** I dag (targetSdk 34): fungerer på 24–35, men flaggene er deprecated siden API 30 og går via en legacy-kompatbanen. Ved heving til targetSdk 35 blir edge-to-edge **påtvunget** på Android 15: `LAYOUT_*`-flaggene er irrelevante, systemradene tegnes oppå innholdet, og kiosken kan få innhold under navigasjonslinjen (rutenettets nederste rad under gestelinjen). Det er *ikke* et brudd i dag.

**Årsak:** Android 15 (API 35) håndhever edge-to-edge for targetSdk 35; opt-out er `android:windowOptOutEdgeToEdgeEnforcement` (ApiSince 35, krever compileSdk 35). Fra API 30 er riktig API `WindowInsetsController` / `Window.setDecorFitsSystemWindows(false)`.

**Rettelse (nå):** Ingen endring nødvendig, men legg inn en kommentar i `Ui.java` om at immersive-banen er bundet til targetSdk 34.
**Rettelse (ved targetSdk 35):** Enten
```java
if (Build.VERSION.SDK_INT >= 30) {
    WindowInsetsController ctl = w.getInsetsController();
    ctl.hide(WindowInsets.Type.systemBars());
    ctl.setSystemBarsBehavior(WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
} else {
    // eksisterende setSystemUiVisibility
}
```
eller (raskeste vei) `values-v35/styles.xml` med `<item name="android:windowOptOutEdgeToEdgeEnforcement">true</item>` og compileSdk hevet til 35.

---

### F10 — `CALL_PHONE` gis fra ParentActivity; auto-reset på API 30+ kan drepe «Ring forelder» · **middels**

**Sted:** `ParentActivity.java:159–161` (`if (SDK_INT >= 23) requestPermissions(... CALL_PHONE ...)`), brukt av `HomeActivity.java:398` (`ACTION_CALL` når tillatelsen finnes, ellers `ACTION_DIAL`).

**Symptom:** Fungerer i dag. Men på Android 11+ (API 30) finnes automatisk tilbaketrekking av kjøretidstillatelser for apper som ikke brukes, og «kun denne gangen»-valg. Mister appen `CALL_PHONE`, faller `HomeActivity` tilbake til `ACTION_DIAL` — som i lock task krever at dialer-pakken er i allowlisten. Kombinert med F1 betyr det at forelderknappen også dør på 30+.

**Årsak:** API 30 introduserte permission auto-reset; API 23-guarden er en no-op siden minSdk allerede er 23 (ufarlig, men misvisende som «versjonshåndtering» — det er den eneste `Build.VERSION`-sjekken i hele kodebasen).

**Rettelse:** La Device Owner innvilge tillatelsen permanent i `Kiosk.lock()` (API 23+):
```java
try {
    d.setPermissionGrantState(admin(c), c.getPackageName(),
            android.Manifest.permission.CALL_PHONE,
            DevicePolicyManager.PERMISSION_GRANT_STATE_GRANTED);
} catch (Throwable t) { Log.w(TAG, "setPermissionGrantState failed", t); }
```
og fjern `requestPermissions`-kallet fra `ParentActivity` (eller behold det som fallback når `!Kiosk.isDeviceOwner(this)`). Vurder samtidig å bruke `ACTION_DIAL` som primær og bare `ACTION_CALL` når tillatelsen faktisk er gitt — det er allerede slik koden er bygget.

---

### F11 — Force Dark kan ødelegge papir-looken på Android 10+ · **lav**

**Sted:** `AndroidManifest.xml:15` (lyst framework-tema), farger satt i kode (`Ui.java`, `Backdrop.java`).

**Symptom:** Med systemets mørke tema på Android 10+ kan systemet automatisk mørklegge/invertere visninger i apper som bruker lyst tema og ikke har opt-out. Kioskens faste palett (`Backdrop`-boblene, `Ui.pill/chip`) kan få feil kontrast — teksten i flisene kan bli uleselig.

**Årsak:** Force Dark (API 29) pålegges apper med lyst tema og targetSdk ≥ 29 uten `android:forceDarkAllowed="false"`.

**Rettelse:** `res/values-v29/styles.xml`:
```xml
<style name="Safestart" parent="@android:style/Theme.Material.Light.NoActionBar">
    <item name="android:forceDarkAllowed">false</item>
</style>
```
(Bygges sammen med F7s styles.xml.) Alternativt tving lyst tema med `android:forceDarkAllowed="false"` i grunnstilen og `AppCompatDelegate`-fri tilnærming — prosjektet bruker ikke AppCompat, så temaattributtet er riktig.

---

### F12 — Prediktiv tilbake (API 33/34): ingen endring nå, men `onBackPressed` må migreres ved opt-in · **lav**

**Sted:** `HomeActivity.java:117–120` (tom `onBackPressed()` = kiosken kan ikke lukkes med tilbake), `ChessActivity.java:51–52` (`finish()`).

**Symptom:** Ingen. `android:enableOnBackInvokedCallback` er ikke satt, og prediktiv tilbake er opt-in for targetSdk 33/34 → arvbanen er legacy og `onBackPressed()` virker.

**Risiko:** Setter noen `enableOnBackInvokedCallback="true"` (eller hever targetSdk til 36 der standarden snur), slutter `onBackPressed()` å bli kalt — da mister `HomeActivity` sin «kan ikke lukkes»-garanti, som er en sikkerhetsmekanisme i kiosken.

**Rettelse:** Ikke nødvendig nå. Ved opt-in: bytt til
```java
getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
    @Override public void handleOnBackPressed() { /* ingenting */ }
});
```
(`androidx.activity` finnes ikke i dette bygget — uten Gradle må dette gjøres med plattform-API `OnBackInvokedDispatcher` (API 33+) bak `Build.VERSION.SDK_INT >= 33`.)

---

### F13 — Implisitt `uses-feature android.hardware.telephony` filtrerer enheter · **lav**

**Sted:** `AndroidManifest.xml:10` (`CALL_PHONE` uten tilhørende `<uses-feature>`).

**Symptom:** Verifisert med `aapt2 dump badging` på den bygde APK-en: `uses-implied-feature: android.hardware.telephony reason='requested a telephony permission'`. APK-en markeres dermed som *avhengig av* telefonoppsett. `adb install` bryr seg ikke, men Play/MDM-rulling filtrerer bort Wi-Fi-nettbrett og enheter uten telephony. Ikke API-nivåavhengig, men relevant for utrullering på tvers av enhetsflåter.

**Rettelse:**
```xml
<uses-feature android:name="android.hardware.telephony" android:required="false" />
```
Sammen med håndtering av at `ACTION_DIAL` ikke finnes på slike enheter (allerede håndtert: `resolveActivity` → `null` → «Ikke her»).

---

### F14 — Bygget kompilerer mot API 34 uten API-nivåkontroll · **lav**

**Sted:** `app/build.sh` — `javac -source 11 -target 11 -classpath $AJAR` mot `platforms/android-34/android.jar`, deretter `d8 --lib $AJAR --min-api 23`. Ingen lint, ingen API-verifisering.

**Symptom:** Ingen feil i dag — alle kalte plattformmetoder finnes på API 21–23 (`getLockTaskModeState` 21, `setStatusBarDisabled`/`setKeyguardDisabled`/`setPermissionGrantState` 23, `DISALLOW_SAFE_BOOT` 21, `DISALLOW_FACTORY_RESET` 21, `addPersistentPreferredActivity` 21). Men ingenting i bygget hindrer at noen kaller f.eks. `setLockTaskFeatures` (28) uten guard: det kompilerer mot API 34 og krasjer med `NoSuchMethodError` på Android 7 — uten at bygget sier fra.

**Rettelse:** Behold konvensjonen «hver API > 23 må ha `Build.VERSION.SDK_INT`-guard», og vurder et enkelt skriptsteg som feiler bygget hvis en kjent ny API brukes uten guard (grep-basert sjekk på `setLockTaskFeatures|WindowInsetsController|registerReceiver.*RECEIVER_|getSerial` o.l.). Dette er prosess, ikke kode.

---

### F15 — Android 14: lock task-features og lock task-pakker er én sammenslått policy · **høy (sammen med F3)**

**Sted:** `Kiosk.java:75–80` — `setLockTaskPackages` kalles isolert.

**Årsak (API 34):** Fra Android 14 er lock task features og lock task packages «bundled as one policy»: «A failure to apply one will result in a failure to apply the other.»

**Konsekvens:** Når F3 fikses, må `setLockTaskFeatures` og `setLockTaskPackages` settes i samme operasjon og resultatet verifiseres. Feiler `setLockTaskFeatures` (f.eks. ugyldig flaggkombinasjon), kan allowlisten også bli stående uendret — som betyr at barnet beholder tilgang til apper forelderen har slått av, eller mister tilgang til telefon.

**Rettelse:** Begge kall i samme `try`, med logging av begge returverdier (begge returnerer `void` i dag, men feil kastes/logges). Verifiser etterpå med `d.getLockTaskPackages(admin(c))` at listen faktisk inneholder dialer-pakken, og logg avvik.

---

### F16 — Avklart uten handling (dekker oppdragets punkt 4)

- **`android:exported` (API 31+):** Alt er allerede riktig satt — `HomeActivity` `true` (`AndroidManifest.xml:20`), `ParentActivity`/`ChessActivity` `false` (`:36`, `:42`), `AdminReceiver` `true` (`:49`). Ingen endring. ⚠️ `AdminReceiver` *må* være `exported="true"` med `BIND_DEVICE_ADMIN`; en «opprydding» til `false` ville bryte device admin.
- **`PendingIntent`-mutabilitet (API 31+):** Appen bruker ingen `PendingIntent` og ingen `Notification`. Intet å fikse. Hvis det legges til: `FLAG_IMMUTABLE` er påkrevd ved targetSdk 31+.
- **`registerReceiver`-flagg (API 34):** Appen registrerer ingen receivere (`grep` bekrefter). Intet å fikse. Hvis F6 løses med kjøretidsregistrering: `RECEIVER_NOT_EXPORTED` er påkrevd.
- **Bakgrunnsstart av activities (API 29/30+):** Alle `startActivity` skjer fra en synlig/resumed activity (`Catalog.java:155` via klikk, `HomeActivity.java:398`, `:485`), så restriksjonen er ikke berørt. Ingen dokumentert DO-fritak er nødvendig — og bør ikke antas hvis det senere startes activities fra receiver.
- **Fjernlagring / `getExternalStorageDir` / `Environment`:** Ikke brukt i det hele tatt. Scoped storage (API 29/30+) er irrelevant.
- **Slettet/fjernet API:** `Button`, `Switch`, `LinearLayout`, `Dialog`, `Paint.RadialGradient`, `MessageDigest` — alle gamle og stabile. Ingen bruk av `java.time`, streams, `Optional`, `List.of`, `String.join`, `java.util.Base64` (verifisert med `grep`) → **ingen core-library-desugaring-felle**, som er bra siden `d8` kjøres uten desugar-flagg.
- **`android:screenOrientation` / `resizeableActivity`:** se F8.
- **Installasjon:** Ingen manifest-attributter nyere enn API 23 brukes (alle `exported`/`launchMode`/`stateNotNeeded`/`excludeFromRecents`/`clearTaskOnLaunch`/`configChanges`/`allowBackup` er API 1–8). `targetSdkVersion 34` på en API 24-enhet er uproblematisk. **Ingenting gjør at install eller oppstart feiler på noe nivå 24–35.** Forutsetningen for DO er fortsatt `adb shell dpm set-device-owner` på en enhet uten kontoer og rett etter oppsett.

---

## 4. Prioriterte kodeendringer

Rekkefølge = risiko for barnet. Alt under `app/` er *ikke* endret i denne revisjonen; dette er forslag.

1. **`app/AndroidManifest.xml`** — legg `<queries>` (F1-koden over) som søsken til `<application>` etter linje 10, med de fem `<intent>`-blokkene og de fire `<package>`-oppføringene for Skyss. Vurder i tillegg `<uses-permission android:name="android.permission.QUERY_ALL_PACKAGES" />` fordi appen distribueres via sideload/MDM, ikke Play. Dette er den ene endringen som gir «barnet kan ringe» tilbake på Android 11–15.
2. **`app/src/no/safestart/kiosk/Kiosk.java:77–80`** — etter `setLockTaskPackages`, legg til `if (Build.VERSION.SDK_INT >= 28) d.setLockTaskFeatures(admin(c), DevicePolicyManager.LOCK_TASK_FEATURE_NONE);` i samme `try`-blokk (API 34 slår features+packages sammen, F3/F15) og logg resultatet.
3. **`Kiosk.java:53–66` (`allowlist`)** — logg `pkgs.size()` og innholdet på `Log.i` slik at en kollapset allowlist er synlig i logcat; vurder å verifisere med `d.getLockTaskPackages(admin(c))` etter påsetting.
4. **`Kiosk.java:82` og `:141`** — ta vare på returverdien fra `setStatusBarDisabled` og logg når den er `false`; deklarer `MANAGE_DEVICE_POLICY_STATUS_BAR` i manifestet for API 34+.
5. **`Kiosk.java:87`** — ta vare på returverdien fra `setKeyguardDisabled`; ved `false`, logg tydelig at skjermlås er satt og at kiosken ikke starter automatisk etter omstart (og fjern passordkravet med `setPasswordQuality(..., PASSWORD_QUALITY_UNSPECIFIED)`).
6. **`app/src/no/safestart/kiosk/AdminReceiver.java` + manifestet** — ny `BootReceiver` (`BOOT_COMPLETED`, ev. `LOCKED_BOOT_COMPLETED` med `directBootAware`), `RECEIVE_BOOT_COMPLETED`-permission, `android:exported="true"`; i `onReceive` kun `Kiosk.lock(context, new Prefs(context))` — ingen `startActivity`.
7. **`Kiosk.java` (`lock()`)** — legg til `d.setPermissionGrantState(admin(c), c.getPackageName(), CALL_PHONE, PERMISSION_GRANT_STATE_GRANTED)` innenfor `if (isDeviceOwner(c))`, og gjør `requestPermissions` i `ParentActivity.java:159–161` betinget av at appen *ikke* er DO.
8. **`Catalog.java:133–140`** — skift `catch (Exception)` til `catch (PackageManager.NameNotFoundException)` og logg pakkenavnet, så «ikke synlig» ikke lenger ser ut som «ikke installert».
9. **`app/AndroidManifest.xml:18–45`** — `android:resizeableActivity="false"` på `HomeActivity`, `ParentActivity`, `ChessActivity`.
10. **Ny `app/res/values/styles.xml` + `values-v31/styles.xml` + `values-v29/styles.xml`** — egen `Safestart`-stil med `windowBackground` (grunn), `windowSplashScreenBackground`/`windowSplashScreenAnimatedIcon` (31+) og `forceDarkAllowed=false` (29+); bytt `android:theme` på `AndroidManifest.xml:15` til `@style/Safestart`.
11. **`app/AndroidManifest.xml`** — `<uses-feature android:name="android.hardware.telephony" android:required="false" />`.
12. **`Ui.java:40–48`** — kommentar om at immersive-banen er knyttet til targetSdk 34; ved heving til 35: `WindowInsetsController`-varianten (eller `windowOptOutEdgeToEdgeEnforcement` i `values-v35`).

---

## 5. Må verifiseres empirisk på emulator

Hver sjekk bør kjøres på API 24, 28, 30, 31, 33, 34 og 35 med `dpm set-device-owner` satt og lock task aktivt.

1. **Allowlist-innhold (API 30+):** `adb shell dumpsys device_policy | grep -A5 "Lock task"` og `adb shell am get-current-user`/logcat — bekreft at dialer-pakken faktisk står i `getLockTaskPackages` *etter* `<queries>`-fiksen. Før fiksen: bekreft at listen bare inneholder `no.safestart.kiosk`.
2. **«Ring» i lock task (API 30+, før/etter fiks):** trykk flisen; før fiksen skal ingenting skje (systemvarsel om blokkert start, `launch()` returnerer likevel `true`); etter fiksen skal dialer åpnes. Dokumenter om systemet viser egen Toast, og om `startActivity` kaster eller ikke (koden fanger `Exception` og returnerer `false` — sjekk hvilken vei som faktisk tas).
3. **Flisetekst (API 30+):** at alle eksterne fliser viser «Ikke her» (`HomeActivity.java:323`) selv om de er installert — og at de etter fiksen viser riktig undertekst.
4. **Strømmeny (API 24–35):** langt trykk på av/på inne i lock task. Før F3: menyen vises på 28+. Etter F3: menyen skal være borte på 28+, men **fortsatt vises på 24–27** (ingen API finnes) — bekreft at dette er akseptert eller at min-API heves.
5. **Nødtelefon-avbrekk (API 28+):** fra strømmenyen, velg «Nødtelefon» og se om barnet kommer ut av allowlisten (kan det taste andre numre, komme til telefon-appen, eller tilbake til kiosken med tilbake-knapp?). Dette er den mest sannsynlige gjenværende fluktruten etter F3.
6. **Varselkurv (API 24–35):** dra ned fra toppen i lock task → skal ikke gi kurv. Deretter: avslutt lock task (`Kiosk.unlock()`), dra ned igjen → kurv skal vises, og på 24–33 skal `setStatusBarDisabled(false)` ha gjenopprettet den. På 34+: bekreft at `MANAGE_DEVICE_POLICY_STATUS_BAR` er innvilget automatisk (logcat/`dumpsys package no.safestart.kiosk | grep MANAGE_DEVICE_POLICY`).
7. **Keyguard (API 28+):** sett PIN *før* DO-oppsett → forvent at `setKeyguardDisabled` returnerer `false`; reboot og se om enheten stopper på låseskjerm. Gjenta uten PIN → forvent direkte oppstart i kiosk.
8. **Reboot per nivå (API 24/28/30/31/34/35):** reboot uten boot-receiver (nå) og med `BootReceiver` (etter F6). Mål: hvor lang tid til kiosken er tilbake, om HomeActivity vises uinnlogget, og om lock task faktisk er aktivt etterpå (`dumpsys activity activities | grep -i lockTask`).
9. **Direct boot (API 24+):** med `directBootAware`-receiver og en enhet som har skjermlås, se om `LOCKED_BOOT_COMPLETED` leveres og om `Prefs` er lesbar før opplåsing (forventet: nei — bekreft at koden ikke krasjer).
10. **Splash (API 31+):** start ParentActivity og ChessActivity; verifiser at splash ikke vises etter F7s `values-v31`-stil, eller at den i det minste er hvit uten ikonflimmer.
11. **Force Dark (API 29+):** slå på systemets mørke tema og sammenlign skjermbilder mot baseline; sjekk lesbarhet i fliser og `Backdrop`.
12. **Multi-vindu (API 24+):** prøv å tvinge split-screen (via en annen app eller `adb shell settings put global enable_freeform_support 1` på egnet image) og se om rutenettet klippes før/etter `resizeableActivity="false"`.
13. **Edge-to-edge (API 35):** kjør appen med targetSdk 34 på Android 15 — bekreft at dagens layout er uendret (ingen påtvunget edge-to-edge). Deretter et testbygg med targetSdk 35 og se om nederste rad går under gestelinjen.
14. **`CALL_PHONE` (API 30+):** tilbakekall tillatelsen manuelt (`adb shell pm revoke no.safestart.kiosk android.permission.CALL_PHONE`), åpne kiosken og trykk «Ring forelder» i lock task → forventet: `ACTION_DIAL` -> blokkert av lock task hvis dialer ikke er i allowlisten (kobler til F1). Verifiser deretter med `setPermissionGrantState` at tillatelsen er permanent.
15. **OEM-avvik:** gjenta sjekk 4, 6 og 7 på minst én Samsung- og én Xiaomi-enhet — statusbar/keyguard/lock task-oppførsel er kjent for å avvike fra AOSP.
16. **`startActivity` med `FLAG_ACTIVITY_NEW_TASK` fra lock task (`Catalog.java:155`):** bekreft at allowlistet app åpnes *i* den låste tasken og at tilbake-knapp fører tilbake til kiosken, i stedet for å gi en ulåst oppgave.

---

*Revisjonen er ren kodelesing + plattformdokumentasjon. Ingen emulator, adb eller Android SDK er berørt, og ingenting under `app/` er endret.*
