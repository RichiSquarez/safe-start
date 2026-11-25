# QA — utflukter fra Safestart-kiosken

**Dato:** 2026-11-23
**App:** `no.safestart.kiosk` 0.1-test (versionCode 1), minSdk 23 / targetSdk 34
**Enhet:** emulator, arm64, Android 6.0 / API 23, 720×1280
**Oppsett:** Device Owner satt med `adb shell dpm set-device-owner no.safestart.kiosk/.AdminReceiver`; `Kiosk.enter()` → `setLockTaskPackages` + `setStatusBarDisabled(true)` + `startLockTask()`
**Metode:** kodelesing av `AndroidManifest.xml`, `HomeActivity`, `ParentActivity`, `PinDialog`, `Prefs`, `Kiosk`, `Catalog` + API-analyse for API 23. Ingen adb-kommandoer er kjørt fra denne QA-en (emulatoren eies av lead), alle kommandoer under er skrevet for å kunne kjøres senere.
**Forbehold:** repoet ble redigert mens dette ble skrevet (`ChessActivity`/`ChessEngine` kom inn underveis). Bygget som lå i `app/Safestart-test.apk` er **ikke `debuggable`** (ingen `--debug-mode` i `app/build.sh`, ingen `android:debuggable` i manifestet) og har `allowBackup="false"`; det er verifisert med `aapt2 dump xmltree` og er avgjørende for U25/U27/U36. Les koden på nytt før test — særlig at `ChessActivity` faktisk ligger i APK-en.

---

## 0. Kort fortalt

- **Det som holder, holder på grunn av Lock Task, ikke på grunn av appen.** `setLockTaskPackages()` + `startLockTask()` i Device Owner-modus gir `LOCK_TASK_MODE_LOCKED`: HOME, RECENTS, statuslinje og start av ikke-allowlistede pakker blokkeres av systemet. Det er denne mekanismen — ikke `excludeFromRecents`, ikke `onBackPressed()` — som gir produktløftet.
- **De kritiske hullene er i vår egen kode, ikke i Android:** `ParentActivity` sjekker ikke PIN selv (holdes i dag bare oppe av `exported="false"`), PIN-sperren teller bare feil ved 8 sifre (ubegrenset gjetting på 4–7 sifre), og `stopLockTask()` ligger bak en knapp uten re-autentisering (latent, bak førstnevnte).
- **Låset faller når lock task faller.** Krasj, tvangsstopp, omstart eller en annen foreground-task utenfor lock task gir vanlig launcher/låseskjerm. Det finnes ingen boot-mottaker, ingen `addPersistentPreferredActivity` for HOME, ingen `setKeyguardDisabled`.
- **De fire Device-Owner-restriksjonene som ville tettet mest mangler:** `DISALLOW_SAFE_BOOT`, `DISALLOW_FACTORY_RESET`, `setKeyguardDisabled`, `addPersistentPreferredActivity(HOME)`.
- **Dom:** som *testdemo* er kiosken overbevisende i lock task. Som *produkt* ("telefonen kan bare ringe") er den ikke klar: én krasj, én omstart eller ett trykk på feil sted i egen kode gir hele telefonen.

---

## 1. Trusselmodell

| Faktor | Antakelse |
|---|---|
| Angriper | barn 10–14 år, fysisk tilgang til telefonen, ingen PC/ladb under normal bruk |
| Motivasjon | komme til nett, YouTube, spill, kamera-rull, venner, "bare se" |
| Evner | høy utholdenhet, lav terskel for å google på en venns telefon, prøver alt som ser ut som en knapp |
| Ikke i modellen | root, fysisk demontering, tyveri av forelderens PC, målrettet adb |
| Testerens virkemidler | adb (for å bevise), `input`, `dumpsys`, `settings`, `pm`, `dpm` |

**Produktløftet som testes:** "telefonen kan bare ringe" = barnet skal ikke kunne (a) komme til andre apper, (b) endre innstillinger/nettverk, (c) komme tilbake til et vanlig Android-skrivebord, (d) fjerne sperren.

---

## 2. Alvorlighetsgrad

| Nivå | Betydning |
|---|---|
| **Kritisk** | Barnet kan selv, uten verktøy, komme ut av kiosken eller fjerne sperren. Bryter produktløftet fullstendig. |
| **Høy** | Barnet kan nå noe det ikke skal (nett, innstillinger, galleri/deling) eller bryte produktløftet midlertidig — men ikke nødvendigvis bli der. |
| **Middels** | Krever kunnskap/verktøy utenfor telefonen (adb, safe mode, recovery), eller gir personvernlekkasje uten full utflukt. |
| **Lav** | Kosmetisk, eller krever fysisk inngrep som ikke er realistisk for målgruppen. |

---

## 3. Mekanikken: hva som faktisk holder i dag

