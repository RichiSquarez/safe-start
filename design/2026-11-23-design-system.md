# Safestart – designsystem for førstemobil-appen

Status: arbeidsdokument for testappen (`no.safestart.kiosk`). Alt her er implementert i
`app/src/no/safestart/kiosk/` med mindre det står «forslag».

Målet med systemet er ikke å se «kul» ut. Det er at en 12-åring skal skjønne skjermen på
to sekunder, og at en forelder som aldri har sett appen skal kunne låse opp uten hjelp.

---

## 1. Prinsipper

1. **Ro før farge.** Bakgrunnen er lys og nesten uten kanter. Farge brukes bare på ting
   barnet kan trykke på, aldri som dekor.
2. **Én ting per flate.** Hjem-skjermen har én oppgave: velge en app. Foreldreskjermen har
   én oppgave: skru av og på. Ingen faner, ingen innstillinger-i-innstillinger.
3. **Stemmen er en voksen, ikke en selger.** «Telefonen virker alltid.» er et løfte, ikke
   en reklame. Ingen utropstegn i brødtekst, ingen «Smart!», ingen emoji.
4. **Låst skal se låst ut.** Status står alltid øverst til høyre: klokke + «LÅST» + hengelås.
   Barnet skal aldri lure på om telefonen er åpen.

---

## 2. Farger

### Basis (brukes overalt)

| Token | Hex | Bruk |
|---|---|---|
| `PETROL` | `#173B4D` | Brødtekst, titler, logo, mørke flater |
| `TEAL` | `#116B65` | Aksent, «alltid tilgjengelig», positiv tilstand |
| `PAPER` | `#F7FAF8` | Bakgrunn |
| `MINT` | `#DDF1E9` | Rolige flater, ikonchips |
| `MINT2` | `#C8E2D8` | Sekundær mint, sjakkbrett (mørke ruter) |
| `PEACH` | `#FFD19A` | Foreldreflaten, «Mamma & Pappa» |
| `BODY` | `#49636B` | Sekundærtekst på lyst |
| `MUTED` | `#6E8586` | Tekst når noe ikke er tilgjengelig |
| `RULE` | `#D9E8E3` | Hårfine linjer og kanter |

### Per-flis aksent (chip)

Hver flis har én pastellfarge, og ikonet er alltid en mørkere nyanse av **samme** farge.
Det er regelen som gjør rutenettet fargerikt uten at det blir barnslig.

| Flis | Chip | Ikon |
|---|---|---|
| Ring | `#2BB98A` | `#FFFFFF` |
| Meldinger | `#C3D8F7` | `#173B4D` |
| Kamera | `#DACCF3` | `#4B3F72` |
| Kart | `#CBE8C1` | `#2C5F3A` |
| Skyss | `#C2E5F1` | `#1F5C6B` |
| Sjakk | `#F1E2C8` | `#6B4F1F` |
| Mamma & Pappa | `#FFD9AB` | `#8A5A1F` |

Regel: aldri to mettede chips ved siden av hverandre. Bare «Ring» er mettet, fordi den er
den eneste flisen som ikke kan slås av.

### Utilgjengelig tilstand

Flis som ikke er installert på telefonen: chip `#66C8E2D8`, ikon `MUTED`, undertekst
«Ikke her». Ingen rød feilmelding – et barn skal ikke tro at noe er ødelagt.

---

## 3. Typografi

Skrift: systemets egen (Roboto på Android 6). Vi laster ikke ned fonter: appen skal kunne
kjøre på en 2015-telefon uten nett.

| Rolle | Størrelse | Vekt | Sporing |
|---|---|---|---|
| Hilsen («Hei!») | 26 sp | bold | −0,01 |
| Flistittel | 16 sp | bold | 0 |
| Flisundertittel | 11 sp | normal | 0 (0,04 når den er en status) |
| Klokke | 16 sp | bold | 0 |
| Status under klokke («LÅST») | 8 sp | normal | stort (0,08) |
| Knapp («Mamma & Pappa») | 14 sp | bold | 0 |
| Hjelpetekst under knapp | 9,5 sp | normal | 0 |
| Bunntekst | 11 sp | normal | 0 |

Aldri mer enn tre tekststørrelser på én flate. Norsk er et langt språk: all tekst skal tåle
+30 % lengde før den bryter.

---

## 4. Rom og form