| Kontroll | API | Hva den gir | Hull |
|---|---|---|---|
| Device Owner | `dpm set-device-owner` (manuelt, adb) | gjør de andre kontrollene mulig | settes utenfor appen, forsvinner ved fabrikkreset, ingen boot-gjenoppretting |
| Allowlist | `DevicePolicyManager.setLockTaskPackages(admin, pkgs)` (API 21) | bare disse pakkene kan startes mens lock task er aktiv | allowlister *hele* pakken — alle aktiviteter, WebView, kontoer, hjelpelenker i tredjepartsapper (Skyss) |
| Lock task | `Activity.startLockTask()` (API 21), gitt allowlist → `LOCK_TASK_MODE_LOCKED` | HOME/RECENTS/statuslinje av; `startActivity` til ikke-allowlistet pakke returnerer `START_RETURN_LOCK_TASK_MODE_VIOLATION` | aktiv bare mens den låste tasken lever; faller ved krasj/omstart/kill; ikke aktiv på låseskjermen |
| Statuslinje | `DevicePolicyManager.setStatusBarDisabled(admin, true)` (API 23) | skjuler statuslinje + Quick Settings | gjelder i praksis bare i lock task; systemvinduer (strøymeny, ANR, lavt batteri) tegnes fortsatt |
| PIN-dialog | egen kode (`PinDialog` + `Prefs`) | foreldre kommer inn | sperren teller bare feil ved 8 sifre; `ParentActivity` sjekker ikke PIN |
| `excludeFromRecents` | manifest-flagg | skjuler tasken i RECENTS | **ingen sikkerhet** — påvirker ikke `startActivity`, HOME eller hvem som helst med adb |
| `singleInstance` / `clearTaskOnLaunch` / `stateNotNeeded` | manifest | ryddig task-oppførsel for en HOME-app | ingen sikkerhet |

**Viktig skille som hele matrisen hviler på:**

1. **Device Owner + lock task aktiv** → "LOCKED"-regimet. Dette er tilstanden appen er i etter `onResume()`.
2. **Device Owner, men lock task ikke aktiv** (oppstart, krasj, `stopLockTask`) → allowlisten gjelder fortsatt for *framtidige* `startLockTask`, men ingenting er låst nå. Barnet ser vanlig Android.
3. **Ikke Device Owner** → `startLockTask()` gir `LOCK_TASK_MODE_PINNED` = skjermfesting med bekreftelsesdialog og avpiningsgest. Dette er ikke en kiosk.

**Det som allerede er gjort riktig** (verdt å ikke ødelegge):

- `allowBackup="false"` → `adb backup` kan ikke hente `shared_prefs` (ellers en triviell PIN-utvinning).
- `MODE_PRIVATE` prefs → andre apper kan ikke lese PIN-filen.
- Bygget er **ikke** `debuggable` (ingen `--debug-mode` i `app/build.sh`, ingen `android:debuggable` i manifestet) → `run-as` er stengt; det holder U25/U27 lukket i dag.
- Device Owner blokkerer avinstallering: `am uninstall` mot egen pakke gir `DELETE_FAILED_DEVICE_POLICY_MANAGER`.
- `onBackPressed()` tom + `startLockTask()` holder faktisk HOME/BACK/RECENTS ute (bekreftet, B1–B4).

---

## 4. QA-matrise

### 4.1 Allerede bekreftet innestengt (baseline)

| ID | Vektor | Resultat |
|---|---|---|
| B1 | HOME (`input keyevent 3`) | Blokkert — `LOCK_TASK_MODE_LOCKED` |
| B2 | BACK (`input keyevent 4`) | Blokkert — `HomeActivity.onBackPressed()` er tom + lock task |
| B3 | RECENTS (`input keyevent 187`) | Blokkert — lock task skjuler/avviser recents |
| B4 | Åpne dialer, deretter HOME | Blokkert — dialer ligger i allowlisten, men HOME er fortsatt sperret |

### 4.2 A — System-UI, låseskjerm og systemvinduer

| ID | Vektor | Hvordan barnet prøver | Status og hva som avgjør | Alvor |
|---|---|---|---|---|
| **U1** | Statuslinje via hjørnesveip | sveip fra toppen av skjermen og ned | **Blokkert** når lock task er aktiv: `setStatusBarDisabled(admin, true)` (API 23) + `LOCK_TASK_MODE_LOCKED`. **Åpen** så snart lock task faller (omstart/krasj) — da er statuslinjen tilbake | Høy |
| **U2** | Hurtiginnstillinger: wifi av, flymodus på, Bluetooth, lommelykt, rotering | sveip to ganger fra toppen, trykk på flis | **Blokkert** sammen med statuslinjen (samme API). Men: ingen `DISALLOW_CONFIG_WIFI` / `DISALLOW_CONFIG_BLUETOOTH` / mobildata-restriksjon er satt, så hvis panelet først åpnes er alt fritt. Flymodus dreper produktløftet uten at barnet "kommer ut" | Høy |
| **U3** | Heads-up-varsel fra SMS | få en SMS mens kiosken står i forgrunnen, trykk på varselet | **Delvis blokkert**: i LOCKED er statuslinjen av, så varsler vises ikke. Kommer det likevel en heads-up (OEM-variant), åpner trykk SMS-appen — som er allowlistet, altså *inne* i kiosken. Ingen utflukt, men barnet kan lese alle meldinger | Middels |
| **U4** | Skjermbilde av PIN-skjermen | skjermdump/opptak, eller en allowlistet app som deler skjerm | **Åpen**: verken `setScreenCaptureDisabled(admin, true)` (API 21) eller `FLAG_SECURE` er satt. `adb shell screencap` fanger PIN-pad og prikkene. Krever riktignok en app/PC | Lav |
| **U5** | Kort trykk av/på → skjerm av → låseskjerm | `input keyevent 26` | **Delvis blokkert**: låseskjermen finnes (se U7), men kiosken ligger bak. Fra en *usikret* låseskjerm (sveip) er det ett sveip tilbake til `HomeActivity`, som låser på nytt i `onResume()` | Middels |
| **U6** | Langt trykk av/på → strøymeny (Slå av / Start på nytt) | holde av/på i ~1,5 s, velge "Start på nytt" | **Åpen**: Android 6 har ingen API for Device Owner til å fjerne strøymenyen (`setLockTaskFeatures`/`LOCK_TASK_FEATURE_GLOBAL_ACTIONS` er API 28+). Strøymenyen tegnes som systemvindu over lock task. Resultat: omstart → U7 | **Høy** |
| **U7** | Omstart → låseskjerm før kiosken rekker å låse | starte på nytt, så ligge på låseskjermen | **Åpen**: lock task er ikke aktiv under oppstart, og `setKeyguardDisabled(admin, true)` (API 23) er **ikke** kalt. På låseskjermen er hurtiginnstillinger (wifi/flymodus/Bluetooth), nødtelefon og kamera-hurtigtasten tilgjengelig — og `HomeActivity` låser først når den er resumed | **Høy** |
| **U8** | Nødnummer fra låseskjerm (112/110/113) | "NØDTILFELLE" → tast 112 → ring | **Åpen, men tillatt**: nødnumre er unntatt av plattformen (`KeyguardUpdateMonitor`/`EmergencyDialer`) og kan ikke blokkeres av Device Owner uten å fjerne låseskjermen. Ligger innenfor produktløftet ("kan ringe"). Ingen videre navigasjon fra nødtelefonen | Lav |
| **U9** | Kamera-hurtigtast på låseskjerm | dra kamera-ikonet på låseskjermen | **Delvis**: på API 23 starter låseskjerm-kamera `MediaStore.INTENT_ACTION_STILL_IMAGE_CAMERA` — samme pakke som kameraflisen, altså allowlistet. Men lock task er ikke aktiv, så barnet er i kamera *utenfor* låset; HOME fra kamera går til låseskjermen, ikke til kiosken. Ingen vei videre til galleri/deling (ikke allowlistet) | Middels |
| **U10** | "Safestart svarer ikke" / systemdialoger over lock task | fremprovosere ANR, lavt batteri, "Strømsparing på?" | **Delvis blokkert**: systemvinduer tegnes over lock task. ANR-dialogen kan avslutte appen → lock task faller → vanlig launcher (se U28). Lavt batteri-vindu gir ingen navigasjon, men beviser at systemvinduer slipper gjennom | Høy |

### 4.3 B — Lock task-mekanikken

| ID | Vektor | Hvordan barnet prøver | Status og hva som avgjør | Alvor |
|---|---|---|---|---|
| **U11** | Avpinning med BACK+RECENTS — **uten** Device Owner | holde BACK og RECENTS samtidig i ~1,5 s | **Åpen**: `startLockTask()` uten allowlist gir `LOCK_TASK_MODE_PINNED` = skjermfesting. Systemet viser "Skjermen er festet" og avpiningsgesten virker. Forutsetter at skjermfesting er slått på i Innstillinger → Sikkerhet. Uten DO er det ingen kiosk | **Kritisk** |
| **U12** | Avpinning med BACK+RECENTS — **med** Device Owner | samme gest | **Blokkert**: pakken står i `setLockTaskPackages`, altså `LOCK_TASK_MODE_LOCKED`, og da er avpiningsgesten deaktivert. Eneste vei ut er `stopLockTask()` fra appen (se U31) eller DPM | Lav |
| **U13** | RECENTS / app-bytte | `input keyevent 187` | **Blokkert** (bekreftet, B3): recents er av i LOCKED | Lav |
| **U14** | Dobbeltklikk RECENTS (bytt til forrige app) | `187` to ganger raskt | **Blokkert** av samme grunn som U13 | Lav |
| **U15** | Splittskjerm / to apper samtidig | langt trykk RECENTS, "Splitt skjerm" | **Ikke aktuelt**: multi-window kom i Android 7.0 (API 24). API 23 har ingen splittskjerm, ingen `windowingMode`, ingen fri-vindu-modus. Ingen test nødvendig — men dokumenter det, for det er første spørsmål fra en tester som kjenner nyere Android | — |
| **U16** | Hjem-app-velger / "alltid vs bare én gang" | trykke HOME når to launchers finnes, eller velge Launcher3 i dialogen | **Delvis**: i LOCKED blokkeres HOME helt. Men appen kaller aldri `addPersistentPreferredActivity(admin, HOME-filter, HomeActivity)` (API 21), så i vinduet før lock task er aktiv (oppstart, etter krasj) kan velgeren dukke opp, og Launcher3 er installert på emulatoren. Velger barnet Launcher3 er telefonen åpen | **Høy** |

### 4.4 C — App-til-app, intens og tredjeparts flater