- Skjermkant: 22 dp side, 12 dp topp, 10 dp bunn.
- Rutenett: 2 kolonner, 3 rader, 9 dp mellom kolonner, 10 dp mellom rader.
- Kort: radius **24 dp**, fyll `#F5FFFFFF` (nesten hvit, litt gjennomsiktig), kant 1 px
  `#E2EFE9`. «Ring» har kant `#7FCCB4` fordi den er alltid på.
- Chip: 42 dp kvadrat, radius 15 dp.
- Pille (knapper, bunntekst): radius 999 dp.
- Innvendig luft i kort: 12 dp. Ikonet øverst, ordene nederst, tomrommet i midten – det er
  det som gir kortet «pust».

---

## 5. Komponenter

### Hode
Logo (skjold, 19 dp) + «Safestart» 18 sp bold petrol. Høyre: hvit pille med klokke,
«LÅST» og hengelås. Ingen meny, ingen innstillinger, ingen profil.

### Flis
Chip med ikon → tittel → undertekst. Sirkelpil (`→`, 28 dp, `#0D173B4D`) vises bare når
flisen faktisk kan åpnes. Er appen ikke installert, forsvinner pilen: ingenting å trykke på.

### Mamma & Pappa-knappen
Full bredde, peach pille, hjerte-chip, tittel + «Låser opp med PIN», hengelås til høyre.
Den er **synlig med vilje**: foreldrene skal finne den uten å huske et triks. Den åpner
PIN-dialogen, og bare PIN slipper inn. Lang-trykk på logo/klokke/bunntekst er beholdt som
hemmelig bakdør for demo, men er ikke nødvendig.

### PIN-dialog
Egen tegnet talltastatur (ingen systemtastatur – det kan ikke byttes ut av barnet).
Fire prikker, rød feiltekst, fem feil ⇒ 30 sekunders sperre. Feil telles fra første
fullstendige forsøk, ellers kan et barn prøve alle 10 000 kombinasjonene i ro og mak.

### Foreldreflate
«Device Owner: aktiv» øverst, deretter listen over hva barnet får bruke, med brytere.
«Ring» står som «ALLTID» og kan ikke skrus av. Nye PIN-felt, lås/lås opp, og en linje om
hvordan telefonen settes opp fra en datamaskin.

### Bunntekst
Hvit pille: skjold + peach prikk + «Telefonen virker alltid.» + hengelås. Dette er
produktløftet, og det står på hver eneste skjerm.

---

## 6. Bakgrunn

`PAPER` med fire myke radial-fargeflekker (mint, mint-mørk, peach, mint-lys) plassert i
hjørnene. De skal være så svake at de bare merkes som «lys», ikke som mønster. Ingen
bilder, ingen illustrasjoner, ingen gradienter med hard kant.

---

## 7. Bevegelse

Ett unntak: ingenting animerer. En telefon som skal føles rolig og låst skal ikke ha
sprett. Sjakkbrikkene tegnes om umiddelbart når et trekk er gjort.

---

## 8. Ikoner

24 × 24 viewBox, én `fill="#000000"`-path, ingen streker. De farges i koden med
`setColorFilter`, så samme fil brukes til alle farger. Filene ligger i `app/icons/` og
rendres til 144 px PNG av `build.sh` ved hvert bygg:

`phone`, `sms`, `camera`, `map`, `bus`, `chess`, `shield`, `arrow`, `lock`, `heart`.

Regel: ikonet skal ha omtrent samme «blekkvekt» (17–50 % av flaten). Et tynt strekikon ved
siden av et tungt fylt ikon ser ut som en feil.

---

## 9. Tekstregler

- Norsk bokmål, du-form til foreldre, «du» til barnet.
- Korte setninger. Maks 8 ord i en undertekst.
- Si hva som skjer, ikke hva brukeren skal føle: «Kan ikke slås av» > «Trygt valg».
- Aldri lov mer enn systemet holder: ikke «100 % sikker», ikke «alltid trygg», ikke
  «fungerer på alle telefoner». Skjermen sier «Telefonen virker alltid» fordi ringing er
  det ene vi faktisk kan garantere.
- Tall og enheter: «30 sek.», «10–15 mobiler», komma som desimaltegn.

---

## 10. Hva som er verifisert

Skjermbilder i `proof/`: `70-design-pass.png` (rutenett med pastellchips, gradientbakgrunn,
bunntekst), `80-mamma-pappa.png` (ny knapp), `84-pin-lockout.png` (sperre etter fem feil),
`71-chess-final.png` (sjakkbrettet).

Ikke verifisert ennå: hvordan systemet ser ut på en telefon med lavere tetthet (240 dpi) og
på Android 12+, der både statuslinje og navigasjon oppfører seg annerledes.