| ID | Vektor | Hvordan barnet prøver | Status og hva som avgjør | Alvor |
|---|---|---|---|---|
| **U17** | Innstillinger via intent fra en allowlistet app (kamera-tannhjul, "Mer informasjon", anropsinnstillinger) | trykke seg gjennom dialerens/kameraets egne menyer | **Blokkert** i LOCKED: `startActivity` til `com.android.settings` avvises fordi pakken ikke er allowlistet (`START_RETURN_LOCK_TASK_MODE_VIOLATION` + toast). **Åpen** utenfor lock task | Middels |
| **U18** | Delingsark / "Åpne med" / "Bruk som bakgrunnsbilde" | dele bilde/kontakt, velge en app i arket | **Delvis**: velgeren (`com.android.internal.app.ChooserActivity`) er systemstyrt og kan tegnes, men hvert ikke-allowlistet mål avvises. Barnet ser applisten, men ingenting starter. Ingen utflukt, men forvirrende UI | Lav |
| **U19** | SMS-lenke → nettleser | motta SMS med lenke, trykke på den | **Blokkert** i LOCKED fordi nettleseren (`com.android.browser` på AOSP 6) ikke er allowlistet. **Kritisk å verifisere**: hvis nettleseren noen gang havner i allowlisten (f.eks. fordi en flises `resolvePackage()` peker på den), er hele internett åpent | **Høy** |
| **U20** | Play Store / pakkeinstallatør / ukjente kilder | åpne Play, installere APK fra fil | **Blokkert/ikke relevant**: Play Butikk er ikke i allowlisten (og finnes ikke på AOSP-avbildningen). "Ukjente kilder" krever Innstillinger (U17). Installasjon krever adb eller filbehandler — ingen av delene er nåbare i LOCKED | Lav |
| **U21** | Langt trykk app-ikon → appinfo / tvangsstopp / avinstaller | langt trykk på Safestart-ikonet i en launcher | **Ikke nåbar** i vårt oppsett (Safestart *er* launcheren, recents er av). Skulle den nås: tvangsstopp er mulig (→ U28), men avinstallering av Device Owner-pakken avvises av systemet (`DELETE_FAILED_DEVICE_POLICY_MANAGER`). `setUninstallBlocked` er ikke satt, men DO-statusen dekker oss | Middels |
| **U22** | Bytte standardapper (Home, telefon, SMS) | Innstillinger → Apper → Standardapper | **Blokkert** i LOCKED (Innstillinger ikke allowlistet). **Åpen** utenfor lock task — og det er nok: bytter barnet standard-Home til Launcher3, er kiosken borte ved neste HOME | **Høy** |
| **U23** | Skyss-flisen: hele den tredje appens flate | åpne Skyss, trykke på hjelp/konto/kjøp/lenker | **Delvis/åpen**: allowlisten gir *hele* pakken — konto, "min profil", hjelpesider, vilkår, eventuell innebygd WebView (da er internett åpent uten nettleser), kjøpsflyt. Under-15-profil i Skyss gir egne begrensninger, men de er Skyss sine, ikke våre. Dette er den største "ukjente" i allowlisten | **Høy** |
| **U24** | Tilbake til kiosken etter ekstern app | HOME fra dialer/Skyss | **Blokkert/ok**: HOME er av i LOCKED, og `HomeActivity` er den eneste HOME-aktiviteten som svarer. Barnet må bruke appens egen tilbake-knapp. Bekreftet i B4 | Lav |

### 4.5 D — Våre egne svakheter

| ID | Vektor | Hvordan barnet prøver | Status og hva som avgjør | Alvor |
|---|---|---|---|---|
| **U25** | **ParentActivity nås direkte — uten PIN** | `adb shell am start -n no.safestart.kiosk/.ParentActivity`, eller en framtidig eksport/deep link/widget | **Blokkert i dag — latent kritisk.** To porter er stengt: (a) manifestet har `android:exported="false"`, så `am start` fra shell gir `java.lang.SecurityException: Permission Denial: ... not exported from uid ...`; (b) bygget er ikke `debuggable`, så omveien `adb shell run-as no.safestart.kiosk am start ...` (som ellers er lovlig fordi den kjører som appens UID) feiler med `run-as: package not debuggable`. **MEN `ParentActivity.onCreate()` sjekker ikke PIN i det hele tatt** — den bygger hele foreldreskjermen med en gang. Én `exported="true"`, én deep link, én widget, eller et debug-bygg (`aapt2 link --debug-mode`, Android Studio) og barnet har "Lås opp telefonen", PIN-bytte og alle fliser. Vernet er altså et manifest-flagg, ikke kode | **Kritisk (latent)** |
| **U26** | PIN-brute force: sperren teller bare 8-sifrede forsøk | taste 4 feil sifre, slette, taste nye — om og om igjen | **Åpen**: `PinDialog.onKey()` kaller `prefs.checkPin()` ved hver lengde ≥ 4, men `fail()` — og dermed `registerFail()` — kalles **bare** når `entry.length() >= 8`. Feil 4–7-sifret PIN registreres aldri. 10 000 kombinasjoner × ~1 s = noen timer, uten ventetid og uten at `fails`-telleren rører seg. 5-forsøks-sperren på 30 s gjelder i praksis bare den som taster 8 sifre | **Kritisk** |
| **U27** | PIN-hashen er offline-knekkbar | lese `shared_prefs/safestart.xml` (root, eller debuggable bygg) | **Middels**: PIN lagres som `SHA-256("safestart:" + pin)` uten iterasjoner og med konstant salt. 10 000 kombinasjoner knekkes på millisekunder. Filen er `MODE_PRIVATE` (0600, app-UID) og `allowBackup="false"`, så verken andre apper eller `adb backup` får tak i den — det er bra. Bare root (eller et framtidig debug-bygg) åpner veien, derfor ikke høyere | Middels |
| **U28** | Krasj / tvangsstopp → lock task faller | appen krasjer, ANR "Lukk app", eller `am force-stop` | **Åpen**: lock task er knyttet til den kjørende tasken. Dør den, avsluttes lock task, og systemet faller tilbake til låseskjerm/launcher. Det finnes ingen boot-mottaker, ingen `DeviceAdminReceiver`-gjenoppretting, ingen `JobScheduler`-vakt. Etter en krasj er telefonen en vanlig Android-telefon til noen åpner Safestart igjen | **Kritisk** |
| **U29** | `stopLockTask()` bak "Lås opp telefonen" uten re-autentisering | komme inn i ParentActivity (U25) og trykke "Lås opp telefonen" | **Ikke nåbar i dag** (krever U25), men farlig når den nås: `Kiosk.unlock()` kaller `stopLockTask()` + `setStatusBarDisabled(false)`. Merk: `stopLockTask()` må kalles fra aktiviteten som startet lock task (`HomeActivity`); kalles den fra `ParentActivity` kan den kaste `IllegalStateException`/ikke gjøre noe. **Verifiser** — enten er knappen en sikkerhetsbombe, eller en funksjonell bug | **Kritisk (latent)** |
| **U30** | ChessActivity startes direkte | `adb shell am start -n no.safestart.kiosk/.ChessActivity` | **Blokkert**: `android:exported="false"` i manifestet. Risikoen er ikke eksport, men at sjakk-flisen er den eneste interne flisen — hvis den senere får WebView, "om appen"-lenke eller deling, arver den allowlisten. **Obs:** `ChessActivity.java`/`ChessEngine.java` kom inn i repoet under denne QA-en — verifiser at klassen faktisk ligger i APK-en du tester, ellers kaster flisen `ActivityNotFoundException` | Lav |
| **U31** | `excludeFromRecents` som "sikkerhet" | — | **Ingen sikkerhet**: flagget skjuler bare tasken i recents-UI. Det blokkerer ikke `startActivity`, `am start`, HOME, eller hvem som helst som kjenner komponentnavnet. Samme gjelder `singleInstance`, `stateNotNeeded`, `clearTaskOnLaunch` — de er UX, ikke vern. Dokumenteres for å hindre at noen "føler seg trygg" på dem | Lav |
| **U32** | Skjermbilde/opptak av PIN (ingen `setScreenCaptureDisabled`) | skjermdump under PIN-tasting | **Åpen** (samme som U4): `setScreenCaptureDisabled(admin, true)` (API 21) er ikke kalt, `FLAG_SECURE` mangler. Krever en app eller PC — derfor Lav/Middels, men det er en éen-linjes fix | Lav |

### 4.6 E — Fysisk, reset, oppstart og adb

| ID | Vektor | Hvordan barnet prøver | Status og hva som avgjør | Alvor |
|---|---|---|---|---|
| **U33** | Safe mode | langt trykk av/på → "Start på nytt i safe mode" (OEM), eller volum-ned under oppstart | **Åpen**: `DISALLOW_SAFE_BOOT` (API 23) er **ikke** satt. I safe mode deaktiveres alle tredjepartsapper — også Safestart — og systemlauncheren tar over. Barnet står i en fullt brukbar Android uten kiosk. Kan heller ikke hindres med `setStatusBarDisabled`. **Dette er den mest sannsynlige reelle utflukten for en 13-åring med Google** | **Kritisk** |
| **U34** | Fabrikkresetting fra Innstillinger | Innstillinger → Sikkerhetskopi og tilbakestilling → Fabrikkdata | **Delvis blokkert**: Innstillinger er ikke nåbar i LOCKED (U17), men er nåbar i safe mode (U33) og utenfor lock task. `DISALLOW_FACTORY_RESET` (API 21) er **ikke** satt, så når Innstillinger først er åpen er det to trykk til full wipe | **Kritisk** |
| **U35** | Fabrikkresetting fra recovery | av/på + volum opp, "Wipe data/factory reset" | **Åpen og kan ikke blokkeres på API 23**: Device Owner hindrer ikke recovery-wipe, og det finnes ingen FRP uten Google-konto. Etter wipe er telefonen ren og Safestart borte. Krever fysisk tastekombinasjon, men det er offentlig kunnskap | **Kritisk** |
| **U36** | adb / utvikleralternativer / USB-feilsøking | koble til PC, `adb shell` | **Åpen**: ingenting i appen slår av adb. `am force-stop` dreper kiosken (U28), `pm disable-user` fjerner den, `am crash`/`am start` når alt som er eksportert. `pm clear` nullstiller PIN til `1234` (appdata slettes; DO-tilstanden ligger i `/data/system/device_policies.xml`, ikke i appdata) — verifiser om systemet avviser `clear` for en DO-pakke. `run-as` er stengt fordi bygget ikke er debuggable, og `adb backup` er stengt av `allowBackup="false"` — men adb alene er nok. `setGlobalSetting(ADB_ENABLED, "0")` er mulig for DO på API 23, men ikke brukt. I felt: Middels (barnet har sjelden PC) — i test: **Kritisk** | Middels (Kritisk i test) |
| **U37** | SIM ut / ingen SIM / bytte SIM | åpne SIM-skuffen, ta ut kortet | **Åpen**: DO kan ikke hindre SIM-uttrekk på API 23. Ingen utflukt, men produktløftet ryker stille: ingen samtaler, "Ingen SIM"-dialoger, nødnumre kan fortsatt ringes. Bytte av SIM krever nål | Middels (produkt) |
| **U38** | Tilbakefall: standard-Home byttet | se U22 | **Åpen** utenfor lock task | **Høy** |

---

## 5. Testoppskrift (adb, 720×1280, API 23)

Alle kommandoer forutsetter `adb` mot emulatoren og at appen er Device Owner. Kjør `adb root` der det er markert (emulatoravbildningen er userdebug; på en user-build feiler det).

### 5.1 Verifiser tilstanden først

```bash
# Er vi Device Owner?
adb shell dumpsys device_policy | grep -iE "device owner|Device Owner"

# Lock task-tilstand og allowlist
adb shell dumpsys activity | grep -iE "mLockTaskModeState|mLockTaskPackages|LockTask"

# Hva har fokus nå (skal være HomeActivity når kiosken står i ro)
adb shell dumpsys window | grep -E "mCurrentFocus|mFocusedApp"

# Hvilke launcherer finnes (bevis for U16)
adb shell pm list packages | grep -iE "launcher|home"

# Er bygget debuggable (avgjør run-as-veien i U25/U36)?
adb shell dumpsys package no.safestart.kiosk | grep -iE "flags=|debuggable"
adb shell getprop ro.debuggable
```

### 5.2 Kommandoer per vektor

| ID | Kommando | Forventet |
|---|---|---|
| U1 | `adb shell input swipe 360 6 360 1100 400` + `adb exec-out screencap -p > /tmp/u1.png` | Ingenting skjer; fokus blir `HomeActivity`. Bilde viser ingen statuslinje |
| U2 | sveip som U1, deretter sveip igjen `input swipe 360 200 360 1100 400`; `adb shell settings get global airplane_mode_on` | Fortsatt `0`; panelet åpnes ikke |
| U3 | `adb emu sms send 40000000 "Hei"` + skjermbilde | Ingen heads-up i LOCKED |
| U4 | `adb exec-out screencap -p > /tmp/u4.png` mens PIN-pad er åpen (langt trykk på "Safestart"-ordmerket: `input swipe 100 60 100 60 1500`) | PIN-pad er synlig på bildet = ingen `FLAG_SECURE` |
| U5 | `adb shell input keyevent 26` → `input keyevent 26` → skjermbilde | Låseskjerm (sveip), ikke kiosk, i noen sekunder |
| U6 | `adb root` deretter `adb shell sendevent` (se 5.3) eller manuelt langt trykk | Strøymeny vises over lock task |
| U7 | `adb reboot`, vent på `sys.boot_completed=1`, `adb exec-out screencap -p > /tmp/boot.png`, `adb shell dumpsys window \| grep mCurrentFocus` | Låseskjerm/Keyguard før `HomeActivity` |
| U8 | på låseskjerm: trykk "NØDTILFELLE" (ca. `input tap 360 1180`), tast `112` | Nødtelefon åpnes; ingen videre navigasjon |
| U9 | på låseskjerm: dra kamera-ikonet (ca. `input swipe 660 1180 360 640 300`) | Kamera åpnes utenfor lock task |
| U10 | `adb shell dumpsys battery unplug && adb shell dumpsys battery set level 1` | Systemvindu over lock task (lavt batteri) |
| U11 | manuelt: hold BACK+RECENTS ~1,5 s (uten DO) | "Skjermen er festet" → avpinning virker |
| U12 | samme gest med DO | Ingenting skjer |
| U13/U14 | `adb shell input keyevent 187` (×2) | Ingen recents |
| U15 | `adb shell am start --windowingMode 3 -n no.safestart.kiosk/.HomeActivity` | `Error: Unknown option: --windowingMode` (finnes ikke på API 23) |
| U16 | `adb shell input keyevent 3` i vinduet rett etter `adb reboot` (før kiosken er resumed), skjermbilde | Mulig "Bruk som startskjerm"-velger med Launcher3 |
| U17 | `adb shell am start -a android.settings.SETTINGS` og `adb shell am start -a android.settings.HOME_SETTINGS` | Avvises i LOCKED (toast/blokkert); åpnes utenfor |
| U18 | `adb shell am start -a android.intent.action.SEND -t text/plain --es android.intent.extra.TEXT "x"` | Delingsark kan vises; alle ikke-allowlistede mål avvises |
| U19 | `adb emu sms send 40000000 "Se http://example.com"` → åpne Meldinger → trykk lenken | Nettleser starter ikke; `mCurrentFocus` blir ikke `com.android.browser` |
| U20 | `adb shell pm list packages \| grep -iE "vending\|packageinstaller"` | Play mangler/er ikke allowlistet |
| U21 | `adb shell pm uninstall no.safestart.kiosk` | `Failure [DELETE_FAILED_DEVICE_POLICY_MANAGER]` |
| U22 | `adb shell am start -a android.settings.HOME_SETTINGS` (uten lock task) | Innstillinger åpnes = barnet kan bytte Home |
| U23 | `adb shell pm list packages \| grep -i skyss` og `adb shell dumpsys package no.skyss.billett \| grep -iE "Activity\|WebView"` | Avgjør om Skyss finnes; se etter WebView/eksterne aktiviteter |
| U25 | `adb shell am start -n no.safestart.kiosk/.ParentActivity` — deretter `adb shell run-as no.safestart.kiosk am start -n no.safestart.kiosk/.ParentActivity` | `SecurityException: ... not exported from uid ...`, deretter `run-as: package not debuggable` (begge forventet). Først på et `--debug-mode`-bygg åpner den uten PIN |
| U26 | 10× : tast 4 feil sifre (`input tap` × 4, koordinater fra `uiautomator dump`) + `input keyevent 67` × 4; tast deretter riktig `1234` | Riktig PIN åpner foreldreskjermen **uten** "Vent 30 sek" → sperren er omgått. (Vil du se telleren: `run-as ... cat shared_prefs/safestart.xml` krever debuggable bygg) |
| U27 | `adb shell run-as no.safestart.kiosk cat /data/data/no.safestart.kiosk/shared_prefs/safestart.xml` (feiler uten debuggable/root) — deretter brute force av hashen (se 5.4) | På dette bygget: `package not debuggable`. På root/debug: PIN i klartekst etter noen ms |
| U28 | `adb shell am force-stop no.safestart.kiosk` → `adb shell input keyevent 3` → skjermbilde | Vanlig launcher/låseskjerm = lock task falt |
| U29 | `adb shell am crash no.safestart.kiosk` → skjermbilde | Krasj → lock task borte |
| U30 | `adb shell am start -n no.safestart.kiosk/.ChessActivity` | `SecurityException` (exported=false) |
| U32 | se U4 | PIN-pad fanges |
| U33 | `adb root; adb shell setprop persist.sys.safemode 1; adb reboot`; etter boot: `adb shell getprop persist.sys.safemode`, `adb shell pm list packages -e \| grep safestart` | Safe mode: Safestart er ikke aktiv, systemlauncher tar over |
| U34 | i safe mode: `adb shell am start -a android.settings.PRIVACY_SETTINGS` | Fabrikkreset-valget er to trykk unna |
| U35 | `adb reboot recovery` | Emulatorens recovery er minimal; på ekte telefon: wipe |
| U36 | `adb shell settings get global adb_enabled`, `adb shell pm clear no.safestart.kiosk`, `adb shell pm disable-user --user 0 no.safestart.kiosk` | `1`; PIN tilbake til `1234` etter `clear` (står det `Failed`, verner systemet DO-pakken — `force-stop`/`disable-user` virker uansett) |
| U37 | `adb emu gsm data off`, `adb emu gsm call 12345678` | Anrop/telefoni oppfører seg annerledes uten SIM |
| U38 | se U22 | — |

**Vil du bevise U25 uten å bygge på nytt?** `adb root` (emulatoren er userdebug) gir deg uid 0, og root er den eneste "brukeren" som kan omgå `exported="false"`. Prøv i denne rekkefølgen og noter hvilken som gir deg skjermen:

```bash
adb root
adb shell am start -n no.safestart.kiosk/.ParentActivity
# hvis fortsatt SecurityException: bygg et eget debug-bygg (aapt2 link --debug-mode) og bruk
adb shell run-as no.safestart.kiosk am start -n no.safestart.kiosk/.ParentActivity
```

Kommer du inn, er U25/U29 bekreftet som reell (om enn ikke barne-nåbar) sårbarhet: foreldreskjermen vises uten PIN, med "Lås opp telefonen" ett trykk unna.

### 5.3 Langt trykk av/på uten `--longpress` (API 23)

`input keyevent` på API 23 har ikke `--longpress` (`input: Unknown option: --longpress`). Bruk `sendevent` som root:

```bash
adb root
adb shell getevent -pl | grep -A3 -i "KEY_POWER"   # finn riktig /dev/input/eventN
# eksempel, event0:
adb shell sendevent /dev/input/event0 1 116 1   # KEY_POWER ned
adb shell sendevent /dev/input/event0 0 0 0     # SYN
sleep 2
adb shell sendevent /dev/input/event0 1 116 0   # KEY_POWER opp
adb shell sendevent /dev/input/event0 0 0 0
```

Samme teknikk for BACK+RECENTS (U11/U12): send `KEY_BACK` (158) og `KEY_APP_SWITCH` (254) ned, `sleep 2`, begge opp.

### 5.4 Bevis PIN-svakheten (U26/U27)

```bash
# 1) hash + teller — krever debuggable bygg eller root.
#    På dette bygget feiler run-as med "run-as: package not debuggable" (det er i seg selv et godt tegn).
#    Med root går det likevel an:
adb root && adb shell cat /data/data/no.safestart.kiosk/shared_prefs/safestart.xml
adb shell run-as no.safestart.kiosk cat /data/data/no.safestart.kiosk/shared_prefs/safestart.xml

# 2) knekk hashen (salt er konstanten "safestart:")
python3 - <<'PY'
import hashlib
target = "<lim-inn-pin_hash-her>"
for i in range(10000):
    p = f"{i:04d}"
    if hashlib.sha256(("safestart:" + p).encode()).hexdigest() == target:
        print("PIN =", p); break
PY
```

U26 trenger ikke filtilgang: ti feil 4-sifrede forsøk etterfulgt av riktig PIN som **åpner uten ventetid** er beviset. Har du XML-en, er `fails`/`locked_until` i samme fil det harde beviset — etter ti feil 4-sifrede forsøk skal `fails` fortsatt være `0`.

### 5.5 Koordinater, 720×1280

Ikke gjett koordinatene til PIN-pad og knapper — hent dem:

```bash
adb shell uiautomator dump /sdcard/ui.xml && adb pull /sdcard/ui.xml /tmp/ui.xml
python3 - <<'PY'
import re
x = open('/tmp/ui.xml').read()
for m in re.finditer(r'text="([^"]*)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', x):
    t, x1, y1, x2, y2 = m.groups()
    if t.strip():
        print(repr(t), "->", (int(x1)+int(x2))//2, (int(y1)+int(y2))//2)
PY
```

Grovark (mdpi/xhdpi-avvik kan forekomme): statuslinje sveip `360 6 → 360 1100`; RECENTS `187`; HOME `3`; BACK `4`; av/på `26`; langt trykk = `input swipe x y x y 1500`.

---

## 6. Prioriterte funn

Rangert etter hvor mye de koster produktløftet. Hver med én konkret fix.

| # | Funn | Alvor | Fix (én linje) |
|---|---|---|---|
| **1** | `ParentActivity` autentiserer ikke — hviler helt på `exported="false"`; debug-bygg + `run-as`, eller én framtidig eksport/deep link, gir hele foreldreskjermen inkl. `stopLockTask()` | Kritisk | La `ParentActivity.onCreate()` selv vise `PinDialog` og `finish()` uten gyldig PIN; aldri start den fra en kontekst som ikke er autentisert |
| **2** | PIN-sperren teller bare feil ved 8 sifre (`PinDialog.onKey` → `fail()` kun når `entry.length() >= 8`), så 4–7-sifrede forsøk gir ubegrenset gjetting | Kritisk | Kall `registerFail()` ved *hver* feil `checkPin()`, uansett lengde, og øk ventetiden eksponentielt (30 s → 5 min → 1 t) |
| **3** | `DISALLOW_SAFE_BOOT` mangler — safe mode deaktiverer Safestart og gir systemlauncheren | Kritisk | `dpm.addUserRestriction(admin, UserManager.DISALLOW_SAFE_BOOT)` (API 23) |
| **4** | Lock task faller ved krasj/tvangsstopp/ANR, og det finnes ingen gjenoppretting | Kritisk | Boot-`BroadcastReceiver` (`BOOT_COMPLETED`/`LOCKED_BOOT_COMPLETED`) + `addPersistentPreferredActivity` for HOME + start kiosken på nytt; vurder `setUninstallBlocked` og en `JobScheduler`-vakt |
| **5** | `DISALLOW_FACTORY_RESET` mangler — fabrikkreset fra Innstillinger (nåbar i safe mode) sletter alt | Kritisk | `dpm.addUserRestriction(admin, UserManager.DISALLOW_FACTORY_RESET)` (API 21) |
| **6** | Etter omstart vises låseskjermen før kiosken: QS (wifi/flymodus/Bluetooth), nødtelefon og kamera er tilgjengelig, og `setKeyguardDisabled` er ikke kalt | Høy | `dpm.setKeyguardDisabled(admin, true)` (API 23) + `setStatusBarDisabled` + `addPersistentPreferredActivity` for HOME |
| **7** | Ingen `addPersistentPreferredActivity` for HOME + Launcher3 installert: hjem-velger/standard-Home kan ta over i vinduet før lock task | Høy | `dpm.addPersistentPreferredActivity(admin, homeFilter, new ComponentName(ctx, HomeActivity.class))` |
| **8** | Skyss-flisen allowlister en hel tredjepartspakke (konto, hjelp, kjøp, ev. WebView) uten at vi kontrollerer flaten | Høy | Verifiser Skyss' aktiviteter/WebView før den er i allowlisten; vurder å ta den ut til leverandøren bekrefter, eller bind til én aktivitet |

**Rangert 9–10 (gratis å ta med):** `setScreenCaptureDisabled(admin, true)` mot PIN-avfotografering (U4/U32), og skru av adb/utvikleralternativer i produksjon (`setGlobalSetting(ADB_ENABLED, "0")`, release-bygg uten `debuggable`) (U36).

---

## 7. Hva vi ikke kan teste på emulatoren

| Ikke testbart | Hvorfor | Hva det betyr for konklusjonen |
|---|---|---|
| Langt trykk av/på → strøymeny → "safe mode" | Ingen fysisk av/på-knapp i emulatoren; `input` på API 23 kan ikke langt-trykke; OEM-menyen finnes ikke på AOSP | U6/U33 er analytisk konkludert, ikke empirisk. **Må testes på ekte Android 6-telefon** (Samsung/Huawei fra 2015–16 har "Restart in safe mode" i strøymenyn) |
| Recovery / wipe fra recovery | Emulatorens recovery er en "No command"-stub; ingen tastekombinasjon | U35 er ikke verifisert, men godt dokumentert plattferadferd. Test på ekte enhet |
| Ekte oppstartssekvens | Emulatoren har ingen bootloader-tilgang, ingen signert boot, ingen oppstart på 40 s med treg flash | U7-vinduet kan være lengre på ekte telefon → alvorligheten er sannsynligvis *høyere* i felt |
| OEM-skall (Samsung TouchWiz, Huawei EMUI, Xiaomi MIUI) | AOSP-avbildning | Strøymeny, safe mode-inngang, "Device care", dual-app, hurtigvalg og safe mode-oppførsel varierer. Matrisen er AOSP-sannhet |
| Google Play / Play Protect / Google-konto / FRP | AOSP-avbildningen har ikke Play | U20 er ikke testet; på en ekte telefon med Play kan "Installer ukjente apper" og Play-lenker fra Skyss være relevante |
| SIM, telefoni, nødnumre | Ingen radio | U8/U37 er ikke verifisert. `adb emu gsm call` simulerer anrop, men ikke ekte nødnummerruting |
| Fysisk SIM-uttrekk, USB, MTP, ADB over USB med PC | Fysisk | U36/U37 er testet kun som "adb-fra-shell", ikke som "barn med kabel" |
| Batteri-/termisk-/minne-ANR under reell bruk | Emulatoren er for rask og har for mye RAM | U10/U28 er fremprovosert, ikke naturlig. På en 2015-telefon med 1–2 GB RAM er krasj *vanligere* |
| Skjermopptak fra en annen app | Ingen slik app i allowlisten på emulatoren | U4/U32 er testet med `screencap` fra adb, ikke fra en ondsinnet app |
| Multivindu | Finnes ikke på API 23 | U15 er en ikke-vektor; ingen test nødvendig |
| Tilgjengelighetstjenester (TalkBack, Switch Access) | Krever at tjenesten aktiveres i Innstillinger, som ikke er nåbar | Ikke en realistisk vei i LOCKED, men uverifisert |

**Anbefalt minimum før lansering:** kjør U6, U7, U33, U34, U35 og U36 på minst én ekte Android 6-telefon med Device Owner, og gjenta U25/U26 på et *release*-bygg (ikke debuggable) for å bekrefte at `run-as`-veien faktisk er stengt.

---

## 8. Sammendrag for beslutning

| Spørsmål | Svar |
|---|---|
| Kan et barn komme ut med bare fingrene, i dag, i lock task? | Sannsynligvis nei — bortsett fra strøymeny → omstart → låseskjerm/safe mode (U6/U7/U33), som er den realistiske veien |
| Kan et barn komme ut ved å trykke lenge nok på feil sted i appen? | Nei i dag, men bare fordi `ParentActivity` er `exported="false"`. Appen selv har ingen sperre der (U25) |
| Er PIN-en et reelt hinder? | Nei. Lockouten kan omgås (U26), og en 4-sifret PIN er 10 000 kombinasjoner uten ventetid |
| Holder låset etter en krasj? | Nei (U28) |
| Er dette leveringsklart som "telefonen kan bare ringe"? | Nei. Fix 1–5 i kapittel 6 er minimumskravet, og 1–2 er rene kodefeil som bør rettes før noe annet |
